import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiFetch, readError } from "@/api/client";
import type { ProductSummary } from "@/api/types";

export function CategoryProducts() {
  const { categorySlug = "" } = useParams();
  const [products, setProducts] = useState<ProductSummary[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const res = await apiFetch(
        "/api/v1/categories/" + encodeURIComponent(categorySlug) + "/products",
      );
      if (!res.ok) {
        if (!cancelled) setErr(await readError(res));
        return;
      }
      const data = (await res.json()) as ProductSummary[];
      if (!cancelled) {
        setProducts(data);
        setErr(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [categorySlug]);

  if (err) return <p className="error">{err}</p>;
  if (!products) return <p className="muted">Loading…</p>;

  return (
    <div>
      <h1>Products</h1>
      <p className="muted">
        Category: <strong>{categorySlug}</strong>
      </p>
      <ul style={{ listStyle: "none", padding: 0 }}>
        {products.map((p) => (
          <li key={p.id} className="card" style={{ marginBottom: "0.5rem" }}>
            <Link to={`/c/${encodeURIComponent(categorySlug)}/p/${encodeURIComponent(p.slug)}`}>
              {p.name}
            </Link>
            {p.subtitle ? <div className="muted">{p.subtitle}</div> : null}
          </li>
        ))}
      </ul>
      {products.length === 0 ? <p className="muted">No published products in this category.</p> : null}
      <p>
        <Link to="/">← Back to categories</Link>
      </p>
    </div>
  );
}
