import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import DbDep
from src.shipping.exceptions import RateNotFound, ZoneNotFound
from src.shipping.models import ShippingRate, ShippingZone
from src.shipping.schemas import CalculateResponse, RateCreate, RateUpdate, ShippingOption


class ShippingService:
    def __init__(self, db: DbDep):
        self.db = db

    # ── Zones ──────────────────────────────────────────────────

    async def list_zones(self) -> list[ShippingZone]:
        result = await self.db.execute(
            select(ShippingZone)
            .options(selectinload(ShippingZone.rates))
            .order_by(ShippingZone.name)
        )
        return list(result.scalars().all())

    async def get_zone(self, zone_id: uuid.UUID) -> ShippingZone:
        zone = await self.db.scalar(
            select(ShippingZone)
            .where(ShippingZone.id == zone_id)
            .options(selectinload(ShippingZone.rates))
        )
        if not zone:
            raise ZoneNotFound()
        return zone

    async def create_zone(
        self, name: str, countries: list[str], is_active: bool = True
    ) -> ShippingZone:
        await self._validate_no_country_overlap(countries)
        zone = ShippingZone(name=name, countries=countries, is_active=is_active)
        self.db.add(zone)
        await self.db.commit()
        await self.db.refresh(zone)
        return zone

    async def update_zone(
        self,
        zone_id: uuid.UUID,
        name: str | None,
        countries: list[str] | None,
        is_active: bool | None,
    ) -> ShippingZone:
        zone = await self.get_zone(zone_id)
        if name is not None:
            zone.name = name
        if countries is not None:
            await self._validate_no_country_overlap(countries, exclude_zone_id=zone_id)
            zone.countries = countries
        if is_active is not None:
            zone.is_active = is_active
        await self.db.commit()
        await self.db.refresh(zone)
        return zone

    async def delete_zone(self, zone_id: uuid.UUID) -> None:
        zone = await self.get_zone(zone_id)
        await self.db.delete(zone)
        await self.db.commit()

    async def _validate_no_country_overlap(
        self, countries: list[str], exclude_zone_id: uuid.UUID | None = None
    ) -> None:
        from src.exceptions import ConflictException
        from src.shipping.constants import ShippingErrorCode

        query = select(ShippingZone).where(ShippingZone.is_active.is_(True))
        if exclude_zone_id:
            query = query.where(ShippingZone.id != exclude_zone_id)

        result = await self.db.execute(query)
        for existing in result.scalars().all():
            overlap = {c.upper() for c in countries} & {c.upper() for c in existing.countries}
            if overlap:
                raise ConflictException(
                    detail=f"Countries {overlap} already belong to zone '{existing.name}'",
                    code=ShippingErrorCode.COUNTRY_OVERLAP,
                )

    # ── Rates ──────────────────────────────────────────────────

    async def get_rate(self, rate_id: uuid.UUID) -> ShippingRate:
        rate = await self.db.scalar(select(ShippingRate).where(ShippingRate.id == rate_id))
        if not rate:
            raise RateNotFound()
        return rate

    async def create_rate(self, zone_id: uuid.UUID, data: RateCreate) -> ShippingRate:
        await self.get_zone(zone_id)
        rate = ShippingRate(zone_id=zone_id, **data.model_dump())
        self.db.add(rate)
        await self.db.commit()
        await self.db.refresh(rate)
        return rate

    async def update_rate(self, rate_id: uuid.UUID, data: RateUpdate) -> ShippingRate:
        rate = await self.get_rate(rate_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(rate, key, value)
        await self.db.commit()
        await self.db.refresh(rate)
        return rate

    async def delete_rate(self, rate_id: uuid.UUID) -> None:
        rate = await self.get_rate(rate_id)
        await self.db.delete(rate)
        await self.db.commit()

    # ── Calculate ──────────────────────────────────────────────

    async def find_zone_for_country(self, country_code: str) -> ShippingZone | None:
        result = await self.db.execute(
            select(ShippingZone)
            .where(ShippingZone.is_active.is_(True))
            .options(selectinload(ShippingZone.rates))
        )
        country_upper = country_code.upper()
        for zone in result.scalars().all():
            if country_upper in (c.upper() for c in zone.countries):
                return zone
        return None

    async def calculate_options(
        self,
        country_code: str,
        cart_subtotal: float,
        cart_weight_kg: float | None = None,
    ) -> CalculateResponse:
        zone = await self.find_zone_for_country(country_code)

        if not zone:
            return CalculateResponse(
                subtotal=cart_subtotal,
                options=[],
                zone_name=None,
            )

        options: list[ShippingOption] = []
        for rate in sorted(zone.rates, key=lambda r: -r.priority):
            if not rate.is_active:
                continue

            if rate.min_subtotal is not None and cart_subtotal < rate.min_subtotal:
                continue

            if (
                rate.max_weight_kg is not None
                and cart_weight_kg is not None
                and cart_weight_kg > rate.max_weight_kg
            ):
                continue

            is_free = rate.free_above is not None and cart_subtotal >= rate.free_above
            options.append(
                ShippingOption(
                    rate_id=rate.id,
                    name=rate.name,
                    description=rate.description,
                    cost=0.0 if is_free else float(rate.base_cost),
                    is_free=is_free,
                    min_days=rate.min_days,
                    max_days=rate.max_days,
                )
            )

        return CalculateResponse(
            subtotal=cart_subtotal,
            options=options,
            zone_name=zone.name,
        )
