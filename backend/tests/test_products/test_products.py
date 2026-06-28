import pytest
from httpx import AsyncClient

API = "/api/v1"


async def _get_admin_token(client: AsyncClient) -> str:
    resp = await client.post(
        f"{API}/admin/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ── List empty ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_products_empty(client: AsyncClient):
    resp = await client.get(f"{API}/products/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_categories_empty(client: AsyncClient):
    resp = await client.get(f"{API}/products/categories")
    assert resp.status_code == 200
    assert resp.json() == []


# ── Categories CRUD ───────────────────────────────────────


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient):
    token = await _get_admin_token(client)
    resp = await client.post(
        f"{API}/products/categories",
        json={"name": "Rings", "slug": "rings"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Rings"


@pytest.mark.asyncio
async def test_get_category_by_slug(client: AsyncClient):
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/products/categories",
        json={"name": "Necklaces", "slug": "necklaces"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(f"{API}/products/categories/necklaces")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Necklaces"


@pytest.mark.asyncio
async def test_list_categories_after_create(client: AsyncClient):
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/products/categories",
        json={"name": "Bracelets", "slug": "bracelets"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(f"{API}/products/categories")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ── Products CRUD ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient):
    token = await _get_admin_token(client)
    resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Gold Ring",
            "slug": "gold-ring",
            "price": 299.99,
            "stock_quantity": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Gold Ring"
    assert data["slug"] == "gold-ring"
    assert data["price"] == 299.99
    assert data["stock_quantity"] == 10


@pytest.mark.asyncio
async def test_get_product_by_slug(client: AsyncClient):
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/products/",
        json={
            "name": "Silver Necklace",
            "slug": "silver-necklace",
            "price": 149.99,
            "stock_quantity": 5,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(f"{API}/products/silver-necklace")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Silver Necklace"


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Diamond Earrings",
            "slug": "diamond-earrings",
            "price": 499.99,
            "stock_quantity": 3,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id = create_resp.json()["id"]

    resp = await client.patch(
        f"{API}/products/{product_id}",
        json={"price": 449.99, "stock_quantity": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["price"] == 449.99
    assert data["stock_quantity"] == 2


@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/products/",
        json={
            "name": "Delete Me",
            "slug": "delete-me",
            "price": 1.00,
            "stock_quantity": 0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id = create_resp.json()["id"]

    resp = await client.delete(
        f"{API}/products/{product_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204

    # Verify gone
    resp = await client.get(f"{API}/products/delete-me")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_products_with_results(client: AsyncClient):
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/products/",
        json={
            "name": "Watch",
            "slug": "watch",
            "price": 199.99,
            "stock_quantity": 20,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(f"{API}/products/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


# ── Unauthorized ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_product_without_auth(client: AsyncClient):
    resp = await client.post(
        f"{API}/products/",
        json={"name": "Nope", "slug": "nope", "price": 1.00, "stock_quantity": 1},
    )
    assert resp.status_code == 403


# ── Product Pagination & Search ───────────────────────────


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/products/categories",
        json={"name": "Updatable", "slug": "updatable"},
        headers={"Authorization": f"Bearer {token}"},
    )
    cat_id = create_resp.json()["id"]

    resp = await client.patch(
        f"{API}/products/categories/{cat_id}",
        json={"name": "Updated Category"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Category"


@pytest.mark.asyncio
async def test_delete_category(client: AsyncClient):
    token = await _get_admin_token(client)
    create_resp = await client.post(
        f"{API}/products/categories",
        json={"name": "Deletable", "slug": "deletable"},
        headers={"Authorization": f"Bearer {token}"},
    )
    cat_id = create_resp.json()["id"]

    resp = await client.delete(
        f"{API}/products/categories/{cat_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_list_products_pagination(client: AsyncClient):
    token = await _get_admin_token(client)
    for i in range(3):
        await client.post(
            f"{API}/products/",
            json={
                "name": f"Page Product {i}",
                "slug": f"page-product-{i}",
                "price": 10.0 + i,
                "stock_quantity": 5,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    resp = await client.get(f"{API}/products/?page=1&page_size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_products_search(client: AsyncClient):
    token = await _get_admin_token(client)
    await client.post(
        f"{API}/products/",
        json={
            "name": "Unique Search Item",
            "slug": "unique-search-item",
            "price": 99.00,
            "stock_quantity": 1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(f"{API}/products/?search=Unique")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Unique Search Item"


@pytest.mark.asyncio
async def test_list_products_by_category(client: AsyncClient):
    token = await _get_admin_token(client)
    cat_resp = await client.post(
        f"{API}/products/categories",
        json={"name": "CatFilter", "slug": "cat-filter"},
        headers={"Authorization": f"Bearer {token}"},
    )
    cat_id = cat_resp.json()["id"]

    await client.post(
        f"{API}/products/",
        json={
            "name": "Categorized Item",
            "slug": "categorized-item",
            "price": 50.00,
            "stock_quantity": 3,
            "category_id": cat_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(f"{API}/products/?category=cat-filter")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_update_product_not_found(client: AsyncClient):
    token = await _get_admin_token(client)
    resp = await client.patch(
        f"{API}/products/00000000-0000-0000-0000-000000000000",
        json={"price": 10.00},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_product_not_found(client: AsyncClient):
    token = await _get_admin_token(client)
    resp = await client.delete(
        f"{API}/products/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_category_without_auth(client: AsyncClient):
    resp = await client.post(
        f"{API}/products/categories",
        json={"name": "Nope", "slug": "nope"},
    )
    assert resp.status_code == 403
