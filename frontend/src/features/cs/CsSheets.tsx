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

export function CsSheets({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const ui = useUI();
  const app = useAppSettings();
  const grid = useRef<AgGridReact<StockSheet>>(null);
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
  const cols = useMemo<ColDef<StockSheet>[]>(() => [
    { headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum" },
    { headerName: t("sheets.col.length"), field: "length", width: 100, ...numP() },
    { headerName: t("sheets.col.width"), field: "width", width: 100, ...numP() },
    { headerName: t("sheets.col.qty"), field: "qty", width: 90, ...numP(true),
      valueFormatter: (p) => (p.value >= 10000 ? `${p.value}` : String(p.value)) },
    { headerName: t("sheets.col.area"), width: 90, cellClass: "num",
      valueGetter: (p) => (p.data ? Math.round((p.data.length * p.data.width) / 1e3) / 1e3 : 0) },
    { headerName: t("sheets.col.used"), field: "used_qty", width: 90, cellClass: "num" },
    { headerName: t("sheets.col.left"), width: 90, cellClass: "num", valueGetter: (p) => (p.data ? p.data.qty - p.data.used_qty : 0) },
    { headerName: t("sheets.col.trim_l"), field: "trim_length", width: 60, editable: true, cellClass: "num",
      valueParser: (p) => parseCellNum(p.newValue) },
    { headerName: t("sheets.col.trim_w"), field: "trim_width", width: 60, editable: true, cellClass: "num",
      valueParser: (p) => parseCellNum(p.newValue) },
    { headerName: t("sheets.col.note"), field: "description", flex: 1, minWidth: 160, editable: true },
  ], [t]); // eslint-disable-line react-hooks/exhaustive-deps

  const onChange = (e: CellValueChangedEvent<StockSheet>) => {
    if (!e.data) return;
    save(op.sheets.map((s) => (s.id === e.data!.id ? { ...s, ...e.data } : s)));
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
      <Grid<StockSheet> ref={grid} className="grow" rowData={op.sheets} columnDefs={cols} getRowId={(p) => p.data.id}
        testid="sheets-grid" rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onSelectionChanged={(e) => setSel(e.api.getSelectedRows()[0]?.id ?? null)}
        getRowClass={(p) => (p.data?.is_remnant ? "row-remnant" : "")} onCellValueChanged={onChange} />
      <div className="hint">{t("sheets.hint")}</div>
      {picker && <RemnantPicker project={project} op={op} onClose={() => setPicker(false)} />}
    </div>
  );
}
