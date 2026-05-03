/**
 * Client-side model for the publish wizard. Maps to API `PublishSnapshotRequest`.
 */

export type BomRow = {
  part_id: string;
  quantity: string;
  sort_order: string;
  bom_group: string;
  show_on_diagram: boolean;
};

export type DisplayRow = {
  part_id: string;
  public_code: string;
  public_description: string;
  is_orderable: boolean;
};

export type HotspotRow = {
  part_id: string;
  z_order: string;
  mode: "rect" | "circle" | "json";
  rect: { x: string; y: string; width: string; height: string };
  circle: { cx: string; cy: string; r: string };
  geometryJson: string;
  label_x: string;
  label_y: string;
};

export type PublishWizardState = {
  publish_notes: string;
  search_blob: string;
  use_diagram: boolean;
  svg_storage_key: string;
  raster_fallback_storage_key: string;
  diagram_title: string;
  alt_summary: string;
  bom: BomRow[];
  displays: DisplayRow[];
  hotspots: HotspotRow[];
};

const emptyBom = (): BomRow => ({
  part_id: "",
  quantity: "1",
  sort_order: "0",
  bom_group: "",
  show_on_diagram: true,
});

const emptyHotspot = (): HotspotRow => ({
  part_id: "",
  z_order: "0",
  mode: "rect",
  rect: { x: "0", y: "0", width: "10", height: "10" },
  circle: { cx: "50", cy: "50", r: "5" },
  geometryJson: '{"type":"rect","x":0,"y":0,"width":10,"height":10}',
  label_x: "",
  label_y: "",
});

export function makeInitialWizardState(): PublishWizardState {
  return {
    publish_notes: "",
    search_blob: "",
    use_diagram: false,
    svg_storage_key: "",
    raster_fallback_storage_key: "",
    diagram_title: "",
    alt_summary: "",
    bom: [emptyBom()],
    displays: [],
    hotspots: [],
  };
}

function syncDisplaysFromBom(bom: BomRow[], prev: DisplayRow[]): DisplayRow[] {
  const byPart = new Map(prev.map((d) => [d.part_id, d]));
  return bom.map((b) => {
    const id = b.part_id.trim();
    if (!id) {
      return { part_id: "", public_code: "", public_description: "", is_orderable: true };
    }
    const old = byPart.get(id);
    if (old) return { ...old, part_id: id };
    return {
      part_id: id,
      public_code: "",
      public_description: "",
      is_orderable: true,
    };
  });
}

/** Apply draft payload (ProductDraftPayload shape) into wizard state. */
export function applyDraftToWizard(
  draft: Record<string, unknown> | null | undefined,
  base: PublishWizardState = makeInitialWizardState(),
): PublishWizardState {
  if (!draft || typeof draft !== "object") {
    return { ...base, displays: syncDisplaysFromBom(base.bom, base.displays) };
  }
  const next = { ...base, bom: base.bom.slice(), displays: base.displays.slice(), hotspots: base.hotspots.slice() };

  if (typeof draft.publish_notes === "string") next.publish_notes = draft.publish_notes;
  if (typeof draft.search_blob === "string") next.search_blob = draft.search_blob;

  const diagram = draft.diagram as Record<string, unknown> | null | undefined;
  if (diagram && typeof diagram === "object") {
    next.use_diagram = Boolean(diagram.svg_storage_key);
    if (typeof diagram.svg_storage_key === "string") next.svg_storage_key = diagram.svg_storage_key;
    if (typeof diagram.raster_fallback_storage_key === "string")
      next.raster_fallback_storage_key = diagram.raster_fallback_storage_key;
    if (typeof diagram.diagram_title === "string") next.diagram_title = diagram.diagram_title;
    if (typeof diagram.alt_summary === "string") next.alt_summary = diagram.alt_summary;
  }

  const rawBom = draft.bill_of_materials;
  if (Array.isArray(rawBom) && rawBom.length) {
    next.bom = rawBom.map((row) => {
      const r = row as Record<string, unknown>;
      return {
        part_id: String(r.part_id ?? ""),
        quantity: String(r.quantity ?? "1"),
        sort_order: String(r.sort_order ?? "0"),
        bom_group: r.bom_group != null ? String(r.bom_group) : "",
        show_on_diagram: r.show_on_diagram !== false,
      };
    });
  }

  const rawDisplays = draft.part_displays;
  if (Array.isArray(rawDisplays) && rawDisplays.length) {
    next.displays = rawDisplays.map((row) => {
      const r = row as Record<string, unknown>;
      return {
        part_id: String(r.part_id ?? ""),
        public_code: String(r.public_code ?? ""),
        public_description: String(r.public_description ?? ""),
        is_orderable: r.is_orderable !== false,
      };
    });
  } else {
    next.displays = syncDisplaysFromBom(next.bom, next.displays);
  }

  const rawH = draft.diagram_hotspots;
  if (Array.isArray(rawH) && rawH.length) {
    next.hotspots = rawH.map((row) => hotspotFromApi(row as Record<string, unknown>));
  }

  if (!next.displays.length) next.displays = syncDisplaysFromBom(next.bom, []);
  const orderedIds = next.bom.map((b) => b.part_id.trim()).filter(Boolean);
  if (orderedIds.length) {
    const dm = new Map(next.displays.map((d) => [d.part_id.trim(), d]));
    next.displays = orderedIds.map(
      (id) =>
        dm.get(id) ?? {
          part_id: id,
          public_code: "",
          public_description: "",
          is_orderable: true,
        },
    );
  }
  return next;
}

function hotspotFromApi(r: Record<string, unknown>): HotspotRow {
  const g = (r.geometry as Record<string, unknown> | undefined) ?? {};
  const t = String(g.type ?? "rect");
  const z = String(r.z_order ?? "0");
  const part_id = String(r.part_id ?? "");
  const la = r.label_anchor as Record<string, unknown> | null | undefined;
  const h: HotspotRow = {
    part_id,
    z_order: z,
    mode: t === "circle" ? "circle" : t === "rect" ? "rect" : "json",
    rect: {
      x: String(g.x ?? "0"),
      y: String(g.y ?? "0"),
      width: String(g.width ?? "10"),
      height: String(g.height ?? "10"),
    },
    circle: {
      cx: String(g.cx ?? "50"),
      cy: String(g.cy ?? "50"),
      r: String(g.r ?? "5"),
    },
    geometryJson: JSON.stringify(r.geometry && typeof r.geometry === "object" ? r.geometry : { type: "rect", x: 0, y: 0, width: 10, height: 10 }),
    label_x: la && typeof la.x === "number" ? String(la.x) : "",
    label_y: la && typeof la.y === "number" ? String(la.y) : "",
  };
  return h;
}

export { emptyBom, emptyHotspot, syncDisplaysFromBom };

/** One API-shaped hotspot (publish + draft). */
export function hotspotRowToApi(h: HotspotRow): {
  part_id: string;
  geometry: Record<string, unknown>;
  z_order: number;
  label_anchor: { x: number; y: number } | null;
} {
  let geometry: Record<string, unknown>;
  if (h.mode === "json") {
    try {
      geometry = JSON.parse(h.geometryJson) as Record<string, unknown>;
    } catch {
      geometry = { type: "rect", x: 0, y: 0, width: 10, height: 10 };
    }
  } else if (h.mode === "circle") {
    geometry = {
      type: "circle",
      cx: parseFloat(h.circle.cx) || 0,
      cy: parseFloat(h.circle.cy) || 0,
      r: parseFloat(h.circle.r) || 1,
    };
  } else {
    geometry = {
      type: "rect",
      x: parseFloat(h.rect.x) || 0,
      y: parseFloat(h.rect.y) || 0,
      width: parseFloat(h.rect.width) || 0,
      height: parseFloat(h.rect.height) || 0,
    };
  }
  const label_anchor: { x: number; y: number } | null =
    h.label_x.trim() && h.label_y.trim()
      ? { x: parseFloat(h.label_x) || 0, y: parseFloat(h.label_y) || 0 }
      : null;
  return {
    part_id: h.part_id.trim(),
    geometry,
    z_order: parseInt(h.z_order, 10) || 0,
    label_anchor,
  };
}

/** Hotspots for publish: only parts on the BOM. */
function hotspotsForPublish(s: PublishWizardState) {
  const part_set = new Set(s.bom.map((b) => b.part_id.trim()).filter(Boolean));
  return s.hotspots
    .filter((h) => h.part_id.trim() && part_set.has(h.part_id.trim()))
    .map(hotspotRowToApi);
}

/** Hotspots for draft save: any row with a part id (work-in-progress; BOM can be edited later). */
function hotspotsForDraft(s: PublishWizardState) {
  return s.hotspots.filter((h) => h.part_id.trim().length > 0).map(hotspotRowToApi);
}

/** Build `ProductDraftPayload`-shaped JSON; merges with existing draft to keep e.g. `spec_import_id`. */
export function stateToDraftPayload(
  s: PublishWizardState,
  mergeFrom: Record<string, unknown> | null | undefined,
): Record<string, unknown> {
  const out: Record<string, unknown> =
    mergeFrom && typeof mergeFrom === "object" ? { ...mergeFrom } : {};

  const bom = s.bom
    .filter((b) => b.part_id.trim())
    .map((b) => ({
      part_id: b.part_id.trim(),
      quantity: parseFloat(b.quantity) || 0,
      sort_order: parseInt(b.sort_order, 10) || 0,
      bom_group: b.bom_group.trim() || null,
      show_on_diagram: b.show_on_diagram,
    }));

  const part_displays = bom.map((b) => {
    const pid = b.part_id as string;
    const d = s.displays.find((x) => x.part_id.trim() === pid);
    return {
      part_id: pid,
      public_code: d?.public_code ?? "",
      public_description: d?.public_description ?? "",
      is_orderable: d?.is_orderable !== false,
      locale: "en",
    };
  });

  const diagram =
    s.use_diagram && s.svg_storage_key.trim()
      ? {
          svg_storage_key: s.svg_storage_key.trim(),
          raster_fallback_storage_key: s.raster_fallback_storage_key.trim() || null,
          diagram_title: s.diagram_title.trim() || null,
          alt_summary: s.alt_summary.trim() || null,
        }
      : null;

  out.publish_notes = s.publish_notes.trim() || null;
  out.search_blob = s.search_blob.trim() || null;
  out.diagram = diagram;
  out.bill_of_materials = bom;
  out.part_displays = part_displays;
  out.diagram_hotspots = hotspotsForDraft(s);
  return out;
}

/** Errors that block saving draft from wizard (lighter than publish). */
export function validateDraftSaveFromWizard(s: PublishWizardState): string[] {
  if (s.hotspots.length === 0) return [];
  const errors: string[] = [];
  for (const h of s.hotspots) {
    const pid = h.part_id.trim();
    if (!pid) {
      errors.push("Remove empty hotspot rows or select a part for each hotspot.");
    }
  }
  return errors;
}

export function validatePublishState(s: PublishWizardState): string[] {
  const errors: string[] = [];
  const bom = s.bom.filter((b) => b.part_id.trim().length);

  if (!bom.length) {
    errors.push("Add at least one BOM line with a part id.");
  }

  for (const b of bom) {
    const q = parseFloat(b.quantity);
    if (!(q > 0) || Number.isNaN(q)) {
      errors.push(`BOM quantity must be > 0 for part ${b.part_id.slice(0, 8)}…`);
    }
  }

  const partIds = new Set(bom.map((b) => b.part_id.trim()));
  for (const id of partIds) {
    const d = s.displays.find((x) => x.part_id.trim() === id);
    if (!d) {
      errors.push(`Missing part display for part ${id}.`);
      continue;
    }
    if (!d.public_code.trim() || !d.public_description.trim()) {
      errors.push(`Part display: code and description required for part ${id.slice(0, 8)}…`);
    }
  }

  if (s.displays.length) {
    const displayIds = s.displays.filter((d) => d.part_id.trim()).map((d) => d.part_id.trim());
    for (const id of displayIds) {
      if (!partIds.has(id)) errors.push(`Part display for ${id} is not in the BOM.`);
    }
  }

  if (s.use_diagram && !s.svg_storage_key.trim()) {
    errors.push("Diagram: svg storage key is required when diagram is included.");
  }

  for (const h of s.hotspots) {
    const pid = h.part_id.trim();
    if (!pid) {
        errors.push("Each hotspot row must select a part_id from the BOM.");
        continue;
    }
    if (!partIds.has(pid)) {
      errors.push(`Hotspot part ${h.part_id} must appear in the BOM.`);
    }
  }

  return errors;
}

/** Build `PublishSnapshotRequest` JSON for POST /publish */
export function stateToPublishRequest(s: PublishWizardState): Record<string, unknown> {
  const bom = s.bom
    .filter((b) => b.part_id.trim())
    .map((b) => ({
      part_id: b.part_id.trim(),
      quantity: parseFloat(b.quantity) || 1,
      sort_order: parseInt(b.sort_order, 10) || 0,
      bom_group: b.bom_group.trim() || null,
      show_on_diagram: b.show_on_diagram,
    }));

  const part_set = new Set(bom.map((b) => b.part_id as string));
  const part_displays = bom.map((b) => {
    const pid = b.part_id as string;
    const d = s.displays.find((x) => x.part_id.trim() === pid);
    return {
      part_id: pid,
      public_code: (d?.public_code ?? "").trim(),
      public_description: (d?.public_description ?? "").trim(),
      is_orderable: d?.is_orderable !== false,
      locale: "en",
    };
  });

  const diagram =
    s.use_diagram && s.svg_storage_key.trim()
      ? {
          svg_storage_key: s.svg_storage_key.trim(),
          raster_fallback_storage_key: s.raster_fallback_storage_key.trim() || null,
          diagram_title: s.diagram_title.trim() || null,
          alt_summary: s.alt_summary.trim() || null,
        }
      : null;

  const hotspots = hotspotsForPublish(s);

  return {
    publish_notes: s.publish_notes.trim() || null,
    search_blob: s.search_blob.trim() || null,
    diagram,
    bill_of_materials: bom,
    part_displays,
    diagram_hotspots: hotspots,
  };
}

/** After BOM edit — keep displays in sync. */
export function recomputeDisplays(
  bom: BomRow[],
  previous: PublishWizardState,
): DisplayRow[] {
  return syncDisplaysFromBom(bom, previous.displays);
}
