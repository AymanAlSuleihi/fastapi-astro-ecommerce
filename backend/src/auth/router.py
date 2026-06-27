from fastapi import APIRouter, status

from src.auth.dependencies import CurrentUserDep
from src.auth.schemas import TokenResponse, UserCreate, UserLogin, UserRead, UserUpdate
from src.auth.service import AuthService
from src.auth.utils import create_access_token, create_refresh_token
from src.database import DbDep

router = APIRouter(prefix="/auth", tags=["auth"])


def _create_tokens(user_id: str) -> TokenResponse:
    token_data = {"sub": user_id}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: DbDep):
    service = AuthService(db)
    return await service.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: DbDep):
    service = AuthService(db)
    user = await service.authenticate(data.email, data.password)
    return _create_tokens(str(user.id))


@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUserDep):
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_me(data: UserUpdate, current_user: CurrentUserDep, db: DbDep):
    if data.first_name is not None:
        current_user.first_name = data.first_name
    if data.last_name is not None:
        current_user.last_name = data.last_name
    if data.email is not None:
        current_user.email = data.email
    if data.password is not None:
        from src.auth.utils import hash_password

        current_user.hashed_password = hash_password(data.password)
    await db.commit()
    await db.refresh(current_user)
    return current_user
