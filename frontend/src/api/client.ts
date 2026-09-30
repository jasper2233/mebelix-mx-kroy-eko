// REST mijoz: JSON, xatolar, JWT (MES SSO) tokeni, fayl yuklab olish.

export class ApiError extends Error {
  status: number;
  details: string[];
  constructor(status: number, message: string, details: string[] = []) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

const TOKEN_KEY = "mxk_token";

function readToken(): string | null {
  try {
    const u = new URL(window.location.href);
    const t = u.searchParams.get("token");
    if (t) {
      localStorage.setItem(TOKEN_KEY, t);
      u.searchParams.delete("token");
      window.history.replaceState(null, "", u.toString());
      return t;
    }
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

let token: string | null = typeof window !== "undefined" ? readToken() : null;

export function setToken(t: string | null) {
  token = t;
  try {
    if (t) localStorage.setItem(TOKEN_KEY, t);
    else localStorage.removeItem(TOKEN_KEY);
  } catch { /* brauzer xotirasi yopiq */ }
}

function uiLang(): string {
  try { return JSON.parse(localStorage.getItem("mxk_lang") ?? '"ru"') as string; } catch { return "ru"; }
}

function headers(extra?: Record<string, string>): Record<string, string> {
  const h: Record<string, string> = { "Accept-Language": uiLang(), ...(extra ?? {}) };
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

async function parseError(r: Response): Promise<ApiError> {
  let msg = `${r.status} ${r.statusText}`;
  let details: string[] = [];
  try {
    const j = await r.json();
    if (typeof j.detail === "string") msg = j.detail;
    else if (Array.isArray(j.detail)) msg = j.detail.map((d: { msg?: string; loc?: unknown[] }) =>
      `${(d.loc ?? []).slice(1).join(".")}: ${d.msg ?? ""}`).join("; ");
    if (Array.isArray(j.details)) details = j.details;
  } catch { /* matn emas */ }
  return new ApiError(r.status, msg, details);
}

export async function api<T = unknown>(path: string, opts: { method?: string; body?: unknown; form?: FormData;
  query?: Record<string, string | number | boolean | null | undefined> } = {}): Promise<T> {
  let url = `/api${path}`;
  if (opts.query) {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(opts.query)) if (v !== undefined && v !== null && v !== "") q.set(k, String(v));
    const s = q.toString();
    if (s) url += (url.includes("?") ? "&" : "?") + s;
  }
  const init: RequestInit = { method: opts.method ?? (opts.body !== undefined || opts.form ? "POST" : "GET") };
  if (opts.form) {
    init.body = opts.form;
    init.headers = headers();
  } else if (opts.body !== undefined) {
    init.body = JSON.stringify(opts.body);
    init.headers = headers({ "Content-Type": "application/json" });
  } else {
    init.headers = headers();
  }
  const r = await fetch(url, init);
  if (!r.ok) throw await parseError(r);
  const ct = r.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) return (await r.json()) as T;
  return (await r.text()) as unknown as T;
}

export const get = <T,>(path: string, query?: Record<string, string | number | boolean | null | undefined>) =>
  api<T>(path, { query });
export const post = <T,>(path: string, body?: unknown, query?: Record<string, string | number | boolean | null | undefined>) =>
  api<T>(path, { method: "POST", body: body ?? {}, query });
export const put = <T,>(path: string, body: unknown) => api<T>(path, { method: "PUT", body });
export const patch = <T,>(path: string, body: unknown) => api<T>(path, { method: "PATCH", body });
export const del = <T,>(path: string, query?: Record<string, string | number | boolean | null | undefined>) =>
  api<T>(path, { method: "DELETE", query });

/** Faylni yuklab olish (postprotsessor, eksport) — token bilan. */
export async function download(path: string, query?: Record<string, string | number | undefined>, fallbackName = "file") {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(query ?? {})) if (v !== undefined && v !== "") q.set(k, String(v));
  const r = await fetch(`/api${path}${q.toString() ? "?" + q : ""}`, { headers: headers() });
  if (!r.ok) throw await parseError(r);
  const cd = r.headers.get("content-disposition") ?? "";
  let name = fallbackName;
  const m1 = /filename\*=UTF-8''([^;]+)/i.exec(cd);
  const m2 = /filename="?([^";]+)"?/i.exec(cd);
  if (m1) name = decodeURIComponent(m1[1]);
  else if (m2) name = m2[1];
  const blob = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}

/** HTML hisobotni token bilan olib, yangi oynada ochish (chop etish uchun). */
/** Hisobot/etiketka HTML ini yangi oynada ko'rsatish: blob-URL orqali (document.write emas), sahifadagi CSP skriptlarni taqiqlaydi. */
export function showHtml(html: string, win?: Window | null) {
  const url = URL.createObjectURL(new Blob([html], { type: "text/html;charset=utf-8" }));
  if (win) win.location.href = url;
  else window.open(url, "_blank");
  setTimeout(() => URL.revokeObjectURL(url), 120_000);
}

export async function openHtml(path: string, query?: Record<string, string | number | undefined>, body?: unknown) {
  const w = window.open("", "_blank");
  try {
    showHtml(await fetchHtml(path, query, body), w);
  } catch (e) {
    w?.close();
    throw e;
  }
}

export async function fetchHtml(path: string, query?: Record<string, string | number | undefined>, body?: unknown) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(query ?? {})) if (v !== undefined && v !== "") q.set(k, String(v));
  const r = await fetch(`/api${path}${q.toString() ? "?" + q : ""}`, body ? {
    method: "POST", headers: headers({ "Content-Type": "application/json" }), body: JSON.stringify(body),
  } : { headers: headers() });
  if (!r.ok) throw await parseError(r);
  return r.text();
}
