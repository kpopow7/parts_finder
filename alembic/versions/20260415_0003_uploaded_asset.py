"""Add uploaded_asset for SVG/PDF file metadata.

Revision ID: 20260415_0003
Revises: 20260414_0002
Create Date: 2026-04-15

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


revision = "20260415_0003"
down_revision = "20260414_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "uploaded_asset" in insp.get_table_names():
        return
    op.create_table(
        "uploaded_asset",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_uploaded_asset_storage_key", "uploaded_asset", ["storage_key"], unique=True)
    op.create_index("ix_uploaded_asset_kind", "uploaded_asset", ["kind"])


def downgrade() -> None:
    op.drop_table("uploaded_asset")
