from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from shade_catalog.core.config import get_settings
from shade_catalog.models.uploaded_asset import UploadedAsset, UploadedAssetKind
from shade_catalog.services import local_storage

_TOC_RE = re.compile(r"^(?P<title>.+?)\s\.{3,}\s(?P<page_ref>MPM-\d+)\s*$")
_PAIR_RE = re.compile(
    r"^(?P<left>.+? - \d{2,4})\s{2,}(?P<right>.+? - \d{2,4})$",
)
_PRICE_MAP_RE = re.compile(
    r"^(?P<color>.+? - \d{2,4})\s{2,}(?P<charts>MPM-\d(?:,\s*MPM-\d)*)$",
)


@dataclass(frozen=True)
class ParsedSizeStandard:
    variant: str
    min_width: str | None
    max_width: str | None
    min_height: str | None
    max_height: str | None
    max_area_sqft: str | None


@dataclass(frozen=True)
class ParsedSpecResult:
    source_asset_id: uuid.UUID
    original_filename: str
    document_title: str | None
    product_line: str | None
    table_of_contents: list[dict[str, str]]
    operating_systems: list[str]
    size_standards: list[ParsedSizeStandard]
    bottom_rail_color_pairs: list[dict[str, str]]
    price_chart_color_map: list[dict[str, object]]
    warnings: list[str]


class SpecParserError(ValueError):
    pass


async def parse_uploaded_spec_pdf(
    session: AsyncSession,
    *,
    uploaded_asset_id: uuid.UUID,
) -> ParsedSpecResult:
    asset = await session.get(UploadedAsset, uploaded_asset_id)
    if asset is None:
        raise SpecParserError("Uploaded asset not found")
    if asset.kind != UploadedAssetKind.PDF:
        raise SpecParserError("Uploaded asset is not a PDF")

    settings = get_settings()
    try:
        path = local_storage.ensure_under_root(settings.upload_dir, asset.storage_key)
    except ValueError as e:
        raise SpecParserError("Invalid PDF storage path") from e
    if not path.is_file():
        raise SpecParserError("Uploaded PDF file is missing on disk")

    text = _extract_pdf_text(path)
    return _parse_text(asset_id=asset.id, filename=asset.original_filename, text=text)


def _extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages: list[str] = []
    total = len(reader.pages)
    for i, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        pages.append(f"-- {i} of {total} --\n{page_text}")
    return "\n\n".join(pages)


def _parse_text(*, asset_id: uuid.UUID, filename: str, text: str) -> ParsedSpecResult:
    lines = [_normalize_line(x) for x in text.splitlines()]
    compact_lines = [x for x in lines if x]
    joined = "\n".join(compact_lines)

    toc = _parse_toc(compact_lines)
    operating_systems = _parse_operating_systems(joined)
    size_standards, size_warnings = _parse_size_standards(joined)
    color_pairs = _parse_color_pairs(compact_lines)
    price_map = _parse_price_chart_color_map(compact_lines)

    warnings: list[str] = []
    if not toc:
        warnings.append("No table-of-contents entries detected.")
    if not size_standards:
        warnings.append("No size standards blocks detected.")
    warnings.extend(size_warnings)

    return ParsedSpecResult(
        source_asset_id=asset_id,
        original_filename=filename,
        document_title=_first_line_with(compact_lines, "Product Specifications Guide"),
        product_line=_first_line_with(compact_lines, "MODERN PRECIOUS METALS"),
        table_of_contents=toc,
        operating_systems=operating_systems,
        size_standards=size_standards,
        bottom_rail_color_pairs=color_pairs,
        price_chart_color_map=price_map,
        warnings=warnings,
    )


def _normalize_line(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _parse_toc(lines: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in lines:
        match = _TOC_RE.match(line)
        if not match:
            continue
        rows.append(
            {
                "title": match.group("title"),
                "page_ref": match.group("page_ref"),
            }
        )
    return rows


def _parse_operating_systems(text: str) -> list[str]:
    found: list[str] = []
    variants = (
        "LiteRise",
        "SimpleLift",
        "SimpleLift with PowerView Gen 3 Automation Tilt-Only",
    )
    for item in variants:
        if item in text:
            found.append(item)
    return found


def _parse_size_standards(text: str) -> tuple[list[ParsedSizeStandard], list[str]]:
    variants = (
        'LiteRise® – 1" Decor®',
        'LiteRise® – 2" Macro',
        'SimpleLift™ – 1" Celebrity® and ½" & 1" Décor®',
        'SimpleLift™ – 2" Macro',
        "SimpleLift™ with PowerView Gen 3 Automation Tilt-Only",
    )

    rows: list[ParsedSizeStandard] = []
    warnings: list[str] = []
    for variant in variants:
        idx = text.find(variant)
        if idx < 0:
            warnings.append(f"Variant not found in text: {variant}")
            continue
        block = text[idx : idx + 2000]
        rows.append(
            ParsedSizeStandard(
                variant=variant,
                min_width=_measure_value(block, "Min. Width"),
                max_width=_measure_value(block, "Max. Width"),
                min_height=_measure_value(block, "Min. Height"),
                max_height=_measure_value(block, "Max. Height"),
                max_area_sqft=_measure_value(block, "Max. Area (sq. ft.)"),
            )
        )
    return rows, warnings


def _measure_value(block: str, label: str) -> str | None:
    pattern = re.compile(rf"{re.escape(label)}\s+([^\n]+)")
    match = pattern.search(block)
    if not match:
        return None
    value = match.group(1).strip()
    if value.lower().startswith("notes"):
        return None
    return value[:64]


def _parse_color_pairs(lines: list[str]) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    for line in lines:
        m = _PAIR_RE.match(line)
        if not m:
            continue
        left = m.group("left")
        right = m.group("right")
        if left.startswith("Color ") or left.startswith("Slat Color "):
            continue
        pairs.append({"slat_color": left, "default_bottom_rail_color": right})
    return pairs


def _parse_price_chart_color_map(lines: list[str]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for line in lines:
        m = _PRICE_MAP_RE.match(line)
        if not m:
            continue
        charts = [x.strip() for x in m.group("charts").split(",")]
        result.append({"color": m.group("color"), "price_charts": charts})
    return result


def _first_line_with(lines: list[str], needle: str) -> str | None:
    for line in lines:
        if needle in line:
            return line
    return None
