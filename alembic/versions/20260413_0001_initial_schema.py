"""Initial schema (all ORM tables).

Revision ID: 20260413_0001
Revises:
Create Date: 2026-04-13

"""

from alembic import op

from shade_catalog.db.base import Base
import shade_catalog.models  # noqa: F401

revision = "20260413_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
