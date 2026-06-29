from src.exceptions import NotFoundException
from src.shipping.constants import ShippingErrorCode


class ZoneNotFound(NotFoundException):
    def __init__(self):
        super().__init__(
            detail="Shipping zone not found", code=ShippingErrorCode.ZONE_NOT_FOUND
        )


class RateNotFound(NotFoundException):
    def __init__(self):
        super().__init__(
            detail="Shipping rate not found", code=ShippingErrorCode.RATE_NOT_FOUND
        )
