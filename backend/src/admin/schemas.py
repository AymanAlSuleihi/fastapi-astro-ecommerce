import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ── Admin Auth ──────────────────────────────────────────


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)
    is_admin: bool = True
    is_active: bool = True


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    is_admin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=128)
    last_name: str | None = Field(default=None, min_length=1, max_length=128)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_admin: bool | None = None
    is_active: bool | None = None


# ── Dashboard ──────────────────────────────────────────


class DashboardStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_orders: int
    total_revenue: float
    total_customers: int
    total_products: int
