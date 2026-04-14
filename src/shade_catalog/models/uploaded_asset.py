from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shade_catalog.db.base import Base


class UploadedAssetKind(str, Enum):
    SVG = "svg"
    PDF = "pdf"


class UploadedAsset(Base):
    """Metadata for a file stored under Settings.upload_dir / storage_key."""

    __tablename__ = "uploaded_asset"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storage_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    kind: Mapped[UploadedAssetKind] = mapped_column(
        SAEnum(UploadedAssetKind, native_enum=False, length=16),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
