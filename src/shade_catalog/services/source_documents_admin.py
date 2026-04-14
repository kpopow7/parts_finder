from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.models.product import Product
from shade_catalog.models.product_source_document import ProductSourceDocument
from shade_catalog.models.uploaded_asset import UploadedAsset
from shade_catalog.schemas.admin import SourceDocumentCreateRequest


class SourceDocumentError(ValueError):
    pass


async def list_source_documents(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
) -> list[ProductSourceDocument]:
    product = await session.get(Product, product_id)
    if product is None:
        raise SourceDocumentError("Product not found")
    stmt = (
        select(ProductSourceDocument)
        .where(ProductSourceDocument.product_id == product_id)
        .order_by(ProductSourceDocument.sort_order, ProductSourceDocument.id)
    )
    return list((await session.scalars(stmt)).all())


async def attach_source_document(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
    body: SourceDocumentCreateRequest,
) -> ProductSourceDocument:
    product = await session.get(Product, product_id)
    if product is None:
        raise SourceDocumentError("Product not found")
    asset = await session.get(UploadedAsset, body.uploaded_asset_id)
    if asset is None:
        raise SourceDocumentError("Uploaded asset not found")

    doc = ProductSourceDocument(
        id=uuid.uuid4(),
        product_id=product_id,
        uploaded_asset_id=asset.id,
        title=body.title,
        sort_order=body.sort_order,
        role=body.role,
    )
    session.add(doc)
    await session.flush()
    return doc


def to_response(row: ProductSourceDocument):
    from shade_catalog.schemas.admin import ProductSourceDocumentResponse

    return ProductSourceDocumentResponse(
        id=row.id,
        product_id=row.product_id,
        uploaded_asset_id=row.uploaded_asset_id,
        title=row.title,
        sort_order=row.sort_order,
        role=row.role,
    )


async def delete_source_document(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
    document_id: uuid.UUID,
) -> None:
    res = await session.execute(
        delete(ProductSourceDocument).where(
            ProductSourceDocument.id == document_id,
            ProductSourceDocument.product_id == product_id,
        )
    )
    if (res.rowcount or 0) == 0:
        raise SourceDocumentError("Document not found")


