// «Операции» jadvali (UI_SPEC §3). Asboblar paneli va o'ng tugma menyusi tartibi xodimlar o'rgangan tizimdagidek (2026-10-18 auditi D7):
// «Объединить» endi oyna orqali (bir xil turdagi operatsiyalar katakcha bilan), «Копировать» [CTRL]+[C], «Конвертировать в
// „Нестинговый раскрой“», «Выбрать элементы для печати», «Настройки» [CTRL]+[P] (ustunlar profillari, `ops_columns`).
import { useEffect, useMemo, useRef, useState } from "react";
import { topTabs } from "./topTabs";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef, GridApi } from "ag-grid-community";
import {
  ArrowDownWideNarrow, ChevronDown, ChevronUp, CircleQuestionMark, Copy, CopyPlus, Library, Merge,
  Plus, Printer, Settings2, Shapes, Trash,
} from "lucide-react";
import { call, qc } from "../../api/hooks";
import { del, patch, post } from "../../api/client";
import type { OpType, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid } from "../../shared/grid/Grid";
import { askConfirm } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { Btn, IconBtn, Modal, Sep, Tabs, cx, money } from "../../shared/ui";
import { SortDialog } from "../../shared/SortDialog";
import { useGridColumns, type GridKind } from "../../shared/grid/ColumnSettings";
import { OpPickDialog } from "./OpPickDialog";
import { IMPLEMENTED, OP_ICONS, OpBadge } from "./opmeta";
import { CatalogPicker } from "./CatalogPicker";

/** «Объединить» ishlaydigan turlar (server: api_ops_x1018.MERGEABLE). */
const MERGEABLE: OpType[] = ["CS", "CL", "CN", "EL"];

/** «Настройки» [CTRL]+[P]: ustunlar katalogi (№ va «Тип» — doim chapda). */
const OPS_COLUMNS: GridKind = { scope: "ops_columns", specs: [
  { key: "code", name: "ops.col.code", width: 15 },
  { key: "name", name: "ops.col.name", width: 27 },
  { key: "cost_material", name: "ops.col.cost_mat", desc: "ops.col.cost_mat_hint", width: 9 },
  { key: "cost_operation", name: "ops.col.cost_op", desc: "ops.col.cost_op_hint", width: 9 },
  { key: "cost", name: "ops.col.cost", desc: "ops.col.cost_hint", width: 9 },
  { key: "print", name: "ops.col.print", desc: "ops.col.print_hint", width: 4 },
  { key: "new_page", name: "ops.col.new_page", desc: "ops.col.new_page_hint", width: 4 },
] };

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
  const [dlg, setDlg] = useState<"" | "type" | "catalog" | "sort" | "merge" | "print">("");
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
  // (O) egasi nomi — doim joriy mahsulotlar ro'yxatidan (ref): import / yangi loyihada jadval qatorlari ustun ta'rifidan oldin
  // chizilardi va katak eski ro'yxat bilan bo'sh qolardi; mahsulot nomi / tarkibi o'zgarsa — ustun qayta chiziladi
  const productsRef = useRef(products);
  productsRef.current = products;
  const ownerName = useMemo(() => (o: Operation) => {
    const id = o.o?.owner_product_id;
    return id ? productsRef.current.find((pr) => pr.id === id)?.name : undefined;
  }, []);
  useEffect(() => {
    const api = grid.current?.api;
    if (api && !api.isDestroyed?.()) api.refreshCells({ columns: ["code"], force: true });
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
    { colId: "cost", headerName: t("ops.col.cost"), headerTooltip: t("ops.col.cost_hint"), width: 110, cellClass: "num",
      valueGetter: (p) => (p.data ? p.data.cost_material + p.data.cost_operation : 0), valueFormatter: (p) => money(p.value) },
    { headerName: t("ops.col.print"), headerTooltip: t("ops.col.print_hint"), field: "print", width: 56, cellRenderer: "agCheckboxCellRenderer", editable: true,
      cellEditor: "agCheckboxCellEditor", cellClass: "center" },
    { headerName: t("ops.col.new_page"), headerTooltip: t("ops.col.new_page_hint"), field: "new_page", width: 60, cellRenderer: "agCheckboxCellRenderer", editable: true,
      cellEditor: "agCheckboxCellEditor", cellClass: "center" },
  ], [t, ownerName]);
  const colset = useGridColumns(OPS_COLUMNS, cols);

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
    // «Объединить»: oyna — joriy operatsiya bilan bir xil turdagi operatsiyalar, belgilanganlari joriyga qo'shiladi
    merge: () => {
      if (!op) return;
      if (!MERGEABLE.includes(op.type)) { ui.toast(t("ops.merge_off"), "info"); return; }
      setDlg("merge");
    },
    sort: () => setDlg("sort"),
    // «Копировать» [CTRL]+[C]: joriy qator jadvaldagidek (tab bilan ajratilgan) buferga — Excel / boshqa joyga matn sifatida
    copy: async () => {
      if (!op) return;
      const row = [op.type, op.code, op.name, money(op.cost_material), money(op.cost_operation), money(op.cost_material + op.cost_operation)];
      try { await navigator.clipboard.writeText(row.join("\t")); ui.toast(t("ops.copied"), "ok"); }
      catch { ui.toast(t("ops.copy_failed"), "error"); }
    },
    convert: async () => {
      if (!op || op.type !== "CS") return;
      if (!(await askConfirm(t("ops.convert_q", { name: op.name || op.type }), op.result ? t("ops.convert_text") : undefined,
        { ok: t("ops.convert_ok") }))) return;
      if (await call(() => post(`/projects/${pid}/operations/${op.id}/convert`, { to: "CN" }))) ui.toast(t("common.done"), "ok");
    },
    settings: () => colset.open(),
  };
  const sameType = op ? project.operations.filter((o) => o.type === op.type && o.id !== op.id) : [];

  useHotkeys("ops", {
    // onlayn jadval yorliqlari: Del / Shift+Del — o'chirish, F8 — «Каталог товаров»
    "ctrl+k": act.clone, "delete,shift+delete": () => void act.remove(), f8: () => setDlg("catalog"), "ctrl+arrowup": () => act.move("up"),
    "ctrl+arrowdown": () => act.move("down"), "ctrl+c": () => void act.copy(), "ctrl+p": act.settings,
    "ctrl+pageup,alt+pageup,insert,ctrl+pagedown": () => setDlg("type"),     // yangi operatsiya (turini tanlash)
  });

  const toolbar = (
    <>
      {/* tezkor qo'shish — CS, EL, GR, XNC (qolgan turlar «+ Операция» oynasida) */}
      <IconBtn icon={OP_ICONS.CS} title={t("ops.add_cs")} onClick={() => add("CS")} testid="add-cs" />
      <IconBtn icon={OP_ICONS.EL} title={t("ops.add_el")} onClick={() => add("EL")} testid="add-el" />
      <IconBtn icon={OP_ICONS.GR} title={t("ops.add_gr")} onClick={() => add("GR")} />
      <IconBtn icon={OP_ICONS.XNC} title={t("ops.add_xnc")} onClick={() => add("XNC")} />
      <Btn icon={Plus} small kind="ghost" label={t("ops.add_op")} onClick={() => setDlg("type")} testid="add-op" />
      <IconBtn icon={CopyPlus} title={`${t("app.clone")} (Ctrl+K)`} onClick={act.clone} disabled={!op} />
      <IconBtn icon={Library} title={`${t("ops.catalog")} (F8)`} onClick={() => setDlg("catalog")} />
      <IconBtn icon={Merge} title={t("ops.merge")} onClick={act.merge} disabled={!op} testid="ops-merge" />
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
      <Tabs tabs={topTabs(t)}
        value="ops" onChange={(k) => ui.set({ topTab: k })} right={toolbar} />
      <Grid<Operation> ref={grid} className="grow" rowData={project.operations} columnDefs={colset.columnDefs} testid="ops-grid"
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
        onRefresh={() => void qc.invalidateQueries({ queryKey: ["project", pid] })}
        // onlayn tartib va guruhlar: Добавить, Клонировать | Удалить | ↑ ↓ | Копировать | Каталог товаров, Объединить, Сортировка,
        // Конвертировать, Выбрать элементы для печати | Настройки | Справка
        menu={() => [
          { label: t("menu.add"), hint: "Ctrl+PgDn", icon: Plus, onClick: () => setDlg("type"), testid: "ctx-op-add" },
          { label: t("app.clone"), hint: "Ctrl+K", icon: CopyPlus, onClick: act.clone, disabled: !op, testid: "ctx-op-clone" },
          { sep: true, label: "" },
          { label: t("app.delete"), hint: "Del", icon: Trash, onClick: () => void act.remove(), disabled: !op, testid: "ctx-op-delete" },
          { sep: true, label: "" },
          { label: t("app.move_up"), hint: "Ctrl+↑", icon: ChevronUp, onClick: () => act.move("up"), disabled: !op },
          { label: t("app.move_down"), hint: "Ctrl+↓", icon: ChevronDown, onClick: () => act.move("down"), disabled: !op },
          { sep: true, label: "" },
          { label: t("ops.copy"), hint: "Ctrl+C", icon: Copy, onClick: () => void act.copy(), disabled: !op, testid: "ctx-op-copy" },
          { sep: true, label: "" },
          { label: t("ops.catalog"), hint: "F8", icon: Library, onClick: () => setDlg("catalog") },
          { label: t("ops.merge"), icon: Merge, onClick: act.merge, disabled: !op, testid: "ctx-op-merge" },
          { label: t("app.sort"), icon: ArrowDownWideNarrow, onClick: act.sort },
          { label: t("ops.convert_cn"), icon: Shapes, onClick: () => void act.convert(), disabled: op?.type !== "CS", testid: "ctx-op-convert" },
          { label: t("ops.print_select"), icon: Printer, onClick: () => setDlg("print"), testid: "ctx-op-print" },
          { sep: true, label: "" },
          { label: t("ops.settings"), hint: "Ctrl+P", icon: Settings2, onClick: act.settings, testid: "ctx-op-settings" },
          { sep: true, label: "" },
          { label: t("menu.help"), hint: "F1", icon: CircleQuestionMark, onClick: () => ui.set({ section: "help" }) },
        ]} />
      {dlg === "sort" && (
        <SortDialog testid="ops-sort" onClose={() => setDlg("")}
          cols={["type", "code", "name", "cost_material", "cost_operation", "cost", "print", "new_page"]
            .map((k) => ({ key: k, label: t(`sortcol.${k}`) }))}
          onApply={(specs) => void call(() => post(`/projects/${pid}/operations/sort`, specs))} />
      )}
      {dlg === "merge" && op && (
        <OpPickDialog title={t("ops.merge")} testid="merge-dialog" ops={sameType} empty={t("ops.merge_none")}
          head={<><OpBadge type={op.type} paren /> {op.name || op.code}</>}
          onClose={() => setDlg("")}
          onOk={async (ids) => {
            setDlg("");
            if (!ids.length) return;
            if (await call(() => post(`/projects/${pid}/operations/${op.id}/merge`, { ids }))) ui.toast(t("ops.merged", { n: ids.length }), "ok");
          }} />
      )}
      {dlg === "print" && (
        <OpPickDialog title={t("ops.print_select")} testid="print-select-dialog" ops={project.operations}
          initial={project.operations.filter((o) => o.print).map((o) => o.id)} head={t("ops.print_select_head")}
          onClose={() => setDlg("")}
          onOk={async (ids) => {
            setDlg("");
            const on = new Set(ids);
            for (const o of project.operations.filter((x) => x.print !== on.has(x.id)))
              await call(() => patch(`/projects/${pid}/operations/${o.id}`, { print: on.has(o.id) }));
          }} />
      )}
      {colset.dialog}
      {dlg === "type" && <OpTypeDialog onClose={() => setDlg("")} onPick={(ty) => { setDlg(""); add(ty); }} />}
      {dlg === "catalog" && <CatalogPicker onClose={() => setDlg("")} onPick={(item) => {
        setDlg("");
        const type: OpType = item.kind === "edge" ? "EL" : item.kind === "surface" ? "SP" : item.kind === "linear" ? "CL" : "CS";
        void addOperation(pid, type, { material_id: item.id });
      }} />}
    </div>
  );
}
