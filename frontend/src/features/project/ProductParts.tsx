// Mahsulot «Детали» oynasi («Изделия» jadvalidan): mahsulotning barcha operatsiyalardagi detallari bitta ro'yxatda —
// Материал (operatsiya), Длина, Ширина, Т-на, Кол, ОК, Наименование. Sarlavhadagi tugmalar: birinchi / oldingi / keyingi /
// oxirgi qator, o'chirish, yuqoriga / pastga (detal o'z operatsiyasi ichida ko'chadi). Yopish — «Ок».
import { useCallback, useMemo, useRef } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { ColDef } from "ag-grid-community";
import { ChevronDown, ChevronFirst, ChevronLast, ChevronLeft, ChevronRight, ChevronUp, Trash } from "lucide-react";
import { call } from "../../api/hooks";
import { post } from "../../api/client";
import type { Product, Project } from "../../api/types";
import { Grid } from "../../shared/grid/Grid";
import { askConfirm } from "../../shared/dialogs";
import { useHotkeys } from "../../shared/hotkeys";
import { Btn, IconBtn, Modal, Sep } from "../../shared/ui";
import { totalQty } from "../cs/sizes";

type Row = { id: string; opId: string; material: string; length: number; width: number; thickness: number | null;
  qty: number; total: number; name: string };

const SCOPE = "product-parts";

export function ProductParts({ project, product, onClose }: { project: Project; product: Product; onClose: () => void }) {
  const { t } = useTranslation();
  const grid = useRef<AgGridReact<Row>>(null);
  const rows = useMemo<Row[]>(() => project.operations.flatMap((op) => op.parts
    .filter((p) => p.product_id === product.id)
    .map((p) => ({
      id: p.id, opId: op.id, material: `(${op.type}) ${op.name}`, length: p.length, width: p.width,
      thickness: op.cs_material?.thickness ?? op.cl?.thickness ?? null, qty: p.qty, total: totalQty(project, p), name: p.name,
    }))), [project, product.id]);
  const cols = useMemo<ColDef<Row>[]>(() => [
    { colId: "n", headerName: "№", valueGetter: (p) => (p.node?.rowIndex ?? 0) + 1, width: 44, cellClass: "num rownum" },
    { colId: "material", headerName: t("pparts.col.material"), field: "material", flex: 1, minWidth: 220 },
    { colId: "length", headerName: t("pparts.col.length"), field: "length", width: 80, cellClass: "num", headerTooltip: t("pcd.length") },
    { colId: "width", headerName: t("pparts.col.width"), field: "width", width: 80, cellClass: "num", headerTooltip: t("pcd.width") },
    { colId: "thickness", headerName: t("pparts.col.thickness"), field: "thickness", width: 56, cellClass: "num" },
    { colId: "qty", headerName: t("pparts.col.qty"), field: "qty", width: 52, cellClass: "num" },
    { colId: "total", headerName: t("pparts.col.total"), field: "total", width: 52, cellClass: "num", headerTooltip: t("pcd.total") },
    { colId: "name", headerName: t("pparts.col.name"), field: "name", width: 220 },
  ], [t]);

  const cur = (): Row | undefined => grid.current?.api.getSelectedRows()[0];
  const go = useCallback((to: "first" | "prev" | "next" | "last") => {
    const api = grid.current?.api;
    const n = api?.getDisplayedRowCount() ?? 0;
    if (!api || !n) return;
    const at = api.getSelectedNodes()[0]?.rowIndex ?? -1;
    const idx = to === "first" ? 0 : to === "last" ? n - 1 : Math.max(0, Math.min(n - 1, at + (to === "prev" ? -1 : 1)));
    const node = api.getDisplayedRowAtIndex(idx);
    node?.setSelected(true, true);
    api.ensureIndexVisible(idx);
  }, []);
  const remove = async () => {
    const r = cur();
    if (!r) return;
    if (!(await askConfirm(t("pparts.delete_q", { name: r.name || r.material }), undefined, { danger: true, ok: t("app.delete") }))) return;
    await call(() => post(`/projects/${project.id}/operations/${r.opId}/parts/delete`, { ids: [r.id] }));
  };
  const move = (d: "up" | "down") => {
    const r = cur();
    if (r) void call(() => post(`/projects/${project.id}/operations/${r.opId}/parts/move?direction=${d}`, { ids: [r.id] }));
  };
  useHotkeys(SCOPE, {
    home: () => go("first"), end: () => go("last"), delete: () => void remove(),
    "ctrl+arrowup": () => move("up"), "ctrl+arrowdown": () => move("down"),
  });
  const none = !rows.length;
  return (
    <Modal title={t("pparts.title")} onClose={onClose} width={990} height={609} scope={SCOPE} testid="product-parts"
      headerRight={<>
        <IconBtn icon={ChevronFirst} title={`${t("cut.first")} (Home)`} onClick={() => go("first")} disabled={none} />
        <IconBtn icon={ChevronLeft} title={`${t("cut.prev")} (↑)`} onClick={() => go("prev")} disabled={none} />
        <IconBtn icon={ChevronRight} title={`${t("cut.next")} (↓)`} onClick={() => go("next")} disabled={none} />
        <IconBtn icon={ChevronLast} title={`${t("cut.last")} (End)`} onClick={() => go("last")} disabled={none} />
        <Sep />
        <IconBtn icon={Trash} title={`${t("app.delete")} (Del)`} onClick={() => void remove()} disabled={none} color="#c0392b"
          testid="product-parts-delete" />
        <Sep />
        <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={() => move("up")} disabled={none} />
        <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={() => move("down")} disabled={none} />
      </>}
      footer={<Btn kind="primary" label={t("app.ok")} onClick={onClose} testid="product-parts-ok" />}>
      <div style={{ height: "100%", minHeight: 420, display: "flex", flexDirection: "column" }}>
        <Grid<Row> ref={grid} className="grow" rowData={rows} columnDefs={cols} getRowId={(p) => p.data.id} testid="product-parts-grid"
          rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }} autoSelectFirst
          onCellFocused={(e) => { if (e.rowIndex != null) e.api.getDisplayedRowAtIndex(e.rowIndex)?.setSelected(true, true); }} />
      </div>
    </Modal>
  );
}
