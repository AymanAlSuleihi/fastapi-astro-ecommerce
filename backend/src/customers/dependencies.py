import uuid
from typing import Annotated

from fastapi import Depends, Path

from src.customers.models import Address
from src.database import DbDep


async def valid_address_id(
    address_id: Annotated[uuid.UUID, Path(description="Address ID")],
    db: DbDep,
) -> Address:
    from sqlalchemy import select

    address = await db.scalar(select(Address).where(Address.id == address_id))
    if not address:
        from src.customers.exceptions import AddressNotFound

        raise AddressNotFound()
    return address


ValidAddressIdDep = Annotated[Address, Depends(valid_address_id)]
