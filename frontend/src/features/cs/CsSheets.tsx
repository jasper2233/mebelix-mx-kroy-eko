// CS «Листы и остатки» (UI_SPEC §5.3): listlar, ombordagi qoldiqlarni qo'shish.
import { useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef } from "ag-grid-community";
import { ChevronDown, ChevronUp, CircleQuestionMark, Infinity as InfinityIcon, Plus, Trash, Warehouse } from "lucide-react";
import { call, useAppSettings, useRemnants } from "../../api/hooks";
import { post, put } from "../../api/client";
import type { Operation, Project, Remnant, StockSheet } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid, parseCellNum } from "../../shared/grid/Grid";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { Btn, Check, IconBtn, Modal, Sep } from "../../shared/ui";
import { CsTabs } from "./CsPanel";

export function RemnantPicker({ project, op, onClose }: { project: Project; op: Operation; onClose: () => void }) {
  const { t } = useTranslation();
  const [all, setAll] = useState(false);
  const code = (op.code || op.name || "").trim();
  const data = useRemnants(all ? undefined : code);
  const [sel, setSel] = useState<number[]>([]);
  const thick = op.cs_material?.thickness;
  const have = new Set(op.sheets.map((s) => s.source_remnant_id).filter(Boolean));
  const cols = useMemo<ColDef<Remnant>[]>(() => [
    { headerName: "ID", field: "id", width: 60, cellClass: "num" },
    { headerName: t("rem.material"), valueGetter: (p) => `${p.data?.material_code ?? ""} ${p.data?.material_name ?? ""}`, flex: 1 },
    { headerName: t("sheets.col.length"), field: "length", width: 80, cellClass: "num" },
    { headerName: t("sheets.col.width"), field: "width", width: 80, cellClass: "num" },
    { headerName: t("rem.thickness"), field: "thickness", width: 70, cellClass: (p) => (p.value !== thick ? "num warn" : "num") },
    { headerName: t("sheets.col.qty"), field: "qty", width: 60, cellClass: "num" },
    { headerName: t("u.m2"), field: "area_m2", width: 70, cellClass: "num" },
    { headerName: t("rem.source"), valueGetter: (p) => (p.data?.source_number ? `№${p.data.source_number}` : ""), width: 90 },
    { headerName: t("rem.note"), field: "note", width: 180 },
  ], [t, thick]);
  const rows = (data.data ?? []).filter((r) => !have.has(r.id));
  return (
    <Modal title={t("sheets.from_warehouse")} onClose={onClose} width={860} height={520} testid="remnant-picker"
      footer={<>
        <Check checked={all} onChange={setAll} label={t("rem.all_materials")} />
        <span className="grow" />
        <Btn kind="primary" label={t("app.add")} disabled={!sel.length} testid="remnant-add"
          onClick={() => void call(() => post(`/projects/${project.id}/operations/${op.id}/sheets/from-remnants`, { ids: sel })).then(onClose)} />
        <Btn label={t("app.cancel")} onClick={onClose} />
      </>}>
      <p className="muted">{t("rem.picker_hint", { code: code || "—" })}</p>
      <Grid<Remnant> className="grow" rowData={rows} columnDefs={cols} getRowId={(p) => String(p.data.id)}
        rowSelection={{ mode: "multiRow", checkboxes: true, headerCheckbox: true, enableClickSelection: true }}
        onSelectionChanged={(e) => setSel(e.api.getSelectedRows().map((r) => r.id))} />
    </Modal>
  );
}

/** Jadval qatori: kiruvchi list (op.sheets) yoki kroy natijasidagi qoldiq (origin = "result"). */
type SheetRow = StockSheet & { origin?: "result"; kindLabel?: "remnant" | "business"; numbers?: number[] };

export function CsSheets({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const app = useAppSettings();
  const grid = useRef<AgGridReact<SheetRow>>(null);
  const [sel, setSel] = useState<string | null>(null);
  const [picker, setPicker] = useState(false);
  const save = (sheets: StockSheet[]) => void call(() => put(`/projects/${project.id}/operations/${op.id}/sheets`, sheets));
  const numP = (int = false) => ({
    editable: true, cellClass: "num",
    valueParser: (p: { newValue: unknown; oldValue: unknown }) => {
      const v = parseCellNum(p.newValue);
      return v === null ? p.oldValue : int ? Math.max(0, Math.round(v)) : v;
    },
  });
  // kroy natijasidagi qoldiqlar — jadval oxirida (faqat o'qish): o'lcham bo'yicha jamlangan
  const resultRows = useMemo<SheetRow[]>(() => {
    const res = op.result;
    if (!res) return [];
    const agg = new Map<string, SheetRow>();
    for (const m of res.maps) for (const o of m.offcuts) {
      if (o.kind !== "remnant") continue;
      const key = `${o.business ? 1 : 0}:${o.length}x${o.width}`;
      const r = agg.get(key) ?? { id: `res-${key}`, length: o.length, width: o.width, qty: 0, is_remnant: false,
        trim_length: null, trim_width: null, end_offset_bottom: null, end_offset_right: null, description: "",
        used_qty: 0, source_remnant_id: null, origin: "result", kindLabel: o.business ? "business" : "remnant",
        numbers: [] as number[] } as SheetRow;
      r.qty += m.copies;
      if (o.number && r.numbers!.length < 6) r.numbers!.push(o.number);
      agg.set(key, r);
    }
    return [...agg.values()].map((r) => ({ ...r, description: r.numbers!.length ? `Д${r.numbers!.join(", Д")}` : "" }));
  }, [op.result]);
  const rowData = useMemo<SheetRow[]>(() => [...op.sheets, ...resultRows], [op.sheets, resultRows]);
  const ro = (p: { data?: SheetRow }) => p.data?.origin !== "result";
  const cols = useMemo<ColDef<SheetRow>[]>(() => [
    { headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum" },
    { headerName: t("sheets.col.kind"), colId: "kind", width: 130,
      valueGetter: (p) => t(`sheets.kind.${p.data?.origin === "result" ? p.data.kindLabel : (p.data?.is_remnant ? "stock" : "sheet")}`) },
    { headerName: t("sheets.col.length"), field: "length", width: 100, ...numP(), editable: ro },
    { headerName: t("sheets.col.width"), field: "width", width: 100, ...numP(), editable: ro },
    { headerName: t("sheets.col.qty"), field: "qty", width: 90, ...numP(true), editable: ro,
      valueFormatter: (p) => (p.value >= 10000 ? `${p.value}` : String(p.value)) },
    { headerName: t("sheets.col.area"), width: 90, cellClass: "num",
      valueGetter: (p) => (p.data ? Math.round((p.data.length * p.data.width) / 1e3) / 1e3 : 0) },
    { headerName: t("sheets.col.used"), field: "used_qty", width: 90, cellClass: "num" },
    { headerName: t("sheets.col.left"), width: 90, cellClass: "num", valueGetter: (p) => (p.data ? p.data.qty - p.data.used_qty : 0) },
    { headerName: t("sheets.col.trim_l"), field: "trim_length", width: 60, editable: ro, cellClass: "num",
      headerTooltip: t("sheets.col.trim_l_hint"), valueParser: (p) => parseCellNum(p.newValue) },
    { headerName: t("sheets.col.trim_w"), field: "trim_width", width: 60, editable: ro, cellClass: "num",
      headerTooltip: t("sheets.col.trim_w_hint"), valueParser: (p) => parseCellNum(p.newValue) },
    { headerName: t("sheets.col.end_b"), field: "end_offset_bottom", width: 60, editable: ro, cellClass: "num",
      headerTooltip: t("cs.p.offset_bottom"), valueParser: (p) => parseCellNum(p.newValue) },
    { headerName: t("sheets.col.end_r"), field: "end_offset_right", width: 60, editable: ro, cellClass: "num",
      headerTooltip: t("cs.p.offset_right"), valueParser: (p) => parseCellNum(p.newValue) },
    { headerName: t("sheets.col.note"), field: "description", flex: 1, minWidth: 160, editable: ro },
  ], [t]); // eslint-disable-line react-hooks/exhaustive-deps

  const onChange = (e: CellValueChangedEvent<SheetRow>) => {
    if (!e.data || e.data.origin === "result") return;
    const { origin: _o, kindLabel: _k, numbers: _n, ...row } = e.data;
    save(op.sheets.map((s) => (s.id === row.id ? { ...s, ...row } : s)));
  };
  const act = {
    add: () => save([...op.sheets, {
      length: app.data?.default_sheet_length ?? 2750, width: app.data?.default_sheet_width ?? 1830, qty: 10000,
    } as StockSheet]),
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
    delete: act.remove, "ctrl+arrowup": () => act.move(-1), "ctrl+arrowdown": () => act.move(1),
    "ctrl+pageup,alt+pageup,insert": act.add,
  });
  return (
    <div className="panel" {...scopeProps("sheets")}>
      <CsTabs right={<>
        <IconBtn icon={Warehouse} title={t("sheets.from_warehouse")} onClick={() => setPicker(true)} testid="sheets-from-warehouse" color="#1f6feb" />
        <IconBtn icon={InfinityIcon} title={t("sheets.unlimited")} onClick={act.unlimited} disabled={!sel} />
        <Sep />
        <IconBtn icon={ChevronUp} title={`${t("app.up")} (Ctrl+↑)`} onClick={() => act.move(-1)} disabled={!sel} />
        <IconBtn icon={ChevronDown} title={`${t("app.down")} (Ctrl+↓)`} onClick={() => act.move(1)} disabled={!sel} />
        <IconBtn icon={Plus} title={`${t("app.add")} (Ctrl+PgUp)`} onClick={act.add} testid="sheets-add" />
        <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={act.remove} disabled={!sel} color="#c0392b" />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
      </>} />
      <Grid<SheetRow> ref={grid} className="grow" rowData={rowData} columnDefs={cols} getRowId={(p) => p.data.id}
        testid="sheets-grid" rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onSelectionChanged={(e) => { const r = e.api.getSelectedRows()[0]; setSel(r && r.origin !== "result" ? r.id : null); }}
        getRowClass={(p) => (p.data?.origin === "result" ? (p.data.kindLabel === "business" ? "row-business" : "row-result")
          : p.data?.is_remnant ? "row-remnant" : "")} onCellValueChanged={onChange} />
      <div className="hint">{t("sheets.hint")}</div>
      {picker && <RemnantPicker project={project} op={op} onClose={() => setPicker(false)} />}
    </div>
  );
}
