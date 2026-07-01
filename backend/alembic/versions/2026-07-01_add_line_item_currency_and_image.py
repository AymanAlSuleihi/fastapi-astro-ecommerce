"""add_line_item_currency_and_image

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-01 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: str | Sequence[str] | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "order_item", sa.Column("currency", sa.String(length=3), nullable=True)
    )
    op.add_column(
        "order_item",
        sa.Column("product_image_url", sa.String(length=2048), nullable=True),
    )
    op.add_column(
        "document_item", sa.Column("currency", sa.String(length=3), nullable=True)
    )
    op.add_column(
        "document_item",
        sa.Column("product_image_url", sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("document_item", "product_image_url")
    op.drop_column("document_item", "currency")
    op.drop_column("order_item", "product_image_url")
    op.drop_column("order_item", "currency")
