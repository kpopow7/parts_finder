from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shade_catalog.models.audit_log import AuditLog
from shade_catalog.models.product import Product
from shade_catalog.models.product_draft import ProductDraft
from shade_catalog.models.snapshot import ProductSnapshot
from shade_catalog.schemas.admin import ProductDraftDocument, ProductDraftPayload
from shade_catalog.services.publish import ProductNotFoundError


class ProductHasNoPublishedSnapshotError(ValueError):
    pass


async def get_product_draft(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
) -> ProductDraftDocument:
    stmt = (
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.current_published_snapshot).selectinload(
                ProductSnapshot.bom_lines
            ),
            selectinload(Product.current_published_snapshot).selectinload(
                ProductSnapshot.part_displays
            ),
            selectinload(Product.current_published_snapshot).selectinload(
                ProductSnapshot.diagram
            ),
            selectinload(Product.current_published_snapshot).selectinload(
                ProductSnapshot.hotspots
            ),
        )
    )
    product = (await session.scalars(stmt)).first()
    if product is None:
        raise ProductNotFoundError

    row = await session.get(ProductDraft, product_id)
    if row is None:
        seeded_payload = _seed_payload_from_current_snapshot(product)
        return ProductDraftDocument(
            product_id=product_id,
            payload=seeded_payload,
            updated_at=(
                product.current_published_snapshot.published_at
                if product.current_published_snapshot is not None
                else None
            ),
            updated_by_user_id=None,
        )

    payload = ProductDraftPayload.model_validate(row.payload)
    return ProductDraftDocument(
        product_id=product_id,
        payload=payload,
        updated_at=row.updated_at,
        updated_by_user_id=row.updated_by_user_id,
    )


async def upsert_product_draft(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
    payload: ProductDraftPayload,
    actor_user_id: uuid.UUID | None = None,
) -> ProductDraftDocument:
    product = await session.get(Product, product_id)
    if product is None:
        raise ProductNotFoundError

    data = payload.model_dump(mode="json")
    now = datetime.now(timezone.utc)

    row = await session.get(ProductDraft, product_id)
    if row is None:
        row = ProductDraft(
            product_id=product_id,
            payload=data,
            updated_at=now,
            updated_by_user_id=actor_user_id,
        )
        session.add(row)
    else:
        row.payload = data
        row.updated_by_user_id = actor_user_id
        row.updated_at = now

    session.add(
        AuditLog(
            id=uuid.uuid4(),
            actor_user_id=actor_user_id,
            action="product_draft.upserted",
            entity_type="product",
            entity_id=product_id,
            metadata_={"has_diagram": payload.diagram is not None},
        )
    )
    await session.flush()
    await session.refresh(row)
    return ProductDraftDocument(
        product_id=product_id,
        payload=ProductDraftPayload.model_validate(row.payload),
        updated_at=row.updated_at,
        updated_by_user_id=row.updated_by_user_id,
    )


async def reset_product_draft_from_published_snapshot(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
    actor_user_id: uuid.UUID | None = None,
) -> ProductDraftDocument:
    """Overwrite draft with current published snapshot data for easier iteration."""
    stmt = (
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.current_published_snapshot).selectinload(
                ProductSnapshot.bom_lines
            ),
            selectinload(Product.current_published_snapshot).selectinload(
                ProductSnapshot.part_displays
            ),
            selectinload(Product.current_published_snapshot).selectinload(
                ProductSnapshot.diagram
            ),
            selectinload(Product.current_published_snapshot).selectinload(
                ProductSnapshot.hotspots
            ),
        )
    )
    product = (await session.scalars(stmt)).first()
    if product is None:
        raise ProductNotFoundError

    if product.current_published_snapshot is None:
        raise ProductHasNoPublishedSnapshotError(
            "Product has no published snapshot to reset from"
        )

    payload = _seed_payload_from_current_snapshot(product)
    return await upsert_product_draft(
        session,
        product_id=product_id,
        payload=payload,
        actor_user_id=actor_user_id,
    )


def _seed_payload_from_current_snapshot(product: Product) -> ProductDraftPayload:
    """Build an editable draft payload from the currently published snapshot, if any."""
    snap = product.current_published_snapshot
    if snap is None:
        return ProductDraftPayload()

    diagram = None
    if snap.diagram is not None:
        diagram = {
            "svg_storage_key": snap.diagram.svg_storage_key,
            "raster_fallback_storage_key": snap.diagram.raster_fallback_storage_key,
            "diagram_title": snap.diagram.diagram_title,
            "alt_summary": snap.diagram.alt_summary,
        }

    bom = [
        {
            "part_id": row.part_id,
            "quantity": float(row.quantity),
            "sort_order": row.sort_order,
            "bom_group": row.bom_group,
            "show_on_diagram": row.show_on_diagram,
        }
        for row in sorted(snap.bom_lines, key=lambda r: (r.sort_order, str(r.id)))
    ]
    displays = [
        {
            "part_id": d.part_id,
            "public_code": d.public_code,
            "public_description": d.public_description,
            "is_orderable": d.is_orderable,
            "locale": d.locale,
        }
        for d in sorted(snap.part_displays, key=lambda x: (x.locale, str(x.part_id)))
    ]
    hotspots = [
        {
            "part_id": h.part_id,
            "geometry": dict(h.geometry),
            "z_order": h.z_order,
            "label_anchor": dict(h.label_anchor) if h.label_anchor else None,
        }
        for h in sorted(snap.hotspots, key=lambda x: (x.z_order, str(x.id)))
    ]
    return ProductDraftPayload.model_validate(
        {
            "publish_notes": snap.publish_notes,
            "search_blob": snap.search_blob,
            "diagram": diagram,
            "bill_of_materials": bom,
            "part_displays": displays,
            "diagram_hotspots": hotspots,
        }
    )
