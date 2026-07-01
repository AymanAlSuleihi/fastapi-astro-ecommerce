from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.admin.dependencies import CurrentAdminDep
from src.cart.dependencies import CartDep
from src.customers.dependencies import CurrentCustomerDep, customer_scheme
from src.database import DbDep
from src.exceptions import BadRequestException
from src.orders.dependencies import ValidOrderIdDep
from src.orders.schemas import OrderCreate, OrderList, OrderRead, OrderStatusUpdate
from src.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    cart: CartDep,
    db: DbDep,
    token: Annotated[str | None, Depends(customer_scheme)] = None,
):
    from src.customers.service import CustomerService

    customer_service = CustomerService(db)

    if token:
        from src.customers.dependencies import get_current_customer

        current_customer = await get_current_customer(db, token)
        if not current_customer:
            raise BadRequestException(detail="Invalid authentication")
        customer = current_customer
    elif data.email and data.first_name and data.last_name:
        customer = await customer_service.get_by_email(data.email)
        if not customer:
            customer = await customer_service.create_guest(
                email=data.email,
                first_name=data.first_name,
                last_name=data.last_name,
            )
    else:
        raise BadRequestException(detail="Authentication required or provide guest checkout info")

    service = OrderService(db)
    return await service.create_order(
        customer,
        cart,
        shipping_address_id=data.shipping_address_id,
        shipping_rate_id=data.shipping_rate_id,
    )


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
