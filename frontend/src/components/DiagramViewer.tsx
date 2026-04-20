import { useEffect, useState, type CSSProperties } from "react";
import type { HotspotPublic } from "@/api/types";
import { apiUrl } from "@/api/client";

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
            .sort((a, b) => a.z_order - b.z_order)
            .map((spot) => {
              const g = spot.geometry as {
                type?: string;
                x?: number;
                y?: number;
                width?: number;
                height?: number;
                cx?: number;
                cy?: number;
                r?: number;
              };
              const style: CSSProperties = {
                zIndex: 10 + spot.z_order,
              };
              if (g.type === "circle" && typeof g.cx === "number" && typeof g.r === "number") {
                const d = g.r * 2;
                Object.assign(style, {
                  left: `${g.cx - g.r}%`,
                  top: `${g.cy - g.r}%`,
                  width: `${d}%`,
                  height: `${d}%`,
                });
              } else if (
                g.type === "rect" &&
                typeof g.x === "number" &&
                typeof g.y === "number"
              ) {
                Object.assign(style, {
                  left: `${g.x}%`,
                  top: `${g.y}%`,
                  width: `${g.width ?? 0}%`,
                  height: `${g.height ?? 0}%`,
                });
              } else {
                return null;
              }
              return (
                <button
                  key={`${spot.part_id}-${spot.z_order}`}
                  type="button"
                  className={
                    "hotspot-btn" +
                    (g.type === "circle" ? " circle" : "") +
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
