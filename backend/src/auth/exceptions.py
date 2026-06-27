from src.auth.constants import AuthErrorCode
from src.exceptions import BadRequestException, ConflictException, ForbiddenException


class InvalidCredentials(BadRequestException):
    def __init__(self):
        super().__init__(detail="Invalid email or password", code=AuthErrorCode.INVALID_CREDENTIALS)


class UserAlreadyExists(ConflictException):
    def __init__(self):
        super().__init__(
            detail="A user with this email already exists",
            code=AuthErrorCode.USER_ALREADY_EXISTS,
        )


class InactiveUser(ForbiddenException):
    def __init__(self):
        super().__init__(
            detail="This account has been deactivated",
            code=AuthErrorCode.INACTIVE_USER,
        )
