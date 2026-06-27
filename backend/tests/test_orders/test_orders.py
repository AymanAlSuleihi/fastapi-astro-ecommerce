import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_order_empty_cart(client: AsyncClient):
    # Register and login
    resp = await client.post(
        "/auth/register",
        json={
            "email": "orderuser@example.com",
            "password": "password123",
            "first_name": "Order",
            "last_name": "User",
        },
    )
    login_resp = await client.post(
        "/auth/login",
        json={"email": "orderuser@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    resp = await client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400  # empty cart


@pytest.mark.asyncio
async def test_list_orders_empty(client: AsyncClient):
    resp = await client.post(
        "/auth/register",
        json={
            "email": "orderlist@example.com",
            "password": "password123",
            "first_name": "OrderList",
            "last_name": "User",
        },
    )
    login_resp = await client.post(
        "/auth/login",
        json={"email": "orderlist@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    resp = await client.get(
        "/orders/", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json() == []
