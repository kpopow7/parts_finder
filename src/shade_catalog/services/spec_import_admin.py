from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.models.audit_log import AuditLog
from shade_catalog.models.enums import SpecImportStatus
from shade_catalog.models.product import Product
from shade_catalog.models.product_spec_import import ProductSpecImport
from shade_catalog.models.uploaded_asset import UploadedAsset, UploadedAssetKind
from shade_catalog.schemas.admin import ProductDraftPayload
from shade_catalog.services.product_draft import get_product_draft, upsert_product_draft
from shade_catalog.services.publish import ProductNotFoundError
from shade_catalog.services.spec_parser import (
    SpecParserError,
    parse_uploaded_spec_pdf,
    parsed_spec_result_to_jsonable,
)


class SpecImportError(ValueError):
    pass


class SpecImportNotFoundError(Exception):
    pass


def search_blob_from_parse_payload(payload: dict) -> str:
    """Flatten parsed spec fields into a single search string for ``search_blob``."""
    parts: list[str] = []
    if t := payload.get("document_title"):
        parts.append(str(t))
    if t := payload.get("product_line"):
        parts.append(str(t))
    for x in payload.get("operating_systems") or []:
        parts.append(str(x))
    for entry in payload.get("table_of_contents") or []:
        if isinstance(entry, dict) and entry.get("title"):
            parts.append(str(entry["title"]))
    for row in payload.get("size_standards") or []:
        if isinstance(row, dict) and row.get("variant"):
            parts.append(str(row["variant"]))
    return " ".join(parts).strip()


async def create_spec_import(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
    uploaded_asset_id: uuid.UUID,
) -> ProductSpecImport:
    product = await session.get(Product, product_id)
    if product is None:
        raise ProductNotFoundError

    asset = await session.get(UploadedAsset, uploaded_asset_id)
    if asset is None:
        raise SpecImportError("uploaded_asset_id not found")
    if asset.kind != UploadedAssetKind.PDF:
        raise SpecImportError("Only PDF uploads can be imported as spec data")

    try:
        parsed = await parse_uploaded_spec_pdf(session, uploaded_asset_id=uploaded_asset_id)
    except SpecParserError as e:
        raise SpecImportError(str(e)) from e

    payload = parsed_spec_result_to_jsonable(parsed)
    row = ProductSpecImport(
        id=uuid.uuid4(),
        product_id=product_id,
        uploaded_asset_id=uploaded_asset_id,
        status=SpecImportStatus.PENDING,
        parse_payload=payload,
    )
    session.add(row)
    await session.flush()
    return row


async def list_spec_imports(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
) -> list[ProductSpecImport]:
    product = await session.get(Product, product_id)
    if product is None:
        raise ProductNotFoundError

    stmt = (
        select(ProductSpecImport)
        .where(ProductSpecImport.product_id == product_id)
        .order_by(ProductSpecImport.created_at.desc())
    )
    return list((await session.scalars(stmt)).all())


async def get_spec_import(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
    import_id: uuid.UUID,
) -> ProductSpecImport:
    row = await session.get(ProductSpecImport, import_id)
    if row is None or row.product_id != product_id:
        raise SpecImportNotFoundError
    return row


async def approve_spec_import(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
    import_id: uuid.UUID,
    review_notes: str | None = None,
) -> ProductSpecImport:
    row = await get_spec_import(session, product_id=product_id, import_id=import_id)
    if row.status != SpecImportStatus.PENDING:
        raise SpecImportError("Only pending imports can be approved")
    row.status = SpecImportStatus.APPROVED
    row.reviewed_at = datetime.now(timezone.utc)
    row.review_notes = review_notes
    await session.flush()
    return row


async def reject_spec_import(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
    import_id: uuid.UUID,
    review_notes: str | None = None,
) -> ProductSpecImport:
    row = await get_spec_import(session, product_id=product_id, import_id=import_id)
    if row.status != SpecImportStatus.PENDING:
        raise SpecImportError("Only pending imports can be rejected")
    row.status = SpecImportStatus.REJECTED
    row.reviewed_at = datetime.now(timezone.utc)
    row.review_notes = review_notes
    await session.flush()
    return row


async def apply_spec_import_to_draft(
    session: AsyncSession,
    *,
    product_id: uuid.UUID,
    import_id: uuid.UUID,
    actor_user_id: uuid.UUID | None = None,
) -> ProductSpecImport:
    row = await get_spec_import(session, product_id=product_id, import_id=import_id)
    if row.status != SpecImportStatus.APPROVED:
        raise SpecImportError("Only approved imports can be applied to the draft")

    await session.execute(
        update(ProductSpecImport)
        .where(
            ProductSpecImport.product_id == product_id,
            ProductSpecImport.status == SpecImportStatus.APPLIED,
        )
        .values(status=SpecImportStatus.SUPERSEDED)
    )

    doc = await get_product_draft(session, product_id=product_id)
    payload = doc.payload
    addition = search_blob_from_parse_payload(row.parse_payload)
    if payload.search_blob and addition:
        payload.search_blob = f"{payload.search_blob}\n{addition}".strip()
    elif addition:
        payload.search_blob = addition

    payload.spec_import_id = row.id
    payload.spec_parse_data = row.parse_payload

    await upsert_product_draft(
        session,
        product_id=product_id,
        payload=payload,
        actor_user_id=actor_user_id,
    )

    row.status = SpecImportStatus.APPLIED
    row.reviewed_at = datetime.now(timezone.utc)

    session.add(
        AuditLog(
            id=uuid.uuid4(),
            actor_user_id=actor_user_id,
            action="product_spec_import.applied_to_draft",
            entity_type="product_spec_import",
            entity_id=row.id,
            metadata_={"product_id": str(product_id)},
        )
    )
    await session.flush()
    return row
