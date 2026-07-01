import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StoreSettingCreate(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    value: Any
    description: str | None = None
    is_public: bool = False
    section: str = Field(default="general", min_length=1, max_length=64)


class StoreSettingUpdate(BaseModel):
    value: Any = None
    description: str | None = None
    is_public: bool | None = None
    section: str | None = Field(default=None, min_length=1, max_length=64)


class StoreSettingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    value: Any
    description: str | None
    is_public: bool
    section: str
    created_at: datetime
    updated_at: datetime


class StoreSettingBulkItem(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    value: Any
    description: str | None = None
    is_public: bool = False
    section: str = Field(default="general", min_length=1, max_length=64)


class StoreSettingBulkUpdate(BaseModel):
    settings: list[StoreSettingBulkItem] = Field(min_length=1, max_length=100)
