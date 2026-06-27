from src.exceptions import NotFoundException


class PaymentNotFound(NotFoundException):
    def __init__(self):
        super().__init__(detail="Payment not found", code="PAYMENT_NOT_FOUND")
