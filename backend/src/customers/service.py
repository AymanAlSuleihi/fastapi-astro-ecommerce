import uuid

from sqlalchemy import select, update

from src.auth.models import User
from src.customers.exceptions import AddressNotFound
from src.customers.models import Address
from src.customers.schemas import AddressCreate, AddressUpdate
from src.database import DbDep


class CustomerService:
    def __init__(self, db: DbDep):
        self.db = db

    async def get_addresses(self, user: User) -> list[Address]:
        result = await self.db.execute(
            select(Address).where(Address.user_id == user.id).order_by(Address.is_default.desc())
        )
        return list(result.scalars().all())

    async def create_address(self, user: User, data: AddressCreate) -> Address:
        if data.is_default:
            await self._clear_default(user.id)
        address = Address(user_id=user.id, **data.model_dump())
        self.db.add(address)
        await self.db.commit()
        await self.db.refresh(address)
        return address

    async def update_address(self, address: Address, data: AddressUpdate) -> Address:
        if data.is_default:
            await self._clear_default(address.user_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(address, key, value)
        await self.db.commit()
        await self.db.refresh(address)
        return address

    async def delete_address(self, address: Address) -> None:
        await self.db.delete(address)
        await self.db.commit()

    async def get_address_by_id(self, address_id: uuid.UUID, user: User) -> Address:
        address = await self.db.scalar(
            select(Address).where(Address.id == address_id, Address.user_id == user.id)
        )
        if not address:
            raise AddressNotFound()
        return address

    async def _clear_default(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Address)
            .where(Address.user_id == user_id, Address.is_default.is_(True))
            .values(is_default=False)
        )
