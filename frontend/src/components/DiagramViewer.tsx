import { useEffect, useState, type CSSProperties } from "react";
import type { HotspotPublic } from "@/api/types";
import { apiUrl } from "@/api/client";

function toFiniteNumber(v: unknown): number | null {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string" && v.trim() !== "") {
    const n = Number(v);
    if (Number.isFinite(n)) return n;
  }
  return null;
}

function asGeometryRecord(raw: unknown): Record<string, unknown> | null {
  if (raw !== null && typeof raw === "object" && !Array.isArray(raw)) {
    return raw as Record<string, unknown>;
  }
  if (typeof raw === "string") {
    try {
      const parsed: unknown = JSON.parse(raw);
      return asGeometryRecord(parsed);
    } catch {
      return null;
    }
  }
  return null;
}

/** Accept API/draft geometry with numeric fields as strings; tolerate missing `type`. */
function normalizeHotspotGeometry(geometry: unknown):
  | { kind: "rect"; x: number; y: number; width: number; height: number }
  | { kind: "circle"; cx: number; cy: number; r: number }
  | null {
  const g = asGeometryRecord(geometry);
  if (!g) return null;

  const typeRaw = g.type;
  const typeStr = typeof typeRaw === "string" ? typeRaw.toLowerCase().trim() : "";

  const cx = toFiniteNumber(g.cx);
  const cy = toFiniteNumber(g.cy);
  const r = toFiniteNumber(g.r);
  const x = toFiniteNumber(g.x);
  const y = toFiniteNumber(g.y);
  const width = toFiniteNumber(g.width);
  const height = toFiniteNumber(g.height);

  if (typeStr === "circle" || (typeStr !== "rect" && cx !== null && r !== null)) {
    if (cx === null || r === null) return null;
    return { kind: "circle", cx, cy: cy !== null ? cy : 50, r };
  }

  if (typeStr === "rect" || (x !== null && y !== null)) {
    if (x === null || y === null) return null;
    return {
      kind: "rect",
      x,
      y,
      width: width !== null ? width : 0,
      height: height !== null ? height : 0,
    };
  }

  return null;
}

type Props = {
  svgStorageKey: string | null;
  rasterKey: string | null;
  alt: string;
  hotspots: HotspotPublic[];
  title: string | null;
};

export function DiagramViewer({ svgStorageKey, rasterKey, alt, hotspots, title }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const [imgError, setImgError] = useState(false);

  const src = svgStorageKey
    ? apiUrl(
        "/api/v1/assets/" +
          svgStorageKey.split("/").map(encodeURIComponent).join("/"),
      )
    : rasterKey
      ? apiUrl("/api/v1/assets/" + rasterKey.split("/").map(encodeURIComponent).join("/"))
      : null;

  useEffect(() => {
    setSelected(null);
    setImgError(false);
  }, [src]);

  const h = hotspots.find((x) => x.part_id === selected);

  if (!src) {
    return <p className="muted">No diagram for this product.</p>;
  }

  return (
    <div>
      {title ? <h2 style={{ marginTop: 0 }}>{title}</h2> : null}
      <div className="diagram-wrap">
        {!imgError ? (
          <img src={src} alt={alt} onError={() => setImgError(true)} />
        ) : (
          <div style={{ padding: "2rem", textAlign: "center" }} className="muted">
            Could not load diagram image.
          </div>
        )}
        <div className="hotspot-layer" aria-hidden="true">
          {hotspots
            .slice()
            .sort((a, b) => (Number(a.z_order) || 0) - (Number(b.z_order) || 0))
            .map((spot, idx) => {
              const g = normalizeHotspotGeometry(spot.geometry);
              const z = Number(spot.z_order);
              const style: CSSProperties = {
                zIndex: 10 + (Number.isFinite(z) ? z : 0),
              };
              if (g?.kind === "circle") {
                const d = g.r * 2;
                Object.assign(style, {
                  left: `${g.cx - g.r}%`,
                  top: `${g.cy - g.r}%`,
                  width: `${d}%`,
                  height: `${d}%`,
                });
              } else if (g?.kind === "rect") {
                Object.assign(style, {
                  left: `${g.x}%`,
                  top: `${g.y}%`,
                  width: `${g.width}%`,
                  height: `${g.height}%`,
                });
              } else {
                return null;
              }
              return (
                <button
                  key={`${spot.part_id}-${idx}`}
                  type="button"
                  className={
                    "hotspot-btn" +
                    (g.kind === "circle" ? " circle" : "") +
                    (selected === spot.part_id ? " selected" : "")
                  }
                  style={style}
                  aria-label={`${spot.public_code}: ${spot.public_description}`}
                  onClick={() => setSelected(spot.part_id)}
                />
              );
            })}
        </div>
      </div>
      {h ? (
        <div className="card" style={{ marginTop: "1rem" }}>
          <span className={"badge " + (h.is_orderable ? "ok" : "no")}>
            {h.is_orderable ? "Orderable" : "Not orderable"}
          </span>
          <div style={{ fontWeight: 700, fontSize: "1.1rem", marginTop: "0.35rem" }}>
            {h.public_code}
          </div>
          <p style={{ margin: "0.35rem 0 0" }}>{h.public_description}</p>
        </div>
      ) : (
        <p className="muted" style={{ marginTop: "0.75rem" }}>
          Click a region on the diagram to see part details.
        </p>
      )}
    </div>
  );
}
