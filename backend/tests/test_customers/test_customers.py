import pytest
from httpx import AsyncClient

API = "/api/v1"


async def _register_and_login(client: AsyncClient, email: str) -> str:
    await client.post(
        f"{API}/customers/register",
        json={
            "email": email,
            "password": "password123",
            "first_name": "Addr",
            "last_name": "Test",
        },
    )
    resp = await client.post(
        f"{API}/customers/login",
        json={"email": email, "password": "password123"},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_create_address(client: AsyncClient):
    token = await _register_and_login(client, "addr1@example.com")
    resp = await client.post(
        f"{API}/customers/addresses",
        json={
            "address_line1": "123 Main St",
            "city": "Testville",
            "postal_code": "12345",
            "country": "US",
            "is_default": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["address_line1"] == "123 Main St"
    assert data["city"] == "Testville"
    assert data["is_default"] is True


@pytest.mark.asyncio
async def test_list_addresses(client: AsyncClient):
    token = await _register_and_login(client, "addr2@example.com")
    # Create an address first
    await client.post(
        f"{API}/customers/addresses",
        json={
            "address_line1": "456 Oak Ave",
            "city": "Othertown",
            "postal_code": "67890",
            "country": "US",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(
        f"{API}/customers/addresses",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_update_address(client: AsyncClient):
    token = await _register_and_login(client, "addr3@example.com")
    create_resp = await client.post(
        f"{API}/customers/addresses",
        json={
            "address_line1": "Original",
            "city": "Oldtown",
            "postal_code": "11111",
            "country": "US",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    addr_id = create_resp.json()["id"]

    resp = await client.patch(
        f"{API}/customers/addresses/{addr_id}",
        json={"city": "Newtown", "address_line1": "Updated"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["city"] == "Newtown"
    assert data["address_line1"] == "Updated"


@pytest.mark.asyncio
async def test_delete_address(client: AsyncClient):
    token = await _register_and_login(client, "addr4@example.com")
    create_resp = await client.post(
        f"{API}/customers/addresses",
        json={
            "address_line1": "Delete me",
            "city": "Gonetown",
            "postal_code": "99999",
            "country": "US",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    addr_id = create_resp.json()["id"]

    resp = await client.delete(
        f"{API}/customers/addresses/{addr_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_update_me(client: AsyncClient):
    token = await _register_and_login(client, "updateme@example.com")
    resp = await client.patch(
        f"{API}/customers/me",
        json={"first_name": "Updated", "last_name": "Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"


@pytest.mark.asyncio
async def test_update_me_password(client: AsyncClient):
    token = await _register_and_login(client, "passchange@example.com")
    resp = await client.patch(
        f"{API}/customers/me",
        json={"password": "newpassword123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    # Verify can login with new password
    login_resp = await client.post(
        f"{API}/customers/login",
        json={"email": "passchange@example.com", "password": "newpassword123"},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_other_customer_address_forbidden(client: AsyncClient):
    """Customer A cannot delete Customer B's address."""
    token_a = await _register_and_login(client, "addra@example.com")
    token_b = await _register_and_login(client, "addrb@example.com")

    # Customer B creates an address
    create_resp = await client.post(
        f"{API}/customers/addresses",
        json={
            "address_line1": "B's Address",
            "city": "Btown",
            "postal_code": "22222",
            "country": "US",
        },
        headers={"Authorization": f"Bearer {token_b}"},
    )
    addr_id = create_resp.json()["id"]

    # Customer A tries to delete B's address
    resp = await client.delete(
        f"{API}/customers/addresses/{addr_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 403
