// CL «Полосы и отходы» (hujjat D-CL4): polosa qatorlari (uzunlik × soni; eni = materialniki), ombordagi погонажный qoldiqlarni qo'shish,
// kroy natijasidagi otxod / деловой otxod qatorlari («Исп. Кол-во» — mijoz olib ketadigan bo'laklar, omborga yozilmaydi).
import { useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef, GridApi } from "ag-grid-community";
import { ArrowDownWideNarrow, ChevronDown, ChevronUp, CircleQuestionMark, Eraser, Infinity as InfinityIcon, Plus, Trash, Warehouse } from "lucide-react";
import { call } from "../../api/hooks";
import { put } from "../../api/client";
import type { Operation, Project, StockSheet } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid, parseCellNum } from "../../shared/grid/Grid";
import { askConfirm } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { excelNavKey } from "../../shared/grid/excelNav";
import { IconBtn, Sep } from "../../shared/ui";
import { RemnantPicker } from "../cs/CsSheets";
import { ClTabs } from "./ClPanel";

type SheetRow = StockSheet & { origin?: "result"; kindLabel?: "remnant" | "business"; numbers?: number[]; key?: string };

/** Natijadagi qoldiq guruhi kaliti — backend `warehouse.rem_key` bilan bir xil (yuzdan birlarda butun son). */
const remKey = (business: boolean, l: number, w: number) => `${business ? "b" : "r"}:${Math.round(l * 100)}x${Math.round(w * 100)}`;

export function ClSheets({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const cl = op.cl!;
  const grid = useRef<AgGridReact<SheetRow>>(null);
  const [sel, setSel] = useState<string | null>(null);
  const [picker, setPicker] = useState(false);
  const saved = !!op.result?.remnants_saved;
  const save = (sheets: StockSheet[]) => void call(() => put(`/projects/${project.id}/operations/${op.id}/sheets`, sheets));
  const numP = (int = false) => ({
    editable: true, cellClass: "num",
    valueParser: (p: { newValue: unknown; oldValue: unknown }) => {
      const v = parseCellNum(p.newValue);
      if (v === null) return p.oldValue;
      if (int) return Math.min(10000, Math.max(0, Math.round(v)));        // soni 0..10000 (10000 — «cheksiz»)
      return v > 0 ? Math.min(20000, v) : p.oldValue;                       // polosa uzunligi > 0
    },
  });
  // kroy natijasidagi otxodlar — jadval oxirida: uzunlik bo'yicha jamlangan
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
        kindLabel: o.business ? "business" : "remnant", numbers: [] as number[] } as SheetRow;
      r.qty += m.copies;
      if (o.number && r.numbers!.length < 6) r.numbers!.push(o.number);
      agg.set(key, r);
    }
    return [...agg.values()].map((r) => ({ ...r, used_qty: Math.min(r.used_qty, r.qty),
      description: r.numbers!.length ? `${t("rem.p")}${r.numbers!.join(`, ${t("rem.p")}`)}` : "" }));
  }, [op.result]);
  const rowData = useMemo<SheetRow[]>(() => [...op.sheets, ...resultRows], [op.sheets, resultRows]);
  const ro = (p: { data?: SheetRow }) => p.data?.origin !== "result";
  // Standart ustunlar onlayn tizim bilan bir xil: № | Длина | Ширина | Сони | Квадрати | Ишлатилди | Колдик | ТШ | Изох;
  // «Наименование» faqat qoldiq qatorlari bo'lganda. «ТШ» — polosa torsovkasi: 1D optimizator operatsiya parametri («Торцовка») dan
  // oladi, polosaga alohida qiymat berilmaydi — shuning uchun ustun faqat o'qish uchun.
  const hasRemnants = op.sheets.some((s) => s.is_remnant) || resultRows.length > 0;
  const cols = useMemo<ColDef<SheetRow>[]>(() => [
    { headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum" },
    ...(hasRemnants ? [{ headerName: t("sheets.col.kind"), colId: "kind", width: 150,
      valueGetter: (p) => t(`sheets.kind.${p.data?.origin === "result" ? p.data.kindLabel : (p.data?.is_remnant ? "stock" : "strip")}`) } as ColDef<SheetRow>] : []),
    { headerName: t("sheets.col.length"), field: "length", width: 110, ...numP(), editable: ro },
    { headerName: t("sheets.col.width"), field: "width", width: 90, cellClass: "num muted", editable: false,
      headerTooltip: t("cl.sheets.width_hint") },
    { headerName: t("sheets.col.qty"), field: "qty", width: 100, ...numP(true), editable: ro },
    { headerName: t("sheets.col.area"), width: 90, cellClass: "num",
      valueGetter: (p) => (p.data ? Math.round((p.data.length * p.data.width) / 1e3) / 1e3 : 0) },
    { headerName: t("sheets.col.used"), field: "used_qty", width: 100, cellClass: (p) => (p.data?.origin === "result" ? "num taken" : "num"),
      headerTooltip: t("sheets.taken_hint"),
      editable: (p) => p.data?.origin === "result" && !saved,
      tooltipValueGetter: (p) => (p.data?.origin === "result" ? (saved ? t("sheets.taken_locked") : t("sheets.taken_hint")) : undefined),
      valueParser: (p) => {
        const v = parseCellNum(p.newValue);
        const max = (p.data as SheetRow | undefined)?.qty ?? 0;
        return v === null ? p.oldValue : Math.min(max, Math.max(0, Math.round(v)));
      } },
    { headerName: t("sheets.col.left"), width: 90, cellClass: "num", valueGetter: (p) => (p.data ? p.data.qty - p.data.used_qty : 0) },
    { headerName: t("sheets.col.trim_w"), colId: "trim", width: 60, cellClass: "num muted", headerTooltip: t("sheets.col.cl_trim_hint"),
      valueGetter: (p) => (p.data && p.data.origin !== "result" ? cl.trim : "") },
    { headerName: t("sheets.col.note"), field: "description", flex: 1, minWidth: 160, editable: ro },
    // «МЗап» — polosa listining minimal to'ldirish foizi (onlayn tizimdagidek; optimizator shu chegaradan past kartani bekor qiladi)
    { headerName: t("sheets.col.min_fill"), field: "min_fill_percent", width: 80, editable: ro, cellClass: "num",
      headerTooltip: t("sheets.col.min_fill_hint"),
      valueParser: (p) => { const v = parseCellNum(p.newValue); return v === null ? null : Math.min(100, Math.max(0, v)); } },
  ], [t, saved, hasRemnants, cl.trim]); // eslint-disable-line react-hooks/exhaustive-deps
  // onlayn tizimdagidek jadvalda doim bitta tanlangan qator: tanlov bo'lmasa — birinchi qator (ko'k fon)
  const selectFirst = (api: GridApi<SheetRow>) => {
    if (!api.getSelectedNodes().length && api.getDisplayedRowCount() > 0) api.getDisplayedRowAtIndex(0)?.setSelected(true);
  };

  const onChange = (e: CellValueChangedEvent<SheetRow>) => {
    if (!e.data) return;
    if (e.data.origin === "result") {
      if (e.colDef.field === "used_qty" && e.data.key && e.newValue !== e.oldValue)
        void call(() => put(`/projects/${project.id}/operations/${op.id}/result/taken`, { key: e.data!.key, qty: Number(e.newValue) || 0 }));
      return;
    }
    const { origin: _o, kindLabel: _k, numbers: _n, key: _key, ...row } = e.data;
    save(op.sheets.map((s) => (s.id === row.id ? { ...s, ...row, width: cl.width } : s)));
  };
  const blank = (): StockSheet => ({ length: op.sheets[op.sheets.length - 1]?.length ?? 6000, width: cl.width, qty: 10000 } as StockSheet);
  const act = {
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
    // «Сортировка» (CS dagidek): ombor qoldiqlari avval, so'ng soni bo'yicha o'sish, uzunroq polosa oldin
    sort: () => save([...op.sheets].sort((a, b) => (Number(b.is_remnant) - Number(a.is_remnant)) || a.qty - b.qty || b.length - a.length)),
    // «Удалить неиспользуемый материал»: kroyda ishlatilmagan polosa qatorlari o'chiriladi
    unused: async () => {
      const used = new Set((op.result?.maps ?? []).map((m) => m.sheet_id));
      const keep = op.sheets.filter((s) => used.has(s.id));
      if (keep.length === op.sheets.length) { ui.toast(t("sheets.nothing_unused"), "info"); return; }
      if (!(await askConfirm(t("sheets.remove_unused_q", { n: op.sheets.length - keep.length })))) return;
      save(keep);
    },
  };
  // onlayn yordam: Tab/Enter — o'ngga, Shift — chapga, Ctrl+Tab/Ctrl+Enter — pastga (oxirida yangi qator)
  const addRef = useRef(act.add);
  addRef.current = act.add;
  const navColDef = useMemo<ColDef<SheetRow>>(() => ({ suppressKeyboardEvent: (p) => excelNavKey(p, () => void addRef.current()) }), []);
  useHotkeys("sheets", {
    "delete,shift+delete": act.remove, "ctrl+arrowup": () => act.move(-1), "ctrl+arrowdown": () => act.move(1),
    "ctrl+pageup,alt+pageup,insert": act.insert, "ctrl+pagedown": act.add,
  });
  return (
    <div className="panel" {...scopeProps("sheets")}>
      {/* onlayn tartib: Сортировка, Удалить неиспользуемый материал | ↑ ↓ | Вставить, Удалить | Справка;
          bizning qo'shimchalar (Добавить остатки со склада, Количество не ограничено, Добавить в конец) — oxirida */}
      <ClTabs right={<>
        <IconBtn icon={ArrowDownWideNarrow} title={t("app.sort")} onClick={act.sort} testid="cl-sheets-sort" />
        <IconBtn icon={Eraser} title={t("sheets.remove_unused")} onClick={() => void act.unused()} disabled={!op.result} />
        <Sep />
        <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={() => act.move(-1)} disabled={!sel} />
        <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={() => act.move(1)} disabled={!sel} />
        <Sep />
        <IconBtn icon={Plus} title={`${t("app.insert")} (Ctrl+PgUp)`} onClick={act.insert} testid="cl-sheets-insert" />
        <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={act.remove} disabled={!sel} color="#c0392b" />
        <Sep />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
        <Sep />
        <IconBtn icon={Warehouse} title={t("sheets.from_warehouse")} onClick={() => setPicker(true)} testid="cl-sheets-from-warehouse" color="#1f6feb" />
        <IconBtn icon={InfinityIcon} title={t("sheets.unlimited")} onClick={act.unlimited} disabled={!sel} />
        <IconBtn icon={Plus} title={`${t("app.add")} (Ctrl+PgDn)`} onClick={act.add} testid="cl-sheets-add" />
      </>} />
      <Grid<SheetRow> ref={grid} className="grow" rowData={rowData} columnDefs={cols} getRowId={(p) => p.data.id}
        testid="cl-sheets-grid" defaultColDef={navColDef} focusFirst rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onFirstDataRendered={(e) => selectFirst(e.api)} onRowDataUpdated={(e) => selectFirst(e.api)}
        onSelectionChanged={(e) => { const r = e.api.getSelectedRows()[0]; setSel(r && r.origin !== "result" ? r.id : null); }}
        getRowClass={(p) => (p.data?.origin === "result" ? (p.data.kindLabel === "business" ? "row-business" : "row-result")
          : p.data?.is_remnant ? "row-remnant" : "")} onCellValueChanged={onChange}
        // onlayn tartib: Добавить, Удалить | Справка; bizning qo'shimchalar — oxirida
        menu={() => [
          { label: t("app.add"), hint: "Ctrl+PgDn", onClick: act.add, testid: "ctx-cl-sheets-add" },
          { label: t("app.delete"), hint: "Del", onClick: act.remove, disabled: !sel },
          { sep: true, label: "" },
          { label: t("menu.help"), hint: "F1", onClick: () => ui.set({ section: "help" }) },
          { sep: true, label: "" },
          { label: t("ctx.insert_row"), hint: "Ctrl+PgUp", onClick: act.insert },
          { label: t("app.move_up"), hint: "Ctrl+↑", onClick: () => act.move(-1), disabled: !sel },
          { label: t("app.move_down"), hint: "Ctrl+↓", onClick: () => act.move(1), disabled: !sel },
          { label: t("app.sort"), onClick: act.sort },
          { label: t("sheets.remove_unused"), onClick: () => void act.unused(), disabled: !op.result },
          { label: t("sheets.from_warehouse"), onClick: () => setPicker(true) },
          { label: t("sheets.unlimited"), onClick: act.unlimited, disabled: !sel },
        ]} />
      <div className="hint">{t("cl.sheets.hint")}</div>
      {picker && <RemnantPicker project={project} op={op} onClose={() => setPicker(false)} />}
    </div>
  );
}
