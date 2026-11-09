// (CN) «Листы и остатки»: listlar (L × W — eni ham tahrirlanadi), ombordagi listli qoldiqlarni qo'shish, nesting natijasidagi qoldiqlar
// (Д№; detalning ichki kesimidagi qoldiq belgilanadi), «Исп. кол-во» — mijoz olib ketadigan bo'laklar. CsSheets namunasida.
import { useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef } from "ag-grid-community";
import { ChevronDown, ChevronUp, CircleQuestionMark, Infinity as InfinityIcon, Plus, Trash, Warehouse } from "lucide-react";
import { call, useAppSettings } from "../../api/hooks";
import { put } from "../../api/client";
import type { Operation, Project, StockSheet } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid, parseCellNum } from "../../shared/grid/Grid";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { IconBtn, Sep } from "../../shared/ui";
import { RemnantPicker } from "../cs/CsSheets";
import { CnTabs } from "./CnPanel";

type SheetRow = StockSheet & { origin?: "result"; kindLabel?: "remnant" | "business"; numbers?: string[]; key?: string };

/** Natijadagi qoldiq guruhi kaliti — backend `warehouse.rem_key` bilan bir xil (yuzdan birlarda butun son). */
const remKey = (business: boolean, l: number, w: number) => `${business ? "b" : "r"}:${Math.round(l * 100)}x${Math.round(w * 100)}`;

export function CnSheets({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const app = useAppSettings();
  const grid = useRef<AgGridReact<SheetRow>>(null);
  const [sel, setSel] = useState<string | null>(null);
  const [picker, setPicker] = useState(false);
  const saved = !!op.result?.remnants_saved;                 // omborga yozilgan — «Исп. кол-во» o'zgarmaydi
  const save = (sheets: StockSheet[]) => void call(() => put(`/projects/${project.id}/operations/${op.id}/sheets`, sheets));
  const numP = (int = false) => ({
    editable: true, cellClass: "num",
    valueParser: (p: { newValue: unknown; oldValue: unknown }) => {
      const v = parseCellNum(p.newValue);
      if (v === null) return p.oldValue;
      if (int) return Math.min(10000, Math.max(0, Math.round(v)));        // soni 0..10000 (10000 — «cheksiz»)
      return v > 0 ? Math.min(20000, v) : p.oldValue;                       // list o'lchami > 0
    },
  });
  // nesting natijasidagi qoldiqlar — jadval oxirida: o'lcham bo'yicha jamlangan; detal ichki kesimidagilari «Д5⊂3» (3 — detal uid)
  const resultRows = useMemo<SheetRow[]>(() => {
    const res = op.result;
    if (!res) return [];
    const agg = new Map<string, SheetRow>();
    for (const m of res.maps) for (const o of m.offcuts) {
      if (o.kind !== "remnant") continue;
      const key = remKey(o.business, o.length, o.width);
      const r = agg.get(key) ?? { id: `res-${key}`, key, length: o.length, width: o.width, qty: 0, is_remnant: false,
        trim_length: null, trim_width: null, end_offset_bottom: null, end_offset_right: null, description: "",
        used_qty: Math.min(Number(res.taken_remnants?.[key] ?? 0), 1e9), source_remnant_id: null, origin: "result",
        kindLabel: o.business ? "business" : "remnant", numbers: [] as string[] } as SheetRow;
      r.qty += m.copies;
      if (o.number && r.numbers!.length < 6) r.numbers!.push(`${t("rem.p")}${o.number}${(o.in_part ?? 0) > 0 ? `⊂${o.in_part}` : ""}`);
      agg.set(key, r);
    }
    return [...agg.values()].map((r) => ({ ...r, used_qty: Math.min(r.used_qty, r.qty), description: r.numbers!.join(", ") }));
  }, [op.result]);
  const rowData = useMemo<SheetRow[]>(() => [...op.sheets, ...resultRows], [op.sheets, resultRows]);
  const ro = (p: { data?: SheetRow }) => p.data?.origin !== "result";
  const cols = useMemo<ColDef<SheetRow>[]>(() => [
    { headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum" },
    { headerName: t("sheets.col.kind"), colId: "kind", width: 140,
      valueGetter: (p) => t(`sheets.kind.${p.data?.origin === "result" ? p.data.kindLabel : (p.data?.is_remnant ? "stock" : "sheet")}`) },
    { headerName: t("sheets.col.length"), field: "length", width: 100, ...numP(), editable: ro },
    { headerName: t("sheets.col.width"), field: "width", width: 100, ...numP(), editable: ro },
    { headerName: t("sheets.col.qty"), field: "qty", width: 90, ...numP(true), editable: ro },
    { headerName: t("sheets.col.area"), width: 90, cellClass: "num",
      valueGetter: (p) => (p.data ? Math.round((p.data.length * p.data.width) / 1e3) / 1e3 : 0) },
    { headerName: t("sheets.col.used"), field: "used_qty", width: 90, cellClass: (p) => (p.data?.origin === "result" ? "num taken" : "num"),
      headerTooltip: t("sheets.taken_hint"),
      editable: (p) => p.data?.origin === "result" && !saved,
      tooltipValueGetter: (p) => (p.data?.origin === "result" ? (saved ? t("sheets.taken_locked") : t("sheets.taken_hint")) : undefined),
      valueParser: (p) => {
        const v = parseCellNum(p.newValue);
        const max = (p.data as SheetRow | undefined)?.qty ?? 0;
        return v === null ? p.oldValue : Math.min(max, Math.max(0, Math.round(v)));
      } },
    { headerName: t("sheets.col.left"), width: 90, cellClass: "num", valueGetter: (p) => (p.data ? p.data.qty - p.data.used_qty : 0) },
    { headerName: t("sheets.col.note"), field: "description", flex: 1, minWidth: 180, editable: ro,
      tooltipValueGetter: (p) => (p.data?.origin === "result" && /⊂/.test(p.data.description) ? t("cn.sheets.in_part_hint") : undefined) },
  ], [t, saved]); // eslint-disable-line react-hooks/exhaustive-deps

  const onChange = (e: CellValueChangedEvent<SheetRow>) => {
    if (!e.data) return;
    if (e.data.origin === "result") {                       // «Исп. кол-во»: faqat shu ustun tahrirlanadi
      if (e.colDef.field === "used_qty" && e.data.key && e.newValue !== e.oldValue)
        void call(() => put(`/projects/${project.id}/operations/${op.id}/result/taken`, { key: e.data!.key, qty: Number(e.newValue) || 0 }));
      return;
    }
    const { origin: _o, kindLabel: _k, numbers: _n, key: _key, ...row } = e.data;
    save(op.sheets.map((s) => (s.id === row.id ? { ...s, ...row } : s)));
  };
  const blank = (): StockSheet => ({ length: app.data?.default_sheet_length ?? 2750, width: app.data?.default_sheet_width ?? 1830, qty: 10000 } as StockSheet);
  const act = {
    // Ctrl+PgUp / Insert — tanlangan qatordan OLDIN qo'shadi (list tartibi = ustuvorlik); Ctrl+PgDn / tugma — oxiriga
    insert: () => {
      const i = sel ? op.sheets.findIndex((s) => s.id === sel) : -1;
      if (i < 0) { act.add(); return; }
      save([...op.sheets.slice(0, i), blank(), ...op.sheets.slice(i)]);
    },
    add: () => save([...op.sheets, blank()]),
    remove: () => sel && save(op.sheets.filter((s) => s.id !== sel)),
    move: (d: -1 | 1) => {
      const i = op.sheets.findIndex((s) => s.id === sel);
      const j = i + d;
      if (i < 0 || j < 0 || j >= op.sheets.length) return;
      const a = [...op.sheets];
      [a[i], a[j]] = [a[j], a[i]];
      save(a);
    },
    unlimited: () => sel && save(op.sheets.map((s) => (s.id === sel ? { ...s, qty: 10000 } : s))),
  };
  useHotkeys("sheets", {
    "delete,shift+delete": act.remove, "ctrl+arrowup": () => act.move(-1), "ctrl+arrowdown": () => act.move(1),
    "ctrl+pageup,alt+pageup,insert": act.insert, "ctrl+pagedown": act.add,
  });
  return (
    <div className="panel" {...scopeProps("sheets")}>
      <CnTabs right={<>
        <IconBtn icon={Warehouse} title={t("sheets.from_warehouse")} onClick={() => setPicker(true)} testid="cn-sheets-from-warehouse" color="#1f6feb" />
        <IconBtn icon={InfinityIcon} title={t("sheets.unlimited")} onClick={act.unlimited} disabled={!sel} />
        <Sep />
        <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={() => act.move(-1)} disabled={!sel} />
        <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={() => act.move(1)} disabled={!sel} />
        <IconBtn icon={Plus} title={`${t("app.add")} (Ctrl+PgDn)`} onClick={act.add} testid="cn-sheets-add" />
        <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={act.remove} disabled={!sel} color="#c0392b" />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
      </>} />
      <Grid<SheetRow> ref={grid} className="grow" textEdit rowData={rowData} columnDefs={cols} getRowId={(p) => p.data.id}
        testid="cn-sheets-grid" focusFirst rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onSelectionChanged={(e) => { const r = e.api.getSelectedRows()[0]; setSel(r && r.origin !== "result" ? r.id : null); }}
        getRowClass={(p) => (p.data?.origin === "result" ? (p.data.kindLabel === "business" ? "row-business" : "row-result")
          : p.data?.is_remnant ? "row-remnant" : "")} onCellValueChanged={onChange}
        menu={() => [
          { label: t("app.add"), hint: "Ctrl+PgDn", onClick: act.add, testid: "ctx-cn-sheets-add" },
          { label: t("ctx.insert_row"), hint: "Insert", onClick: act.insert },
          { label: t("app.delete"), hint: "Del", onClick: act.remove, disabled: !sel },
          { sep: true, label: "" },
          { label: t("app.move_up"), hint: "Ctrl+↑", onClick: () => act.move(-1), disabled: !sel },
          { label: t("app.move_down"), hint: "Ctrl+↓", onClick: () => act.move(1), disabled: !sel },
          { sep: true, label: "" },
          { label: t("sheets.from_warehouse"), onClick: () => setPicker(true) },
          { label: t("sheets.unlimited"), onClick: act.unlimited, disabled: !sel },
          { sep: true, label: "" },
          { label: t("menu.help"), hint: "F1", onClick: () => ui.set({ section: "help" }) },
        ]} />
      <div className="hint">{t("cn.sheets.hint")}</div>
      {picker && <RemnantPicker project={project} op={op} onClose={() => setPicker(false)} />}
    </div>
  );
}
