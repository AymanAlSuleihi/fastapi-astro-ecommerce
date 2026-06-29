import pytest
from httpx import AsyncClient

API = "/api/v1"


async def _register_and_login(client: AsyncClient, email: str) -> str:
    await client.post(
        f"{API}/customers/register",
        json={
            "email": email,
            "password": "password123",
            "first_name": "Pay",
            "last_name": "Test",
        },
    )
    resp = await client.post(
        f"{API}/customers/login",
        json={"email": email, "password": "password123"},
    )
    return resp.json()["access_token"]


async def _get_admin_token(client: AsyncClient) -> str:
    resp = await client.post(
        f"{API}/admin/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    return resp.json()["access_token"]


async def _setup_order(client: AsyncClient) -> tuple[str, str, str]:
    """Create product, add to cart, create order. Returns (customer_token, order_id, payment_id)."""
    admin_token = await _get_admin_token(client)
    product_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Payment Test Ring",
            "slug": "payment-test-ring",
            "price": 100.00,
            "stock_quantity": 10,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    product_id = product_resp.json()["id"]

    token = await _register_and_login(client, f"paytest_{product_id}@example.com")
    await client.post(
        f"{API}/cart/items",
        json={"product_id": product_id, "quantity": 1},
    )
    order_resp = await client.post(
        f"{API}/orders/",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    return token, order_resp.json()["id"]


@pytest.mark.asyncio
async def test_create_payment_intent(client: AsyncClient):
    token, order_id = await _setup_order(client)

    resp = await client.post(
        f"{API}/payments/create-intent",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "client_secret" in data
    assert "payment_id" in data


@pytest.mark.asyncio
async def test_payment_webhook_success(client: AsyncClient):
    token, order_id = await _setup_order(client)

    # Create payment intent first
    await client.post(
        f"{API}/payments/create-intent",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Webhook uses provider_payment_id (the stripe stub format)
    resp = await client.post(
        f"{API}/payments/webhook?provider=stripe&event_type=payment_intent.succeeded&payment_id=pi_stub_{order_id}",
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_payment_webhook_wrong_provider(client: AsyncClient):
    resp = await client.post(
        f"{API}/payments/webhook?provider=paypal&event_type=payment.succeeded&payment_id=abc123",
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_payment_webhook_not_found(client: AsyncClient):
    resp = await client.post(
        f"{API}/payments/webhook?provider=stripe&event_type=payment_intent.succeeded&payment_id=nonexistent",
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_payment_intent_without_auth(client: AsyncClient):
    resp = await client.post(
        f"{API}/payments/create-intent",
        json={"order_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert resp.status_code in (400, 401, 403)


@pytest.mark.asyncio
async def test_get_payment(client: AsyncClient):
    token, order_id = await _setup_order(client)

    intent_resp = await client.post(
        f"{API}/payments/create-intent",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    payment_id = intent_resp.json()["payment_id"]

    resp = await client.get(f"{API}/payments/{payment_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == payment_id
    assert data["order_id"] == order_id
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_get_payment_not_found(client: AsyncClient):
    resp = await client.get(
        f"{API}/payments/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404
