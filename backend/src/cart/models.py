from __future__ import annotations

import uuid

from sqlalchemy import DECIMAL, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base, TimestampMixin, UUIDMixin
from src.products.models import Product, ProductVariant


class Cart(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cart"

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("customer.id", ondelete="CASCADE"), nullable=True, index=True, unique=True
    )
    session_id: Mapped[str | None] = mapped_column(nullable=True, index=True)

    items: Mapped[list[CartItem]] = relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )


class CartItem(Base):
    __tablename__ = "cart_item"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cart.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variant.id", ondelete="RESTRICT"), nullable=False
    )
    unit_price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    cart: Mapped[Cart] = relationship("Cart", back_populates="items")
    product: Mapped[Product] = relationship("Product", lazy="joined")
    variant: Mapped[ProductVariant] = relationship("ProductVariant", lazy="joined")

    __table_args__ = (
        UniqueConstraint(
            "cart_id",
            "product_id",
            "variant_id",
            name="cart_item_cart_product_variant_key",
        ),
    )
