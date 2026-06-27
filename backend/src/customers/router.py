from fastapi import APIRouter, status

from src.auth.dependencies import CurrentUserDep
from src.customers.dependencies import ValidAddressIdDep
from src.customers.schemas import AddressCreate, AddressRead, AddressUpdate
from src.customers.service import CustomerService
from src.database import DbDep

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/addresses", response_model=list[AddressRead])
async def list_addresses(current_user: CurrentUserDep, db: DbDep):
    service = CustomerService(db)
    return await service.get_addresses(current_user)


@router.post("/addresses", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
async def create_address(data: AddressCreate, current_user: CurrentUserDep, db: DbDep):
    service = CustomerService(db)
    return await service.create_address(current_user, data)


@router.patch("/addresses/{address_id}", response_model=AddressRead)
async def update_address(
    data: AddressUpdate,
    address: ValidAddressIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
):
    if address.user_id != current_user.id:
        from src.exceptions import ForbiddenException

        raise ForbiddenException(detail="Not your address")
    service = CustomerService(db)
    return await service.update_address(address, data)


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address: ValidAddressIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
):
    if address.user_id != current_user.id:
        from src.exceptions import ForbiddenException

        raise ForbiddenException(detail="Not your address")
    service = CustomerService(db)
    await service.delete_address(address)
