from typing import Any

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base, TimestampMixin, UUIDMixin


class StoreSetting(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "store_setting"
    __table_args__ = (UniqueConstraint("key"),)

    key: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    value: Mapped[Any] = mapped_column(JSONB, nullable=False, default=dict)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    section: Mapped[str] = mapped_column(String(64), default="general", nullable=False)
