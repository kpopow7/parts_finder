from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.models.audit_log import AuditLog
from shade_catalog.models.enums import ProductStatus
from shade_catalog.models.part import Part
from shade_catalog.models.product import Product
from shade_catalog.models.snapshot import (
    ProductSnapshot,
    SnapshotBomLine,
    SnapshotDiagram,
    SnapshotDiagramHotspot,
    SnapshotPartDisplay,
)
from shade_catalog.schemas.admin import PublishSnapshotRequest, PublishSnapshotResponse


class PublishValidationError(ValueError):
    pass


class ProductNotFoundError(Exception):
    pass


async def publish_snapshot(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
    body: PublishSnapshotRequest,
    actor_user_id: uuid.UUID | None = None,
) -> PublishSnapshotResponse:
    stmt = select(Product).where(Product.id == product_id).with_for_update()
    product = (await session.execute(stmt)).scalar_one_or_none()
    if product is None:
        raise ProductNotFoundError

    bom_part_ids = {row.part_id for row in body.bill_of_materials}
    if not bom_part_ids:
        raise PublishValidationError("bill_of_materials must not be empty")

    display_en = {d.part_id for d in body.part_displays if d.locale == "en"}
    if display_en != bom_part_ids:
        raise PublishValidationError(
            "part_displays for locale 'en' must include exactly one row per BOM part_id"
        )

    all_part_ids = set(bom_part_ids)
    for h in body.diagram_hotspots:
        all_part_ids.add(h.part_id)
    await _ensure_parts_exist(session, all_part_ids)

    hotspot_parts = {h.part_id for h in body.diagram_hotspots}
    if not hotspot_parts.issubset(bom_part_ids):
        raise PublishValidationError("diagram_hotspots may only reference parts present in the BOM")

    max_version = await session.scalar(
        select(func.coalesce(func.max(ProductSnapshot.version), 0)).where(
            ProductSnapshot.product_id == product_id
        )
    )
    next_version = int(max_version or 0) + 1
    now = datetime.now(timezone.utc)
    prev_snapshot_id = product.current_published_snapshot_id

    snapshot = ProductSnapshot(
        id=uuid.uuid4(),
        product_id=product_id,
        version=next_version,
        published_at=now,
        published_by_user_id=actor_user_id,
        publish_notes=body.publish_notes,
        search_blob=body.search_blob,
    )
    session.add(snapshot)
    await session.flush()

    for row in sorted(body.bill_of_materials, key=lambda r: (r.sort_order, str(r.part_id))):
        session.add(
            SnapshotBomLine(
                id=uuid.uuid4(),
                snapshot_id=snapshot.id,
                part_id=row.part_id,
                quantity=row.quantity,
                sort_order=row.sort_order,
                bom_group=row.bom_group,
                show_on_diagram=row.show_on_diagram,
            )
        )

    for d in body.part_displays:
        session.add(
            SnapshotPartDisplay(
                id=uuid.uuid4(),
                snapshot_id=snapshot.id,
                part_id=d.part_id,
                public_code=d.public_code,
                public_description=d.public_description,
                locale=d.locale,
            )
        )

    if body.diagram is not None:
        session.add(
            SnapshotDiagram(
                id=uuid.uuid4(),
                snapshot_id=snapshot.id,
                svg_storage_key=body.diagram.svg_storage_key,
                raster_fallback_storage_key=body.diagram.raster_fallback_storage_key,
                diagram_title=body.diagram.diagram_title,
                alt_summary=body.diagram.alt_summary,
            )
        )

    for h in sorted(body.diagram_hotspots, key=lambda x: (x.z_order, str(x.part_id))):
        session.add(
            SnapshotDiagramHotspot(
                id=uuid.uuid4(),
                snapshot_id=snapshot.id,
                part_id=h.part_id,
                geometry=h.geometry,
                z_order=h.z_order,
                label_anchor=h.label_anchor,
            )
        )

    product.current_published_snapshot_id = snapshot.id
    product.status = ProductStatus.PUBLISHED

    session.add(
        AuditLog(
            id=uuid.uuid4(),
            actor_user_id=actor_user_id,
            action="product_snapshot.published",
            entity_type="product_snapshot",
            entity_id=snapshot.id,
            metadata_={
                "product_id": str(product_id),
                "version": next_version,
                "previous_snapshot_id": str(prev_snapshot_id) if prev_snapshot_id else None,
            },
        )
    )

    return PublishSnapshotResponse(
        snapshot_id=snapshot.id,
        product_id=product_id,
        version=next_version,
        published_at=now,
    )


async def _ensure_parts_exist(session: AsyncSession, part_ids: set[uuid.UUID]) -> None:
    if not part_ids:
        return
    rows = (await session.scalars(select(Part.id).where(Part.id.in_(part_ids)))).all()
    found = set(rows)
    if found != part_ids:
        missing = part_ids - found
        raise PublishValidationError(f"Unknown part_id values: {sorted(missing)}")
