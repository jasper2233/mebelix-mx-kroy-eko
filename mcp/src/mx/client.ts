/** MebeliX Kroy REST mijozi (fetch). Hamma yo'llar `/api/...` ga nisbatan. */
import fs from "node:fs/promises";
import path from "node:path";

export class MxError extends Error {
  constructor(public status: number, public url: string, public body: string) {
    super(`MX ${status} ${url}: ${body.slice(0, 500)}`);
  }
}

export interface MxClientOptions { baseUrl: string; token?: string; timeoutMs?: number }

export class MxClient {
  constructor(private opt: MxClientOptions) {}

  get baseUrl(): string { return this.opt.baseUrl; }

  private headers(extra: Record<string, string> = {}): Record<string, string> {
    const h: Record<string, string> = { ...extra };
    if (this.opt.token) h["Authorization"] = `Bearer ${this.opt.token}`;
    return h;
  }

  private async req(method: string, p: string, init: { body?: BodyInit; headers?: Record<string, string>; query?: Record<string, unknown> } = {}): Promise<Response> {
    const url = new URL(this.opt.baseUrl + "/api" + p);
    for (const [k, v] of Object.entries(init.query || {})) {
      if (v === undefined || v === null || v === "") continue;
      url.searchParams.set(k, String(v));
    }
    const ac = new AbortController();
    const t = setTimeout(() => ac.abort(), this.opt.timeoutMs ?? 600_000);
    try {
      const r = await fetch(url, { method, body: init.body, headers: this.headers(init.headers), signal: ac.signal });
      if (!r.ok) throw new MxError(r.status, url.pathname, await r.text());
      return r;
    } finally { clearTimeout(t); }
  }

  async get<T = unknown>(p: string, query?: Record<string, unknown>): Promise<T> {
    return (await this.req("GET", p, { query })).json() as Promise<T>;
  }
  async getText(p: string, query?: Record<string, unknown>): Promise<string> {
    return (await this.req("GET", p, { query })).text();
  }
  async getBytes(p: string, query?: Record<string, unknown>): Promise<{ bytes: Uint8Array; type: string; filename: string }> {
    const r = await this.req("GET", p, { query });
    const cd = r.headers.get("content-disposition") || "";
    const m = /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i.exec(cd);
    const filename = decodeURIComponent(m?.[1] || m?.[2] || path.basename(p));
    return { bytes: new Uint8Array(await r.arrayBuffer()), type: r.headers.get("content-type") || "", filename };
  }
  async send<T = unknown>(method: "POST" | "PUT" | "PATCH" | "DELETE", p: string, body?: unknown, query?: Record<string, unknown>): Promise<T> {
    const r = await this.req(method, p, {
      body: body === undefined ? undefined : JSON.stringify(body),
      headers: body === undefined ? {} : { "Content-Type": "application/json" }, query,
    });
    const txt = await r.text();
    return (txt ? JSON.parse(txt) : null) as T;
  }
  post<T = unknown>(p: string, body?: unknown, query?: Record<string, unknown>) { return this.send<T>("POST", p, body, query); }
  put<T = unknown>(p: string, body?: unknown, query?: Record<string, unknown>) { return this.send<T>("PUT", p, body, query); }
  patch<T = unknown>(p: string, body?: unknown, query?: Record<string, unknown>) { return this.send<T>("PATCH", p, body, query); }
  del<T = unknown>(p: string, query?: Record<string, unknown>) { return this.send<T>("DELETE", p, undefined, query); }

  /** multipart fayl yuborish (import). */
  async upload<T = unknown>(p: string, filePath: string, field = "file", extra: Record<string, string> = {}, query?: Record<string, unknown>): Promise<T> {
    const data = await fs.readFile(filePath);
    const fd = new FormData();
    fd.set(field, new Blob([data]), path.basename(filePath));
    for (const [k, v] of Object.entries(extra)) fd.set(k, v);
    const r = await this.req("POST", p, { body: fd, query });
    return r.json() as Promise<T>;
  }
}
