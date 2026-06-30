from pathlib import Path

import resend
from jinja2 import Environment, FileSystemLoader

from src.notifications.config import notification_settings

resend.api_key = notification_settings.RESEND_API_KEY

_templates = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=True,
)


def _render(template_name: str, **context) -> str:
    template = _templates.get_template(template_name)
    return template.render(**context)


def _send(*, email: str, subject: str, html: str) -> None:
    if (
        not notification_settings.EMAIL_ENABLED
        or not notification_settings.RESEND_API_KEY
    ):
        return

    resend.Emails.send(
        {
            "from": (
                f"{notification_settings.EMAIL_FROM_NAME} "
                f"<{notification_settings.EMAIL_FROM_ADDRESS}>"
            ),
            "to": [email],
            "subject": subject,
            "html": html,
        }
    )


def send_order_confirmation(order: dict, customer_email: str) -> None:
    """Render and send the order confirmation email."""
    # Format date strings for the template
    order = dict(order)
    if order.get("created_at"):
        from datetime import datetime
        if isinstance(order["created_at"], str):
            try:
                dt = datetime.fromisoformat(order["created_at"])
                order["created_at"] = dt.strftime("%B %d, %Y at %H:%M")
            except ValueError:
                pass
    if order.get("estimated_delivery") and isinstance(
        order["estimated_delivery"], str
    ):
            try:
                dt = datetime.fromisoformat(order["estimated_delivery"])
                order["estimated_delivery"] = dt.strftime("%B %d, %Y")
            except ValueError:
                pass

    order["order_number"] = order["id"][:8]
    order["customer_name"] = order.get("customer_name", "Customer")

    html = _render("order_confirmation.html", order=order)
    _send(
        email=customer_email,
        subject=f"Order #{order['order_number']} Confirmed",
        html=html,
    )


def send_dispatch_notification(order: dict, customer_email: str) -> None:
    """Render and send the shipping dispatch email."""
    order = dict(order)
    if order.get("estimated_delivery"):
        from datetime import datetime
        if isinstance(order["estimated_delivery"], str):
            try:
                dt = datetime.fromisoformat(order["estimated_delivery"])
                order["estimated_delivery"] = dt.strftime("%B %d, %Y")
            except ValueError:
                pass

    order["order_number"] = order["id"][:8]

    html = _render("dispatch.html", order=order)
    _send(
        email=customer_email,
        subject=f"Order #{order['order_number']} Has Shipped",
        html=html,
    )


# ── Async enqueue helpers ──────────────────────────────────────────


async def enqueue_order_confirmation(order: dict, customer_email: str) -> None:
    """Enqueue order confirmation email via the task queue."""
    from src.worker.tasks import send_order_confirmation_email

    await send_order_confirmation_email.kiq(order, customer_email)


async def enqueue_dispatch(order: dict, customer_email: str) -> None:
    """Enqueue dispatch notification via the task queue."""
    from src.worker.tasks import send_dispatch_email

    await send_dispatch_email.kiq(order, customer_email)
