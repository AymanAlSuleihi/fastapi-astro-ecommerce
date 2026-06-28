from src.exceptions import BadRequestException


class InvalidCredentials(BadRequestException):
    def __init__(self):
        super().__init__(detail="Invalid email or password", code="INVALID_CREDENTIALS")
