"""rename_admin_user_to_user

Revision ID: 4a940fb1d60d
Revises: 19ff66ea5b1f
Create Date: 2026-06-28 19:54:14.297430

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a940fb1d60d'
down_revision: Union[str, Sequence[str], None] = '19ff66ea5b1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table("admin_user", "user")


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table("user", "admin_user")
