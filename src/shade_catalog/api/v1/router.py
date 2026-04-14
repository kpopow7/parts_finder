from fastapi import APIRouter

from shade_catalog.api.v1 import admin, catalog

api_v1_router = APIRouter()
api_v1_router.include_router(catalog.router)
api_v1_router.include_router(admin.admin_router)
