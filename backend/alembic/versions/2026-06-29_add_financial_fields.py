"""add_financial_fields

Revision ID: 414ce9f68bb4
Revises: f6abcd2f7de6
Create Date: 2026-06-29 22:41:00.876819

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "414ce9f68bb4"
down_revision: Union[str, Sequence[str], None] = "f6abcd2f7de6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cart_item",
        sa.Column("unit_price", sa.DECIMAL(10, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "order",
        sa.Column("subtotal", sa.DECIMAL(12, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "order",
        sa.Column("tax_amount", sa.DECIMAL(12, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "order_item",
        sa.Column("line_total", sa.DECIMAL(12, 2), nullable=False, server_default="0"),
    )
    # Fill existing order_item line_totals
    op.execute("UPDATE order_item SET line_total = product_price * quantity")


def downgrade() -> None:
    op.drop_column("order_item", "line_total")
    op.drop_column("order", "tax_amount")
    op.drop_column("order", "subtotal")
    op.drop_column("cart_item", "unit_price")


def downgrade() -> None:
    """Downgrade schema."""
    pass
