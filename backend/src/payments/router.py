from uuid import UUID

from fastapi import APIRouter, status

from src.customers.dependencies import CurrentCustomerDep
from src.database import DbDep
from src.payments.schemas import PaymentCreate, PaymentIntentResponse, PaymentRead
from src.payments.service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(data: PaymentCreate, _current_user: CurrentCustomerDep, db: DbDep):
    service = PaymentService(db)
    return await service.create_payment_intent(data.order_id)


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment(payment_id: UUID, db: DbDep):
    service = PaymentService(db)
    return await service.get_payment(payment_id)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def payment_webhook(
    provider: str,
    event_type: str,
    payment_id: str,
    db: DbDep,
):
    service = PaymentService(db)
    await service.handle_webhook(provider, event_type, payment_id)
    return {"status": "ok"}
