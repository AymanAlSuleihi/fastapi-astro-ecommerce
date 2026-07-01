import pytest
from httpx import AsyncClient

API = "/api/v1"


async def _get_admin_token(client: AsyncClient) -> str:
    resp = await client.post(
        f"{API}/admin/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ── Public ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_public_config_empty(client: AsyncClient):
    """Public config returns empty dict when no public settings exist."""
    resp = await client.get(f"{API}/store-config/public")
    assert resp.status_code == 200
    assert resp.json() == {}


@pytest.mark.asyncio
async def test_get_public_config_with_data(client: AsyncClient):
    """Public config returns only is_public=True settings."""
    token = await _get_admin_token(client)

    # Create a public and a private setting
    await client.post(
        f"{API}/admin/store-config",
        json={"key": "STORE_NAME", "value": "My Store", "is_public": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        f"{API}/admin/store-config",
        json={"key": "SECRET_KEY", "value": "shhh", "is_public": False},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(f"{API}/store-config/public")
    assert resp.status_code == 200
    data = resp.json()
    assert "STORE_NAME" in data
    assert data["STORE_NAME"] == "My Store"
    assert "SECRET_KEY" not in data


# ── Admin CRUD ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_setting(client: AsyncClient):
    token = await _get_admin_token(client)
    resp = await client.post(
        f"{API}/admin/store-config",
        json={"key": "CURRENCY", "value": "USD", "section": "general"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["key"] == "CURRENCY"
    assert data["value"] == "USD"
    assert data["section"] == "general"
    assert data["is_public"] is False


@pytest.mark.asyncio
async def test_create_duplicate_key(client: AsyncClient):
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/admin/store-config",
        json={"key": "DUPE", "value": "first"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.post(
        f"{API}/admin/store-config",
        json={"key": "DUPE", "value": "second"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_settings(client: AsyncClient):
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/admin/store-config",
        json={"key": "SITE_TITLE", "value": "Test Site"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(
        f"{API}/admin/store-config",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    keys = [s["key"] for s in data]
    assert "SITE_TITLE" in keys


@pytest.mark.asyncio
async def test_get_setting(client: AsyncClient):
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/admin/store-config",
        json={"key": "TAX_RATE", "value": 0.08},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(
        f"{API}/admin/store-config/TAX_RATE",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["value"] == 0.08


@pytest.mark.asyncio
async def test_get_setting_not_found(client: AsyncClient):
    token = await _get_admin_token(client)
    resp = await client.get(
        f"{API}/admin/store-config/NONEXISTENT",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_setting(client: AsyncClient):
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/admin/store-config",
        json={"key": "MOTTO", "value": "Old Motto"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.patch(
        f"{API}/admin/store-config/MOTTO",
        json={"value": "New Motto", "is_public": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["value"] == "New Motto"
    assert data["is_public"] is True


@pytest.mark.asyncio
async def test_delete_setting(client: AsyncClient):
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/admin/store-config",
        json={"key": "TEMP", "value": "delete me"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.delete(
        f"{API}/admin/store-config/TEMP",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204

    # Verify gone
    resp = await client.get(
        f"{API}/admin/store-config/TEMP",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_bulk_upsert(client: AsyncClient):
    token = await _get_admin_token(client)

    items = [
        {"key": "BULK_ONE", "value": "first", "section": "test"},
        {"key": "BULK_TWO", "value": "second", "section": "test", "is_public": True},
    ]
    resp = await client.put(
        f"{API}/admin/store-config/bulk",
        json={"settings": items},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    keys = {s["key"] for s in data}
    assert "BULK_ONE" in keys
    assert "BULK_TWO" in keys


@pytest.mark.asyncio
async def test_bulk_upsert_updates_existing(client: AsyncClient):
    token = await _get_admin_token(client)

    # Create first
    await client.post(
        f"{API}/admin/store-config",
        json={"key": "BULK_UPDATE", "value": "old"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Bulk upsert with new value
    resp = await client.put(
        f"{API}/admin/store-config/bulk",
        json={"settings": [{"key": "BULK_UPDATE", "value": "new"}]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    updated = next(s for s in data if s["key"] == "BULK_UPDATE")
    assert updated["value"] == "new"


@pytest.mark.asyncio
async def test_admin_routes_require_auth(client: AsyncClient):
    """All admin store-config routes require admin auth."""
    endpoints = [
        ("GET", "/api/v1/admin/store-config"),
        ("POST", "/api/v1/admin/store-config"),
        ("PATCH", "/api/v1/admin/store-config/TEST"),
        ("DELETE", "/api/v1/admin/store-config/TEST"),
        ("PUT", "/api/v1/admin/store-config/bulk"),
    ]
    for method, url in endpoints:
        resp = await client.request(method, url)
        assert resp.status_code == 403, f"{method} {url} should require auth"
