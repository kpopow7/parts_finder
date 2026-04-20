import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch, readError } from "@/api/client";
import type { CategorySummary } from "@/api/types";

export function Home() {
  const [cats, setCats] = useState<CategorySummary[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const res = await apiFetch("/api/v1/categories");
      if (!res.ok) {
        if (!cancelled) setErr(await readError(res));
        return;
      }
      const data = (await res.json()) as CategorySummary[];
      if (!cancelled) {
        setCats(data);
        setErr(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (err) return <p className="error">Could not load categories: {err}</p>;
  if (!cats) return <p className="muted">Loading…</p>;

  return (
    <div>
      <h1>Catalog</h1>
      <p className="muted">Published products by category.</p>
      <ul style={{ listStyle: "none", padding: 0 }}>
        {cats.map((c) => (
          <li key={c.id} className="card" style={{ marginBottom: "0.65rem" }}>
            <Link to={`/c/${encodeURIComponent(c.slug)}`}>
              <strong>{c.name}</strong>
            </Link>
            <span className="muted" style={{ marginLeft: "0.5rem" }}>
              ({c.published_product_count} products)
            </span>
          </li>
        ))}
      </ul>
      {cats.length === 0 ? <p className="muted">No categories yet.</p> : null}
    </div>
  );
}
