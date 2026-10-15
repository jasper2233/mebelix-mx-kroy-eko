// Loyiha holati belgisi (Не заказан / Заказан / Утвержден / Готов): ro'yxatda, sarlavhada, «Заказать» panelida.
import { useTranslation } from "react-i18next";
import "./order.css";

export function StatusBadge({ status, testid }: { status: number | null | undefined; testid?: string }) {
  const { t } = useTranslation();
  const s = Math.min(3, Math.max(0, Math.trunc(status ?? 0)));
  return <span className={`st-badge st-badge-${s}`} data-testid={testid}>{t(`status.${s}`)}</span>;
}
