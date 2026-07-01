import pytest
from httpx import AsyncClient

API = "/api/v1"


async def _get_admin_token(client: AsyncClient) -> str:
    """Seed ensures admin@example.com / admin123 exists."""
    resp = await client.post(
        f"{API}/admin/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ── Auth ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_login_success(client: AsyncClient):
    resp = await client.post(
        f"{API}/admin/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_admin_login_wrong_password(client: AsyncClient):
    resp = await client.post(
        f"{API}/admin/login",
        json={"email": "admin@example.com", "password": "wrong"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_admin_login_wrong_email(client: AsyncClient):
    resp = await client.post(
        f"{API}/admin/login",
        json={"email": "nobody@example.com", "password": "admin123"},
    )
    assert resp.status_code == 400


# ── Users CRUD ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    token = await _get_admin_token(client)
    resp = await client.get(
        f"{API}/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) >= 1
    assert users[0]["email"] == "admin@example.com"


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    token = await _get_admin_token(client)
    resp = await client.post(
        f"{API}/admin/users",
        json={
            "email": "newadmin@example.com",
            "password": "newadmin123",
            "first_name": "New",
            "last_name": "Admin",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newadmin@example.com"
    assert data["is_admin"] is True
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient):
    token = await _get_admin_token(client)
    resp = await client.post(
        f"{API}/admin/users",
        json={
            "email": "admin@example.com",
            "password": "password123",
            "first_name": "Dup",
            "last_name": "Admin",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient):
    token = await _get_admin_token(client)
    # Create a user to update
    create_resp = await client.post(
        f"{API}/admin/users",
        json={
            "email": "update@example.com",
            "password": "password123",
            "first_name": "Before",
            "last_name": "Update",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = create_resp.json()["id"]

    resp = await client.patch(
        f"{API}/admin/users/{user_id}",
        json={"first_name": "After", "is_admin": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["first_name"] == "After"
    assert data["is_admin"] is False


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/admin/users",
        json={
            "email": "delete@example.com",
            "password": "password123",
            "first_name": "Delete",
            "last_name": "Me",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = create_resp.json()["id"]

    resp = await client.delete(
        f"{API}/admin/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204

    # Verify gone
    resp = await client.get(
        f"{API}/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    emails = [u["email"] for u in resp.json()]
    assert "delete@example.com" not in emails


# ── Dashboard ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dashboard(client: AsyncClient):
    token = await _get_admin_token(client)
    resp = await client.get(
        f"{API}/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "total_orders" in data
    assert "total_revenue" in data
    assert "total_customers" in data
    assert "total_products" in data


# ── Customers ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_customers(client: AsyncClient):
    token = await _get_admin_token(client)
    # Register a customer first so there's something to list
    await client.post(
        f"{API}/customers/register",
        json={
            "email": "customer1@example.com",
            "password": "password123",
            "first_name": "Cust",
            "last_name": "One",
        },
    )
    resp = await client.get(
        f"{API}/admin/customers",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    customers = resp.json()
    assert len(customers) >= 1


@pytest.mark.asyncio
async def test_toggle_customer_active(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/customers/register",
        json={
            "email": "toggle@example.com",
            "password": "password123",
            "first_name": "Toggle",
            "last_name": "Customer",
        },
    )
    customer_id = create_resp.json()["id"]
    assert create_resp.json()["is_active"] is True

    resp = await client.patch(
        f"{API}/admin/customers/{customer_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # Toggle back
    resp = await client.patch(
        f"{API}/admin/customers/{customer_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


# ── Password Reset ────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_forgot_password_valid_email(client: AsyncClient):
    """Forgot password with admin email returns 200."""
    resp = await client.post(
        f"{API}/admin/forgot-password",
        json={"email": "admin@example.com"},
    )
    assert resp.status_code == 200
    assert "message" in resp.json()


@pytest.mark.asyncio
async def test_admin_forgot_password_unknown_email(client: AsyncClient):
    """Forgot password with unknown email also returns 200."""
    resp = await client.post(
        f"{API}/admin/forgot-password",
        json={"email": "nobody@example.com"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_admin_reset_password_valid_token(client: AsyncClient):
    """Reset admin password with a valid token and login with new password."""
    from src.auth.utils import create_reset_token

    login_resp = await client.post(
        f"{API}/admin/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    token = login_resp.json()["access_token"]

    import jwt

    from src.auth.config import auth_settings

    payload = jwt.decode(token, auth_settings.JWT_SECRET, algorithms=[auth_settings.JWT_ALG])
    admin_id = payload["sub"]

    reset_token = create_reset_token(admin_id)
    resp = await client.post(
        f"{API}/admin/reset-password",
        json={"token": reset_token, "new_password": "newadmin123"},
    )
    assert resp.status_code == 200

    # Verify can login with new password
    login_resp = await client.post(
        f"{API}/admin/login",
        json={"email": "admin@example.com", "password": "newadmin123"},
    )
    assert login_resp.status_code == 200

    # Reset password back so other tests don't break
    reset_token2 = create_reset_token(admin_id)
    await client.post(
        f"{API}/admin/reset-password",
        json={"token": reset_token2, "new_password": "admin123"},
    )


@pytest.mark.asyncio
async def test_admin_reset_password_invalid_token(client: AsyncClient):
    """Reset admin password with a garbage token returns 400."""
    resp = await client.post(
        f"{API}/admin/reset-password",
        json={"token": "invalid-token", "new_password": "newpass123"},
    )
    assert resp.status_code == 400


# ── Unauthorized access ───────────────────────────────────


@pytest.mark.asyncio
async def test_admin_route_without_token(client: AsyncClient):
    resp = await client.get(f"{API}/admin/dashboard")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_route_with_customer_token(client: AsyncClient):
    # Login as customer (not admin)
    await client.post(
        f"{API}/customers/register",
        json={
            "email": "notadmin@example.com",
            "password": "password123",
            "first_name": "Not",
            "last_name": "Admin",
        },
    )
    login = await client.post(
        f"{API}/customers/login",
        json={"email": "notadmin@example.com", "password": "password123"},
    )
    customer_token = login.json()["access_token"]

    resp = await client.get(
        f"{API}/admin/dashboard",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 403
