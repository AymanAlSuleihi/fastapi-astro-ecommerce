import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from src.admin.dependencies import CurrentAdminDep
from src.config import settings
from src.currencies.service import ExchangeRateService
from src.database import DbDep
from src.products.dependencies import (
    ValidCategorySlugDep,
    ValidProductIdDep,
    ValidProductSlugDep,
)
from src.products.schemas import (
    AttributeTemplateCreate,
    AttributeTemplateRead,
    AttributeTemplateUpdate,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    ProductCreate,
    ProductList,
    ProductRead,
    ProductUpdate,
    VariantCreate,
    VariantRead,
    VariantUpdate,
)
from src.products.service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


async def _product_to_read(
    product, service: ProductService, db: DbDep, currency: str | None = None
) -> ProductRead:
    total_stock = sum(v.stock_quantity for v in product.variants if v.is_active)
    display_price = None
    display_currency = settings.DEFAULT_CURRENCY

    if currency and currency != settings.DEFAULT_CURRENCY:
        rate_service = ExchangeRateService(db)
        rate = await rate_service.get_rate(settings.DEFAULT_CURRENCY, currency)
        if rate:
            display_price = round(float(product.price) * rate, 2)
            display_currency = currency

    return ProductRead(
        id=product.id,
        name=product.name,
        slug=product.slug,
        description=product.description,
        price=product.price,
        currency=display_currency,
        display_price=display_price,
        stock_quantity=total_stock,
        category_id=product.category_id,
        is_active=product.is_active,
        attribute_template_id=product.attribute_template_id,
        variant_attributes=service._resolve_variant_attributes(product),
        variants=[VariantRead.model_validate(v) for v in product.variants],
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


# ── Categories ──────────────────────────────────────────────────


@router.get("/categories", response_model=list[CategoryRead])
async def list_categories(db: DbDep):
    service = ProductService(db)
    categories = await service.get_categories()
    return [
        CategoryRead(
            id=c.id,
            name=c.name,
            slug=c.slug,
            parent_id=c.parent_id,
            children=[],  # root categories have no children in listing
            created_at=c.created_at,
        )
        for c in categories
    ]


@router.get("/categories/{slug}", response_model=CategoryRead)
async def get_category(category: ValidCategorySlugDep):
    return CategoryRead(
        id=category.id,
        name=category.name,
        slug=category.slug,
        parent_id=category.parent_id,
        children=[],  # loaded children if needed
        created_at=category.created_at,
    )


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
    cat = await service.create_category(data.name, data.slug, data.parent_id)
    return CategoryRead(
        id=cat.id,
        name=cat.name,
        slug=cat.slug,
        parent_id=cat.parent_id,
        children=[],
        created_at=cat.created_at,
    )


@router.patch("/categories/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ProductService(db)
    cat = await service.update_category(category_id, data.name, data.slug)
    return CategoryRead(
        id=cat.id,
        name=cat.name,
        slug=cat.slug,
        parent_id=cat.parent_id,
        children=[],
        created_at=cat.created_at,
    )


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ProductService(db)
    await service.delete_category(category_id)


# ── Attribute Templates ───────────────────────────────────────


@router.get("/attribute-templates", response_model=list[AttributeTemplateRead])
async def list_templates(db: DbDep):
    service = ProductService(db)
    return await service.list_templates()


@router.get(
    "/attribute-templates/{template_id}",
    response_model=AttributeTemplateRead,
)
async def get_template(template_id: uuid.UUID, db: DbDep):
    service = ProductService(db)
    return await service.get_template(template_id)


@router.post(
    "/attribute-templates",
    response_model=AttributeTemplateRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(data: AttributeTemplateCreate, db: DbDep, _admin: CurrentAdminDep):
    service = ProductService(db)
    return await service.create_template(data.name, data.attributes)


@router.patch(
    "/attribute-templates/{template_id}",
    response_model=AttributeTemplateRead,
)
async def update_template(
    template_id: uuid.UUID,
    data: AttributeTemplateUpdate,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ProductService(db)
    return await service.update_template(template_id, data.name, data.attributes)


@router.delete(
    "/attribute-templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_template(template_id: uuid.UUID, db: DbDep, _admin: CurrentAdminDep):
    service = ProductService(db)
    await service.delete_template(template_id)


# ── Products ────────────────────────────────────────────────────


@router.get("/", response_model=ProductList)
async def list_products(
    db: DbDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    search: str | None = None,
    currency: str | None = Query(default=None, min_length=3, max_length=3),
):
    service = ProductService(db)
    items, total = await service.get_products(
        page=page,
        page_size=page_size,
        category_slug=category,
        search=search,
    )
    converted = [await _product_to_read(p, service, db, currency) for p in items]
    return ProductList(
        items=converted,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{slug}", response_model=ProductRead)
async def get_product(
    product: ValidProductSlugDep,
    db: DbDep,
    currency: str | None = Query(default=None, min_length=3, max_length=3),
):
    service = ProductService(db)
    return await _product_to_read(product, service, db, currency)


@router.post(
    "/",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(data: ProductCreate, db: DbDep, _admin: CurrentAdminDep):
    service = ProductService(db)
    product = await service.create_product(data)
    return await _product_to_read(product, service, db)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    data: ProductUpdate,
    product: ValidProductIdDep,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ProductService(db)
    updated = await service.update_product(product.id, data)
    return await _product_to_read(updated, service, db)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product: ValidProductIdDep,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ProductService(db)
    await service.delete_product(product.id)


# ── Variants ──────────────────────────────────────────────────


@router.post(
    "/{product_id}/variants",
    response_model=VariantRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_variant(
    product_id: uuid.UUID,
    data: VariantCreate,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ProductService(db)
    return await service.create_variant(product_id, data)


@router.patch("/variants/{variant_id}", response_model=VariantRead)
async def update_variant(
    variant_id: uuid.UUID,
    data: VariantUpdate,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ProductService(db)
    return await service.update_variant(variant_id, data)


@router.delete("/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(variant_id: uuid.UUID, db: DbDep, _admin: CurrentAdminDep):
    service = ProductService(db)
    await service.delete_variant(variant_id)
