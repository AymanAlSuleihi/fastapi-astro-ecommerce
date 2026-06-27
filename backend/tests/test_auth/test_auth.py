import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["first_name"] == "Test"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={
            "email": "dup@example.com",
            "password": "password123",
            "first_name": "A",
            "last_name": "B",
        },
    )
    resp = await client.post(
        "/auth/register",
        json={
            "email": "dup@example.com",
            "password": "password123",
            "first_name": "C",
            "last_name": "D",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
            "first_name": "Login",
            "last_name": "Test",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={
            "email": "wrong@example.com",
            "password": "password123",
            "first_name": "Wrong",
            "last_name": "Pwd",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={
            "email": "me@example.com",
            "password": "password123",
            "first_name": "Me",
            "last_name": "Test",
        },
    )
    login_resp = await client.post(
        "/auth/login",
        json={"email": "me@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    resp = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/auth/me")
    assert resp.status_code == 400
