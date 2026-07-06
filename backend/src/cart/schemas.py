import uuid

from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: int = Field(ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0)


class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: uuid.UUID
    product_name: str
    product_slug: str
    product_image_url: str | None = None
    variant_id: uuid.UUID
    variant_sku: str | None = None
    unit_price: float
    quantity: int
    line_total: float


class CartRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID | None
    items: list[CartItemRead] = []
    subtotal: float = 0.0
    item_count: int = 0
