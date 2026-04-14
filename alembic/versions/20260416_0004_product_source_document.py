"""Add product_source_document links (product <-> uploaded_asset).

Revision ID: 20260416_0004
Revises: 20260415_0003
Create Date: 2026-04-16

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


revision = "20260416_0004"
down_revision = "20260415_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "product_source_document" in insp.get_table_names():
        return
    op.create_table(
        "product_source_document",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_asset_id", UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("role", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_asset_id"], ["uploaded_asset.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_source_document_product_id",
        "product_source_document",
        ["product_id"],
    )
    op.create_index(
        "ix_product_source_document_uploaded_asset_id",
        "product_source_document",
        ["uploaded_asset_id"],
    )


def downgrade() -> None:
    op.drop_table("product_source_document")
