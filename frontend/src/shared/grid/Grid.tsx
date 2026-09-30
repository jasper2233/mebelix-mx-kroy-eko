// AG Grid Community o'rami: MebeliX mavzusi, ixcham qatorlar, Excel kabi tahrir, bizning yorliqlar.
import { forwardRef, useMemo } from "react";
import { AllCommunityModule, ModuleRegistry, themeBalham, type ColDef } from "ag-grid-community";
import { AgGridReact, type AgGridReactProps } from "ag-grid-react";
import { useTranslation } from "react-i18next";
import { suppressGridKey } from "../hotkeys";

ModuleRegistry.registerModules([AllCommunityModule]);

export const gridTheme = themeBalham.withParams({
  fontFamily: "var(--font)",
  fontSize: 12,
  headerFontSize: 12,
  headerHeight: 24,
  rowHeight: 22,
  spacing: 3,
  accentColor: "#1d6fb8",
  backgroundColor: "#ffffff",
  foregroundColor: "#1b2733",
  borderColor: "#c9d3dd",
  headerBackgroundColor: "#e4eaf1",
  headerTextColor: "#23384d",
  selectedRowBackgroundColor: "#d3e6fb",
  rowHoverColor: "#eef5fc",
  oddRowBackgroundColor: "#ffffff",
  wrapperBorderRadius: 0,
  cellHorizontalPadding: 5,
  columnBorder: { color: "#dde3ea" },
  headerColumnBorder: { color: "#c9d3dd" },
});

export type GridProps<T> = AgGridReactProps<T> & { className?: string; testid?: string };

function GridInner<T>(props: GridProps<T>, ref: React.ForwardedRef<AgGridReact<T>>) {
  const { t } = useTranslation();
  const { className, testid, defaultColDef, ...rest } = props;
  const dcd = useMemo<ColDef<T>>(() => ({
    resizable: true, sortable: false, suppressMovable: true, suppressKeyboardEvent: suppressGridKey,
    ...(defaultColDef ?? {}),
  }), [defaultColDef]);
  const localeText = useMemo(() => ({ noRowsToShow: t("app.no_rows"), loadingOoo: t("app.loading") }), [t]);
  return (
    <div className={`grid-wrap ${className ?? ""}`} data-testid={testid}>
      <AgGridReact<T> ref={ref} theme={gridTheme} animateRows={false} stopEditingWhenCellsLoseFocus
        tooltipShowDelay={500} tooltipHideDelay={15000} enterNavigatesVerticallyAfterEdit={false}
        localeText={localeText} defaultColDef={dcd} suppressDragLeaveHidesColumns {...rest} />
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
