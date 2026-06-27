from src.exceptions import NotFoundException


class OrderNotFound(NotFoundException):
    def __init__(self):
        super().__init__(detail="Order not found", code="ORDER_NOT_FOUND")
