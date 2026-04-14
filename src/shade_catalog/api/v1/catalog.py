from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.db.session import get_db
from shade_catalog.schemas.catalog import CategorySummary, ProductPublishedDetail, ProductSummary
from shade_catalog.services import catalog_public

router = APIRouter()


@router.get("/categories", response_model=list[CategorySummary])
async def list_categories(
    session: AsyncSession = Depends(get_db),
) -> list[CategorySummary]:
    return await catalog_public.list_categories(session)


@router.get("/categories/{category_slug}/products", response_model=list[ProductSummary])
async def list_products_in_category(
    category_slug: str,
    session: AsyncSession = Depends(get_db),
) -> list[ProductSummary]:
    category = await catalog_public.get_category_by_slug(session, category_slug)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    products = await catalog_public.list_published_products_in_category(
        session, category_id=category.id
    )
    return [
        ProductSummary(
            id=p.id,
            slug=p.slug,
            name=p.name,
            subtitle=p.subtitle,
        )
        for p in products
    ]


@router.get(
    "/categories/{category_slug}/products/{product_slug}",
    response_model=ProductPublishedDetail,
)
async def get_product_published(
    category_slug: str,
    product_slug: str,
    session: AsyncSession = Depends(get_db),
    locale: str = Query(default=catalog_public.DEFAULT_LOCALE, min_length=2, max_length=16),
) -> ProductPublishedDetail:
    category = await catalog_public.get_category_by_slug(session, category_slug)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    detail = await catalog_public.get_published_product_detail(
        session,
        category_id=category.id,
        product_slug=product_slug,
        locale=locale,
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return detail
