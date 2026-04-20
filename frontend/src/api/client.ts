/** Base for API paths. Empty = same origin (Vite dev proxy to FastAPI). */
export function apiOrigin(): string {
  const o = import.meta.env.VITE_API_BASE_URL;
  if (o === undefined || o === "") return "";
  return o.replace(/\/$/, "");
}

/** Absolute URL for API paths like `/api/v1/...` */
export function apiUrl(path: string): string {
  const origin = apiOrigin();
  if (!origin) return path;
  return `${origin}${path.startsWith("/") ? "" : "/"}${path}`;
}

const TOKEN_KEY = "shade_catalog_admin_token";

export function getAdminToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAdminToken(token: string | null): void {
  if (token === null || token === "") localStorage.removeItem(TOKEN_KEY);
  else localStorage.setItem(TOKEN_KEY, token);
}

export type ApiError = { detail: string | string[] | Record<string, unknown> };

export async function apiFetch(
  path: string,
  init: RequestInit & { admin?: boolean } = {},
): Promise<Response> {
  const { admin, ...rest } = init;
  const headers = new Headers(rest.headers);
  if (admin) {
    const t = getAdminToken();
    if (t) headers.set("Authorization", `Bearer ${t}`);
  }
  return fetch(apiUrl(path), { ...rest, headers });
}

export async function readError(res: Response): Promise<string> {
  try {
    const j = (await res.json()) as ApiError;
    if (typeof j.detail === "string") return j.detail;
    return JSON.stringify(j.detail ?? j);
  } catch {
    return res.statusText || String(res.status);
  }
}
