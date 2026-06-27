import uuid

from sqlalchemy import select

from src.auth.exceptions import InactiveUser, InvalidCredentials, UserAlreadyExists
from src.auth.models import User
from src.auth.schemas import UserCreate
from src.auth.utils import hash_password, verify_password
from src.database import DbDep


class AuthService:
    def __init__(self, db: DbDep):
        self.db = db

    async def register(self, data: UserCreate) -> User:
        existing = await self.db.scalar(select(User).where(User.email == data.email))
        if existing:
            raise UserAlreadyExists()

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.db.scalar(select(User).where(User.email == email))
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentials()
        if not user.is_active:
            raise InactiveUser()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.db.scalar(select(User).where(User.id == user_id))
