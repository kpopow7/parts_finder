from __future__ import annotations

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.models.category import Category
from shade_catalog.models.enums import ProductStatus
from shade_catalog.models.product import Product
from shade_catalog.models.snapshot import ProductSnapshot
from shade_catalog.schemas.catalog import SearchHit


async def search_published_products(
    session: AsyncSession,
    *,
    query: str,
    category_slug: str | None,
    limit: int,
    offset: int,
) -> tuple[list[SearchHit], int]:
    """Search published KMATs using Postgres full-text search (English)."""

    q = query.strip()
    if not q:
        return [], 0

    fts = text(
        "to_tsvector('english', concat_ws(' ', "
        "coalesce(product.name, ''), "
        "coalesce(product.subtitle, ''), "
        "coalesce(category.name, ''), "
        "coalesce(product_snapshot.search_blob, '')"
        ")) @@ plainto_tsquery('english', :search_query)"
    )

    conditions = [
        Product.status == ProductStatus.PUBLISHED,
        fts,
    ]
    if category_slug:
        conditions.append(Category.slug == category_slug)

    count_stmt = (
        select(func.count())
        .select_from(Product)
        .join(Category, Product.category_id == Category.id)
        .join(ProductSnapshot, Product.current_published_snapshot_id == ProductSnapshot.id)
        .where(*conditions)
    )
    total = int((await session.execute(count_stmt, {"search_query": q})).scalar_one())

    order = text(
        "ts_rank("
        "to_tsvector('english', concat_ws(' ', "
        "coalesce(product.name, ''), "
        "coalesce(product.subtitle, ''), "
        "coalesce(category.name, ''), "
        "coalesce(product_snapshot.search_blob, '')"
        ")), "
        "plainto_tsquery('english', :search_query)"
        ") DESC, product.name ASC"
    )

    stmt = (
        select(Product, Category)
        .join(Category, Product.category_id == Category.id)
        .join(ProductSnapshot, Product.current_published_snapshot_id == ProductSnapshot.id)
        .where(*conditions)
        .order_by(order)
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(stmt, {"search_query": q})).all()
    hits = [
        SearchHit(
            category_slug=cat.slug,
            category_name=cat.name,
            product_id=p.id,
            product_slug=p.slug,
            product_name=p.name,
            subtitle=p.subtitle,
        )
        for p, cat in rows
    ]
    return hits, total
