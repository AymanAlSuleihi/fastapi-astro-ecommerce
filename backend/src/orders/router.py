from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from src.admin.dependencies import CurrentAdminDep
from src.cart.dependencies import CartDep
from src.customers.dependencies import CurrentCustomerDep
from src.database import DbDep
from src.orders.dependencies import ValidOrderIdDep
from src.orders.schemas import OrderList, OrderRead, OrderStatusUpdate
from src.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    current_customer: CurrentCustomerDep,
    cart: CartDep,
    db: DbDep,
    shipping_address_id: UUID | None = None,
):
    service = OrderService(db)
    return await service.create_order(current_customer, cart, shipping_address_id)


@router.get("/", response_model=OrderList)
async def list_orders(
    current_customer: CurrentCustomerDep,
    db: DbDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    service = OrderService(db)
    items, total = await service.get_user_orders(current_customer, page=page, page_size=page_size)
    return OrderList(items=items, total=total, page=page, page_size=page_size)


@router.get("/all", response_model=OrderList)
async def list_all_orders(
    db: DbDep,
    _admin: CurrentAdminDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    service = OrderService(db)
    items, total = await service.get_all_orders(page=page, page_size=page_size)
    return OrderList(items=items, total=total, page=page, page_size=page_size)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(order: ValidOrderIdDep, current_customer: CurrentCustomerDep):
    if order.customer_id != current_customer.id:
        from src.exceptions import ForbiddenException

        raise ForbiddenException(detail="Not your order")
    return order


@router.patch("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: UUID,
    current_customer: CurrentCustomerDep,
    db: DbDep,
):
    service = OrderService(db)
    return await service.cancel_order(current_customer, order_id)



@router.patch("/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    data: OrderStatusUpdate,
    order: ValidOrderIdDep,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = OrderService(db)
    return await service.update_status(order.id, data.status)
