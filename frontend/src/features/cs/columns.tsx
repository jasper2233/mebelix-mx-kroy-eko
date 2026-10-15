// «Детали» jadvali ustunlari: to'liq ro'yxat (UI_SPEC §5.2, «Настройки колонок»), profil bo'yicha tuziladi.
import type { ColDef, ITooltipParams, ValueFormatterParams } from "ag-grid-community";
import type { TFunction } from "i18next";
import type { Operation, Part, Project } from "../../api/types";
import { parseCellNum } from "../../shared/grid/Grid";
import { ListEditor, type ListOption } from "../../shared/grid/ListEditor";
import { computeSizes, edgeParams, mapsOfPart, productQty, totalQty } from "./sizes";

export const ALL_COLUMNS = [
  "num", "article", "name", "length", "width", "qty", "grain", "edge_top", "edge_bottom", "edge_left", "edge_right",
  "product_name", "used", "left", "description", "code", "uid", "total", "minus", "group_by", "group_min", "group_max",
  "product_qty", "product_num", "part_num", "op_num", "blank_l", "blank_w", "detail_l", "detail_w", "jointed_l",
  "jointed_w", "saw_l", "saw_w", "allow_top", "allow_bottom", "allow_left", "allow_right", "groove_top",
  "groove_bottom", "groove_left", "groove_right", "surface_face", "surface_back", "xnc", "area",
] as const;
export type ColKey = (typeof ALL_COLUMNS)[number];

export const DEFAULT_VISIBLE: ColKey[] = ["num", "name", "length", "width", "qty", "grain", "edge_top", "edge_bottom",
  "edge_left", "edge_right", "code", "uid", "total"];

const DEFAULT_WIDTH: Partial<Record<ColKey, number>> = {
  num: 42, name: 260, length: 62, width: 62, qty: 50, grain: 40, edge_top: 110, edge_bottom: 110, edge_left: 110,
  edge_right: 110, code: 100, uid: 52, total: 48, description: 180, product_name: 160, article: 80,
};

export interface ColSetting { key: ColKey; visible: boolean; title?: string; width?: number }

export function defaultColumns(): ColSetting[] {
  const vis = new Set<string>(DEFAULT_VISIBLE);
  const order: ColKey[] = [...DEFAULT_VISIBLE, ...ALL_COLUMNS.filter((k) => !vis.has(k))];
  return order.map((k) => ({ key: k, visible: vis.has(k) }));
}

/** Profil ustunlari (yangi qo'shilgan ustunlar oxiriga, yashirin). */
export function normalizeColumns(cols: ColSetting[] | undefined): ColSetting[] {
  if (!cols || !cols.length) return defaultColumns();
  const seen = new Set(cols.map((c) => c.key));
  return [...cols.filter((c) => (ALL_COLUMNS as readonly string[]).includes(c.key)),
    ...ALL_COLUMNS.filter((k) => !seen.has(k)).map((k) => ({ key: k, visible: false }))];
}

type Patch = (v: unknown, data: Part) => Record<string, unknown>;
export interface PartCol extends ColDef<Part> { context?: { patch?: Patch } }

export const NEW_ID = "__new__";
const isNew = (d?: Part) => d?.id === NEW_ID;

export function buildColumns(t: TFunction, project: Project, op: Operation, settings: ColSetting[]): PartCol[] {
  const els = project.operations.filter((o) => o.type === "EL");
  const grs = project.operations.filter((o) => o.type === "GR");
  const edges = edgeParams(project);
  const mode = project.size_mode;
  const allowance = op.cs_cut?.machining_allowance ?? 0;
  const products = project.products;
  const partsByProduct = new Map<string, Part[]>();
  for (const o of project.operations) for (const p of o.parts) {
    const k = p.product_id ?? "";
    partsByProduct.set(k, [...(partsByProduct.get(k) ?? []), p]);
  }
  const sizes = (p: Part) => computeSizes(p, mode, edges, allowance);
  const num = (field: keyof Part, int = false): Partial<PartCol> => ({
    field, editable: true, cellClass: "num",
    valueParser: (pp) => { const v = parseCellNum(pp.newValue); return v === null ? pp.oldValue : (int ? Math.max(0, Math.round(v)) : v); },
    context: { patch: (v) => ({ [field]: v }) },
  });
  const edgeRef: Record<string, string> = { "": "" };
  els.forEach((o) => { edgeRef[o.id] = o.name || o.code || o.el?.symbol || o.id; });
  const grRef: Record<string, string> = { "": "" };
  grs.forEach((o) => { grRef[o.id] = o.name || o.code || o.id; });
  const edgeOpts: ListOption[] = [{ value: "", label: "—" }, ...els.map((o) => ({
    value: o.id, label: `${o.el?.symbol ?? ""}  ${o.name || o.code}`, key: o.el?.symbol,
    color: o.el?.color && o.el.color !== "#000000" ? o.el.color : "#1b2733" }))];
  const grOpts: ListOption[] = [{ value: "", label: "—" }, ...grs.map((o) => ({ value: o.id, label: o.name || o.code || "GR" }))];
  const edgeCol = (side: "top" | "bottom" | "left" | "right"): Partial<PartCol> => ({
    colId: `edge_${side}`, editable: true, cellEditor: ListEditor, cellEditorPopup: true,
    cellEditorParams: { options: edgeOpts }, refData: edgeRef,
    valueGetter: (p) => p.data?.[`edge_${side}`]?.op_id ?? "",
    valueSetter: (p) => { if (!p.data) return false; p.data[`edge_${side}`] = { op_id: p.newValue || null }; return true; },
    cellClass: "edge-cell wrap", wrapText: true, autoHeight: true,   // uzun kromka nomi to'liq ko'rinadi (qator balandlashadi)
    cellStyle: (p) => { const e = p.value ? edges.get(p.value as string) : undefined;
      return e && e.color && e.color !== "#000000" ? { color: e.color } : null; },
    context: { patch: (v) => ({ [`edge_${side}`]: { op_id: v || null } }) },
  });
  const grooveCol = (side: "top" | "bottom" | "left" | "right"): Partial<PartCol> => ({
    colId: `groove_${side}`, editable: true, cellEditor: ListEditor, cellEditorPopup: true,
    cellEditorParams: { options: grOpts }, refData: grRef,
    valueGetter: (p) => p.data?.[`groove_${side}`]?.op_id ?? "",
    valueSetter: (p) => { if (!p.data) return false; p.data[`groove_${side}`] = { ...p.data[`groove_${side}`], op_id: p.newValue || null }; return true; },
    context: { patch: (v, d) => ({ [`groove_${side}`]: { ...(d[`groove_${side}`] ?? { back_side: false }), op_id: v || null } }) },
  });
  // (SP) Обработка поверхности: lits / orqa tomon uchun SP operatsiyasi (W12; ustun ixtiyoriy, EL ustunlari kabi)
  const sps = project.operations.filter((o) => o.type === "SP");
  const spRef: Record<string, string> = { "": "" };
  sps.forEach((o) => { spRef[o.id] = o.name || o.code || o.id; });
  const spOpts: ListOption[] = [{ value: "", label: "—" }, ...sps.map((o) => ({ value: o.id, label: o.name || o.code || "SP" }))];
  const surfaceCol = (colId: string, field: "surface_face_op" | "surface_back_op"): Partial<PartCol> => ({
    colId, editable: true, cellEditor: ListEditor, cellEditorPopup: true, cellEditorParams: { options: spOpts }, refData: spRef,
    valueGetter: (p) => p.data?.[field] ?? "",
    valueSetter: (p) => { if (!p.data) return false; p.data[field] = p.newValue || null; return true; },
    context: { patch: (v) => ({ [field]: v || null }) },
  });
  const sizeCol = (kind: "blank" | "detail" | "jointed" | "saw", i: 0 | 1): Partial<PartCol> => ({
    cellClass: `num size-${kind}`,
    valueGetter: (p) => (p.data && !isNew(p.data) ? sizes(p.data)[kind][i] : null),
  });
  const defs: Record<ColKey, Partial<PartCol>> = {
    num: { colId: "num", pinned: "left", cellClass: "num rownum", sortable: false,
      valueGetter: (p) => (isNew(p.data) ? "*" : `${(p.node?.rowIndex ?? 0) + 1}${p.data?.xnc_op_ids.length ? "'" : ""}`) },
    article: { colId: "article", valueGetter: (p) => products.find((x) => x.id === p.data?.product_id)?.code ?? "" },
    // nom toza ko'rsatiladi (onlayn tizimdagidek); «= * %» ishlov belgilari faqat kroy kartalari / hisobotda (`sizes.partMarks`)
    name: { field: "name", editable: true, cellClass: "wrap",
      valueFormatter: (p: ValueFormatterParams<Part>) => p.value ?? "", context: { patch: (v) => ({ name: v ?? "" }) } },
    // CS-082: sarlavha va qiymat rangi kiritish rejimiga qarab (zagotovka — ko'k, detal — yashil, prifugovkadan keyin — qizil kursiv)
    length: { ...num("length"), cellClass: `num strong sz-in-${mode}`, headerClass: `hdr-sz-${mode}` },
    width: { ...num("width"), cellClass: `num strong sz-in-${mode}`, headerClass: `hdr-sz-${mode}` },
    qty: num("qty", true),
    grain: { field: "grain", editable: true, cellRenderer: "agCheckboxCellRenderer", cellEditor: "agCheckboxCellEditor",
      cellClass: "center", context: { patch: (v) => ({ grain: Boolean(v) }) } },
    edge_top: edgeCol("top"), edge_bottom: edgeCol("bottom"), edge_left: edgeCol("left"), edge_right: edgeCol("right"),
    product_name: { colId: "product_name", editable: true, cellEditor: ListEditor, cellEditorPopup: true,
      cellEditorParams: { options: products.map((x, i) => ({ value: x.id, label: `№${i + 1} ${x.name}` })) },
      refData: Object.fromEntries(products.map((x, i) => [x.id, `№${i + 1} ${x.name}`])),
      valueGetter: (p) => p.data?.product_id ?? "",
      valueSetter: (p) => { if (!p.data) return false; p.data.product_id = p.newValue || null; return true; },
      context: { patch: (v) => ({ product_id: v || null }) } },
    used: { field: "used_qty", cellClass: "num" },
    left: { field: "left_qty", cellClass: (p) => (p.value > 0 ? "num warn" : "num") },
    description: { field: "description", editable: true, context: { patch: (v) => ({ description: v ?? "" }) } },
    code: { field: "code", editable: true, context: { patch: (v) => ({ code: v ?? "" }) } },
    uid: { field: "uid", cellClass: "num muted" },
    total: { colId: "total", cellClass: "num strong", valueGetter: (p) => (p.data && !isNew(p.data) ? totalQty(project, p.data) : null) },
    minus: { ...num("minus_qty", true), colId: "minus" },
    group_by: { field: "group_by", editable: true, cellEditor: ListEditor, cellEditorPopup: true,
      cellEditorParams: { options: (["none", "length", "width"] as const).map((v) => ({ value: v, label: t(`pp.group.${v}`) })) },
      refData: { none: t("pp.group.none"), length: t("pp.group.length"), width: t("pp.group.width") },
      context: { patch: (v) => ({ group_by: v || "none" }) } },
    group_min: num("group_min", true),
    group_max: num("group_max", true),
    product_qty: { colId: "product_qty", cellClass: "num", valueGetter: (p) => (p.data && !isNew(p.data) ? productQty(project, p.data) : null) },
    product_num: { colId: "product_num", cellClass: "num",
      valueGetter: (p) => { const i = products.findIndex((x) => x.id === p.data?.product_id); return i >= 0 ? i + 1 : ""; } },
    part_num: { colId: "part_num", cellClass: "num",
      valueGetter: (p) => { if (!p.data || isNew(p.data)) return ""; const l = partsByProduct.get(p.data.product_id ?? "") ?? [];
        return l.findIndex((x) => x.id === p.data!.id) + 1; } },
    op_num: { colId: "op_num", cellClass: "num", valueGetter: (p) => (isNew(p.data) ? "" : (p.node?.rowIndex ?? 0) + 1) },
    blank_l: sizeCol("blank", 0), blank_w: sizeCol("blank", 1), detail_l: sizeCol("detail", 0), detail_w: sizeCol("detail", 1),
    jointed_l: sizeCol("jointed", 0), jointed_w: sizeCol("jointed", 1), saw_l: sizeCol("saw", 0), saw_w: sizeCol("saw", 1),
    allow_top: num("allow_top"), allow_bottom: num("allow_bottom"), allow_left: num("allow_left"), allow_right: num("allow_right"),
    groove_top: grooveCol("top"), groove_bottom: grooveCol("bottom"), groove_left: grooveCol("left"), groove_right: grooveCol("right"),
    surface_face: surfaceCol("surface_face", "surface_face_op"),
    surface_back: surfaceCol("surface_back", "surface_back_op"),
    xnc: { colId: "xnc", valueGetter: (p) => (p.data?.xnc_op_ids ?? []).map((id) =>
      project.operations.find((o) => o.id === id)?.code ?? "").filter(Boolean).join(", ") },
    area: { colId: "area", cellClass: "num", valueGetter: (p) => {
      if (!p.data || isNew(p.data)) return null;
      const s = sizes(p.data).saw;                       // jadval ostidagi «Площадь» bilan bir xil asos (zagotovka + pripusk)
      return Math.round((s[0] * s[1] * totalQty(project, p.data)) / 1e3) / 1e3;
    } },
  };
  const out: PartCol[] = [];
  for (const s of settings) {
    if (!s.visible) continue;
    const d = defs[s.key];
    if (!d) continue;
    const col = {
      colId: s.key, headerName: s.title || t(`pc.${s.key}`), headerTooltip: t(`pcd.${s.key}`),
      width: s.width ?? DEFAULT_WIDTH[s.key] ?? 70, ...d,
    } as PartCol;
    // «детал номи» bo'sh joyni egallaydi — jadval butun kenglikka cho'ziladi (profilda kenglik berilgan bo'lsa — o'sha)
    if (s.key === "name" && !s.width) { delete col.width; col.flex = 1; col.minWidth = 200; }
    out.push(col);
  }
  return out;
}

/** Qator ustidagi maslahat: mahsulot, raqamlar, 4 xil o'lcham. */
export function partTooltip(t: TFunction, project: Project, op: Operation) {
  const edges = edgeParams(project);
  return (p: ITooltipParams<Part>): string => {
    const d = p.data;
    if (!d || d.id === NEW_ID) return "";
    const s = computeSizes(d, project.size_mode, edges, op.cs_cut?.machining_allowance ?? 0);
    const prod = project.products.find((x) => x.id === d.product_id);
    const same = project.operations.flatMap((o) => o.parts).filter((x) => x.product_id === d.product_id);
    const f = (a: [number, number]) => `${a[0]} × ${a[1]}`;
    return [
      `${t("tip.product")}: ${prod ? prod.name : "—"}`,
      `${t("tip.num_in_product")}: ${same.findIndex((x) => x.id === d.id) + 1}`,
      `${t("tip.num_in_cut")}: ${mapsOfPart(op, d.id).join(", ") || "—"}`,
      `id: ${d.uid}`,
      `${t("tip.detail")}: ${f(s.detail)}`,
      `${t("tip.jointed")}: ${f(s.jointed)}`,
      `${t("tip.blank")}: ${f(s.blank)}`,
      `${t("tip.saw")}: ${f(s.saw)}`,
    ].join("\n");
  };
}
