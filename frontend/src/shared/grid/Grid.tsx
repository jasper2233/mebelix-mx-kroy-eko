// AG Grid Community o'rami: MebeliX mavzusi, ixcham qatorlar, Excel kabi tahrir, bizning yorliqlar.
import { forwardRef, useCallback, useEffect, useMemo, useRef } from "react";
import {
  AllCommunityModule, ModuleRegistry, themeBalham, type ColDef, type FirstDataRenderedEvent, type GridApi, type IRowNode,
  type RowDataUpdatedEvent,
} from "ag-grid-community";
import { AgGridReact, type AgGridReactProps } from "ag-grid-react";
import { useTranslation } from "react-i18next";
import { RefreshCw } from "lucide-react";
import { suppressGridKey } from "../hotkeys";
import { useContextMenu, type CtxItem } from "./ContextMenu";
import "./grid.css";

ModuleRegistry.registerModules([AllCommunityModule]);

export const gridTheme = themeBalham.withParams({
  // xodimlar o'rgangan ko'rinish: Arial 11pt (14.67px), ixcham qatorlar (21px), sarlavha 20px, och-ko'k tanlov, hover yo'q
  fontFamily: "Arial, \"Arial Unicode MS\", Helvetica, sans-serif",
  fontSize: 14.67,
  headerFontSize: 14.67,
  headerFontWeight: 700,
  headerHeight: 20,
  rowHeight: 21,
  spacing: 3,
  accentColor: "#1d6fb8",
  backgroundColor: "#ffffff",
  foregroundColor: "#000000",
  borderColor: "#c9d3dd",
  headerBackgroundColor: "#eeeeee",
  headerTextColor: "#01243b",
  selectedRowBackgroundColor: "#bbdeff",
  rowHoverColor: "transparent",
  oddRowBackgroundColor: "#ffffff",
  wrapperBorderRadius: 0,
  cellHorizontalPadding: 4,
  columnBorder: { color: "#dde3ea" },
  headerColumnBorder: { color: "#c9d3dd" },
});

export type GridProps<T> = AgGridReactProps<T> & { className?: string; testid?: string;
  /** o'ng tugma menyusi: bandlar (ochilgan paytdagi holat bo'yicha); tanlov o'zgarmaydi */
  menu?: () => CtxItem[];
  /** hech qaysi qator tanlanmagan bo'lsa — birinchi (shartga mos) qator tanlanadi (ochilganda va ma'lumot yangilanganda) */
  autoSelectFirst?: boolean | ((d: T) => boolean);
  /** sarlavha o'ng burchagidagi kichik «Обновить» tugmasi (xodimlar o'rgangan jadvallardagidek) */
  onRefresh?: () => void;
};

/** Saralash belgilari: saralanadigan ustunda «◆», faol ustunda «▲» / «▼». */
const SORT_ICONS = {
  sortUnSort: '<span class="g-sort">◆</span>',
  sortAscending: '<span class="g-sort g-sort-on">▲</span>',
  sortDescending: '<span class="g-sort g-sort-on">▼</span>',
};

/** AG Grid ning ichki (ekran o'quvchi / maslahat) matnlari — bizning tilda. */
const AG_LOCALE_KEYS = [
  "ariaToggleCellValue", "ariaChecked", "ariaUnchecked", "ariaIndeterminate", "ariaRowSelect", "ariaRowDeselect",
  "ariaRowToggleSelection", "ariaRowSelectAll", "ariaRowSelectionDisabled", "ariaSortableColumn", "ariaSortableColumnWithCellSelection",
  "ariaMenuColumn", "ariaFilterColumn", "ariaColumnFiltered", "ariaInputEditor", "ariaHeaderSelection", "ariaColumnGroupExpansion",
  "ariaLabelColumnMenu", "ariaLabelColumnFilter", "ariaValidationErrorPrefix", "ariaPendingChange", "ariaSkeletonCellLoading",
  "ariaDeferSkeletonCellLoading", "invalidNumber", "invalidDate",
] as const;

/** Tanlov yo'q bo'lsa — birinchi ko'rinadigan (filtr / saralashdan keyin) mos qatorni tanlash. */
export function selectFirstIfNone<T>(api: GridApi<T>, ok?: (d: T) => boolean) {
  if (api.isDestroyed?.() || api.getSelectedNodes().length) return;
  let first: IRowNode<T> | null = null;
  api.forEachNodeAfterFilterAndSort((n) => {
    if (!first && n.data && n.selectable && (!ok || ok(n.data))) first = n;
  });
  if (first) (first as IRowNode<T>).setSelected(true, true);
}

/** «Копировать» [CTRL]+[C]: tanlangan (bo'lmasa fokusdagi) qatorlar ko'rinib turgan ustunlar bo'yicha, tab bilan ajratilgan matn
 *  sifatida buferga (Excel / boshqa jadvalga qo'yish uchun). Ko'chirilgan qatorlar sonini qaytaradi (0 — hech narsa / ruxsat yo'q). */
export async function copyGridRows<T>(api: GridApi<T> | undefined | null): Promise<number> {
  if (!api || api.isDestroyed?.()) return 0;
  let nodes = api.getSelectedNodes().filter((n) => n.data);
  if (!nodes.length) {
    const fc = api.getFocusedCell();
    const n = fc ? api.getDisplayedRowAtIndex(fc.rowIndex) : undefined;
    if (n?.data) nodes = [n];
  }
  if (!nodes.length) return 0;
  nodes.sort((a, b) => (a.rowIndex ?? 0) - (b.rowIndex ?? 0));
  const cols = api.getAllDisplayedColumns();
  const text = nodes.map((n) => cols.map((c) => {
    const v = api.getCellValue({ rowNode: n, colKey: c, useFormatter: true });
    return v === null || v === undefined ? "" : String(v).replace(/[\t\r\n]+/g, " ");
  }).join("\t")).join("\r\n");
  try { await navigator.clipboard.writeText(text); return nodes.length; } catch { return 0; }
}

/** Qator raqamini ko'rsatadigan ustunlar (colId) — tartib o'zgarganda yangilanadi. */
const NUM_COLS = ["n", "num", "op_num"];

function GridInner<T>(props: GridProps<T>, ref: React.ForwardedRef<AgGridReact<T>>) {
  const { t } = useTranslation();
  const { className, testid, defaultColDef, menu, autoSelectFirst, onRefresh, ...rest } = props;
  const ctx = useContextMenu(() => menu?.() ?? [], testid ? `${testid}-menu` : undefined);
  const dcd = useMemo<ColDef<T>>(() => ({
    resizable: true, sortable: false, unSortIcon: true, suppressMovable: true, suppressKeyboardEvent: suppressGridKey,
    ...(defaultColDef ?? {}),
  }), [defaultColDef]);
  const localeText = useMemo(() => ({
    noRowsToShow: t("app.no_rows"), loadingOoo: t("app.loading"),
    ...Object.fromEntries(AG_LOCALE_KEYS.map((k) => [k, t(`grid.${k}`)])),
  }), [t]);
  // foydalanuvchi «Выражение» ustunlari (shared/grid/userColumns.tsx): server javobi kelib ustun ta'rifi yangilanganda kataklar qayta
  // chiziladi (AG Grid ta'rif o'zgarishida qiymatni o'zi qayta hisoblamaydi)
  const apiRef = useRef<GridApi<T> | null>(null);
  useEffect(() => {
    const api = apiRef.current;
    const ids = (rest.columnDefs ?? []).flatMap((c) => ((c as ColDef<T>).context?.userExpr && (c as ColDef<T>).colId ? [(c as ColDef<T>).colId!] : []));
    if (api && !api.isDestroyed?.() && ids.length) api.refreshCells({ columns: ids, force: true });
  }, [rest.columnDefs]);
  const autoSel = useCallback((api: GridApi<T>) => {
    if (!autoSelectFirst) return;
    selectFirstIfNone(api, typeof autoSelectFirst === "function" ? autoSelectFirst : undefined);
  }, [autoSelectFirst]);
  // tartib o'zgarganda (klon, o'chirish, ko'chirish, saralash, Undo) qator raqami ustuni qayta hisoblansin
  const onRowDataUpdated = useCallback((e: RowDataUpdatedEvent<T>) => {
    const cols = NUM_COLS.filter((id) => e.api.getColumn(id));
    if (cols.length) e.api.refreshCells({ columns: cols, force: true });
    rest.onRowDataUpdated?.(e);
    autoSel(e.api);
  }, [rest.onRowDataUpdated, autoSel]); // eslint-disable-line react-hooks/exhaustive-deps
  const onFirstDataRendered = useCallback((e: FirstDataRenderedEvent<T>) => {
    rest.onFirstDataRendered?.(e);
    autoSel(e.api);
  }, [rest.onFirstDataRendered, autoSel]); // eslint-disable-line react-hooks/exhaustive-deps
  // o'ng tugma tanlovni / fokusni o'zgartirmasin: jadval o'z pointerdown / mousedown / contextmenu hodisalarini olmaydi (faqat
  // menyu bo'lsa; ushlash bosqichida — jadval ichki tinglovchilaridan oldin). Katak muharriri / matn maydonida — brauzer menyusi.
  const wrap = useRef<HTMLDivElement>(null);
  const openRef = useRef(ctx.open);
  openRef.current = ctx.open;
  const hasMenu = !!menu;
  useEffect(() => {
    const el = wrap.current;
    if (!el || !hasMenu) return;
    const inEditor = (e: Event) =>
      !!(e.target as HTMLElement).closest?.("input, textarea, select, .ag-cell-inline-editing, .ag-popup-editor");
    const down = (e: MouseEvent) => {
      if (e.button !== 2 || inEditor(e)) return;
      e.stopPropagation();
      if (e.type === "mousedown") e.preventDefault();      // brauzer katakka fokus bermasin (fokus → tanlov)
    };
    const menuEv = (e: MouseEvent) => {
      if (inEditor(e)) return;
      e.stopPropagation();
      openRef.current(e);
    };
    el.addEventListener("pointerdown", down, true);
    el.addEventListener("mousedown", down, true);
    el.addEventListener("contextmenu", menuEv, true);
    return () => {
      el.removeEventListener("pointerdown", down, true);
      el.removeEventListener("mousedown", down, true);
      el.removeEventListener("contextmenu", menuEv, true);
    };
  }, [hasMenu]);
  return (
    <div ref={wrap} className={`grid-wrap ${className ?? ""}`} data-testid={testid}>
      <AgGridReact<T> ref={ref} theme={gridTheme} animateRows={false} stopEditingWhenCellsLoseFocus
        tooltipShowDelay={500} tooltipHideDelay={15000} enterNavigatesVerticallyAfterEdit={false}
        localeText={localeText} defaultColDef={dcd} suppressDragLeaveHidesColumns icons={SORT_ICONS} {...rest}
        onRowDataUpdated={onRowDataUpdated} onFirstDataRendered={onFirstDataRendered}
        onGridReady={(e) => { apiRef.current = e.api; rest.onGridReady?.(e); }} />
      {onRefresh && (
        <button type="button" className="grid-refresh" title={t("menu.refresh")} aria-label={t("menu.refresh")}
          data-testid={testid ? `${testid}-refresh` : undefined} onClick={onRefresh}><RefreshCw size={11} /></button>
      )}
      {ctx.node}
    </div>
  );
}

export const Grid = forwardRef(GridInner) as <T>(p: GridProps<T> & { ref?: React.Ref<AgGridReact<T>> }) => JSX.Element;

/** Raqamli ustun (o'ngga tekislangan). */
export const numCol = { type: "rightAligned", cellClass: "num" } as const;

export function parseCellNum(v: unknown): number | null {
  if (v === null || v === undefined || v === "") return null;
  if (typeof v === "number") return v;
  const n = Number(String(v).replace(/\s/g, "").replace(",", "."));
  return Number.isFinite(n) ? n : null;
}
