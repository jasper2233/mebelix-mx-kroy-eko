// «Параметры» yorlig'i: dasturdagi Par buyruqlari uchun kiritish maydonlari (tur, yorliq, ko'rinish sharti, faqat o'qish).
// Qiymatlar operatsiyada (XNCParams.par_values) saqlanadi; shablon dasturi o'zgarmaydi. Turlar: son (double / integer),
// mantiqiy (boolean), matn (string, W18 — qiymat matn sifatida saqlanadi, 200 belgigacha).
import { RotateCcw } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { XncParamState, XNCParams } from "../../api/types";
import { Check, Field, IconBtn, Num, Txt, fmt } from "../../shared/ui";

export const PAR_STRING_MAX = 200;

/** `x` — faqat `par_values` kerak (XNC operatsiyasi yoki mahsulot «Программа» si, W12). `onSet(nom, null)` — standartga qaytarish. */
export function ParForm({ x, params, onSet, title, hint }: {
  x: Pick<XNCParams, "par_values">; params: XncParamState[] | undefined; onSet: (name: string, v: number | string | null) => void;
  title?: string; hint?: string;
}) {
  const { t } = useTranslation();
  const list = (params ?? []).filter((p) => p.visible);
  const values = x.par_values ?? {};
  if (!params) return null;
  return (
    <div className="par-form" data-testid="xnc-par-form">
      <div className="form-h">{title ?? t("xnc.par.title")}</div>
      {list.length === 0 && <div className="par-note">{t("xnc.par.none")}</div>}
      {list.map((p) => {
        const overridden = p.name in values && !p.readonly;
        const def = p.default === null ? "" : typeof p.default === "string" ? p.default : fmt(p.default, 4);
        const unit = (
          <>
            {p.suffix}
            {overridden && <span className="par-def" title={t("xnc.par.reset")}> {t("xnc.par.default", { v: def })}</span>}
            {overridden && <span className="par-reset"><IconBtn icon={RotateCcw} title={t("xnc.par.reset")} testid={`par-reset-${p.name}`}
              onClick={() => onSet(p.name, null)} /></span>}
          </>
        );
        return (
          <Field key={p.name} label={p.label || p.name} unit={unit} hint={`${p.name}`}>
            {p.type === "boolean"
              ? <Check checked={!!p.value} disabled={p.readonly} testid={`par-${p.name}`} onChange={(v) => onSet(p.name, v ? 1 : 0)} />
              : p.type === "string"
                ? <Txt value={String(p.value ?? "")} disabled={p.readonly} width={220} maxLength={PAR_STRING_MAX} testid={`par-${p.name}`}
                    onCommit={(v) => onSet(p.name, v === "" ? null : v)} />
                : <Num value={typeof p.value === "number" ? p.value : null} readOnly={p.readonly} disabled={p.readonly} testid={`par-${p.name}`}
                    onCommit={(v) => onSet(p.name, v === null ? null : p.type === "integer" ? Math.round(v) : v)} allowEmpty />}
          </Field>
        );
      })}
      {list.length > 0 && <div className="par-note">{hint ?? t("xnc.par.edit_hint")}</div>}
    </div>
  );
}
