import os
import uuid
from unittest.mock import AsyncMock, patch

# Override DB for tests before any src imports
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://ecommerce:ecommerce@localhost:5432/ecommerce_test"
)

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.database import get_db
from src.main import app
from src.models import Base

TEST_DATABASE_URL = os.environ["DATABASE_URL"]


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    test_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Seed user for admin tests
    async with test_session_factory() as seed_session:
        from sqlalchemy import select

        from src.admin.models import User
        from src.auth.utils import hash_password

        existing = await seed_session.scalar(select(User).where(User.email == "admin@example.com"))
        if not existing:
            admin = User(
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
                first_name="Store",
                last_name="Admin",
                is_admin=True,
                is_active=True,
            )
            seed_session.add(admin)
            await seed_session.commit()

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
def fake_user_id():
    return uuid.uuid4()


@pytest.fixture(autouse=True)
def _mock_enqueue():
    """Mock all task enqueues so tests don't need Valkey."""
    with (
        patch("src.worker.tasks.generate_thumbnails.kiq", new=AsyncMock()),
        patch("src.notifications.service.enqueue_order_confirmation", new=AsyncMock()),
        patch("src.notifications.service.enqueue_dispatch", new=AsyncMock()),
        patch("src.notifications.service.enqueue_password_reset", new=AsyncMock()),
    ):
        yield
