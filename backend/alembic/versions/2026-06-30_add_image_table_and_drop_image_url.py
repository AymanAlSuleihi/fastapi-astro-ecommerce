"""add_image_table_and_drop_image_url

Revision ID: 6b2cd2116bba
Revises: 91990442a702
Create Date: 2026-06-30 01:16:07.904390

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b2cd2116bba'
down_revision: Union[str, Sequence[str], None] = '91990442a702'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "image",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("alt_text", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("parent_id", sa.Uuid(), sa.ForeignKey("image.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_image_entity", "image", ["entity_type", "entity_id"])
    op.drop_column("product", "image_url")


def downgrade() -> None:
    op.add_column("product", sa.Column("image_url", sa.String(length=2048), nullable=True))
    op.drop_table("image")


def downgrade() -> None:
    """Downgrade schema."""
    pass
