from fastapi import APIRouter

from shade_catalog.api.v1 import admin, assets_public, catalog, search

api_v1_router = APIRouter()
api_v1_router.include_router(catalog.router)
api_v1_router.include_router(search.router)
api_v1_router.include_router(assets_public.public_files_router)
api_v1_router.include_router(admin.admin_router)
