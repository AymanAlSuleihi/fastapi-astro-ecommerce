import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ── Attribute Templates ──────────────────────────────────────


class AttributeDefinition(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    values: list[str] = Field(min_length=1)


class AttributeTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    attributes: dict[str, AttributeDefinition]


class AttributeTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    attributes: dict[str, AttributeDefinition] | None = None


class AttributeTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    attributes: dict
    created_at: datetime
    updated_at: datetime


# ── Categories ───────────────────────────────────────────────


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    slug: str = Field(min_length=1, max_length=256, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    parent_id: uuid.UUID | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )


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
    stock_quantity: int = Field(default=0, ge=0)
    category_id: uuid.UUID | None = None
    is_active: bool = True
    attribute_template_id: uuid.UUID | None = None
    variant_attributes_override: dict[str, AttributeDefinition] | None = None


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
    is_active: bool | None = None
    attribute_template_id: uuid.UUID | None = None
    variant_attributes_override: dict[str, AttributeDefinition] | None = None


class VariantCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=128)
    price_override: float | None = Field(default=None, gt=0)
    stock_quantity: int = Field(default=0, ge=0)
    weight_kg: float | None = Field(default=None, ge=0)
    attributes: dict[str, str] | None = None
    is_active: bool = True


class VariantUpdate(BaseModel):
    price_override: float | None = Field(default=None, gt=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    weight_kg: float | None = Field(default=None, ge=0)
    attributes: dict[str, str] | None = None
    is_active: bool | None = None


class VariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sku: str
    price_override: float | None
    stock_quantity: int
    weight_kg: float | None
    attributes: dict | None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    price: float
    currency: str
    display_price: float | None = None
    stock_quantity: int
    category_id: uuid.UUID | None
    is_active: bool
    attribute_template_id: uuid.UUID | None
    variant_attributes: dict | None
    variants: list[VariantRead] = []
    created_at: datetime
    updated_at: datetime


class ProductList(BaseModel):
    items: list[ProductRead]
    total: int
    page: int
    page_size: int
