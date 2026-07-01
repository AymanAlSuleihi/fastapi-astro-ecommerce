import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from src.constants import OrderStatus


class OrderCreate(BaseModel):
    shipping_address_id: uuid.UUID | None = None
    billing_address: dict[str, Any] | None = None
    shipping_rate_id: uuid.UUID | None = None
    currency: str | None = None
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
    product_image_url: str | None
    line_total: float
    quantity: int
    currency: str | None


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_id: int
    order_number: str
    customer_id: uuid.UUID
    status: OrderStatus
    currency: str | None
    exchange_rate: float | None
    total_amount: float
    subtotal: float
    tax_amount: float
    shipping_cost: float
    base_total_amount: float | None
    base_subtotal: float | None
    base_tax_amount: float | None
    base_shipping_cost: float | None
    shipping_address: dict[str, Any] | None
    billing_address: dict[str, Any] | None
    shipping_rate_id: uuid.UUID | None
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
