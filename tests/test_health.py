from fastapi.testclient import TestClient

from shade_catalog.main import app
from shade_catalog.models.enums import ProductStatus, enum_as_str, str_enum_values_callable

client = TestClient(app)


def test_enum_as_str_plain_string_and_enum() -> None:
    assert enum_as_str("draft") == "draft"
    assert enum_as_str(ProductStatus.PUBLISHED) == "published"


def test_str_enum_values_callable_uses_lowercase_values() -> None:
    assert str_enum_values_callable(ProductStatus) == ["draft", "published", "archived"]


def test_health_ok() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_interactive_diagram_page_served() -> None:
    r = client.get("/interactive/diagram")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert b"diagram_hotspots" in r.content or b"Interactive" in r.content


def test_openapi_lists_v1_catalog_paths() -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert "/api/v1/categories" in paths
    assert "/api/v1/categories/{category_slug}/products" in paths
    assert "/api/v1/categories/{category_slug}/products/{product_slug}" in paths
    assert "/api/v1/admin/categories" in paths
    assert "/api/v1/admin/parts" in paths
    assert "get" in paths["/api/v1/admin/parts"]
    assert "/api/v1/admin/parts/{part_id}" in paths
    assert "/api/v1/admin/products" in paths
    assert "get" in paths["/api/v1/admin/products"]
    assert "/api/v1/admin/products/{product_id}/spec-imports" in paths
    assert "/api/v1/admin/products/{product_id}/spec-imports/{import_id}" in paths
    assert "/api/v1/admin/products/{product_id}/spec-imports/{import_id}/approve" in paths
    assert "/api/v1/admin/products/{product_id}/spec-imports/{import_id}/reject" in paths
    assert "/api/v1/admin/products/{product_id}/spec-imports/{import_id}/apply-to-draft" in paths
    assert "/api/v1/admin/products/{product_id}/publish" in paths
    assert "/api/v1/admin/products/{product_id}/draft" in paths
    assert "/api/v1/admin/uploads" in paths
    assert "/api/v1/assets/{storage_key}" in paths
    assert "/api/v1/search" in paths
    assert "/api/v1/admin/products/{product_id}/source-documents" in paths
