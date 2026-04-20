import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch, readError } from "@/api/client";
import type { CategorySummary, ProductListItem } from "@/api/types";

export function AdminProducts() {
  const [products, setProducts] = useState<ProductListItem[] | null>(null);
  const [cats, setCats] = useState<CategorySummary[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [slug, setSlug] = useState("");
  const [name, setName] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [catSlug, setCatSlug] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  async function refresh() {
    const res = await apiFetch("/api/v1/admin/products?limit=500", { admin: true });
    if (!res.ok) {
      setErr(await readError(res));
      return;
    }
    setProducts(await res.json());
    setErr(null);
  }

  useEffect(() => {
    (async () => {
      const res = await apiFetch("/api/v1/categories");
      if (res.ok) setCats(await res.json());
    })();
    refresh();
  }, []);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    const res = await apiFetch("/api/v1/admin/products", {
      method: "POST",
      admin: true,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        category_slug: catSlug.trim(),
        slug: slug.trim(),
        name: name.trim(),
        subtitle: subtitle.trim() || null,
      }),
    });
    if (!res.ok) {
      setErr(await readError(res));
      return;
    }
    setErr(null);
    setMsg("Product created.");
    setSlug("");
    setName("");
    setSubtitle("");
    await refresh();
  }

  if (!products || !cats) return <p className="muted">Loading…</p>;

  return (
    <div>
      <h1>Products</h1>
      {err ? <p className="error">{err}</p> : null}
      {msg ? <p style={{ color: "var(--accent)" }}>{msg}</p> : null}

      <div className="card">
        <h2>Create product (draft KMAT)</h2>
        <form onSubmit={onCreate}>
          <div className="field">
            <label>Category</label>
            <select value={catSlug} onChange={(e) => setCatSlug(e.target.value)} required>
              <option value="">—</option>
              {cats.map((c) => (
                <option key={c.id} value={c.slug}>
                  {c.name} ({c.slug})
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Slug</label>
            <input value={slug} onChange={(e) => setSlug(e.target.value)} required />
          </div>
          <div className="field">
            <label>Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="field">
            <label>Subtitle</label>
            <input value={subtitle} onChange={(e) => setSubtitle(e.target.value)} />
          </div>
          <button type="submit" className="btn btn-primary">
            Create
          </button>
        </form>
      </div>

      <h2>All products</h2>
      <table className="data">
        <thead>
          <tr>
            <th>Name</th>
            <th>Slug</th>
            <th>Category</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.id}>
              <td>{p.name}</td>
              <td>{p.slug}</td>
              <td>{p.category_slug}</td>
              <td>{p.status}</td>
              <td>
                <Link to={"/admin/products/" + p.id}>Edit draft / publish</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
