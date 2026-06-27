import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.constants import PaymentStatus


class PaymentCreate(BaseModel):
    order_id: uuid.UUID


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    amount: float
    status: PaymentStatus
    provider: str
    provider_payment_id: str | None
    created_at: datetime
    updated_at: datetime


class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_id: uuid.UUID
