// XNC stanok cheklovlari xabarlari (xnc-stats → constraint_issues): ogohlantirish / xato; bosilsa — buyruq tanlanadi.
import { useTranslation } from "react-i18next";
import { cx } from "../../shared/ui";
import { pathOf, type XncIssue } from "./xncSettingsApi";
import { isUz, uzScript } from "../../i18n/lang";

export function XncIssues({ issues, turn, onPick }: { issues: XncIssue[]; turn?: number; onPick?: (path: number[]) => void }) {
  const { t, i18n } = useTranslation();
  if (!issues.length && !turn) return null;
  const lang = i18n.language;
  return (
    <div className="xs-issues" data-testid="xnc-issues">
      {issues.length > 0 && <div className="xs-issues-h">{t("xs.issues.title", { n: issues.length })}</div>}
      {issues.map((i, k) => {
        const p = onPick ? pathOf(i.command_path) : null;
        return (
          <div key={k} className={cx("xs-issue", i.level === "error" ? "xs-error" : "xs-warn", p && "xs-link")}
            data-testid={`xnc-issue-${i.code}`} data-level={i.level} onClick={p ? () => onPick?.(p) : undefined}
            title={p ? t("xs.issues.go") : undefined}>
            <b>{i.level === "error" ? "✖" : "⚠"}</b> {(isUz(lang) ? (i.text_uz !== undefined ? uzScript(i.text_uz, lang) : undefined) : i.text_ru) ?? i.text}
          </div>
        );
      })}
      {!!turn && <div className="xs-issue xs-info" data-testid="xnc-issue-turn">↻ {t("xs.issues.turn", { n: turn })}</div>}
    </div>
  );
}
