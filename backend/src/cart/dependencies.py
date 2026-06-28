from typing import Annotated

from fastapi import Cookie, Depends

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
    cart_session: Annotated[str | None, Cookie(alias="cart_session")] = None,
    current_user: Annotated[Customer | None, Depends(_get_optional_customer)] = None,
) -> dict:
    service = CartService(db)
    return await service.get_or_create_cart(user=current_user, session_id=cart_session)


CartDep = Annotated[dict, Depends(get_cart)]
