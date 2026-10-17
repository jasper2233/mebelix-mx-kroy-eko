// «Операции» jadvali (UI_SPEC §3).
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef, GridApi } from "ag-grid-community";
import {
  ArrowDownWideNarrow, ChevronDown, ChevronUp, CircleQuestionMark, CopyPlus, Drill, LayoutGrid, Library, Merge,
  Plus, Ribbon, Rows3, Trash,
} from "lucide-react";
import { call } from "../../api/hooks";
import { del, patch, post } from "../../api/client";
import type { OpType, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid } from "../../shared/grid/Grid";
import { askConfirm } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { Btn, IconBtn, Modal, Sep, Tabs, cx, money } from "../../shared/ui";
import { SortDialog } from "../../shared/SortDialog";
import { IMPLEMENTED, OP_ICONS, OpBadge } from "./opmeta";
import { CatalogPicker } from "./CatalogPicker";

export async function addOperation(pid: string, type: OpType, extra: Record<string, unknown> = {}, name = "") {
  const p = await call(() => post<Project>(`/projects/${pid}/operations`, { type, name, ...extra }));
  if (p) {
    const op = p.operations[p.operations.length - 1];
    useUI.getState().set({ opId: op.id, csTab: type === "CS" || type === "CL" || type === "CN" ? "parts" : useUI.getState().csTab });
  }
}

function OpTypeDialog({ onPick, onClose }: { onPick: (t: OpType) => void; onClose: () => void }) {
  const { t } = useTranslation();
  const types: OpType[] = ["O", "CS", "CN", "CL", "EL", "SP", "GR", "XNC", "LB"];
  return (
    <Modal title={t("ops.choose_type")} onClose={onClose} width={420} testid="op-type-dialog"
      footer={<Btn label={t("app.cancel")} onClick={onClose} />}>
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
  const [dlg, setDlg] = useState<"" | "type" | "catalog" | "sort">("");
  const pid = project.id;
  const op = project.operations.find((o) => o.id === ui.opId);
  const defName = (ty: OpType) => {
    // GibLab kabi standart nomlar: O — nomsiz, LB — «Этикетки: Детали и остатки» (raqamsiz)
    if (!["CS", "CN", "CL", "EL", "GR", "SP", "LB"].includes(ty)) return "";
    const n = project.operations.filter((o) => o.type === ty).length + 1;
    return t(`ops.default.${ty}`, { n });
  };
  // yangi kromka (EL) operatsiyasining id si: nomi darhol tahrir rejimida (D3). Id bo'yicha — boshqa operatsiyaga «sirqib» o'tmaydi
  const pendingEdit = useRef<string | null>(null);
  const add = async (ty: OpType) => {
    pendingEdit.current = null;
    const before = new Set(project.operations.map((o) => o.id));
    await addOperation(pid, ty, {}, defName(ty));
    const id = useUI.getState().opId;
    if (ty === "EL" && id && !before.has(id)) pendingEdit.current = id;
  };
  // Kutilayotgan tahrir: qator jadvalga tushgach (virtual ro'yxatda ko'rinmasa — avval unga suriladi, keyin muharrir ochiladi)
  const startPending = (api: GridApi<Operation>) => {
    const id = pendingEdit.current;
    if (!id) return;
    const node = api.getRowNode(id);
    if (!node || node.rowIndex == null) return;
    pendingEdit.current = null;
    const rowIndex = node.rowIndex;
    api.ensureIndexVisible(rowIndex);
    setTimeout(() => { if (api.getRowNode(id)) api.startEditingCell({ rowIndex, colKey: "name" }); }, 60);
  };

  // joriy operatsiya jadvalda tanlangan bo'lsin: effekt jadval API si tayyor bo'lmasdan ishlashi mumkin — shuning uchun
  // birinchi chizishda (onFirstDataRendered) ham chaqiriladi
  const syncSel = (api: GridApi<Operation>) => {
    const id = useUI.getState().opId;
    if (!id) return;
    const node = api.getRowNode(id);
    if (node && !node.isSelected()) { node.setSelected(true, true); api.ensureNodeVisible(node); }
  };
  useEffect(() => {
    const api = grid.current?.api;
    if (!api || !ui.opId) return;
    syncSel(api);
    startPending(api);
  }, [ui.opId, project]);

  const products = project.products;
  const ownerName = useMemo(() => (o: Operation) => {
    const id = o.o?.owner_product_id;
    return id ? products.find((pr) => pr.id === id)?.name : undefined;
  }, [products]);

  const cols = useMemo<ColDef<Operation>[]>(() => [
    { colId: "n", headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum" },
    { headerName: t("ops.col.type"), field: "type", width: 72, cellRenderer: (p: { value: OpType }) => <OpBadge type={p.value} /> },
    // (O) kodi bo'sh bo'lsa — egasi mahsulot nomi ko'rsatiladi («Код/Изделие», onlayn tizimdagidek); tahrir kodning o'zini o'zgartiradi
    { headerName: t("ops.col.code"), field: "code", width: 180, editable: true, valueParser: (p) => p.newValue ?? "",
      valueFormatter: (p) => p.value || (p.data?.type === "O" ? (ownerName(p.data) ?? "") : "") },
    { headerName: t("ops.col.name"), field: "name", flex: 1, minWidth: 200, editable: true, valueParser: (p) => p.newValue ?? "" },
    { headerName: t("ops.col.cost_mat"), headerTooltip: t("ops.col.cost_mat_hint"), field: "cost_material", width: 110, cellClass: "num", valueFormatter: (p) => money(p.value) },
    { headerName: t("ops.col.cost_op"), headerTooltip: t("ops.col.cost_op_hint"), field: "cost_operation", width: 110, cellClass: "num", valueFormatter: (p) => money(p.value) },
    { headerName: t("ops.col.cost"), headerTooltip: t("ops.col.cost_hint"), width: 110, cellClass: "num",
      valueGetter: (p) => (p.data ? p.data.cost_material + p.data.cost_operation : 0), valueFormatter: (p) => money(p.value) },
    { headerName: t("ops.col.print"), headerTooltip: t("ops.col.print_hint"), field: "print", width: 56, cellRenderer: "agCheckboxCellRenderer", editable: true,
      cellEditor: "agCheckboxCellEditor", cellClass: "center" },
    { headerName: t("ops.col.new_page"), headerTooltip: t("ops.col.new_page_hint"), field: "new_page", width: 60, cellRenderer: "agCheckboxCellRenderer", editable: true,
      cellEditor: "agCheckboxCellEditor", cellClass: "center" },
  ], [t, ownerName]);

  const onChange = (e: CellValueChangedEvent<Operation>) => {
    if (!e.data || !e.colDef.field) return;
    const v = e.newValue ?? (typeof e.oldValue === "string" ? "" : e.newValue);     // bo'sh katak null emas, "" yuboradi
    void call(() => patch(`/projects/${pid}/operations/${e.data!.id}`, { [e.colDef.field as string]: v }));
  };

  const act = {
    clone: () => op && void call(() => post(`/projects/${pid}/operations/${op.id}/clone`)),
    remove: async () => {
      if (!op) return;
      // Kroy operatsiyasi bilan birga uning detallariga bog'langan XNC dasturlari ham o'chadi — tasdiqda soni aytiladi
      const ids = new Set(op.parts.map((p) => p.id));
      const xnc = project.operations.filter((o) => o.type === "XNC" && o.xnc_part_id && ids.has(o.xnc_part_id)).length;
      const q = xnc ? t("ops.delete_xnc_q", { name: op.name || op.type, n: xnc }) : t("ops.delete_q", { name: op.name || op.type });
      if (!(await askConfirm(q, undefined, { danger: true, ok: t("app.delete") }))) return;
      await call(() => del(`/projects/${pid}/operations/${op.id}`));
    },
    move: (d: "up" | "down") => op && void call(() => post(`/projects/${pid}/operations/${op.id}/move?direction=${d}`)),
    merge: async () => { if (await call(() => post(`/projects/${pid}/actions/merge-same`))) ui.toast(t("common.done"), "ok"); },
    sort: () => setDlg("sort"),
  };

  useHotkeys("ops", {
    "ctrl+k": act.clone, delete: () => void act.remove(), "ctrl+arrowup": () => act.move("up"),
    "ctrl+arrowdown": () => act.move("down"),
    "ctrl+pageup,alt+pageup,insert,ctrl+pagedown": () => setDlg("type"),     // yangi operatsiya (turini tanlash)
  });

  const toolbar = (
    <>
      {/* tezkor qo'shish — CS, EL, GR, XNC (qolgan turlar «+ Операция» oynasida) */}
      <IconBtn icon={LayoutGrid} title={t("ops.add_cs")} onClick={() => add("CS")} testid="add-cs" color="#b86e00" />
      <IconBtn icon={Ribbon} title={t("ops.add_el")} onClick={() => add("EL")} testid="add-el" color="#1f6feb" />
      <IconBtn icon={Rows3} title={t("ops.add_gr")} onClick={() => add("GR")} color="#7a5c2e" />
      <IconBtn icon={Drill} title={t("ops.add_xnc")} onClick={() => add("XNC")} color="#7d3cc9" />
      <Btn icon={Plus} small kind="ghost" label={t("ops.add_op")} onClick={() => setDlg("type")} testid="add-op" />
      <IconBtn icon={CopyPlus} title={`${t("app.clone")} (Ctrl+K)`} onClick={act.clone} disabled={!op} />
      <IconBtn icon={Library} title={t("ops.catalog")} onClick={() => setDlg("catalog")} />
      <IconBtn icon={Merge} title={t("ops.merge")} onClick={() => void act.merge()} />
      <IconBtn icon={ArrowDownWideNarrow} title={t("app.sort")} onClick={act.sort} />
      <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={() => void act.remove()} disabled={!op} color="#c0392b" />
      <Sep />
      <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={() => act.move("up")} disabled={!op} />
      <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={() => act.move("down")} disabled={!op} />
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
        onCellFocused={(e) => {      // klaviatura (↑/↓/Home/End) bilan yurganda tanlov fokusga ergashadi
          if (e.rowIndex == null) return;
          const n = e.api.getDisplayedRowAtIndex(e.rowIndex);
          if (n && !n.isSelected()) n.setSelected(true, true);
        }}
        onCellValueChanged={onChange}
        onFirstDataRendered={(e) => syncSel(e.api)}
        onRowDataUpdated={(e) => { syncSel(e.api); startPending(e.api); }}
        menu={() => [
          { label: t("menu.add"), hint: "Ctrl+PgDn", onClick: () => setDlg("type"), testid: "ctx-op-add" },
          { label: t("app.clone"), hint: "Ctrl+K", onClick: act.clone, disabled: !op, testid: "ctx-op-clone" },
          { label: t("app.delete"), hint: "Del", onClick: () => void act.remove(), disabled: !op, testid: "ctx-op-delete" },
          { sep: true, label: "" },
          { label: t("app.move_up"), onClick: () => act.move("up"), disabled: !op },
          { label: t("app.move_down"), onClick: () => act.move("down"), disabled: !op },
          { sep: true, label: "" },
          { label: t("ops.catalog"), onClick: () => setDlg("catalog") },
          { label: t("ops.merge"), onClick: () => void act.merge() },
          { label: t("app.sort"), onClick: act.sort },
          { sep: true, label: "" },
          { label: t("menu.help"), hint: "F1", onClick: () => ui.set({ section: "help" }) },
        ]} />
      {dlg === "sort" && (
        <SortDialog testid="ops-sort" onClose={() => setDlg("")}
          cols={["type", "code", "name", "cost_material", "cost_operation", "cost", "print", "new_page"]
            .map((k) => ({ key: k, label: t(`sortcol.${k}`) }))}
          onApply={(specs) => void call(() => post(`/projects/${pid}/operations/sort`, specs))} />
      )}
      {dlg === "type" && <OpTypeDialog onClose={() => setDlg("")} onPick={(ty) => { setDlg(""); add(ty); }} />}
      {dlg === "catalog" && <CatalogPicker onClose={() => setDlg("")} onPick={(item) => {
        setDlg("");
        const type: OpType = item.kind === "edge" ? "EL" : item.kind === "surface" ? "SP" : item.kind === "linear" ? "CL" : "CS";
        void addOperation(pid, type, { material_id: item.id });
      }} />}
    </div>
  );
}
