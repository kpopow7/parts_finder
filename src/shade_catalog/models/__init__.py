"""ORM models — import side effects register metadata with Base."""

from shade_catalog.models.audit_log import AuditLog
from shade_catalog.models.category import Category
from shade_catalog.models.part import Part
from shade_catalog.models.product import Product
from shade_catalog.models.snapshot import (
    ProductSnapshot,
    SnapshotBomLine,
    SnapshotDiagram,
    SnapshotDiagramHotspot,
    SnapshotPartDisplay,
)
from shade_catalog.models.user import User

__all__ = [
    "AuditLog",
    "Category",
    "Part",
    "Product",
    "ProductSnapshot",
    "SnapshotBomLine",
    "SnapshotDiagram",
    "SnapshotDiagramHotspot",
    "SnapshotPartDisplay",
    "User",
]
