from typing import Annotated

from fastapi import Depends, Header

from src.auth.exceptions import InactiveUser, InvalidCredentials
from src.auth.models import User
from src.auth.service import AuthService
from src.auth.utils import decode_token
from src.database import DbDep


async def get_current_user(
    db: DbDep, authorization: Annotated[str | None, Header()] = None
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise InvalidCredentials()

    token = authorization.removeprefix("Bearer ")
    payload = decode_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidCredentials()

    service = AuthService(db)
    user = await service.get_by_id(user_id)
    if not user:
        raise InvalidCredentials()
    if not user.is_active:
        raise InactiveUser()
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_current_admin_user(current_user: CurrentUserDep) -> User:
    if not current_user.is_admin:
        from src.exceptions import ForbiddenException

        raise ForbiddenException(detail="Admin access required")
    return current_user


CurrentAdminDep = Annotated[User, Depends(get_current_admin_user)]
