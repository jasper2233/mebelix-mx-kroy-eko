/**
 * `compare_*` vositalari — MebeliX Kroy natijasini (1) `.project` faylida saqlangan avvalgi tizim natijasi bilan,
 * (2) onlayn tizimdagi ochiq loyiha ko'rsatkichlari bilan solishtirish.
 */
import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { Config } from "../config.js";
import { MxClient, MxError } from "../mx/client.js";
import { cutOperations } from "../mx/tools.js";
import { resultSummary, type MxProject } from "../mx/summary.js";
import { fail, fmt, getJob, json, round, startJob, table, text, type ToolResult } from "../util.js";
import { projectFileSummary, readProjectFile, type FileOperation, type ProjectFile } from "./projectfile.js";
import type { GiblabDriver } from "../giblab/driver.js";

export interface CompareRow {
  op: string; type: string;
  parts_file: number | null; parts_mx: number | null; unplaced_mx: number;
  sheets_file: number | null; sheets_mx: number | null;
  fill_file: number | null; fill_mx: number | null;
  business_file: number | null; business_mx: number | null;
  cut_file: number | null; cut_mx: number | null;
  verdict: string; error?: string;
}

function verdict(r: Omit<CompareRow, "verdict">): string {
  if (r.error) return "xato";
  if (r.sheets_file === null) return "faylda natija yo'q";
  if (r.sheets_mx === null) return "MX natija yo'q";
  if (r.sheets_mx < r.sheets_file) return `MX yaxshi (−${r.sheets_file - r.sheets_mx} list)`;
  if (r.sheets_mx > r.sheets_file) return `MX yomon (+${r.sheets_mx - r.sheets_file} list)`;
  const df = (r.fill_mx ?? 0) - (r.fill_file ?? 0);
  const db = (r.business_mx ?? 0) - (r.business_file ?? 0);
  return `listlar teng; F ${df >= 0 ? "+" : ""}${fmt(df)} %, деловой ${db >= 0 ? "+" : ""}${fmt(db, 2)} m²`;
}

/** Fayl operatsiyalarini import qilingan loyiha operatsiyalari bilan tartib bo'yicha moslashtirish (CS/CL ketma-ketligi saqlanadi). */
export function matchOps(pf: ProjectFile, p: MxProject): Array<[FileOperation, MxProject["operations"][number] | undefined]> {
  const fileCut = pf.operations.filter((o) => o.type === "CS" || o.type === "CL");
  const mxCut = p.operations.filter((o) => o.type === "CS" || o.type === "CL");
  return fileCut.map((fo, i) => [fo, mxCut[i]]);
}

export async function compareProjectFile(mx: MxClient, filePath: string, opts: { quality: string; keep: boolean; folder_id?: string }, log: (s: string) => void) {
  const pf = await readProjectFile(filePath);
  log(`fayl o'qildi: ${pf.name}, ${JSON.stringify(pf.counts)}`);
  const imp = await mx.upload<{ project: MxProject; warnings: string[] }>("/projects/import-file", filePath, "file", {}, { folder_id: opts.folder_id });
  const p = imp.project ?? (imp as unknown as MxProject);
  log(`import: loyiha ${p.number} (${p.id}), ogohlantirish ${imp.warnings?.length ?? 0}`);
  const cut = await cutOperations(mx, p.id, null, { quality: opts.quality }, log);
  const after = await mx.get<MxProject>(`/projects/${p.id}`);
  const rows: CompareRow[] = matchOps(pf, after).map(([fo, mo]) => {
    const s = mo ? resultSummary(mo.result) : null;
    const c = cut.find((x) => x.op_id === mo?.id);
    const r: Omit<CompareRow, "verdict"> = {
      op: fo.name, type: fo.type,
      parts_file: fo.saved?.parts ?? fo.partsQty, parts_mx: s ? (s.parts_placed as number) : null, unplaced_mx: s ? (s.unplaced as number) : 0,
      sheets_file: fo.saved?.sheets ?? null, sheets_mx: s ? (s.sheets as number) : null,
      fill_file: fo.saved?.fill ?? null, fill_mx: s ? (s.fill_percent as number) : null,
      business_file: fo.saved?.businessM2 ?? null, business_mx: s ? (s.business_remnant_m2 as number) : null,
      cut_file: fo.saved?.cutLengthM ?? null, cut_mx: s ? (s.cut_length_m as number) : null,
      error: c?.error as string | undefined,
    };
    return { ...r, verdict: verdict(r) };
  });
  const tot = (k: keyof CompareRow) => rows.reduce((a, r) => a + (typeof r[k] === "number" ? (r[k] as number) : 0), 0);
  const summary = {
    file: filePath, project_name: pf.name, file_version: pf.version, mx_project_id: p.id, mx_number: p.number, quality: opts.quality, kept: opts.keep,
    import_warnings: imp.warnings ?? [],
    totals: { sheets_file: tot("sheets_file"), sheets_mx: tot("sheets_mx"), business_file: round(tot("business_file")), business_mx: round(tot("business_mx")), cut_file: round(tot("cut_file"), 1), cut_mx: round(tot("cut_mx"), 1), unplaced_mx: tot("unplaced_mx") },
    rows,
  };
  if (!opts.keep) { await mx.del(`/projects/${p.id}`); log("vaqtinchalik loyiha o'chirildi"); }
  return summary;
}

export function compareText(s: Awaited<ReturnType<typeof compareProjectFile>>): string {
  const t = s.totals;
  const head = `${s.project_name} (fayl ${s.file_version || "?"}) — MX ${s.quality}: listlar ${t.sheets_mx} vs avvalgi ${t.sheets_file}; деловой ${t.business_mx} vs ${t.business_file} m²; kesish ${t.cut_mx} vs ${t.cut_file} m; joylashmagan ${t.unplaced_mx}` +
    (s.kept ? `; MX loyiha #${s.mx_number} (${s.mx_project_id}) saqlab qolindi` : "");
  return head + "\n" + table(["Operatsiya", "Detal fayl/MX", "List fayl", "List MX", "F fayl", "F MX", "Деловой fayl", "Деловой MX", "LT fayl", "LT MX", "Xulosa"],
    s.rows.map((r) => [r.op, `${r.parts_file ?? ""}/${r.parts_mx ?? ""}${r.unplaced_mx ? ` (−${r.unplaced_mx})` : ""}`, r.sheets_file, r.sheets_mx, r.fill_file, r.fill_mx, r.business_file, r.business_mx, r.cut_file, r.cut_mx, r.verdict + (r.error ? `: ${r.error}` : "")]));
}

export function registerCompareTools(server: McpServer, cfg: Config, mx: MxClient, giblab: () => Promise<GiblabDriver>): void {
  const reg = <S extends z.ZodRawShape>(name: string, description: string, shape: S, fn: (a: z.infer<z.ZodObject<S>>) => Promise<ToolResult>) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    server.registerTool(name, { description, inputSchema: shape }, (async (args: z.infer<z.ZodObject<S>>) => {
      try { return await fn(args); } catch (e) {
        if (e instanceof MxError) return fail(`MebeliX Kroy xatosi ${e.status}: ${e.body.slice(0, 1500)}`);
        return fail(`Xato: ${String((e as Error)?.message || e)}`);
      }
    }) as any);

  reg("compare_file_info", "`.project` faylidagi operatsiyalar va avvalgi tizim saqlagan natija (listlar, F, деловой, kesish) — kroy qilmasdan.",
    { path: z.string() }, async (a) => { const pf = await readProjectFile(a.path); return text(projectFileSummary(pf)); });

  reg("compare_project", "`.project` faylini MebeliX Kroy ga import qilib, BARCHA kroy operatsiyalarini kesadi va faylda saqlangan avvalgi tizim natijasi bilan solishtiradi (listlar, F %, деловой qoldiq, kesish uzunligi, joylashmagan detallar). keep=false — vaqtinchalik loyiha o'chiriladi. background=true — fon vazifasi (mx_jobs).",
    { path: z.string(), quality: z.enum(["fast", "normal", "max"]).optional(), keep: z.boolean().default(false), folder_id: z.string().optional(), background: z.boolean().default(false) },
    async (a) => {
      const opts = { quality: a.quality ?? cfg.quality, keep: a.keep, folder_id: a.folder_id };
      if (a.background) { const j = startJob(`compare ${a.path}`, (log) => compareProjectFile(mx, a.path, opts, log).then((s) => ({ text: compareText(s), ...s }))); return json({ job_id: j.id }); }
      const s = await compareProjectFile(mx, a.path, opts, () => {});
      return text(compareText(s));
    });

  reg("compare_job", "compare_project (background) natijasi.", { job_id: z.string() }, async (a) => {
    const j = getJob(a.job_id); if (!j) return fail("vazifa topilmadi");
    if (j.status !== "done") return json({ status: j.status, progress: j.progress, error: j.error });
    return text((j.result as { text: string }).text);
  });

  reg("compare_online", "MebeliX Kroy loyihasini onlayn tizimda OCHIQ turgan loyiha bilan solishtirish: har kroy operatsiyasi uchun onlayn ko'rsatkichlar (listlar, F, LT, деловой) o'qiladi, MX da kroy qilinadi (cut=true) yoki mavjud natija olinadi. Onlayn loyiha o'zgartirilmaydi.",
    { pid: z.string().describe("MX loyiha id / raqami"), cut: z.boolean().default(false), quality: z.enum(["fast", "normal", "max"]).optional() },
    async (a) => {
      const g = await giblab();
      const online = await g.cuttingStatsAll();
      let p = await mx.get<MxProject>(`/projects/${a.pid}`);
      if (a.cut) { await cutOperations(mx, p.id, null, { quality: a.quality ?? cfg.quality }); p = await mx.get<MxProject>(`/projects/${p.id}`); }
      const mxCut = p.operations.filter((o) => o.type === "CS" || o.type === "CL");
      const rows = online.map((o, i) => {
        const m = mxCut.find((x) => x.name.trim() === o.name.trim()) || mxCut[i];
        const s = m ? resultSummary(m.result) : null;
        return [o.name, o.sheets ?? "", s?.sheets ?? "", o.fill ?? "", s?.fill_percent ?? "", o.cutLengthM ?? "", s?.cut_length_m ?? "", o.business ?? "", s?.business_remnant_m2 ?? "",
          o.sheets !== null && s ? (s.sheets === o.sheets ? "teng" : (s.sheets as number) < o.sheets ? "MX yaxshi" : "MX yomon") : ""];
      });
      return text(`Onlayn loyiha: ${(await g.status()).project ?? "?"}; MX: #${p.number} ${p.name}\n` +
        table(["Operatsiya", "List onlayn", "List MX", "F onlayn", "F MX", "LT onlayn", "LT MX", "Деловой onlayn", "Деловой MX", "Xulosa"], rows));
    });
}
