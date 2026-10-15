// «Настройки → Общие»: «Минимальный размер детали» — umumiy standart (cs_defaults profili). Yangi CS operatsiyalari shu qiymat bilan
// yaratiladi (har sex uskunasiga qarab o'zgartiriladi); tayyor operatsiyada — «Параметры → Ограничения». Xulq o'zgarmaydi: kichik detal
// kroyga kirmaydi va ogohlantirish chiqadi (backend calc.py).
import { useTranslation } from "react-i18next";
import { call, qc, useDefaults } from "../../api/hooks";
import { put } from "../../api/client";
import type { CSCutParams, CSMaterialParams } from "../../api/types";
import { useUI } from "../../store/ui";
import { Field, Num } from "../../shared/ui";

type CsDefaults = { material: CSMaterialParams; cut: CSCutParams };

export function MinPartSetting() {
  const { t } = useTranslation();
  const q = useDefaults<CsDefaults>("cs_defaults");
  if (!q.data) return null;
  const save = async (v: number | null) => {
    const d = q.data!;
    const r = await call(() => put("/settings/cs_defaults/default", { material: { ...d.material, min_part_size: v ?? 30 }, cut: d.cut }));
    if (r) { void qc.invalidateQueries({ queryKey: ["defaults"] }); useUI.getState().toast(t("app.saved"), "ok"); }
  };
  return (
    <Field label={t("settings.min_part")} unit={t("u.mm")} hint={t("settings.min_part_hint")}>
      <Num value={q.data.material.min_part_size} min={0} max={1000} width={70} onCommit={(v) => void save(v)} testid="settings-min-part" />
    </Field>
  );
}
