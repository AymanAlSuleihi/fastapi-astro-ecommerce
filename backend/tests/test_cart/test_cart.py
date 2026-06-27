import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_cart_empty(client: AsyncClient):
    resp = await client.get("/cart/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert "id" in data


@pytest.mark.asyncio
async def test_get_cart_with_session(client: AsyncClient):
    resp = await client.get("/cart/", cookies={"cart_session": "test-session-123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
