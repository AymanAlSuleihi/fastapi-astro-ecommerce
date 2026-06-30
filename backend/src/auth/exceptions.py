from src.exceptions import BadRequestException


class InvalidCredentials(BadRequestException):
    def __init__(self):
        super().__init__(detail="Invalid email or password", code="INVALID_CREDENTIALS")


class InvalidResetToken(BadRequestException):
    def __init__(self):
        super().__init__(
            detail="Invalid or expired reset token", code="INVALID_RESET_TOKEN"
        )
