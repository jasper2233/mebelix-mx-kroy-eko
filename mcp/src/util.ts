/** Umumiy yordamchilar: natija matni, jadval, fayl saqlash. */
import fs from "node:fs/promises";
import path from "node:path";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

export type ToolResult = CallToolResult;

export function text(s: string): ToolResult { return { content: [{ type: "text", text: s }] }; }
export function json(v: unknown): ToolResult { return text(JSON.stringify(v, null, 1)); }
export function fail(msg: string): ToolResult { return { content: [{ type: "text", text: msg }], isError: true }; }

/** Markdown jadval. */
export function table(headers: string[], rows: Array<Array<unknown>>): string {
  const cell = (v: unknown) => (v === null || v === undefined ? "" : typeof v === "number" ? fmt(v) : String(v)).replace(/\|/g, "\\|");
  const lines = ["| " + headers.join(" | ") + " |", "|" + headers.map(() => "---").join("|") + "|"];
  for (const r of rows) lines.push("| " + r.map(cell).join(" | ") + " |");
  return lines.join("\n");
}

export function fmt(v: number, digits = 2): string {
  if (Number.isInteger(v)) return String(v);
  return v.toFixed(digits).replace(/\.?0+$/, "");
}

export async function ensureDir(dir: string): Promise<string> {
  await fs.mkdir(dir, { recursive: true });
  return dir;
}

/** Fayl nomini xavfsiz qilish (yo'l ajratgichlari va boshqaruv belgilari olib tashlanadi). */
export function safeName(name: string, fallback = "file"): string {
  const s = name.replace(/[\\/:*?"<>|\u0000-\u001f]+/g, "_").trim();
  return s || fallback;
}

export async function saveBytes(outDir: string, filename: string, data: Uint8Array | string): Promise<string> {
  await ensureDir(outDir);
  const p = path.join(outDir, safeName(filename));
  await fs.writeFile(p, data);
  return p;
}

/** Oddiy fon vazifalari ro'yxati (uzoq kroylar uchun — mijoz vaqt chegarasidan qo'rqmasdan). */
export interface Job { id: string; name: string; started: number; finished?: number; status: "running" | "done" | "error"; result?: unknown; error?: string; progress: string[] }
const jobs = new Map<string, Job>();
let jobSeq = 0;

export function startJob(name: string, run: (log: (s: string) => void) => Promise<unknown>): Job {
  const job: Job = { id: `job-${++jobSeq}-${Date.now().toString(36)}`, name, started: Date.now(), status: "running", progress: [] };
  jobs.set(job.id, job);
  run((s) => job.progress.push(s)).then(
    (r) => { job.status = "done"; job.result = r; job.finished = Date.now(); },
    (e) => { job.status = "error"; job.error = String(e?.message || e); job.finished = Date.now(); });
  return job;
}
export function getJob(id: string): Job | undefined { return jobs.get(id); }
export function listJobs(): Job[] { return [...jobs.values()].sort((a, b) => b.started - a.started); }

export function pct(a: number, b: number): string { return b ? fmt((a / b) * 100, 2) + "%" : "—"; }
export function round(v: number, d = 3): number { const k = 10 ** d; return Math.round(v * k) / k; }
