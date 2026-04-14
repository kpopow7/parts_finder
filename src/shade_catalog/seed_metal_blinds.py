"""
Load demo data: one Metal blinds category, one published KMAT, parts, snapshot, diagram, hotspots.

Run from project root (after migrations):  python -m shade_catalog.seed_metal_blinds
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from shade_catalog.db.session import AsyncSessionLocal
from shade_catalog.models.category import Category
from shade_catalog.models.enums import PartStatus, ProductStatus
from shade_catalog.models.part import Part
from shade_catalog.models.product import Product
from shade_catalog.models.snapshot import (
    ProductSnapshot,
    SnapshotBomLine,
    SnapshotDiagram,
    SnapshotDiagramHotspot,
    SnapshotPartDisplay,
)

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
                    locale="en",
                )
            )

        session.add(
            SnapshotDiagram(
                id=uuid.uuid4(),
                snapshot_id=snapshot.id,
                svg_storage_key="demo/metal-blinds/exploded.svg",
                raster_fallback_storage_key=None,
                diagram_title="Exploded view — standard metal blind",
                alt_summary=(
                    "Exploded diagram of a standard metal blind with callouts for major parts."
                ),
            )
        )

        rects = [
            {"type": "rect", "x": 10, "y": 20, "width": 80, "height": 40},
            {"type": "rect", "x": 110, "y": 20, "width": 70, "height": 35},
            {"type": "rect", "x": 210, "y": 15, "width": 120, "height": 25},
            {"type": "rect", "x": 360, "y": 30, "width": 90, "height": 20},
        ]
        for i, part in enumerate(parts):
            session.add(
                SnapshotDiagramHotspot(
                    id=uuid.uuid4(),
                    snapshot_id=snapshot.id,
                    part_id=part.id,
                    geometry=rects[i],
                    z_order=(i + 1) * 10,
                    label_anchor={"x": rects[i]["x"], "y": rects[i]["y"] - 8},
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
