import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base, TimestampMixin, UUIDMixin


class Image(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "image"

    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("image.id", ondelete="SET NULL"), nullable=True
    )

    parent: Mapped[Image | None] = relationship(
        "Image", remote_side="Image.id", back_populates="children"
    )
    children: Mapped[list[Image]] = relationship("Image", back_populates="parent", lazy="selectin")
