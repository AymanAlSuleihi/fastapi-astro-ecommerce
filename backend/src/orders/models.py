import uuid
from datetime import datetime

from sqlalchemy import DECIMAL, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.constants import OrderStatus
from src.models import Base, TimestampMixin, UUIDMixin


class Order(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "order"

    display_id: Mapped[int] = mapped_column(
        Integer,
        server_default=text("nextval('order_display_id_seq')"),
        nullable=False,
        unique=True,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customer.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        String(32), default=OrderStatus.PENDING, nullable=False
    )
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    exchange_rate: Mapped[float | None] = mapped_column(DECIMAL(14, 8), nullable=True)
    total_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=False)
    tax_amount: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0.0, nullable=False)
    shipping_cost: Mapped[float] = mapped_column(DECIMAL(8, 2), default=0.0, nullable=False)
    base_total_amount: Mapped[float | None] = mapped_column(DECIMAL(12, 2), nullable=True)
    base_subtotal: Mapped[float | None] = mapped_column(DECIMAL(12, 2), nullable=True)
    base_tax_amount: Mapped[float | None] = mapped_column(DECIMAL(12, 2), nullable=True)
    base_shipping_cost: Mapped[float | None] = mapped_column(DECIMAL(8, 2), nullable=True)
    shipping_address_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("address.id", ondelete="SET NULL"), nullable=True
    )
    shipping_address: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    billing_address: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    shipping_rate_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("shipping_rate.id", ondelete="SET NULL"), nullable=True
    )
    estimated_delivery: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    items: Mapped[list[OrderItem]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def order_number(self) -> str:
        return f"ORD-{self.display_id:06d}"


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
    product_image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    line_total: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    order: Mapped[Order] = relationship("Order", back_populates="items")
