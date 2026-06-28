from contextlib import suppress
from uuid import UUID

from fastapi import APIRouter, status

from src.cart.dependencies import CartDep
from src.cart.exceptions import CartItemNotFound
from src.cart.schemas import CartItemCreate, CartItemUpdate, CartRead
from src.cart.service import CartService
from src.database import DbDep

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=CartRead)
async def get_cart_view(cart: CartDep):
    return cart


@router.post("/items", response_model=CartRead, status_code=status.HTTP_201_CREATED)
async def add_cart_item(data: CartItemCreate, cart: CartDep, db: DbDep):
    service = CartService(db)
    cart_orm = await service.get_cart_with_items(cart["id"])
    await service.add_item(cart_orm, data)
    await db.refresh(cart_orm, ["items"])
    return service.cart_to_dict(cart_orm)


@router.patch("/items/{product_id}", response_model=CartRead)
async def update_cart_item(
    product_id: str, data: CartItemUpdate, cart: CartDep, db: DbDep
):
    service = CartService(db)
    cart_orm = await service.get_cart_with_items(cart["id"])
    with suppress(CartItemNotFound):
        await service.update_quantity(cart_orm, UUID(product_id), data.quantity)
    await db.refresh(cart_orm, ["items"])
    return service.cart_to_dict(cart_orm)


@router.delete("/items/{product_id}", response_model=CartRead)
async def remove_cart_item(product_id: str, cart: CartDep, db: DbDep):
    service = CartService(db)
    cart_orm = await service.get_cart_with_items(cart["id"])
    await service.remove_item(cart_orm, UUID(product_id))
    await db.refresh(cart_orm, ["items"])
    return service.cart_to_dict(cart_orm)


@router.delete("/", response_model=CartRead)
async def clear_cart(cart: CartDep, db: DbDep):
    service = CartService(db)
    cart_orm = await service.get_cart_with_items(cart["id"])
    await service.clear_cart(cart_orm)
    await db.refresh(cart_orm, ["items"])
    return service.cart_to_dict(cart_orm)
