from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shade_catalog.db.base import Base
from shade_catalog.models.enums import SpecImportStatus, str_enum_values_callable

if TYPE_CHECKING:
    from shade_catalog.models.product import Product
    from shade_catalog.models.uploaded_asset import UploadedAsset


class ProductSpecImport(Base):
    """Persisted PDF spec parse for a product (review → apply to draft)."""

    __tablename__ = "product_spec_import"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uploaded_asset.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[SpecImportStatus] = mapped_column(
        SQLEnum(
            SpecImportStatus,
            native_enum=False,
            length=32,
            values_callable=str_enum_values_callable,
        ),
        nullable=False,
        default=SpecImportStatus.PENDING,
        index=True,
    )
    parse_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="spec_imports")
    uploaded_asset: Mapped["UploadedAsset"] = relationship("UploadedAsset")

