/** MebeliX Kroy loyiha JSON idan qisqa jadval va natija xulosalari (xodimlar ko'radigan «Операции» jadvali kabi). */
import { fmt, round, table } from "../util.js";

export interface MxPart { id: string; uid: number; name: string; code?: string; length: number; width: number; qty: number; grain: boolean;
  used_qty?: number; left_qty?: number; minus_qty?: number; product_id?: string | null;
  edge_top?: { op_id?: string | null }; edge_bottom?: { op_id?: string | null }; edge_left?: { op_id?: string | null }; edge_right?: { op_id?: string | null };
  xnc_op_ids?: string[]; [k: string]: unknown }
export interface MxSheet { id: string; length: number; width: number; qty: number; is_remnant: boolean; trim_length?: number | null; trim_width?: number | null;
  end_offset_bottom?: number | null; end_offset_right?: number | null; description?: string; used_qty?: number; source_remnant_id?: number | null }
export interface MxOffcut { x: number; y: number; length: number; width: number; kind: "remnant" | "waste"; number?: number; business?: boolean; raw_length?: number; raw_width?: number }
export interface MxMap { index: number; sheet_id: string; sheet_length: number; sheet_width: number; is_remnant?: boolean; copies: number;
  placements: Array<{ part_id: string; part_uid: number; x: number; y: number; length: number; width: number; rotated?: boolean }>;
  offcuts: MxOffcut[]; commands?: unknown[]; parts_count: number; cut_length_m: number; cuts_count: number; fill_percent: number;
  parts_area_m2: number; sheet_area_m2: number; remnant_area_m2: number; comment?: string; packs?: number; done_count?: number }
export interface MxResult { maps: MxMap[]; total_sheets: number; total_parts: number; unplaced: string[]; total_cut_length_m: number; total_cuts: number;
  total_fill_percent: number; parts_area_m2: number; material_area_m2: number; remnant_area_m2: number; material_qty_m2: number; remnants: MxOffcut[];
  warnings: string[]; sheets_per_pack?: number; total_packs?: number; variant?: string; manual?: boolean; remnants_saved?: boolean; elapsed_s?: number;
  kind?: string; material_len_m?: number; business_len_m?: number; [k: string]: unknown }
export interface MxOperation { id: string; type: string; code?: string; name: string; description?: string; material_id?: string | null;
  parts: MxPart[]; sheets: MxSheet[]; result?: MxResult | null; cs_cut?: Record<string, unknown> | null; cs_material?: Record<string, unknown> | null;
  el?: Record<string, unknown> | null; xnc?: Record<string, unknown> | null; xnc_part_id?: string | null; cost_material?: number; cost_operation?: number; [k: string]: unknown }
export interface MxProject { id: string; number: number; name: string; folder_id?: string | null; status: number; currency?: string; size_mode?: string;
  customer?: string; note?: string; mes_order_ref?: string | null; order_date?: string; ready_date?: string;
  operations: MxOperation[]; products: Array<{ id: string; code?: string; name: string; qty: number }>; [k: string]: unknown }

export const STATUS: Record<number, string> = { 0: "Не заказан", 1: "Заказан", 2: "Утвержден", 3: "Готов" };

export function sumQty(parts: MxPart[]): number { return parts.reduce((s, p) => s + (p.qty || 0), 0); }

/** Natija xulosasi — kroy paneli holat qatori (S, C, Ср, LT, F) kabi. */
export function resultSummary(r: MxResult | null | undefined): Record<string, unknown> | null {
  if (!r) return null;
  const biz = r.maps.reduce((s, m) => s + m.offcuts.filter((o) => o.kind === "remnant" && o.business).reduce((a, o) => a + (o.length * o.width) / 1e6, 0) * m.copies, 0);
  return {
    sheets: r.total_sheets, maps: r.maps.length, parts_placed: r.total_parts, unplaced: r.unplaced.length,
    fill_percent: round(r.total_fill_percent, 2), cut_length_m: round(r.total_cut_length_m, 2), cuts: r.total_cuts,
    business_remnant_m2: round(biz, 3), remnant_area_m2: round(r.remnant_area_m2, 3), material_area_m2: round(r.material_area_m2, 3),
    material_qty_m2: round(r.material_qty_m2, 3), packs: r.total_packs ?? null, sheets_per_pack: r.sheets_per_pack ?? null,
    variant: r.variant || "", manual: !!r.manual, remnants_saved: !!r.remnants_saved, elapsed_s: r.elapsed_s ?? null, warnings: r.warnings, kind: r.kind || "sheet",
  };
}

export function operationRow(o: MxOperation): Record<string, unknown> {
  const s = resultSummary(o.result);
  return {
    id: o.id, type: o.type, name: o.name, code: o.code || "", parts: o.parts.length, qty: sumQty(o.parts), sheets_rows: o.sheets.length,
    result: s ? `${s.sheets} list, F ${s.fill_percent}%, LT ${s.cut_length_m} m${s.unplaced ? `, joylashmagan ${s.unplaced}` : ""}` : (o.type === "CS" || o.type === "CL" || o.type === "CN" ? "kroy yo'q" : ""),
    description: o.description || "",
  };
}

export function projectSummary(p: MxProject): string {
  const head = `#${p.number} «${p.name}» (id ${p.id}) — ${STATUS[p.status] ?? p.status}; mahsulotlar ${p.products.length}; operatsiyalar ${p.operations.length}` +
    (p.mes_order_ref ? `; MES ${p.mes_order_ref}` : "") + (p.customer ? `; buyurtmachi ${p.customer}` : "");
  const rows = p.operations.map(operationRow).map((r) => [r.type, r.name, r.parts, r.qty, r.sheets_rows, r.result, r.id]);
  return head + "\n" + table(["Tur", "Nom", "Detal", "Σ soni", "List qatorlari", "Natija", "op id"], rows);
}

export function partsTable(o: MxOperation, limit = 500): string {
  const rows = o.parts.slice(0, limit).map((p) => [p.uid, p.name, p.length, p.width, p.qty, p.grain ? "✓" : "", p.used_qty ?? "", p.left_qty ?? "",
    [p.edge_top?.op_id ? "В" : "", p.edge_bottom?.op_id ? "Н" : "", p.edge_left?.op_id ? "Л" : "", p.edge_right?.op_id ? "П" : ""].join(""), (p.xnc_op_ids || []).length || "", p.id]);
  return table(["ID", "Наименование", "Д-на", "Ш-на", "Кол", "Ткт", "ИК", "Ост", "Кромка", "XNC", "id"], rows) + (o.parts.length > limit ? `\n… jami ${o.parts.length} qator` : "");
}

export function sheetsTable(o: MxOperation): string {
  return table(["№", "Длина", "Ширина", "Кол-во", "Остаток", "ТД", "ТШ", "Исп.", "Описание", "id"],
    o.sheets.map((s, i) => [i + 1, s.length, s.width, s.qty >= 10000 ? "∞" : s.qty, s.is_remnant ? "✓" : "", s.trim_length ?? "", s.trim_width ?? "", s.used_qty ?? "", s.description || "", s.id]));
}

export function mapsTable(r: MxResult): string {
  return table(["№", "Лист", "C", "Ср", "LT, m", "CT", "F %", "Деловой, m²", "Пакет", "Изготовлено"],
    r.maps.map((m) => [m.index, `${m.sheet_length}×${m.sheet_width}${m.is_remnant ? " (ост.)" : ""}`, m.copies, m.parts_count, fmt(m.cut_length_m), m.cuts_count,
      fmt(m.fill_percent), fmt(m.offcuts.filter((o) => o.kind === "remnant" && o.business).reduce((a, o) => a + (o.length * o.width) / 1e6, 0), 3), m.packs ?? "", m.done_count ?? 0]));
}
