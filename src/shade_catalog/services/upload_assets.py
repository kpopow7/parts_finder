from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.core.config import get_settings
from shade_catalog.models.uploaded_asset import UploadedAsset, UploadedAssetKind
from shade_catalog.services import local_storage


@dataclass(frozen=True)
class UploadResult:
    id: uuid.UUID
    storage_key: str
    kind: UploadedAssetKind
    original_filename: str
    content_type: str
    byte_size: int


def _normalize_content_type(kind: UploadedAssetKind, raw: str | None) -> str:
    if raw and raw.strip():
        return raw.strip()
    if kind == UploadedAssetKind.SVG:
        return "image/svg+xml"
    if kind == UploadedAssetKind.JPEG:
        return "image/jpeg"
    if kind == UploadedAssetKind.PNG:
        return "image/png"
    return "application/pdf"


async def save_uploaded_file(session: AsyncSession, file: UploadFile) -> UploadResult:
    settings = get_settings()
    max_b = settings.max_upload_bytes
    data = await file.read()
    if len(data) > max_b:
        raise HTTPException(status_code=413, detail="File too large")

    filename = file.filename or "upload"
    kind = local_storage.detect_kind(data)
    if kind is None:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type (only SVG, PDF, JPEG, or PNG are accepted)",
        )

    storage_key, _ = local_storage.build_storage_key(kind)
    content_type = _normalize_content_type(kind, file.content_type)

    try:
        local_storage.write_bytes(settings.upload_dir, storage_key, data)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to store file: {e}") from e

    row = UploadedAsset(
        id=uuid.uuid4(),
        storage_key=storage_key,
        kind=kind,
        original_filename=filename[:500],
        content_type=content_type[:120],
        byte_size=len(data),
    )
    session.add(row)
    try:
        await session.flush()
    except Exception:
        try:
            path = local_storage.ensure_under_root(settings.upload_dir, storage_key)
            path.unlink(missing_ok=True)
        except ValueError:
            pass
        raise

    return UploadResult(
        id=row.id,
        storage_key=row.storage_key,
        kind=row.kind,
        original_filename=row.original_filename,
        content_type=row.content_type,
        byte_size=row.byte_size,
    )


async def get_asset_for_download(
    session: AsyncSession,
    *,
    storage_key: str,
) -> tuple[UploadedAsset, Path] | None:
    settings = get_settings()
    row = (
        await session.scalars(
            select(UploadedAsset).where(UploadedAsset.storage_key == storage_key)
        )
    ).first()
    if row is None:
        return None
    try:
        path = local_storage.ensure_under_root(settings.upload_dir, storage_key)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return row, path
