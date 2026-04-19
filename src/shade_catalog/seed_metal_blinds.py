"""
Load demo data: one Metal blinds category, one published KMAT, parts, snapshot, diagram, hotspots.

Run from project root (after migrations):  python -m shade_catalog.seed_metal_blinds
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from shade_catalog.core.config import get_settings
from shade_catalog.db.session import AsyncSessionLocal
from shade_catalog.models.category import Category
from shade_catalog.models.enums import PartStatus, ProductStatus
from shade_catalog.models.part import Part
from shade_catalog.models.product import Product
from shade_catalog.models.uploaded_asset import UploadedAsset, UploadedAssetKind
from shade_catalog.models.snapshot import (
    ProductSnapshot,
    SnapshotBomLine,
    SnapshotDiagram,
    SnapshotDiagramHotspot,
    SnapshotPartDisplay,
)
from shade_catalog.services.local_storage import build_storage_key, write_bytes

CATEGORY_SLUG = "metal-blinds"
PRODUCT_SLUG = "standard-metal-blind"


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.scalar(select(Category.id).where(Category.slug == CATEGORY_SLUG))
        if existing is not None:
            print("Demo data already present (category 'metal-blinds' exists). Skipping.")
            return

        now = datetime.now(timezone.utc)

        category = Category(
            id=uuid.uuid4(),
            slug=CATEGORY_SLUG,
            name="Metal blinds",
            sort_order=10,
        )
        session.add(category)
        await session.flush()

        parts_spec: list[tuple[str, str]] = [
            ("ENG-MB-CORD-001", "Cord lock assembly"),
            ("ENG-MB-BRACKET-002", "Mounting bracket"),
            ("ENG-MB-HEADRAIL-003", "Headrail"),
            ("ENG-MB-SLAT-004", "Slat segment"),
        ]
        parts: list[Part] = []
        for internal_no, internal_desc in parts_spec:
            p = Part(
                id=uuid.uuid4(),
                internal_part_number=internal_no,
                internal_description=internal_desc,
                status=PartStatus.ACTIVE,
            )
            session.add(p)
            parts.append(p)
        await session.flush()

        product = Product(
            id=uuid.uuid4(),
            category_id=category.id,
            slug=PRODUCT_SLUG,
            name="Standard metal blind",
            subtitle="Demo KMAT for catalog and diagram work",
            status=ProductStatus.DRAFT,
            current_published_snapshot_id=None,
        )
        session.add(product)
        await session.flush()

        snapshot = ProductSnapshot(
            id=uuid.uuid4(),
            product_id=product.id,
            version=1,
            published_at=now,
            published_by_user_id=None,
            publish_notes="Initial demo publish",
            search_blob="metal blind standard slat headrail bracket cord",
        )
        session.add(snapshot)
        await session.flush()

        friendly = [
            ("A", "Cord lock", "Hardware"),
            ("B", "Mounting bracket", "Hardware"),
            ("C", "Headrail", "Blind"),
            ("D", "Slat", "Blind"),
        ]
        settings = get_settings()
        svg_key, svg_name = build_storage_key(UploadedAssetKind.SVG)
        demo_svg = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img" aria-label="Exploded diagram">
  <title>Exploded view</title>
  <rect width="100" height="100" fill="#f4f4f5"/>
  <rect x="2" y="28" width="20" height="38" rx="1" fill="#c7d2fe" stroke="#3730a3" stroke-width="0.4"/>
  <rect x="26" y="28" width="18" height="32" rx="1" fill="#a5b4fc" stroke="#3730a3" stroke-width="0.4"/>
  <rect x="48" y="24" width="24" height="30" rx="1" fill="#93c5fd" stroke="#1d4ed8" stroke-width="0.4"/>
  <rect x="74" y="30" width="22" height="26" rx="1" fill="#bfdbfe" stroke="#1d4ed8" stroke-width="0.4"/>
</svg>"""
        write_bytes(settings.upload_dir, svg_key, demo_svg)
        session.add(
            UploadedAsset(
                id=uuid.uuid4(),
                storage_key=svg_key,
                kind=UploadedAssetKind.SVG,
                original_filename=svg_name,
                content_type="image/svg+xml",
                byte_size=len(demo_svg),
            )
        )

        for i, part in enumerate(parts):
            code, desc, group = friendly[i]
            session.add(
                SnapshotBomLine(
                    id=uuid.uuid4(),
                    snapshot_id=snapshot.id,
                    part_id=part.id,
                    quantity=1.0,
                    sort_order=i * 10,
                    bom_group=group,
                    show_on_diagram=True,
                )
            )
            session.add(
                SnapshotPartDisplay(
                    id=uuid.uuid4(),
                    snapshot_id=snapshot.id,
                    part_id=part.id,
                    public_code=code,
                    public_description=desc,
                    is_orderable=(i != 3),
                    locale="en",
                )
            )

        session.add(
            SnapshotDiagram(
                id=uuid.uuid4(),
                snapshot_id=snapshot.id,
                svg_storage_key=svg_key,
                raster_fallback_storage_key=None,
                diagram_title="Exploded view — standard metal blind",
                alt_summary=(
                    "Exploded diagram of a standard metal blind with callouts for major parts."
                ),
            )
        )

        # Geometry is relative to the diagram image box: x/y/width/height as percentages 0–100.
        rects = [
            {"type": "rect", "x": 2, "y": 28, "width": 20, "height": 38},
            {"type": "rect", "x": 26, "y": 28, "width": 18, "height": 32},
            {"type": "rect", "x": 48, "y": 24, "width": 24, "height": 30},
            {"type": "rect", "x": 74, "y": 30, "width": 22, "height": 26},
        ]
        for i, part in enumerate(parts):
            session.add(
                SnapshotDiagramHotspot(
                    id=uuid.uuid4(),
                    snapshot_id=snapshot.id,
                    part_id=part.id,
                    geometry=rects[i],
                    z_order=(i + 1) * 10,
                    label_anchor={"x": rects[i]["x"], "y": max(0, rects[i]["y"] - 6)},
                )
            )

        product.status = ProductStatus.PUBLISHED
        product.current_published_snapshot_id = snapshot.id

        await session.commit()
        print("Seeded demo category, product, snapshot, BOM, diagram, and hotspots.")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
