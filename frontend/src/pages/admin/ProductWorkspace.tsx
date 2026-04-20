import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiFetch, readError } from "@/api/client";
import type { ProductDraftDocument, ProductListItem } from "@/api/types";

export function ProductWorkspace() {
  const { productId = "" } = useParams();
  const [product, setProduct] = useState<ProductListItem | null | undefined>(undefined);
  const [draftJson, setDraftJson] = useState("");
  const [publishJson, setPublishJson] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const listRes = await apiFetch("/api/v1/admin/products?limit=500", { admin: true });
      if (!listRes.ok) return;
      const list = (await listRes.json()) as ProductListItem[];
      const p = list.find((x) => x.id === productId);
      if (!cancelled) setProduct(p === undefined ? null : p);
    })();
    return () => {
      cancelled = true;
    };
  }, [productId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!productId) return;
      const res = await apiFetch("/api/v1/admin/products/" + encodeURIComponent(productId) + "/draft", {
        admin: true,
      });
      if (!res.ok) {
        if (!cancelled) setErr(await readError(res));
        return;
      }
      const doc = (await res.json()) as ProductDraftDocument;
      if (!cancelled) {
        setDraftJson(JSON.stringify(doc.payload ?? {}, null, 2));
        setErr(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [productId]);

  async function saveDraft(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    let payload: Record<string, unknown>;
    try {
      payload = JSON.parse(draftJson) as Record<string, unknown>;
    } catch {
      setErr("Draft is not valid JSON.");
      return;
    }
    const res = await apiFetch(
      "/api/v1/admin/products/" + encodeURIComponent(productId) + "/draft",
      {
        method: "PUT",
        admin: true,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    if (!res.ok) {
      setErr(await readError(res));
      return;
    }
    setErr(null);
    setMsg("Draft saved.");
  }

  async function publish(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    let body: unknown;
    try {
      body = JSON.parse(publishJson);
    } catch {
      setErr("Publish body is not valid JSON.");
      return;
    }
    const res = await apiFetch(
      "/api/v1/admin/products/" + encodeURIComponent(productId) + "/publish",
      {
        method: "POST",
        admin: true,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      setErr(await readError(res));
      return;
    }
    const out = await res.json();
    setErr(null);
    setMsg("Published snapshot v" + String((out as { version?: number }).version ?? "?"));
  }

  if (!productId) return <p className="error">Missing product id.</p>;
  if (product === undefined) return <p className="muted">Loading…</p>;
  if (product === null) return <p className="error">Product not found.</p>;

  return (
    <div>
      <p>
        <Link to="/admin/products">← Products</Link>
      </p>
      <h1>{product.name}</h1>
      <p className="muted">
        {product.category_slug} / {product.slug} · {product.status}
      </p>
      {err ? <p className="error">{err}</p> : null}
      {msg ? <p style={{ color: "var(--accent)" }}>{msg}</p> : null}

      <div className="card">
        <h2>Draft payload</h2>
        <p className="muted" style={{ fontSize: "0.88rem" }}>
          Edit JSON (BOM, diagram keys, hotspots, part displays). See OpenAPI schema{" "}
          <code>ProductDraftPayload</code>.
        </p>
        <form onSubmit={saveDraft}>
          <textarea
            value={draftJson}
            onChange={(e) => setDraftJson(e.target.value)}
            rows={18}
            style={{ width: "100%", maxWidth: "100%", fontFamily: "ui-monospace, monospace", fontSize: "0.8rem" }}
          />
          <button type="submit" className="btn btn-primary" style={{ marginTop: "0.5rem" }}>
            Save draft
          </button>
        </form>
      </div>

      <div className="card">
        <h2>Publish snapshot</h2>
        <p className="muted" style={{ fontSize: "0.88rem" }}>
          POST a full <code>PublishSnapshotRequest</code> body (bill_of_materials, part_displays,
          optional diagram, diagram_hotspots). Example available in README / OpenAPI.
        </p>
        <form onSubmit={publish}>
          <textarea
            value={publishJson}
            onChange={(e) => setPublishJson(e.target.value)}
            rows={16}
            placeholder='{"bill_of_materials":[],"part_displays":[],"diagram":null,"diagram_hotspots":[]}'
            style={{ width: "100%", maxWidth: "100%", fontFamily: "ui-monospace, monospace", fontSize: "0.8rem" }}
          />
          <button type="submit" className="btn btn-primary" style={{ marginTop: "0.5rem" }}>
            Publish
          </button>
        </form>
      </div>
    </div>
  );
}
