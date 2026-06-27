from fastapi import APIRouter, Depends, Query

from src.admin.schemas import AdminUserRead, DashboardStats
from src.auth.dependencies import CurrentAdminDep
from src.database import DbDep

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(CurrentAdminDep)],
)


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(db: DbDep):
    from sqlalchemy import func, select

    from src.auth.models import User
    from src.orders.models import Order
    from src.products.models import Product

    total_orders = await db.scalar(select(func.count(Order.id)))
    total_revenue = await db.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)))
    total_users = await db.scalar(select(func.count(User.id)))
    total_products = await db.scalar(select(func.count(Product.id)))

    return DashboardStats(
        total_orders=total_orders or 0,
        total_revenue=float(total_revenue or 0),
        total_users=total_users or 0,
        total_products=total_products or 0,
    )


@router.get("/users", response_model=list[AdminUserRead])
async def list_users(
    db: DbDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    from sqlalchemy import select

    from src.auth.models import User

    offset = (page - 1) * page_size
    result = await db.execute(
        select(User).offset(offset).limit(page_size).order_by(User.created_at.desc())
    )
    return list(result.scalars().all())


@router.patch("/users/{user_id}", response_model=AdminUserRead)
async def toggle_user_active(user_id: str, db: DbDep):
    from sqlalchemy import select

    from src.auth.models import User

    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        from src.exceptions import NotFoundException

        raise NotFoundException(detail="User not found")

    user.is_active = not user.is_active
    await db.commit()
    await db.refresh(user)
    return user
