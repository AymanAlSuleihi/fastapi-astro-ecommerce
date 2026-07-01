"""Exchange rate service — fetch, store, convert."""

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.currencies.models import ExchangeRate
from src.database import DbDep


class ExchangeRateService:
    def __init__(self, db: DbDep):
        self.db = db

    async def get_rate(self, base_currency: str, target_currency: str) -> float | None:
        if base_currency == target_currency:
            return 1.0
        rate = await self.db.scalar(
            select(ExchangeRate.rate).where(
                ExchangeRate.base_currency == base_currency.upper(),
                ExchangeRate.target_currency == target_currency.upper(),
            )
        )
        return float(rate) if rate else None

    def convert(self, amount: float, base_currency: str, target_currency: str) -> float:
        """Placeholder — rate must be fetched separately for async."""
        return amount

    async def convert_async(
        self, amount: float, base_currency: str, target_currency: str
    ) -> float | None:
        rate = await self.get_rate(base_currency, target_currency)
        if rate is None:
            return None
        return round(amount * rate, 2)

    async def fetch_live_rates(self, base_currency: str) -> int:
        """Fetch live rates from exchangerate-api.com. Returns count of rates stored."""
        url = f"https://api.exchangerate-api.com/v4/latest/{base_currency.upper()}"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return 0

        rates = data.get("rates", {})
        count = 0
        for target, rate in rates.items():
            if target == base_currency.upper():
                continue
            stmt = (
                pg_insert(ExchangeRate)
                .values(
                    base_currency=base_currency.upper(),
                    target_currency=target,
                    rate=rate,
                )
                .on_conflict_do_update(
                    constraint="exchange_rate_base_currency_target_currency_key",
                    set_={"rate": rate},
                )
            )
            await self.db.execute(stmt)
            count += 1

        await self.db.commit()
        return count
