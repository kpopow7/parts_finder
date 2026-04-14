from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog import __version__
from shade_catalog.api.v1.router import api_v1_router
from shade_catalog.db.session import get_db

app = FastAPI(title="Shade Product Catalog API", version=__version__)
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
async def health_db(session: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "shade-product-catalog", "docs": "/docs"}
