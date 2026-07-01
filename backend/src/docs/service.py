import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.database import DbDep
from src.docs.constants import DocumentStatus, DocumentType
from src.docs.exceptions import DocumentNotFound
from src.docs.models import Document, DocumentItem
from src.logging_config import get_logger
from src.storage.service import StorageService

logger = get_logger(__name__)


class DocumentService:
    def __init__(self, db: DbDep):
        self.db = db

    async def create_from_order(
        self,
        order_id: uuid.UUID,
        customer_id: uuid.UUID,
        items: list[dict],
        subtotal: float,
        tax_amount: float,
        total_amount: float,
        billing_address: dict | None = None,
        notes: str | None = None,
        document_type: DocumentType = DocumentType.INVOICE,
    ) -> Document:
        doc = Document(
            order_id=order_id,
            customer_id=customer_id,
            document_type=document_type,
            status=DocumentStatus.SENT,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            billing_address=billing_address,
            notes=notes,
        )
        self.db.add(doc)
        await self.db.flush()

        for item in items:
            doc_item = DocumentItem(
                document_id=doc.id,
                product_name=item["product_name"],
                product_price=item["product_price"],
                quantity=item["quantity"],
                line_total=item["line_total"],
            )
            self.db.add(doc_item)

        await self.db.commit()
        await self.db.refresh(doc)

        # Generate PDF (best-effort — don't fail order creation)
        try:
            await self._generate_and_store_pdf(doc)
        except Exception:
            logger.warning("pdf_generation_failed", document_id=str(doc.id))

        logger.info(
            "document_created",
            document_id=str(doc.id),
            document_type=document_type.value,
            order_id=str(order_id),
        )
        return doc

    async def get_by_id(self, doc_id: uuid.UUID) -> Document:
        doc = await self.db.scalar(
            select(Document)
            .where(Document.id == doc_id)
            .options(selectinload(Document.items))
        )
        if not doc:
            raise DocumentNotFound()
        return doc

    async def list_for_order(self, order_id: uuid.UUID) -> list[Document]:
        result = await self.db.execute(
            select(Document)
            .where(Document.order_id == order_id)
            .options(selectinload(Document.items))
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[Document], int]:
        count_query = select(func.count(Document.id))
        total = await self.db.scalar(count_query)

        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Document)
            .options(selectinload(Document.items))
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total or 0

    async def update_status(
        self, doc_id: uuid.UUID, status: DocumentStatus
    ) -> Document:
        doc = await self.get_by_id(doc_id)
        doc.status = status
        await self.db.commit()
        await self.db.refresh(doc)
        logger.info(
            "document_status_changed", document_id=str(doc_id), status=status.value
        )
        return doc

    async def regenerate_pdf(self, doc_id: uuid.UUID) -> Document:
        doc = await self.get_by_id(doc_id)
        await self._generate_and_store_pdf(doc)
        return doc

    async def _generate_and_store_pdf(self, doc: Document) -> None:
        from src.docs.pdf import generate_pdf

        doc_dict = _document_to_dict(doc)
        pdf_bytes = generate_pdf(doc_dict)

        storage = StorageService()
        key = storage.build_key("documents", doc.id, f"{doc.document_number}.pdf")
        if storage.configured:
            doc.pdf_url = storage.upload(pdf_bytes, key, "application/pdf")
        else:
            doc.pdf_url = f"/storage/{key}"

        await self.db.commit()
        await self.db.refresh(doc)


def _document_to_dict(doc: Document) -> dict:
    return {
        "id": str(doc.id),
        "document_number": doc.document_number,
        "document_type": doc.document_type.value,
        "status": doc.status.value,
        "due_date": doc.due_date.isoformat() if doc.due_date else None,
        "subtotal": float(doc.subtotal),
        "tax_amount": float(doc.tax_amount),
        "total_amount": float(doc.total_amount),
        "billing_address": doc.billing_address,
        "notes": doc.notes,
        "items": [
            {
                "product_name": item.product_name,
                "product_price": float(item.product_price),
                "quantity": item.quantity,
                "line_total": float(item.line_total),
            }
            for item in doc.items
        ],
        "created_at": doc.created_at.isoformat(),
    }
