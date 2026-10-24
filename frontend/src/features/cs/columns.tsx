// «Детали» jadvali ustunlari: to'liq ro'yxat (UI_SPEC §5.2, «Настройки колонок»), profil bo'yicha tuziladi.
import type { ColDef, ITooltipParams, ValueFormatterParams } from "ag-grid-community";
import type { TFunction } from "i18next";
import type { Operation, Part, Project } from "../../api/types";
import { parseCellNum } from "../../shared/grid/Grid";
import { ListEditor, type ListOption } from "../../shared/grid/ListEditor";
import { chMin, chToPx } from "../../shared/grid/ColumnSettings";
import { PARAM_NAME_RE, type ExprVar, type UserCol, type UserColsSource } from "../../shared/grid/userColumns";
import { useUI } from "../../store/ui";
import { cx } from "../../shared/ui";
import { computeSizes, edgeParams, mapsOfPart, partMarks, productQty, totalQty } from "./sizes";

export const ALL_COLUMNS = [
  "num", "article", "name", "length", "width", "qty", "grain", "from_remnant", "edge_top", "edge_bottom", "edge_left", "edge_right",
  "product_name", "used", "left", "description", "code", "uid", "total", "minus", "group_by", "group_min", "group_max",
  "product_qty", "product_num", "part_num", "op_num", "blank_l", "blank_w", "detail_l", "detail_w", "jointed_l",
  "jointed_w", "saw_l", "saw_w", "allow_top", "allow_bottom", "allow_left", "allow_right", "groove_top",
  "groove_bottom", "groove_left", "groove_right", "surface_face", "surface_back", "xnc", "area",
  // onlayn tizimdagi qo'shimcha ustunlar: pazlash tomoni, ishlov belgilari (П / С / Ф), XNC 1…5 (kod, tomon, «по размеру детали»)
  "groove_top_side", "groove_bottom_side", "groove_left_side", "groove_right_side", "mark_groove", "mark_drill", "mark_mill",
  "xnc1", "xnc1_side", "xnc1_bsd", "xnc2", "xnc2_side", "xnc2_bsd", "xnc3", "xnc3_side", "xnc3_bsd",
  "xnc4", "xnc4_side", "xnc4_bsd", "xnc5", "xnc5_side", "xnc5_bsd",
] as const;
export type ColKey = (typeof ALL_COLUMNS)[number];

export const DEFAULT_VISIBLE: ColKey[] = ["num", "name", "length", "width", "qty", "grain", "edge_top", "edge_bottom",
  "edge_left", "edge_right", "code", "uid", "total"];

/** Standart kenglik — BELGILARDA (onlayn tizimdagi «Настройки» kabi; px = chToPx). Ro'yxatda yo'qlari — 8. */
const DEFAULT_CH: Partial<Record<ColKey, number>> = {
  num: 4, name: 35, length: 7, width: 7, qty: 5, grain: 5, from_remnant: 6, edge_top: 10, edge_bottom: 10, edge_left: 10, edge_right: 10,
  code: 12, uid: 7, total: 5, minus: 5, used: 5, left: 5, description: 35, product_name: 35, article: 8, group_by: 12,
  group_min: 6, group_max: 6, product_qty: 7,
};

export interface ColSetting { key: ColKey; visible: boolean; title?: string; width?: number; user?: UserCol }

/** «Настройки» oynasidagi standart tartib (xodimlarga tanish): ko'rinadiganlar, keyin МК, ИК, Ост, Описание, Изделие, Группировка… */
// «Из ост.» — standart yashirin (xodimlar o'rgangan TAB tartibi «Ткт» → «ОВ» o'zgarmasin); «Настройки» da yoqiladi
const DEFAULT_ORDER: ColKey[] = [...DEFAULT_VISIBLE, "minus", "used", "left", "from_remnant", "description", "product_name", "group_by"];

/** Ustunning standart kengligi (px) — «Ш-на» katagida ko'rsatiladi. */
export const defaultWidth = (k: string): number => DEFAULT_CH[k as ColKey] ?? 8;

/** Profil ma'lumoti → ustunlar (kenglik belgilarda). Eski profillar kenglikni px da saqlagan (`unit` yo'q) — belgiga o'giriladi
 *  (ko'rinish deyarli o'zgarmaydi: px ≈ belgi·12 + 6). Saqlashda `{ unit: "ch" }` qo'shiladi. */
export function partColsFromData(d?: { columns?: ColSetting[]; unit?: string } | null): ColSetting[] | undefined {
  if (!d?.columns) return undefined;
  if (d.unit === "ch") return d.columns;
  return d.columns.map((c) => (c.width && c.width > 0 ? { ...c, width: Math.max(1, Math.round((c.width - 6) / 12)) } : c));
}

export function defaultColumns(): ColSetting[] {
  const vis = new Set<string>(DEFAULT_VISIBLE);
  const head = new Set<string>(DEFAULT_ORDER);
  const order: ColKey[] = [...DEFAULT_ORDER, ...ALL_COLUMNS.filter((k) => !head.has(k))];
  return order.map((k) => ({ key: k, visible: vis.has(k) }));
}

/** Profil ustunlari (yangi qo'shilgan ustunlar oxiriga, yashirin). */
export function normalizeColumns(cols: ColSetting[] | undefined): ColSetting[] {
  if (!cols || !cols.length) return defaultColumns();
  const seen = new Set(cols.map((c) => c.key));
  const known = (c: ColSetting) => (c.user ? PARAM_NAME_RE.test(c.key) && !(ALL_COLUMNS as readonly string[]).includes(c.key)
    : (ALL_COLUMNS as readonly string[]).includes(c.key));
  return [...cols.filter(known),
    ...ALL_COLUMNS.filter((k) => !seen.has(k)).map((k) => ({ key: k, visible: false }))];
}

type Patch = (v: unknown, data: Part) => Record<string, unknown>;
export interface PartCol extends ColDef<Part> { context?: { patch?: Patch } }

export const NEW_ID = "__new__";
const isNew = (d?: Part) => d?.id === NEW_ID;

/** `buildUser` — foydalanuvchi ustunlari («Настроенный Параметры», «Выражение»; shared/grid/userColumns.tsx). */
export function buildColumns(t: TFunction, project: Project, op: Operation, settings: ColSetting[],
  buildUser?: (s: ColSetting) => ColDef<Part> | null): PartCol[] {
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
    // manfiy son qabul qilinmaydi (0 ga qisqartiriladi), soni — butun: server 422 ga yetib bormaydi (#12)
    valueParser: (pp) => { const v = parseCellNum(pp.newValue); return v === null ? pp.oldValue : (int ? Math.max(0, Math.round(v)) : Math.max(0, v)); },
    context: { patch: (v) => ({ [field]: v }) },
  });
  // detal o'lchami (Длина / Ширина): 0 yoki manfiy — jimgina 0 emas: eski qiymat qoladi va sabab xabarda ko'rsatiladi;
  // «Мин. размер детали» dan kichik / 0 o'lchamli katak — to'q sariq, sababi maslahatda (`partSizeIssue`)
  const sizeNum = (field: "length" | "width"): Partial<PartCol> => ({
    ...num(field),
    valueParser: (pp) => {
      const v = parseCellNum(pp.newValue);
      if (v === null) {
        if (String(pp.newValue ?? "").trim() !== "") useUI.getState().toast(`${t(`pp.${field}`)}: ${t("num.nan")}`, "warn");
        return pp.oldValue;
      }
      if (v <= 0 && sizeRule) { useUI.getState().toast(`${t(`pp.${field}`)}: ${t("parts.size_pos")}`, "warn"); return pp.oldValue; }
      return Math.max(0, v);
    },
    cellClass: (p) => cx("num strong", `sz-in-${mode}`, sizeRule && p.data && !isNew(p.data)
      && partSizeIssue(t, p.data, sizes(p.data), minPart, field) && "cell-warn"),
    headerClass: `hdr-sz-${mode}`,
  });
  const sizeRule = op.type !== "CL";
  const minPart = op.type === "CS" ? (op.cs_material?.min_part_size ?? 0) : 0;
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
    cellClass: "edge-cell clip",   // onlayndagidek: qator balandligi o'zgarmaydi, uzun kromka nomi qirqiladi (foydalanuvchi, 2026-10-21)
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
  const defs: Partial<Record<ColKey, Partial<PartCol>>> = {
    num: { colId: "num", pinned: "left", cellClass: "num rownum", sortable: false,
      valueGetter: (p) => (isNew(p.data) ? "*" : `${(p.node?.rowIndex ?? 0) + 1}${p.data?.xnc_op_ids.length ? "'" : ""}`) },
    article: { colId: "article", valueGetter: (p) => products.find((x) => x.id === p.data?.product_id)?.code ?? "" },
    // nom toza ko'rsatiladi (onlayn tizimdagidek); «= * %» ishlov belgilari faqat kroy kartalari / hisobotda (`sizes.partMarks`)
    name: { field: "name", editable: true, cellClass: "clip",
      valueFormatter: (p: ValueFormatterParams<Part>) => p.value ?? "", context: { patch: (v) => ({ name: v ?? "" }) } },
    // CS-082: sarlavha va qiymat rangi kiritish rejimiga qarab (zagotovka — ko'k, detal — yashil, prifugovkadan keyin — qizil kursiv)
    length: sizeNum("length"),
    width: sizeNum("width"),
    // soni 0 (ОК = 0) — kroyga kirmaydi: xira ko'rinish, sababi maslahatda
    qty: { ...num("qty", true), cellClass: (p) => cx("num", p.data && !isNew(p.data) && totalQty(project, p.data) <= 0 && "cell-zero") },
    grain: { field: "grain", editable: true, cellRenderer: "agCheckboxCellRenderer", cellEditor: "agCheckboxCellEditor",
      cellClass: "center", context: { patch: (v) => ({ grain: Boolean(v) }) } },
    // «Из ост.» (2026-10-24): belgilangan detal kroyda avval ro'yxatdagi qoldiq listlarga joylanadi, qolgani umumiy qoida bilan
    from_remnant: { field: "from_remnant", editable: true, cellRenderer: "agCheckboxCellRenderer", cellEditor: "agCheckboxCellEditor",
      cellClass: "center", valueGetter: (p) => Boolean(p.data?.from_remnant),
      valueSetter: (p) => { if (!p.data) return false; p.data.from_remnant = Boolean(p.newValue); return true; },
      context: { patch: (v) => ({ from_remnant: Boolean(v) }) } },
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
    uid: { field: "uid" },                              // ID — chapga, qora (onlayn ko'rinish)
    total: { colId: "total", cellClass: "num", valueGetter: (p) => (p.data && !isNew(p.data) ? totalQty(project, p.data) : null) },
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
      valueGetter: (p) => { if (!p.data || isNew(p.data)) return ""; const l = [...(partsByProduct.get(p.data.product_id ?? "") ?? [])].sort((x, y) => x.uid - y.uid);
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
    ...Object.fromEntries((["top", "bottom", "left", "right"] as const).map((side) => [`groove_${side}_side`, {
      colId: `groove_${side}_side`, editable: true, cellEditor: ListEditor, cellEditorPopup: true,
      cellEditorParams: { options: [{ value: "face", label: t("pc.side_face") }, { value: "back", label: t("pc.side_back") }] },
      refData: { face: t("pc.side_face"), back: t("pc.side_back") },
      valueGetter: (p: { data?: Part }) => (p.data?.[`groove_${side}`]?.op_id ? (p.data[`groove_${side}`].back_side ? "back" : "face") : ""),
      context: { patch: (v: unknown, d: Part) => ({ [`groove_${side}`]: { ...(d[`groove_${side}`] ?? { op_id: null }), back_side: v === "back" } }) },
    } as PartCol])),
    mark_groove: { colId: "mark_groove", valueGetter: (p) => (p.data && !isNew(p.data) && partMarks(project, p.data).includes("=") ? "✓" : "") },
    mark_drill: { colId: "mark_drill", valueGetter: (p) => (p.data && !isNew(p.data) && partMarks(project, p.data).includes("%") ? "✓" : "") },
    mark_mill: { colId: "mark_mill", valueGetter: (p) => (p.data && !isNew(p.data) && partMarks(project, p.data).includes("*") ? "✓" : "") },
    ...Object.fromEntries([1, 2, 3, 4, 5].flatMap((i) => {
      const xop = (d?: Part) => { const id = d?.xnc_op_ids?.[i - 1]; return id ? project.operations.find((o) => o.id === id) : undefined; };
      return [
        [`xnc${i}`, { colId: `xnc${i}`, valueGetter: (p: { data?: Part }) => xop(p.data)?.code ?? "" } as PartCol],
        [`xnc${i}_side`, { colId: `xnc${i}_side`, valueGetter: (p: { data?: Part }) => { const x = xop(p.data)?.xnc; return x ? t(x.face_side ? "pc.side_face" : "pc.side_back") : ""; } } as PartCol],
        [`xnc${i}_bsd`, { colId: `xnc${i}_bsd`, valueGetter: (p: { data?: Part }) => (xop(p.data)?.xnc?.by_part_size ? "✓" : "") } as PartCol],
      ];
    })),
    area: { colId: "area", cellClass: "num", valueGetter: (p) => {
      if (!p.data || isNew(p.data)) return null;
      const s = sizes(p.data).saw;                       // jadval ostidagi «Площадь» bilan bir xil asos (zagotovka + pripusk)
      return Math.round((s[0] * s[1] * totalQty(project, p.data)) / 1e3) / 1e3;
    } },
  };
  const out: PartCol[] = [];
  for (const s of settings) {
    if (!s.visible) continue;
    if (s.user) {
      const u = buildUser?.(s);
      if (u) { const ch = s.width && s.width > 0 ? s.width : 10; out.push({ ...u, flex: ch, minWidth: chMin(ch) } as PartCol); }
      continue;
    }
    const d = defs[s.key];
    if (!d) continue;
    const col = {
      colId: s.key, headerName: s.title || t(`pc.${s.key}`), headerTooltip: t(`pcd.${s.key}`),
      ...d,
    } as PartCol;
    // onlayn tizimdagidek: kenglik (belgilar) — jadval eniga mutanosib cho'zilish ulushi
    { const ch = s.width && s.width > 0 ? s.width : defaultWidth(s.key);
      if (s.key === "num") { col.width = chToPx(ch); delete col.flex; }        // «№» — chapga mahkamlangan, kengligi o'zgarmas
      else { delete col.width; col.flex = ch; col.minWidth = chMin(ch); } }

    out.push(col);
  }
  return out;
}

/** Qator ustidagi maslahat: mahsulot, raqamlar, 4 xil o'lcham. */
/** Detal o'lchami muammosi (yo'q bo'lsa — null): 0 / manfiy o'lcham yoki «Мин. размер детали» dan kichik (pilniy o'lcham bo'yicha,
 *  guruhlanmagan detal). `field` berilsa — faqat shu o'lcham (katak rangi uchun). */
export function partSizeIssue(t: TFunction, d: Part, s: ReturnType<typeof computeSizes>, minPart: number,
  field?: "length" | "width"): string | null {
  const dims: ["length" | "width", number, number][] = [["length", d.length, s.saw[0]], ["width", d.width, s.saw[1]]];
  for (const [k, v, saw] of dims) {
    if (field && k !== field) continue;
    if (!(v > 0)) return t("parts.size_zero", { what: t(`pp.${k}`) });
    if (minPart > 0 && d.group_by === "none" && saw > 0 && saw < minPart - 1e-9)
      return t("parts.size_small", { what: t(`pp.${k}`), v: Math.round(saw * 100) / 100, mm: minPart });
  }
  return null;
}

export function partTooltip(t: TFunction, project: Project, op: Operation) {
  const edges = edgeParams(project);
  return (p: ITooltipParams<Part>): string => {
    const d = p.data;
    if (!d || d.id === NEW_ID) return "";
    const s = computeSizes(d, project.size_mode, edges, op.cs_cut?.machining_allowance ?? 0);
    const prod = project.products.find((x) => x.id === d.product_id);
    const same = project.operations.flatMap((o) => o.parts).filter((x) => x.product_id === d.product_id)
      .sort((x, y) => x.uid - y.uid);   // «№ в изделии»: mahsulot detallari ID tartibida (onlayn tizimdagidek)
    const f = (a: [number, number]) => `${a[0]} × ${a[1]}`;
    const issue = op.type !== "CL" ? partSizeIssue(t, d, s, op.type === "CS" ? (op.cs_material?.min_part_size ?? 0) : 0) : null;
    const left = op.result && d.left_qty > 0 ? t("parts.left_tip", { n: d.left_qty }) : null;
    const zero = totalQty(project, d) <= 0 ? t("parts.qty_zero") : null;
    const notes = [issue, zero, left].filter(Boolean).map((x) => `⚠ ${x}`);
    return [
      ...(notes.length ? [...notes, ""] : []),
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

// ───────────────────────── foydalanuvchi ustunlari: ifoda o'zgaruvchilari ─────────────────────────
/** Detal maydonlari → ifoda o'zgaruvchilari (kalit va rus qisqa nomi: «qty» / «Кол»). */
const PART_VARS: [string, string | null][] = [
  ["length", "Длина"], ["width", "Ширина"], ["qty", "Кол"], ["minus", "МК"], ["total", "ОК"], ["used", "ИК"], ["left", "Ост"],
  ["grain", "Ткт"], ["name", "Наименование"], ["code", "Код"], ["description", "Описание"], ["uid", "ID"],
  ["product_name", "Изделие"], ["product_qty", null], ["product_num", null],
];

/** «Vs» ro'yxati (detallar jadvallari). */
export function partVarList(t: TFunction): ExprVar[] {
  return PART_VARS.flatMap(([k, alias]) => {
    const label = t(`pc.${k}`);
    return [{ name: k, label }, ...(alias ? [{ name: alias, label }] : [])];
  });
}

/** Detal qatorining ifoda konteksti (o'rnatilgan o'zgaruvchilar). */
export function partVars(project: Project, p: Part): Record<string, unknown> {
  const pi = project.products.findIndex((x) => x.id === p.product_id);
  const prod = pi >= 0 ? project.products[pi] : undefined;
  const v: Record<string, unknown> = {
    length: p.length, width: p.width, qty: p.qty, minus: p.minus_qty, total: totalQty(project, p), used: p.used_qty,
    left: p.left_qty, grain: p.grain, name: p.name, code: p.code, description: p.description, uid: p.uid,
    product_name: prod?.name ?? "", product_qty: productQty(project, p), product_num: pi >= 0 ? pi + 1 : 0,
  };
  for (const [k, alias] of PART_VARS) if (alias) v[alias] = v[k];
  return v;
}

/** Detallar jadvali (CS / CL / CN) uchun foydalanuvchi ustunlari manbai (prefiks «part»). */
export function partsUserSource(t: TFunction, project: Project, rows: Part[]): UserColsSource<Part> {
  return {
    prefix: "part", rows, rowKey: (r) => r.id, params: (r) => r.user_params,
    setParams: (r, next) => { r.user_params = next; },
    vars: (r) => partVars(project, r), varList: partVarList(t),
  };
}
