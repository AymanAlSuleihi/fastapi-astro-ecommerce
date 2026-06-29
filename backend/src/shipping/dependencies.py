from fastapi import Depends
from sqlalchemy import select

from src.database import DbDep
from src.shipping.exceptions import RateNotFound, ZoneNotFound
from src.shipping.models import ShippingRate, ShippingZone


async def valid_zone_id(zone_id: str, db: DbDep) -> ShippingZone:
    zone = await db.scalar(
        select(ShippingZone).where(ShippingZone.id == zone_id)
    )
    if not zone:
        raise ZoneNotFound()
    return zone


async def valid_rate_id(rate_id: str, db: DbDep) -> ShippingRate:
    rate = await db.scalar(
        select(ShippingRate).where(ShippingRate.id == rate_id)
    )
    if not rate:
        raise RateNotFound()
    return rate


ValidZoneIdDep = Depends(valid_zone_id)
ValidRateIdDep = Depends(valid_rate_id)
