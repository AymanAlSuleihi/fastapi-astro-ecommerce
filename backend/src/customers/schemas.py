import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    label: str | None = Field(default=None, max_length=64)
    address_line1: str = Field(min_length=1, max_length=256)
    address_line2: str | None = Field(default=None, max_length=256)
    city: str = Field(min_length=1, max_length=128)
    state: str | None = Field(default=None, max_length=128)
    postal_code: str = Field(min_length=1, max_length=32)
    country: str = Field(min_length=1, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    is_default: bool = False


class AddressUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=64)
    address_line1: str | None = Field(default=None, min_length=1, max_length=256)
    address_line2: str | None = Field(default=None, max_length=256)
    city: str | None = Field(default=None, min_length=1, max_length=128)
    state: str | None = Field(default=None, max_length=128)
    postal_code: str | None = Field(default=None, min_length=1, max_length=32)
    country: str | None = Field(default=None, min_length=1, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    is_default: bool | None = None


class AddressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    label: str | None
    address_line1: str
    address_line2: str | None
    city: str
    state: str | None
    postal_code: str
    country: str
    phone: str | None
    is_default: bool
    created_at: datetime
    updated_at: datetime
