from fastapi.testclient import TestClient

from shade_catalog.main import app

client = TestClient(app)


def test_health_ok() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_openapi_lists_v1_catalog_paths() -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert "/api/v1/categories" in paths
    assert "/api/v1/categories/{category_slug}/products" in paths
    assert "/api/v1/categories/{category_slug}/products/{product_slug}" in paths
    assert "/api/v1/admin/parts" in paths
    assert "/api/v1/admin/products" in paths
    assert "/api/v1/admin/products/{product_id}/publish" in paths
    assert "/api/v1/admin/products/{product_id}/draft" in paths
    assert "/api/v1/admin/uploads" in paths
    assert "/api/v1/assets/{storage_key}" in paths
