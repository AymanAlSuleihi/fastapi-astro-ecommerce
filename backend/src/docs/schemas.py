import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.docs.constants import DocumentStatus, DocumentType


class DocumentItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_name: str
    product_price: float
    quantity: int
    line_total: float


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_id: int
    document_number: str
    order_id: uuid.UUID
    customer_id: uuid.UUID
    document_type: DocumentType
    status: DocumentStatus
    due_date: datetime | None
    subtotal: float
    tax_amount: float
    total_amount: float
    billing_address: dict | None
    notes: str | None
    pdf_url: str | None
    items: list[DocumentItemRead] = []
    created_at: datetime
    updated_at: datetime


class DocumentList(BaseModel):
    items: list[DocumentRead]
    total: int
    page: int
    page_size: int


class DocumentStatusUpdate(BaseModel):
    status: DocumentStatus
