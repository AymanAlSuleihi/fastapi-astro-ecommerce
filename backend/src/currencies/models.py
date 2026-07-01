from sqlalchemy import DECIMAL, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base, TimestampMixin, UUIDMixin


class ExchangeRate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "exchange_rate"
    __table_args__ = (UniqueConstraint("base_currency", "target_currency"),)

    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[float] = mapped_column(DECIMAL(14, 8), nullable=False)
