import uuid

from sqlalchemy import DECIMAL, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base, TimestampMixin, UUIDMixin


class Category(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "category"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("category.id", ondelete="SET NULL"), nullable=True, index=True
    )

    parent: Mapped[Category | None] = relationship(
        "Category", remote_side="Category.id", back_populates="children"
    )
    children: Mapped[list[Category]] = relationship("Category", back_populates="parent")


class Product(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(256), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("category.id", ondelete="SET NULL"), nullable=True, index=True
    )
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category: Mapped[Category | None] = relationship("Category")
