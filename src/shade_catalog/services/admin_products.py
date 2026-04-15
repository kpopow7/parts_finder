from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.models.category import Category
from shade_catalog.models.enums import PartStatus, ProductStatus
from shade_catalog.models.part import Part
from shade_catalog.models.product import Product
from shade_catalog.models.uploaded_asset import UploadedAsset, UploadedAssetKind
from shade_catalog.schemas.admin import (
    CreateCategoryRequest,
    CreatePartRequest,
    CreateProductRequest,
    UpdatePartRequest,
)


class AdminValidationError(ValueError):
    pass


class PartNotFoundError(Exception):
    pass


_PART_IMAGE_KINDS = frozenset({UploadedAssetKind.JPEG, UploadedAssetKind.PNG})


async def list_parts(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
) -> list[Part]:
    stmt = (
        select(Part)
        .order_by(Part.internal_part_number)
        .limit(limit)
        .offset(offset)
    )
    return list((await session.scalars(stmt)).all())


async def list_products(
    session: AsyncSession,
    *,
    category_slug: str | None,
    limit: int,
    offset: int,
) -> list[tuple[Product, str]]:
    stmt = select(Product, Category.slug).join(Category, Product.category_id == Category.id)
    if category_slug is not None and category_slug.strip():
        stmt = stmt.where(Category.slug == category_slug.strip())
    stmt = stmt.order_by(Category.slug, Product.name).limit(limit).offset(offset)
    rows = (await session.execute(stmt)).all()
    return [(p, str(cat_slug)) for p, cat_slug in rows]


async def create_category(session: AsyncSession, body: CreateCategoryRequest) -> Category:
    slug = body.slug.strip()
    name = body.name.strip()
    if not slug or not name:
        raise AdminValidationError("slug and name must not be empty after trimming whitespace")
    cat = Category(
        id=uuid.uuid4(),
        slug=slug,
        name=name,
        sort_order=body.sort_order,
    )
    session.add(cat)
    await session.flush()
    return cat


async def _validate_part_image_asset(session: AsyncSession, asset_id: uuid.UUID | None) -> None:
    if asset_id is None:
        return
    asset = await session.get(UploadedAsset, asset_id)
    if asset is None:
        raise AdminValidationError("image_uploaded_asset_id: uploaded asset not found")
    if asset.kind not in _PART_IMAGE_KINDS:
        raise AdminValidationError(
            "image_uploaded_asset_id: must reference a JPEG or PNG from POST /api/v1/admin/uploads"
        )


async def create_part(session: AsyncSession, body: CreatePartRequest) -> Part:
    await _validate_part_image_asset(session, body.image_uploaded_asset_id)
    part = Part(
        id=uuid.uuid4(),
        internal_part_number=body.internal_part_number.strip(),
        internal_description=body.internal_description,
        status=PartStatus.ACTIVE,
        image_uploaded_asset_id=body.image_uploaded_asset_id,
    )
    session.add(part)
    await session.flush()
    return part


async def update_part(session: AsyncSession, *, part_id: uuid.UUID, body: UpdatePartRequest) -> Part:
    part = await session.get(Part, part_id)
    if part is None:
        raise PartNotFoundError
    await _validate_part_image_asset(session, body.image_uploaded_asset_id)
    part.image_uploaded_asset_id = body.image_uploaded_asset_id
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
