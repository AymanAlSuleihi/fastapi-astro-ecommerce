"""add_guest_customers

Revision ID: 91990442a702
Revises: 414ce9f68bb4
Create Date: 2026-06-30 00:03:32.715709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91990442a702'
down_revision: Union[str, Sequence[str], None] = '414ce9f68bb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("customer", "hashed_password", nullable=True)
    op.add_column(
        "customer",
        sa.Column("is_guest", sa.Boolean(), nullable=False, server_default="f"),
    )


def downgrade() -> None:
    op.drop_column("customer", "is_guest")
    op.alter_column("customer", "hashed_password", nullable=False)
