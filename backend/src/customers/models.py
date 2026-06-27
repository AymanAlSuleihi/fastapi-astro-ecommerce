import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base, TimestampMixin, UUIDMixin


class Address(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "address"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address_line1: Mapped[str] = mapped_column(String(256), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(256), nullable=True)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(32), nullable=False)
    country: Mapped[str] = mapped_column(String(128), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
