import { useEffect, useState } from "react";
import { apiFetch, readError } from "@/api/client";
import type { PartListItem } from "@/api/types";

export function AdminParts() {
  const [rows, setRows] = useState<PartListItem[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [num, setNum] = useState("");
  const [desc, setDesc] = useState("");
  const [imageId, setImageId] = useState("");
  const [patchPart, setPatchPart] = useState("");
  const [patchImage, setPatchImage] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  async function refresh() {
    const res = await apiFetch("/api/v1/admin/parts?limit=500", { admin: true });
    if (!res.ok) {
      setErr(await readError(res));
      return;
    }
    setRows(await res.json());
    setErr(null);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function createPart(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    const body: Record<string, unknown> = {
      internal_part_number: num.trim(),
      internal_description: desc.trim() || null,
    };
    if (imageId.trim()) body.image_uploaded_asset_id = imageId.trim();
    const res = await apiFetch("/api/v1/admin/parts", {
      method: "POST",
      admin: true,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      setErr(await readError(res));
      return;
    }
    setErr(null);
    setMsg("Part created.");
    setNum("");
    setDesc("");
    setImageId("");
    await refresh();
  }

  async function patchPartImage(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    const res = await apiFetch("/api/v1/admin/parts/" + encodeURIComponent(patchPart.trim()), {
      method: "PATCH",
      admin: true,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image_uploaded_asset_id: patchImage.trim() ? patchImage.trim() : null,
      }),
    });
    if (!res.ok) {
      setErr(await readError(res));
      return;
    }
    setErr(null);
    setMsg("Part image updated.");
    await refresh();
  }

  if (!rows) return <p className="muted">Loading…</p>;

  return (
    <div>
      <h1>Parts</h1>
      {err ? <p className="error">{err}</p> : null}
      {msg ? <p style={{ color: "var(--accent)" }}>{msg}</p> : null}

      <div className="card">
        <h2>Create part</h2>
        <form onSubmit={createPart}>
          <div className="field">
            <label>Internal part number</label>
            <input value={num} onChange={(e) => setNum(e.target.value)} required />
          </div>
          <div className="field">
            <label>Description (optional)</label>
            <input value={desc} onChange={(e) => setDesc(e.target.value)} />
          </div>
          <div className="field">
            <label>Part image asset id (optional)</label>
            <input value={imageId} onChange={(e) => setImageId(e.target.value)} placeholder="UUID" />
          </div>
          <button type="submit" className="btn btn-primary">
            Create
          </button>
        </form>
      </div>

      <div className="card">
        <h2>Set part photo (PATCH)</h2>
        <form onSubmit={patchPartImage}>
          <div className="field">
            <label>Part id</label>
            <input value={patchPart} onChange={(e) => setPatchPart(e.target.value)} required />
          </div>
          <div className="field">
            <label>Image uploaded asset id (empty = clear)</label>
            <input value={patchImage} onChange={(e) => setPatchImage(e.target.value)} />
          </div>
          <button type="submit" className="btn btn-primary">
            Update image
          </button>
        </form>
      </div>

      <h2>All parts</h2>
      <div style={{ overflowX: "auto" }}>
        <table className="data">
          <thead>
            <tr>
              <th>ID</th>
              <th>Number</th>
              <th>Description</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id}>
                <td style={{ fontSize: "0.75rem", wordBreak: "break-all" }}>{p.id}</td>
                <td>{p.internal_part_number}</td>
                <td>{p.internal_description ?? "—"}</td>
                <td>{p.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
