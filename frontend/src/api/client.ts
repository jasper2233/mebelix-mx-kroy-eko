// REST mijoz: JSON, xatolar, JWT (MES SSO) tokeni, fayl yuklab olish.
import i18n from "i18next";

export class ApiError extends Error {
  status: number;
  details: string[];
  code: string;                 // server belgisi (masalan «rotate_keep») — maxsus oyna uchun
  constructor(status: number, message: string, details: string[] = [], code = "") {
    super(message);
    this.status = status;
    this.details = details;
    this.code = code;
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

/** JWT tokeni bormi (chap paneldagi «Выйти» uchun). */
export function hasToken(): boolean { return !!token; }

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

/** Holat kodi bo'yicha foydalanuvchi tilidagi umumiy xabar (server matn bermaganda: proksi HTML sahifasi, bo'sh javob …). */
export function statusText(status: number): string {
  const k = status === 0 ? "network" : status === 401 ? "401" : status === 403 ? "403" : status === 404 ? "404"
    : status === 409 ? "409" : status === 413 ? "413" : status === 422 ? "422" : status === 429 ? "429"
    : status >= 500 ? "5xx" : "other";
  return i18n.t(`err.http.${k}`, { status });
}

/** 422 tafsiloti (`[{loc, msg}]`) → «maydon: sabab» qatorlari (server `message` bermagan eski javoblar uchun). */
function validationLines(detail: unknown[]): string[] {
  return detail.slice(0, 5).map((d) => {
    const o = (d ?? {}) as { msg?: unknown; loc?: unknown[] };
    const loc = (o.loc ?? []).filter((x) => x !== "body" && x !== "query" && x !== "path").join(".");
    const msg = typeof o.msg === "string" ? o.msg : "";
    return loc ? `${loc}: ${msg}` : msg;
  }).filter(Boolean);
}

async function parseError(r: Response): Promise<ApiError> {
  let msg = "";
  let details: string[] = [];
  let code = "";
  let raw = "";
  try { raw = await r.text(); } catch { /* tana o'qilmadi */ }
  try {
    const j = JSON.parse(raw) as { detail?: unknown; message?: unknown; messages?: unknown; details?: unknown };
    const d = j.detail;
    if (typeof d === "string") msg = d;
    else if (Array.isArray(d)) {
      // 422: server tilga mos qisqa `message` yuboradi; har maydon — alohida qator (xabarnomada ro'yxat)
      const human = Array.isArray(j.messages) ? j.messages.filter((x): x is string => typeof x === "string") : [];
      const lines = human.length ? human : validationLines(d);
      msg = typeof j.message === "string" && j.message ? j.message : lines.join("; ");
      if (lines.length > 1) details = lines;
    } else if (d && typeof d === "object") {
      const o = d as { message?: unknown; msg?: unknown };
      msg = typeof o.message === "string" ? o.message : typeof o.msg === "string" ? o.msg : "";
    } else if (typeof j.message === "string") msg = j.message;
    if (Array.isArray(j.details)) details = j.details.map(String);
    if (typeof (j as { code?: unknown }).code === "string") code = (j as { code: string }).code;
  } catch { /* JSON emas (proksi HTML / oddiy matn) — umumiy xabar */ }
  if (!msg) msg = statusText(r.status);
  if (msg.length > 600) msg = `${msg.slice(0, 600)}…`;            // xabarnoma cheksiz cho'zilmasin
  return new ApiError(r.status, msg, details, code);
}

/** Tarmoq xatosi (server ishlamayapti, aloqa uzildi): brauzerning inglizcha «Failed to fetch» o'rniga tushunarli xabar. */
async function send(url: string, init?: RequestInit): Promise<Response> {
  let r: Response;
  try {
    r = await fetch(url, init);
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") throw e;
    throw new ApiError(0, statusText(0));
  }
  if (r.status === 401) {                            // token yo'q / muddati o'tgan — kirish oynasi
    if (token) setToken(null);
    unauthorized.forEach((f) => f());
  }
  return r;
}

const unauthorized = new Set<() => void>();

/** Server 401 qaytarganda chaqiriladi (App kirish oynasini ko'rsatadi); obunani bekor qiluvchi funksiya qaytaradi. */
export function onUnauthorized(f: () => void): () => void {
  unauthorized.add(f);
  return () => { unauthorized.delete(f); };
}

/** Kirish oynasi: login/parol → JWT (saqlanadi). Xato bo'lsa ApiError. */
export async function login(username: string, password: string): Promise<void> {
  let r: Response;
  try {
    r = await fetch("/api/auth/login", { method: "POST", headers: headers({ "Content-Type": "application/json" }),
      body: JSON.stringify({ username, password }) });
  } catch {
    throw new ApiError(0, statusText(0));
  }
  if (!r.ok) throw await parseError(r);
  setToken(((await r.json()) as { token: string }).token);
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
  const r = await send(url, init);
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
  const r = await send(`/api${path}${q.toString() ? "?" + q : ""}`, { headers: headers() });
  await saveResponse(r, fallbackName);
  return r.headers;                                  // masalan «X-PP-Refit» (kroy stanokka moslab qayta bajarildi)
}

/** Faylni POST (JSON tanasi) bilan yuklab olish — masalan, bir nechta loyihani ZIP qilib eksport (W10). */
export async function downloadPost(path: string, body: unknown, fallbackName = "file") {
  const r = await send(`/api${path}`, { method: "POST", headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify(body) });
  await saveResponse(r, fallbackName);
}

async function saveResponse(r: Response, fallbackName: string) {
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

/** POST (JSON tanasi) → fayl (Blob), masalan hisobot PDF. 501 — server PDF yasay olmaydi (chaqiruvchi HTML ga qaytadi). */
export async function fetchBlob(path: string, query?: Record<string, string | number | undefined>, body?: unknown) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(query ?? {})) if (v !== undefined && v !== "") q.set(k, String(v));
  const r = await send(`/api${path}${q.toString() ? "?" + q : ""}`, body ? {
    method: "POST", headers: headers({ "Content-Type": "application/json" }), body: JSON.stringify(body),
  } : { headers: headers() });
  if (!r.ok) throw await parseError(r);
  return r.blob();
}

export async function fetchHtml(path: string, query?: Record<string, string | number | undefined>, body?: unknown) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(query ?? {})) if (v !== undefined && v !== "") q.set(k, String(v));
  const r = await send(`/api${path}${q.toString() ? "?" + q : ""}`, body ? {
    method: "POST", headers: headers({ "Content-Type": "application/json" }), body: JSON.stringify(body),
  } : { headers: headers() });
  if (!r.ok) throw await parseError(r);
  return r.text();
}
