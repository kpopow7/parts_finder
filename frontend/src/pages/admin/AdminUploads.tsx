import { useState } from "react";
import { apiFetch, readError } from "@/api/client";
import type { UploadAssetResponse } from "@/api/types";

export function AdminUploads() {
  const [file, setFile] = useState<File | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<UploadAssetResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setErr(null);
    setResult(null);
    setLoading(true);
    const fd = new FormData();
    fd.append("file", file);
    const res = await apiFetch("/api/v1/admin/uploads", {
      method: "POST",
      admin: true,
      body: fd,
    });
    setLoading(false);
    if (!res.ok) {
      setErr(await readError(res));
      return;
    }
    setResult((await res.json()) as UploadAssetResponse);
  }

  return (
    <div>
      <h1>Upload file</h1>
      <p className="muted">SVG, PDF, JPEG, or PNG. Use returned id for part images or storage_key for diagrams.</p>
      {err ? <p className="error">{err}</p> : null}
      <form onSubmit={onSubmit} className="card">
        <div className="field">
          <label>File</label>
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            accept=".svg,.pdf,.jpg,.jpeg,.png,image/*"
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={!file || loading}>
          {loading ? "Uploading…" : "Upload"}
        </button>
      </form>
      {result ? (
        <div className="card">
          <h2>Response</h2>
          <pre
            style={{
              background: "#f1f5f9",
              padding: "0.75rem",
              borderRadius: 8,
              overflow: "auto",
              fontSize: "0.85rem",
            }}
          >
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      ) : null}
    </div>
  );
}
