import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.database import DbDep
from src.products.exceptions import CategoryNotFound, InsufficientStock, ProductNotFound
from src.products.models import Category, Product
from src.products.schemas import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, db: DbDep):
        self.db = db

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
        query = select(Product)
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
        product = await self.db.scalar(select(Product).where(Product.slug == slug))
        if not product:
            raise ProductNotFound()
        return product

    async def get_product_by_id(self, product_id: uuid.UUID) -> Product:
        product = await self.db.scalar(select(Product).where(Product.id == product_id))
        if not product:
            raise ProductNotFound()
        return product

    async def create_product(self, data: ProductCreate) -> Product:
        if data.category_id:
            cat = await self.db.scalar(select(Category).where(Category.id == data.category_id))
            if not cat:
                raise CategoryNotFound()

        product = Product(**data.model_dump())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update_product(self, product_id: uuid.UUID, data: ProductUpdate) -> Product:
        product = await self.get_product_by_id(product_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(product, key, value)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete_product(self, product_id: uuid.UUID) -> None:
        product = await self.get_product_by_id(product_id)
        await self.db.delete(product)
        await self.db.commit()

    async def validate_stock(self, product_id: uuid.UUID, quantity: int) -> Product:
        product = await self.get_product_by_id(product_id)
        if product.stock_quantity < quantity:
            raise InsufficientStock(product.name, product.stock_quantity, quantity)
        return product

    async def decrement_stock(self, product_id: uuid.UUID, quantity: int) -> Product:
        product = await self.validate_stock(product_id, quantity)
        product.stock_quantity -= quantity
        await self.db.commit()
        return product
