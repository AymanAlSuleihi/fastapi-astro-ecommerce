import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.cart.exceptions import CartItemNotFound
from src.cart.models import Cart, CartItem
from src.cart.schemas import CartItemCreate
from src.customers.models import Customer
from src.database import DbDep
from src.products.service import ProductService


class CartService:
    def __init__(self, db: DbDep):
        self.db = db

    async def get_cart_with_items(self, cart_id: str) -> Cart:
        """Fetch a Cart ORM object with its items eagerly loaded."""
        result = await self.db.execute(
            select(Cart).where(Cart.id == uuid.UUID(cart_id)).options(selectinload(Cart.items))
        )
        cart = result.scalars().first()
        assert cart is not None
        return cart

    async def get_or_create_cart(
        self, customer: Customer | None = None, session_id: str | None = None
    ) -> dict:
        if customer:
            result = await self.db.execute(select(Cart.id).where(Cart.customer_id == customer.id))
            cart_id = result.scalar()
            if cart_id:
                return await self._build_cart_dict(cart_id)

            # Merge anonymous cart if session_id provided
            if session_id:
                result = await self.db.execute(
                    select(Cart.id).where(Cart.session_id == session_id, Cart.customer_id.is_(None))
                )
                anon_id = result.scalar()
                if anon_id:
                    await self.db.execute(
                        update(Cart)
                        .where(Cart.id == anon_id)
                        .values(customer_id=customer.id, session_id=None)
                    )
                    await self.db.commit()
                    return await self._build_cart_dict(anon_id)

            new_cart = Cart(customer_id=customer.id)
            self.db.add(new_cart)
            await self.db.commit()
            return {
                "id": str(new_cart.id),
                "customer_id": str(customer.id),
                "session_id": None,
                "items": [],
            }

        if session_id:
            result = await self.db.execute(
                select(Cart.id).where(Cart.session_id == session_id, Cart.customer_id.is_(None))
            )
            cart_id = result.scalar()
            if cart_id:
                return await self._build_cart_dict(cart_id)

        new_cart = Cart(session_id=session_id or str(uuid.uuid4()))
        self.db.add(new_cart)
        await self.db.commit()
        return {
            "id": str(new_cart.id),
            "customer_id": None,
            "session_id": str(new_cart.session_id),
            "items": [],
        }

    def cart_to_dict(self, cart: Cart) -> dict:
        """Convert a Cart ORM object to a dict for API responses."""
        items = []
        subtotal = 0.0
        for item in cart.items:
            line = float(item.unit_price * item.quantity)
            subtotal += line
            items.append(
                {
                    "id": item.id,
                    "product_id": str(item.product_id),
                    "product_name": item.product.name,
                    "product_slug": item.product.slug,
                    "product_image_url": None,  # TODO: Get from image service
                    "variant_id": str(item.variant_id),
                    "variant_sku": item.variant.sku,
                    "unit_price": float(item.unit_price),
                    "quantity": item.quantity,
                    "line_total": round(line, 2),
                }
            )
        return {
            "id": str(cart.id),
            "customer_id": str(cart.customer_id) if cart.customer_id else None,
            "session_id": cart.session_id,
            "items": items,
            "subtotal": round(subtotal, 2),
            "item_count": sum(i["quantity"] for i in items),
        }

    async def _build_cart_dict(self, cart_id) -> dict:
        cart = await self.get_cart_with_items(str(cart_id))
        return self.cart_to_dict(cart)

    async def _get_or_create_cart_orm(
        self, customer: Customer | None = None, session_id: str | None = None
    ) -> Cart:
        if customer:
            cart = await self.db.scalar(
                select(Cart)
                .where(Cart.customer_id == customer.id)
                .options(selectinload(Cart.items).selectinload(CartItem.product))
            )
            if cart:
                return cart

            # Merge anonymous cart if session_id provided
            if session_id:
                anon_cart = await self.db.scalar(
                    select(Cart)
                    .where(Cart.session_id == session_id, Cart.customer_id.is_(None))
                    .options(selectinload(Cart.items).selectinload(CartItem.product))
                )
                if anon_cart:
                    anon_cart.customer_id = customer.id
                    anon_cart.session_id = None
                    await self.db.commit()
                    return anon_cart

            cart = Cart(customer_id=customer.id)
            self.db.add(cart)
            await self.db.commit()
            await self.db.refresh(
                cart,
                ["id", "customer_id", "session_id", "created_at", "updated_at"],
            )
            _ = cart.items  # force load within session
            return cart

        if session_id:
            cart = await self.db.scalar(
                select(Cart)
                .where(Cart.session_id == session_id, Cart.customer_id.is_(None))
                .options(selectinload(Cart.items).selectinload(CartItem.product))
            )
            if cart:
                return cart

        cart = Cart(session_id=session_id or str(uuid.uuid4()))
        self.db.add(cart)
        await self.db.commit()
        await self.db.refresh(cart, ["id", "customer_id", "session_id", "created_at", "updated_at"])
        _ = cart.items  # force load within session
        return cart

    async def add_item(self, cart: Cart, data: CartItemCreate) -> CartItem:
        await ProductService(self.db).validate_stock(data.product_id, data.quantity)

        # Resolve default variant if not provided
        variant_id = data.variant_id
        variant_price = None
        from src.products.models import ProductVariant

        if variant_id:
            variant = await self.db.scalar(
                select(ProductVariant).where(ProductVariant.id == variant_id)
            )
            if variant:
                variant_price = variant.price_override
        if not variant_id:
            variant_id = await self.db.scalar(
                select(ProductVariant.id).where(
                    ProductVariant.product_id == data.product_id,
                    ProductVariant.is_default.is_(True),
                )
            )
            if not variant_id:
                variant_id = await self.db.scalar(
                    select(ProductVariant.id)
                    .where(ProductVariant.product_id == data.product_id)
                    .order_by(ProductVariant.created_at)
                )
            if not variant_id:
                raise ValueError(f"No variant found for product {data.product_id}")

        if variant_price is None:
            product = await self.db.scalar(
                select(ProductVariant).where(ProductVariant.id == variant_id)
            )
            if product:
                variant_price = product.price_override

        # Look up base product price as fallback
        unit_price = variant_price
        if unit_price is None:
            from src.products.models import Product as ProductModel

            base = await self.db.scalar(
                select(ProductModel.price).where(ProductModel.id == data.product_id)
            )
            unit_price = float(base) if base else 0.0
        else:
            unit_price = float(unit_price)

        existing = await self.db.scalar(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == data.product_id,
                CartItem.variant_id == variant_id,
            )
        )
        if existing:
            existing.quantity += data.quantity
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        item = CartItem(
            cart_id=cart.id,
            product_id=data.product_id,
            variant_id=variant_id,
            unit_price=unit_price,
            quantity=data.quantity,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_quantity(self, cart: Cart, product_id: uuid.UUID, quantity: int) -> CartItem:
        item = await self.db.scalar(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        )
        if not item:
            raise CartItemNotFound()

        if quantity == 0:
            await self.db.delete(item)
            await self.db.commit()
            raise CartItemNotFound()

        item.quantity = quantity
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def remove_item(self, cart: Cart, product_id: uuid.UUID) -> None:
        item = await self.db.scalar(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        )
        if not item:
            raise CartItemNotFound()
        await self.db.delete(item)
        await self.db.commit()

    async def clear_cart(self, cart: Cart) -> None:
        for item in cart.items:
            await self.db.delete(item)
        await self.db.commit()
