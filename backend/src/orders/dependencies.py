import uuid
from typing import Annotated

from fastapi import Depends, Path

from src.database import DbDep
from src.orders.models import Order


async def valid_order_id(
    order_id: Annotated[uuid.UUID, Path(description="Order ID")],
    db: DbDep,
) -> Order:
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    order = await db.scalar(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    if not order:
        from src.orders.exceptions import OrderNotFound

        raise OrderNotFound()
    return order


ValidOrderIdDep = Annotated[Order, Depends(valid_order_id)]
