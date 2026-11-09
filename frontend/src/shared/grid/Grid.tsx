// AG Grid Community o'rami: MebeliX mavzusi, ixcham qatorlar, Excel kabi tahrir, bizning yorliqlar.
import { forwardRef, useCallback, useEffect, useMemo, useRef } from "react";
import {
  AllCommunityModule, ModuleRegistry, themeBalham, type ColDef, type FirstDataRenderedEvent, type GridApi, type IRowNode,
  type RowDataUpdatedEvent, type CellFocusedEvent,
} from "ag-grid-community";
import { AgGridReact, type AgGridReactProps } from "ag-grid-react";
import { useTranslation } from "react-i18next";
import { RefreshCw } from "lucide-react";
import { suppressGridKey } from "../hotkeys";
import { uiZoom } from "../uiZoom";
import { useContextMenu, type CtxItem } from "./ContextMenu";
import "./grid.css";

ModuleRegistry.registerModules([AllCommunityModule]);

/** Tik aylantirish chizig'i eni. Windows 11 Chrome «ustma-ust» (overlay) chiziqlarida brauzer 0 qaytaradi va jadval joy
 *  qoldirmaydi — oxirgi ustun raqamlari chiziq ostida ko'rinmay qolardi (2026-10-23, «ОК» / «Всего»); 0 bo'lsa — 16 px. */
const SCROLLBAR_W = (() => {
  if (typeof document === "undefined" || !document.body) return 16;
  const d = document.createElement("div");
  d.style.cssText = "position:absolute;top:-200px;width:100px;height:100px;overflow:scroll;opacity:0";
  document.body.appendChild(d);
  const w = d.offsetWidth - d.clientWidth;
  d.remove();
  return w > 0 ? w : 16;
})();

// Ustun kengligini sudrash oyna masshtabida (shared/uiZoom): jadval sichqoncha siljishini ekran px da oladi, kenglik esa CSS px da —
// ustun chegarasi kursordan z marta sekin yurardi. Sudrash davomida siljish masshtabga bo'linadi (chegara kursor ostida qoladi).
if (typeof document !== "undefined") {
  let startX: number | null = null;
  const down = (e: MouseEvent) => {
    if (e.type === "mousedown" && startX !== null) return;           // pointerdown dan keyin keladigan mousedown
    startX = (e.target as Element | null)?.closest?.(".ag-header-cell-resize") ? e.clientX : null;
  };
  const fix = (e: MouseEvent) => {
    const z = uiZoom();
    if (startX === null || z === 1) return;
    Object.defineProperty(e, "clientX", { value: startX + (e.clientX - startX) / z });
  };
  const up = (e: MouseEvent) => { fix(e); setTimeout(() => { startX = null; }, 0); };
  for (const [ev, fn] of [["pointerdown", down], ["mousedown", down], ["pointermove", fix], ["mousemove", fix],
    ["pointerup", up], ["mouseup", up], ["pointercancel", up]] as const) document.addEventListener(ev, fn as EventListener, true);
}

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
  /** varaq ochilganda klaviatura fokusi jadvalning 1-qatoriga (TAB yuqoridagi tugmalardan emas, ro'yxatdan boshlanadi) */
  focusFirst?: boolean;
  /** o'ng tugma menyusi: bandlar (ochilgan paytdagi holat bo'yicha); tanlov o'zgarmaydi */
  menu?: () => CtxItem[];
  /** hech qaysi qator tanlanmagan bo'lsa — birinchi (shartga mos) qator tanlanadi (ochilganda va ma'lumot yangilanganda) */
  autoSelectFirst?: boolean | ((d: T) => boolean);
  /** sarlavha o'ng burchagidagi kichik «Обновить» tugmasi (xodimlar o'rgangan jadvallardagidek) */
  onRefresh?: () => void;
  /** lokal tizimdagidek matn kataklari (xodim videosi 2026-11-09): kursor kelgan katak matni belgilangan holatda (yozilsa — almashadi),
   *  ← / → — matn ichiga kirib tahrirlash (kursor oxirida / boshida), Ctrl+C — katak matni buferga (F2 siz) */
  textEdit?: boolean;
};

/** Katak oddiy matn muharriri bilan tahrirlanadimi (ro'yxat, katakcha — yo'q). */
function textEditable<T>(api: GridApi<T>, rowIndex: number, colId: string): boolean {
  const col = api.getColumn(colId);
  const node = api.getDisplayedRowAtIndex(rowIndex);
  if (!col || !node || !col.isCellEditable(node)) return false;
  const ed = col.getColDef().cellEditor;
  return ed == null || ed === "agTextCellEditor" || ed === "agNumberCellEditor" || ed === "agLargeTextCellEditor";
}

/** Fokusdagi katak matnini belgilash (brauzer tanlovi — ko'k fon, Ctrl+C uni oladi). */
function selectCellText(cell: Element | null) {
  const sel = typeof window !== "undefined" ? window.getSelection() : null;
  if (!sel) return;
  sel.removeAllRanges();
  if (!cell || !(cell.textContent ?? "").trim()) return;
  const r = document.createRange();
  r.selectNodeContents(cell);
  sel.addRange(r);
}

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

/** Jadvalning 1-qatori, birinchi katagiga («№») fokus — onlayn tizimdagidek birinchi TAB «Наименование» ga o'tadi; qator bo'lmasa —
 *  pastdagi yangi qator. Foydalanuvchi boshqa joyda
 *  yozayotgan bo'lsa (maydon, ochiq oyna) fokus tortib olinmaydi. */
function focusFirstCell<T>(api: GridApi<T>, force = false) {
  setTimeout(() => {
    if (api.isDestroyed?.()) return;
    const a = document.activeElement as HTMLElement | null;
    if (!force && a && a !== document.body
      && (a.closest("input, textarea, select, [contenteditable=true], .modal, [role=dialog]") || a.closest(".ag-root-wrapper"))) return;
    const col = api.getAllDisplayedColumns()[0];
    if (!col) return;
    if (api.getDisplayedRowCount() > 0) { api.ensureIndexVisible(0); api.setFocusedCell(0, col); }
    else if (api.getPinnedBottomRowCount() > 0) api.setFocusedCell(0, col, "bottom");
  }, 0);
}

/** `focusFirst` jadvallari (varaq yorlig'i bosilganda shu panel jadvaliga fokus — `focusGridIn`). */
const FOCUS_APIS = new WeakMap<Element, GridApi<unknown>>();
export function focusGridIn(from: Element | null) {
  // yorliqdan yuqoriga: shu panelning `focusFirst` jadvali (yorliqlar jadval asboblar qatorida ham bo'lishi mumkin)
  let el: Element | null = null;
  for (let n = from; n && !el; n = n.parentElement) el = n.querySelector(".grid-wrap[data-focus-first]");
  const api = el ? FOCUS_APIS.get(el) : undefined;
  if (api) focusFirstCell(api, true);
}

function GridInner<T>(props: GridProps<T>, ref: React.ForwardedRef<AgGridReact<T>>) {
  const { t } = useTranslation();
  const { className, testid, defaultColDef, menu, autoSelectFirst, onRefresh, focusFirst, textEdit, ...rest } = props;
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
  // Kursor qatori bilan birga yuradi: qatorlar soni o'zgarmay tartib o'zgarsa (↑ / ↓ bilan ko'chirish, saralash) kursor o'sha qatorga
  // (lokal tizimdagidek). Xodim videosi 2026-11-09: kursor eski joyda qolib, keyingi strelka / Ctrl+↑ boshqa qatorni ko'chirardi.
  const focusRow = useRef<{ id: string; count: number } | null>(null);
  const followFocus = (api: GridApi<T>) => {
    const f = focusRow.current;
    const fc = api.getFocusedCell();
    if (!f || !fc || fc.rowPinned != null || api.getDisplayedRowCount() !== f.count || api.getEditingCells().length) return;
    const node = api.getRowNode(f.id);
    if (!node || node.rowIndex == null || node.rowIndex === fc.rowIndex) return;
    const a = document.activeElement as HTMLElement | null;
    if (a && a !== document.body && !wrap.current?.contains(a) && a.closest("input, textarea, select, [contenteditable=true], .modal, [role=dialog]")) return;
    api.ensureIndexVisible(node.rowIndex);
    api.setFocusedCell(node.rowIndex, fc.column);
  };
  const onRowDataUpdated = useCallback((e: RowDataUpdatedEvent<T>) => {
    const cols = NUM_COLS.filter((id) => e.api.getColumn(id));
    if (cols.length) e.api.refreshCells({ columns: cols, force: true });
    rest.onRowDataUpdated?.(e);
    autoSel(e.api);
    followFocus(e.api);
  }, [rest.onRowDataUpdated, autoSel]); // eslint-disable-line react-hooks/exhaustive-deps
  const onFirstDataRendered = useCallback((e: FirstDataRenderedEvent<T>) => {
    rest.onFirstDataRendered?.(e);
    autoSel(e.api);
    if (focusFirst) focusFirstCell(e.api);
  }, [rest.onFirstDataRendered, autoSel, focusFirst]); // eslint-disable-line react-hooks/exhaustive-deps
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
  // Shift+↑/↓ — belgilangan oraliqni kengaytirish / qisqartirish (onlayn tizimda 2026-10-21 o'lchandi: «tayanch» qator — oxirgi oddiy
  // yoki Ctrl bosilgan / strelka bilan kelingan qator; Shift+bosish tayanchni o'zgartirmaydi). Faqat ko'p qatorli tanlovli jadvallarda.
  const anchor = useRef<number | null>(null);
  const ptrShift = useRef(false);
  const ptrDown = useRef(false);
  const selMode = (rest.rowSelection as { mode?: string } | undefined)?.mode;
  const multi = selMode === "multiRow";
  // qator tugma BOSILGAN zahoti belgilanadi (onlayndagidek). Jadval kutubxonasi tanlovni faqat `click` da (tugma qo'yib yuborilganda)
  // qilardi — kursor (oq katak) bosishda, ko'k qator ≈ 60–90 ms keyin: tez bosishda ko'k fon orqada qolardi (2026-10-21 o'lchov).
  const clickSel = !!selMode && (rest.rowSelection as { enableClickSelection?: boolean }).enableClickSelection === true;
  const rowSelection = useMemo(() => (clickSel ? { ...(rest.rowSelection as object), enableClickSelection: false } : rest.rowSelection),
    [rest.rowSelection, clickSel]) as typeof rest.rowSelection;
  const selectOnDown = (e: React.PointerEvent<HTMLDivElement>) => {
    const api = apiRef.current;
    if (!clickSel || !api || api.isDestroyed?.() || e.button !== 0) return;
    const t = e.target as HTMLElement;
    // qator tanlash katagi — kutubxonaning o'zi almashtiradi (bu yerda ham belgilansa, katak bosilishi uni qaytarib olib tashlardi)
    if (t.closest?.(".ag-selection-checkbox")) return;
    const row = t.closest?.(".ag-row") as HTMLElement | null;
    if (!row || !wrap.current?.contains(row) || row.closest(".ag-floating-bottom, .ag-floating-top")) return;
    const idx = Number(row.getAttribute("row-index"));
    const node = Number.isFinite(idx) ? api.getDisplayedRowAtIndex(idx) : undefined;
    if (!node || node.selectable === false) return;
    const ctrl = e.ctrlKey || e.metaKey;
    if (multi && e.shiftKey && anchor.current != null) {
      const nodes: IRowNode<T>[] = [];
      for (let k = Math.min(anchor.current, idx); k <= Math.max(anchor.current, idx); k++) { const n = api.getDisplayedRowAtIndex(k); if (n) nodes.push(n); }
      if (!ctrl) api.deselectAll();
      api.setNodesSelected({ nodes, newValue: true });
      return;                                                  // tayanch o'zgarmaydi
    }
    anchor.current = idx;
    if (multi && ctrl) { node.setSelected(!node.isSelected()); return; }
    if (!(node.isSelected() && api.getSelectedNodes().length === 1)) node.setSelected(true, true);
  };
  const shiftArrow = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!multi || !e.shiftKey || e.ctrlKey || e.altKey || e.metaKey || (e.key !== "ArrowDown" && e.key !== "ArrowUp")) return false;
    const api = apiRef.current;
    const t = e.target as HTMLElement;
    if (!api || api.isDestroyed?.() || t.closest("input, textarea, select, [contenteditable=true]") || api.getEditingCells().length) return false;
    const fc = api.getFocusedCell();
    if (!fc || fc.rowPinned != null) return false;
    const to = fc.rowIndex + (e.key === "ArrowDown" ? 1 : -1);
    e.preventDefault();
    e.stopPropagation();
    if (to < 0 || to >= api.getDisplayedRowCount()) return true;
    const a = anchor.current ?? fc.rowIndex;
    anchor.current = a;
    const lo = Math.min(a, to), hi = Math.max(a, to);
    const nodes: IRowNode<T>[] = [];
    for (let i = lo; i <= hi; i++) { const n = api.getDisplayedRowAtIndex(i); if (n) nodes.push(n); }
    api.deselectAll();
    api.setNodesSelected({ nodes, newValue: true });
    api.ensureIndexVisible(to);
    api.setFocusedCell(to, fc.column);
    return true;
  };
  // «№» ustunida sichqoncha bilan sudrash — oraliqdagi qatorlar belgilanadi (Ctrl bilan — oldingi tanlov saqlanadi)
  const drag = useRef<{ start: number; last: number; keep: IRowNode<T>[] } | null>(null);
  const numDown = (e: React.PointerEvent<HTMLDivElement>) => {
    const api = apiRef.current;
    const cell = (e.target as HTMLElement).closest?.(".ag-cell") as HTMLElement | null;
    const row = cell?.closest(".ag-row") as HTMLElement | null;
    if (!multi || !api || e.button !== 0 || !cell || !row || row.closest(".ag-floating-bottom, .ag-floating-top")
      || !NUM_COLS.includes(cell.getAttribute("col-id") ?? "")) return;
    const start = Number(row.getAttribute("row-index"));
    if (!Number.isFinite(start)) return;
    drag.current = { start, last: start, keep: e.ctrlKey || e.metaKey ? api.getSelectedNodes() : [] };
    const move = (ev: PointerEvent) => {
      const d = drag.current;
      if (!d || !(ev.buttons & 1) || api.isDestroyed?.()) return;
      const r = (document.elementFromPoint(ev.clientX, ev.clientY) as HTMLElement | null)?.closest(".ag-row") as HTMLElement | null;
      if (!r || !wrap.current?.contains(r) || r.closest(".ag-floating-bottom, .ag-floating-top")) return;
      const i = Number(r.getAttribute("row-index"));
      if (!Number.isFinite(i) || i === d.last) return;
      d.last = i;
      const nodes: IRowNode<T>[] = [...d.keep];
      for (let k = Math.min(d.start, i); k <= Math.max(d.start, i); k++) { const n = api.getDisplayedRowAtIndex(k); if (n) nodes.push(n); }
      api.deselectAll();
      api.setNodesSelected({ nodes, newValue: true });
      anchor.current = d.start;
      ev.preventDefault();
    };
    const up = () => { drag.current = null; window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  };
  const onCellFocused = useCallback((ev: CellFocusedEvent<T>) => {
    // sichqoncha bilan (Shift'siz) bosilgan qator — Shift+strelka uchun tayanch
    if (ptrDown.current && !ptrShift.current && ev.rowIndex != null && ev.rowPinned == null) anchor.current = ev.rowIndex;
    if (ev.rowIndex != null && ev.rowPinned == null) {
      const id = ev.api.getDisplayedRowAtIndex(ev.rowIndex)?.id;
      focusRow.current = id ? { id, count: ev.api.getDisplayedRowCount() } : null;
    }
    rest.onCellFocused?.(ev);
    if (textEdit) markText();
  }, [rest.onCellFocused, textEdit]); // eslint-disable-line react-hooks/exhaustive-deps
  // textEdit: kursor katagining matni belgilanadi (katak chizilib bo'lgach)
  const markText = () => {
    setTimeout(() => {
      const api = apiRef.current;
      if (!api || api.isDestroyed?.() || api.getEditingCells().length) return;
      const fc = api.getFocusedCell();
      const cell = wrap.current?.querySelector(".ag-cell-focus") ?? null;
      const ok = !!fc && fc.rowPinned == null && textEditable(api, fc.rowIndex, fc.column.getColId());
      const a = document.activeElement;
      if (cell && (a === cell || cell.contains(a))) selectCellText(ok ? cell : null);
    }, 0);
  };
  const textKeys = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const api = apiRef.current;
    const t = e.target as HTMLElement;
    if (!textEdit || !api || api.isDestroyed?.() || e.altKey || e.shiftKey || api.getEditingCells().length
      || t.closest("input, textarea, select, [contenteditable=true]")) return false;
    const fc = api.getFocusedCell();
    if (!fc || fc.rowPinned != null) return false;
    const colId = fc.column.getColId();
    const ctrl = e.ctrlKey || e.metaKey;
    if (ctrl && (e.key === "c" || e.key === "C" || e.code === "KeyC")) {
      // katak matni (ko'rinishdagidek) — tanlangan qatorlar emas; matn yo'q katakda — jadvalning o'z «Копировать» amali qoladi
      const node = api.getDisplayedRowAtIndex(fc.rowIndex);
      const v = node ? api.getCellValue({ rowNode: node, colKey: colId, useFormatter: true }) : null;
      const s = v == null ? "" : String(v);
      if (!s || !textEditable(api, fc.rowIndex, colId)) return false;
      e.preventDefault();
      e.stopPropagation();
      void navigator.clipboard?.writeText(s).catch(() => undefined);
      return true;
    }
    if (ctrl || (e.key !== "ArrowLeft" && e.key !== "ArrowRight") || !textEditable(api, fc.rowIndex, colId)) return false;
    e.preventDefault();
    e.stopPropagation();
    const atEnd = e.key === "ArrowRight";
    api.startEditingCell({ rowIndex: fc.rowIndex, colKey: colId });
    // muharrir o'z fokusini (matnni to'liq belgilash bilan) bir necha kadrdan keyin berishi mumkin — kursor muharrir tayyor bo'lgach
    // va yozish boshlanmaguncha qo'yiladi (aks holda birinchi harf eski matnni almashtirardi)
    let orig: string | null = null;
    const place = (k: number) => {
      const inp = wrap.current?.querySelector(".ag-cell-inline-editing input, .ag-cell-inline-editing textarea") as HTMLInputElement | null;
      if (inp) {
        if (orig === null) orig = inp.value;
        if (inp.value !== orig) return;                        // yozish boshlandi
        if (document.activeElement !== inp) inp.focus();
        const n = inp.value.length;
        try { inp.setSelectionRange(atEnd ? n : 0, atEnd ? n : 0); } catch { /* number input */ }
      }
      if (k < 6) requestAnimationFrame(() => place(k + 1));
    };
    place(0);
    return true;
  };
  // onlayndagidek: klaviatura bilan (TAB / Enter / strelka / Page / Home / End) kelingan qator belgilanadi — butun qator ko'k, kursor
  // katagi oq. Jadval kursorni surgandan keyin (keyingi vazifada) bajariladi — kechikib keladigan fokus hodisalariga bog'liq emas.
  const keySelect = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!multi || e.ctrlKey || e.altKey || e.metaKey) return;
    if (!["Tab", "Enter", "ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End"].includes(e.key)) return;
    if (e.shiftKey && (e.key === "ArrowUp" || e.key === "ArrowDown")) return;     // Shift+strelka — oraliq (shiftArrow)
    const api = apiRef.current;
    if (!api) return;
    setTimeout(() => {
      if (api.isDestroyed?.()) return;
      const fc = api.getFocusedCell();
      if (!fc || fc.rowPinned != null) return;
      anchor.current = fc.rowIndex;
      const n = api.getDisplayedRowAtIndex(fc.rowIndex);
      if (n && !(n.isSelected() && api.getSelectedNodes().length === 1)) n.setSelected(true, true);
    }, 0);
  };
  // onlayn yordam: [HOME] — birinchi qator, [END] — oxirgi qator (ustun saqlanadi); tahrir paytida — matn ichida (odatdagidek)
  const homeEnd = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (textKeys(e)) return;
    if (shiftArrow(e)) return;
    keySelect(e);
    if ((e.key !== "Home" && e.key !== "End") || e.ctrlKey || e.altKey || e.shiftKey || e.metaKey) return;
    const api = apiRef.current;
    const t = e.target as HTMLElement;
    if (!api || api.isDestroyed?.() || t.closest("input, textarea, select, [contenteditable=true]") || api.getEditingCells().length) return;
    const fc = api.getFocusedCell();
    const n = api.getDisplayedRowCount();
    if (!fc || !n) return;
    e.preventDefault();
    e.stopPropagation();
    const row = e.key === "Home" ? 0 : n - 1;
    api.ensureIndexVisible(row);
    api.setFocusedCell(row, fc.column);
  };
  return (
    <div ref={wrap} className={`grid-wrap ${textEdit ? "grid-text-edit " : ""}${className ?? ""}`} data-testid={testid} data-focus-first={focusFirst ? "" : undefined}
      onKeyDownCapture={homeEnd} onPointerDownCapture={(e) => { ptrShift.current = e.shiftKey; ptrDown.current = true; selectOnDown(e); numDown(e); }}
      onPointerUpCapture={() => { setTimeout(() => { ptrShift.current = false; ptrDown.current = false; }, 0); }}>
      <AgGridReact<T> ref={ref} theme={gridTheme} animateRows={false} stopEditingWhenCellsLoseFocus
        rowHeight={21} headerHeight={20}   // aniq qiymat: oyna masshtabida (shared/uiZoom) jadval o'lchamni CSS dan noto'g'ri o'lchamasin
        popupParent={typeof document !== "undefined" ? document.body : undefined}   // ro'yxatlar masshtabsiz body da — joyi aniq
        tooltipShowDelay={500} tooltipHideDelay={15000} enterNavigatesVerticallyAfterEdit={false}
        localeText={localeText} defaultColDef={dcd} suppressDragLeaveHidesColumns icons={SORT_ICONS}
        alwaysShowVerticalScroll scrollbarWidth={SCROLLBAR_W}   // tik chiziq doim joy egallaydi: oxirgi ustun («ОК», «Всего») ostida qolmaydi
        {...rest}
        rowSelection={rowSelection}
        onRowDataUpdated={onRowDataUpdated} onFirstDataRendered={onFirstDataRendered} onCellFocused={onCellFocused}
        onCellEditingStopped={(e) => { rest.onCellEditingStopped?.(e); if (textEdit) markText(); }}
        onGridReady={(e) => { apiRef.current = e.api; if (focusFirst && wrap.current) FOCUS_APIS.set(wrap.current, e.api as GridApi<unknown>); rest.onGridReady?.(e); }} />
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
