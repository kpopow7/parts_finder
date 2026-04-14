from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shade_catalog.db.base import Base
from shade_catalog.models.category import Category
from shade_catalog.models.enums import ProductStatus

if TYPE_CHECKING:
    from shade_catalog.models.product_draft import ProductDraft
    from shade_catalog.models.product_source_document import ProductSourceDocument
    from shade_catalog.models.snapshot import ProductSnapshot


class Product(Base):
    """One KMAT (finished good) within a category."""

    __tablename__ = "product"
    __table_args__ = (UniqueConstraint("category_id", "slug", name="uq_product_category_slug"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("category.id"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[ProductStatus] = mapped_column(
        String(32), nullable=False, default=ProductStatus.DRAFT
    )
    current_published_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_snapshot.id", use_alter=True, name="fk_product_current_snapshot"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category: Mapped[Category] = relationship(back_populates="products")
    snapshots: Mapped[list[ProductSnapshot]] = relationship(
        "ProductSnapshot",
        back_populates="product",
        foreign_keys="ProductSnapshot.product_id",
        overlaps="current_published_snapshot,product",
    )
    current_published_snapshot: Mapped[ProductSnapshot | None] = relationship(
        "ProductSnapshot",
        foreign_keys=[current_published_snapshot_id],
        overlaps="snapshots,product",
    )
    draft: Mapped[ProductDraft | None] = relationship(
        "ProductDraft",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    source_documents: Mapped[list[ProductSourceDocument]] = relationship(
        "ProductSourceDocument",
        back_populates="product",
        cascade="all, delete-orphan",
    )
