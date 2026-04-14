from __future__ import annotations

from fastapi import Header, HTTPException

from shade_catalog.core.config import get_settings


async def require_admin(authorization: str | None = Header(default=None)) -> None:
    token = get_settings().admin_api_token
    if not token:
        return
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    got = authorization.removeprefix("Bearer ").strip()
    if got != token:
        raise HTTPException(status_code=403, detail="Invalid admin token")
