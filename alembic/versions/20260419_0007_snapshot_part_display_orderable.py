"""snapshot_part_display: is_orderable flag for public diagram/BOM.

Revision ID: 20260419_0007
Revises: 20260418_0006
Create Date: 2026-04-19

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision = "20260419_0007"
down_revision = "20260418_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("snapshot_part_display")}
    if "is_orderable" in cols:
        return
    op.add_column(
        "snapshot_part_display",
        sa.Column("is_orderable", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.alter_column("snapshot_part_display", "is_orderable", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("snapshot_part_display")}
    if "is_orderable" not in cols:
        return
    op.drop_column("snapshot_part_display", "is_orderable")
