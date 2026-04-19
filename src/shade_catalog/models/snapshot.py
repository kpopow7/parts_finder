from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shade_catalog.db.base import Base

if TYPE_CHECKING:
    from shade_catalog.models.part import Part
    from shade_catalog.models.product import Product


class ProductSnapshot(Base):
    """Immutable published view of one KMAT (diagram + BOM + labels)."""

    __tablename__ = "product_snapshot"
    __table_args__ = (
        UniqueConstraint("product_id", "version", name="uq_product_snapshot_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_user.id"), nullable=True
    )
    publish_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_blob: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped[Product] = relationship(
        "Product",
        back_populates="snapshots",
        foreign_keys=[product_id],
    )
    bom_lines: Mapped[list[SnapshotBomLine]] = relationship(back_populates="snapshot")
    part_displays: Mapped[list[SnapshotPartDisplay]] = relationship(back_populates="snapshot")
    diagram: Mapped[SnapshotDiagram | None] = relationship(
        back_populates="snapshot",
        uselist=False,
    )
    hotspots: Mapped[list[SnapshotDiagramHotspot]] = relationship(back_populates="snapshot")


class SnapshotBomLine(Base):
    __tablename__ = "snapshot_bom_line"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_snapshot.id"), nullable=False, index=True
    )
    part_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("part.id"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bom_group: Mapped[str | None] = mapped_column(String(128), nullable=True)
    show_on_diagram: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    snapshot: Mapped[ProductSnapshot] = relationship(back_populates="bom_lines")
    part: Mapped[Part] = relationship("Part")


class SnapshotPartDisplay(Base):
    __tablename__ = "snapshot_part_display"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_id",
            "part_id",
            "locale",
            name="uq_snapshot_part_display_locale",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_snapshot.id"), nullable=False, index=True
    )
    part_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("part.id"), nullable=False, index=True
    )
    public_code: Mapped[str] = mapped_column(String(255), nullable=False)
    public_description: Mapped[str] = mapped_column(Text, nullable=False)
    is_orderable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en")

    snapshot: Mapped[ProductSnapshot] = relationship(back_populates="part_displays")
    part: Mapped[Part] = relationship("Part")


class SnapshotDiagram(Base):
    __tablename__ = "snapshot_diagram"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_snapshot.id"), unique=True, nullable=False
    )
    svg_storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    raster_fallback_storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    diagram_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    alt_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    snapshot: Mapped[ProductSnapshot] = relationship(back_populates="diagram")


class SnapshotDiagramHotspot(Base):
    __tablename__ = "snapshot_diagram_hotspot"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_snapshot.id"), nullable=False, index=True
    )
    part_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("part.id"), nullable=False, index=True
    )
    geometry: Mapped[dict] = mapped_column(JSONB, nullable=False)
    z_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    label_anchor: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    snapshot: Mapped[ProductSnapshot] = relationship(back_populates="hotspots")
    part: Mapped[Part] = relationship("Part")
