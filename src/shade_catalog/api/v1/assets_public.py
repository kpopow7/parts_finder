from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.db.session import get_db
from shade_catalog.services import upload_assets

public_files_router = APIRouter(tags=["assets"])


@public_files_router.get("/assets/{storage_key:path}")
async def get_uploaded_file(
    storage_key: str,
    session: AsyncSession = Depends(get_db),
) -> FileResponse:
    result = await upload_assets.get_asset_for_download(session, storage_key=storage_key)
    if result is None:
        raise HTTPException(status_code=404, detail="Not found")
    row, path = result
    return FileResponse(
        str(path),
        media_type=row.content_type,
        filename=row.original_filename,
    )
