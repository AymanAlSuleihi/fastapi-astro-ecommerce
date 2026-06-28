import uuid

from sqlalchemy import select
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
        self, user: Customer, shipping_address_id: uuid.UUID | None = None
    ) -> Order:
        cart_service = CartService(self.db)
        cart = await cart_service.get_or_create_cart(user=user)

        if not cart["items"]:
            raise BadRequestException(detail="Cart is empty", code="EMPTY_CART")

        # Fetch cart ORM for item processing
        from sqlalchemy.orm import selectinload

        from src.cart.models import Cart as CartModel
        from src.cart.models import CartItem

        cart_orm = await self.db.scalar(
            select(CartModel)
            .where(CartModel.id == cart["id"])
            .options(selectinload(CartModel.items).selectinload(CartItem.product))
        )
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
                }
            )

        order = Order(
            customer_id=user.id,
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
        await self.db.refresh(order)
        return order

    async def get_user_orders(self, user: Customer) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .where(Order.customer_id == user.id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_order_by_id(self, order_id: uuid.UUID) -> Order:
        order = await self.db.scalar(
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        if not order:
            raise OrderNotFound()
        return order

    async def update_status(self, order_id: uuid.UUID, status: OrderStatus) -> Order:
        order = await self.get_order_by_id(order_id)
        order.status = status
        await self.db.commit()
        await self.db.refresh(order)
        return order
