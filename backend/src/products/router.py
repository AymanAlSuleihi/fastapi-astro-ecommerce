from typing import Annotated

from fastapi import APIRouter, Query, status

from src.admin.dependencies import CurrentAdminDep
from src.database import DbDep
from src.products.dependencies import (
    ValidCategorySlugDep,
    ValidProductIdDep,
    ValidProductSlugDep,
)
from src.products.schemas import (
    CategoryCreate,
    CategoryRead,
    ProductCreate,
    ProductList,
    ProductRead,
    ProductUpdate,
)
from src.products.service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


# ── Categories ──────────────────────────────────────────────────


@router.get("/categories", response_model=list[CategoryRead])
async def list_categories(db: DbDep):
    service = ProductService(db)
    return await service.get_categories()


@router.get("/categories/{slug}", response_model=CategoryRead)
async def get_category(category: ValidCategorySlugDep):
    return category


@router.post(
    "/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    data: CategoryCreate,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ProductService(db)
    return await service.create_category(data.name, data.slug, data.parent_id)


# ── Products ────────────────────────────────────────────────────


@router.get("/", response_model=ProductList)
async def list_products(
    db: DbDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    search: str | None = None,
):
    service = ProductService(db)
    items, total = await service.get_products(
        page=page,
        page_size=page_size,
        category_slug=category,
        search=search,
    )
    return ProductList(
        items=[ProductRead.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{slug}", response_model=ProductRead)
async def get_product(product: ValidProductSlugDep):
    return product


@router.post(
    "/",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(data: ProductCreate, db: DbDep, _admin: CurrentAdminDep):
    service = ProductService(db)
    return await service.create_product(data)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    data: ProductUpdate,
    product: ValidProductIdDep,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ProductService(db)
    return await service.update_product(product.id, data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product: ValidProductIdDep,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ProductService(db)
    await service.delete_product(product.id)
