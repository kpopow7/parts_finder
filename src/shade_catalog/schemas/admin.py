from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreatePartRequest(BaseModel):
    internal_part_number: str = Field(min_length=1, max_length=128)
    internal_description: str | None = None
    image_uploaded_asset_id: uuid.UUID | None = None


class CreatePartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    internal_part_number: str
    image_uploaded_asset_id: uuid.UUID | None = None


class PartListItem(BaseModel):
    """Row from GET /admin/parts (canonical parts catalog)."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    internal_part_number: str
    internal_description: str | None = None
    status: str
    image_uploaded_asset_id: uuid.UUID | None = None


class UpdatePartRequest(BaseModel):
    """Set or clear the optional part photo (JPEG/PNG upload id from POST /admin/uploads)."""

    image_uploaded_asset_id: uuid.UUID | None


class CreateCategoryRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    sort_order: int = Field(default=0)


class CreateCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    sort_order: int


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


class ProductListItem(BaseModel):
    """Row from GET /admin/products (draft and published KMATs)."""

    id: uuid.UUID
    category_id: uuid.UUID
    category_slug: str
    slug: str
    name: str
    subtitle: str | None = None
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


class DiagramDraftRequest(BaseModel):
    """Diagram fields may be incomplete while editing."""

    svg_storage_key: str | None = Field(default=None, max_length=1024)
    raster_fallback_storage_key: str | None = Field(default=None, max_length=1024)
    diagram_title: str | None = Field(default=None, max_length=512)
    alt_summary: str | None = None


class BomLineDraftRequest(BaseModel):
    part_id: uuid.UUID
    quantity: float = Field(default=1, ge=0)
    sort_order: int = 0
    bom_group: str | None = Field(default=None, max_length=128)
    show_on_diagram: bool = True


class PartDisplayDraftRequest(BaseModel):
    part_id: uuid.UUID
    public_code: str = ""
    public_description: str = ""
    locale: str = Field(default="en", min_length=2, max_length=16)


class HotspotDraftRequest(BaseModel):
    part_id: uuid.UUID
    geometry: dict = Field(default_factory=dict)
    z_order: int = 0
    label_anchor: dict | None = None


class ProductDraftPayload(BaseModel):
    """Persisted editor state (partial / work-in-progress)."""

    publish_notes: str | None = None
    search_blob: str | None = None
    diagram: DiagramDraftRequest | None = None
    bill_of_materials: list[BomLineDraftRequest] = Field(default_factory=list)
    part_displays: list[PartDisplayDraftRequest] = Field(default_factory=list)
    diagram_hotspots: list[HotspotDraftRequest] = Field(default_factory=list)


class ProductDraftDocument(BaseModel):
    product_id: uuid.UUID
    payload: ProductDraftPayload
    updated_at: datetime | None = None
    updated_by_user_id: uuid.UUID | None = None


class UploadAssetResponse(BaseModel):
    id: uuid.UUID
    storage_key: str
    kind: str
    original_filename: str
    content_type: str
    byte_size: int


class SourceDocumentCreateRequest(BaseModel):
    uploaded_asset_id: uuid.UUID
    title: str | None = Field(default=None, max_length=512)
    sort_order: int = 0
    role: str | None = Field(default=None, max_length=64)


class ProductSourceDocumentResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    uploaded_asset_id: uuid.UUID
    title: str | None
    sort_order: int
    role: str | None


class ParsedSpecTocEntry(BaseModel):
    title: str
    page_ref: str


class ParsedSizeStandardResponse(BaseModel):
    variant: str
    min_width: str | None = None
    max_width: str | None = None
    min_height: str | None = None
    max_height: str | None = None
    max_area_sqft: str | None = None


class ParsedColorPairResponse(BaseModel):
    slat_color: str
    default_bottom_rail_color: str


class ParsedPriceChartColorMapResponse(BaseModel):
    color: str
    price_charts: list[str]


class ParseSpecResponse(BaseModel):
    source_asset_id: uuid.UUID
    original_filename: str
    document_title: str | None
    product_line: str | None
    table_of_contents: list[ParsedSpecTocEntry]
    operating_systems: list[str]
    size_standards: list[ParsedSizeStandardResponse]
    bottom_rail_color_pairs: list[ParsedColorPairResponse]
    price_chart_color_map: list[ParsedPriceChartColorMapResponse]
    warnings: list[str]
