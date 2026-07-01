from src.exceptions import ConflictException, NotFoundException
from src.store_config.constants import StoreConfigErrorCode


class StoreConfigKeyNotFound(NotFoundException):
    def __init__(self, key: str):
        super().__init__(
            detail=f"Store config key '{key}' not found",
            code=StoreConfigErrorCode.KEY_NOT_FOUND,
        )


class StoreConfigKeyAlreadyExists(ConflictException):
    def __init__(self, key: str):
        super().__init__(
            detail=f"Store config key '{key}' already exists",
            code=StoreConfigErrorCode.KEY_ALREADY_EXISTS,
        )
