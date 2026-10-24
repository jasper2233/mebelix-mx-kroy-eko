// «Настройки колонок» (Ctrl+P): CS detallari ustunlari profillari — umumiy oyna (shared/grid/ColumnSettings) ustida.
import { useTranslation } from "react-i18next";
import { call, qc, useDefaults } from "../../api/hooks";
import { put } from "../../api/client";
import { useUI } from "../../store/ui";
import { ColumnSettings as GridColumnSettings } from "../../shared/grid/ColumnSettings";
import type { ExprVar } from "../../shared/grid/userColumns";
import { defaultWidth, normalizeColumns, partColsFromData, type ColKey, type ColSetting } from "./columns";

export function ColumnSettings({ current, onClose, vars }: { current: ColSetting[]; onClose: () => void; vars: ExprVar[] }) {
  const { t } = useTranslation();
  const ui = useUI();
  const dflt = useDefaults<{ columns?: ColSetting[]; unit?: string }>("part_columns");
  const normalize = (cols: ColSetting[] | undefined) => normalizeColumns(cols && cols.length ? cols : partColsFromData(dflt.data));
  // «Настройка значений по умолчанию»: joriy ustunlar «Стандарт» bo'ladi (profil tanlanmaganda ishlatiladi)
  const saveDefault = async (cols: ColSetting[]) => {
    const r = await call(() => put("/settings/part_columns/default", { columns: cols, unit: "ch" }));
    if (r) { ui.toast(t("cols.default_saved"), "ok"); await qc.invalidateQueries({ queryKey: ["defaults", "part_columns"] }); }
  };
  return (
    <GridColumnSettings<ColKey> scope="part_columns" title={t("cols.title")} profileId={ui.columnProfile}
      onProfile={(id) => ui.set({ columnProfile: id })} current={current} normalize={normalize} unit="ch"
      readCols={(d) => partColsFromData(d as { columns?: ColSetting[]; unit?: string })} dataExtra={{ unit: "ch" }}
      label={(k) => t(`pc.${k}`)} desc={(k) => t(`pcd.${k}`)} onClose={onClose} user={{ prefix: "part", vars }}
      onSaveDefault={saveDefault} defaultWidth={defaultWidth} testid="column-settings" />
  );
}
