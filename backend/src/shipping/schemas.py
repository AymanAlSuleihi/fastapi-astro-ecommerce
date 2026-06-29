import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ── Zones ──────────────────────────────────────────────────────


class ZoneCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    countries: list[str] = Field(min_length=1)
    is_active: bool = True


class ZoneUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    countries: list[str] | None = None
    is_active: bool | None = None


class ZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    countries: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ── Rates ──────────────────────────────────────────────────────


class RateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    base_cost: float = Field(ge=0)
    free_above: float | None = Field(default=None, gt=0)
    max_weight_kg: float | None = Field(default=None, gt=0)
    min_subtotal: float | None = Field(default=None, ge=0)
    min_days: int | None = Field(default=None, ge=1)
    max_days: int | None = Field(default=None, ge=1)
    priority: int = Field(default=0)
    is_active: bool = True


class RateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = None
    base_cost: float | None = Field(default=None, ge=0)
    free_above: float | None = Field(default=None, gt=0)
    max_weight_kg: float | None = Field(default=None, gt=0)
    min_subtotal: float | None = Field(default=None, ge=0)
    min_days: int | None = Field(default=None, ge=1)
    max_days: int | None = Field(default=None, ge=1)
    priority: int | None = None
    is_active: bool | None = None


class RateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    zone_id: uuid.UUID
    name: str
    description: str | None
    base_cost: float
    free_above: float | None
    max_weight_kg: float | None
    min_subtotal: float | None
    min_days: int | None
    max_days: int | None
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ── Calculate ──────────────────────────────────────────────────


class ShippingOption(BaseModel):
    rate_id: uuid.UUID
    name: str
    description: str | None
    cost: float
    is_free: bool
    min_days: int | None
    max_days: int | None


class CalculateRequest(BaseModel):
    country_code: str = Field(min_length=2, max_length=2)
    product_id: uuid.UUID | None = None
    quantity: int = Field(default=1, ge=1)


class CalculateResponse(BaseModel):
    subtotal: float
    options: list[ShippingOption]
    zone_name: str | None
