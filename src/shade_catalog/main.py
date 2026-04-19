from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware

from shade_catalog import __version__
from shade_catalog.api.v1.router import api_v1_router
from shade_catalog.core.config import get_settings
from shade_catalog.db.session import get_db

app = FastAPI(title="Shade Product Catalog API", version=__version__)
app.include_router(api_v1_router, prefix="/api/v1")

_INTERACTIVE_DIAGRAM = Path(__file__).resolve().parents[2] / "static" / "interactive_diagram.html"

_origins = [o.strip() for o in get_settings().cors_allow_origins.split(",") if o.strip()]
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
async def health_db(session: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "shade-product-catalog",
        "docs": "/docs",
        "interactive_diagram": "/interactive/diagram",
    }


@app.get("/interactive/diagram")
async def interactive_diagram() -> FileResponse:
    """Point-and-click diagram viewer (uses public catalog API + diagram hotspots)."""
    if not _INTERACTIVE_DIAGRAM.is_file():
        raise HTTPException(status_code=404, detail="Interactive diagram page not found")
    return FileResponse(
        str(_INTERACTIVE_DIAGRAM),
        media_type="text/html; charset=utf-8",
    )
