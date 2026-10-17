// «Настройки колонок» (Ctrl+P): CS detallari ustunlari profillari — umumiy oyna (shared/grid/ColumnSettings) ustida.
import { useTranslation } from "react-i18next";
import { useUI } from "../../store/ui";
import { ColumnSettings as GridColumnSettings } from "../../shared/grid/ColumnSettings";
import type { ExprVar } from "../../shared/grid/userColumns";
import { normalizeColumns, type ColKey, type ColSetting } from "./columns";

export function ColumnSettings({ current, onClose, vars }: { current: ColSetting[]; onClose: () => void; vars: ExprVar[] }) {
  const { t } = useTranslation();
  const ui = useUI();
  return (
    <GridColumnSettings<ColKey> scope="part_columns" title={t("parts.columns")} profileId={ui.columnProfile}
      onProfile={(id) => ui.set({ columnProfile: id })} current={current} normalize={normalizeColumns} unit="px"
      label={(k) => t(`pc.${k}`)} desc={(k) => t(`pcd.${k}`)} onClose={onClose} user={{ prefix: "part", vars }} />
  );
}
