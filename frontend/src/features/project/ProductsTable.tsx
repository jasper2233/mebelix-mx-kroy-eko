// «Изделия» jadvali (UI_SPEC §4): mahsulot soni o'zgarsa — detallar ОК qayta hisoblanadi.
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellValueChangedEvent, ColDef } from "ag-grid-community";
import {
  ArrowDownAZ, ChevronDown, ChevronUp, CircleQuestionMark, CopyPlus, Funnel, ListOrdered, PanelTopOpen, Plus, Settings2,
  SquarePen, Trash,
} from "lucide-react";
import { call } from "../../api/hooks";
import { del, patch, post } from "../../api/client";
import type { Product, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Grid, parseCellNum } from "../../shared/grid/Grid";
import { askConfirm, askText } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { Btn, Check, IconBtn, Modal, Sep, Tabs, money } from "../../shared/ui";

export function ProductsTable({ project }: { project: Project }) {
  const { t } = useTranslation();
  const ui = useUI();
  const grid = useRef<AgGridReact<Product>>(null);
  const pid = project.id;
  const prod = project.products.find((p) => p.id === ui.productId) ?? project.products[0];
  const rows = ui.zeroFilter ? project.products.filter((p) => p.qty > 0) : project.products;

  useEffect(() => {
    const api = grid.current?.api;
    if (!api || !prod) return;
    const n = api.getRowNode(prod.id);
    if (n && !n.isSelected()) n.setSelected(true, true);
  }, [prod?.id, project]);

  const [colsDlg, setColsDlg] = useState(false);
  const cols = useMemo<ColDef<Product>[]>(() => ([
    { colId: "n", headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum" },
    { colId: "code", headerName: t("products.col.code"), field: "code", width: 140, editable: true },
    { colId: "name", headerName: t("products.col.name"), field: "name", flex: 1, minWidth: 200, editable: true },
    { colId: "qty", headerName: t("products.col.qty"), field: "qty", width: 70, editable: true, cellClass: "num",
      valueParser: (p) => Math.max(0, Math.round(parseCellNum(p.newValue) ?? p.oldValue)) },
    { colId: "cost_mat", headerName: t("products.col.cost_mat"), field: "cost_material", width: 110, cellClass: "num", valueFormatter: (p) => money(p.value) },
    { colId: "cost_op", headerName: t("products.col.cost_op"), field: "cost_operation", width: 110, cellClass: "num", valueFormatter: (p) => money(p.value) },
    // narxlar 1 dona uchun (backend), «Всего» = (material + ish) × soni
    { colId: "cost", headerName: t("products.col.cost"), width: 110, cellClass: "num",
      valueGetter: (p) => (p.data ? p.data.cost_material + p.data.cost_operation : 0),
      valueFormatter: (p) => money(p.value) },
    { colId: "total", headerName: t("products.col.total"), width: 120, cellClass: "num",
      valueGetter: (p) => (p.data ? (p.data.cost_material + p.data.cost_operation) * p.data.qty : 0), valueFormatter: (p) => money(p.value) },
  ] as ColDef<Product>[]).map((c) => ({ ...c, hide: ui.productHidden.includes(c.colId!) })), [t, ui.productHidden]);

  const onChange = (e: CellValueChangedEvent<Product>) => {
    if (!e.data || !e.colDef.field) return;
    void call(() => patch(`/projects/${pid}/products/${e.data!.id}`, { [e.colDef.field as string]: e.newValue }));
  };

  const act = {
    props: async () => {
      if (!prod) return;
      const name = await askText(t("products.props"), prod.name);
      if (name && name !== prod.name) await call(() => patch(`/projects/${pid}/products/${prod.id}`, { name }));
    },
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
    sort: () => void call(() => post(`/projects/${pid}/products/sort?by=name`)),
    parts: () => ui.set({ csTab: "parts" }),
  };

  useHotkeys("products", {
    "ctrl+space": () => void act.props(), "ctrl+k": act.clone, delete: () => void act.remove(),
    "ctrl+arrowup": () => act.move("up"), "ctrl+arrowdown": () => act.move("down"),
    "ctrl+pageup,alt+pageup,insert": () => void act.insert(), "ctrl+f": () => ui.set({ zeroFilter: !ui.zeroFilter }),
    "ctrl+p": () => setColsDlg(true),
  });

  const toolbar = (
    <>
      <IconBtn icon={SquarePen} title={`${t("app.properties")} (Ctrl+Space)`} onClick={() => void act.props()} disabled={!prod} />
      <IconBtn icon={PanelTopOpen} title={t("products.parts")} onClick={act.parts} />
      <IconBtn icon={ListOrdered} title={t("products.zero_all")} onClick={() => void act.zero()} />
      <IconBtn icon={ArrowDownAZ} title={t("app.sort")} onClick={act.sort} />
      <IconBtn icon={Funnel} title={`${t("products.zero_filter")} (Ctrl+F)`} active={ui.zeroFilter}
        onClick={() => ui.set({ zeroFilter: !ui.zeroFilter })} />
      <Sep />
      <IconBtn icon={ChevronUp} title={`${t("app.up")} (Ctrl+↑)`} onClick={() => act.move("up")} disabled={!prod} />
      <IconBtn icon={ChevronDown} title={`${t("app.down")} (Ctrl+↓)`} onClick={() => act.move("down")} disabled={!prod} />
      <IconBtn icon={Plus} title={`${t("app.insert")} (Ctrl+PgUp)`} onClick={() => void act.insert()} testid="add-product" />
      <IconBtn icon={CopyPlus} title={`${t("app.clone")} (Ctrl+K)`} onClick={act.clone} disabled={!prod} />
      <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={() => void act.remove()} disabled={!prod} color="#c0392b" />
      <IconBtn icon={Settings2} title={`${t("products.settings")} (Ctrl+P)`} onClick={() => setColsDlg(true)} testid="products-settings" />
      <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => ui.set({ section: "help" })} />
    </>
  );

  return (
    <div className="panel" {...scopeProps("products")}>
      <Tabs tabs={[{ key: "ops", label: t("ops.tab"), testid: "tab-ops" }, { key: "products", label: t("products.tab"), testid: "tab-products" }]}
        value="products" onChange={(k) => ui.set({ topTab: k })} right={toolbar} />
      <Grid<Product> ref={grid} className="grow" rowData={rows} columnDefs={cols} getRowId={(p) => p.data.id}
        testid="products-grid" rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onSelectionChanged={(e) => { const s = e.api.getSelectedRows()[0]; if (s) ui.set({ productId: s.id }); }}
        onCellValueChanged={onChange} />
      {colsDlg && (
        <Modal title={t("products.settings")} onClose={() => setColsDlg(false)} width={360} testid="products-columns"
          footer={<Btn kind="primary" label={t("app.ok")} onClick={() => setColsDlg(false)} />}>
          <div className="checks-col">
            {cols.filter((c) => c.colId !== "name").map((c) => (
              <Check key={c.colId} checked={!ui.productHidden.includes(c.colId!)} label={String(c.headerName)}
                onChange={(v) => ui.set({ productHidden: v ? ui.productHidden.filter((x) => x !== c.colId)
                  : [...ui.productHidden, c.colId!] })} />
            ))}
          </div>
        </Modal>
      )}
    </div>
  );
}
