"""add_variants_and_templates

Revision ID: 23e24cc24677
Revises: 4a940fb1d60d
Create Date: 2026-06-28 20:34:58.216934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23e24cc24677'
down_revision: Union[str, Sequence[str], None] = '4a940fb1d60d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create attribute_template table
    op.create_table(
        "attribute_template",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("attributes", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create product_variant table
    op.create_table(
        "product_variant",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "product_id",
            sa.Uuid(),
            sa.ForeignKey("product.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("price_override", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("stock_quantity", sa.Integer(), nullable=False),
        sa.Column("attributes", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )
    op.create_index(
        op.f("ix_product_variant_product_id"),
        "product_variant",
        ["product_id"],
    )

    # Modify product table
    op.drop_column("product", "stock_quantity")
    op.add_column(
        "product",
        sa.Column("attribute_template_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "product",
        sa.Column(
            "variant_attributes_override",
            sa.dialects.postgresql.JSONB(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        None,
        "product",
        "attribute_template",
        ["attribute_template_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(None, "product", type_="foreignkey")
    op.drop_column("product", "variant_attributes_override")
    op.drop_column("product", "attribute_template_id")
    op.add_column(
        "product",
        sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"),
    )
    op.drop_table("product_variant")
    op.drop_table("attribute_template")
