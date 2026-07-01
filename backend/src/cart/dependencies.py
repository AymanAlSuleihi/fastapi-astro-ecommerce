from typing import Annotated

from fastapi import Cookie, Depends, Response

from src.auth.utils import decode_token
from src.cart.service import CartService
from src.customers.dependencies import customer_scheme
from src.customers.models import Customer
from src.database import DbDep


async def _get_optional_customer(
    db: DbDep,
    token: Annotated[str | None, Depends(customer_scheme)] = None,
) -> Customer | None:
    from src.customers.service import CustomerService

    if not token:
        return None
    try:
        payload = decode_token(token)
        customer_id = payload.get("sub")
        if not customer_id:
            return None
        service = CustomerService(db)
        return await service.get_by_id(customer_id)
    except Exception:
        return None


async def get_cart(
    db: DbDep,
    response: Response,
    cart_session: Annotated[str | None, Cookie(alias="cart_session")] = None,
    current_customer: Annotated[Customer | None, Depends(_get_optional_customer)] = None,
) -> dict:
    service = CartService(db)
    cart = await service.get_or_create_cart(customer=current_customer, session_id=cart_session)
    # Persist the session cookie for anonymous carts
    if not current_customer and cart.get("session_id"):
        response.set_cookie(
            key="cart_session",
            value=cart["session_id"],
            max_age=60 * 60 * 24 * 30,  # 30 days
            httponly=True,
            samesite="lax",
        )
    return cart


CartDep = Annotated[dict, Depends(get_cart)]
