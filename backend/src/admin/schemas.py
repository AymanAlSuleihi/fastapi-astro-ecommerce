from pydantic import BaseModel, ConfigDict


class DashboardStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_orders: int
    total_revenue: float
    total_users: int
    total_products: int


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    first_name: str
    last_name: str
    is_admin: bool
    is_active: bool
