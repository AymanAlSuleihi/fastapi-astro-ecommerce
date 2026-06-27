from uuid import UUID

from fastapi import APIRouter, status

from src.auth.dependencies import CurrentAdminDep, CurrentUserDep
from src.database import DbDep
from src.orders.dependencies import ValidOrderIdDep
from src.orders.schemas import OrderRead, OrderStatusUpdate
from src.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    current_user: CurrentUserDep,
    db: DbDep,
    shipping_address_id: UUID | None = None,
):
    service = OrderService(db)
    return await service.create_order(current_user, shipping_address_id)


@router.get("/", response_model=list[OrderRead])
async def list_orders(current_user: CurrentUserDep, db: DbDep):
    service = OrderService(db)
    return await service.get_user_orders(current_user)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(order: ValidOrderIdDep, current_user: CurrentUserDep):
    if order.user_id != current_user.id and not current_user.is_admin:
        from src.exceptions import ForbiddenException

        raise ForbiddenException(detail="Not your order")
    return order


@router.patch("/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    data: OrderStatusUpdate,
    order: ValidOrderIdDep,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = OrderService(db)
    return await service.update_status(order.id, data.status)
