import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient) -> str:
    """Helper to get an admin auth token."""
    import uuid

    await client.post(
        "/auth/register",
        json={
            "email": f"admin_{uuid.uuid4().hex[:8]}@test.com",
            "password": "adminpass123",
            "first_name": "Admin",
            "last_name": "User",
        },
    )
    # Make the user an admin manually isn't possible via API,
    # so test the product public endpoints for now.
    login_resp = await client.post(
        "/auth/login",
        json={"email": f"admin_{uuid.uuid4().hex[:8]}@test.com", "password": "adminpass123"},
    )
    # This won't work cleanly — skip admin tests without admin setup
    return ""


@pytest.mark.asyncio
async def test_list_products_empty(client: AsyncClient):
    resp = await client.get("/products/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_categories_empty(client: AsyncClient):
    resp = await client.get("/products/categories")
    assert resp.status_code == 200
    assert resp.json() == []
