from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.models.category import Category
from shade_catalog.models.enums import PartStatus, ProductStatus
from shade_catalog.models.part import Part
from shade_catalog.models.product import Product
from shade_catalog.schemas.admin import CreatePartRequest, CreateProductRequest


class AdminValidationError(ValueError):
    pass


async def create_part(session: AsyncSession, body: CreatePartRequest) -> Part:
    part = Part(
        id=uuid.uuid4(),
        internal_part_number=body.internal_part_number.strip(),
        internal_description=body.internal_description,
        status=PartStatus.ACTIVE,
    )
    session.add(part)
    await session.flush()
    return part


async def create_product(session: AsyncSession, body: CreateProductRequest) -> Product:
    cat = (
        await session.scalars(select(Category).where(Category.slug == body.category_slug))
    ).first()
    if cat is None:
        raise AdminValidationError(f"Category not found: {body.category_slug}")

    product = Product(
        id=uuid.uuid4(),
        category_id=cat.id,
        slug=body.slug.strip(),
        name=body.name.strip(),
        subtitle=body.subtitle.strip() if body.subtitle else None,
        status=ProductStatus.DRAFT,
        current_published_snapshot_id=None,
    )
    session.add(product)
    await session.flush()
    return product
