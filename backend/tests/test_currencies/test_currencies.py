"""Currency tests — exchange rates, product display, order currency."""

import os

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.currencies.service import ExchangeRateService

API = "/api/v1"

TEST_DB = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://ecommerce:ecommerce@localhost:5432/ecommerce_test",
)


@pytest_asyncio.fixture
async def db_session():
    """Fixture that provides a clean DB session with its own engine."""
    eng = create_async_engine(TEST_DB, echo=False)
    factory = async_sessionmaker(eng, expire_on_commit=False)
    async with factory() as session:
        yield session
    await eng.dispose()


# ── Service (DB-level) ──────────────────────────────────────


@pytest.mark.asyncio
async def test_get_rate_same_currency(db_session):
    """get_rate returns 1.0 for same currency."""
    service = ExchangeRateService(db_session)
    rate = await service.get_rate("USD", "USD")
    assert rate == 1.0


@pytest.mark.asyncio
async def test_get_rate_found(db_session):
    """get_rate returns the stored rate."""
    from sqlalchemy import select

    from src.currencies.models import ExchangeRate

    existing = await db_session.scalar(
        select(ExchangeRate).where(
            ExchangeRate.base_currency == "USD",
            ExchangeRate.target_currency == "EUR",
        )
    )
    if not existing:
        rate = ExchangeRate(base_currency="USD", target_currency="EUR", rate=0.92)
        db_session.add(rate)
        await db_session.commit()

    service = ExchangeRateService(db_session)
    result = await service.get_rate("USD", "EUR")
    assert result == 0.92


@pytest.mark.asyncio
async def test_get_rate_not_found(db_session):
    """get_rate returns None when no rate exists."""
    service = ExchangeRateService(db_session)
    result = await service.get_rate("USD", "XYZ")
    assert result is None


@pytest.mark.asyncio
async def test_convert_async(db_session):
    """convert_async converts amount using stored rate."""
    from sqlalchemy import select as sa_select

    from src.currencies.models import ExchangeRate

    existing = await db_session.scalar(
        sa_select(ExchangeRate).where(
            ExchangeRate.base_currency == "USD",
            ExchangeRate.target_currency == "EUR",
        )
    )
    if not existing:
        rate = ExchangeRate(base_currency="USD", target_currency="EUR", rate=0.92)
        db_session.add(rate)
        await db_session.commit()

    service = ExchangeRateService(db_session)
    result = await service.convert_async(100.0, "USD", "EUR")
    assert result == 92.00


@pytest.mark.asyncio
async def test_convert_async_no_rate(db_session):
    """convert_async returns None when no rate exists."""
    service = ExchangeRateService(db_session)
    result = await service.convert_async(100.0, "USD", "XYZ")
    assert result is None


# ── Helpers ─────────────────────────────────────────────────


async def _get_admin_token(client: AsyncClient) -> str:
    resp = await client.post(
        f"{API}/admin/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    return resp.json()["access_token"]


async def _seed_rate(base: str, target: str, rate_val: float) -> None:
    from sqlalchemy import select

    from src.currencies.models import ExchangeRate

    eng = create_async_engine(TEST_DB, echo=False)
    factory = async_sessionmaker(eng, expire_on_commit=False)
    async with factory() as session:
        existing = await session.scalar(
            select(ExchangeRate).where(
                ExchangeRate.base_currency == base,
                ExchangeRate.target_currency == target,
            )
        )
        if not existing:
            er = ExchangeRate(base_currency=base, target_currency=target, rate=rate_val)
            session.add(er)
            await session.commit()
    await eng.dispose()


# ── Products with currency ──────────────────────────────────


@pytest.mark.asyncio
async def test_product_list_with_currency(client: AsyncClient):
    """Product list with ?currency=EUR returns display_price."""
    await _seed_rate("USD", "EUR", 0.92)

    token = await _get_admin_token(client)
    await client.post(
        f"{API}/products/",
        json={
            "name": "Currency Product",
            "slug": "currency-product",
            "price": 50.00,
            "stock_quantity": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(f"{API}/products/?currency=EUR")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) >= 1
    product = data["items"][0]
    assert product["currency"] == "EUR"
    assert product["display_price"] == 46.00  # 50 * 0.92
    assert product["price"] == 50.00  # base price unchanged


@pytest.mark.asyncio
async def test_product_list_default_currency(client: AsyncClient):
    """Product list without currency param shows USD, no display_price."""
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/products/",
        json={
            "name": "Default Currency Product",
            "slug": "default-currency-product",
            "price": 30.00,
            "stock_quantity": 5,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(f"{API}/products/")
    assert resp.status_code == 200
    product = resp.json()["items"][0]
    assert product["currency"] == "USD"
    assert product["display_price"] is None


# ── Orders with currency ────────────────────────────────────


@pytest.mark.asyncio
async def test_order_with_currency(client: AsyncClient):
    """Order created with EUR currency stores base amounts."""
    await _seed_rate("USD", "EUR", 0.85)

    token = await _get_admin_token(client)
    prod_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "EUR Order Item",
            "slug": "eur-order-item",
            "price": 100.00,
            "stock_quantity": 5,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id = prod_resp.json()["id"]

    # Register and login customer
    customer_resp = await client.post(
        f"{API}/customers/register",
        json={
            "email": "eurcust@example.com",
            "password": "password123",
            "first_name": "Eur",
            "last_name": "Customer",
        },
    )
    customer_id = customer_resp.json()["id"]
    cust_token = (
        await client.post(
            f"{API}/customers/login",
            json={"email": "eurcust@example.com", "password": "password123"},
        )
    ).json()["access_token"]

    # Add to cart
    await client.post(
        f"{API}/cart/items",
        json={"product_id": product_id, "quantity": 1},
        headers={"Authorization": f"Bearer {cust_token}"},
    )

    # Create order in EUR
    order_resp = await client.post(
        f"{API}/orders/",
        json={"currency": "EUR"},
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert order_resp.status_code == 201
    order = order_resp.json()

    assert order["currency"] == "EUR"
    assert order["exchange_rate"] == 0.85
    assert order["total_amount"] == 85.00
    assert order["base_total_amount"] == 100.00
    assert order["base_subtotal"] == 100.00
    assert order["customer_id"] == customer_id


@pytest.mark.asyncio
async def test_order_default_currency(client: AsyncClient):
    """Order without explicit currency defaults to USD, no base amounts."""
    token = await _get_admin_token(client)
    prod_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "USD Order Item",
            "slug": "usd-order-item",
            "price": 50.00,
            "stock_quantity": 5,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id = prod_resp.json()["id"]

    await client.post(
        f"{API}/customers/register",
        json={
            "email": "usdcust@example.com",
            "password": "password123",
            "first_name": "Usd",
            "last_name": "Customer",
        },
    )
    cust_token = (
        await client.post(
            f"{API}/customers/login",
            json={"email": "usdcust@example.com", "password": "password123"},
        )
    ).json()["access_token"]

    await client.post(
        f"{API}/cart/items",
        json={"product_id": product_id, "quantity": 2},
        headers={"Authorization": f"Bearer {cust_token}"},
    )

    order_resp = await client.post(
        f"{API}/orders/",
        json={},
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert order_resp.status_code == 201
    order = order_resp.json()

    assert order["currency"] == "USD"
    assert order["exchange_rate"] is None
    assert order["total_amount"] == 100.00  # 2 * 50
    assert order["base_total_amount"] is None
