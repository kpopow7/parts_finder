"""Part optional JPEG/PNG image (uploaded_asset FK).

Revision ID: 20260417_0005
Revises: 20260416_0004
Create Date: 2026-04-17

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "20260417_0005"
down_revision = "20260416_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "part",
        sa.Column(
            "image_uploaded_asset_id",
            UUID(as_uuid=True),
            sa.ForeignKey("uploaded_asset.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_part_image_uploaded_asset_id",
        "part",
        ["image_uploaded_asset_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_part_image_uploaded_asset_id", table_name="part")
    op.drop_column("part", "image_uploaded_asset_id")
