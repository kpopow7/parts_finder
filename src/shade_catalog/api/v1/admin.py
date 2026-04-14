from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.api.deps import require_admin
from shade_catalog.db.session import get_db
from shade_catalog.schemas.admin import (
    CreatePartRequest,
    CreatePartResponse,
    CreateProductRequest,
    CreateProductResponse,
    ProductDraftDocument,
    ProductDraftPayload,
    ProductSourceDocumentResponse,
    PublishSnapshotRequest,
    PublishSnapshotResponse,
    SourceDocumentCreateRequest,
    UploadAssetResponse,
)
from shade_catalog.services import admin_products, source_documents_admin, upload_assets
from shade_catalog.services import product_draft as product_draft_service
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


@admin_router.get(
    "/products/{product_id}/draft",
    response_model=ProductDraftDocument,
)
async def admin_get_product_draft(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ProductDraftDocument:
    try:
        return await product_draft_service.get_product_draft(session, product_id=product_id)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=404, detail="Product not found") from e


@admin_router.put(
    "/products/{product_id}/draft",
    response_model=ProductDraftDocument,
)
async def admin_put_product_draft(
    product_id: uuid.UUID,
    body: ProductDraftPayload,
    session: AsyncSession = Depends(get_db),
) -> ProductDraftDocument:
    try:
        async with session.begin():
            return await product_draft_service.upsert_product_draft(
                session,
                product_id=product_id,
                payload=body,
            )
    except ProductNotFoundError as e:
        raise HTTPException(status_code=404, detail="Product not found") from e


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


@admin_router.post("/uploads", response_model=UploadAssetResponse, status_code=201)
async def admin_upload_file(
    session: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
) -> UploadAssetResponse:
    async with session.begin():
        r = await upload_assets.save_uploaded_file(session, file)
    return UploadAssetResponse(
        id=r.id,
        storage_key=r.storage_key,
        kind=r.kind.value,
        original_filename=r.original_filename,
        content_type=r.content_type,
        byte_size=r.byte_size,
    )


@admin_router.get(
    "/products/{product_id}/source-documents",
    response_model=list[ProductSourceDocumentResponse],
)
async def admin_list_source_documents(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> list[ProductSourceDocumentResponse]:
    try:
        rows = await source_documents_admin.list_source_documents(session, product_id=product_id)
    except source_documents_admin.SourceDocumentError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return [source_documents_admin.to_response(r) for r in rows]


@admin_router.post(
    "/products/{product_id}/source-documents",
    response_model=ProductSourceDocumentResponse,
    status_code=201,
)
async def admin_create_source_document(
    product_id: uuid.UUID,
    body: SourceDocumentCreateRequest,
    session: AsyncSession = Depends(get_db),
) -> ProductSourceDocumentResponse:
    try:
        async with session.begin():
            doc = await source_documents_admin.attach_source_document(
                session,
                product_id=product_id,
                body=body,
            )
    except source_documents_admin.SourceDocumentError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return source_documents_admin.to_response(doc)


@admin_router.delete(
    "/products/{product_id}/source-documents/{document_id}",
    status_code=204,
)
async def admin_delete_source_document(
    product_id: uuid.UUID,
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> None:
    try:
        async with session.begin():
            await source_documents_admin.delete_source_document(
                session,
                product_id=product_id,
                document_id=document_id,
            )
    except source_documents_admin.SourceDocumentError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
