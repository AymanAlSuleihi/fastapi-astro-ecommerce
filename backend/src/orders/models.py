import uuid
from datetime import datetime

from sqlalchemy import DECIMAL, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.constants import OrderStatus
from src.models import Base, TimestampMixin, UUIDMixin


class Order(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "order"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customer.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        String(32), default=OrderStatus.PENDING, nullable=False
    )
    total_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=False)
    shipping_address_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("address.id", ondelete="SET NULL"), nullable=True
    )
    shipping_rate_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("shipping_rate.id", ondelete="SET NULL"), nullable=True
    )
    shipping_cost: Mapped[float] = mapped_column(DECIMAL(8, 2), default=0.0, nullable=False)
    estimated_delivery: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    items: Mapped[list[OrderItem]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )


class OrderItem(Base):
    __tablename__ = "order_item"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("order.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product.id", ondelete="RESTRICT"), nullable=False
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_variant.id", ondelete="RESTRICT"), nullable=True
    )
    variant_sku: Mapped[str | None] = mapped_column(String(128), nullable=True)
    product_name: Mapped[str] = mapped_column(String(256), nullable=False)
    product_price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped[Order] = relationship("Order", back_populates="items")
