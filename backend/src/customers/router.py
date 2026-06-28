from fastapi import APIRouter, status

from src.customers.dependencies import CurrentCustomerDep, ValidAddressIdDep
from src.customers.schemas import (
    AddressCreate,
    AddressRead,
    AddressUpdate,
    CustomerCreate,
    CustomerLogin,
    CustomerRead,
    CustomerUpdate,
)
from src.customers.service import CustomerService
from src.database import DbDep

router = APIRouter(prefix="/customers", tags=["customers"])


# ── Auth ──────────────────────────────────────────────────


@router.post("/register", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def register(data: CustomerCreate, db: DbDep):
    service = CustomerService(db)
    return await service.register(data)


@router.post("/login")
async def login(data: CustomerLogin, db: DbDep):
    from src.auth.schemas import TokenResponse
    from src.auth.utils import create_access_token

    service = CustomerService(db)
    customer = await service.authenticate(data.email, data.password)
    token_data = {"sub": str(customer.id)}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token="",
        token_type="bearer",
    )


@router.get("/me", response_model=CustomerRead)
async def get_me(customer: CurrentCustomerDep):
    return customer


@router.patch("/me", response_model=CustomerRead)
async def update_me(data: CustomerUpdate, customer: CurrentCustomerDep, db: DbDep):
    if data.first_name is not None:
        customer.first_name = data.first_name
    if data.last_name is not None:
        customer.last_name = data.last_name
    if data.email is not None:
        customer.email = data.email
    if data.password is not None:
        from src.auth.utils import hash_password

        customer.hashed_password = hash_password(data.password)
    await db.commit()
    await db.refresh(customer)
    return customer


# ── Addresses ─────────────────────────────────────────────


@router.get("/addresses", response_model=list[AddressRead])
async def list_addresses(customer: CurrentCustomerDep, db: DbDep):
    service = CustomerService(db)
    return await service.get_addresses(customer)


@router.post("/addresses", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
async def create_address(data: AddressCreate, customer: CurrentCustomerDep, db: DbDep):
    service = CustomerService(db)
    return await service.create_address(customer, data)


@router.patch("/addresses/{address_id}", response_model=AddressRead)
async def update_address(
    data: AddressUpdate,
    address: ValidAddressIdDep,
    customer: CurrentCustomerDep,
    db: DbDep,
):
    if address.customer_id != customer.id:
        from src.exceptions import ForbiddenException

        raise ForbiddenException(detail="Not your address")
    service = CustomerService(db)
    return await service.update_address(address, data)


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address: ValidAddressIdDep,
    customer: CurrentCustomerDep,
    db: DbDep,
):
    if address.customer_id != customer.id:
        from src.exceptions import ForbiddenException

        raise ForbiddenException(detail="Not your address")
    service = CustomerService(db)
    await service.delete_address(address)
