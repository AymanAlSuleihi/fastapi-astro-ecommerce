import uuid

from fastapi import APIRouter, Response

from src.admin.dependencies import CurrentAdminDep
from src.customers.dependencies import CurrentCustomerDep
from src.database import DbDep
from src.docs.schemas import DocumentList, DocumentRead, DocumentStatusUpdate
from src.docs.service import DocumentService, _document_to_dict

router = APIRouter(tags=["docs"])

# ── Customer ──────────────────────────────────────────────


@router.get("/orders/{order_id}/docs", response_model=list[DocumentRead])
async def list_order_docs(
    order_id: uuid.UUID,
    current_customer: CurrentCustomerDep,
    db: DbDep,
):
    """List all documents for an order. Customer must own the order."""
    from src.orders.service import OrderService

    order_service = OrderService(db)
    order = await order_service.get_order_by_id(order_id)
    if order.customer_id != current_customer.id:
        from src.exceptions import ForbiddenException
        raise ForbiddenException(detail="Not your order")

    service = DocumentService(db)
    return await service.list_for_order(order_id)


@router.get("/docs/{doc_id}/download")
async def download_document(
    doc_id: uuid.UUID,
    current_customer: CurrentCustomerDep,
    db: DbDep,
):
    """Download a document PDF. Customer must own the order."""
    service = DocumentService(db)
    doc = await service.get_by_id(doc_id)

    if doc.customer_id != current_customer.id:
        from src.exceptions import ForbiddenException
        raise ForbiddenException(detail="Not your document")

    return await _stream_pdf(doc, service, doc_id)


# ── Admin ─────────────────────────────────────────────────

_admin_router = APIRouter(prefix="/admin/docs", tags=["docs"])
admin_router = _admin_router


@_admin_router.get("", response_model=DocumentList)
async def list_all_docs(
    db: DbDep,
    _admin: CurrentAdminDep,
    page: int = 1,
    page_size: int = 20,
):
    service = DocumentService(db)
    items, total = await service.list_all(page=page, page_size=page_size)
    return DocumentList(items=items, total=total, page=page, page_size=page_size)


@_admin_router.get("/{doc_id}", response_model=DocumentRead)
async def get_doc(doc_id: uuid.UUID, db: DbDep, _admin: CurrentAdminDep):
    service = DocumentService(db)
    return await service.get_by_id(doc_id)


@_admin_router.patch("/{doc_id}/status", response_model=DocumentRead)
async def update_doc_status(
    doc_id: uuid.UUID,
    data: DocumentStatusUpdate,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = DocumentService(db)
    return await service.update_status(doc_id, data.status)


@_admin_router.get("/{doc_id}/download")
async def admin_download_document(doc_id: uuid.UUID, db: DbDep, _admin: CurrentAdminDep):
    service = DocumentService(db)
    doc = await service.get_by_id(doc_id)
    return await _stream_pdf(doc, service, doc_id)


@_admin_router.post("/{doc_id}/regenerate-pdf", response_model=DocumentRead)
async def regenerate_doc_pdf(doc_id: uuid.UUID, db: DbDep, _admin: CurrentAdminDep):
    service = DocumentService(db)
    return await service.regenerate_pdf(doc_id)


async def _stream_pdf(doc, service, doc_id) -> Response:
    """Return PDF bytes. Regenerates if no stored URL."""
    if not doc.pdf_url:
        doc = await service.regenerate_pdf(doc_id)

    if doc.pdf_url and doc.pdf_url.startswith("http"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=doc.pdf_url)

    from src.docs.pdf import generate_pdf

    pdf_bytes = generate_pdf(_document_to_dict(doc))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={doc.document_number}.pdf"
        },
    )
