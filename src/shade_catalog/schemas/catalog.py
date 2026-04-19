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
    is_orderable: bool = True
    part_image_asset_url_path: str | None = None
    part_image_storage_key: str | None = None
    part_image_content_type: str | None = None


class HotspotPublic(BaseModel):
    part_id: uuid.UUID
    geometry: dict = Field(default_factory=dict)
    z_order: int
    label_anchor: dict | None = None
    public_code: str
    public_description: str
    is_orderable: bool = True


class SourceDocumentPublic(BaseModel):
    id: uuid.UUID
    title: str
    role: str | None = None
    storage_key: str
    asset_url_path: str
    content_type: str
    kind: str


class ProductPublishedDetail(BaseModel):
    category: CategoryRef
    product: ProductSummary
    snapshot: PublishedSnapshotMeta
    diagram: DiagramPublic | None = None
    bill_of_materials: list[BomLinePublic]
    diagram_hotspots: list[HotspotPublic]
    source_documents: list[SourceDocumentPublic] = Field(default_factory=list)


class SearchHit(BaseModel):
    category_slug: str
    category_name: str
    product_id: uuid.UUID
    product_slug: str
    product_name: str
    subtitle: str | None = None


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchHit]
