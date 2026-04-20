# Shade catalog UI

Vite + React + TypeScript. Two experiences:

| Area   | Routes   | Purpose |
|--------|----------|---------|
| Public | `/`, `/search`, `/c/:categorySlug`, `/c/.../p/:productSlug` | Browse published catalog, search, product detail + clickable diagram |
| Admin  | `/admin`, `/admin/categories`, … | Manage categories, parts, uploads, product drafts, publish (JSON) |

## Development

1. Start the API (repo root): `uvicorn shade_catalog.main:app --reload` on port **8000**.
2. In the API `.env`, set:
   `SHADE_CATALOG_CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`
3. Here in `frontend/`:

```bash
npm install
npm run dev
```

Open http://localhost:5173 — requests to `/api/...` are proxied to the FastAPI server.

## Admin authentication

If `SHADE_CATALOG_ADMIN_API_TOKEN` is set on the API, paste the same value in **Admin → Admin API token → Save**. It is stored in `localStorage`. If the env var is unset, admin routes stay open (development only).

## Production build

```bash
npm run build
```

Serve the `dist/` folder behind your static host. Set `VITE_API_BASE_URL` to your public API origin (e.g. `https://api.example.com`) so browser calls go to the real server (no dev proxy).
