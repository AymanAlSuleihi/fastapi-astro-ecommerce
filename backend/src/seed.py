import asyncio
import os
from pathlib import Path

from alembic.config import Config
from sqlalchemy import select

from alembic import command
from src.admin.models import User
from src.auth.utils import hash_password
from src.config import settings
from src.database import SessionFactory


def _get_alembic_cfg() -> Config:
    ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"
    cfg = Config(str(ini_path))
    db_url = os.getenv("DATABASE_URL", "")
    if db_url:
        cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


async def run_migrations() -> None:
    """Apply any pending Alembic migrations."""
    cfg = _get_alembic_cfg()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, command.upgrade, cfg, "head")


async def seed_initial_data() -> None:
    """Idempotent seed: superuser."""
    async with SessionFactory() as db:
        existing = await db.scalar(select(User).where(User.email == settings.SUPERUSER_EMAIL))
        if not existing:
            admin = User(
                email=settings.SUPERUSER_EMAIL,
                hashed_password=hash_password(settings.SUPERUSER_PASSWORD),
                first_name="Store",
                last_name="Admin",
                is_admin=True,
                is_active=True,
            )
            db.add(admin)
            await db.commit()
