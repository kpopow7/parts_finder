from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.api.deps import require_admin
from shade_catalog.db.session import get_db
from shade_catalog.schemas.admin import (
    CreatePartRequest,
    CreatePartResponse,
    CreateProductRequest,
    CreateProductResponse,
    PublishSnapshotRequest,
    PublishSnapshotResponse,
)
from shade_catalog.services import admin_products
from shade_catalog.services.publish import (
    ProductNotFoundError,
    PublishValidationError,
    publish_snapshot,
)

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@admin_router.post("/parts", response_model=CreatePartResponse, status_code=201)
async def admin_create_part(
    body: CreatePartRequest,
    session: AsyncSession = Depends(get_db),
) -> CreatePartResponse:
    try:
        async with session.begin():
            part = await admin_products.create_part(session, body)
    except IntegrityError as e:
        raise HTTPException(
            status_code=409,
            detail="Part number already exists or constraint violated",
        ) from e
    return CreatePartResponse(id=part.id, internal_part_number=part.internal_part_number)


@admin_router.post("/products", response_model=CreateProductResponse, status_code=201)
async def admin_create_product(
    body: CreateProductRequest,
    session: AsyncSession = Depends(get_db),
) -> CreateProductResponse:
    try:
        async with session.begin():
            product = await admin_products.create_product(session, body)
    except admin_products.AdminValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except IntegrityError as e:
        raise HTTPException(
            status_code=409,
            detail="Product slug already exists in this category or constraint violated",
        ) from e
    return CreateProductResponse(
        id=product.id,
        category_id=product.category_id,
        slug=product.slug,
        name=product.name,
        status=str(product.status.value),
    )


@admin_router.post(
    "/products/{product_id}/publish",
    response_model=PublishSnapshotResponse,
    status_code=201,
)
async def admin_publish_product(
    product_id: uuid.UUID,
    body: PublishSnapshotRequest,
    session: AsyncSession = Depends(get_db),
) -> PublishSnapshotResponse:
    try:
        async with session.begin():
            return await publish_snapshot(session, product_id=product_id, body=body)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=404, detail="Product not found") from e
    except PublishValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
