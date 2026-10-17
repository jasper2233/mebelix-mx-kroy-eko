/**
 * `mx_*` vositalari — MebeliX Kroy REST API (loyihalar, operatsiyalar, detallar, listlar, kroy, qoldiqlar ombori,
 * material katalogi, hisobot, etiketka, postprotsessorlar, MES, sozlamalar).
 */
import path from "node:path";
import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { Config } from "../config.js";
import { MxClient, MxError } from "./client.js";
import { fail, getJob, json, listJobs, saveBytes, startJob, table, text, type ToolResult } from "../util.js";
import { mapsTable, partsTable, projectSummary, resultSummary, sheetsTable, sumQty, STATUS, type MxOperation, type MxProject, type MxResult } from "./summary.js";

const CUT_TYPES = new Set(["CS", "CL", "CN"]);

export async function cutOperations(mx: MxClient, pid: string, oids: string[] | null, opts: { quality?: string; only_remaining?: boolean; first_cut?: number }, log: (s: string) => void = () => {}) {
  const p = await mx.get<MxProject>(`/projects/${pid}`);
  const targets = p.operations.filter((o) => (oids ? oids.includes(o.id) : CUT_TYPES.has(o.type)));
  const out: Array<Record<string, unknown>> = [];
  for (const o of targets) {
    const t0 = Date.now();
    try {
      const r = await mx.post<MxResult>(`/projects/${pid}/operations/${o.id}/optimize`, undefined,
        { quality: opts.quality, only_remaining: opts.only_remaining ? "true" : undefined, first_cut: opts.first_cut });
      const s = resultSummary(r)!;
      out.push({ op_id: o.id, type: o.type, name: o.name, ...s, seconds: Math.round((Date.now() - t0) / 100) / 10 });
      log(`${o.name}: ${s.sheets} list, F ${s.fill_percent}%`);
    } catch (e) {
      const msg = e instanceof MxError ? `${e.status} ${e.body.slice(0, 200)}` : String((e as Error).message || e);
      out.push({ op_id: o.id, type: o.type, name: o.name, error: msg });
      log(`${o.name}: xato ${msg}`);
    }
  }
  return out;
}

export function registerMxTools(server: McpServer, cfg: Config, mx: MxClient): void {
  const reg = <S extends z.ZodRawShape>(name: string, description: string, shape: S, fn: (a: z.infer<z.ZodObject<S>>) => Promise<ToolResult>) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    server.registerTool(name, { description, inputSchema: shape }, (async (args: z.infer<z.ZodObject<S>>) => {
      try { return await fn(args); } catch (e) {
        if (e instanceof MxError) return fail(`MebeliX Kroy xatosi ${e.status} (${e.url}): ${e.body.slice(0, 1500)}`);
        return fail(`Xato: ${String((e as Error)?.message || e)}`);
      }
    }) as any);
  const pidS = z.string().describe("Loyiha id (mx_projects dan) yoki raqami");
  const oidS = z.string().describe("Operatsiya id (mx_project → ops jadvalidagi «op id»)");
  const resolvePid = async (pid: string): Promise<string> => {
    if (/^\d{4,}$/.test(pid)) {           // raqam bo'yicha
      const list = await mx.get<MxProject[]>("/projects", { q: pid });
      const hit = list.find((p) => String(p.number) === pid);
      if (hit) return hit.id;
    }
    return pid;
  };
  const loadProject = async (pid: string) => mx.get<MxProject>(`/projects/${await resolvePid(pid)}`);
  const findOp = (p: MxProject, oid: string): MxOperation => {
    const o = p.operations.find((x) => x.id === oid) || p.operations[Number(oid) - 1];
    if (!o) throw new Error(`Operatsiya topilmadi: ${oid}`);
    return o;
  };

  // ───── umumiy ─────
  reg("mx_health", "MebeliX Kroy serveri holati (manzil, versiya).", {}, async () => json({ url: mx.baseUrl, ...(await mx.get<Record<string, unknown>>("/health")) }));

  reg("mx_folders", "Loyiha papkalari ro'yxati (id, nom, ota papka).", {}, async () => json(await mx.get("/folders/all")));

  reg("mx_projects", "Loyihalar ro'yxati (xodimlar ko'radigan jadval: ID, Владелец, Состояние, Дата, Стоимость, Наименование). q — qidiruv (nomi, raqami, buyurtmachi, MES raqami).",
    { folder_id: z.string().optional().describe("Papka id (bo'sh — ildiz)"), q: z.string().optional(), status: z.number().int().min(0).max(3).optional(), all_folders: z.boolean().optional() },
    async (a) => {
      const rows = await mx.get<MxProject[]>("/projects", { folder_id: a.folder_id, q: a.q, status: a.status, all_folders: a.all_folders ? "true" : undefined });
      return text(table(["ID", "id", "Владелец", "Состояние", "Дата", "Наименование", "MES"],
        rows.map((p) => [p.number, p.id, p.owner || "", STATUS[p.status] ?? p.status, p.order_date || "", p.name, p.mes_order_ref || ""])) + `\n${rows.length} loyiha`);
    });

  reg("mx_project", "Bitta loyiha: summary — operatsiyalar jadvali va natija; ops — operatsiyalar JSON (detallarsiz); full — to'liq JSON.",
    { pid: pidS, detail: z.enum(["summary", "ops", "full"]).default("summary") },
    async (a) => {
      const p = await loadProject(a.pid);
      if (a.detail === "full") return json(p);
      if (a.detail === "ops") return json({ ...p, operations: p.operations.map((o) => ({ ...o, parts: `[${o.parts.length}]`, result: resultSummary(o.result) })) });
      return text(projectSummary(p));
    });

  reg("mx_project_create", "Yangi loyiha yaratish.", { name: z.string(), folder_id: z.string().optional(), customer: z.string().optional(), note: z.string().optional() },
    async (a) => json(await mx.post("/projects", { name: a.name, folder_id: a.folder_id ?? null, customer: a.customer ?? "", note: a.note ?? "" })));

  reg("mx_project_update", "Loyiha maydonlarini o'zgartirish (name, customer, note, status 0..3, folder_id, mes_order_ref, order_date, ready_date, size_mode).",
    { pid: pidS, patch: z.record(z.string(), z.unknown()) }, async (a) => json(await mx.patch(`/projects/${await resolvePid(a.pid)}`, a.patch)));

  reg("mx_project_delete", "Loyihani o'chirish (qaytarib bo'lmaydi) — confirm=true shart.", { pid: pidS, confirm: z.boolean() },
    async (a) => a.confirm ? json(await mx.del(`/projects/${await resolvePid(a.pid)}`)) : fail("confirm=true bering"));

  reg("mx_project_copy", "Loyiha nusxasi.", { pid: pidS, name: z.string().optional() }, async (a) => json(await mx.post(`/projects/${await resolvePid(a.pid)}/copy`, a.name ? { name: a.name } : {})));

  reg("mx_project_undo", "Ctrl+Z — oxirgi amalni bekor qilish (server tarixi).", { pid: pidS }, async (a) => text(projectSummary(await mx.post<MxProject>(`/projects/${await resolvePid(a.pid)}/undo`))));
  reg("mx_project_redo", "Ctrl+Y — qaytarish.", { pid: pidS }, async (a) => text(projectSummary(await mx.post<MxProject>(`/projects/${await resolvePid(a.pid)}/redo`))));

  reg("mx_project_import", "Faylni import qilish: `.project` (XML — korxona fayllari), `.mxk.json`, Excel/CSV va boshqa formatlar (mx_import_formats). Natija: yangi loyiha xulosasi va ogohlantirishlar.",
    { path: z.string().describe("Fayl yo'li (lokal disk)"), folder_id: z.string().optional() },
    async (a) => {
      const r = await mx.upload<{ project: MxProject; warnings: string[] }>("/projects/import-file", a.path, "file", a.folder_id ? { folder_id: a.folder_id } : {});   // folder_id — forma maydoni (query emas)
      const p = r.project ?? (r as unknown as MxProject);
      return text(projectSummary(p) + (r.warnings?.length ? `\n\nOgohlantirishlar (${r.warnings.length}):\n- ` + r.warnings.slice(0, 40).join("\n- ") : "\n\nOgohlantirish yo'q"));
    });

  reg("mx_import_formats", "Import qilinadigan formatlar ro'yxati.", {}, async () => json(await mx.get("/import/formats")));

  reg("mx_project_export", "Loyihani faylga eksport qilish: project — `.project` XML (boshqa tizimda ochiladi), mxk — `.mxk.json`.",
    { pid: pidS, format: z.enum(["project", "mxk"]).default("project"), out_dir: z.string().optional() },
    async (a) => {
      const pid = await resolvePid(a.pid);
      const f = a.format === "project" ? await mx.getBytes(`/projects/${pid}/export/project`) : await mx.getBytes(`/projects/${pid}/export`);
      const saved = await saveBytes(a.out_dir || cfg.outDir, f.filename, f.bytes);
      return json({ saved, bytes: f.bytes.length, filename: f.filename });
    });

  // ───── operatsiyalar ─────
  reg("mx_operation_add", "Operatsiya qo'shish: CS (listli kroy), CL (pogonaj), CN (nesting), EL (kromka), GR (paz), XNC (CNC), SP, O, LB. material_id — katalog tovar id (ixtiyoriy).",
    { pid: pidS, type: z.enum(["CS", "CL", "CN", "EL", "GR", "XNC", "SP", "O", "LB"]), name: z.string().optional(), code: z.string().optional(), material_id: z.string().optional(), position: z.number().int().optional() },
    async (a) => {
      const p = await mx.post<MxProject>(`/projects/${await resolvePid(a.pid)}/operations`, { type: a.type, name: a.name ?? "", code: a.code ?? "", material_id: a.material_id ?? null }, { position: a.position });
      return text(projectSummary(p));
    });

  reg("mx_operation_update", "Operatsiya parametrlarini o'zgartirish (PATCH): masalan {\"cs_cut\": {\"max_rotations\": 4, \"kerf\": 3}}, {\"cs_material\": {\"thickness\": 18}}, {\"name\": \"...\"}, {\"el\": {\"width\": 19}}.",
    { pid: pidS, oid: oidS, patch: z.record(z.string(), z.unknown()) },
    async (a) => { const p = await mx.patch<MxProject>(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}`, a.patch); return json(findOp(p, a.oid)); });

  reg("mx_operation_delete", "Operatsiyani o'chirish.", { pid: pidS, oid: oidS }, async (a) => text(projectSummary(await mx.del<MxProject>(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}`))));

  reg("mx_operation_get", "Operatsiya JSON (parametrlar; parts/result qisqartirilgan). include_parts=true — detallar ham.",
    { pid: pidS, oid: oidS, include_parts: z.boolean().default(false) },
    async (a) => { const o = findOp(await loadProject(a.pid), a.oid); return json({ ...o, parts: a.include_parts ? o.parts : `[${o.parts.length}]`, result: resultSummary(o.result) }); });

  reg("mx_actions", "«Общие действия»: merge-same — bir xil operatsiyalarni birlashtirish; split-edges — kromkani materiallar bo'yicha ajratish; optimize-ops — operatsiyalarni optimallashtirish; recode-xnc — XNC kodlarini qayta raqamlash; clear — kroy natijalarini tozalash; recalc-parametric — parametrik mahsulotlarni qayta hisoblash.",
    { pid: pidS, action: z.enum(["merge-same", "split-edges", "optimize-ops", "recode-xnc", "clear", "recalc-parametric"]) },
    async (a) => { const r = await mx.post<MxProject | Record<string, unknown>>(`/projects/${await resolvePid(a.pid)}/actions/${a.action}`, {}); return "operations" in r ? text(projectSummary(r as MxProject)) : json(r); });

  // ───── detallar ─────
  reg("mx_parts", "Operatsiya detallari jadvali («Детали»): ID, nom, Д-на, Ш-на, Кол, Ткт, ИК (kroyga kirgan), Ост, kromka tomonlari, XNC soni.",
    { pid: pidS, oid: oidS, limit: z.number().int().min(1).max(5000).default(500), as_json: z.boolean().default(false) },
    async (a) => { const o = findOp(await loadProject(a.pid), a.oid); return a.as_json ? json(o.parts.slice(0, a.limit)) : text(`${o.type} ${o.name}: ${o.parts.length} qator, Σ ${sumQty(o.parts)} dona\n` + partsTable(o, a.limit)); });

  reg("mx_parts_add", "Detallar qo'shish (Excel kabi): [{name, length, width, qty, grain?, code?, description?, product_id?, edge_top/bottom/left/right: {op_id}}].",
    { pid: pidS, oid: oidS, parts: z.array(z.record(z.string(), z.unknown())).min(1), position: z.number().int().optional() },
    async (a) => { const p = await mx.post<MxProject>(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}/parts`, a.parts, { position: a.position }); const o = findOp(p, a.oid); return text(`Qo'shildi. Endi ${o.parts.length} qator, Σ ${sumQty(o.parts)}\n` + partsTable(o, 50)); });

  reg("mx_parts_update", "Bitta detalni o'zgartirish (PATCH maydonlari).", { pid: pidS, oid: oidS, part_id: z.string(), patch: z.record(z.string(), z.unknown()) },
    async (a) => { const p = await mx.patch<MxProject>(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}/parts/${a.part_id}`, a.patch); const o = findOp(p, a.oid); return json(o.parts.find((x) => x.id === a.part_id)); });

  reg("mx_parts_group_update", "«Групповые действия» (Ctrl+B): tanlangan detallarga bir xil maydonlar.", { pid: pidS, oid: oidS, ids: z.array(z.string()).min(1), fields: z.record(z.string(), z.unknown()) },
    async (a) => text(projectSummary(await mx.post<MxProject>(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}/parts/group-update`, { ids: a.ids, fields: a.fields }))));

  reg("mx_parts_delete", "Detallarni o'chirish.", { pid: pidS, oid: oidS, ids: z.array(z.string()).min(1) },
    async (a) => { const p = await mx.post<MxProject>(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}/parts/delete`, { ids: a.ids }); return text(`Qoldi ${findOp(p, a.oid).parts.length} qator`); });

  reg("mx_parts_move_to", "Ctrl+M — detallarni boshqa kroy operatsiyasiga (CS/CL/CN) ko'chirish.", { pid: pidS, oid: oidS, target_oid: z.string(), ids: z.array(z.string()).min(1) },
    async (a) => text(projectSummary(await mx.post<MxProject>(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}/parts/move-to/${a.target_oid}`, { ids: a.ids }))));

  reg("mx_parts_bulk", "Ctrl+W — o'lchamlarni almashtirish (swap); Ctrl+E/D — tekstura qo'yish/olish (grain-on / grain-off).", { pid: pidS, oid: oidS, action: z.enum(["swap", "grain-on", "grain-off"]), ids: z.array(z.string()).min(1) },
    async (a) => { const p = await mx.post<MxProject>(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}/parts/bulk/${a.action}`, { ids: a.ids }); return text(partsTable(findOp(p, a.oid), 50)); });

  // ───── listlar va qoldiqlar ─────
  reg("mx_sheets", "«Листы и остатки» jadvali (kroy ustuvorligi tartibida; soni 10000 = cheksiz).", { pid: pidS, oid: oidS },
    async (a) => text(sheetsTable(findOp(await loadProject(a.pid), a.oid))));

  reg("mx_sheets_set", "Listlar ro'yxatini to'liq almashtirish: [{length, width, qty (10000 = cheksiz), is_remnant?, trim_length?, trim_width?, end_offset_bottom?, end_offset_right?, description?}].",
    { pid: pidS, oid: oidS, sheets: z.array(z.record(z.string(), z.unknown())).min(1) },
    async (a) => { const p = await mx.put<MxProject>(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}/sheets`, a.sheets); return text(sheetsTable(findOp(p, a.oid))); });

  reg("mx_sheets_from_warehouse", "Ombordagi qoldiqlarni listlar ro'yxatiga qo'shish (rezerv qilinadi; kroyda birinchi navbatda kesiladi).", { pid: pidS, oid: oidS, remnant_ids: z.array(z.number().int()).min(1) },
    async (a) => { const p = await mx.post<MxProject>(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}/sheets/from-remnants`, { ids: a.remnant_ids }); return text(sheetsTable(findOp(p, a.oid))); });

  // ───── kroy ─────
  reg("mx_cut", "«Раскроить»: oid berilsa — shu operatsiya; berilmasa — loyihadagi BARCHA kroy operatsiyalari (CS/CL/CN) ketma-ket. quality: fast (≤2 s), normal (≤17 s), max. background=true — fon vazifasi (mx_jobs bilan kuzatiladi).",
    { pid: pidS, oid: z.string().optional(), quality: z.enum(["fast", "normal", "max"]).optional(), only_remaining: z.boolean().default(false).describe("«До кроить» — faqat kroyga kirmagan detallar"),
      first_cut: z.number().int().min(0).max(4).optional().describe("Начальное направление резов: 0 любое, 1 по длине, 2 по ширине, 3 авто-смешанный, 4 …"), background: z.boolean().default(false) },
    async (a) => {
      const pid = await resolvePid(a.pid);
      const opts = { quality: a.quality ?? cfg.quality, only_remaining: a.only_remaining, first_cut: a.first_cut };
      if (a.background) { const j = startJob(`cut ${pid}`, (log) => cutOperations(mx, pid, a.oid ? [a.oid] : null, opts, log)); return json({ job_id: j.id, status: j.status }); }
      const out = await cutOperations(mx, pid, a.oid ? [a.oid] : null, opts);
      return text(table(["Operatsiya", "Listlar", "F %", "LT, m", "Деловой m²", "Joylashmagan", "Paket", "s", "Xato"],
        out.map((r) => [r.name, r.sheets, r.fill_percent, r.cut_length_m, r.business_remnant_m2, r.unplaced, r.packs, r.seconds, r.error ?? ""])));
    });

  reg("mx_cut_all", "«Общие действия → Раскроить все операции»: barcha kroy operatsiyalari (CS/CL/CN) serverda ketma-ket, BITTA tarix qadami (Ctrl+Z). skip_done — natijasi borlarini o'tkazib yuborish.",
    { pid: pidS, quality: z.enum(["fast", "normal", "max"]).optional(), only_remaining: z.boolean().default(false), skip_done: z.boolean().default(false) },
    async (a) => {
      const r = await mx.post<{ results: Array<Record<string, unknown>>; message: string }>(`/projects/${await resolvePid(a.pid)}/actions/optimize-all`, undefined,
        { quality: a.quality ?? cfg.quality, only_remaining: a.only_remaining ? "true" : undefined, skip_done: a.skip_done ? "true" : undefined });
      return text(r.message + "\n" + table(["Operatsiya", "Tur", "Listlar", "F %", "LT, m", "Joylashmagan", "Xato / holat"],
        r.results.map((x) => [x.name, x.type, x.sheets ?? "", x.fill ?? "", x.cut_length_m ?? "", x.unplaced ?? "", x.error ?? (x.skipped ? "o'tkazib yuborildi" : "")])));
    });

  reg("mx_jobs", "Fon vazifalari (mx_cut background=true, compare_*): holat va natija.", { job_id: z.string().optional() },
    async (a) => a.job_id ? json(getJob(a.job_id) ?? { error: "topilmadi" }) : json(listJobs().map((j) => ({ id: j.id, name: j.name, status: j.status, seconds: Math.round(((j.finished ?? Date.now()) - j.started) / 1000), progress: j.progress.slice(-3) }))));

  reg("mx_result", "Kroy natijasi: summary — holat qatori (S, C, Ср, LT, F, деловой); maps — kartalar jadvali; remnants — qoldiqlar; full — to'liq JSON (joylashuvlar, buyruqlar).",
    { pid: pidS, oid: oidS, detail: z.enum(["summary", "maps", "remnants", "full"]).default("summary") },
    async (a) => {
      const o = findOp(await loadProject(a.pid), a.oid);
      if (!o.result) return text(`${o.name}: kroy qilinmagan`);
      if (a.detail === "full") return json(o.result);
      if (a.detail === "maps") return text(mapsTable(o.result));
      if (a.detail === "remnants") return text(table(["№", "Длина", "Ширина", "Деловой", "Xom o'lcham"], o.result.remnants.map((r) => [r.number ?? "", r.length, r.width, r.business ? "✓" : "", `${r.raw_length ?? ""}×${r.raw_width ?? ""}`])));
      const s = resultSummary(o.result)!;
      const unplaced = o.result.unplaced.map((id) => o.parts.find((p) => p.id === id)).filter(Boolean).map((p) => `${p!.uid} ${p!.name} ${p!.length}×${p!.width}${p!.grain ? " Ткт" : ""}`);
      return json({ op: o.name, ...s, unplaced_parts: unplaced });
    });

  reg("mx_variants", "Kroy variantlarini solishtirish (optimal / 1-kesim uzunlik / eni bo'yicha; CL — kam material / kam sarf / …).", { pid: pidS, oid: oidS },
    async (a) => json(await mx.post(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}/variants`, {})));

  reg("mx_result_delete", "«Удаление раскроя» — natijani o'chirish.", { pid: pidS, oid: oidS }, async (a) => { await mx.del(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}/result`); return text("Natija o'chirildi"); });

  reg("mx_map_svg", "Kroy kartasi chizmasi (SVG) faylga.", { pid: pidS, oid: oidS, index: z.number().int().min(0), out_dir: z.string().optional() },
    async (a) => { const pid = await resolvePid(a.pid); const svg = await mx.getText(`/projects/${pid}/operations/${a.oid}/maps/${a.index}.svg`); return json({ saved: await saveBytes(a.out_dir || cfg.outDir, `map_${pid}_${a.oid}_${a.index}.svg`, svg), bytes: svg.length }); });

  // ───── qoldiqlar ombori ─────
  reg("mx_remnants_proposed", "Kroydan keyingi деловой qoldiqlar (omborga yozishdan oldin ko'rish).", { pid: pidS, oid: oidS },
    async (a) => json(await mx.get(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}/remnants`)));
  reg("mx_remnants_commit", "Деловой qoldiqlarni omborga yozish (tasdiq).", { pid: pidS, oid: oidS },
    async (a) => json(await mx.post(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}/remnants/commit`, {})));
  reg("mx_remnants_rollback", "Omborga yozilgan qoldiqlarni bekor qilish.", { pid: pidS, oid: oidS },
    async (a) => json(await mx.post(`/projects/${await resolvePid(a.pid)}/operations/${a.oid}/remnants/rollback`, {})));

  reg("mx_warehouse", "Qoldiqlar ombori ro'yxati (material kodi, nomi, o'lcham, soni, rezerv).", { q: z.string().optional(), material_code: z.string().optional(), thickness: z.number().optional(), linear: z.boolean().optional(), include_empty: z.boolean().default(false) },
    async (a) => {
      const rows = await mx.get<Array<Record<string, unknown>>>("/remnants", { q: a.q, material_code: a.material_code, thickness: a.thickness, linear: a.linear, include_empty: a.include_empty ? "true" : undefined });
      return text(table(["id", "Код", "Материал", "Т", "Длина", "Ширина", "Кол", "Рез. loyiha", "Izoh"], rows.map((r) => [r.id, r.material_code, r.material_name, r.thickness, r.length, r.width, r.qty, r.reserved_number ?? "", r.note ?? ""])) + `\n${rows.length} qator`);
    });
  reg("mx_warehouse_add", "Omborga qoldiq qo'shish (qo'lda / MES dan).", { material_code: z.string(), material_name: z.string().default(""), length: z.number().positive(), width: z.number().positive(), thickness: z.number().default(16), qty: z.number().int().min(1).default(1), note: z.string().default(""), linear: z.boolean().default(false) },
    async (a) => json(await mx.post("/remnants", a)));
  reg("mx_warehouse_update", "Ombor qatorini o'zgartirish (qty, note, o'lcham).", { rid: z.number().int(), patch: z.record(z.string(), z.unknown()) }, async (a) => json(await mx.patch(`/remnants/${a.rid}`, a.patch)));
  reg("mx_warehouse_delete", "Ombor qatorini o'chirish.", { rid: z.number().int() }, async (a) => json(await mx.del(`/remnants/${a.rid}`)));
  reg("mx_warehouse_request", "«Заявка на склад» — loyiha uchun kerakli listlar / qoldiqlar (MES uchun).", { pid: pidS }, async (a) => json(await mx.get(`/projects/${await resolvePid(a.pid)}/warehouse`)));

  // ───── material katalogi ─────
  reg("mx_catalog", "Material katalogi (listli, pogonaj, kromka, yuza): ro'yxat yoki daraxt.", { q: z.string().optional(), kind: z.string().optional(), tree: z.boolean().default(false) },
    async (a) => a.tree ? json(await mx.get("/catalog/tree")) : (async () => {
      const rows = await mx.get<Array<Record<string, unknown>>>("/catalog", { q: a.q, kind: a.kind });
      return text(table(["id", "kind", "Код", "Наименование", "Ед", "Цена", "Склад", "Т", "Длина", "Ширина"], rows.map((r) => [r.id, r.kind, r.code, r.name, r.unit, r.price, r.stock, r.thickness, r.length, r.width])) + `\n${rows.length} tovar`);
    })());
  reg("mx_catalog_sync", "MES dan tovarlarni yuklash (upsert): [{id, kind (sheet|band|simple|surface|folder), code, name, unit, price, stock, thickness, length, width, params}].",
    { items: z.array(z.record(z.string(), z.unknown())).min(1) }, async (a) => json(await mx.post("/catalog/sync", a.items)));

  // ───── hisobot, etiketka ─────
  reg("mx_report", "«Печать отчета» — HTML hisobot faylga (profillar: /settings print).", { pid: pidS, lang: z.enum(["ru", "uz"]).default("ru"), profile_id: z.number().int().optional(), out_dir: z.string().optional() },
    async (a) => { const pid = await resolvePid(a.pid); const html = await mx.getText(`/projects/${pid}/report`, { lang: a.lang, profile_id: a.profile_id }); return json({ saved: await saveBytes(a.out_dir || cfg.outDir, `report_${pid}_${a.lang}.html`, html), bytes: html.length }); });
  reg("mx_labels", "Etiketkalar (QR) — HTML faylga.", { pid: pidS, op_id: z.string().optional(), lang: z.enum(["ru", "uz"]).default("ru"), out_dir: z.string().optional() },
    async (a) => { const pid = await resolvePid(a.pid); const html = await mx.getText(`/projects/${pid}/labels`, { op_id: a.op_id, lang: a.lang }); return json({ saved: await saveBytes(a.out_dir || cfg.outDir, `labels_${pid}.html`, html), bytes: html.length }); });

  // ───── postprotsessorlar ─────
  reg("mx_postprocessors", "Stanok formatlari: o'rnatilgan generatorlar (arra / ishlov markazi) va sozlangan stanoklar.", {},
    async () => json({ native: await mx.get("/postprocessors/native"), machines: await mx.get("/postprocessors/machines"), formats: await mx.get("/postprocessors") }));
  reg("mx_postprocess", "Kroy natijasini stanok formatida faylga: key = csv | commands | dxf | json | machine:<kalit> (mx_postprocessors). XNC operatsiyasi uchun ham ishlaydi.",
    { pid: pidS, oid: oidS, key: z.string(), long_side: z.enum(["any", "horizontal", "vertical"]).default("any"), out_dir: z.string().optional() },
    async (a) => { const pid = await resolvePid(a.pid); const f = await mx.getBytes(`/projects/${pid}/operations/${a.oid}/postprocess`, { key: a.key, long_side: a.long_side }); return json({ saved: await saveBytes(a.out_dir || cfg.outDir, f.filename, f.bytes), bytes: f.bytes.length, type: f.type }); });
  reg("mx_postprocess_xnc_all", "Loyihaning barcha XNC dasturlari ishlov markazi formatida bitta zip da (key = machine:<kalit>).",
    { pid: pidS, key: z.string(), long_side: z.enum(["any", "horizontal", "vertical"]).default("any"), ops: z.array(z.string()).optional(), out_dir: z.string().optional() },
    async (a) => { const pid = await resolvePid(a.pid); const f = await mx.getBytes(`/projects/${pid}/postprocess-xnc`, { key: a.key, long_side: a.long_side, ops: a.ops?.join(",") }); return json({ saved: await saveBytes(a.out_dir || cfg.outDir, f.filename, f.bytes), bytes: f.bytes.length }); });

  // ───── MES ─────
  reg("mx_mes_export", "MES uchun natija: listlar, m², qoldiqlar, kromka m, narxlar, kartalar, omborga talabnoma.", { pid: pidS }, async (a) => json(await mx.get(`/projects/${await resolvePid(a.pid)}/mes-export`)));
  reg("mx_mes_order", "MES buyurtmasini loyihaga aylantirish (POST /api/mes/orders): {ref, name, customer, materials[], edges[], products[], parts[]} — qayta yuborilsa mavjud loyiha yangilanadi.",
    { order: z.record(z.string(), z.unknown()) }, async (a) => json(await mx.post("/mes/orders", a.order)));
  reg("mx_mes_order_get", "MES buyurtma raqami bo'yicha natija.", { ref: z.string() }, async (a) => json(await mx.get(`/mes/orders/${encodeURIComponent(a.ref)}`)));
  reg("mx_mes_scan", "Etiketka / karta QR kodi bo'yicha ma'lumot; done=true — karta kesildi (+1).", { code: z.string(), done: z.boolean().default(false) },
    async (a) => json(a.done ? await mx.post(`/mes/scan/${encodeURIComponent(a.code)}/done`, {}) : await mx.get(`/mes/scan/${encodeURIComponent(a.code)}`)));
  reg("mx_mes_webhook_test", "MES webhook ulanishini sinash.", {}, async () => json(await mx.post("/mes/webhook-test", {})));

  // ───── navbat va material bazasi (2026-10-15) ─────
  reg("mx_material_check", "Loyiha uchun material bazasi tekshiruvi: har kroy operatsiyasi — kerak (kroydan keyin butun listlar, kroygacha ≈ taxmin) / bazada (katalog `stock`) / yetmaydi; ombordagi qoldiqlar soni; ogohlantirishlar.",
    { pid: pidS }, async (a) => {
      const r = await mx.get<{ ok: boolean; known: boolean; items: Array<Record<string, unknown>>; warnings: string[] }>(`/projects/${await resolvePid(a.pid)}/material-check`);
      return text((r.ok ? "Material to'liq bor" : r.known ? "Material yetmaydi" : "Katalogda yo'q material bor") + "\n" +
        table(["Operatsiya", "Qalinlik", "Kerak", "Bazada", "Yetmaydi", "Qoldiq (ombor)", "Holat"], r.items.map((i) => [i.name, i.thickness ?? "", `${i.estimated ? "≈ " : ""}${i.need}`, i.have ?? "?", i.short ?? "?", i.remnants, i.status])) +
        (r.warnings.length ? "\n\nOgohlantirishlar:\n- " + r.warnings.join("\n- ") : ""));
    });
  reg("mx_queue", "«Очередь заказов»: loyihalar kelish tartibida, har biri uchun material bazasi tekshiruvi; `next` — material to'liq bor birinchi loyiha; yetmaganlar uchun «bazani to'ldiring» ogohlantirishlari (loyiha raqami bilan).",
    { statuses: z.string().default("0,1,2").describe("Holatlar: 0 Не заказан, 1 Заказан, 2 Утвержден, 3 Готов"), limit: z.number().int().min(1).max(1000).default(100) },
    async (a) => {
      const r = await mx.get<{ message: string; next: { number: number; name: string } | null; rows: Array<Record<string, unknown>>; warnings: string[] }>("/queue", { statuses: a.statuses, limit: a.limit });
      return text(r.message + "\n" + table(["№", "ID", "Loyiha", "Holat", "Material", "Xulosa"], r.rows.map((x) => {
        const items = x.items as Array<Record<string, unknown>>;
        return [x.position, x.number, x.name, STATUS[x.status as number] ?? x.status,
          items.map((i) => `${i.name}: ${i.estimated ? "≈" : ""}${i.need}/${i.have ?? "?"}`).join("; "),
          x.ok ? "to'liq" + (x.next ? " — NAVBATDAGI" : "") : x.known ? "yetmaydi" : "katalogda yo'q"];
      })) + (r.warnings.length ? "\n\nBazani to'ldiring:\n- " + r.warnings.join("\n- ") : ""));
    });

  // ───── sozlamalar ─────
  reg("mx_settings", "Sozlamalar: scope berilmasa — hamma scope lar; berilsa — standart profil (cs_defaults, print, labels, general, …).", { scope: z.string().optional() },
    async (a) => json(a.scope ? await mx.get(`/settings/${a.scope}/default`) : await mx.get("/settings")));
  reg("mx_settings_set", "Standart sozlamalarni o'zgartirish (PUT /settings/{scope}/default).", { scope: z.string(), values: z.record(z.string(), z.unknown()) },
    async (a) => json(await mx.put(`/settings/${a.scope}/default`, a.values)));

  // ───── umumiy API ─────
  reg("mx_api", "Istalgan MebeliX Kroy REST so'rovi (yo'l `/api` dan keyin, masalan `/projects/{pid}/edge-usage`). Ro'yxat: {mxUrl}/docs.",
    { method: z.enum(["GET", "POST", "PUT", "PATCH", "DELETE"]).default("GET"), path: z.string(), body: z.unknown().optional(), query: z.record(z.string(), z.unknown()).optional(), save_to: z.string().optional().describe("Javobni faylga yozish (ikkilik fayllar uchun)") },
    async (a) => {
      if (a.save_to) { const f = await mx.getBytes(a.path, a.query); return json({ saved: await saveBytes(path.dirname(a.save_to), path.basename(a.save_to), f.bytes), bytes: f.bytes.length }); }
      if (a.method === "GET") return json(await mx.get(a.path, a.query));
      return json(await mx.send(a.method, a.path, a.body, a.query));
    });
}
