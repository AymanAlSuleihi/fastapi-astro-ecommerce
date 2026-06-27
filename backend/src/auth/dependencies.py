from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.auth.exceptions import InactiveUser, InvalidCredentials
from src.auth.models import User
from src.auth.service import AuthService
from src.auth.utils import decode_token
from src.config import settings
from src.database import DbDep

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)


async def get_current_user(
    db: DbDep,
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
) -> User:
    if not token:
        raise InvalidCredentials()

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
