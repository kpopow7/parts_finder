from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    sort_order: int
    published_product_count: int = 0


class ProductSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    subtitle: str | None = None


class CategoryRef(BaseModel):
    slug: str
    name: str


class PublishedSnapshotMeta(BaseModel):
    version: int
    published_at: datetime


class DiagramPublic(BaseModel):
    svg_storage_key: str
    raster_fallback_storage_key: str | None = None
    diagram_title: str | None = None
    alt_summary: str | None = None


class BomLinePublic(BaseModel):
    part_id: uuid.UUID
    quantity: float
    sort_order: int
    bom_group: str | None = None
    show_on_diagram: bool
    public_code: str
    public_description: str


class HotspotPublic(BaseModel):
    part_id: uuid.UUID
    geometry: dict = Field(default_factory=dict)
    z_order: int
    label_anchor: dict | None = None
    public_code: str
    public_description: str


class ProductPublishedDetail(BaseModel):
    category: CategoryRef
    product: ProductSummary
    snapshot: PublishedSnapshotMeta
    diagram: DiagramPublic | None = None
    bill_of_materials: list[BomLinePublic]
    diagram_hotspots: list[HotspotPublic]
