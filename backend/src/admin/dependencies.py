from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from src.admin.models import User
from src.config import settings
from src.database import DbDep
from src.exceptions import ForbiddenException

admin_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/admin/login", auto_error=False
)


async def get_current_admin(
    db: DbDep,
    token: Annotated[str | None, Depends(admin_scheme)] = None,
) -> User:
    from src.auth.utils import decode_token

    if not token:
        raise ForbiddenException(detail="Admin access required")

    payload = decode_token(token)
    admin_id = payload.get("sub")
    if not admin_id:
        raise ForbiddenException(detail="Admin access required")

    admin = await db.scalar(select(User).where(User.id == admin_id))
    if not admin:
        raise ForbiddenException(detail="Admin access required")
    return admin


CurrentAdminDep = Annotated[User, Depends(get_current_admin)]
