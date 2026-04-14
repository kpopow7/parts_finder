from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shade_catalog.db.base import Base

if TYPE_CHECKING:
    from shade_catalog.models.product import Product
    from shade_catalog.models.uploaded_asset import UploadedAsset


class ProductSourceDocument(Base):
    """Links a product (KMAT) to an uploaded file (typically PDF spec)."""

    __tablename__ = "product_source_document"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uploaded_asset.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)

    product: Mapped[Product] = relationship(
        "Product",
        back_populates="source_documents",
    )
    uploaded_asset: Mapped[UploadedAsset] = relationship("UploadedAsset")
