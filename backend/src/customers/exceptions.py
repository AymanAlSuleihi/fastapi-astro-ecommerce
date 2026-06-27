from src.exceptions import NotFoundException


class AddressNotFound(NotFoundException):
    def __init__(self):
        super().__init__(detail="Address not found", code="ADDRESS_NOT_FOUND")
