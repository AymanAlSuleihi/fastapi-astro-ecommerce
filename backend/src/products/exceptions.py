from src.exceptions import ConflictException, NotFoundException
from src.products.constants import ProductsErrorCode


class ProductNotFound(NotFoundException):
    def __init__(self):
        super().__init__(detail="Product not found", code=ProductsErrorCode.PRODUCT_NOT_FOUND)


class CategoryNotFound(NotFoundException):
    def __init__(self):
        super().__init__(detail="Category not found", code=ProductsErrorCode.CATEGORY_NOT_FOUND)


class InsufficientStock(ConflictException):
    def __init__(self, product_name: str, available: int, requested: int):
        super().__init__(
            detail=(
                f"Insufficient stock for '{product_name}': "
                f"{requested} requested, {available} available"
            ),
            code=ProductsErrorCode.INSUFFICIENT_STOCK,
        )


class TemplateNotFound(NotFoundException):
    def __init__(self):
        super().__init__(
            detail="Attribute template not found",
            code=ProductsErrorCode.TEMPLATE_NOT_FOUND,
        )


class VariantNotFound(NotFoundException):
    def __init__(self):
        super().__init__(
            detail="Product variant not found",
            code=ProductsErrorCode.VARIANT_NOT_FOUND,
        )
