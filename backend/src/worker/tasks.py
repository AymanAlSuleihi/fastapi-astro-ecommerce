from src.worker.settings import broker


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
        try:
            await ImageService(session).generate_thumbnails(
                image_id, entity_type, entity_id, base_key
            )
        except ImageNotFound:
            pass  # Image deleted before task ran
