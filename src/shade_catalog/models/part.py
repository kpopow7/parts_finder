from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shade_catalog.db.base import Base
from shade_catalog.models.enums import PartStatus


class Part(Base):
    """Canonical part row (engineering identity; not shown verbatim to end users)."""

    __tablename__ = "part"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    internal_part_number: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    internal_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PartStatus] = mapped_column(
        String(32), nullable=False, default=PartStatus.ACTIVE
    )
    superseded_by_part_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("part.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    superseded_by: Mapped[Part | None] = relationship(
        "Part",
        remote_side="Part.id",
        foreign_keys=[superseded_by_part_id],
    )
