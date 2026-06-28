import uuid

from sqlalchemy import select, update

from src.customers.exceptions import (
    AddressNotFound,
    CustomerAlreadyExists,
    InactiveCustomer,
    InvalidCustomerCredentials,
)
from src.customers.models import Address, Customer
from src.customers.schemas import AddressCreate, AddressUpdate, CustomerCreate
from src.database import DbDep


class CustomerService:
    def __init__(self, db: DbDep):
        self.db = db

    # ── Auth ───────────────────────────────────────────────

    async def register(self, data: CustomerCreate) -> Customer:
        existing = await self.db.scalar(select(Customer).where(Customer.email == data.email))
        if existing:
            raise CustomerAlreadyExists()

        from src.auth.utils import hash_password

        customer = Customer(
            email=data.email,
            hashed_password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
        )
        self.db.add(customer)
        await self.db.commit()
        await self.db.refresh(customer)
        return customer

    async def authenticate(self, email: str, password: str) -> Customer:
        from src.auth.utils import verify_password

        customer = await self.db.scalar(select(Customer).where(Customer.email == email))
        if not customer or not verify_password(password, customer.hashed_password):
            raise InvalidCustomerCredentials()
        if not customer.is_active:
            raise InactiveCustomer()
        return customer

    async def get_by_id(self, customer_id: uuid.UUID) -> Customer | None:
        return await self.db.scalar(select(Customer).where(Customer.id == customer_id))

    # ── Addresses ──────────────────────────────────────────

    async def get_addresses(self, customer: Customer) -> list[Address]:
        result = await self.db.execute(
            select(Address)
            .where(Address.customer_id == customer.id)
            .order_by(Address.is_default.desc())
        )
        return list(result.scalars().all())

    async def create_address(self, customer: Customer, data: AddressCreate) -> Address:
        if data.is_default:
            await self._clear_default(customer.id)
        address = Address(customer_id=customer.id, **data.model_dump())
        self.db.add(address)
        await self.db.commit()
        await self.db.refresh(address)
        return address

    async def update_address(self, address: Address, data: AddressUpdate) -> Address:
        if data.is_default:
            await self._clear_default(address.customer_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(address, key, value)
        await self.db.commit()
        await self.db.refresh(address)
        return address

    async def delete_address(self, address: Address) -> None:
        await self.db.delete(address)
        await self.db.commit()

    async def get_address_by_id(self, address_id: uuid.UUID, customer: Customer) -> Address:
        address = await self.db.scalar(
            select(Address).where(Address.id == address_id, Address.customer_id == customer.id)
        )
        if not address:
            raise AddressNotFound()
        return address

    async def _clear_default(self, customer_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Address)
            .where(Address.customer_id == customer_id, Address.is_default.is_(True))
            .values(is_default=False)
        )
