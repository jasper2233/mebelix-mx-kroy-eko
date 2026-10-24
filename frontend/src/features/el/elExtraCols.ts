// EL «Детали»: onlayn tizimdagi qo'shimcha ustunlar (standart yashirin, «Настройки» / Ctrl+P orqali yoqiladi) — mahsulot, detal
// raqamlari, o'lchamlar (zagotovka / detal / prifugovka / arra), pripusklar, ishlov belgilari va har tomon kromkasi xossalari.
// Qiymatlar qator detalidan (part_id) hisoblanadi; nomlar — i18n `elx.*`.
import type { ColDef } from "ag-grid-community";
import type { TFunction } from "i18next";
import type { ColSpec } from "../../shared/grid/ColumnSettings";
import type { ELParams, EdgeUsage, Operation, Part, Project } from "../../api/types";
import { computeSizes, edgeParams, partMarks } from "../cs/sizes";

type Row = EdgeUsage["rows"][number];
const SIDES = ["top", "bottom", "left", "right"] as const;

/** Katalog: kalit, nom / tavsif (i18n), kenglik (belgilarda — onlayn «Настройки» raqamlari), standart yashirin. */
export const EL_EXTRA_SPECS: ColSpec[] = [
  { key: "product_code", name: "elx.product_code", desc: "elx.product_code_d", width: 20 },
  { key: "product_name", name: "elx.product_name", desc: "elx.product_name_d", width: 35 },
  { key: "product_num", name: "elx.product_num", desc: "elx.product_num_d", width: 5 },
  { key: "product_qty", name: "elx.product_qty", desc: "elx.product_qty_d", width: 7 },
  { key: "uid", name: "elx.uid", desc: "elx.uid_d", width: 7 },
  { key: "code", name: "elx.code", desc: "elx.code", width: 12 },
  { key: "grain", name: "elx.grain", desc: "elx.grain_d", width: 5 },
  { key: "description", name: "elx.description", desc: "elx.description_d", width: 35 },
  { key: "part_num", name: "elx.part_num", desc: "elx.part_num_d", width: 5 },
  { key: "op_num", name: "elx.op_num", desc: "elx.op_num_d", width: 5 },
  { key: "part_qty", name: "elx.part_qty", desc: "elx.part_qty_d", width: 9 },
  { key: "used", name: "elx.used", desc: "elx.used_d", width: 7 },
  { key: "left", name: "elx.left", desc: "elx.left_d", width: 7 },
  ...(["blank", "detail", "jointed", "saw"] as const).flatMap((k) => [
    { key: `${k}_l`, name: `elx.${k}_l`, desc: `elx.${k}_l_d`, width: 12 },
    { key: `${k}_w`, name: `elx.${k}_w`, desc: `elx.${k}_w_d`, width: 12 }]),
  ...SIDES.map((s) => ({ key: `allow_${s}`, name: `elx.allow_${s}`, desc: `elx.allow_${s}_d`, width: 7 })),
  { key: "drill", name: "elx.drill", desc: "elx.drill_d", width: 5 },
  { key: "mill", name: "elx.mill", desc: "elx.mill_d", width: 5 },
  { key: "groove", name: "elx.groove", desc: "elx.groove_d", width: 5 },
  ...SIDES.flatMap((s) => (["code", "name", "sym", "th", "w", "joint"] as const).map((f) => ({
    key: `e_${s}_${f}`, name: `elx.e_${s}_${f}`, desc: `elx.e_${s}_${f}_d`, width: f === "sym" ? 5 : f === "name" ? 15 : 12 }))),
].map((x) => ({ ...x, visible: false }));

/** Ustunlar ta'rifi (colId = katalog kaliti). */
export function elExtraCols(t: TFunction, project: Project): ColDef<Row>[] {
  const partOf = new Map<string, { op: Operation; part: Part; idx: number }>();
  for (const o of project.operations) o.parts.forEach((p, i) => partOf.set(p.id, { op: o, part: p, idx: i }));
  const edges = edgeParams(project);
  const elOp = new Map<string, Operation>(project.operations.filter((o) => o.type === "EL").map((o) => [o.id, o]));
  const byProduct = new Map<string, Part[]>();
  for (const o of project.operations) for (const p of o.parts) {
    const k = p.product_id ?? "";
    byProduct.set(k, [...(byProduct.get(k) ?? []), p]);
  }
  for (const l of byProduct.values()) l.sort((a, b) => a.uid - b.uid);
  const usedOf = (h: { op: Operation; part: Part }) =>
    (h.op.result?.maps ?? []).reduce((n, m) => n + m.copies * m.placements.filter((pl) => pl.part_id === h.part.id).length, 0);
  const get = (fn: (h: { op: Operation; part: Part; idx: number }, r: Row) => unknown) =>
    (p: { data?: Row }) => { const h = p.data ? partOf.get(p.data.part_id) : undefined; return h && p.data ? fn(h, p.data) ?? "" : ""; };
  const prod = (h: { part: Part }) => project.products.find((x) => x.id === h.part.product_id);
  const size = (h: { op: Operation; part: Part }, k: "blank" | "detail" | "jointed" | "saw", i: 0 | 1) =>
    computeSizes(h.part, project.size_mode, edges, h.op.cs_cut?.machining_allowance ?? 0)[k][i];
  const edgeOf = (h: { part: Part }, s: (typeof SIDES)[number]): { op?: Operation; el?: ELParams } => {
    const id = h.part[`edge_${s}`]?.op_id;
    const op = id ? elOp.get(id) : undefined;
    return { op, el: op?.el ?? undefined };
  };
  const num = { cellClass: "num" };
  const defs: ColDef<Row>[] = [
    { colId: "product_code", valueGetter: get((h) => prod(h)?.code) },
    { colId: "product_name", valueGetter: get((h) => prod(h)?.name) },
    { colId: "product_num", ...num, valueGetter: get((h) => { const i = project.products.findIndex((x) => x.id === h.part.product_id); return i >= 0 ? i + 1 : ""; }) },
    { colId: "product_qty", ...num, valueGetter: get((h) => prod(h)?.qty) },
    { colId: "uid", ...num, valueGetter: get((h) => h.part.uid) },
    { colId: "code", valueGetter: get((h) => h.part.code) },
    { colId: "grain", valueGetter: get((h) => (h.part.grain ? "✓" : "")) },
    { colId: "description", valueGetter: get((h) => h.part.description) },
    { colId: "part_num", ...num, valueGetter: get((h) => (byProduct.get(h.part.product_id ?? "") ?? []).findIndex((x) => x.id === h.part.id) + 1) },
    { colId: "op_num", ...num, valueGetter: get((h) => h.idx + 1) },
    { colId: "part_qty", ...num, valueGetter: get((h) => h.part.qty) },
    { colId: "used", ...num, valueGetter: get((h) => usedOf(h)) },
    { colId: "left", ...num, valueGetter: get((h, r) => Math.max(0, r.qty - usedOf(h))) },
    ...(["blank", "detail", "jointed", "saw"] as const).flatMap((k) => [
      { colId: `${k}_l`, ...num, valueGetter: get((h) => size(h, k, 0)) },
      { colId: `${k}_w`, ...num, valueGetter: get((h) => size(h, k, 1)) }] as ColDef<Row>[]),
    ...SIDES.map((s) => ({ colId: `allow_${s}`, ...num, valueGetter: get((h) => h.part[`allow_${s}`] || "") }) as ColDef<Row>),
    { colId: "drill", valueGetter: get((h) => (partMarks(project, h.part).includes("%") ? "✓" : "")) },
    { colId: "mill", valueGetter: get((h) => (partMarks(project, h.part).includes("*") ? "✓" : "")) },
    { colId: "groove", valueGetter: get((h) => (partMarks(project, h.part).includes("=") ? "✓" : "")) },
    ...SIDES.flatMap((s) => [
      { colId: `e_${s}_code`, valueGetter: get((h) => edgeOf(h, s).op?.code) },
      { colId: `e_${s}_name`, valueGetter: get((h) => edgeOf(h, s).op?.name) },
      { colId: `e_${s}_sym`, valueGetter: get((h) => edgeOf(h, s).el?.symbol) },
      { colId: `e_${s}_th`, ...num, valueGetter: get((h) => edgeOf(h, s).el?.thickness) },
      { colId: `e_${s}_w`, ...num, valueGetter: get((h) => edgeOf(h, s).el?.width) },
      { colId: `e_${s}_joint`, ...num, valueGetter: get((h) => edgeOf(h, s).el?.jointing_width) },
    ] as ColDef<Row>[]),
  ];
  return defs.map((d) => {
    const spec = EL_EXTRA_SPECS.find((x) => x.key === d.colId);
    return { ...d, headerName: t(spec?.name ?? String(d.colId)), headerTooltip: t(spec?.desc ?? spec?.name ?? "") };
  });
}
