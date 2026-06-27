from http import HTTPStatus

from fastapi import HTTPException


class AppException(HTTPException):
    def __init__(self, status_code: int, detail: str, code: str | None = None):
        self.code = code
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(status_code=HTTPStatus.NOT_FOUND, detail=detail, code=code)


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Not authorized", code: str = "FORBIDDEN"):
        super().__init__(status_code=HTTPStatus.FORBIDDEN, detail=detail, code=code)


class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad request", code: str = "BAD_REQUEST"):
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=detail, code=code)


class ConflictException(AppException):
    def __init__(self, detail: str = "Conflict", code: str = "CONFLICT"):
        super().__init__(status_code=HTTPStatus.CONFLICT, detail=detail, code=code)
