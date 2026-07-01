"""add_order_display_id

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-01 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE order_display_id_seq START 1000")
    op.add_column(
        "order",
        sa.Column(
            "display_id",
            sa.Integer(),
            server_default=sa.text("nextval('order_display_id_seq')"),
            nullable=False,
        ),
    )
    op.create_unique_constraint("uq_order_display_id", "order", ["display_id"])
    op.create_index("ix_order_display_id", "order", ["display_id"])


def downgrade() -> None:
    op.drop_index("ix_order_display_id", table_name="order")
    op.drop_constraint("uq_order_display_id", "order", type_="unique")
    op.drop_column("order", "display_id")
    op.execute("DROP SEQUENCE order_display_id_seq")
