// «Изделия» jadvali (UI_SPEC §4): mahsulot soni o'zgarsa — detallar ОК qayta hisoblanadi.
import { useEffect, useMemo, useRef, useState } from "react";
import { topTabs } from "./topTabs";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef, GridApi } from "ag-grid-community";
import {
  ArrowDownAZ, ChevronDown, ChevronUp, CircleQuestionMark, Copy, CopyPlus, Funnel, ListOrdered, PanelTopOpen, Plus, Settings2,
  SquarePen, Trash,
} from "lucide-react";
import { call } from "../../api/hooks";
import { del, patch, post } from "../../api/client";
import type { Product, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid, copyGridRows, parseCellNum } from "../../shared/grid/Grid";
import { useGridColumns, type GridKind } from "../../shared/grid/ColumnSettings";
import { askConfirm, askText } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { IconBtn, Sep, Tabs, money2 } from "../../shared/ui";
import { SortDialog } from "../../shared/SortDialog";
import { ProductProps } from "./ProductProps";
import { ProductParts } from "./ProductParts";

// «Настройки» (Ctrl+P) ustunlar katalogi — boshqa jadvallardagi kabi profil oynasi (nom, tavsif, kenglik belgilarda)
const PRODUCT_COLUMNS: GridKind = { scope: "products_columns", specs: [
  { key: "code", name: "products.col.code", width: 10 },
  { key: "name", name: "products.col.name", width: 27 },
  { key: "qty", name: "products.col.qty", desc: "products.cold.qty", width: 5 },
  { key: "cost_mat", name: "products.col.cost_mat", desc: "products.cold.cost_mat", width: 7 },
  { key: "cost_op", name: "products.col.cost_op", desc: "products.cold.cost_op", width: 7 },
  { key: "cost", name: "products.col.cost", desc: "products.cold.cost", width: 7 },
  { key: "total", name: "products.col.total", width: 7 },
] };

export function ProductsTable({ project }: { project: Project }) {
  const { t } = useTranslation();
  const ui = useUI();
  const grid = useRef<AgGridReact<Product>>(null);
  const pid = project.id;
  const prod = project.products.find((p) => p.id === ui.productId) ?? project.products[0];
  const rows = ui.zeroFilter ? project.products.filter((p) => p.qty > 0) : project.products;

  // joriy mahsulot qatori tanlangan bo'lsin (effekt jadval tayyor bo'lmasdan ishlashi mumkin — birinchi chizishda ham)
  const syncSel = (api: GridApi<Product>) => {
    if (!prod) return;
    const n = api.getRowNode(prod.id);
    if (n && !n.isSelected()) n.setSelected(true, true);
  };
  useEffect(() => {
    const api = grid.current?.api;
    if (api) syncSel(api);
  }, [prod?.id, project]); // eslint-disable-line react-hooks/exhaustive-deps

  const [partsDlg, setPartsDlg] = useState(false);
  const [propsDlg, setPropsDlg] = useState(false);
  const [sortDlg, setSortDlg] = useState(false);
  const cols = useMemo<ColDef<Product>[]>(() => ([
    { colId: "n", headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum" },
    { colId: "code", headerName: t("products.col.code"), field: "code", width: 140, editable: true, valueParser: (p) => p.newValue ?? "" },
    { colId: "name", headerName: t("products.col.name"), field: "name", flex: 1, minWidth: 200, editable: true, valueParser: (p) => p.newValue ?? "" },
    { colId: "qty", headerName: t("products.col.qty"), field: "qty", width: 70, editable: true, cellClass: "num",
      valueParser: (p) => Math.max(0, Math.round(parseCellNum(p.newValue) ?? p.oldValue)) },
    { colId: "cost_mat", headerName: t("products.col.cost_mat"), field: "cost_material", width: 110, cellClass: "num", valueFormatter: (p) => money2(p.value) },
    { colId: "cost_op", headerName: t("products.col.cost_op"), field: "cost_operation", width: 110, cellClass: "num", valueFormatter: (p) => money2(p.value) },
    // narxlar 1 dona uchun (backend), «Всего» = (material + ish) × soni
    { colId: "cost", headerName: t("products.col.cost"), width: 110, cellClass: "num",
      valueGetter: (p) => (p.data ? p.data.cost_material + p.data.cost_operation : 0),
      valueFormatter: (p) => money2(p.value) },
    { colId: "total", headerName: t("products.col.total"), width: 120, cellClass: "num",
      valueGetter: (p) => (p.data ? (p.data.cost_material + p.data.cost_operation) * p.data.qty : 0), valueFormatter: (p) => money2(p.value) },
  ] as ColDef<Product>[]), [t]);
  const colset = useGridColumns(PRODUCT_COLUMNS, cols);

  const onChange = (e: CellValueChangedEvent<Product>) => {
    if (!e.data || !e.colDef.field) return;
    const v = e.newValue ?? (typeof e.oldValue === "string" ? "" : e.newValue);
    void call(() => patch(`/projects/${pid}/products/${e.data!.id}`, { [e.colDef.field as string]: v }));
  };

  const act = {
    props: () => { if (prod) setPropsDlg(true); },
    insert: async () => {
      const name = await askText(t("products.new_name"), t("products.default_name", { n: project.products.length + 1 }));
      if (!name) return;
      const pos = prod ? project.products.findIndex((p) => p.id === prod.id) : project.products.length;
      const p = await call(() => post<Project>(`/projects/${pid}/products`, { name }, { position: pos }));
      if (p) ui.set({ productId: p.products[pos]?.id ?? null });
    },
    clone: () => prod && void call(() => post(`/projects/${pid}/products/${prod.id}/clone`)),
    remove: async () => {
      if (!prod) return;
      if (!(await askConfirm(t("products.delete_q", { name: prod.name }), t("products.delete_text"),
        { danger: true, ok: t("app.delete") }))) return;
      await call(() => del(`/projects/${pid}/products/${prod.id}`));
    },
    move: (d: "up" | "down") => prod && void call(() => post(`/projects/${pid}/products/${prod.id}/move?direction=${d}`)),
    zero: async () => {
      if (await askConfirm(t("products.zero_q"))) await call(() => post(`/projects/${pid}/products/zero-qty`));
    },
    sort: () => setSortDlg(true),
    // «Детали»: mahsulotning barcha operatsiyalardagi detallari oynasi
    parts: () => { if (prod) setPartsDlg(true); },
    copy: async () => {
      const n = await copyGridRows(grid.current?.api);
      ui.toast(n ? t("ops.copied") : t("ops.copy_failed"), n ? "ok" : "error");
    },
    settings: () => colset.open(),
  };

  useHotkeys("products", {
    "ctrl+space": act.props, "ctrl+k": act.clone, "delete,shift+delete": () => void act.remove(),
    "ctrl+arrowup": () => act.move("up"), "ctrl+arrowdown": () => act.move("down"),
    "ctrl+pageup,alt+pageup,insert,ctrl+pagedown": () => void act.insert(), "ctrl+f": () => ui.set({ zeroFilter: !ui.zeroFilter }),
    "ctrl+p": act.settings, "ctrl+c": () => void act.copy(),
  });

  // onlayn tartib va guruhlar: Свойства, Детали, Обнулить | Сортировка | Фильтр | ↑ ↓ | Вставить, Клонировать | Удалить | Настройки;
  // «Справка» — bizning qo'shimcha (oxirida)
  const toolbar = (
    <>
      <IconBtn icon={SquarePen} title={`${t("app.properties")} (Ctrl+Space)`} onClick={act.props} disabled={!prod} testid="product-props-btn" />
      <IconBtn icon={PanelTopOpen} title={t("products.parts")} onClick={act.parts} disabled={!prod} testid="product-parts-btn" />
      <IconBtn icon={ListOrdered} title={t("products.zero_all")} onClick={() => void act.zero()} />
      <Sep />
      <IconBtn icon={ArrowDownAZ} title={t("app.sort")} onClick={act.sort} />
      <Sep />
      <IconBtn icon={Funnel} title={`${t("products.zero_filter")} (Ctrl+F)`} active={ui.zeroFilter}
        onClick={() => ui.set({ zeroFilter: !ui.zeroFilter })} />
      <Sep />
      <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={() => act.move("up")} disabled={!prod} />
      <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={() => act.move("down")} disabled={!prod} />
      <Sep />
      <IconBtn icon={Plus} title={`${t("app.insert")} (Ctrl+PgUp)`} onClick={() => void act.insert()} testid="add-product" />
      <IconBtn icon={CopyPlus} title={`${t("app.clone")} (Ctrl+K)`} onClick={act.clone} disabled={!prod} />
      <Sep />
      <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={() => void act.remove()} disabled={!prod} color="#c0392b" />
      <IconBtn icon={Settings2} title={`${t("products.settings")} (Ctrl+P)`} onClick={act.settings} testid="products-settings" />
      <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
    </>
  );

  return (
    <div className="panel" {...scopeProps("products")}>
      <Tabs tabs={topTabs(t)}
        value="products" onChange={(k) => ui.set({ topTab: k })} right={toolbar} />
      <Grid<Product> ref={grid} className="grow" textEdit rowData={rows} columnDefs={colset.columnDefs} getRowId={(p) => p.data.id}
        testid="products-grid" rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onSelectionChanged={(e) => { const s = e.api.getSelectedRows()[0]; if (s) ui.set({ productId: s.id }); }}
        onCellFocused={(e) => {
          if (e.rowIndex == null) return;
          const n = e.api.getDisplayedRowAtIndex(e.rowIndex);
          if (n && !n.isSelected()) n.setSelected(true, true);
        }}
        onFirstDataRendered={(e) => syncSel(e.api)}
        onCellValueChanged={onChange}
        // onlayn tartib: Вставить, Удалить | Копировать, Клонировать | Сортировка, Фильтр | Обнулить, Детали | Настройки | Справка;
        // bizning qo'shimchalar (Свойства, ↑ ↓) — oxirida
        menu={() => [
          { label: t("app.insert"), hint: "Ctrl+PgUp", icon: Plus, onClick: () => void act.insert(), testid: "ctx-product-insert" },
          { label: t("app.delete"), hint: "Del", icon: Trash, onClick: () => void act.remove(), disabled: !prod },
          { sep: true, label: "" },
          { label: t("ops.copy"), hint: "Ctrl+C", icon: Copy, onClick: () => void act.copy(), disabled: !prod, testid: "ctx-product-copy" },
          { label: t("app.clone"), hint: "Ctrl+K", icon: CopyPlus, onClick: act.clone, disabled: !prod },
          { sep: true, label: "" },
          { label: t("app.sort"), icon: ArrowDownAZ, onClick: act.sort },
          { label: t("products.zero_filter"), hint: "Ctrl+F", icon: Funnel, onClick: () => ui.set({ zeroFilter: !ui.zeroFilter }) },
          { sep: true, label: "" },
          { label: t("products.zero_all"), icon: ListOrdered, onClick: () => void act.zero() },
          { label: t("products.parts"), icon: PanelTopOpen, onClick: act.parts, disabled: !prod, testid: "ctx-product-parts" },
          { sep: true, label: "" },
          { label: t("products.settings"), hint: "Ctrl+P", icon: Settings2, onClick: act.settings, testid: "ctx-product-settings" },
          { sep: true, label: "" },
          { label: t("menu.help"), hint: "F1", icon: CircleQuestionMark, onClick: () => ui.set({ section: "help" }) },
          { sep: true, label: "" },
          { label: t("app.properties"), hint: "Ctrl+Space", icon: SquarePen, onClick: act.props, disabled: !prod, testid: "ctx-product-props" },
          { label: t("app.move_up"), hint: "Ctrl+↑", icon: ChevronUp, onClick: () => act.move("up"), disabled: !prod },
          { label: t("app.move_down"), hint: "Ctrl+↓", icon: ChevronDown, onClick: () => act.move("down"), disabled: !prod },
        ]} />
      {propsDlg && prod && <ProductProps pid={pid} product={prod} onClose={() => setPropsDlg(false)} />}
      {sortDlg && (
        <SortDialog testid="products-sort" onClose={() => setSortDlg(false)}
          cols={["code", "name", "qty", "cost_material", "cost_operation", "cost"].map((k) => ({ key: k, label: t(`sortcol.${k}`) }))}
          onApply={(specs) => void call(() => post(`/projects/${pid}/products/sort`, specs))} />
      )}
      {colset.dialog}
      {partsDlg && prod && <ProductParts project={project} product={prod} onClose={() => setPartsDlg(false)} />}
    </div>
  );
}
