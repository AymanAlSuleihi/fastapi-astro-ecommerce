from fastapi import APIRouter, status

from src.cart.dependencies import CartDep
from src.cart.schemas import CartItemCreate, CartItemUpdate, CartRead

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=CartRead)
async def get_cart_view(cart: CartDep):
    return cart


@router.post("/items", response_model=CartRead, status_code=status.HTTP_201_CREATED)
async def add_cart_item(
    data: CartItemCreate,
    cart: CartDep,
):
    return cart


@router.patch("/items/{product_id}", response_model=CartRead)
async def update_cart_item(
    product_id: str,
    data: CartItemUpdate,
    cart: CartDep,
):
    return cart


@router.delete("/items/{product_id}", response_model=CartRead)
async def remove_cart_item(
    product_id: str,
    cart: CartDep,
):
    return cart
