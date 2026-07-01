"""add_shipping_and_variant_ids

Revision ID: f6abcd2f7de6
Revises: 23e24cc24677
Create Date: 2026-06-29 19:06:51.111471

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f6abcd2f7de6"
down_revision: Union[str, Sequence[str], None] = "23e24cc24677"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create shipping_zone table
    op.create_table(
        "shipping_zone",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("countries", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create shipping_rate table
    op.create_table(
        "shipping_rate",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "zone_id",
            sa.Uuid(),
            sa.ForeignKey("shipping_zone.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("base_cost", sa.DECIMAL(8, 2), nullable=False),
        sa.Column("free_above", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("max_weight_kg", sa.DECIMAL(8, 3), nullable=True),
        sa.Column("min_subtotal", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("min_days", sa.Integer(), nullable=True),
        sa.Column("max_days", sa.Integer(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_shipping_rate_zone_id"),
        "shipping_rate",
        ["zone_id"],
    )

    # Add product_variant columns
    op.add_column(
        "product_variant",
        sa.Column("weight_kg", sa.DECIMAL(8, 3), nullable=True),
    )
    op.add_column(
        "product_variant",
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="f"),
    )

    # Add order columns
    op.add_column(
        "order",
        sa.Column(
            "shipping_rate_id",
            sa.Uuid(),
            sa.ForeignKey("shipping_rate.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "order",
        sa.Column("shipping_cost", sa.DECIMAL(8, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "order",
        sa.Column("estimated_delivery", sa.DateTime(timezone=True), nullable=True),
    )

    # Add order_item columns
    op.add_column(
        "order_item",
        sa.Column(
            "variant_id",
            sa.Uuid(),
            sa.ForeignKey("product_variant.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column(
        "order_item",
        sa.Column("variant_sku", sa.String(length=128), nullable=True),
    )

    # Add cart_item variant_id (drop old constraint, add new)
    op.drop_constraint("cart_item_cart_product_key", "cart_item", type_="unique")
    op.add_column(
        "cart_item",
        sa.Column(
            "variant_id",
            sa.Uuid(),
            sa.ForeignKey("product_variant.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    # Fill variant_id for existing cart items from the default variant
    op.execute("""
        UPDATE cart_item
        SET variant_id = (
            SELECT pv.id FROM product_variant pv
            WHERE pv.product_id = cart_item.product_id AND pv.is_default = true
            LIMIT 1
        )
    """)
    op.alter_column("cart_item", "variant_id", nullable=False)
    op.create_unique_constraint(
        "cart_item_cart_product_variant_key",
        "cart_item",
        ["cart_id", "product_id", "variant_id"],
    )


def downgrade() -> None:
    op.drop_constraint("cart_item_cart_product_variant_key", "cart_item", type_="unique")
    op.drop_column("cart_item", "variant_id")
    op.create_unique_constraint(
        "cart_item_cart_product_key",
        "cart_item",
        ["cart_id", "product_id"],
    )
    op.drop_column("order_item", "variant_sku")
    op.drop_column("order_item", "variant_id")
    op.drop_column("order", "estimated_delivery")
    op.drop_column("order", "shipping_cost")
    op.drop_column("order", "shipping_rate_id")
    op.drop_column("product_variant", "is_default")
    op.drop_column("product_variant", "weight_kg")
    op.drop_table("shipping_rate")
    op.drop_table("shipping_zone")
