"""product_spec_import: persist PDF spec parses (review → draft).

Revision ID: 20260418_0006
Revises: 20260417_0005
Create Date: 2026-04-18

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision = "20260418_0006"
down_revision = "20260417_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "product_spec_import" in insp.get_table_names():
        return
    op.create_table(
        "product_spec_import",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_asset_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("parse_payload", JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_asset_id"], ["uploaded_asset.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_spec_import_product_id", "product_spec_import", ["product_id"])
    op.create_index(
        "ix_product_spec_import_uploaded_asset_id",
        "product_spec_import",
        ["uploaded_asset_id"],
    )
    op.create_index("ix_product_spec_import_status", "product_spec_import", ["status"])


def downgrade() -> None:
    op.drop_table("product_spec_import")
