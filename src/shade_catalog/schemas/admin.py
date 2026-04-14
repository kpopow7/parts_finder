from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreatePartRequest(BaseModel):
    internal_part_number: str = Field(min_length=1, max_length=128)
    internal_description: str | None = None


class CreatePartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    internal_part_number: str


class CreateProductRequest(BaseModel):
    category_slug: str = Field(min_length=1, max_length=128)
    slug: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    subtitle: str | None = Field(default=None, max_length=512)


class CreateProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    slug: str
    name: str
    status: str


class DiagramPublishRequest(BaseModel):
    svg_storage_key: str = Field(min_length=1, max_length=1024)
    raster_fallback_storage_key: str | None = Field(default=None, max_length=1024)
    diagram_title: str | None = Field(default=None, max_length=512)
    alt_summary: str | None = None


class BomLinePublishRequest(BaseModel):
    part_id: uuid.UUID
    quantity: float = Field(gt=0)
    sort_order: int = 0
    bom_group: str | None = Field(default=None, max_length=128)
    show_on_diagram: bool = True


class PartDisplayPublishRequest(BaseModel):
    part_id: uuid.UUID
    public_code: str = Field(min_length=1, max_length=255)
    public_description: str = Field(min_length=1)
    locale: str = Field(default="en", min_length=2, max_length=16)


class HotspotPublishRequest(BaseModel):
    part_id: uuid.UUID
    geometry: dict = Field(default_factory=dict)
    z_order: int = 0
    label_anchor: dict | None = None


class PublishSnapshotRequest(BaseModel):
    """Publish a new immutable snapshot (version increments)."""

    publish_notes: str | None = None
    search_blob: str | None = None
    diagram: DiagramPublishRequest | None = None
    bill_of_materials: list[BomLinePublishRequest]
    part_displays: list[PartDisplayPublishRequest]
    diagram_hotspots: list[HotspotPublishRequest] = Field(default_factory=list)


class PublishSnapshotResponse(BaseModel):
    snapshot_id: uuid.UUID
    product_id: uuid.UUID
    version: int
    published_at: datetime
