import uuid

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base, TimestampMixin, UUIDMixin


class Cart(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cart"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=True, index=True, unique=True
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
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    cart: Mapped[Cart] = relationship("Cart", back_populates="items")
    product: Mapped[Product] = relationship("Product", lazy="joined")  # noqa: F821

    __table_args__ = (UniqueConstraint("cart_id", "product_id", name="cart_item_cart_product_key"),)
