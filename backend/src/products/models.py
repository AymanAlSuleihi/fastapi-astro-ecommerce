import uuid

from sqlalchemy import DECIMAL, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base, TimestampMixin, UUIDMixin


class AttributeTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "attribute_template"

    name: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=False)


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
    children: Mapped[list[Category]] = relationship(
        "Category", back_populates="parent", lazy="selectin"
    )


class Product(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("category.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    attribute_template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("attribute_template.id", ondelete="SET NULL"), nullable=True
    )
    variant_attributes_override: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )

    category: Mapped[Category | None] = relationship("Category")
    attribute_template: Mapped[AttributeTemplate | None] = relationship(
        "AttributeTemplate"
    )
    variants: Mapped[list[ProductVariant]] = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ProductVariant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product_variant"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    price_override: Mapped[float | None] = mapped_column(
        DECIMAL(10, 2), nullable=True
    )
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(DECIMAL(8, 3), nullable=True)
    attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    product: Mapped[Product] = relationship("Product", back_populates="variants")
