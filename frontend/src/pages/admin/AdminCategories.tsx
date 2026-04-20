import { useEffect, useState } from "react";
import { apiFetch, readError } from "@/api/client";
import type { CategorySummary, CreateCategoryResponse } from "@/api/types";

export function AdminCategories() {
  const [list, setList] = useState<CategorySummary[] | null>(null);
  const [slug, setSlug] = useState("");
  const [name, setName] = useState("");
  const [sort, setSort] = useState("0");
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  async function refresh() {
    const res = await apiFetch("/api/v1/categories");
    if (!res.ok) {
      setErr(await readError(res));
      return;
    }
    setList(await res.json());
    setErr(null);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    const res = await apiFetch("/api/v1/admin/categories", {
      method: "POST",
      admin: true,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        slug: slug.trim(),
        name: name.trim(),
        sort_order: Number(sort) || 0,
      }),
    });
    if (!res.ok) {
      setErr(await readError(res));
      return;
    }
    const created = (await res.json()) as CreateCategoryResponse;
    setErr(null);
    setMsg(`Created category “${created.name}” (${created.slug}).`);
    setSlug("");
    setName("");
    await refresh();
  }

  if (!list) return <p className="muted">Loading…</p>;

  return (
    <div>
      <h1>Categories</h1>
      {err ? <p className="error">{err}</p> : null}
      {msg ? <p style={{ color: "var(--accent)" }}>{msg}</p> : null}

      <div className="card">
        <h2>Create category</h2>
        <form onSubmit={onCreate}>
          <div className="field">
            <label htmlFor="slug">Slug</label>
            <input id="slug" value={slug} onChange={(e) => setSlug(e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="name">Name</label>
            <input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="so">Sort order</label>
            <input id="so" type="number" value={sort} onChange={(e) => setSort(e.target.value)} />
          </div>
          <button type="submit" className="btn btn-primary">
            Create
          </button>
        </form>
      </div>

      <h2>Existing (published counts from public API)</h2>
      <table className="data">
        <thead>
          <tr>
            <th>Slug</th>
            <th>Name</th>
            <th>Published products</th>
          </tr>
        </thead>
        <tbody>
          {list.map((c) => (
            <tr key={c.id}>
              <td>{c.slug}</td>
              <td>{c.name}</td>
              <td>{c.published_product_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
