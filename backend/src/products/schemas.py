import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    slug: str = Field(min_length=1, max_length=256, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    parent_id: uuid.UUID | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    parent_id: uuid.UUID | None
    children: list[CategoryRead] = []
    created_at: datetime


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    slug: str = Field(min_length=1, max_length=256, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    price: float = Field(gt=0)
    stock_quantity: int = Field(ge=0)
    category_id: uuid.UUID | None = None
    image_url: str | None = None
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    category_id: uuid.UUID | None = None
    image_url: str | None = None
    is_active: bool | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    price: float
    stock_quantity: int
    category_id: uuid.UUID | None
    image_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductList(BaseModel):
    items: list[ProductRead]
    total: int
    page: int
    page_size: int
