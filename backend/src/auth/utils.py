from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

from src.auth.config import auth_settings
from src.auth.exceptions import InvalidCredentials

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=auth_settings.JWT_EXP_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, auth_settings.JWT_SECRET, algorithm=auth_settings.JWT_ALG)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + auth_settings.REFRESH_TOKEN_EXP
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, auth_settings.REFRESH_TOKEN_KEY, algorithm=auth_settings.JWT_ALG)


def decode_token(token: str, secret: str | None = None) -> dict:
    key = secret or auth_settings.JWT_SECRET
    try:
        return jwt.decode(token, key, algorithms=[auth_settings.JWT_ALG])
    except InvalidTokenError as exc:
        raise InvalidCredentials() from exc
