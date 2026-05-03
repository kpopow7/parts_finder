import { useCallback, useEffect, useState } from "react";
import { apiFetch, readError } from "@/api/client";
import type { PartListItem } from "@/api/types";
import {
  applyDraftToWizard,
  emptyBom,
  emptyHotspot,
  makeInitialWizardState,
  recomputeDisplays,
  stateToDraftPayload,
  type BomRow,
  type HotspotRow,
  type PublishWizardState,
  stateToPublishRequest,
  validateDraftSaveFromWizard,
  validatePublishState,
} from "./publishModel";
import type { ProductDraftDocument } from "@/api/types";

const STEPS = [
  "Search & notes",
  "Bill of materials",
  "Part labels (en)",
  "Diagram",
  "Hotspots",
  "Review & publish",
] as const;

type Props = {
  productId: string;
  /** Latest draft payload from GET draft (for “Load from draft”). */
  draftPayload: Record<string, unknown> | null;
  onPublished?: (version: number) => void;
  /** After PUT draft from wizard; keeps JSON editor and draftPayload in sync. */
  onDraftSaved?: (doc: ProductDraftDocument) => void;
};

export function PublishWizard({ productId, draftPayload, onPublished, onDraftSaved }: Props) {
  const [state, setState] = useState<PublishWizardState>(makeInitialWizardState);
  const [step, setStep] = useState(0);
  const [parts, setParts] = useState<PartListItem[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [localErrs, setLocalErrs] = useState<string[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [savingDraft, setSavingDraft] = useState(false);

  const loadParts = useCallback(async () => {
    const res = await apiFetch("/api/v1/admin/parts?limit=500", { admin: true });
    if (res.ok) setParts(await res.json());
  }, []);

  useEffect(() => {
    loadParts();
  }, [loadParts]);

  const loadFromDraft = () => {
    if (!draftPayload) {
      setErr("No draft loaded yet. Save a draft or open this page after draft loads.");
      return;
    }
    setState(applyDraftToWizard(draftPayload));
    setErr(null);
    setMsg("Wizard filled from current draft.");
    setStep(0);
  };

  const resetWizard = () => {
    setState(makeInitialWizardState());
    setErr(null);
    setMsg(null);
    setStep(0);
  };

  const updateBom = (rows: BomRow[]) => {
    setState((prev) => {
      const displays = recomputeDisplays(rows, prev);
      return { ...prev, bom: rows, displays };
    });
  };

  const saveDraftFromWizard = async () => {
    setErr(null);
    setMsg(null);
    const dv = validateDraftSaveFromWizard(state);
    if (dv.length) {
      setErr(dv.join(" "));
      return;
    }
    setSavingDraft(true);
    const body = stateToDraftPayload(state, draftPayload ?? undefined);
    const res = await apiFetch(
      "/api/v1/admin/products/" + encodeURIComponent(productId) + "/draft",
      {
        method: "PUT",
        admin: true,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    setSavingDraft(false);
    if (!res.ok) {
      setErr(await readError(res));
      return;
    }
    const doc = (await res.json()) as ProductDraftDocument;
    setMsg("Draft saved (includes hotspots).");
    onDraftSaved?.(doc);
  };

  const publish = async () => {
    setErr(null);
    setMsg(null);
    const v = validatePublishState(state);
    if (v.length) {
      setLocalErrs(v);
      return;
    }
    setLocalErrs([]);
    setPublishing(true);
    const body = stateToPublishRequest(state);
    const res = await apiFetch(
      "/api/v1/admin/products/" + encodeURIComponent(productId) + "/publish",
      {
        method: "POST",
        admin: true,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    setPublishing(false);
    if (!res.ok) {
      setErr(await readError(res));
      return;
    }
    const out = (await res.json()) as { version: number };
    setMsg("Published successfully.");
    onPublished?.(out.version);
  };

  return (
    <div className="card publish-wizard">
      <h2>Publish wizard</h2>
      <p className="muted" style={{ fontSize: "0.88rem" }}>
        Step through BOM, one public label per part (locale <code>en</code>), optional diagram and
        hotspots. Use <strong>Save draft (wizard)</strong> to persist hotspots to the draft after
        it already exists, then publish when ready.
      </p>

      <div className="wizard-toolbar">
        <button type="button" className="btn" onClick={loadFromDraft} disabled={!draftPayload}>
          Load from current draft
        </button>
        <button
          type="button"
          className="btn btn-primary"
          disabled={savingDraft}
          onClick={saveDraftFromWizard}
        >
          {savingDraft ? "Saving draft…" : "Save draft (wizard)"}
        </button>
        <button type="button" className="btn" onClick={resetWizard}>
          Clear wizard
        </button>
      </div>

      {err ? <p className="error">{err}</p> : null}
      {msg ? <p style={{ color: "var(--accent)" }}>{msg}</p> : null}

      <div className="wizard-steps" role="tablist" aria-label="Steps">
        {STEPS.map((label, i) => (
          <button
            key={label}
            type="button"
            className={"wizard-step" + (i === step ? " active" : "")}
            onClick={() => setStep(i)}
          >
            {i + 1}. {label}
          </button>
        ))}
      </div>

      {localErrs.length > 0 && step === STEPS.length - 1 ? (
        <ul className="wizard-errors">
          {localErrs.map((e) => (
            <li key={e}>{e}</li>
          ))}
        </ul>
      ) : null}

      {step === 0 && (
        <section className="wizard-panel">
          <h3>Search & notes</h3>
          <div className="field">
            <label>Search blob (optional, full-text)</label>
            <textarea
              value={state.search_blob}
              onChange={(e) => setState((s) => ({ ...s, search_blob: e.target.value }))}
              rows={3}
              style={{ width: "100%", maxWidth: "100%" }}
            />
          </div>
          <div className="field">
            <label>Publish notes (optional)</label>
            <textarea
              value={state.publish_notes}
              onChange={(e) => setState((s) => ({ ...s, publish_notes: e.target.value }))}
              rows={2}
              style={{ width: "100%", maxWidth: "100%" }}
            />
          </div>
        </section>
      )}

      {step === 1 && (
        <BomStep
          bom={state.bom}
          parts={parts}
          onChange={updateBom}
        />
      )}

      {step === 2 && (
        <section className="wizard-panel">
          <h3>Part labels (locale en)</h3>
          <p className="muted" style={{ fontSize: "0.85rem" }}>
            One row per BOM part. Code and description are required.
          </p>
          <table className="data" style={{ marginTop: "0.5rem" }}>
            <thead>
              <tr>
                <th>Part id</th>
                <th>Public code</th>
                <th>Public description</th>
                <th>Orderable</th>
              </tr>
            </thead>
            <tbody>
              {state.displays.map((d, i) => (
                <tr key={d.part_id + "-" + String(i)}>
                  <td style={{ fontSize: "0.75rem", wordBreak: "break-all" }}>{d.part_id}</td>
                  <td>
                    <input
                      value={d.public_code}
                      onChange={(e) => {
                        const v = e.target.value;
                        setState((s) => {
                          const next = s.displays.slice();
                          if (next[i]) next[i] = { ...next[i], public_code: v };
                          return { ...s, displays: next };
                        });
                      }}
                    />
                  </td>
                  <td>
                    <input
                      value={d.public_description}
                      onChange={(e) => {
                        const v = e.target.value;
                        setState((s) => {
                          const next = s.displays.slice();
                          if (next[i]) next[i] = { ...next[i], public_description: v };
                          return { ...s, displays: next };
                        });
                      }}
                    />
                  </td>
                  <td>
                    <input
                      type="checkbox"
                      checked={d.is_orderable}
                      onChange={(e) => {
                        const v = e.target.checked;
                        setState((s) => {
                          const next = s.displays.slice();
                          if (next[i]) next[i] = { ...next[i], is_orderable: v };
                          return { ...s, displays: next };
                        });
                      }}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {step === 3 && (
        <section className="wizard-panel">
          <h3>Diagram (optional)</h3>
          <div className="field">
            <label>
              <input
                type="checkbox"
                checked={state.use_diagram}
                onChange={(e) => setState((s) => ({ ...s, use_diagram: e.target.checked }))}
              />{" "}
              Include diagram
            </label>
          </div>
          {state.use_diagram ? (
            <>
              <div className="field">
                <label>SVG storage key (required) — from Uploads</label>
                <input
                  value={state.svg_storage_key}
                  onChange={(e) => setState((s) => ({ ...s, svg_storage_key: e.target.value }))}
                  placeholder="svg/…"
                />
              </div>
              <div className="field">
                <label>Raster fallback storage key (optional)</label>
                <input
                  value={state.raster_fallback_storage_key}
                  onChange={(e) =>
                    setState((s) => ({ ...s, raster_fallback_storage_key: e.target.value }))
                  }
                />
              </div>
              <div className="field">
                <label>Title</label>
                <input
                  value={state.diagram_title}
                  onChange={(e) => setState((s) => ({ ...s, diagram_title: e.target.value }))}
                />
              </div>
              <div className="field">
                <label>Alt / summary</label>
                <textarea
                  value={state.alt_summary}
                  onChange={(e) => setState((s) => ({ ...s, alt_summary: e.target.value }))}
                  rows={2}
                  style={{ width: "100%" }}
                />
              </div>
            </>
          ) : null}
        </section>
      )}

      {step === 4 && (
        <HotspotsStep
          hotspots={state.hotspots}
          bomPartIds={state.bom.map((b) => b.part_id.trim()).filter(Boolean)}
          onChange={(hotspots) => setState((s) => ({ ...s, hotspots }))}
        />
      )}

      {step === 5 && (
        <section className="wizard-panel">
          <h3>Review</h3>
          <p className="muted" style={{ fontSize: "0.85rem" }}>
            Hotspots to publish:{" "}
            {
              state.hotspots.filter(
                (h) =>
                  h.part_id.trim().length > 0 &&
                  state.bom.some((b) => b.part_id.trim() === h.part_id.trim()),
              ).length
            }
          </p>
          <pre className="wizard-preview">{JSON.stringify(stateToPublishRequest(state), null, 2)}</pre>
          <button
            type="button"
            className="btn btn-primary"
            disabled={publishing}
            onClick={publish}
          >
            {publishing ? "Publishing…" : "Publish snapshot"}
          </button>
        </section>
      )}

      <div className="wizard-nav">
        <button
          type="button"
          className="btn"
          disabled={step === 0}
          onClick={() => setStep((s) => Math.max(0, s - 1))}
        >
          Back
        </button>
        <button
          type="button"
          className="btn btn-primary"
          disabled={step >= STEPS.length - 1}
          onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))}
        >
            Next
        </button>
      </div>
    </div>
  );
}

function BomStep({
  bom,
  parts,
  onChange,
}: {
  bom: BomRow[];
  parts: PartListItem[] | null;
  onChange: (rows: BomRow[]) => void;
}) {
  return (
    <section className="wizard-panel">
      <h3>Bill of materials</h3>
      <p className="muted" style={{ fontSize: "0.85rem" }}>
        Add lines and choose a part. Quantities must be greater than 0.
      </p>
      <table className="data" style={{ marginTop: "0.75rem" }}>
        <thead>
          <tr>
            <th>Part</th>
            <th>Qty</th>
            <th>Sort</th>
            <th>Group</th>
            <th>On diagram</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {bom.map((row, i) => (
            <tr key={i}>
              <td>
                {parts && parts.length ? (
                  <select
                    value={row.part_id}
                    onChange={(e) => {
                      const v = e.target.value;
                      const next = bom.slice();
                      if (next[i]) next[i] = { ...next[i], part_id: v };
                      onChange(next);
                    }}
                    style={{ maxWidth: "240px" }}
                  >
                    <option value="">— Select part —</option>
                    {parts.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.internal_part_number} ({p.id.slice(0, 8)}…)
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    value={row.part_id}
                    onChange={(e) => {
                      const v = e.target.value;
                      const next = bom.slice();
                      if (next[i]) next[i] = { ...next[i], part_id: v };
                      onChange(next);
                    }}
                    placeholder="Part UUID"
                    style={{ width: "100%", maxWidth: "280px" }}
                  />
                )}
              </td>
              <td>
                <input
                  value={row.quantity}
                  onChange={(e) => {
                    const v = e.target.value;
                    const next = bom.slice();
                    if (next[i]) next[i] = { ...next[i], quantity: v };
                    onChange(next);
                  }}
                  style={{ width: "4rem" }}
                />
              </td>
              <td>
                <input
                  value={row.sort_order}
                  onChange={(e) => {
                    const v = e.target.value;
                    const next = bom.slice();
                    if (next[i]) next[i] = { ...next[i], sort_order: v };
                    onChange(next);
                  }}
                  style={{ width: "3.5rem" }}
                />
              </td>
              <td>
                <input
                  value={row.bom_group}
                  onChange={(e) => {
                    const v = e.target.value;
                    const next = bom.slice();
                    if (next[i]) next[i] = { ...next[i], bom_group: v };
                    onChange(next);
                  }}
                  style={{ maxWidth: "7rem" }}
                />
              </td>
              <td>
                <input
                  type="checkbox"
                  checked={row.show_on_diagram}
                  onChange={(e) => {
                    const v = e.target.checked;
                    const next = bom.slice();
                    if (next[i]) next[i] = { ...next[i], show_on_diagram: v };
                    onChange(next);
                  }}
                />
              </td>
              <td>
                <button
                  type="button"
                  className="btn"
                  onClick={() => {
                    onChange(bom.filter((_, j) => j !== i));
                  }}
                >
                  Remove
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button
        type="button"
        className="btn"
        style={{ marginTop: "0.75rem" }}
        onClick={() => onChange([...bom, emptyBom()])}
      >
        + Add BOM line
      </button>
    </section>
  );
}

function HotspotsStep({
  hotspots,
  bomPartIds,
  onChange,
}: {
  hotspots: HotspotRow[];
  bomPartIds: string[];
  onChange: (h: HotspotRow[]) => void;
}) {
  return (
    <section className="wizard-panel">
      <h3>Hotspots (optional)</h3>
      <p className="muted" style={{ fontSize: "0.85rem" }}>
        Each hotspot must use a part from the BOM. Use percentages 0–100 for layout boxes.
      </p>
      {hotspots.map((h, i) => (
        <div key={i} className="card" style={{ marginTop: "0.75rem" }}>
          <div className="field">
            <label>Part</label>
            <select
              value={h.part_id}
              onChange={(e) => {
                const v = e.target.value;
                const next = hotspots.slice();
                if (next[i]) next[i] = { ...next[i], part_id: v };
                onChange(next);
              }}
            >
              <option value="">—</option>
              {bomPartIds.map((id) => (
                <option key={id} value={id}>
                  {id.slice(0, 8)}…
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>z-index order</label>
            <input
              value={h.z_order}
              onChange={(e) => {
                const v = e.target.value;
                const next = hotspots.slice();
                if (next[i]) next[i] = { ...next[i], z_order: v };
                onChange(next);
              }}
            />
          </div>
          <div className="field">
            <label>Shape</label>
            <select
              value={h.mode}
              onChange={(e) => {
                const v = e.target.value as HotspotRow["mode"];
                const next = hotspots.slice();
                if (next[i]) next[i] = { ...next[i], mode: v };
                onChange(next);
              }}
            >
              <option value="rect">Rectangle</option>
              <option value="circle">Circle</option>
              <option value="json">Custom JSON</option>
            </select>
          </div>
          {h.mode === "rect" && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.5rem" }}>
              {(["x", "y", "width", "height"] as const).map((k) => (
                <div className="field" key={k}>
                  <label>{k}</label>
                  <input
                    value={h.rect[k]}
                    onChange={(e) => {
                      const v = e.target.value;
                      const next = hotspots.slice();
                      if (next[i]) {
                        const row = { ...next[i]!, rect: { ...next[i]!.rect, [k]: v } };
                        next[i] = row;
                        onChange(next);
                      }
                    }}
                  />
                </div>
              ))}
            </div>
          )}
          {h.mode === "circle" && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.5rem" }}>
              {(["cx", "cy", "r"] as const).map((k) => (
                <div className="field" key={k}>
                  <label>{k}</label>
                  <input
                    value={h.circle[k]}
                    onChange={(e) => {
                      const v = e.target.value;
                      const next = hotspots.slice();
                      if (next[i]) {
                        const row = { ...next[i]!, circle: { ...next[i]!.circle, [k]: v } };
                        next[i] = row;
                        onChange(next);
                      }
                    }}
                  />
                </div>
              ))}
            </div>
          )}
          {h.mode === "json" && (
            <div className="field">
              <label>Geometry JSON</label>
              <textarea
                value={h.geometryJson}
                onChange={(e) => {
                  const v = e.target.value;
                  const next = hotspots.slice();
                  if (next[i]) next[i] = { ...next[i]!, geometryJson: v };
                  onChange(next);
                }}
                rows={4}
                style={{ width: "100%", fontFamily: "ui-monospace, monospace", fontSize: "0.8rem" }}
              />
            </div>
          )}
          <div className="field" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
            <div>
              <label>Label anchor x (optional)</label>
              <input
                value={h.label_x}
                onChange={(e) => {
                  const v = e.target.value;
                  const next = hotspots.slice();
                  if (next[i]) next[i] = { ...next[i]!, label_x: v };
                  onChange(next);
                }}
              />
            </div>
            <div>
              <label>Label anchor y (optional)</label>
              <input
                value={h.label_y}
                onChange={(e) => {
                  const v = e.target.value;
                  const next = hotspots.slice();
                  if (next[i]) next[i] = { ...next[i]!, label_y: v };
                  onChange(next);
                }}
              />
            </div>
          </div>
          <button
            type="button"
            className="btn"
            onClick={() => onChange(hotspots.filter((_, j) => j !== i))}
          >
            Remove hotspot
          </button>
        </div>
      ))}
      <button
        type="button"
        className="btn"
        style={{ marginTop: "0.75rem" }}
        onClick={() => onChange([...hotspots, emptyHotspot()])}
      >
        + Add hotspot
      </button>
    </section>
  );
}
