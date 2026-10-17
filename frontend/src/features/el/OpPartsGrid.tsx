// EL / GR «Детали» jadvali uchun umumiy o'ram: sarlavha bosilsa saralash, Ctrl+Space — detal xossalari,
// Home / End — birinchi / oxirgi qator, ↑ / ↓ — qatorlar bo'ylab yurish (tanlov fokusga ergashadi).
import { useCallback, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellFocusedEvent, CellValueChangedEvent, ColDef, GetRowIdParams, RowClassParams } from "ag-grid-community";
import { SquarePen, ChevronFirst, ChevronLeft, ChevronRight, ChevronLast, Columns3 } from "lucide-react";
import type { Operation, Part, Project } from "../../api/types";
import { Grid } from "../../shared/grid/Grid";
import { useUI } from "../../store/ui";
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
  /** «Настройки» (ustunlar profili, Ctrl+P) — berilsa asboblar panelida tugma chiqadi */
  onColumns?: () => void;
  /** o'ng tugma menyusidagi «Справка» (bo'lmasa — umumiy yordam bo'limi) */
  onHelp?: () => void;
  /** tahrirlanadigan (foydalanuvchi «Настроенный Параметры») ustun katagi o'zgardi */
  onCellValueChanged?: (e: CellValueChangedEvent<T>) => void;
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

  useHotkeys(SCOPE, { "ctrl+space": openProps, home: () => jump("first"), end: () => jump("last"),
    ...(props.onColumns ? { "ctrl+p": () => props.onColumns?.() } : {}) });

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
        {props.onColumns && <>
          <Sep />
          <IconBtn icon={Columns3} title={`${t("parts.columns")} (Ctrl+P)`} onClick={props.onColumns} testid={`${props.testid}-columns`} />
        </>}
        <div className="grow" />
        {props.summary}
      </Toolbar>
      <Grid<T> ref={grid} className="grow" rowData={props.rows} columnDefs={props.columnDefs} testid={props.testid}
        defaultColDef={{ sortable: true }} getRowId={(p: GetRowIdParams<T>) => p.data.part_id}
        rowSelection={{ mode: "singleRow", checkboxes: false, enableClickSelection: true }} autoSelectFirst
        onCellFocused={onCellFocused} onCellDoubleClicked={(e) => { if (!e.colDef.editable) openProps(); }}
        onCellValueChanged={props.onCellValueChanged}
        menu={() => {
          const none = !props.rows.length;
          return [
            { label: t("app.properties"), hint: "Ctrl+Space", onClick: openProps, disabled: none, testid: `${props.testid}-ctx-props` },
            { sep: true, label: "" },
            { label: t("cut.first"), hint: "Home", onClick: () => jump("first"), disabled: none },
            { label: t("cut.prev"), hint: "↑", onClick: () => step(-1), disabled: none },
            { label: t("cut.next"), hint: "↓", onClick: () => step(1), disabled: none },
            { label: t("cut.last"), hint: "End", onClick: () => jump("last"), disabled: none },
            { sep: true, label: "" },
            ...(props.onColumns ? [{ label: t("cols.title"), hint: "Ctrl+P", onClick: props.onColumns, testid: `${props.testid}-ctx-settings` }] : []),
            { label: t("menu.help"), hint: "F1", onClick: props.onHelp ?? (() => useUI.getState().set({ section: "help" })) },
          ];
        }}
        onSortChanged={(e) => e.api.refreshCells({ columns: ["n"], force: true })}
        getRowClass={props.rowClass ? (p: RowClassParams<T>) => (p.data ? props.rowClass!(p.data) : "") : undefined} />
      {propsFor && <PartProperties project={props.project} op={propsFor.op} part={propsFor.part} onClose={() => setPropsFor(null)} />}
    </div>
  );
}
