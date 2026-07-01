from fastapi import APIRouter, status

from src.admin.dependencies import CurrentAdminDep
from src.database import DbDep
from src.store_config.schemas import (
    StoreSettingBulkUpdate,
    StoreSettingCreate,
    StoreSettingRead,
    StoreSettingUpdate,
)
from src.store_config.service import StoreConfigService

router = APIRouter(tags=["store_config"])


# ── Public ──────────────────────────────────────────────────


@router.get("/store-config/public")
async def get_public_config(db: DbDep):
    """Return all public store settings as a flat key→value map."""
    service = StoreConfigService(db)
    return await service.get_public()


# ── Admin ───────────────────────────────────────────────────

_admin_router = APIRouter(prefix="/admin/store-config", tags=["store_config"])

# Alias for external import
admin_router = _admin_router


@_admin_router.get("", response_model=list[StoreSettingRead])
async def list_settings(db: DbDep, _admin: CurrentAdminDep):
    service = StoreConfigService(db)
    return await service.get_all()


@_admin_router.get("/{key}", response_model=StoreSettingRead)
async def get_setting(key: str, db: DbDep, _admin: CurrentAdminDep):
    service = StoreConfigService(db)
    return await service.get_by_key(key)


@_admin_router.post("", response_model=StoreSettingRead, status_code=status.HTTP_201_CREATED)
async def create_setting(data: StoreSettingCreate, db: DbDep, _admin: CurrentAdminDep):
    service = StoreConfigService(db)
    return await service.create(data)


@_admin_router.patch("/{key}", response_model=StoreSettingRead)
async def update_setting(key: str, data: StoreSettingUpdate, db: DbDep, _admin: CurrentAdminDep):
    service = StoreConfigService(db)
    return await service.update(key, data)


@_admin_router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(key: str, db: DbDep, _admin: CurrentAdminDep):
    service = StoreConfigService(db)
    await service.delete(key)


@_admin_router.put("/bulk", response_model=list[StoreSettingRead])
async def bulk_update_settings(data: StoreSettingBulkUpdate, db: DbDep, _admin: CurrentAdminDep):
    service = StoreConfigService(db)
    return await service.bulk_set(data.settings)
