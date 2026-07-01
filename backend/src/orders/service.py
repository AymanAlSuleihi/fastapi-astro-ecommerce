import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.cart.service import CartService
from src.constants import OrderStatus
from src.customers.models import Customer
from src.database import DbDep
from src.exceptions import BadRequestException
from src.logging_config import get_logger
from src.orders.exceptions import OrderNotFound
from src.orders.models import Order, OrderItem
from src.products.service import ProductService

logger = get_logger(__name__)


class OrderService:
    def __init__(self, db: DbDep):
        self.db = db

    async def create_order(
        self,
        customer: Customer,
        cart: dict,
        shipping_address_id: uuid.UUID | None = None,
        shipping_rate_id: uuid.UUID | None = None,
        billing_address: dict | None = None,
        currency: str | None = None,
    ) -> dict:
        if not cart["items"]:
            raise BadRequestException(detail="Cart is empty", code="EMPTY_CART")

        cart_service = CartService(self.db)
        cart_orm = await cart_service.get_cart_with_items(cart["id"])
        if not cart_orm:
            raise BadRequestException(detail="Cart not found", code="CART_NOT_FOUND")

        # Validate shipping rate if provided
        shipping_cost = 0.0
        estimated_delivery = None
        if shipping_rate_id:
            from src.shipping.service import ShippingService

            shipping_service = ShippingService(self.db)
            rate = await shipping_service.get_rate(shipping_rate_id)
            shipping_cost = float(rate.cost)
            if rate.min_days is not None and rate.max_days is not None:
                from datetime import UTC, datetime, timedelta

                estimated_delivery = datetime.now(UTC) + timedelta(days=rate.max_days)

        product_service = ProductService(self.db)
        subtotal = 0.0
        order_items_data: list[dict] = []

        for item in cart_orm.items:
            product = await product_service.validate_stock(item.product_id, item.quantity)
            line_total = float(product.price) * item.quantity
            subtotal += line_total
            order_items_data.append(
                {
                    "product_id": product.id,
                    "product_name": product.name,
                    "product_price": float(product.price),
                    "line_total": line_total,
                    "quantity": item.quantity,
                    "variant_id": item.variant_id,
                    "variant_sku": item.variant.sku,
                }
            )

        # Snapshot shipping address (freeze at order time)
        shipping_address_snapshot = None
        if shipping_address_id:
            from src.customers.models import Address

            addr = await self.db.scalar(select(Address).where(Address.id == shipping_address_id))
            if addr:
                shipping_address_snapshot = {
                    "name": f"{customer.first_name} {customer.last_name}",
                    "line1": addr.address_line1,
                    "line2": addr.address_line2,
                    "city": addr.city,
                    "state": addr.state,
                    "postal_code": addr.postal_code,
                    "country": addr.country,
                }

        # Currency handling
        order_currency = currency or "USD"
        exchange_rate = 1.0
        base_subtotal = subtotal
        base_shipping_cost = shipping_cost

        if order_currency != "USD":
            from src.currencies.service import ExchangeRateService

            rate_service = ExchangeRateService(self.db)
            rate = await rate_service.get_rate("USD", order_currency)
            if rate:
                exchange_rate = rate
                base_subtotal = subtotal
                base_shipping_cost = shipping_cost
                subtotal = round(subtotal * rate, 2)
                shipping_cost = round(shipping_cost * rate, 2)

        order = Order(
            customer_id=customer.id,
            currency=order_currency,
            exchange_rate=exchange_rate if order_currency != "USD" else None,
            total_amount=subtotal + shipping_cost,
            subtotal=subtotal,
            tax_amount=0.0,
            shipping_cost=shipping_cost,
            base_total_amount=(
                base_subtotal + base_shipping_cost if order_currency != "USD" else None
            ),
            base_subtotal=base_subtotal if order_currency != "USD" else None,
            base_tax_amount=None,
            base_shipping_cost=base_shipping_cost if order_currency != "USD" else None,
            shipping_address_id=shipping_address_id,
            shipping_address=shipping_address_snapshot,
            billing_address=billing_address,
            shipping_rate_id=shipping_rate_id,
            estimated_delivery=estimated_delivery,
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

        order = await self.db.scalar(
            select(Order).where(Order.id == order.id).options(selectinload(Order.items))
        )
        assert order is not None
        result = _order_to_dict(order)

        from src.notifications.service import enqueue_order_confirmation

        await enqueue_order_confirmation(result, customer.email)

        logger.info(
            "order_created",
            order_id=str(order.id),
            customer_id=str(customer.id),
            total=float(order.total_amount),
            items=len(order_items_data),
        )

        # Auto-generate invoice document
        try:
            from src.docs.constants import DocumentType
            from src.docs.service import DocumentService

            doc_service = DocumentService(self.db)

            await doc_service.create_from_order(
                order_id=order.id,
                customer_id=customer.id,
                items=order_items_data,
                subtotal=subtotal,
                tax_amount=0.0,
                total_amount=float(order.total_amount),
                billing_address=order.billing_address or order.shipping_address,
                document_type=DocumentType.INVOICE,
            )
        except Exception:
            logger.exception("invoice_generation_failed", order_id=str(order.id))

        return result

    async def get_order_by_id(self, order_id: uuid.UUID) -> Order:
        order = await self.db.scalar(
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        if not order:
            raise OrderNotFound()
        return order

    async def get_by_order_number(self, order_number: str) -> Order:
        """Look up an order by its display number (e.g., 'ORD-001042')."""
        # Parse the numeric part from "ORD-NNNNNN"
        try:
            display_id = int(order_number.upper().replace("ORD-", ""))
        except ValueError:
            raise OrderNotFound() from None

        order = await self.db.scalar(
            select(Order).where(Order.display_id == display_id).options(selectinload(Order.items))
        )
        if not order:
            raise OrderNotFound()
        return order

    async def update_status(self, order_id: uuid.UUID, status: OrderStatus) -> dict:
        order = await self.get_order_by_id(order_id)
        previous_status = order.status
        order.status = status
        await self.db.commit()
        order = await self.db.scalar(
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        assert order is not None
        result = _order_to_dict(order)

        if status == OrderStatus.SHIPPED and previous_status != OrderStatus.SHIPPED:
            from src.customers.service import CustomerService
            from src.notifications.service import enqueue_dispatch

            customer_service = CustomerService(self.db)
            customer = await customer_service.get_by_id(order.customer_id)
            await enqueue_dispatch(result, customer.email)

        logger.info(
            "order_status_changed",
            order_id=str(order_id),
            previous=previous_status,
            new=status.value,
        )

        return result

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
        count = (
            await self.db.scalar(
                select(func.count(Order.id)).where(Order.customer_id == customer.id)
            )
            or 0
        )
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

    async def get_all_orders(self, page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
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
        "display_id": order.display_id,
        "order_number": order.order_number,
        "customer_id": str(order.customer_id),
        "status": order.status.value if hasattr(order.status, "value") else order.status,
        "currency": order.currency,
        "exchange_rate": float(order.exchange_rate) if order.exchange_rate else None,
        "total_amount": float(order.total_amount),
        "subtotal": float(order.subtotal),
        "tax_amount": float(order.tax_amount),
        "shipping_cost": float(order.shipping_cost),
        "base_total_amount": float(order.base_total_amount) if order.base_total_amount else None,
        "base_subtotal": float(order.base_subtotal) if order.base_subtotal else None,
        "base_tax_amount": float(order.base_tax_amount) if order.base_tax_amount else None,
        "base_shipping_cost": float(order.base_shipping_cost) if order.base_shipping_cost else None,
        "shipping_address": order.shipping_address,
        "billing_address": order.billing_address,
        "shipping_rate_id": (str(order.shipping_rate_id) if order.shipping_rate_id else None),
        "estimated_delivery": (
            order.estimated_delivery.isoformat() if order.estimated_delivery else None
        ),
        "items": [
            {
                "id": item.id,
                "product_id": str(item.product_id),
                "variant_id": str(item.variant_id) if item.variant_id else None,
                "variant_sku": item.variant_sku,
                "product_name": item.product_name,
                "product_price": float(item.product_price),
                "line_total": float(item.line_total),
                "quantity": item.quantity,
            }
            for item in order.items
        ],
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
    }
