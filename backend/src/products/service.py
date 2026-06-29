import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.database import DbDep
from src.products.exceptions import (
    CategoryNotFound,
    InsufficientStock,
    ProductNotFound,
    TemplateNotFound,
    VariantNotFound,
)
from src.products.models import (
    AttributeTemplate,
    Category,
    Product,
    ProductVariant,
)
from src.products.schemas import (
    ProductCreate,
    ProductUpdate,
    VariantCreate,
    VariantUpdate,
)


class ProductService:
    def __init__(self, db: DbDep):
        self.db = db

    # ── Attribute Templates ────────────────────────────────────

    async def list_templates(self) -> list[AttributeTemplate]:
        result = await self.db.execute(
            select(AttributeTemplate).order_by(AttributeTemplate.name)
        )
        return list(result.scalars().all())

    async def get_template(self, template_id: uuid.UUID) -> AttributeTemplate:
        template = await self.db.scalar(
            select(AttributeTemplate).where(AttributeTemplate.id == template_id)
        )
        if not template:
            raise TemplateNotFound()
        return template

    async def create_template(
        self, name: str, attributes: dict
    ) -> AttributeTemplate:
        template = AttributeTemplate(
            name=name,
            attributes={k: v.model_dump() for k, v in attributes.items()},
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update_template(
        self,
        template_id: uuid.UUID,
        name: str | None,
        attributes: dict | None,
    ) -> AttributeTemplate:
        template = await self.get_template(template_id)
        if name is not None:
            template.name = name
        if attributes is not None:
            template.attributes = {
                k: v.model_dump() for k, v in attributes.items()
            }
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete_template(self, template_id: uuid.UUID) -> None:
        template = await self.get_template(template_id)
        await self.db.delete(template)
        await self.db.commit()

    # ── Categories ──────────────────────────────────────────────

    async def get_categories(self) -> list[Category]:
        result = await self.db.execute(
            select(Category)
            .where(Category.parent_id.is_(None))
            .options(selectinload(Category.children))
            .order_by(Category.name)
        )
        return list(result.scalars().all())

    async def get_category_by_slug(self, slug: str) -> Category:
        cat = await self.db.scalar(
            select(Category)
            .where(Category.slug == slug)
            .options(selectinload(Category.children))
        )
        if not cat:
            raise CategoryNotFound()
        return cat

    async def create_category(self, name: str, slug: str, parent_id: uuid.UUID | None) -> Category:
        if parent_id:
            parent = await self.db.scalar(select(Category).where(Category.id == parent_id))
            if not parent:
                raise CategoryNotFound()
        category = Category(name=name, slug=slug, parent_id=parent_id)
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update_category(
        self, category_id: uuid.UUID, name: str | None, slug: str | None
    ) -> Category:
        cat = await self.db.scalar(select(Category).where(Category.id == category_id))
        if not cat:
            raise CategoryNotFound()
        if name is not None:
            cat.name = name
        if slug is not None:
            cat.slug = slug
        await self.db.commit()
        await self.db.refresh(cat)
        return cat

    async def delete_category(self, category_id: uuid.UUID) -> None:
        cat = await self.db.scalar(select(Category).where(Category.id == category_id))
        if not cat:
            raise CategoryNotFound()
        await self.db.delete(cat)
        await self.db.commit()

    # ── Products ────────────────────────────────────────────────

    async def get_products(
        self,
        page: int = 1,
        page_size: int = 20,
        category_slug: str | None = None,
        search: str | None = None,
        active_only: bool = True,
    ) -> tuple[list[Product], int]:
        query = select(Product).options(selectinload(Product.variants))
        count_query = select(func.count(Product.id))

        if active_only:
            query = query.where(Product.is_active.is_(True))
            count_query = count_query.where(Product.is_active.is_(True))

        if category_slug:
            cat = await self.get_category_by_slug(category_slug)
            query = query.where(Product.category_id == cat.id)
            count_query = count_query.where(Product.category_id == cat.id)

        if search:
            search_filter = Product.name.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total = await self.db.scalar(count_query) or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Product.name)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_product_by_slug(self, slug: str) -> Product:
        product = await self.db.scalar(
            select(Product)
            .where(Product.slug == slug)
            .options(
                selectinload(Product.variants),
                selectinload(Product.attribute_template),
            )
        )
        if not product:
            raise ProductNotFound()
        return product

    async def get_product_by_id(self, product_id: uuid.UUID) -> Product:
        product = await self.db.scalar(
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.variants),
                selectinload(Product.attribute_template),
            )
        )
        if not product:
            raise ProductNotFound()
        return product

    async def create_product(self, data: ProductCreate) -> Product:
        if data.category_id:
            cat = await self.db.scalar(
                select(Category).where(Category.id == data.category_id)
            )
            if not cat:
                raise CategoryNotFound()

        if data.attribute_template_id:
            await self.get_template(data.attribute_template_id)

        override = None
        if data.variant_attributes_override:
            override = {
                k: v.model_dump()
                for k, v in data.variant_attributes_override.items()
            }

        create_data = data.model_dump(
            exclude={"variant_attributes_override", "stock_quantity"}
        )
        create_data["variant_attributes_override"] = override
        product = Product(**create_data)
        self.db.add(product)
        await self.db.flush()

        # Always create one default variant
        variant = ProductVariant(
            product_id=product.id,
            sku=f"{data.slug}-default",
            stock_quantity=data.stock_quantity,
            is_default=True,
        )
        self.db.add(variant)
        await self.db.commit()
        await self.db.refresh(product, ["variants", "attribute_template"])
        return product

    async def update_product(
        self, product_id: uuid.UUID, data: ProductUpdate
    ) -> Product:
        product = await self.get_product_by_id(product_id)
        update_data = data.model_dump(
            exclude_unset=True, exclude={"variant_attributes_override", "stock_quantity"}
        )

        if "variant_attributes_override" in data.model_fields_set:
            override = data.variant_attributes_override
            update_data["variant_attributes_override"] = (
                {k: v.model_dump() for k, v in override.items()}
                if override
                else None
            )

        if "attribute_template_id" in update_data:
            tid = update_data["attribute_template_id"]
            if tid:
                await self.get_template(tid)

        for key, value in update_data.items():
            setattr(product, key, value)

        # Route stock_quantity to the default (first) variant
        if data.stock_quantity is not None and product.variants:
            product.variants[0].stock_quantity = data.stock_quantity

        await self.db.commit()
        await self.db.refresh(product, ["variants", "attribute_template"])
        return product

    async def delete_product(self, product_id: uuid.UUID) -> None:
        product = await self.get_product_by_id(product_id)
        await self.db.delete(product)
        await self.db.commit()

    def _resolve_variant_attributes(self, product: Product) -> dict | None:
        template_attrs = product.attribute_template.attributes if (
            product.attribute_template
        ) else None
        override = product.variant_attributes_override
        if not template_attrs and not override:
            return None
        result = dict(template_attrs or {})
        if override:
            result.update(override)
        return result

    @property
    def _stock_total(self, product: Product) -> int:
        return sum(
            v.stock_quantity for v in product.variants if v.is_active
        )

    # ── Variants ────────────────────────────────────────────────

    async def create_variant(
        self, product_id: uuid.UUID, data: VariantCreate
    ) -> ProductVariant:
        product = await self.get_product_by_id(product_id)
        variant = ProductVariant(
            product_id=product.id,
            sku=data.sku,
            price_override=data.price_override,
            stock_quantity=data.stock_quantity,
            attributes=data.attributes,
            is_active=data.is_active,
        )
        self.db.add(variant)
        await self.db.commit()
        await self.db.refresh(variant)
        return variant

    async def update_variant(
        self, variant_id: uuid.UUID, data: VariantUpdate
    ) -> ProductVariant:
        variant = await self.db.scalar(
            select(ProductVariant).where(ProductVariant.id == variant_id)
        )
        if not variant:
            raise VariantNotFound()
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(variant, key, value)
        await self.db.commit()
        await self.db.refresh(variant)
        return variant

    async def delete_variant(self, variant_id: uuid.UUID) -> None:
        variant = await self.db.scalar(
            select(ProductVariant).where(ProductVariant.id == variant_id)
        )
        if not variant:
            raise VariantNotFound()
        was_default = variant.is_default
        await self.db.delete(variant)
        await self.db.commit()
        # Promote another variant to default if needed
        if was_default:
            remaining = await self.db.scalar(
                select(ProductVariant)
                .where(ProductVariant.product_id == variant.product_id)
                .order_by(ProductVariant.created_at)
            )
            if remaining:
                remaining.is_default = True
                await self.db.commit()

    async def validate_stock(
        self, product_id: uuid.UUID, quantity: int
    ) -> Product:
        product = await self.get_product_by_id(product_id)
        total = sum(
            v.stock_quantity for v in product.variants if v.is_active
        )
        if total < quantity:
            raise InsufficientStock(product.name, total, quantity)
        return product

    async def decrement_stock(
        self, product_id: uuid.UUID, quantity: int
    ) -> Product:
        product = await self.validate_stock(product_id, quantity)
        remaining = quantity
        for v in product.variants:
            if not v.is_active or v.stock_quantity <= 0:
                continue
            take = min(remaining, v.stock_quantity)
            v.stock_quantity -= take
            remaining -= take
            if remaining == 0:
                break
        await self.db.commit()
        return product
