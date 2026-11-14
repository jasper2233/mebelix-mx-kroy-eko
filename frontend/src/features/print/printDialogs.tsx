// «Печать отчета» sozlamalari oynalari (§11, 2026-10-15) — xodimlar o'rgangan tizimdagi kabi «Параметр | Значение» jadvallari:
// «Поля страницы», «Настройки печати», «Изделия», (CS) [Общие | Детали | Карты кроя | Заголовок карт кроя], (CL) [Общие | Детали],
// (CN), (EL), (SP), «Обработка» (XNC) [Статистика | Чертеж], (GR), (O). Bizning qo'shimchalar — guruh oxirida yoki
// «Дополнительно (MebeliX)» guruhida. Qiymatlar `PrintSettings` ga `upd` orqali yoziladi (Ок/Отмена — Print.tsx).
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { HatchKind, PrintCol, PrintSettings } from "../../api/types";
import { Tabs } from "../../shared/ui";
import { ColumnsGrid, PropGrid, type ColDef, type ColVal, type GridGroup, type GridRow } from "./PrintGrid";

export type Dlg = "margins" | "general" | "products" | "cs" | "cn" | "cl" | "el" | "sp" | "gr" | "xnc" | "o";
type Upd = (f: Partial<PrintSettings>) => void;

/** «Заголовок карт кроя» standart ustunlari (backend `MAP_HEADER_COLS` bilan bir xil): №, S, C, Cp, LT, F yoqilgan. */
export const HEADER_DEFAULTS: ColVal[] = [
  { key: "N", on: true, width: 8 }, { key: "S", on: true, width: 12 }, { key: "C", on: true, width: 8 }, { key: "Cp", on: true, width: 8 },
  { key: "LT", on: true, width: 12 }, { key: "F", on: true, width: 12 }, { key: "R", on: false, width: 12 }, { key: "CT", on: false, width: 8 },
  { key: "T", on: false, width: 10 }, { key: "AP", on: false, width: 12 }, { key: "AM", on: false, width: 12 }, { key: "AW", on: false, width: 12 },
  { key: "PK", on: false, width: 10 },
];
/** XNC «Статистика» ustunlari (backend `XNC_STAT_COLS` bilan bir xil). */
export const XNC_STAT_DEFAULTS: ColVal[] = [
  { key: "n", on: true, width: 8 }, { key: "side", on: true, width: 5 }, { key: "code", on: true, width: 30 }, { key: "name", on: true, width: 25 },
  { key: "length", on: true, width: 8 }, { key: "width", on: true, width: 8 }, { key: "qty", on: true, width: 7 }, { key: "drills", on: true, width: 8 },
  { key: "drill_price", on: false, width: 10 }, { key: "drill_cost", on: false, width: 12 }, { key: "mill_len", on: true, width: 9 },
  { key: "mill_price", on: false, width: 11 }, { key: "mill_cost", on: false, width: 12 }, { key: "saw_len", on: true, width: 9 },
  { key: "saw_price", on: false, width: 11 }, { key: "saw_cost", on: false, width: 12 }, { key: "extra_cost", on: false, width: 10 },
  { key: "op_cost", on: true, width: 12 },
];
const HEADER_KEYS = new Set(HEADER_DEFAULTS.map((c) => c.key));
const HATCH: HatchKind[] = ["none", "diag", "cross", "horizontal", "vertical"];
const ORIGIN_POS = ["lt", "t", "rt", "l", "c", "r", "lb", "b", "rb"] as const;
type OriginPos = (typeof ORIGIN_POS)[number];

/** Sarlavha ustunlari: profilda jadval bo'lmasa yoki eski `map_header_fields` u bilan mos kelmasa — ro'yxatdan quriladi. */
export function headerCols(s: PrintSettings): ColVal[] {
  const cols = (s.map_header_cols ?? []).filter((c) => HEADER_KEYS.has(c.key));
  const fields = (s.map_header_fields ?? []).filter((k) => HEADER_KEYS.has(k));
  const onCols = cols.filter((c) => c.on).map((c) => c.key);
  if (cols.length && JSON.stringify(onCols) === JSON.stringify(fields)) return cols;
  const w = new Map([...HEADER_DEFAULTS, ...cols].map((c) => [c.key, c.width]));
  return [...fields.map((k) => ({ key: k, on: true, width: w.get(k) ?? 10 })),
    ...HEADER_DEFAULTS.filter((d) => !fields.includes(d.key)).map((d) => ({ key: d.key, on: false, width: w.get(d.key) ?? d.width }))];
}

function LineSample({ style }: { style: string }) {
  const dash = style === "dashed" ? "6 3" : style === "dotted" ? "2 2" : undefined;
  return <svg className="pgrid-line" viewBox="0 0 56 10" aria-hidden="true"><line x1="1" y1="5" x2="55" y2="5" stroke="#1b2a38" strokeWidth="2" strokeDasharray={dash} /></svg>;
}

export function PrintDialogBody({ dlg, s, upd }: { dlg: Dlg; s: PrintSettings; upd: Upd }) {
  const { t } = useTranslation();
  const [csTab, setCsTab] = useState<"general" | "parts" | "maps" | "header">("general");
  const [clTab, setClTab] = useState<"general" | "parts">("general");
  const [xncTab, setXncTab] = useState<"stats" | "drawing">("stats");
  const set = (key: keyof PrintSettings) => (v: unknown) => upd({ [key]: v } as Partial<PrintSettings>);
  const b = (key: keyof PrintSettings, label: string, dflt = false): GridRow =>
    ({ key, label, kind: "bool", value: Boolean(s[key] ?? dflt), onChange: set(key) });
  const sel = (key: keyof PrintSettings, label: string, dflt: string, options: { value: string; label: string }[]): GridRow =>
    ({ key, label, kind: "select", value: String(s[key] ?? dflt), options, onChange: set(key) });
  const opts = (prefix: string, values: readonly string[]) => values.map((v) => ({ value: v, label: t(`${prefix}.${v}`) }));
  const colorHatch = (key: string, label: string, color: string, hatch: HatchKind, onColor: (v: string) => void,
    onHatch: (v: HatchKind) => void): GridRow => ({
    key, label, kind: "custom",
    node: <>
      <input type="color" value={color} onChange={(e) => onColor(e.target.value)} data-testid={`pf-${key}`} />
      <span className="muted">{color.toUpperCase()}</span>
      <select className="pgrid-sel" value={hatch} onChange={(e) => onHatch(e.target.value as HatchKind)} data-testid={`pf-${key}_hatch`}>
        {HATCH.map((h) => <option key={h} value={h}>{t("print.f.hatch")}: {t(`print.hatch.${h}`)}</option>)}
      </select>
    </>,
  });
  const extra = (rows: GridRow[]): GridGroup => ({ key: "extra", label: t("print.g.extra"), rows });

  switch (dlg) {
    case "margins": {
      const m = (k: "left" | "right" | "top" | "bottom"): GridRow => {
        const key = `page_margin_${k}` as const;
        return { key, label: t(`print.margin.${k}`), kind: "number", value: s[key] ?? (k === "top" ? 8 : 10), min: 0, max: 50,
          unit: t("u.mm"), onChange: set(key) };
      };
      return <PropGrid testid="print-grid-margins" groups={[{ key: "m", rows: [m("left"), m("right"), m("top"), m("bottom"),
        b("page_mirror_margins", t("print.r.mirror_margins")),
        sel("page_footer_pos", t("print.r.footer_pos"), "bottom", opts("print.fp", ["bottom", "top", "none"]))] }]} />;
    }
    case "general":
      return <PropGrid testid="print-grid-general" groups={[
        { key: "top", rows: [b("header", t("print.r.header_project"), true)] },
        { key: "materials", label: t("print.g.materials"), rows: [b("materials_list", t("print.r.materials_list")),
          b("materials_group_by_code", t("print.r.materials_group"))] },
        { key: "warehouse", label: t("print.g.warehouse"), rows: [b("warehouse", t("print.r.warehouse"), true),
          b("warehouse_cut_work", t("print.r.warehouse_cut"), true), b("warehouse_edge_work", t("print.r.warehouse_edge"), true)] },
        { key: "products", label: t("print.g.products"), rows: [b("products_list", t("print.r.products_list")),
          b("products_list_single", t("print.r.products_single"))] },
        { key: "operations", label: t("print.g.operations"), rows: [b("operations_list", t("print.r.operations_list")),
          b("operations_list_single", t("print.r.operations_single")), b("operations", t("print.r.operations"), true)] },
        { key: "xnc", label: t("print.g.xnc"), rows: [b("xnc_stats", t("print.r.xnc_stats"))] },
      ]} />;
    case "products":
      return <PropGrid testid="print-grid-products" groups={[{ key: "p", rows: [b("prod_header", t("print.r.print_header")),
        b("prod_operations", t("print.r.print_ops")), b("prod_materials", t("print.r.print_materials")),
        b("prod_parts", t("print.r.print_parts"), true)] }]} />;
    case "cs": {
      const lbl = s.map_part_label ?? "number_name";
      const hasNum = lbl === "number" || lbl === "number_name";
      const hasName = lbl === "name" || lbl === "number_name";
      const setLbl = (n: boolean, m: boolean) => upd({ map_part_label: n && m ? "number_name" : n ? "number" : m ? "name" : "none" });
      const mirrorH = s.map_mirror_h ?? (s.map_mirror ? "yes" : "no");
      const tabs = <Tabs<"general" | "parts" | "maps" | "header"> value={csTab} onChange={setCsTab} tabs={[
        { key: "general", label: t("print.cstab.cs"), testid: "print-cs-tab-general" }, { key: "parts", label: t("print.tab.parts"), testid: "print-cs-tab-parts" },
        { key: "maps", label: t("print.cstab.maps"), testid: "print-cs-tab-maps" }, { key: "header", label: t("print.cstab.header"), testid: "print-cs-tab-header" }]} />;
      if (csTab === "general") return <>{tabs}<PropGrid testid="print-grid-cs" groups={[
        { key: "g", label: t("print.g.sections"), rows: [b("cs_title", t("print.r.print_header")), b("cs_warehouse", t("print.r.print_warehouse")),
          b("cs_stats", t("print.r.print_stats")), b("cs_parts", t("print.r.print_parts"), true),
          b("cs_unplaced", t("print.r.print_unplaced")), b("cs_sheets", t("print.r.print_sheets"), true),
          b("cs_remnants", t("print.r.print_remnants")), b("cs_maps", t("print.r.print_maps"), true)] },
        extra([b("cs_commands", t("print.r.commands_table"))]),
      ]} /></>;
      if (csTab === "parts") return <>{tabs}<PropGrid testid="print-grid-cs-parts" groups={[{ key: "d", rows: [
        b("cs_group_by_product", t("print.r.group_products")),
        { key: "cs_size_mode", label: t("print.r.size_mode"), kind: "select", value: s.cs_size_mode ?? "",
          options: [{ value: "", label: t("print.project_mode") }, { value: "blank", label: t("sizemode.blank") },
            { value: "detail", label: t("sizemode.detail") }, { value: "jointed", label: t("sizemode.jointed") }],
          onChange: (v) => upd({ cs_size_mode: (v || null) as PrintSettings["cs_size_mode"] }) },
        b("cs_edge_highlight", t("print.r.edge_highlight")), b("cs_edge_symbols", t("print.r.edge_symbols")),
        sel("cs_parts_form", t("print.r.parts_form"), "merged", opts("print.form", ["merged", "sides"])),
      ] }]} /></>;
      if (csTab === "maps") return <>{tabs}<PropGrid testid="print-grid-cs-maps" groups={[
        { key: "top", rows: [sel("map_orientation", t("print.r.map_layout"), "portrait", opts("print.orient", ["portrait", "landscape"])),
          b("map_parts_list", t("print.r.map_parts_list"), true)] },
        { key: "mirror", label: t("print.g.mirror"), rows: [
          { key: "map_mirror_h", label: t("print.r.mirror_h"), kind: "select", value: mirrorH,
            options: opts("print.mir", ["no", "yes", "cuts_v", "cuts_h"]),
            onChange: (v) => upd({ map_mirror_h: v as PrintSettings["map_mirror_h"], map_mirror: v === "yes" }) },
          b("map_mirror_v", t("print.r.mirror_v"))] },
        { key: "marks", label: t("print.g.part_marks"), rows: [
          { key: "map_part_number", label: t("print.r.part_number"), kind: "bool", value: hasNum, onChange: (v) => setLbl(v, hasName) },
          { key: "map_part_name", label: t("print.r.part_name"), kind: "bool", value: hasName, onChange: (v) => setLbl(hasNum, v) },
          b("map_part_marks", t("print.r.part_marks")),
          { key: "map_part_expr", label: t("print.r.part_expr"), kind: "text", value: s.map_part_expr ?? "", maxLength: 300,
            placeholder: t("print.r.part_expr_hint"), onChange: set("map_part_expr") },
          b("map_edges", t("print.r.edges"), true),
          sel("map_edge_marker", t("print.r.edge_marker"), "lines", opts("print.em", ["lines", "symbols", "both"])),
          { key: "map_edge_line_style", label: t("print.r.edge_line_style"), kind: "custom", node: <>
            <select className="pgrid-sel" value={s.map_edge_line_style ?? "solid"} data-testid="pf-map_edge_line_style"
              onChange={(e) => upd({ map_edge_line_style: e.target.value as PrintSettings["map_edge_line_style"] })}>
              {(["solid", "dashed", "dotted"] as const).map((v) => <option key={v} value={v}>{t(`print.ls.${v}`)}</option>)}
            </select><LineSample style={s.map_edge_line_style ?? "solid"} /></> },
          b("map_machining", t("print.r.machining"))] },
        { key: "remnant", label: t("print.g.remnant_marks"), rows: [b("map_remnant_number", t("print.r.remnant_number"), true)] },
        { key: "num", label: t("print.g.num_style"), rows: [
          { key: "map_num_font", label: `${t("print.r.font_size")} (${t("print.r.font_auto")})`, kind: "number", value: s.map_num_font ?? 0,
            min: 0, max: 40, unit: "pt", onChange: set("map_num_font") },
          b("map_num_bold", t("print.r.font_bold"), true)] },
        { key: "dim", label: t("print.g.dim_style"), rows: [
          { key: "map_dim_font", label: `${t("print.r.font_size")} (${t("print.r.font_auto")})`, kind: "number", value: s.map_dim_font ?? 0,
            min: 0, max: 40, unit: "pt", onChange: set("map_dim_font") },
          b("map_dim_bold", t("print.r.font_bold"), true), b("map_dim_rotate", t("print.r.font_rotate"), true)] },
        { key: "fill", label: t("print.g.fill_style"), rows: [
          b("map_mono", t("print.r.mono"), true),
          colorHatch("map_part_fill", t("print.r.fill_part"), s.map_part_fill ?? "#F2A541", s.map_part_hatch ?? "none",
            (v) => upd({ map_part_fill: v }), (v) => upd({ map_part_hatch: v })),
          colorHatch("map_waste_fill", t("print.r.fill_waste"), s.map_waste_fill ?? "#CBCED3", s.map_waste_hatch ?? "none",
            (v) => upd({ map_waste_fill: v }), (v) => upd({ map_waste_hatch: v }))] },
        { key: "barcode", label: t("print.g.barcode"), rows: [b("map_qr", t("print.r.barcode_print"), true),
          { key: "barcode_type", label: t("print.r.barcode_type"), kind: "custom", node: <span>QRCode</span> },
          { key: "barcode_data", label: t("print.r.barcode_data"), kind: "custom", node: <span className="muted">MXK:№:op:map</span> }] },
        extra([b("map_allowance", t("print.r.allowance"), true)]),
      ]} /></>;
      const defs: ColDef[] = HEADER_DEFAULTS.map((c) => ({ key: c.key, name: c.key === "N" ? "№" : c.key, desc: t(`print.hf.${c.key}`) }));
      return <>{tabs}
        <ColumnsGrid testid="print-header-cols" defs={defs} value={headerCols(s)} defaults={HEADER_DEFAULTS}
          onChange={(v) => upd({ map_header_cols: v, map_header_fields: v.filter((c) => c.on).map((c) => c.key) })} />
      </>;
    }
    case "cl": {
      const tabs = <Tabs<"general" | "parts"> value={clTab} onChange={setClTab} tabs={[
        { key: "general", label: t("print.tab.general") }, { key: "parts", label: t("print.tab.parts") }]} />;
      if (clTab === "general") return <>{tabs}<PropGrid testid="print-grid-cl" groups={[
        { key: "g", rows: [b("cl_header", t("print.r.print_header"), true), b("cl_warehouse", t("print.r.print_warehouse")),
          b("cl_stats", t("print.r.print_stats")), b("cl_parts", t("print.r.print_parts"), true),
          b("cl_unplaced", t("print.r.print_unplaced"), true), b("cl_strips", t("print.r.print_strips"), true),
          b("cl_remnants", t("print.r.print_remnants"), true), b("cl_maps", t("print.r.print_maps"), true)] },
        extra([b("cl_commands", t("print.r.commands_table"))]),
      ]} /></>;
      return <>{tabs}<PropGrid testid="print-grid-cl-parts" groups={[{ key: "d", rows: [b("cl_group_by_product", t("print.r.group_products"))] }]} /></>;
    }
    case "cn":
      return <PropGrid testid="print-grid-cn" groups={[{ key: "g", rows: [b("cn_params", t("print.r.print_params"), true),
        b("cn_parts", t("print.r.print_parts"), true), b("cn_unplaced", t("print.r.print_unplaced"), true),
        b("cn_sheets", t("print.r.print_sheets"), true), b("cn_remnants", t("print.r.print_remnants"), true),
        b("cn_maps", t("print.r.print_maps"), true)] }]} />;
    case "el":
      return <PropGrid testid="print-grid-el" groups={[
        { key: "g", rows: [b("el_params", t("print.r.print_header"), true), b("el_parts", t("print.r.print_parts"), true)] },
        { key: "h", label: t("print.g.el_header"), rows: [b("el_header_work", t("print.r.el_work")), b("el_header_material", t("print.r.el_material"))] },
      ]} />;
    case "sp":
      return <PropGrid testid="print-grid-sp" groups={[{ key: "g", rows: [b("sp_params", t("print.r.print_header"), true),
        b("sp_parts", t("print.r.print_parts"), true)] }]} />;
    case "gr":
      return <PropGrid testid="print-grid-gr" groups={[{ key: "g", rows: [b("gr_params", t("print.r.print_header"), true),
        b("gr_parts", t("print.r.print_parts"), true)] }]} />;
    case "o":
      return <PropGrid testid="print-grid-o" groups={[{ key: "g", rows: [b("o_params", t("print.f.o_params"), true),
        b("o_materials", t("print.f.o_materials"), true)] }]} />;
    case "xnc": {
      const tabs = <Tabs<"stats" | "drawing"> value={xncTab} onChange={setXncTab} tabs={[
        { key: "stats", label: t("print.tab.stats"), testid: "print-xnc-tab-stats" }, { key: "drawing", label: t("print.tab.drawing"), testid: "print-xnc-tab-drawing" }]} />;
      if (xncTab === "stats") {
        const defs: ColDef[] = XNC_STAT_DEFAULTS.map((c) => ({ key: c.key, name: t(`print.xc.${c.key}.n`), desc: t(`print.xc.${c.key}.d`) }));
        const cols: PrintCol[] = (s.xnc_stat_cols ?? []).length ? s.xnc_stat_cols! : XNC_STAT_DEFAULTS;
        return <>{tabs}<PropGrid testid="print-grid-xnc" groups={[{ key: "g", rows: [b("xnc_stats", t("print.r.xnc_stats")),
          sel("xnc_stats_group", t("print.r.grouping"), "material", opts("print.grp", ["none", "material", "product"]))] }]} />
          <ColumnsGrid testid="print-xnc-cols" defs={defs} value={cols} defaults={XNC_STAT_DEFAULTS} onChange={(v) => upd({ xnc_stat_cols: v })} />
        </>;
      }
      const asOp = Boolean(s.xnc_origin_as_op);
      const pos = (s.xnc_origin ?? "lt") as OriginPos;
      return <>{tabs}<PropGrid testid="print-grid-xnc-drawing" groups={[
        { key: "m", rows: [sel("xnc_back_mirror", t("print.r.back_mirror"), "horizontal", opts("print.bm", ["horizontal", "vertical", "none"]))] },
        { key: "origin", label: t("print.g.origin"), rows: [b("xnc_origin_as_op", t("print.r.origin_as_op")),
          { key: "xnc_origin", label: t("print.r.origin_pos"), kind: "custom", node: (
            <span className={asOp ? "origin9 is-off" : "origin9"} data-testid="pf-xnc_origin">
              {ORIGIN_POS.map((p) => <label key={p} title={p}><input type="radio" name="xnc_origin" checked={pos === p} disabled={asOp}
                onChange={() => upd({ xnc_origin: p })} /></label>)}
            </span>) }] },
        extra([b("xnc_drawing", t("print.r.print_drawings"), true)]),
      ]} /></>;
    }
  }
}

/** Oyna sarlavhasi: havola yozuvi bilan bir xil, «(XNC) Обработка» oynasi — «Обработка». */
export function dlgTitle(d: Dlg, t: (k: string) => string): string {
  if (d === "margins" || d === "general" || d === "products" || d === "xnc") return t(`print.dlg.${d}`);
  return t(d === "cs" ? "print.sec.cs_main" : `print.sec.${d}`);
}

export const DLG_WIDTH: Record<Dlg, number> = { margins: 440, general: 660, products: 440, cs: 840, cn: 460, cl: 520, el: 500,
  sp: 440, gr: 440, xnc: 660, o: 460 };
