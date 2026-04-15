from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shade_catalog.db.base import Base
from shade_catalog.models.enums import PartStatus, str_enum_values_callable

if TYPE_CHECKING:
    from shade_catalog.models.uploaded_asset import UploadedAsset


class Part(Base):
    """Canonical part row (engineering identity; not shown verbatim to end users)."""

    __tablename__ = "part"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    internal_part_number: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    internal_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PartStatus] = mapped_column(
        SQLEnum(
            PartStatus,
            native_enum=False,
            length=32,
            values_callable=str_enum_values_callable,
        ),
        nullable=False,
        default=PartStatus.ACTIVE,
    )
    superseded_by_part_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("part.id"), nullable=True
    )
    image_uploaded_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uploaded_asset.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
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
    image_asset: Mapped["UploadedAsset | None"] = relationship(
        "UploadedAsset",
        foreign_keys=[image_uploaded_asset_id],
    )
