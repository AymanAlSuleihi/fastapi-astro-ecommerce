from typing import Annotated

from fastapi import Cookie, Depends

from src.auth.dependencies import oauth2_scheme
from src.auth.models import User
from src.auth.utils import decode_token
from src.cart.service import CartService
from src.database import DbDep


async def _get_optional_user(
    db: DbDep,
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
) -> User | None:
    from src.auth.service import AuthService

    if not token:
        return None
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        service = AuthService(db)
        return await service.get_by_id(user_id)
    except Exception:
        return None


async def get_cart(
    db: DbDep,
    cart_session: Annotated[str | None, Cookie(alias="cart_session")] = None,
    current_user: Annotated[User | None, Depends(_get_optional_user)] = None,
) -> dict:
    service = CartService(db)
    return await service.get_or_create_cart(user=current_user, session_id=cart_session)


CartDep = Annotated[dict, Depends(get_cart)]
