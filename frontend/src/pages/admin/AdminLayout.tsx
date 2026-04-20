import { Link, NavLink, Outlet } from "react-router-dom";
import { useState } from "react";
import { getAdminToken, setAdminToken } from "@/api/client";

export function AdminLayout() {
  const [token, setTok] = useState(() => getAdminToken() ?? "");
  const hasToken = Boolean(getAdminToken());

  function saveToken() {
    setAdminToken(token.trim() || null);
    setTok(getAdminToken() ?? "");
  }

  function clearToken() {
    setAdminToken(null);
    setTok("");
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="app-brand">
          Shade catalog
        </Link>
        <nav className="app-nav">
          <Link to="/">Public site</Link>
        </nav>
      </header>
      <div className="app-main">
        <div className="card token-bar" style={{ marginBottom: "1rem" }}>
          <strong style={{ marginRight: "0.5rem" }}>Admin API token</strong>
          <span className="muted" style={{ marginRight: "0.75rem" }}>
            (matches <code>SHADE_CATALOG_ADMIN_API_TOKEN</code> in the API; leave empty if unset)
          </span>
          <input
            type="password"
            autoComplete="off"
            value={token}
            onChange={(e) => setTok(e.target.value)}
            placeholder="Bearer token"
            style={{ maxWidth: "320px" }}
          />
          <button type="button" className="btn btn-primary" onClick={saveToken}>
            Save
          </button>
          {hasToken ? (
            <button type="button" className="btn" onClick={clearToken}>
              Clear
            </button>
          ) : null}
        </div>

        <div className="admin-layout">
          <aside className="admin-side">
            <NavLink
              to="/admin"
              end
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              Overview
            </NavLink>
            <NavLink
              to="/admin/categories"
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              Categories
            </NavLink>
            <NavLink to="/admin/parts" className={({ isActive }) => (isActive ? "active" : "")}>
              Parts
            </NavLink>
            <NavLink to="/admin/uploads" className={({ isActive }) => (isActive ? "active" : "")}>
              Uploads
            </NavLink>
            <NavLink
              to="/admin/products"
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              Products
            </NavLink>
          </aside>
          <div>
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}
