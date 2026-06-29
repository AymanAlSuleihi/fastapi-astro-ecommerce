import pytest
from httpx import AsyncClient

API = "/api/v1"


async def _get_admin_token(client: AsyncClient) -> str:
    resp = await client.post(
        f"{API}/admin/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    return resp.json()["access_token"]


# ── Zones ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_zone(client: AsyncClient):
    token = await _get_admin_token(client)
    resp = await client.post(
        f"{API}/shipping/zones",
        json={"name": "UK", "countries": ["GB"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "UK"
    assert data["countries"] == ["GB"]


@pytest.mark.asyncio
async def test_list_zones(client: AsyncClient):
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/shipping/zones",
        json={"name": "Europe", "countries": ["DE", "FR"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(f"{API}/shipping/zones")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_zone(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/shipping/zones",
        json={"name": "ROW", "countries": ["US", "CA", "AU"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    zone_id = create_resp.json()["id"]
    resp = await client.get(f"{API}/shipping/zones/{zone_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "ROW"


@pytest.mark.asyncio
async def test_update_zone(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/shipping/zones",
        json={"name": "OldZone", "countries": ["XX"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    zone_id = create_resp.json()["id"]

    resp = await client.patch(
        f"{API}/shipping/zones/{zone_id}",
        json={"name": "NewZone"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "NewZone"


@pytest.mark.asyncio
async def test_delete_zone(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/shipping/zones",
        json={"name": "DeleteMe", "countries": ["ZZ"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    zone_id = create_resp.json()["id"]

    resp = await client.delete(
        f"{API}/shipping/zones/{zone_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_zone_country_overlap_rejected(client: AsyncClient):
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/shipping/zones",
        json={"name": "Alpha", "countries": ["GB"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.post(
        f"{API}/shipping/zones",
        json={"name": "Beta", "countries": ["GB", "FR"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


# ── Rates ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_rate(client: AsyncClient):
    token = await _get_admin_token(client)
    zone_resp = await client.post(
        f"{API}/shipping/zones",
        json={"name": "TestZone", "countries": ["JP"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    zone_id = zone_resp.json()["id"]

    resp = await client.post(
        f"{API}/shipping/zones/{zone_id}/rates",
        json={
            "name": "Standard",
            "base_cost": 5.99,
            "free_above": 75.00,
            "min_days": 3,
            "max_days": 5,
            "priority": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Standard"
    assert data["base_cost"] == 5.99


@pytest.mark.asyncio
async def test_update_rate(client: AsyncClient):
    token = await _get_admin_token(client)
    zone_resp = await client.post(
        f"{API}/shipping/zones",
        json={"name": "RateZone", "countries": ["KR"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    zone_id = zone_resp.json()["id"]
    rate_resp = await client.post(
        f"{API}/shipping/zones/{zone_id}/rates",
        json={"name": "Express", "base_cost": 10.00, "priority": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    rate_id = rate_resp.json()["id"]

    resp = await client.patch(
        f"{API}/shipping/rates/{rate_id}",
        json={"base_cost": 12.50},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["base_cost"] == 12.50


@pytest.mark.asyncio
async def test_delete_rate(client: AsyncClient):
    token = await _get_admin_token(client)
    zone_resp = await client.post(
        f"{API}/shipping/zones",
        json={"name": "DelRateZone", "countries": ["CN"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    zone_id = zone_resp.json()["id"]
    rate_resp = await client.post(
        f"{API}/shipping/zones/{zone_id}/rates",
        json={"name": "Slow", "base_cost": 2.00, "priority": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    rate_id = rate_resp.json()["id"]

    resp = await client.delete(
        f"{API}/shipping/rates/{rate_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


# ── Calculate ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_calculate_product_based(client: AsyncClient):
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/shipping/zones",
        json={"name": "CalcZone", "countries": ["GB", "US"]},
        headers={"Authorization": f"Bearer {token}"},
    )

    product_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Calc Product",
            "slug": "calc-product",
            "price": 30.00,
            "stock_quantity": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id = product_resp.json()["id"]

    resp = await client.post(
        f"{API}/shipping/calculate",
        json={
            "country_code": "GB",
            "product_id": product_id,
            "quantity": 1,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone_name"] == "CalcZone"
    assert data["options"] == []
    assert data["subtotal"] == 30.00


@pytest.mark.asyncio
async def test_calculate_with_rates(client: AsyncClient):
    admin_token = await _get_admin_token(client)

    zone_resp = await client.post(
        f"{API}/shipping/zones",
        json={"name": "FullZone", "countries": ["FR"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    zone_id = zone_resp.json()["id"]

    await client.post(
        f"{API}/shipping/zones/{zone_id}/rates",
        json={
            "name": "Standard",
            "base_cost": 4.99,
            "free_above": 50.00,
            "min_days": 3,
            "max_days": 5,
            "priority": 10,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    await client.post(
        f"{API}/shipping/zones/{zone_id}/rates",
        json={
            "name": "Express",
            "base_cost": 9.99,
            "min_days": 1,
            "max_days": 2,
            "priority": 20,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    await client.post(
        f"{API}/shipping/zones/{zone_id}/rates",
        json={
            "name": "Inactive Rate",
            "base_cost": 1.00,
            "is_active": False,
            "priority": 30,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    product_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "FullCalc Product",
            "slug": "fullcalc-product",
            "price": 60.00,
            "stock_quantity": 10,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    product_id = product_resp.json()["id"]

    resp = await client.post(
        f"{API}/shipping/calculate",
        json={
            "country_code": "FR",
            "product_id": product_id,
            "quantity": 1,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone_name"] == "FullZone"
    assert len(data["options"]) == 2

    standard = next(o for o in data["options"] if o["name"] == "Standard")
    assert standard["is_free"] is True
    assert standard["cost"] == 0.0
    assert standard["min_days"] == 3
    assert standard["max_days"] == 5

    express = next(o for o in data["options"] if o["name"] == "Express")
    assert express["is_free"] is False
    assert express["cost"] == 9.99


@pytest.mark.asyncio
async def test_calculate_unknown_country(client: AsyncClient):
    resp = await client.post(
        f"{API}/shipping/calculate",
        json={"country_code": "XX", "quantity": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone_name"] is None
    assert data["options"] == []
