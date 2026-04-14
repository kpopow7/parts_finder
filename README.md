# Shade product catalog (API)

Python stack: **FastAPI**, **SQLAlchemy 2** (async Postgres via **asyncpg**), **Alembic** migrations (sync **psycopg**), **Pydantic Settings**.

## Data setup flow

Follow these steps in order so the database schema exists and the API has something to serve. (Commands are spelled out again under **Local setup** below.)

1. **Environment** — Copy `.env.example` to `.env`. Set `SHADE_CATALOG_DATABASE_URL` and `SHADE_CATALOG_SYNC_DATABASE_URL` so they match the Postgres you will actually use (same host, port, user, password, database name as in Docker Compose if you use it).
2. **Postgres** — Start the database (for example `docker compose up -d` from the repo root). Confirm the container or instance is reachable on the port your `.env` uses.
3. **Python dependencies** — Create a virtual environment and install the package (see **Local setup** for exact commands). Either `pip install -e ".[dev]"` or `pip install -r requirements.txt` is fine for running the app and tooling.
4. **Schema (migrations)** — From the **project root**, run `alembic upgrade head`. This creates or updates tables only; it does **not** insert categories, products, or demo KMATs.
5. **Catalog data** — Choose one path (exact table order and API bodies are in **Creating catalog data in detail** below):
   - **Demo data (easiest first run):** `python -m shade_catalog.seed_metal_blinds` after migrations. It does nothing if the `metal-blinds` category already exists.
   - **Your own data:** Create a category (`POST /api/v1/admin/categories`), then parts → optional uploads → product → publish. Public catalog and search only show **published** snapshots.
6. **Run the server** — `uvicorn shade_catalog.main:app --reload`. Open `/docs` to try endpoints. Without step 5 (or equivalent admin work), list/search routes may be empty but the app still runs.

**Uploads directory:** Ensure `SHADE_CATALOG_UPLOAD_DIR` exists (default `data/uploads`) if you use file uploads or diagrams stored on disk.

## Creating catalog data in detail

Migrations create **empty** tables. You add rows in an order that respects foreign keys. The public API reads **published** products only (`product.current_published_snapshot_id` set, snapshot rows present).

### Tables involved (short map)

| Area | Table(s) |
|------|----------|
| Taxonomy | `category`, `product` (`product.category_id` → `category`) |
| Engineering parts | `part` (referenced by BOM and hotspots; optional `image_uploaded_asset_id` → JPEG/PNG `uploaded_asset`) |
| Publish snapshot | `product_snapshot`, `snapshot_bom_line`, `snapshot_part_display`, optional `snapshot_diagram`, `snapshot_diagram_hotspot` |
| Audit | `audit_log` (e.g. on publish, draft save) |
| Files | `uploaded_asset` (+ files under `SHADE_CATALOG_UPLOAD_DIR`) |
| Optional | `product_draft` (WIP JSON), `product_source_document` (link product ↔ uploaded PDF/SVG) |

### Option A — Demo seed (single command)

From the project root (after migrations):

```bash
python -m shade_catalog.seed_metal_blinds
```

**Order of inserts (conceptually):** `category` → `part` (several rows) → `product` → `product_snapshot` (version 1) → `snapshot_bom_line`, `snapshot_part_display`, `snapshot_diagram`, `snapshot_diagram_hotspot` → `product` updated to published with `current_published_snapshot_id` set.

If a row with `slug = metal-blinds` already exists in `category`, the script **exits without changing anything** (safe re-run).

### Option B — Build data yourself (exact order)

Do these steps in order. Use `/docs` or any HTTP client; if `SHADE_CATALOG_ADMIN_API_TOKEN` is set, send `Authorization: Bearer <token>` on admin routes.

1. **`category` (required first)**  
   `POST /api/v1/admin/products` requires an existing `category_slug`. Create the category with:

   ```http
   POST /api/v1/admin/categories
   Content-Type: application/json

   {"slug": "metal-blinds", "name": "Metal blinds", "sort_order": 10}
   ```

   `sort_order` defaults to `0` if omitted. Slug and name are trimmed; slug must be unique (409 if duplicate). You need at least one category before creating a product (step 4).

2. **`part` (one row per BOM line)**  
   For each engineering part: `POST /api/v1/admin/parts` with JSON, for example:

   ```json
   {
     "internal_part_number": "ENG-MB-001",
     "internal_description": "Optional",
     "image_uploaded_asset_id": null
   }
   ```

   To attach a **JPEG or PNG** photo, upload the image first (`POST /api/v1/admin/uploads`), then set `image_uploaded_asset_id` to the returned asset **`id`** (not the storage key). Only JPEG/PNG uploads are accepted for part images. To change or remove the photo later: `PATCH /api/v1/admin/parts/{part_id}` with `{"image_uploaded_asset_id": "<uuid>"}` or `{"image_uploaded_asset_id": null}`.  
   Save each returned part `id` (UUID); those are the `part_id` values used in the BOM and displays. `internal_part_number` must be unique.

3. **`uploaded_asset` (optional diagram or spec files)**  
   If the published snapshot will include a diagram: `POST /api/v1/admin/uploads` (multipart file field) with an **SVG** file. Response includes `storage_key` and `id`. Use that `storage_key` as `diagram.svg_storage_key` when you publish. For a linked PDF spec only (no diagram), upload a PDF and use step 6; diagram SVG is not required if you omit `diagram` in the publish body. (JPEG/PNG uploads are for part photos, step 2.)

4. **`product` (draft KMAT)**  
   `POST /api/v1/admin/products` with JSON:

   ```json
   {
     "category_slug": "metal-blinds",
     "slug": "my-product",
     "name": "My product",
     "subtitle": "Optional"
   }
   ```

   Save the returned `id` as `product_id`. This creates a `product` row in **draft**; it does not appear on the public catalog until you publish.

5. **`product_draft` (optional)**  
   `PUT /api/v1/admin/products/{product_id}/draft` — saves work-in-progress BOM/diagram/hotspots as JSON. Does **not** replace publishing; the public API still reads published snapshots only.

6. **`product_source_document` (optional)**  
   Upload a PDF (or reuse an asset): `POST /api/v1/admin/uploads`, then `POST /api/v1/admin/products/{product_id}/source-documents` with `{"uploaded_asset_id": "<uuid>", "title": "...", "sort_order": 0, "role": "spec"}`. This only links the file to the product; it does not fill the BOM.

7. **PDF spec helper (read-only)**  
   `GET /api/v1/admin/uploads/{uploaded_asset_id}/parse-spec` (PDF assets only) returns a first-pass structured parse (TOC, size snippets, colors, etc.). It **does not write** to Postgres; use it to assist manual data entry or a future importer.

8. **`product_snapshot` + children (publish)**  
   `POST /api/v1/admin/products/{product_id}/publish` with a full `PublishSnapshotRequest` body. This is the step that creates catalog-visible data.

   **Validation rules (must all pass):**

   - `bill_of_materials` — non-empty list. Each item: `part_id` (UUID from step 2), `quantity` **> 0**, optional `sort_order`, `bom_group`, `show_on_diagram`.
   - `part_displays` — must include **exactly one** display row per BOM `part_id` for **`locale`: `"en"`** (same set of parts: no missing, no extra).
   - `diagram` — optional. If present, `svg_storage_key` must match a key returned from step 3 (file must still exist under the upload directory).
   - `diagram_hotspots` — optional; each `part_id` must appear in the BOM.
   - Optional top-level fields: `publish_notes`, `search_blob` (useful for `/api/v1/search`).

   **What publish writes:** a new `product_snapshot` row (version increments), `snapshot_bom_line` and `snapshot_part_display` rows for that snapshot, optional `snapshot_diagram` / `snapshot_diagram_hotspot`, updates `product` to **published** and sets `current_published_snapshot_id`, and appends `audit_log`.

9. **Later changes**  
   Each successful publish creates a **new** snapshot version; old snapshots remain for history. To change the live catalog, publish again with a new body.

### Quick sanity check

After publish: `GET /api/v1/categories/{category_slug}/products` should list your product slug, and `GET /api/v1/categories/{category_slug}/products/{product_slug}` should return the snapshot, BOM, and diagram if you included one.

## Local setup

Use this section for copy-paste commands; the checklist above is the same flow in short form.

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
| POST | `/api/v1/admin/categories` | Create category (`slug`, `name`, optional `sort_order`) |
| POST | `/api/v1/admin/parts` | Create canonical part (optional `image_uploaded_asset_id`: must be a **JPEG or PNG** from uploads) |
| PATCH | `/api/v1/admin/parts/{part_id}` | Set or clear part photo (`image_uploaded_asset_id`: UUID or `null`) |
| POST | `/api/v1/admin/products` | Create draft KMAT in a category (`category_slug`, `slug`, `name`, …) |
| POST | `/api/v1/admin/products/{product_id}/publish` | Publish a new snapshot (bumps `version`), updates `current_published_snapshot_id`, appends `audit_log` |
| POST | `/api/v1/admin/uploads` | Multipart upload: **SVG**, **PDF**, **JPEG**, or **PNG** (magic-byte sniffing); use SVG keys for published diagrams, PDF for specs, JPEG/PNG for part photos |
| GET | `/api/v1/admin/products/{product_id}/source-documents` | List linked documents for a product |
| POST | `/api/v1/admin/products/{product_id}/source-documents` | Link an **`uploaded_asset_id`** to the product (optional `title`, `sort_order`, `role`) |
| DELETE | `/api/v1/admin/products/{product_id}/source-documents/{document_id}` | Remove a link |

**File uploads:** files are stored under `SHADE_CATALOG_UPLOAD_DIR` (default `data/uploads`). Max size `SHADE_CATALOG_MAX_UPLOAD_BYTES` (default 25MB). Use the returned **`storage_key`** as `svg_storage_key` in drafts/publish for diagrams; link PDFs via source documents; pass the returned **`id`** as `image_uploaded_asset_id` on part create/patch for JPEG/PNG part images. The public read URL is **`GET /api/v1/assets/{storage_key}`** (served only if the file is registered in `uploaded_asset`). Published product detail includes optional **`part_image_*`** fields on each BOM line when a part has an image.

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
