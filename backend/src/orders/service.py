import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.cart.service import CartService
from src.constants import OrderStatus
from src.customers.models import Customer
from src.database import DbDep
from src.exceptions import BadRequestException
from src.orders.exceptions import OrderNotFound
from src.orders.models import Order, OrderItem
from src.products.service import ProductService


class OrderService:
    def __init__(self, db: DbDep):
        self.db = db

    async def create_order(
        self, customer: Customer, cart: dict, shipping_address_id: uuid.UUID | None = None
    ) -> dict:
        if not cart["items"]:
            raise BadRequestException(detail="Cart is empty", code="EMPTY_CART")

        cart_service = CartService(self.db)
        cart_orm = await cart_service.get_cart_with_items(cart["id"])
        if not cart_orm:
            raise BadRequestException(detail="Cart not found", code="CART_NOT_FOUND")

        product_service = ProductService(self.db)
        total = 0.0
        order_items_data: list[dict] = []

        for item in cart_orm.items:
            product = await product_service.validate_stock(item.product_id, item.quantity)
            line_total = float(product.price) * item.quantity
            total += line_total
            order_items_data.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "product_price": float(product.price),
                    "quantity": item.quantity,
                    "variant_id": item.variant_id,
                    "variant_sku": item.variant.sku,
                }
            )

        order = Order(
            customer_id=customer.id,
            total_amount=total,
            shipping_address_id=shipping_address_id,
            status=OrderStatus.PENDING,
        )
        self.db.add(order)
        await self.db.flush()

        for item_data in order_items_data:
            order_item = OrderItem(order_id=order.id, **item_data)
            self.db.add(order_item)
            await product_service.decrement_stock(item_data["product_id"], item_data["quantity"])

        await cart_service.clear_cart(cart_orm)
        await self.db.commit()

        # Re-fetch with items eagerly loaded, then build dict inside session
        order = await self.db.scalar(
            select(Order).where(Order.id == order.id).options(selectinload(Order.items))
        )
        assert order is not None
        return _order_to_dict(order)

    async def get_order_by_id(self, order_id: uuid.UUID) -> Order:
        order = await self.db.scalar(
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        if not order:
            raise OrderNotFound()
        return order

    async def update_status(self, order_id: uuid.UUID, status: OrderStatus) -> dict:
        order = await self.get_order_by_id(order_id)
        order.status = status
        await self.db.commit()
        order = await self.db.scalar(
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        assert order is not None
        return _order_to_dict(order)

    async def cancel_order(self, customer: Customer, order_id: uuid.UUID) -> dict:
        order = await self.get_order_by_id(order_id)
        if order.customer_id != customer.id:
            from src.exceptions import ForbiddenException
            raise ForbiddenException(detail="Not your order")
        if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            raise BadRequestException(
                detail=f"Cannot cancel order in '{order.status}' status",
            )
        # Restore stock to variants
        product_service = ProductService(self.db)
        for item in order.items:
            product = await product_service.get_product_by_id(item.product_id)
            if product.variants:
                product.variants[0].stock_quantity += item.quantity
        order.status = OrderStatus.CANCELLED
        await self.db.commit()
        order = await self.db.scalar(
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        assert order is not None
        return _order_to_dict(order)

    async def get_user_orders(
        self, customer: Customer, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict], int]:
        count = await self.db.scalar(
            select(func.count(Order.id)).where(Order.customer_id == customer.id)
        ) or 0
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Order)
            .where(Order.customer_id == customer.id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return [_order_to_dict(o) for o in result.scalars().all()], count

    async def get_all_orders(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict], int]:
        count = await self.db.scalar(select(func.count(Order.id))) or 0
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return [_order_to_dict(o) for o in result.scalars().all()], count


def _order_to_dict(order: Order) -> dict:
    return {
        "id": str(order.id),
        "customer_id": str(order.customer_id),
        "status": order.status.value if hasattr(order.status, "value") else order.status,
        "total_amount": float(order.total_amount),
        "shipping_address_id": (
            str(order.shipping_address_id) if order.shipping_address_id else None
        ),
        "items": [
            {
                "id": item.id,
                "product_id": str(item.product_id),
                "variant_id": str(item.variant_id) if item.variant_id else None,
                "variant_sku": item.variant_sku,
                "product_name": item.product_name,
                "product_price": float(item.product_price),
                "quantity": item.quantity,
            }
            for item in order.items
        ],
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
    }
