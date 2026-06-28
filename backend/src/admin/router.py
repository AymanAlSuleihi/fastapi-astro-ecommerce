from fastapi import APIRouter, Query, status
from sqlalchemy import func, select

from src.admin.dependencies import CurrentAdminDep
from src.admin.models import User
from src.admin.schemas import (
    AdminLogin,
    DashboardStats,
    UserCreate,
    UserRead,
    UserUpdate,
)
from src.auth.schemas import TokenResponse
from src.auth.utils import create_access_token, hash_password, verify_password
from src.database import DbDep

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Auth ──────────────────────────────────────────────────

@router.post("/login")
async def admin_login(data: AdminLogin, db: DbDep):
    admin = await db.scalar(select(User).where(User.email == data.email))
    if not admin or not verify_password(data.password, admin.hashed_password):
        from src.exceptions import BadRequestException

        raise BadRequestException(
            detail="Invalid credentials", code="INVALID_CREDENTIALS"
        )
    token_data = {"sub": str(admin.id)}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token="",
        token_type="bearer",
    )


# ── Admin Users ───────────────────────────────────────────

@router.get("/users", response_model=list[UserRead])
async def list_admin_users(db: DbDep, _admin: CurrentAdminDep):
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_admin_user(data: UserCreate, db: DbDep, _admin: CurrentAdminDep):
    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing:
        from src.exceptions import ConflictException

        raise ConflictException(
            detail="A user with this email already exists", code="USER_ALREADY_EXISTS"
        )
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        is_admin=data.is_admin,
        is_active=data.is_active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_admin_user(
    user_id: str, data: UserUpdate, db: DbDep, _admin: CurrentAdminDep
):
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        from src.exceptions import NotFoundException

        raise NotFoundException(detail="User not found")
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.email is not None:
        user.email = data.email
    if data.password is not None:
        user.hashed_password = hash_password(data.password)
    if data.is_admin is not None:
        user.is_admin = data.is_admin
    if data.is_active is not None:
        user.is_active = data.is_active
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_user(user_id: str, db: DbDep, _admin: CurrentAdminDep):
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        from src.exceptions import NotFoundException

        raise NotFoundException(detail="User not found")
    await db.delete(user)
    await db.commit()


# ── Dashboard ─────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(db: DbDep, _admin: CurrentAdminDep):
    from src.customers.models import Customer
    from src.orders.models import Order
    from src.products.models import Product

    total_orders = await db.scalar(select(func.count(Order.id)))
    total_revenue = await db.scalar(
        select(func.coalesce(func.sum(Order.total_amount), 0))
    )
    total_users = await db.scalar(select(func.count(Customer.id)))
    total_products = await db.scalar(select(func.count(Product.id)))

    return DashboardStats(
        total_orders=total_orders or 0,
        total_revenue=float(total_revenue or 0),
        total_users=total_users or 0,
        total_products=total_products or 0,
    )


# ── Customers ─────────────────────────────────────────────

@router.get("/customers", response_model=list[UserRead])
async def list_customers(
    db: DbDep,
    _admin: CurrentAdminDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    from src.customers.models import Customer

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Customer)
        .offset(offset)
        .limit(page_size)
        .order_by(Customer.created_at.desc())
    )
    return list(result.scalars().all())


@router.patch("/customers/{customer_id}", response_model=UserRead)
async def toggle_customer_active(
    customer_id: str, db: DbDep, _admin: CurrentAdminDep
):
    from src.customers.models import Customer

    customer = await db.scalar(
        select(Customer).where(Customer.id == customer_id)
    )
    if not customer:
        from src.exceptions import NotFoundException

        raise NotFoundException(detail="Customer not found")

    customer.is_active = not customer.is_active
    await db.commit()
    await db.refresh(customer)
    return customer
