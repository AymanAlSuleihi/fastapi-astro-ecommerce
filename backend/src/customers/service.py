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
        from src.auth.utils import hash_password

        existing = await self.db.scalar(select(Customer).where(Customer.email == data.email))
        if existing:
            if existing.is_guest:
                existing.hashed_password = hash_password(data.password)
                existing.first_name = data.first_name
                existing.last_name = data.last_name
                existing.is_guest = False
                await self.db.commit()
                await self.db.refresh(existing)
                return existing
            raise CustomerAlreadyExists()

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
        if (
            not customer
            or not customer.hashed_password
            or not verify_password(password, customer.hashed_password)
        ):
            raise InvalidCustomerCredentials()
        if not customer.is_active:
            raise InactiveCustomer()
        return customer

    async def get_by_id(self, customer_id: uuid.UUID) -> Customer | None:
        return await self.db.scalar(select(Customer).where(Customer.id == customer_id))

    async def get_by_email(self, email: str) -> Customer | None:
        return await self.db.scalar(select(Customer).where(Customer.email == email))

    async def reset_password(self, token: str, new_password: str) -> None:
        """Validate a reset token and set a new password."""
        from src.auth.exceptions import InvalidResetToken
        from src.auth.utils import hash_password, verify_reset_token

        payload = verify_reset_token(token)
        sub = payload.get("sub")
        if not sub:
            raise InvalidResetToken()

        customer = await self.get_by_id(uuid.UUID(sub))
        if not customer or not customer.hashed_password:
            raise InvalidResetToken()

        customer.hashed_password = hash_password(new_password)
        await self.db.commit()

    async def create_guest(self, email: str, first_name: str, last_name: str) -> Customer:
        customer = Customer(
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_guest=True,
            is_active=True,
        )
        self.db.add(customer)
        await self.db.commit()
        await self.db.refresh(customer)
        return customer

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
