# Shade product catalog (API)

Python stack: **FastAPI**, **SQLAlchemy 2** (async Postgres via **asyncpg**), **Alembic** migrations (sync **psycopg**), **Pydantic Settings**.

## Local setup

1. Copy `.env.example` to `.env` and adjust if needed.
2. Start Postgres: `docker compose up -d`
3. Create a venv and install:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
```

4. Run migrations from the **project root** (so `.env` is found): `alembic upgrade head`
5. (Optional) Load demo data for Metal blinds: `python -m shade_catalog.seed_metal_blinds`
6. Run API: `uvicorn shade_catalog.main:app --reload`

Open http://127.0.0.1:8000/docs for OpenAPI.

### Public catalog API (v1)

After seeding, these endpoints return data:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/categories` | Categories with published product counts |
| GET | `/api/v1/categories/{category_slug}/products` | Published KMATs in a category |
| GET | `/api/v1/categories/{category_slug}/products/{product_slug}` | Published snapshot: diagram, BOM, hotspots, **linked source documents** (optional `locale`) |
| GET | `/api/v1/search` | Full-text search over **published** products (`q` required; optional `category_slug`, `limit`, `offset`) |

Search uses Postgres **English** full-text on product name/subtitle, category name, and the published snapshot `search_blob`.

Demo slugs: category `metal-blinds`, product `standard-metal-blind`.

### Admin API (draft → publish)

Protected optionally: set `SHADE_CATALOG_ADMIN_API_TOKEN` in `.env`, then send `Authorization: Bearer <token>` on admin routes. If unset, admin is **open** (development only).

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/admin/parts` | Create canonical part (engineering id / description) |
| POST | `/api/v1/admin/products` | Create draft KMAT in a category (`category_slug`, `slug`, `name`, …) |
| POST | `/api/v1/admin/products/{product_id}/publish` | Publish a new snapshot (bumps `version`), updates `current_published_snapshot_id`, appends `audit_log` |
| POST | `/api/v1/admin/uploads` | Multipart upload of **SVG** or **PDF** (magic-byte sniffing); returns `storage_key` for diagram/spec references |
| GET | `/api/v1/admin/products/{product_id}/source-documents` | List linked documents for a product |
| POST | `/api/v1/admin/products/{product_id}/source-documents` | Link an **`uploaded_asset_id`** to the product (optional `title`, `sort_order`, `role`) |
| DELETE | `/api/v1/admin/products/{product_id}/source-documents/{document_id}` | Remove a link |

**File uploads:** files are stored under `SHADE_CATALOG_UPLOAD_DIR` (default `data/uploads`). Max size `SHADE_CATALOG_MAX_UPLOAD_BYTES` (default 25MB). Use the returned **`storage_key`** as `svg_storage_key` in drafts/publish (and for PDF spec links later). The public read URL is **`GET /api/v1/assets/{storage_key}`** (served only if the file is registered in `uploaded_asset`).

**Publish body** must include `bill_of_materials` and `part_displays`. For locale `en`, there must be **exactly one** display row per BOM `part_id` (same set as the BOM). `diagram_hotspots` may only reference parts that appear in the BOM. Each publish creates a new `product_snapshot` row (immutable history).

### Product draft (editor state)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/admin/products/{product_id}/draft` | Load saved draft or empty defaults (`updated_at` null if never saved) |
| PUT | `/api/v1/admin/products/{product_id}/draft` | Replace persisted draft (`product_draft.payload` JSONB); writes `audit_log` (`product_draft.upserted`) |

Draft shape matches **work-in-progress** fields (optional diagram, empty strings allowed on labels). Publishing still uses **`POST .../publish`** with a full `PublishSnapshotRequest` body (the client can load GET draft and map it into that payload when ready).

### Frontend (testing without a dedicated UI yet)

This repo is **API-only** right now. You can exercise everything in three ways:

1. **Swagger UI** — with the server running, open `/docs`, authorize if `SHADE_CATALOG_ADMIN_API_TOKEN` is set, then try search, uploads, and admin routes.
2. **curl / PowerShell** — e.g. `GET http://127.0.0.1:8000/api/v1/search?q=metal` and multipart `POST` to `/api/v1/admin/uploads`.
3. **A separate SPA** (e.g. Vite + React on port 5173) — set in `.env`:
   - `SHADE_CATALOG_CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`
   - Point `fetch` / axios at `http://127.0.0.1:8000` (or your API host).
   - Use **`asset_url_path`** from product detail as the path part of the URL (prepend the API origin), or build `GET /api/v1/assets/{storage_key}` yourself for SVG `<img src>` / PDF links.

**What a real frontend still needs:** pages for category → product → diagram/BOM, search box calling `/api/v1/search`, admin screens for draft/publish (or internal tools only), and optional auth UI if you lock down admin with a token.

### Tests

```bash
pytest tests -q
```

## Troubleshooting

### `password authentication failed for user "shade"`

The URL in `.env` must match **whichever Postgres is actually listening on port 5432**.

1. **Using Docker Compose in this repo**  
   The file `docker-compose.yml` creates user `shade`, password `shade`, database `shade_catalog`. Your `.env` should use those values (as in `.env.example`).  
   Check the container is running: `docker compose ps`.  
   If you **changed** `POSTGRES_USER` / `POSTGRES_PASSWORD` after the database was first created, Postgres still uses the **old** data in the Docker volume. Either:
   - Put the **original** credentials back in `.env`, or  
   - Reset the volume (deletes DB data): `docker compose down -v`, then `docker compose up -d`, then `alembic upgrade head` again.

2. **Another Postgres is using port 5432** (common on dev machines)  
   If you are **not** running our `docker compose` service, or it failed to bind `5432`, Alembic may be connecting to a **different** server (for example a local install) where user `shade` does not exist or has another password.  
   Fix: either stop the other service and use only Docker for this project, **or** set `SHADE_CATALOG_DATABASE_URL` and `SHADE_CATALOG_SYNC_DATABASE_URL` to that server’s real user, password, host, port, and database name.

3. **Run Alembic from the repo root**  
   Settings load `.env` from the current working directory. If you run `alembic` from another folder, you may get defaults or a different `.env`, which looks like a “wrong password” error.

Quick check when Docker is up:  
`docker compose exec db psql -U shade -d shade_catalog -c "SELECT 1"`  
If that works but Python still fails, compare the exact URL in `.env` (no extra spaces, correct password encoding for special characters).

## Why this stack

- **FastAPI**: typed routes, automatic OpenAPI, async-friendly I/O.
- **Postgres**: relational model fits categories, KMATs, snapshots, BOM, audit.
- **SQLAlchemy + Alembic**: explicit schema evolution; no lock-in to one ORM pattern.

Optional later: **HTMX + Jinja** (server-rendered admin), **Celery/ARQ** (PDF jobs), **S3-compatible** storage for PDFs/SVGs.
