import uuid

from sqlalchemy import DECIMAL, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base, TimestampMixin, UUIDMixin


class ShippingZone(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "shipping_zone"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    countries: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rates: Mapped[list[ShippingRate]] = relationship(
        "ShippingRate",
        back_populates="zone",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ShippingRate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "shipping_rate"

    zone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shipping_zone.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_cost: Mapped[float] = mapped_column(DECIMAL(8, 2), nullable=False)
    free_above: Mapped[float | None] = mapped_column(DECIMAL(8, 2), nullable=True)
    max_weight_kg: Mapped[float | None] = mapped_column(DECIMAL(8, 3), nullable=True)
    min_subtotal: Mapped[float | None] = mapped_column(DECIMAL(8, 2), nullable=True)
    min_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    zone: Mapped[ShippingZone] = relationship("ShippingZone", back_populates="rates")
