from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.models.audit_log import AuditLog
from shade_catalog.models.product import Product
from shade_catalog.models.product_draft import ProductDraft
from shade_catalog.schemas.admin import ProductDraftDocument, ProductDraftPayload
from shade_catalog.services.publish import ProductNotFoundError


async def get_product_draft(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
) -> ProductDraftDocument:
    product = await session.get(Product, product_id)
    if product is None:
        raise ProductNotFoundError

    row = await session.get(ProductDraft, product_id)
    if row is None:
        return ProductDraftDocument(
            product_id=product_id,
            payload=ProductDraftPayload(),
            updated_at=None,
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
