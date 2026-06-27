import uuid

from sqlalchemy import select

from src.constants import PaymentStatus
from src.database import DbDep
from src.orders.service import OrderService
from src.payments.exceptions import PaymentNotFound
from src.payments.models import Payment
from src.payments.schemas import PaymentIntentResponse


class PaymentService:
    def __init__(self, db: DbDep):
        self.db = db

    async def create_payment_intent(self, order_id: uuid.UUID) -> PaymentIntentResponse:
        # Stub Stripe integration — in production, call stripe.PaymentIntent.create()
        order_service = OrderService(self.db)
        order = await order_service.get_order_by_id(order_id)

        payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            status=PaymentStatus.PENDING,
            provider="stripe",
            provider_payment_id=f"pi_stub_{order.id}",
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        return PaymentIntentResponse(
            client_secret=f"pi_{payment.id}_secret_stub",
            payment_id=payment.id,
        )

    async def handle_webhook(self, provider: str, event_type: str, payment_id: str) -> None:
        if provider != "stripe":
            return

        payment = await self.db.scalar(
            select(Payment).where(Payment.provider_payment_id == payment_id)
        )
        if not payment:
            raise PaymentNotFound()

        if event_type == "payment_intent.succeeded":
            payment.status = PaymentStatus.COMPLETED
        elif event_type == "payment_intent.payment_failed":
            payment.status = PaymentStatus.FAILED

        await self.db.commit()
