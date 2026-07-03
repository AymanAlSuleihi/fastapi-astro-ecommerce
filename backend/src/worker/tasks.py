"""Background tasks executed by the Taskiq worker."""

from contextlib import suppress

from src.worker.settings import broker


@broker.task(task_name="fetch_exchange_rates")
async def fetch_exchange_rates() -> int:
    """Fetch latest exchange rates from exchangerate-api.com."""
    import os

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from src.config import settings as app_settings
    from src.currencies.service import ExchangeRateService

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://ecommerce:ecommerce@db:5432/ecommerce",
    )
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        service = ExchangeRateService(session)
        count = await service.fetch_live_rates(app_settings.DEFAULT_CURRENCY)

    await engine.dispose()
    return count


@broker.task(task_name="send_password_reset_email")
async def send_password_reset_email(email: str, reset_url: str) -> None:
    """Send password reset email via Resend."""
    from src.notifications.service import send_password_reset

    send_password_reset(email, reset_url)


@broker.task(task_name="send_order_confirmation_email")
async def send_order_confirmation_email(order: dict, customer_email: str) -> None:
    """Send order confirmation email via Resend."""
    from src.notifications.service import send_order_confirmation

    send_order_confirmation(order, customer_email)


@broker.task(task_name="send_dispatch_email")
async def send_dispatch_email(order: dict, customer_email: str) -> None:
    """Send shipping dispatch notification via Resend."""
    from src.notifications.service import send_dispatch_notification

    send_dispatch_notification(order, customer_email)


@broker.task(task_name="generate_thumbnails")
async def generate_thumbnails(
    image_id: str, entity_type: str, entity_id: str, base_key: str
) -> None:
    """Generate thumbnail variants for an uploaded image."""
    from src.database import SessionFactory
    from src.images.exceptions import ImageNotFound
    from src.images.service import ImageService

    async with SessionFactory() as session:
        with suppress(ImageNotFound):
            await ImageService(session).generate_thumbnails(
                image_id, entity_type, entity_id, base_key
            )
