// GR sxemasi: paz kesimi — W (eni), D (chuqurligi), O (detal chetidan masofa). Sxematik (masshtabsiz), o'zimizning chizma.
import { useTranslation } from "react-i18next";

/** Paz eskizi: `vals` berilsa harflar (O / W / D) o'rniga haqiqiy qiymatlar yoziladi (GibLab kabi). */
export function GrSketch({ vals }: { vals?: { o: number; w: number; d: number } } = {}) {
  const { t } = useTranslation();
  return (
    <svg viewBox="0 0 280 130" width={280} height={130} className="gr-sketch" role="img" aria-label={t("gr.sketch")} data-testid="gr-sketch">
      <path d="M20 40 H80 V76 H124 V40 H260 V108 H20 Z" fill="#f2a541" stroke="#5a3a0a" strokeWidth="1.5" />
      <g stroke="#1b2733" strokeWidth="1" fill="#1b2733" fontSize="12" fontFamily="inherit">
        <line x1="20" y1="26" x2="80" y2="26" /><line x1="20" y1="21" x2="20" y2="31" /><line x1="80" y1="21" x2="80" y2="31" />
        <text x="50" y="18" textAnchor="middle" stroke="none">{vals ? fmtv(vals.o) : "O"}</text>
        <line x1="80" y1="26" x2="124" y2="26" /><line x1="124" y1="21" x2="124" y2="31" />
        <text x="102" y="18" textAnchor="middle" stroke="none">{vals ? fmtv(vals.w) : "W"}</text>
        <line x1="138" y1="40" x2="138" y2="76" /><line x1="133" y1="40" x2="143" y2="40" /><line x1="133" y1="76" x2="143" y2="76" />
        <text x="150" y="62" stroke="none">{vals ? fmtv(vals.d) : "D"}</text>
      </g>
      <text x="22" y="124" fontSize="11" fill="#6b7a89">{t("gr.sketch_edge")}</text>
    </svg>
  );
}

const fmtv = (v: number) => String(Math.round(v * 100) / 100);
