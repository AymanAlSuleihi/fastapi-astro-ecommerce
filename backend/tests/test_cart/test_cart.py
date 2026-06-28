import pytest
from httpx import AsyncClient

API = "/api/v1"


async def _get_admin_token(client: AsyncClient) -> str:
    resp = await client.post(
        f"{API}/admin/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_get_cart_empty(client: AsyncClient):
    resp = await client.get(f"{API}/cart/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert "id" in data


@pytest.mark.asyncio
async def test_get_cart_with_session(client: AsyncClient):
    resp = await client.get(f"{API}/cart/", cookies={"cart_session": "test-session-123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


@pytest.mark.asyncio
async def test_add_item_to_cart(client: AsyncClient):
    token = await _get_admin_token(client)
    # Create a product first
    create_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Cart Test Ring",
            "slug": "cart-test-ring",
            "price": 99.99,
            "stock_quantity": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id = create_resp.json()["id"]

    resp = await client.post(
        f"{API}/cart/items",
        json={"product_id": product_id, "quantity": 2},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_cart_persists_across_requests(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Persist Ring",
            "slug": "persist-ring",
            "price": 50.00,
            "stock_quantity": 5,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201


@pytest.mark.asyncio
async def test_update_cart_item_quantity(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Update Qty Ring",
            "slug": "update-qty-ring",
            "price": 25.00,
            "stock_quantity": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id = create_resp.json()["id"]

    # Add item
    await client.post(f"{API}/cart/items", json={"product_id": product_id, "quantity": 2})
    # Update quantity
    resp = await client.patch(
        f"{API}/cart/items/{product_id}",
        json={"quantity": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 5


@pytest.mark.asyncio
async def test_update_cart_item_quantity_zero_removes(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Zero Qty Ring",
            "slug": "zero-qty-ring",
            "price": 10.00,
            "stock_quantity": 5,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id = create_resp.json()["id"]

    await client.post(f"{API}/cart/items", json={"product_id": product_id, "quantity": 1})
    resp = await client.patch(
        f"{API}/cart/items/{product_id}",
        json={"quantity": 0},
    )
    assert resp.status_code == 200
    assert resp.json()["items"] == []


@pytest.mark.asyncio
async def test_remove_cart_item(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Remove Me Ring",
            "slug": "remove-me-ring",
            "price": 15.00,
            "stock_quantity": 5,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id = create_resp.json()["id"]

    await client.post(f"{API}/cart/items", json={"product_id": product_id, "quantity": 1})
    resp = await client.delete(f"{API}/cart/items/{product_id}")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


@pytest.mark.asyncio
async def test_add_same_item_increments_quantity(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Stack Ring",
            "slug": "stack-ring",
            "price": 30.00,
            "stock_quantity": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id = create_resp.json()["id"]

    await client.post(f"{API}/cart/items", json={"product_id": product_id, "quantity": 2})
    resp = await client.post(f"{API}/cart/items", json={"product_id": product_id, "quantity": 3})
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 5


@pytest.mark.asyncio
async def test_cart_merges_on_login(client: AsyncClient):
    """Anonymous cart merges into user cart when authenticated."""
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Merge Ring",
            "slug": "merge-ring",
            "price": 40.00,
            "stock_quantity": 5,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id = create_resp.json()["id"]

    # Add item anonymously
    await client.post(f"{API}/cart/items", json={"product_id": product_id, "quantity": 2})

    # Register and login as customer
    await client.post(
        f"{API}/customers/register",
        json={
            "email": "merger@example.com",
            "password": "password123",
            "first_name": "Merge",
            "last_name": "Test",
        },
    )
    login_resp = await client.post(
        f"{API}/customers/login",
        json={"email": "merger@example.com", "password": "password123"},
    )
    cust_token = login_resp.json()["access_token"]

    # Get cart with auth — should merge
    resp = await client.get(
        f"{API}/cart/",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["customer_id"] is not None
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_user_gets_own_cart(client: AsyncClient):
    """Authenticated user gets their customer-linked cart."""
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "User Cart Ring",
            "slug": "user-cart-ring",
            "price": 60.00,
            "stock_quantity": 5,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id = create_resp.json()["id"]

    # Register & login
    await client.post(
        f"{API}/customers/register",
        json={
            "email": "usercart@example.com",
            "password": "password123",
            "first_name": "User",
            "last_name": "Cart",
        },
    )
    login_resp = await client.post(
        f"{API}/customers/login",
        json={"email": "usercart@example.com", "password": "password123"},
    )
    cust_token = login_resp.json()["access_token"]

    # Add item while authenticated
    resp = await client.post(
        f"{API}/cart/items",
        json={"product_id": product_id, "quantity": 1},
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["customer_id"] is not None
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_clear_cart(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Clear Cart Ring",
            "slug": "clear-cart-ring",
            "price": 20.00,
            "stock_quantity": 5,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id = create_resp.json()["id"]

    await client.post(f"{API}/cart/items", json={"product_id": product_id, "quantity": 2})
    resp = await client.delete(f"{API}/cart/")
    assert resp.status_code == 200
    assert resp.json()["items"] == []
