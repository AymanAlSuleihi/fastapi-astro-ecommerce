"""add_multi_currency_support

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-01 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Exchange rate table
    op.create_table(
        "exchange_rate",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("target_currency", sa.String(length=3), nullable=False),
        sa.Column("rate", sa.DECIMAL(14, 8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("base_currency", "target_currency"),
    )

    # Order: currency + exchange_rate
    op.add_column("order", sa.Column("currency", sa.String(length=3), nullable=True))
    op.add_column("order", sa.Column("exchange_rate", sa.DECIMAL(14, 8), nullable=True))

    # Order: base equivalents
    op.add_column(
        "order",
        sa.Column("base_subtotal", sa.DECIMAL(12, 2), nullable=True),
    )
    op.add_column(
        "order",
        sa.Column("base_shipping_cost", sa.DECIMAL(8, 2), nullable=True),
    )
    op.add_column(
        "order",
        sa.Column("base_tax_amount", sa.DECIMAL(12, 2), nullable=True),
    )
    op.add_column(
        "order",
        sa.Column("base_total_amount", sa.DECIMAL(12, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("order", "base_total_amount")
    op.drop_column("order", "base_tax_amount")
    op.drop_column("order", "base_shipping_cost")
    op.drop_column("order", "base_subtotal")
    op.drop_column("order", "exchange_rate")
    op.drop_column("order", "currency")
    op.drop_table("exchange_rate")
