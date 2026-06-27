from src.exceptions import NotFoundException


class CartItemNotFound(NotFoundException):
    def __init__(self):
        super().__init__(detail="Cart item not found", code="CART_ITEM_NOT_FOUND")
