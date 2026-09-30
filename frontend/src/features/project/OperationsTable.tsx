// «Операции» jadvali (UI_SPEC §3).
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef } from "ag-grid-community";
import {
  ArrowDownWideNarrow, ChevronDown, ChevronUp, CircleQuestionMark, CopyPlus, Drill, LayoutGrid, Library, Merge, Plus,
  Ribbon, Rows3, Trash,
} from "lucide-react";
import { call } from "../../api/hooks";
import { del, patch, post } from "../../api/client";
import type { OpType, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid } from "../../shared/grid/Grid";
import { askConfirm } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { Btn, IconBtn, Modal, Sep, Tabs, cx, money } from "../../shared/ui";
import { IMPLEMENTED, OP_ICONS, OpBadge } from "./opmeta";
import { CatalogPicker } from "./CatalogPicker";

export async function addOperation(pid: string, type: OpType, extra: Record<string, unknown> = {}, name = "") {
  const p = await call(() => post<Project>(`/projects/${pid}/operations`, { type, name, ...extra }));
  if (p) {
    const op = p.operations[p.operations.length - 1];
    useUI.getState().set({ opId: op.id, csTab: type === "CS" ? "parts" : useUI.getState().csTab });
  }
}

function OpTypeDialog({ onPick, onClose }: { onPick: (t: OpType) => void; onClose: () => void }) {
  const { t } = useTranslation();
  const types: OpType[] = ["O", "CS", "CN", "CL", "EL", "SP", "GR", "XNC", "LB"];
  return (
    <Modal title={t("ops.choose_type")} onClose={onClose} width={420} testid="op-type-dialog">
      <div className="type-list">
        {types.map((ty) => {
          const Icon = OP_ICONS[ty];
          const ok = IMPLEMENTED.includes(ty);
          return (
            <button key={ty} type="button" className={cx("type-item", !ok && "type-item-off")} disabled={!ok}
              onClick={() => onPick(ty)} title={ok ? "" : t("ops.later")}>
              <Icon size={16} /> <b>({ty})</b> {t(`optype.${ty}`)}
            </button>
          );
        })}
      </div>
    </Modal>
  );
}

export function OperationsTable({ project }: { project: Project }) {
  const { t } = useTranslation();
  const ui = useUI();
  const grid = useRef<AgGridReact<Operation>>(null);
  const [dlg, setDlg] = useState<"" | "type" | "catalog">("");
  const pid = project.id;
  const op = project.operations.find((o) => o.id === ui.opId);
  const defName = (ty: OpType) => {
    if (!["CS", "EL", "GR"].includes(ty)) return "";
    const n = project.operations.filter((o) => o.type === ty).length + 1;
    return t(`ops.default.${ty}`, { n });
  };
  const add = (ty: OpType) => void addOperation(pid, ty, {}, defName(ty));

  useEffect(() => {
    const api = grid.current?.api;
    if (!api || !ui.opId) return;
    const node = api.getRowNode(ui.opId);
    if (node && !node.isSelected()) { node.setSelected(true, true); api.ensureNodeVisible(node); }
  }, [ui.opId, project]);

  const cols = useMemo<ColDef<Operation>[]>(() => [
    { headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum" },
    { headerName: t("ops.col.type"), field: "type", width: 72, cellRenderer: (p: { value: OpType }) => <OpBadge type={p.value} /> },
    { headerName: t("ops.col.code"), field: "code", width: 180, editable: true },
    { headerName: t("ops.col.name"), field: "name", flex: 1, minWidth: 200, editable: true },
    { headerName: t("ops.col.cost_mat"), field: "cost_material", width: 110, cellClass: "num", valueFormatter: (p) => money(p.value) },
    { headerName: t("ops.col.cost_op"), field: "cost_operation", width: 110, cellClass: "num", valueFormatter: (p) => money(p.value) },
    { headerName: t("ops.col.cost"), width: 110, cellClass: "num",
      valueGetter: (p) => (p.data ? p.data.cost_material + p.data.cost_operation : 0), valueFormatter: (p) => money(p.value) },
    { headerName: t("ops.col.print"), field: "print", width: 56, cellRenderer: "agCheckboxCellRenderer", editable: true,
      cellEditor: "agCheckboxCellEditor", cellClass: "center" },
    { headerName: t("ops.col.new_page"), field: "new_page", width: 60, cellRenderer: "agCheckboxCellRenderer", editable: true,
      cellEditor: "agCheckboxCellEditor", cellClass: "center" },
  ], [t]);

  const onChange = (e: CellValueChangedEvent<Operation>) => {
    if (!e.data || !e.colDef.field) return;
    void call(() => patch(`/projects/${pid}/operations/${e.data!.id}`, { [e.colDef.field as string]: e.newValue }));
  };

  const act = {
    clone: () => op && void call(() => post(`/projects/${pid}/operations/${op.id}/clone`)),
    remove: async () => {
      if (!op) return;
      if (!(await askConfirm(t("ops.delete_q", { name: op.name || op.type }), undefined, { danger: true, ok: t("app.delete") }))) return;
      await call(() => del(`/projects/${pid}/operations/${op.id}`));
    },
    move: (d: "up" | "down") => op && void call(() => post(`/projects/${pid}/operations/${op.id}/move?direction=${d}`)),
    merge: () => void call(() => post(`/projects/${pid}/actions/merge-same`)),
    sort: () => void call(() => post(`/projects/${pid}/operations/sort?by=type`)),
  };

  useHotkeys("ops", {
    "ctrl+k": act.clone, delete: () => void act.remove(), "ctrl+arrowup": () => act.move("up"),
    "ctrl+arrowdown": () => act.move("down"),
  });

  const toolbar = (
    <>
      <IconBtn icon={LayoutGrid} title={t("ops.add_cs")} onClick={() => add("CS")} testid="add-cs" color="#b86e00" />
      <IconBtn icon={Ribbon} title={t("ops.add_el")} onClick={() => add("EL")} testid="add-el" color="#1f6feb" />
      <IconBtn icon={Rows3} title={t("ops.add_gr")} onClick={() => add("GR")} color="#7a5c2e" />
      <IconBtn icon={Drill} title={t("ops.add_xnc")} onClick={() => add("XNC")} color="#7d3cc9" />
      <Btn icon={Plus} small kind="ghost" label={t("ops.add_op")} onClick={() => setDlg("type")} testid="add-op" />
      <IconBtn icon={CopyPlus} title={`${t("app.clone")} (Ctrl+K)`} onClick={act.clone} disabled={!op} />
      <IconBtn icon={Library} title={t("ops.catalog")} onClick={() => setDlg("catalog")} />
      <IconBtn icon={Merge} title={t("ops.merge")} onClick={act.merge} />
      <IconBtn icon={ArrowDownWideNarrow} title={t("app.sort")} onClick={act.sort} />
      <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={() => void act.remove()} disabled={!op} color="#c0392b" />
      <Sep />
      <IconBtn icon={ChevronUp} title={`${t("app.up")} (Ctrl+↑)`} onClick={() => act.move("up")} disabled={!op} />
      <IconBtn icon={ChevronDown} title={`${t("app.down")} (Ctrl+↓)`} onClick={() => act.move("down")} disabled={!op} />
      <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
    </>
  );

  return (
    <div className="panel" {...scopeProps("ops")}>
      <Tabs tabs={[{ key: "ops", label: t("ops.tab"), testid: "tab-ops" }, { key: "products", label: t("products.tab"), testid: "tab-products" }]}
        value="ops" onChange={(k) => ui.set({ topTab: k })} right={toolbar} />
      <Grid<Operation> ref={grid} className="grow" rowData={project.operations} columnDefs={cols} testid="ops-grid"
        getRowId={(p) => p.data.id}
        rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onSelectionChanged={(e) => { const s = e.api.getSelectedRows()[0]; if (s && s.id !== useUI.getState().opId) ui.set({ opId: s.id, mapIndex: 1 }); }}
        onCellValueChanged={onChange} />
      {dlg === "type" && <OpTypeDialog onClose={() => setDlg("")} onPick={(ty) => { setDlg(""); add(ty); }} />}
      {dlg === "catalog" && <CatalogPicker onClose={() => setDlg("")} onPick={(item) => {
        setDlg("");
        const type: OpType = item.kind === "edge" ? "EL" : "CS";
        void addOperation(pid, type, { material_id: item.id });
      }} />}
    </div>
  );
}
