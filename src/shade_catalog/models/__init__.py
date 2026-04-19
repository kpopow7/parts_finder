"""ORM models — import side effects register metadata with Base."""

from shade_catalog.models.audit_log import AuditLog
from shade_catalog.models.category import Category
from shade_catalog.models.part import Part
from shade_catalog.models.product import Product
from shade_catalog.models.product_draft import ProductDraft
from shade_catalog.models.product_source_document import ProductSourceDocument
from shade_catalog.models.product_spec_import import ProductSpecImport
from shade_catalog.models.snapshot import (
    ProductSnapshot,
    SnapshotBomLine,
    SnapshotDiagram,
    SnapshotDiagramHotspot,
    SnapshotPartDisplay,
)
from shade_catalog.models.uploaded_asset import UploadedAsset, UploadedAssetKind
from shade_catalog.models.user import User

__all__ = [
    "AuditLog",
    "Category",
    "Part",
    "Product",
    "ProductDraft",
    "ProductSourceDocument",
    "ProductSpecImport",
    "ProductSnapshot",
    "SnapshotBomLine",
    "SnapshotDiagram",
    "SnapshotDiagramHotspot",
    "SnapshotPartDisplay",
    "UploadedAsset",
    "UploadedAssetKind",
    "User",
]
