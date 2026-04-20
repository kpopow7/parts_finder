import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiFetch, readError } from "@/api/client";
import type { ProductPublishedDetail } from "@/api/types";
import { DiagramViewer } from "@/components/DiagramViewer";

export function ProductDetail() {
  const { categorySlug = "", productSlug = "" } = useParams();
  const [detail, setDetail] = useState<ProductPublishedDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const res = await apiFetch(
        "/api/v1/categories/" +
          encodeURIComponent(categorySlug) +
          "/products/" +
          encodeURIComponent(productSlug),
      );
      if (!res.ok) {
        if (!cancelled) setErr(await readError(res));
        return;
      }
      const data = (await res.json()) as ProductPublishedDetail;
      if (!cancelled) {
        setDetail(data);
        setErr(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [categorySlug, productSlug]);

  if (err) return <p className="error">{err}</p>;
  if (!detail) return <p className="muted">Loading…</p>;

  const d = detail.diagram;

  return (
    <div>
      <nav className="muted" style={{ marginBottom: "0.75rem" }}>
        <Link to="/">Catalog</Link>
        {" / "}
        <Link to={`/c/${encodeURIComponent(categorySlug)}`}>{detail.category.name}</Link>
      </nav>
      <h1>{detail.product.name}</h1>
      {detail.product.subtitle ? <p className="muted">{detail.product.subtitle}</p> : null}
      <p className="muted" style={{ fontSize: "0.88rem" }}>
        Snapshot v{detail.snapshot.version} · {new Date(detail.snapshot.published_at).toLocaleString()}
      </p>

      {d ? (
        <div className="card" style={{ marginTop: "1rem" }}>
          <DiagramViewer
            svgStorageKey={d.svg_storage_key}
            rasterKey={d.raster_fallback_storage_key}
            alt={d.alt_summary ?? d.diagram_title ?? "Product diagram"}
            hotspots={detail.diagram_hotspots}
            title={d.diagram_title}
          />
        </div>
      ) : (
        <p className="muted">No diagram for this product.</p>
      )}

      <h2 style={{ marginTop: "1.5rem" }}>Bill of materials</h2>
      <div className="card" style={{ overflowX: "auto" }}>
        <table className="data">
          <thead>
            <tr>
              <th>Code</th>
              <th>Description</th>
              <th>Qty</th>
              <th>Orderable</th>
            </tr>
          </thead>
          <tbody>
            {detail.bill_of_materials
              .slice()
              .sort((a, b) => a.sort_order - b.sort_order)
              .map((row) => (
                <tr key={row.part_id}>
                  <td>{row.public_code}</td>
                  <td>{row.public_description}</td>
                  <td>{row.quantity}</td>
                  <td>{row.is_orderable ? "Yes" : "No"}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <p style={{ marginTop: "1rem" }}>
        <Link to={`/c/${encodeURIComponent(categorySlug)}`}>← Back to category</Link>
      </p>
    </div>
  );
}
