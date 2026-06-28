import uuid
from typing import Annotated

from fastapi import Depends, Path
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from src.config import settings
from src.customers.exceptions import AddressNotFound, InactiveCustomer, InvalidCustomerCredentials
from src.customers.models import Address, Customer
from src.customers.service import CustomerService
from src.database import DbDep

customer_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/customers/login", auto_error=False
)


async def get_current_customer(
    db: DbDep,
    token: Annotated[str | None, Depends(customer_scheme)] = None,
) -> Customer:
    if not token:
        raise InvalidCustomerCredentials()

    from src.auth.utils import decode_token

    payload = decode_token(token)
    customer_id = payload.get("sub")
    if not customer_id:
        raise InvalidCustomerCredentials()

    service = CustomerService(db)
    customer = await service.get_by_id(customer_id)
    if not customer:
        raise InvalidCustomerCredentials()
    if not customer.is_active:
        raise InactiveCustomer()
    return customer


CurrentCustomerDep = Annotated[Customer, Depends(get_current_customer)]


async def valid_address_id(
    address_id: Annotated[uuid.UUID, Path(description="Address ID")],
    db: DbDep,
) -> Address:
    address = await db.scalar(select(Address).where(Address.id == address_id))
    if not address:
        raise AddressNotFound()
    return address


ValidAddressIdDep = Annotated[Address, Depends(valid_address_id)]
