from __future__ import annotations

import re
import uuid
from pathlib import Path

from shade_catalog.models.uploaded_asset import UploadedAssetKind

_SAFE_KEY_RE = re.compile(r"^[a-z0-9]+/[a-f0-9\-]+\.(svg|pdf)$")


def _looks_like_svg(data: bytes) -> bool:
    head = data[:16384].lstrip()
    if head.startswith(b"\xef\xbb\xbf"):
        head = head[3:].lstrip()
    sample = head[:8192].lower()
    return b"<svg" in sample or sample.startswith(b"<?xml") or b"<!doctype svg" in sample[:500]


def detect_kind(data: bytes) -> UploadedAssetKind | None:
    if len(data) >= 4 and data[:4] == b"%PDF":
        return UploadedAssetKind.PDF

    if _looks_like_svg(data):
        return UploadedAssetKind.SVG

    return None


def build_storage_key(kind: UploadedAssetKind) -> tuple[str, str]:
    ext = ".svg" if kind == UploadedAssetKind.SVG else ".pdf"
    prefix = kind.value
    name = f"{uuid.uuid4()}{ext}"
    return f"{prefix}/{name}", name


def ensure_under_root(root: Path, storage_key: str) -> Path:
    if not _SAFE_KEY_RE.match(storage_key):
        raise ValueError("Invalid storage key")
    target = (root / storage_key).resolve()
    root_res = root.resolve()
    if root_res != target and root_res not in target.parents:
        raise ValueError("Invalid storage path")
    return target


def write_bytes(root: Path, storage_key: str, data: bytes) -> Path:
    path = ensure_under_root(root, storage_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path
