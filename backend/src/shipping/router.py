import uuid

from fastapi import APIRouter, status

from src.admin.dependencies import CurrentAdminDep
from src.database import DbDep
from src.shipping.schemas import (
    CalculateRequest,
    CalculateResponse,
    RateCreate,
    RateRead,
    RateUpdate,
    ZoneCreate,
    ZoneRead,
    ZoneUpdate,
)
from src.shipping.service import ShippingService

router = APIRouter(prefix="/shipping", tags=["shipping"])


# ── Zones ──────────────────────────────────────────────────────


@router.get("/zones", response_model=list[ZoneRead])
async def list_zones(db: DbDep):
    service = ShippingService(db)
    return await service.list_zones()


@router.get("/zones/{zone_id}", response_model=ZoneRead)
async def get_zone(zone_id: uuid.UUID, db: DbDep):
    service = ShippingService(db)
    return await service.get_zone(zone_id)


@router.post(
    "/zones",
    response_model=ZoneRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_zone(
    data: ZoneCreate, db: DbDep, _admin: CurrentAdminDep
):
    service = ShippingService(db)
    return await service.create_zone(data.name, data.countries, data.is_active)


@router.patch("/zones/{zone_id}", response_model=ZoneRead)
async def update_zone(
    zone_id: uuid.UUID,
    data: ZoneUpdate,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ShippingService(db)
    return await service.update_zone(
        zone_id, data.name, data.countries, data.is_active
    )


@router.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    zone_id: uuid.UUID, db: DbDep, _admin: CurrentAdminDep
):
    service = ShippingService(db)
    await service.delete_zone(zone_id)


# ── Rates ──────────────────────────────────────────────────────


@router.post(
    "/zones/{zone_id}/rates",
    response_model=RateRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_rate(
    zone_id: uuid.UUID,
    data: RateCreate,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ShippingService(db)
    return await service.create_rate(zone_id, data)


@router.patch("/rates/{rate_id}", response_model=RateRead)
async def update_rate(
    rate_id: uuid.UUID,
    data: RateUpdate,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ShippingService(db)
    return await service.update_rate(rate_id, data)


@router.delete("/rates/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate(
    rate_id: uuid.UUID, db: DbDep, _admin: CurrentAdminDep
):
    service = ShippingService(db)
    await service.delete_rate(rate_id)


# ── Calculate ──────────────────────────────────────────────────


@router.post("/calculate", response_model=CalculateResponse)
async def calculate_shipping(
    data: CalculateRequest,
    db: DbDep,
):
    service = ShippingService(db)

    if data.product_id is not None:
        from src.products.service import ProductService

        product_service = ProductService(db)
        product = await product_service.get_product_by_id(data.product_id)
        subtotal = float(product.price) * data.quantity
        total_weight = None
        if product.variants:
            default = next(
                (v for v in product.variants if v.is_default),
                product.variants[0],
            )
            if default.weight_kg is not None:
                total_weight = default.weight_kg * data.quantity
        return await service.calculate_options(
            data.country_code, subtotal, total_weight
        )

    return CalculateResponse(subtotal=0.0, options=[], zone_name=None)
