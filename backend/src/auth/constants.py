from enum import StrEnum


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class AuthErrorCode:
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    INACTIVE_USER = "INACTIVE_USER"
    INVALID_TOKEN = "INVALID_TOKEN"
