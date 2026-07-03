"""Structured logging configuration with dual output: console + rotating file."""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import structlog

from src.config import settings


def _sanitize(_, __, event_dict: dict) -> dict:
    """Remove sensitive fields from log events."""
    for key in ("password", "token", "secret", "authorization", "hashed_password"):
        event_dict.pop(key, None)
    return event_dict


def configure_logging() -> None:
    """Set up structlog with console + file handlers. Call once at startup."""
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # ── File handler: JSON, daily rotation, 30 days retention ──
    file_handler = TimedRotatingFileHandler(
        filename=log_dir / "app.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
        )
    )

    # ── Console handler: colored in dev, plain otherwise ──
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    if settings.LOG_FORMAT == "console":
        console_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty()),
            )
        )
    else:
        console_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer(),
            )
        )

    # ── Root logger ──
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Disable noisy third-party loggers
    for name in ("boto3", "botocore", "urllib3", "resend", "aiosqlite"):
        logging.getLogger(name).setLevel(logging.WARNING)

    # ── structlog configuration ──
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            _sanitize,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name or __name__)
