// EL / GR «Детали» jadvali uchun umumiy o'ram: sarlavha bosilsa saralash, Ctrl+Space — detal xossalari,
// Home / End — birinchi / oxirgi qator, ↑ / ↓ — qatorlar bo'ylab yurish (tanlov fokusga ergashadi).
import { useCallback, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellFocusedEvent, ColDef, GetRowIdParams, RowClassParams } from "ag-grid-community";
import { SquarePen, ChevronFirst, ChevronLeft, ChevronRight, ChevronLast } from "lucide-react";
import type { Operation, Part, Project } from "../../api/types";
import { Grid } from "../../shared/grid/Grid";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { IconBtn, Sep, Toolbar } from "../../shared/ui";
import { PartProperties } from "../cs/PartDialogs";
import "./el.css";

type Row = { part_id: string };

const SCOPE = "oparts";

/** Jadval qatori → (detal, uning CS/CL operatsiyasi). */
function findPart(project: Project, partId: string): { op: Operation; part: Part } | null {
  for (const op of project.operations) {
    const part = op.parts.find((p) => p.id === partId);
    if (part) return { op, part };
  }
  return null;
}

export function OpPartsGrid<T extends Row>(props: {
  project: Project; rows: T[]; columnDefs: ColDef<T>[]; testid: string; rowClass?: (r: T) => string;
  /** Jadval ustidagi qo'shimcha yig'ma matn (jami va h.k.). */
  summary?: ReactNode;
}) {
  const { t } = useTranslation();
  const grid = useRef<AgGridReact<T>>(null);
  const [propsFor, setPropsFor] = useState<{ op: Operation; part: Part } | null>(null);

  /** Joriy qator: fokusdagi katak, bo'lmasa tanlangan qator. */
  const current = useCallback((): T | undefined => {
    const api = grid.current?.api;
    if (!api) return undefined;
    const fc = api.getFocusedCell();
    const byFocus = fc ? api.getDisplayedRowAtIndex(fc.rowIndex)?.data : undefined;
    return byFocus ?? api.getSelectedRows()[0];
  }, []);

  const openProps = useCallback(() => {
    const r = current();
    const hit = r ? findPart(props.project, r.part_id) : null;
    if (hit) setPropsFor(hit);
  }, [current, props.project]);

  const jump = useCallback((to: "first" | "last") => {
    const api = grid.current?.api;
    const n = api?.getDisplayedRowCount() ?? 0;
    if (!api || !n) return;
    const idx = to === "first" ? 0 : n - 1;
    const col = api.getFocusedCell()?.column ?? api.getAllDisplayedColumns()[0];
    api.ensureIndexVisible(idx);
    if (col) api.setFocusedCell(idx, col);
  }, []);

  const step = useCallback((d: number) => {                  // «Предыдущая» / «Следующая» qator
    const api = grid.current?.api;
    const n = api?.getDisplayedRowCount() ?? 0;
    if (!api || !n) return;
    const fc = api.getFocusedCell();
    const idx = Math.max(0, Math.min(n - 1, (fc?.rowIndex ?? -1) + d));
    const col = fc?.column ?? api.getAllDisplayedColumns()[0];
    api.ensureIndexVisible(idx);
    if (col) api.setFocusedCell(idx, col);
  }, []);

  useHotkeys(SCOPE, { "ctrl+space": openProps, home: () => jump("first"), end: () => jump("last") });

  const onCellFocused = (e: CellFocusedEvent<T>) => {          // fokus qatorga ko'chsa — qator ham tanlanadi (↑ / ↓ / Home / End)
    if (e.rowIndex === null || e.rowIndex === undefined || e.rowPinned) return;
    e.api.getDisplayedRowAtIndex(e.rowIndex)?.setSelected(true);
  };

  return (
    <div className="op-parts grow" {...scopeProps(SCOPE)}>
      <Toolbar className="subbar">
        <IconBtn icon={SquarePen} title={`${t("app.properties")} (Ctrl+Space)`} onClick={openProps} disabled={!props.rows.length}
          testid={`${props.testid}-props`} />
        <Sep />
        {/* GibLab kabi: birinchi / oldingi / keyingi / oxirgi qator */}
        <IconBtn icon={ChevronFirst} title={`${t("cut.first")} (Home)`} onClick={() => jump("first")} disabled={!props.rows.length} />
        <IconBtn icon={ChevronLeft} title={`${t("cut.prev")} (↑)`} onClick={() => step(-1)} disabled={!props.rows.length} />
        <IconBtn icon={ChevronRight} title={`${t("cut.next")} (↓)`} onClick={() => step(1)} disabled={!props.rows.length} />
        <IconBtn icon={ChevronLast} title={`${t("cut.last")} (End)`} onClick={() => jump("last")} disabled={!props.rows.length} />
        <div className="grow" />
        {props.summary}
      </Toolbar>
      <Grid<T> ref={grid} className="grow" rowData={props.rows} columnDefs={props.columnDefs} testid={props.testid}
        defaultColDef={{ sortable: true }} getRowId={(p: GetRowIdParams<T>) => p.data.part_id}
        rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }}
        onCellFocused={onCellFocused} onCellDoubleClicked={openProps}
        onSortChanged={(e) => e.api.refreshCells({ columns: ["n"], force: true })}
        getRowClass={props.rowClass ? (p: RowClassParams<T>) => (p.data ? props.rowClass!(p.data) : "") : undefined} />
      {propsFor && <PartProperties project={props.project} op={propsFor.op} part={propsFor.part} onClose={() => setPropsFor(null)} />}
    </div>
  );
}
