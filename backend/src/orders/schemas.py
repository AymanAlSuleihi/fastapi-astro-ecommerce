import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.constants import OrderStatus


class OrderCreate(BaseModel):
    shipping_address_id: uuid.UUID | None = None
    shipping_rate_id: uuid.UUID | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    variant_sku: str | None
    product_name: str
    product_price: float
    line_total: float
    quantity: int


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_id: int
    order_number: str
    customer_id: uuid.UUID
    status: OrderStatus
    total_amount: float
    subtotal: float
    tax_amount: float
    shipping_address_id: uuid.UUID | None
    shipping_rate_id: uuid.UUID | None
    shipping_cost: float
    estimated_delivery: datetime | None
    items: list[OrderItemRead] = []
    created_at: datetime
    updated_at: datetime


class OrderList(BaseModel):
    items: list[OrderRead]
    total: int
    page: int
    page_size: int


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
