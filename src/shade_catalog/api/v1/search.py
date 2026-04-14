from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.db.session import get_db
from shade_catalog.schemas.catalog import SearchResponse
from shade_catalog.services import search_public

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search_catalog(
    q: str = Query(min_length=1, max_length=500),
    category_slug: str | None = Query(default=None, max_length=128),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> SearchResponse:
    results, total = await search_public.search_published_products(
        session,
        query=q,
        category_slug=category_slug,
        limit=limit,
        offset=offset,
    )
    return SearchResponse(query=q, total=total, results=results)
