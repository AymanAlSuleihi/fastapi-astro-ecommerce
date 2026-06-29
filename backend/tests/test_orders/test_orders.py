import pytest
from httpx import AsyncClient

API = "/api/v1"


async def _get_admin_token(client: AsyncClient) -> str:
    resp = await client.post(
        f"{API}/admin/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    return resp.json()["access_token"]


async def _register_and_login(client: AsyncClient, email: str) -> str:
    await client.post(
        f"{API}/customers/register",
        json={
            "email": email,
            "password": "password123",
            "first_name": "Order",
            "last_name": "Test",
        },
    )
    resp = await client.post(
        f"{API}/customers/login",
        json={"email": email, "password": "password123"},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_create_order_empty_cart(client: AsyncClient):
    token = await _register_and_login(client, "emptycart@example.com")
    resp = await client.post(
        f"{API}/orders/",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400  # empty cart


@pytest.mark.asyncio
async def test_list_orders_empty(client: AsyncClient):
    token = await _register_and_login(client, "nolist@example.com")
    resp = await client.get(
        f"{API}/orders/", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_checkout_flow(client: AsyncClient):
    """Full checkout: create product → add to cart → place order."""
    # Create product as admin
    admin_token = await _get_admin_token(client)
    product_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Checkout Ring",
            "slug": "checkout-ring",
            "price": 100.00,
            "stock_quantity": 5,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    product_id = product_resp.json()["id"]

    # Customer login
    token = await _register_and_login(client, "checkout@example.com")

    # Add to cart
    cart_resp = await client.post(
        f"{API}/cart/items",
        json={"product_id": product_id, "quantity": 2},
    )
    assert cart_resp.status_code == 201

    # Place order
    order_resp = await client.post(
        f"{API}/orders/",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert order_resp.status_code == 201
    order = order_resp.json()
    assert order["subtotal"] == 200.00
    assert order["total_amount"] == 200.00
    assert order["status"] == "PENDING"
    assert len(order["items"]) == 1
    assert order["items"][0]["quantity"] == 2

    # Verify stock decreased
    product_check = await client.get(f"{API}/products/checkout-ring")
    assert product_check.json()["stock_quantity"] == 3

    # Verify order appears in list
    orders = await client.get(
        f"{API}/orders/", headers={"Authorization": f"Bearer {token}"}
    )
    assert len(orders.json()["items"]) == 1


@pytest.mark.asyncio
async def test_cancel_order(client: AsyncClient):
    """Customer can cancel a pending order and stock is restored."""
    admin_token = await _get_admin_token(client)
    product_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Cancel Ring",
            "slug": "cancel-ring",
            "price": 50.00,
            "stock_quantity": 5,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    product_id = product_resp.json()["id"]

    token = await _register_and_login(client, "cancel@example.com")
    await client.post(
        f"{API}/cart/items",
        json={"product_id": product_id, "quantity": 2},
    )
    order_resp = await client.post(
        f"{API}/orders/",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    order_id = order_resp.json()["id"]
    assert order_resp.json()["status"] == "PENDING"

    # Cancel
    cancel_resp = await client.patch(
        f"{API}/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"

    # Stock restored
    product_check = await client.get(f"{API}/products/cancel-ring")
    assert product_check.json()["stock_quantity"] == 5


@pytest.mark.asyncio
async def test_admin_list_all_orders(client: AsyncClient):
    """Admin can list all orders across all customers."""
    token = await _get_admin_token(client)
    resp = await client.get(
        f"{API}/orders/all",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_checkout_insufficient_stock(client: AsyncClient):
    admin_token = await _get_admin_token(client)
    product_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Scarce Ring",
            "slug": "scarce-ring",
            "price": 500.00,
            "stock_quantity": 1,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    product_id = product_resp.json()["id"]

    # Try to add more than stock — should be rejected at cart level
    cart_resp = await client.post(
        f"{API}/cart/items",
        json={"product_id": product_id, "quantity": 5},  # more than stock
    )
    assert cart_resp.status_code == 409


@pytest.mark.asyncio
async def test_admin_update_order_status(client: AsyncClient):
    admin_token = await _get_admin_token(client)

    # Create product
    product_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Status Ring",
            "slug": "status-ring",
            "price": 50.00,
            "stock_quantity": 3,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    product_id = product_resp.json()["id"]

    # Customer checkout
    token = await _register_and_login(client, "status@example.com")
    await client.post(
        f"{API}/cart/items",
        json={"product_id": product_id, "quantity": 1},
    )
    order_resp = await client.post(
        f"{API}/orders/",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    order_id = order_resp.json()["id"]

    # Admin updates status
    resp = await client.patch(
        f"{API}/orders/{order_id}/status",
        json={"status": "CONFIRMED"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "CONFIRMED"


# ── Guest Checkout ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_guest_checkout(client: AsyncClient):
    """Guest can place an order without creating an account."""
    admin_token = await _get_admin_token(client)
    product_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Guest Ring",
            "slug": "guest-ring",
            "price": 25.00,
            "stock_quantity": 5,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    product_id = product_resp.json()["id"]

    await client.post(
        f"{API}/cart/items",
        json={"product_id": product_id, "quantity": 2},
    )

    resp = await client.post(
        f"{API}/orders/",
        json={
            "email": "guest@example.com",
            "first_name": "Guest",
            "last_name": "User",
        },
    )
    assert resp.status_code == 201
    order = resp.json()
    assert order["subtotal"] == 50.00
    assert len(order["items"]) == 1


@pytest.mark.asyncio
async def test_guest_checkout_missing_fields(client: AsyncClient):
    resp = await client.post(
        f"{API}/orders/",
        json={},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_guest_checkout_becomes_customer(client: AsyncClient):
    """Guest who later registers can still log in."""
    admin_token = await _get_admin_token(client)
    product_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Guest Register Ring",
            "slug": "guest-register-ring",
            "price": 10.00,
            "stock_quantity": 2,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    product_id = product_resp.json()["id"]

    await client.post(
        f"{API}/cart/items",
        json={"product_id": product_id, "quantity": 1},
    )

    # Guest checkout
    await client.post(
        f"{API}/orders/",
        json={
            "email": "guest-register@example.com",
            "first_name": "Later",
            "last_name": "Register",
        },
    )

    # Later registers
    await client.post(
        f"{API}/customers/register",
        json={
            "email": "guest-register@example.com",
            "password": "password123",
            "first_name": "Later",
            "last_name": "Register",
        },
    )
    login_resp = await client.post(
        f"{API}/customers/login",
        json={
            "email": "guest-register@example.com",
            "password": "password123",
        },
    )
    assert login_resp.status_code == 200
