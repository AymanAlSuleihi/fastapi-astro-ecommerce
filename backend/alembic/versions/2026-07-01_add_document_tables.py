"""add_document_tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-01 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE doc_display_id_seq START 1000")
    op.create_table(
        "document",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "display_id",
            sa.Integer(),
            server_default=sa.text("nextval('doc_display_id_seq')"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            sa.Uuid(),
            sa.ForeignKey("order.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            sa.Uuid(),
            sa.ForeignKey("customer.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("subtotal", sa.DECIMAL(12, 2), nullable=False),
        sa.Column("tax_amount", sa.DECIMAL(12, 2), nullable=False),
        sa.Column("total_amount", sa.DECIMAL(12, 2), nullable=False),
        sa.Column("billing_address", postgresql.JSONB(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("pdf_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("display_id"),
    )
    op.create_index("ix_document_order_id", "document", ["order_id"])
    op.create_index("ix_document_customer_id", "document", ["customer_id"])

    op.create_table(
        "document_item",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "document_id",
            sa.Uuid(),
            sa.ForeignKey("document.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_name", sa.String(length=256), nullable=False),
        sa.Column("product_price", sa.DECIMAL(10, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total", sa.DECIMAL(12, 2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("document_item")
    op.drop_table("document")
    op.execute("DROP SEQUENCE doc_display_id_seq")
