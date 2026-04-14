from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shade_catalog.models.category import Category
from shade_catalog.models.enums import ProductStatus
from shade_catalog.models.product import Product
from shade_catalog.models.snapshot import ProductSnapshot, SnapshotPartDisplay
from shade_catalog.schemas.catalog import (
    BomLinePublic,
    CategoryRef,
    CategorySummary,
    DiagramPublic,
    HotspotPublic,
    ProductPublishedDetail,
    ProductSummary,
    PublishedSnapshotMeta,
    SourceDocumentPublic,
)

DEFAULT_LOCALE = "en"


async def list_categories(session: AsyncSession) -> list[CategorySummary]:
    stmt = select(Category).order_by(Category.sort_order, Category.name)
    categories = (await session.scalars(stmt)).all()
    out: list[CategorySummary] = []
    for c in categories:
        cnt = await session.scalar(
            select(func.count())
            .select_from(Product)
            .where(
                Product.category_id == c.id,
                Product.status == ProductStatus.PUBLISHED,
                Product.current_published_snapshot_id.isnot(None),
            )
        )
        out.append(
            CategorySummary(
                id=c.id,
                slug=c.slug,
                name=c.name,
                sort_order=c.sort_order,
                published_product_count=int(cnt or 0),
            )
        )
    return out


async def get_category_by_slug(session: AsyncSession, slug: str) -> Category | None:
    stmt = select(Category).where(Category.slug == slug)
    return (await session.scalars(stmt)).first()


async def list_published_products_in_category(
    session: AsyncSession,
    *,
    category_id: uuid.UUID,
) -> list[Product]:
    stmt = (
        select(Product)
        .where(
            Product.category_id == category_id,
            Product.status == ProductStatus.PUBLISHED,
            Product.current_published_snapshot_id.isnot(None),
        )
        .order_by(Product.name)
    )
    return list((await session.scalars(stmt)).all())


async def get_published_product_detail(
    session: AsyncSession,
    *,
    category_id: uuid.UUID,
    product_slug: str,
    locale: str = DEFAULT_LOCALE,
) -> ProductPublishedDetail | None:
    stmt = (
        select(Product)
        .where(
            Product.category_id == category_id,
            Product.slug == product_slug,
            Product.status == ProductStatus.PUBLISHED,
            Product.current_published_snapshot_id.isnot(None),
        )
        .options(
            selectinload(Product.category),
            selectinload(Product.current_published_snapshot)
            .selectinload(ProductSnapshot.bom_lines),
            selectinload(Product.current_published_snapshot).selectinload(
                ProductSnapshot.part_displays
            ),
            selectinload(Product.current_published_snapshot).selectinload(ProductSnapshot.diagram),
            selectinload(Product.current_published_snapshot).selectinload(ProductSnapshot.hotspots),
            selectinload(Product.source_documents).selectinload("uploaded_asset"),
        )
    )
    product = (await session.scalars(stmt)).first()
    if product is None:
        return None

    snap = product.current_published_snapshot
    if snap is None:
        return None

    display_by_part: dict[uuid.UUID, SnapshotPartDisplay] = {}
    for d in snap.part_displays:
        if d.locale == locale:
            display_by_part[d.part_id] = d

    def display_for(part_id: uuid.UUID) -> tuple[str, str]:
        d = display_by_part.get(part_id)
        if d is None:
            return ("", "")
        return (d.public_code, d.public_description)

    bom_lines = sorted(snap.bom_lines, key=lambda r: (r.sort_order, str(r.id)))
    bom_public: list[BomLinePublic] = []
    for row in bom_lines:
        code, desc = display_for(row.part_id)
        bom_public.append(
            BomLinePublic(
                part_id=row.part_id,
                quantity=float(row.quantity),
                sort_order=row.sort_order,
                bom_group=row.bom_group,
                show_on_diagram=row.show_on_diagram,
                public_code=code,
                public_description=desc,
            )
        )

    hotspots = sorted(snap.hotspots, key=lambda h: (h.z_order, str(h.id)))
    hotspot_public: list[HotspotPublic] = []
    for h in hotspots:
        code, desc = display_for(h.part_id)
        hotspot_public.append(
            HotspotPublic(
                part_id=h.part_id,
                geometry=dict(h.geometry),
                z_order=h.z_order,
                label_anchor=dict(h.label_anchor) if h.label_anchor else None,
                public_code=code,
                public_description=desc,
            )
        )

    diagram_public: DiagramPublic | None = None
    if snap.diagram is not None:
        d = snap.diagram
        diagram_public = DiagramPublic(
            svg_storage_key=d.svg_storage_key,
            raster_fallback_storage_key=d.raster_fallback_storage_key,
            diagram_title=d.diagram_title,
            alt_summary=d.alt_summary,
        )

    doc_public: list[SourceDocumentPublic] = []
    for d in sorted(
        product.source_documents or [],
        key=lambda row: (row.sort_order, str(row.id)),
    ):
        asset = d.uploaded_asset
        if asset is None:
            continue
        title = d.title if d.title else asset.original_filename
        doc_public.append(
            SourceDocumentPublic(
                id=d.id,
                title=title,
                role=d.role,
                storage_key=asset.storage_key,
                asset_url_path=f"/api/v1/assets/{asset.storage_key}",
                content_type=asset.content_type,
                kind=asset.kind.value,
            )
        )

    assert product.category is not None
    return ProductPublishedDetail(
        category=CategoryRef(slug=product.category.slug, name=product.category.name),
        product=ProductSummary(
            id=product.id,
            slug=product.slug,
            name=product.name,
            subtitle=product.subtitle,
        ),
        snapshot=PublishedSnapshotMeta(version=snap.version, published_at=snap.published_at),
        diagram=diagram_public,
        bill_of_materials=bom_public,
        diagram_hotspots=hotspot_public,
        source_documents=doc_public,
    )
