import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiFetch, readError } from "@/api/client";
import type { SearchResponse } from "@/api/types";

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const [input, setInput] = useState(q);
  const [data, setData] = useState<SearchResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setInput(q);
  }, [q]);

  useEffect(() => {
    if (!q.trim()) {
      setData(null);
      setErr(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    (async () => {
      const res = await apiFetch(
        "/api/v1/search?" + new URLSearchParams({ q: q.trim(), limit: "30" }),
      );
      setLoading(false);
      if (!res.ok) {
        if (!cancelled) setErr(await readError(res));
        return;
      }
      const j = (await res.json()) as SearchResponse;
      if (!cancelled) {
        setData(j);
        setErr(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [q]);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setParams(input.trim() ? { q: input.trim() } : {});
  }

  return (
    <div>
      <h1>Search</h1>
      <form onSubmit={onSubmit} className="card" style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <input
          type="search"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Product name…"
          style={{ flex: "1 1 200px" }}
        />
        <button type="submit" className="btn btn-primary">
          Search
        </button>
      </form>
      {loading ? <p className="muted">Searching…</p> : null}
      {err ? <p className="error">{err}</p> : null}
      {data && !err ? (
        <div>
          <p className="muted">
            {data.total} result{data.total === 1 ? "" : "s"} for &quot;{data.query}&quot;
          </p>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {data.results.map((r) => (
              <li key={r.product_id} className="card" style={{ marginBottom: "0.5rem" }}>
                <Link to={`/c/${encodeURIComponent(r.category_slug)}/p/${encodeURIComponent(r.product_slug)}`}>
                  {r.product_name}
                </Link>
                <div className="muted" style={{ fontSize: "0.88rem" }}>
                  {r.category_name}
                  {r.subtitle ? ` · ${r.subtitle}` : ""}
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
