import uuid

from sqlalchemy import DECIMAL, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.constants import PaymentStatus
from src.models import Base, TimestampMixin, UUIDMixin


class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payment"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("order.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        String(32), default=PaymentStatus.PENDING, nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), default="stripe", nullable=False)
    provider_payment_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
