// CS «Листы и остатки» (UI_SPEC §5.3): listlar, ombordagi qoldiqlarni qo'shish (rezerv bilan), kroy natijasidagi qoldiqlar.
// W2: qoldiq qatorida «Исп. кол-во» — mijoz olib ketadigan bo'laklar (omborga yozilmaydi), qoldiq rezervi, Ctrl+PgUp joriy qatordan oldin.
import { useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef, GridApi, ICellRendererParams } from "ag-grid-community";
import { ChevronDown, ChevronUp, CircleQuestionMark, Infinity as InfinityIcon, Plus, Trash, Warehouse, ArrowDownWideNarrow, Eraser } from "lucide-react";
import { call, qc, useAppSettings, useRemnants } from "../../api/hooks";
import { post, put } from "../../api/client";
import type { Operation, Project, Remnant, StockSheet } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm } from "../../shared/dialogs";
import { Grid, parseCellNum } from "../../shared/grid/Grid";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { Btn, Check, IconBtn, Modal, Sep } from "../../shared/ui";
import { CsTabs } from "./CsPanel";

export function RemnantPicker({ project, op, onClose }: { project: Project; op: Operation; onClose: () => void }) {
  const { t } = useTranslation();
  const [all, setAll] = useState(false);
  const code = (op.code || op.name || "").trim();
  const linear = op.type === "CL";                       // (CL, W11) погонажный qoldiqlar alohida: CS faqat listli, CL faqat погонажный
  const data = useRemnants(all ? undefined : code, "", linear);               // (CL) погонажный / (CS) listli qoldiqlar
  const [sel, setSel] = useState<number[]>([]);
  const thick = linear ? op.cl?.thickness : op.type === "CN" ? op.cn?.thickness : op.cs_material?.thickness;     // (CN, W16) nesting: qalinlik CNParams da
  const have = new Set(op.sheets.map((s) => s.source_remnant_id).filter(Boolean));
  // rezerv: boshqa loyiha band qilgan qoldiqni tanlab bo'lmaydi (REM-009)
  const reservedByOther = (r?: Remnant) => !!r?.reserved_project && r.reserved_project !== project.id;
  const release = async (id: number) => {
    if (!(await askConfirm(t("rem.release_q"), undefined, { danger: true }))) return;
    const r = await call(() => post<{ released: number }>("/remnants/reservations/release", { ids: [id] }));
    if (r) { useUI.getState().toast(t("rem.released", { n: r.released }), "ok"); void qc.invalidateQueries({ queryKey: ["remnants"] }); }
  };
  const cols = useMemo<ColDef<Remnant>[]>(() => [
    { headerName: "ID", field: "id", width: 60, cellClass: "num" },
    { headerName: t("rem.material"), valueGetter: (p) => `${p.data?.material_code ?? ""} ${p.data?.material_name ?? ""}`, flex: 1, minWidth: 120 },
    { headerName: t("sheets.col.length"), field: "length", width: 80, cellClass: "num" },
    { headerName: t("sheets.col.width"), field: "width", width: 80, cellClass: "num" },
    { headerName: t("rem.thickness"), field: "thickness", width: 70, cellClass: (p) => (p.value !== thick ? "num warn" : "num") },
    { headerName: t("sheets.col.qty"), field: "qty", width: 60, cellClass: "num" },
    { headerName: t("u.m2"), field: "area_m2", width: 70, cellClass: "num" },
    { headerName: t("rem.source"), valueGetter: (p) => (p.data?.source_number ? `№${p.data.source_number}` : ""), width: 90 },
    { headerName: t("rem.reserved"), colId: "reserved", width: 270,
      cellRenderer: (p: ICellRendererParams<Remnant>) => {
        const r = p.data;
        if (!r?.reserved_project) return null;
        if (r.reserved_project === project.id) return <span>{t("rem.reserved_mine")}</span>;
        return (
          <span className="rem-reserved" data-testid={`rem-reserved-${r.id}`}>{t("rem.reserved_by", { n: r.reserved_number ?? "?" })}{" "}
            <button type="button" className="linkbtn" onClick={(e) => { e.stopPropagation(); void release(r.id); }}>{t("rem.release")}</button></span>
        );
      } },
    { headerName: t("rem.note"), field: "note", width: 190 },
  ], [t, thick, project.id]); // eslint-disable-line react-hooks/exhaustive-deps
  const rows = (data.data ?? []).filter((r) => !have.has(r.id));
  const add = async () => {
    // «Показать все материалы» yoqilgan bo'lsa — qalinligi boshqa qoldiq ham ataylab qo'shiladi (force); aks holda server 400 qaytaradi
    const r = await call(() => post(`/projects/${project.id}/operations/${op.id}/sheets/from-remnants?force=${all ? "true" : "false"}`, { ids: sel }));
    void qc.invalidateQueries({ queryKey: ["remnants"] });
    if (r) onClose();
  };
  return (
    <Modal title={t("sheets.from_warehouse")} onClose={onClose} width={1100} height={520} testid="remnant-picker"
      footer={<>
        <Check checked={all} onChange={setAll} label={t("rem.all_materials")} />
        <span className="grow" />
        <Btn kind="primary" label={t("app.add")} disabled={!sel.length} testid="remnant-add" onClick={() => void add()} />
        <Btn label={t("app.cancel")} onClick={onClose} />
      </>}>
      <p className="muted">{t("rem.picker_hint", { code: code || "—" })}</p>
      <Grid<Remnant> className="grow" rowData={rows} columnDefs={cols} getRowId={(p) => String(p.data.id)}
        rowSelection={{ mode: "multiRow", checkboxes: true, headerCheckbox: true, enableClickSelection: true,
          isRowSelectable: (n) => !!n.data && !reservedByOther(n.data) }}
        getRowClass={(p) => (reservedByOther(p.data) ? "row-reserved" : "")}
        onSelectionChanged={(e) => setSel(e.api.getSelectedRows().filter((r) => !reservedByOther(r)).map((r) => r.id))} />
      {rows.some((r) => reservedByOther(r)) && <div className="hint">{t("rem.reserved_hint")}</div>}
    </Modal>
  );
}

/** Jadval qatori: kiruvchi list (op.sheets) yoki kroy natijasidagi qoldiq (origin = "result"). */
type SheetRow = StockSheet & { origin?: "result"; kindLabel?: "remnant" | "business"; numbers?: number[]; key?: string };

/** Natijadagi qoldiq guruhi kaliti — backend `warehouse.rem_key` bilan bir xil (yuzdan birlarda butun son). */
const remKey = (business: boolean, l: number, w: number) => `${business ? "b" : "r"}:${Math.round(l * 100)}x${Math.round(w * 100)}`;

export function CsSheets({ project, op }: { project: Project; op: Operation }) {
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
      return v > 0 ? Math.min(20000, v) : p.oldValue;                       // list o'lchami > 0 (rad etilsa eski qiymat)
    },
  });
  // kroy natijasidagi qoldiqlar — jadval oxirida: o'lcham bo'yicha jamlangan; «Исп. кол-во» (used_qty) — mijoz olib ketadigani
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
      description: r.numbers!.length ? `Д${r.numbers!.join(", Д")}` : "" }));
  }, [op.result]);
  const rowData = useMemo<SheetRow[]>(() => [...op.sheets, ...resultRows], [op.sheets, resultRows]);
  const ro = (p: { data?: SheetRow }) => p.data?.origin !== "result";
  // Standart ustunlar onlayn tizim bilan bir xil: № | Длина | Ширина | Сони | Квадрати | Ишлатилди | Колдик | ТД | ТШ | Изох;
  // «Наименование», «ОН», «ОП» faqat qoldiq qatorlari bo'lganda (ombordan olingan yoki kroy natijasidagi) ko'rsatiladi
  const hasRemnants = op.sheets.some((s) => s.is_remnant) || resultRows.length > 0;
  const cols = useMemo<ColDef<SheetRow>[]>(() => ([
    { headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum" },
    ...(hasRemnants ? [{ headerName: t("sheets.col.kind"), colId: "kind", width: 130,
      valueGetter: (p) => t(`sheets.kind.${p.data?.origin === "result" ? p.data.kindLabel : (p.data?.is_remnant ? "stock" : "sheet")}`) } as ColDef<SheetRow>] : []),
    { headerName: t("sheets.col.length"), field: "length", width: 100, ...numP(), editable: ro },
    { headerName: t("sheets.col.width"), field: "width", width: 100, ...numP(), editable: ro },
    { headerName: t("sheets.col.qty"), field: "qty", width: 90, ...numP(true), editable: ro, headerTooltip: t("sheets.hint"),
      valueFormatter: (p) => (p.value >= 10000 ? `${p.value}` : String(p.value)) },
    { headerName: t("sheets.col.area"), width: 90, cellClass: "num",
      valueGetter: (p) => (p.data ? Math.round((p.data.length * p.data.width) / 1e3) / 1e3 : 0) },
    // Исп. Кол-во: list qatorida — kroyda ishlatilgan (hisoblanadi); qoldiq qatorida — mijoz olib ketadigan bo'laklar (tahrirlanadi)
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
    { headerName: t("sheets.col.trim_l"), field: "trim_length", width: 60, editable: ro, cellClass: "num",
      headerTooltip: t("sheets.col.trim_l_hint"), valueParser: (p) => parseCellNum(p.newValue) },
    { headerName: t("sheets.col.trim_w"), field: "trim_width", width: 60, editable: ro, cellClass: "num",
      headerTooltip: t("sheets.col.trim_w_hint"), valueParser: (p) => parseCellNum(p.newValue) },
    ...(hasRemnants ? [
      { headerName: t("sheets.col.end_b"), field: "end_offset_bottom", width: 60, editable: ro, cellClass: "num",
        headerTooltip: t("cs.p.offset_bottom"), valueParser: (p) => parseCellNum(p.newValue) },
      { headerName: t("sheets.col.end_r"), field: "end_offset_right", width: 60, editable: ro, cellClass: "num",
        headerTooltip: t("cs.p.offset_right"), valueParser: (p) => parseCellNum(p.newValue) },
    ] as ColDef<SheetRow>[] : []),
    { headerName: t("sheets.col.note"), field: "description", width: 160, editable: ro },
    // ustunlar jadval kengligiga mutanosib cho'ziladi (panel bo'sh qolmaydi — onlayn ko'rinish)
  ] as ColDef<SheetRow>[]).map((c) => ({ ...c, flex: c.width, minWidth: Math.min(c.width ?? 60, 60) })), [t, saved, hasRemnants]); // eslint-disable-line react-hooks/exhaustive-deps
  // onlayn tizimdagidek jadvalda doim bitta tanlangan qator: tanlov bo'lmasa — birinchi qator (ko'k fon)
  const selectFirst = (api: GridApi<SheetRow>) => {
    if (!api.getSelectedNodes().length && api.getDisplayedRowCount() > 0) api.getDisplayedRowAtIndex(0)?.setSelected(true);
  };

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
    // Ctrl+PgUp / Alt+PgUp / Insert — tanlangan qatordan OLDIN qo'shadi (list tartibi = ustuvorlik); Ctrl+PgDn / tugma — oxiriga (CS-106)
    insert: () => {
      const i = sel ? op.sheets.findIndex((s) => s.id === sel) : -1;
      if (i < 0) { act.add(); return; }
      save([...op.sheets.slice(0, i), blank(), ...op.sheets.slice(i)]);
    },
    add: () => save([...op.sheets, blank()]),
    remove: () => {
      if (!sel) return;
      if (op.sheets.length <= 1) { ui.toast(t("sheets.last_row"), "info"); return; }      // yagona qator — o'chirilmaydi (#21)
      save(op.sheets.filter((s) => s.id !== sel));
    },
    move: (d: -1 | 1) => {
      const i = op.sheets.findIndex((s) => s.id === sel);
      const j = i + d;
      if (i < 0 || j < 0 || j >= op.sheets.length) return;
      const a = [...op.sheets];
      [a[i], a[j]] = [a[j], a[i]];
      save(a);
    },
    unlimited: () => sel && save(op.sheets.map((s) => (s.id === sel ? { ...s, qty: 10000 } : s))),
    // «Сортировка»: ustuvorlik tartibi — soni bo'yicha o'sish (ombor qoldiqlari va cheklangan listlar oldin, 10000 — oxirida)
    sort: () => save([...op.sheets].sort((a, b) => (Number(b.is_remnant) - Number(a.is_remnant)) || a.qty - b.qty
      || b.length * b.width - a.length * a.width)),
    // «Удалить неиспользуемый материал»: kroyda ishlatilmagan list qatorlari o'chiriladi
    unused: async () => {
      const used = new Set((op.result?.maps ?? []).map((m) => m.sheet_id));
      const keep = op.sheets.filter((s) => used.has(s.id));
      if (keep.length === op.sheets.length) { ui.toast(t("sheets.nothing_unused"), "info"); return; }   // hammasi ishlatilgan (#21)
      if (!(await askConfirm(t("sheets.remove_unused_q", { n: op.sheets.length - keep.length })))) return;
      save(keep);
    },
  };
  useHotkeys("sheets", {
    "delete,shift+delete": act.remove, "ctrl+arrowup": () => act.move(-1), "ctrl+arrowdown": () => act.move(1),
    "ctrl+pageup,alt+pageup,insert": act.insert, "ctrl+pagedown": act.add,
  });
  return (
    <div className="panel" {...scopeProps("sheets")}>
      <CsTabs right={<>
        <IconBtn icon={Warehouse} title={t("sheets.from_warehouse")} onClick={() => setPicker(true)} testid="sheets-from-warehouse" color="#1f6feb" />
        <IconBtn icon={InfinityIcon} title={t("sheets.unlimited")} onClick={act.unlimited} disabled={!sel} />
        <IconBtn icon={ArrowDownWideNarrow} title={t("app.sort")} onClick={act.sort} disabled={op.sheets.length < 2} testid="sheets-sort" />
        <IconBtn icon={Eraser} title={t("sheets.remove_unused")} onClick={() => void act.unused()} disabled={!op.result}
          testid="sheets-remove-unused" />
        <Sep />
        <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={() => act.move(-1)} disabled={!sel} />
        <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={() => act.move(1)} disabled={!sel} />
        <IconBtn icon={Plus} title={`${t("app.add")} (Ctrl+PgDn)`} onClick={act.add} testid="sheets-add" />
        <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={act.remove} disabled={!sel} color="#c0392b" />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
      </>} />
      <Grid<SheetRow> ref={grid} className="grow" rowData={rowData} columnDefs={cols} getRowId={(p) => p.data.id}
        testid="sheets-grid" rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onFirstDataRendered={(e) => selectFirst(e.api)} onRowDataUpdated={(e) => selectFirst(e.api)}
        onSelectionChanged={(e) => { const r = e.api.getSelectedRows()[0]; setSel(r && r.origin !== "result" ? r.id : null); }}
        getRowClass={(p) => (p.data?.origin === "result" ? (p.data.kindLabel === "business" ? "row-business" : "row-result")
          : p.data?.is_remnant ? "row-remnant" : "")} onCellValueChanged={onChange} />
      {picker && <RemnantPicker project={project} op={op} onClose={() => setPicker(false)} />}
    </div>
  );
}
