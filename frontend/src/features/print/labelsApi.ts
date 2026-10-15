// LB (etiketkalar): shablon turlari, standart parametrlar, so'rov hooklari (backend: app/api_labels.py).
import { useQuery } from "@tanstack/react-query";
import { get } from "../../api/client";
import type { LBParams } from "../../api/types";

export interface TplParam { name: string; type: "double" | "integer" | "string" | "boolean"; default?: unknown; title?: string }
export interface TplElement { t: string; [k: string]: unknown }
export interface TplVar { name: string; expr: string }
export interface LabelTemplate {
  v: number; name: string; size: { w: number; h: number }; params: TplParam[]; vars: TplVar[]; elements: TplElement[];
  layout?: GlLayout | null;      // fayldan import qilingan shablon: sahifa joylashuvi maslahati (columns/rows/gap/margin/mode)
}
/** Tayyor shablon fayli (W9): sahifa joylashuvi — `LBParams` maydon nomlari bilan. */
export interface GlLayout { mode: "sheet" | "roll"; columns: number; rows: number; gap_mm: number; margin_mm: number | null }
export interface GlWarning { code: string; key: string; count: number; message: string }
export interface GlItem {
  index: number; source: string; name: string; ops: number; template: LabelTemplate; size: { w: number; h: number };
  layout: GlLayout | null; warnings: GlWarning[]; errors: LabelIssue[];
  info: { elements: number; params: number; vars: number; images: number; std_pars: number };
}
export interface GlImport { filename: string; kind: "program" | "project"; items: GlItem[]; skipped: { source: string; error: string }[]; more: number }
export interface TplMeta {
  id: string; key: string | null; name: string; builtin: boolean; kind: string; size: { w: number; h: number };
  params: TplParam[]; profile_id?: number; is_default?: boolean;
}
export interface LabelIssue { path: string; field: string; expr: string; message: string; count?: number; label?: number }
export interface LbCounts { total: number; parts: number; wastes: number; products: number; user: number }
export interface LbPreview {
  html: string; total: number; rendered: number; pages: number; counts: LbCounts; errors: LabelIssue[]; warnings: string[];
  template: string; template_name: string; truncated: boolean; max_labels: number;
}
export interface LabelVars {
  groups: { key: string; vars: { name: string; type: string; title: string }[] }[];
  functions: { group: string; name: string; sig: string }[]; aliases: string[]; max_labels: number;
}

/** Backend `LBParams` standarti bilan bir xil (yangi LB operatsiyasi va «Печать → Этикетки» boshlang'ich holati). */
export const DEFAULT_LB: LBParams = {
  source: "parts", mode: "sheet", rotate_page: 0, width_mm: 58, height_mm: 40, columns: 3, rows: 0, gap_mm: 2, margin_mm: 6,
  border: true, border_mode: null, part_selected_only: null, cs_op_id: null, print_parts: true, part_each: true, part_only_nonzero: true, part_selected: [], label_count: 1,
  print_wastes: false, waste_each: true, waste_business_only: false, product_each: false, product_only_nonzero: true,
  template_id: null, template: null, params: {}, fields: [], data: [], legacy_program: "",
};

/** «Границы»: amaldagi tur (eski ma'lumotda `border_mode` yo'q — `border` bayrog'idan). */
export const borderKind = (lb: LBParams): "none" | "perimeter" => lb.border_mode ?? (lb.border ? "perimeter" : "none");
/** «Выбранные детали» katakchasi (eski ma'lumotda — ro'yxat bo'sh bo'lmasa yoqiq). */
export const selectedOnly = (lb: LBParams): boolean => lb.part_selected_only ?? lb.part_selected.length > 0;

export const DEFAULT_TEMPLATE_ID = "builtin:detail";

export const useTemplates = (lang: string) =>
  useQuery({ queryKey: ["label-templates", lang], queryFn: () => get<TplMeta[]>("/label-templates", { lang }) });

export const useTemplate = (id: string | null, lang: string) =>
  useQuery({
    queryKey: ["label-template", id, lang],
    queryFn: () => get<{ id: string; name: string; builtin: boolean; template: LabelTemplate }>(`/label-templates/${id}`, { lang }),
    enabled: !!id,
  });

export const useLabelVars = (lang: string) =>
  useQuery({ queryKey: ["label-vars", lang], queryFn: () => get<LabelVars>("/label-variables", { lang }), staleTime: 600_000 });

/** Element yo'li (backend xato yo'li bilan bir xil format): [1] → «2», [1,"then",0] → «2.then.1». */
export type ElPath = (number | string)[];
export const pathLabel = (p: ElPath): string => p.map((x) => (typeof x === "number" ? String(x + 1) : x)).join(".");

export const CHILD_KEYS = ["elements", "then", "else"] as const;

export interface FlatEl { path: ElPath; label: string; depth: number; el: TplElement }

export function flatten(els: TplElement[], base: ElPath = [], depth = 0): FlatEl[] {
  const out: FlatEl[] = [];
  els.forEach((el, i) => {
    const path = [...base, i];
    out.push({ path, label: pathLabel(path), depth, el });
    for (const k of CHILD_KEYS) {
      const ch = el[k];
      if (Array.isArray(ch)) out.push(...flatten(ch as TplElement[], [...path, k], depth + 1));
    }
  });
  return out;
}

/** Shablonning chuqur nusxasida yo'l bo'yicha ro'yxatni topadi: [ro'yxat, ro'yxatdagi indeks]. */
export function locate(tpl: LabelTemplate, path: ElPath): [TplElement[], number] | null {
  let list: TplElement[] = tpl.elements;
  for (let i = 0; i < path.length - 1; i += 2) {
    const el = list[path[i] as number];
    const key = path[i + 1] as string;
    const next = el?.[key];
    if (!Array.isArray(next)) return null;
    list = next as TplElement[];
  }
  return [list, path[path.length - 1] as number];
}

export const cloneTpl = (t: LabelTemplate): LabelTemplate => JSON.parse(JSON.stringify(t)) as LabelTemplate;

/** Ustun xaritasi: elementning qaysi maydonlari jadvaldagi x, y, o'lcham (a, b) va ifoda ustunlariga to'g'ri keladi. */
export function fieldMap(el: TplElement): { x?: string; y?: string; a?: string; b?: string; e?: string } {
  switch (el.t) {
    case "text": return { x: "x", y: "y", a: "size", e: "text" };
    case "rect": case "image": case "part": case "edges": return { x: "x", y: "y", a: "w", b: "h" };
    case "line": return { x: "x1", y: "y1", a: "x2", b: "y2" };
    case "barcode": return String(el.kind ?? "qr").toLowerCase() === "code128"
      ? { x: "x", y: "y", a: "w", b: "h", e: "data" } : { x: "x", y: "y", a: "size", e: "data" };
    case "group": return { x: "origin.0", y: "origin.1", a: "rotate" };
    case "if": return { e: "cond" };
    case "var": return { x: "name", e: "expr" };
    case "arc": return { x: "cx", y: "cy", a: "r", b: "a2" };
    case "ellipse": return { x: "cx", y: "cy", a: "rx", b: "ry" };
    default: return {};
  }
}

export function getField(el: TplElement, key: string): string {
  if (key.startsWith("origin.")) {
    const o = el.origin;
    const v = Array.isArray(o) ? o[Number(key.slice(7))] : undefined;
    return v === undefined || v === null ? "" : String(v);
  }
  const v = el[key];
  if (v === undefined || v === null) return "";
  return typeof v === "object" ? JSON.stringify(v) : String(v);
}

const NUM_RE = /^-?\d+(\.\d+)?$/;

/** Qiymatni elementga yozish: raqamga o'xshash matn — son (JSON toza chiqadi); ifoda maydonlari (`isExpr`) matn bo'lib qoladi. */
export function setField(el: TplElement, key: string, raw: string, isExpr: boolean): void {
  const val: string | number = !isExpr && NUM_RE.test(raw.trim()) ? Number(raw.trim()) : raw;
  if (key.startsWith("origin.")) {
    const o = Array.isArray(el.origin) ? [...(el.origin as unknown[])] : [0, 0];
    o[Number(key.slice(7))] = val;
    el.origin = o;
    return;
  }
  el[key] = val;
}

export const NEW_ELEMENTS: Record<string, TplElement> = {
  text: { t: "text", x: 2, y: 2, size: 3, text: "'Text'" },
  rect: { t: "rect", x: 1, y: 1, w: 20, h: 10, stroke: { w: 0.2 } },
  line: { t: "line", x1: 1, y1: 10, x2: 40, y2: 10, stroke: { w: 0.2 } },
  qr: { t: "barcode", kind: "qr", x: 2, y: 10, size: 15, data: "part.qr" },
  code128: { t: "barcode", kind: "code128", x: 2, y: 28, w: 50, h: 9, caption: true, data: "project.number" },
  part: { t: "part", x: 30, y: 5, w: 20, h: 14 },
  edges: { t: "edges", x: 40, y: 5, w: 14, h: 9 },
  if: { t: "if", cond: "true", then: [] },
  group: { t: "group", rotate: 90, origin: [10, 10], elements: [] },
  var: { t: "var", name: "v1", expr: "1" },
  // W15 (LB-D): chizma elementlari
  polyline: { t: "polyline", points: [[4, 20], [14, 12], [24, 20], [34, 12]], stroke: { w: 0.3 } },
  arc: { t: "arc", cx: 20, cy: 20, r: 8, a1: 0, a2: 180, stroke: { w: 0.3 } },
  ellipse: { t: "ellipse", cx: 24, cy: 16, rx: 10, ry: 6, stroke: { w: 0.3 } },
};
