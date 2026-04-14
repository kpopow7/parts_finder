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
| GET | `/api/v1/categories/{category_slug}/products/{product_slug}` | Published snapshot: diagram metadata, BOM, hotspots (optional `locale` query, default `en`) |

Demo slugs: category `metal-blinds`, product `standard-metal-blind`.

### Admin API (draft → publish)

Protected optionally: set `SHADE_CATALOG_ADMIN_API_TOKEN` in `.env`, then send `Authorization: Bearer <token>` on admin routes. If unset, admin is **open** (development only).

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/admin/parts` | Create canonical part (engineering id / description) |
| POST | `/api/v1/admin/products` | Create draft KMAT in a category (`category_slug`, `slug`, `name`, …) |
| POST | `/api/v1/admin/products/{product_id}/publish` | Publish a new snapshot (bumps `version`), updates `current_published_snapshot_id`, appends `audit_log` |

**Publish body** must include `bill_of_materials` and `part_displays`. For locale `en`, there must be **exactly one** display row per BOM `part_id` (same set as the BOM). `diagram_hotspots` may only reference parts that appear in the BOM. Each publish creates a new `product_snapshot` row (immutable history).

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
