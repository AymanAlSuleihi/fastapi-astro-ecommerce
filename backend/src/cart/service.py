import uuid

from sqlalchemy import select
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

    async def get_or_create_cart(
        self, user: Customer | None = None, session_id: str | None = None
    ) -> dict:
        if user:
            cart = await self.db.scalar(
                select(Cart.id, Cart.customer_id, Cart.session_id).where(
                    Cart.customer_id == user.id
                )
            )
            if cart:
                cart_id, cart_customer_id, _ = cart
                return await self._build_cart_dict(cart_id)

            # Merge anonymous cart if session_id provided
            if session_id:
                anon = await self.db.scalar(
                    select(Cart.id, Cart.customer_id, Cart.session_id).where(
                        Cart.session_id == session_id, Cart.customer_id.is_(None)
                    )
                )
                if anon:
                    anon_id, _, _ = anon
                    await self.db.execute(
                        __import__("sqlalchemy")
                        .update(Cart)
                        .where(Cart.id == anon_id)
                        .values(customer_id=user.id, session_id=None)
                    )
                    await self.db.commit()
                    return await self._build_cart_dict(anon_id)

            new_cart = Cart(customer_id=user.id)
            self.db.add(new_cart)
            await self.db.commit()
            return {"id": str(new_cart.id), "customer_id": str(user.id), "items": []}

        if session_id:
            cart = await self.db.scalar(
                select(Cart.id, Cart.customer_id, Cart.session_id).where(
                    Cart.session_id == session_id, Cart.customer_id.is_(None)
                )
            )
            if cart:
                cart_id, _, _ = cart
                return await self._build_cart_dict(cart_id)

        new_cart = Cart(session_id=session_id or str(uuid.uuid4()))
        self.db.add(new_cart)
        await self.db.commit()
        return {"id": str(new_cart.id), "customer_id": None, "items": []}

    async def _build_cart_dict(self, cart_id) -> dict:
        cart = await self.db.scalar(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        assert cart is not None  # cart exists, was just created or fetched above
        return {
            "id": str(cart.id),
            "customer_id": str(cart.customer_id) if cart.customer_id else None,
            "items": [
                {
                    "id": item.id,
                    "product_id": str(item.product_id),
                    "quantity": item.quantity,
                }
                for item in cart.items
            ],
        }

    async def _get_or_create_cart_orm(
        self, user: Customer | None = None, session_id: str | None = None
    ) -> Cart:
        if user:
            cart = await self.db.scalar(
                select(Cart)
                .where(Cart.customer_id == user.id)
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
                    anon_cart.customer_id = user.id
                    anon_cart.session_id = None
                    await self.db.commit()
                    return anon_cart

            cart = Cart(customer_id=user.id)
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

        existing = await self.db.scalar(
            select(CartItem).where(
                CartItem.cart_id == cart.id, CartItem.product_id == data.product_id
            )
        )
        if existing:
            existing.quantity += data.quantity
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        item = CartItem(cart_id=cart.id, product_id=data.product_id, quantity=data.quantity)
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
