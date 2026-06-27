import uuid
from typing import Annotated

from fastapi import Depends, Path
from sqlalchemy import select

from src.database import DbDep
from src.products.exceptions import CategoryNotFound, ProductNotFound
from src.products.models import Category, Product


async def valid_category_by_slug(
    slug: Annotated[str, Path(description="Category slug")],
    db: DbDep,
) -> Category:
    cat = await db.scalar(select(Category).where(Category.slug == slug))
    if not cat:
        raise CategoryNotFound()
    return cat


async def valid_product_by_slug(
    slug: Annotated[str, Path(description="Product slug")],
    db: DbDep,
) -> Product:
    product = await db.scalar(select(Product).where(Product.slug == slug))
    if not product:
        raise ProductNotFound()
    return product


async def valid_product_by_id(
    product_id: Annotated[uuid.UUID, Path(description="Product ID")],
    db: DbDep,
) -> Product:
    product = await db.scalar(select(Product).where(Product.id == product_id))
    if not product:
        raise ProductNotFound()
    return product


async def valid_category_by_id(
    category_id: Annotated[uuid.UUID, Path(description="Category ID")],
    db: DbDep,
) -> Category:
    cat = await db.scalar(select(Category).where(Category.id == category_id))
    if not cat:
        raise CategoryNotFound()
    return cat


ValidCategorySlugDep = Annotated[Category, Depends(valid_category_by_slug)]
ValidProductSlugDep = Annotated[Product, Depends(valid_product_by_slug)]
ValidProductIdDep = Annotated[Product, Depends(valid_product_by_id)]
