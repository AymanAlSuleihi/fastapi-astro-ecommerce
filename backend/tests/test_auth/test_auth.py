import pytest
from httpx import AsyncClient

from src.auth.exceptions import InvalidCredentials
from src.auth.utils import create_access_token, create_refresh_token, decode_token

API = "/api/v1"


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post(
        f"{API}/customers/register",
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
        f"{API}/customers/register",
        json={
            "email": "dup@example.com",
            "password": "password123",
            "first_name": "A",
            "last_name": "B",
        },
    )
    resp = await client.post(
        f"{API}/customers/register",
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
        f"{API}/customers/register",
        json={
            "email": "login@example.com",
            "password": "password123",
            "first_name": "Login",
            "last_name": "Test",
        },
    )
    resp = await client.post(
        f"{API}/customers/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        f"{API}/customers/register",
        json={
            "email": "wrong@example.com",
            "password": "password123",
            "first_name": "Wrong",
            "last_name": "Pwd",
        },
    )
    resp = await client.post(
        f"{API}/customers/login",
        json={"email": "wrong@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient):
    await client.post(
        f"{API}/customers/register",
        json={
            "email": "me@example.com",
            "password": "password123",
            "first_name": "Me",
            "last_name": "Test",
        },
    )
    login_resp = await client.post(
        f"{API}/customers/login",
        json={"email": "me@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    resp = await client.get(
        f"{API}/customers/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    resp = await client.get(f"{API}/customers/me")
    assert resp.status_code == 400


# ── Auth utilities ────────────────────────────────────────


def test_create_access_token():
    token = create_access_token({"sub": "user-123"})
    assert isinstance(token, str)
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_refresh_token():
    from src.auth.config import auth_settings

    token = create_refresh_token({"sub": "user-123"})
    assert isinstance(token, str)
    # Refresh tokens use REFRESH_TOKEN_KEY
    payload = decode_token(token, secret=auth_settings.REFRESH_TOKEN_KEY)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "refresh"


def test_decode_invalid_token():
    try:
        decode_token("not.a.valid.token")
    except InvalidCredentials:
        pass
    else:
        pytest.fail("Expected InvalidCredentials for invalid token")


def test_decode_token_with_custom_secret():
    token = create_refresh_token({"sub": "user-456"})
    from src.auth.config import auth_settings

    payload = decode_token(token, secret=auth_settings.REFRESH_TOKEN_KEY)
    assert payload["sub"] == "user-456"
    assert payload["type"] == "refresh"


def test_decode_expired_token():
    from datetime import UTC, datetime, timedelta

    import jwt

    from src.auth.config import auth_settings

    expired = datetime.now(UTC) - timedelta(minutes=5)
    token = jwt.encode(
        {"sub": "x", "exp": expired},
        auth_settings.JWT_SECRET,
        algorithm=auth_settings.JWT_ALG,
    )
    try:
        decode_token(token)
    except InvalidCredentials:
        pass
    else:
        pytest.fail("Expected InvalidCredentials for expired token")
