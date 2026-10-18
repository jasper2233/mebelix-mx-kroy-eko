// EL / GR «Детали» jadvali uchun umumiy o'ram: sarlavha bosilsa saralash, Ctrl+Space — detal xossalari,
// Home / End — birinchi / oxirgi qator, ↑ / ↓ — qatorlar bo'ylab yurish (tanlov fokusga ergashadi), Ctrl+↑ / Ctrl+↓ — detal o'z
// operatsiyasi ichida ko'chadi, Ctrl+C — tanlangan qatorlar buferga, Ctrl+A — hammasini tanlash.
// `tabs` berilsa (EL) asboblar panelli yorliqlar qatorining o'ng tomonida (onlayn tizimdagidek), aks holda alohida qatorda.
import { useCallback, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { AgGridReact } from "ag-grid-react";
import type { CellFocusedEvent, CellValueChangedEvent, ColDef, GetRowIdParams, RowClassParams } from "ag-grid-community";
import { SquarePen, ChevronFirst, ChevronLeft, ChevronRight, ChevronLast, ChevronDown, ChevronUp, CircleQuestionMark, Columns3, Copy, ListChecks } from "lucide-react";
import type { Operation, Part, Project } from "../../api/types";
import { Grid, copyGridRows } from "../../shared/grid/Grid";
import { call } from "../../api/hooks";
import { post } from "../../api/client";
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
  /** yorliqlar qatori: asboblar paneli uning o'ng tomoniga qo'yiladi (berilmasa — jadval ustidagi alohida qator) */
  tabs?: (right: ReactNode) => ReactNode;
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

  // «Переместить вверх / вниз»: detal o'z (CS / CL) operatsiyasidagi ro'yxatda ko'chadi
  const move = useCallback((d: "up" | "down") => {
    const r = current();
    const hit = r ? findPart(props.project, r.part_id) : null;
    if (hit) void call(() => post(`/projects/${props.project.id}/operations/${hit.op.id}/parts/move?direction=${d}`, { ids: [hit.part.id] }));
  }, [current, props.project]);
  const copy = useCallback(async () => {
    const n = await copyGridRows(grid.current?.api);
    useUI.getState().toast(n ? t("ops.copied") : t("ops.copy_failed"), n ? "ok" : "error");
  }, [t]);
  const selectAll = useCallback(() => grid.current?.api.selectAll(), []);
  const help = props.onHelp ?? (() => useUI.getState().set({ section: "help" }));

  useHotkeys(SCOPE, { "ctrl+space": openProps, home: () => jump("first"), end: () => jump("last"),
    "ctrl+arrowup": () => move("up"), "ctrl+arrowdown": () => move("down"), "ctrl+c": () => void copy(), "ctrl+a": selectAll,
    ...(props.onColumns ? { "ctrl+p": () => props.onColumns?.() } : {}) });

  const onCellFocused = (e: CellFocusedEvent<T>) => {          // fokus qatorga ko'chsa — qator ham tanlanadi (↑ / ↓ / Home / End)
    if (e.rowIndex === null || e.rowIndex === undefined || e.rowPinned) return;
    const n = e.api.getDisplayedRowAtIndex(e.rowIndex);
    if (n && !n.isSelected()) n.setSelected(true, true);
  };
  const none = !props.rows.length;
  // onlayn tartib: Свойства | Первая, Предыдущая, Следующая, Последняя | ↑ ↓ | Настройки | Справка
  const tools = (
    <>
      <IconBtn icon={SquarePen} title={`${t("app.properties")} (Ctrl+Space)`} onClick={openProps} disabled={none}
        testid={`${props.testid}-props`} />
      <Sep />
      <IconBtn icon={ChevronFirst} title={`${t("cut.first")} (Home)`} onClick={() => jump("first")} disabled={none} />
      <IconBtn icon={ChevronLeft} title={`${t("cut.prev")} (↑)`} onClick={() => step(-1)} disabled={none} />
      <IconBtn icon={ChevronRight} title={`${t("cut.next")} (↓)`} onClick={() => step(1)} disabled={none} />
      <IconBtn icon={ChevronLast} title={`${t("cut.last")} (End)`} onClick={() => jump("last")} disabled={none} />
      <Sep />
      <IconBtn icon={ChevronUp} title={t("app.move_up")} onClick={() => move("up")} disabled={none} />
      <IconBtn icon={ChevronDown} title={t("app.move_down")} onClick={() => move("down")} disabled={none} />
      {props.onColumns && <>
        <Sep />
        <IconBtn icon={Columns3} title={`${t("cols.title")} (Ctrl+P)`} onClick={props.onColumns} testid={`${props.testid}-columns`} />
      </>}
      {props.tabs && <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={help} />}
    </>
  );

  return (
    <div className="op-parts grow" {...scopeProps(SCOPE)}>
      {props.tabs ? props.tabs(tools) : (
        <Toolbar className="subbar">
          {tools}
          <div className="grow" />
          {props.summary}
        </Toolbar>
      )}
      <Grid<T> ref={grid} className="grow" rowData={props.rows} columnDefs={props.columnDefs} testid={props.testid}
        defaultColDef={{ sortable: true }} getRowId={(p: GetRowIdParams<T>) => p.data.part_id}
        rowSelection={{ mode: "multiRow", checkboxes: false, headerCheckbox: false, enableClickSelection: true }} autoSelectFirst
        onCellFocused={onCellFocused} onCellDoubleClicked={(e) => { if (!e.colDef.editable) openProps(); }}
        onCellValueChanged={props.onCellValueChanged}
        // onlayn tartib: Копировать, Выделить все | Настройки | Справка; bizning qo'shimchalar (Свойства, qatorlar bo'ylab) — oxirida
        menu={() => {
          const none = !props.rows.length;
          return [
            { label: t("ops.copy"), hint: "Ctrl+C", icon: Copy, onClick: () => void copy(), disabled: none, testid: `${props.testid}-ctx-copy` },
            { label: t("ctx.select_all"), hint: "Ctrl+A", icon: ListChecks, onClick: selectAll, disabled: none },
            { sep: true, label: "" },
            ...(props.onColumns ? [{ label: t("cols.title"), hint: "Ctrl+P", icon: Columns3, onClick: props.onColumns, testid: `${props.testid}-ctx-settings` }] : []),
            { sep: true, label: "" },
            { label: t("menu.help"), hint: "F1", icon: CircleQuestionMark, onClick: help },
            { sep: true, label: "" },
            { label: t("app.properties"), hint: "Ctrl+Space", icon: SquarePen, onClick: openProps, disabled: none, testid: `${props.testid}-ctx-props` },
            { label: t("cut.first"), hint: "Home", icon: ChevronFirst, onClick: () => jump("first"), disabled: none },
            { label: t("cut.prev"), hint: "↑", icon: ChevronLeft, onClick: () => step(-1), disabled: none },
            { label: t("cut.next"), hint: "↓", icon: ChevronRight, onClick: () => step(1), disabled: none },
            { label: t("cut.last"), hint: "End", icon: ChevronLast, onClick: () => jump("last"), disabled: none },
          ];
        }}
        onSortChanged={(e) => e.api.refreshCells({ columns: ["n"], force: true })}
        getRowClass={props.rowClass ? (p: RowClassParams<T>) => (p.data ? props.rowClass!(p.data) : "") : undefined} />
      {propsFor && <PartProperties project={props.project} op={propsFor.op} part={propsFor.part} onClose={() => setPropsFor(null)} />}
    </div>
  );
}
