from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DECIMAL, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.docs.constants import DocumentStatus, DocumentType
from src.models import Base, TimestampMixin, UUIDMixin


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document"

    display_id: Mapped[int] = mapped_column(
        Integer,
        server_default=text("nextval('doc_display_id_seq')"),
        nullable=False,
        unique=True,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("order.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customer.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    document_type: Mapped[DocumentType] = mapped_column(String(32), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        String(32), default=DocumentStatus.SENT, nullable=False
    )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    subtotal: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=False)
    tax_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=False)
    total_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=False)
    billing_address: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    items: Mapped[list[DocumentItem]] = relationship(
        "DocumentItem",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def document_number(self) -> str:
        if isinstance(self.document_type, str):
            prefix = self.document_type[:3]
        else:
            prefix = self.document_type.value[:3]
        return f"{prefix}-{self.display_id:06d}"


class DocumentItem(Base):
    __tablename__ = "document_item"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )
    product_name: Mapped[str] = mapped_column(String(256), nullable=False)
    product_price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=False)

    document: Mapped[Document] = relationship("Document", back_populates="items")
