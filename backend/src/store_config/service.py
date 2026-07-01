from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.database import DbDep
from src.logging_config import get_logger
from src.store_config.exceptions import StoreConfigKeyAlreadyExists, StoreConfigKeyNotFound
from src.store_config.models import StoreSetting
from src.store_config.schemas import StoreSettingBulkItem, StoreSettingCreate, StoreSettingUpdate

logger = get_logger(__name__)


class StoreConfigService:
    def __init__(self, db: DbDep):
        self.db = db

    async def get_all(self) -> list[StoreSetting]:
        result = await self.db.execute(
            select(StoreSetting).order_by(StoreSetting.section, StoreSetting.key)
        )
        return list(result.scalars().all())

    async def get_public(self) -> dict[str, object]:
        """Return a flat key→value dict of all public settings."""
        result = await self.db.execute(
            select(StoreSetting).where(StoreSetting.is_public.is_(True)).order_by(StoreSetting.key)
        )
        return {row.key: row.value for row in result.scalars().all()}

    async def get_by_key(self, key: str) -> StoreSetting:
        setting = await self.db.scalar(select(StoreSetting).where(StoreSetting.key == key))
        if not setting:
            raise StoreConfigKeyNotFound(key)
        return setting

    async def create(self, data: StoreSettingCreate) -> StoreSetting:
        existing = await self.db.scalar(select(StoreSetting).where(StoreSetting.key == data.key))
        if existing:
            raise StoreConfigKeyAlreadyExists(data.key)

        setting = StoreSetting(**data.model_dump())
        self.db.add(setting)
        await self.db.commit()
        await self.db.refresh(setting)
        logger.info("store_config_created", key=data.key, section=data.section)
        return setting

    async def update(self, key: str, data: StoreSettingUpdate) -> StoreSetting:
        setting = await self.get_by_key(key)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(setting, field, value)
        await self.db.commit()
        await self.db.refresh(setting)
        logger.info("store_config_updated", key=key)
        return setting

    async def delete(self, key: str) -> None:
        setting = await self.get_by_key(key)
        await self.db.delete(setting)
        await self.db.commit()
        logger.info("store_config_deleted", key=key)

    async def bulk_set(self, items: list[StoreSettingBulkItem]) -> list[StoreSetting]:
        """Upsert multiple settings at once. Returns all settings after upsert."""
        for item in items:
            stmt = (
                pg_insert(StoreSetting)
                .values(**item.model_dump())
                .on_conflict_do_update(
                    constraint="store_setting_key_key",
                    set_={
                        "value": item.value,
                        "description": item.description,
                        "is_public": item.is_public,
                        "section": item.section,
                    },
                )
            )
            await self.db.execute(stmt)

        await self.db.commit()

        # Return all settings
        result = await self.db.execute(
            select(StoreSetting).order_by(StoreSetting.section, StoreSetting.key)
        )
        return list(result.scalars().all())
