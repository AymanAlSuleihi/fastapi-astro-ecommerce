import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    url: str
    alt_text: str | None
    sort_order: int
    width: int | None
    height: int | None
    file_size: int | None
    created_at: datetime
    updated_at: datetime


class ImageUpdate(BaseModel):
    alt_text: str | None = None
    sort_order: int | None = Field(default=None, ge=0)
