from src.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)


class AddressNotFound(NotFoundException):
    def __init__(self):
        super().__init__(detail="Address not found", code="ADDRESS_NOT_FOUND")


class InvalidCustomerCredentials(BadRequestException):
    def __init__(self):
        super().__init__(detail="Invalid email or password", code="INVALID_CREDENTIALS")


class CustomerAlreadyExists(ConflictException):
    def __init__(self):
        super().__init__(
            detail="A customer with this email already exists",
            code="CUSTOMER_ALREADY_EXISTS",
        )


class InactiveCustomer(ForbiddenException):
    def __init__(self):
        super().__init__(detail="This account has been deactivated", code="INACTIVE_CUSTOMER")
