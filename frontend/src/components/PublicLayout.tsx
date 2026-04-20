import { Link, Outlet } from "react-router-dom";

export function PublicLayout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="app-brand">
          Shade catalog
        </Link>
        <nav className="app-nav">
          <Link to="/">Browse</Link>
          <Link to="/search">Search</Link>
          <Link to="/admin">Admin</Link>
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
