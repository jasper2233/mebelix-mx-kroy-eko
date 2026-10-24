// OEE grafiklari — tashqi kutubxonasiz (SVG / HTML): chiziqli trend, gorizontal Pareto, ko'rsatkich kartasi, holat belgisi.
// Qoidalar: ingichka belgilar (2 px chiziq, ≤24 px ustun, 4 px yumaloq uch), ≥2 qator uchun legenda, rang faqat belgida (matn — oddiy
// rang), holat — rang + belgi + so'z (rang yolg'iz emas), hover'da yo'naltiruvchi chiziq va izoh, jadval ko'rinishi (dashboard).
import { useEffect, useRef, useState, type ReactNode, type RefObject } from "react";
import { useTranslation } from "react-i18next";
import { CircleCheck, CircleX, TriangleAlert } from "lucide-react";
import { cx } from "../../shared/ui";
import { fmtMin, pct, reasonName, type Band, type ParetoItem } from "./oeeApi";
import { uiZoom } from "../../shared/uiZoom";

// Qatorlar ranglari (kategoriya o'rinlari tartibi qat'iy): OEE — ko'k, A — to'q sariq, P — moviy-yashil, Q — sariq
export const LINE_COLORS: Record<string, string> = { oee: "#2a78d6", availability: "#eb6834", performance: "#1baf7a", quality: "#eda100" };
// Holat ranglari (<60 qizil, 60–85 sariq, ≥85 yashil) — doimiy; belgi + so'z bilan birga ishlatiladi
export const BAND_COLOR: Record<Band, string> = { low: "#d03b3b", mid: "#e0a100", high: "#0ca30c", none: "#98a4b0" };
const NEUTRAL_BAR = "#98a4b0";

export function BandChip({ band }: { band: Band }) {
  const { t } = useTranslation();
  if (band === "none") return <span className="oee-chip oee-chip-none" data-testid="band-none">{t("oee.band.none")}</span>;
  const Icon = band === "high" ? CircleCheck : band === "mid" ? TriangleAlert : CircleX;
  return (
    <span className={`oee-chip oee-chip-${band}`} data-testid={`band-${band}`}>
      <Icon size={13} color={BAND_COLOR[band]} strokeWidth={2.4} />{t(`oee.band.${band}`)}
    </span>
  );
}

export function KpiTile(props: { label: string; value: number | null | undefined; band: Band; hero?: boolean; sub?: ReactNode; testid: string;
  hint?: string }) {
  return (
    <div className={cx("oee-kpi", props.hero && "oee-kpi-hero")} style={{ borderLeftColor: BAND_COLOR[props.band] }} data-testid={props.testid} title={props.hint}>
      <div className="oee-kpi-label">{props.label}</div>
      <div className="oee-kpi-value" data-testid={`${props.testid}-value`}>{pct(props.value)}</div>
      <BandChip band={props.band} />
      {props.sub && <div className="oee-kpi-sub">{props.sub}</div>}
    </div>
  );
}

// ───────────────────────── Chiziqli trend ─────────────────────────
export interface Line { key: string; name: string; color: string; values: (number | null)[] }

function useWidth(): [RefObject<HTMLDivElement>, number] {
  const ref = useRef<HTMLDivElement>(null);
  const [w, setW] = useState(640);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const upd = () => setW(Math.max(280, Math.floor(el.clientWidth)));
    upd();
    if (typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(upd);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, w];
}

export function TrendChart(props: { labels: string[]; tips: string[]; lines: Line[]; bands: { low: number; high: number }; height?: number;
  ariaLabel: string }) {
  const { t } = useTranslation();
  const [ref, W] = useWidth();
  const [hover, setHover] = useState<number | null>(null);
  const H = props.height ?? 240;
  const m = { l: 38, r: 34, t: 12, b: 26 };
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const n = props.labels.length;
  const x = (i: number) => m.l + (n <= 1 ? iw / 2 : (i * iw) / (n - 1));
  const y = (v: number) => m.t + ih - Math.max(0, Math.min(1, v)) * ih;
  const maxLabels = Math.max(2, Math.floor(iw / 54));
  const step = Math.max(1, Math.ceil(n / maxLabels));
  const ticks = [0, 0.25, 0.5, 0.75, 1];
  if (n === 0) return <div className="oee-empty" ref={ref}>{t("oee.no_points")}</div>;

  const segs = (vals: (number | null)[]) => {
    const out: { d: string; single: number | null }[] = [];
    let cur: number[] = [];
    const flush = () => {
      if (cur.length === 1) out.push({ d: "", single: cur[0] });
      else if (cur.length > 1) out.push({ d: cur.map((i, k) => `${k ? "L" : "M"}${x(i).toFixed(1)} ${y(vals[i] as number).toFixed(1)}`).join(" "), single: null });
      cur = [];
    };
    vals.forEach((v, i) => { if (v === null || v === undefined) flush(); else cur.push(i); });
    flush();
    return out;
  };
  const onMove = (e: React.MouseEvent<SVGRectElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const px = e.clientX - r.left;
    setHover(Math.max(0, Math.min(n - 1, n <= 1 ? 0 : Math.round((px / r.width) * (n - 1)))));
  };
  const tipLeft = hover === null ? 0 : x(hover);
  const flip = tipLeft > W * 0.6;
  return (
    <div className="oee-chart" ref={ref} data-testid="oee-trend">
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={props.ariaLabel}>
        {ticks.map((tk) => (
          <g key={tk}>
            <line x1={m.l} x2={W - m.r} y1={y(tk)} y2={y(tk)} className="oee-grid" />
            <text x={m.l - 6} y={y(tk) + 4} textAnchor="end" className="oee-axis">{Math.round(tk * 100)}</text>
          </g>
        ))}
        {[props.bands.low, props.bands.high].map((b) => (
          <g key={b}>
            <line x1={m.l} x2={W - m.r} y1={y(b)} y2={y(b)} className="oee-target" />
            <text x={W - m.r + 4} y={y(b) + 4} className="oee-axis">{Math.round(b * 100)}</text>
          </g>
        ))}
        {props.labels.map((lb, i) => i % step === 0 ? (
          <text key={i} x={x(i)} y={H - 8} textAnchor="middle" className="oee-axis">{lb}</text>
        ) : null)}
        {hover !== null && <line x1={x(hover)} x2={x(hover)} y1={m.t} y2={m.t + ih} className="oee-cross" />}
        {props.lines.map((ln) => {
          const last = [...ln.values.keys()].reverse().find((i) => ln.values[i] !== null);
          return (
            <g key={ln.key} data-testid={`oee-line-${ln.key}`}>
              {segs(ln.values).map((s, i) => s.single !== null
                ? <circle key={i} cx={x(s.single)} cy={y(ln.values[s.single] as number)} r={4} fill={ln.color} stroke="#fff" strokeWidth={2} />
                : <path key={i} d={s.d} fill="none" stroke={ln.color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />)}
              {last !== undefined && <circle cx={x(last)} cy={y(ln.values[last] as number)} r={4} fill={ln.color} stroke="#fff" strokeWidth={2} />}
              {hover !== null && ln.values[hover] !== null && (
                <circle cx={x(hover)} cy={y(ln.values[hover] as number)} r={4.5} fill={ln.color} stroke="#fff" strokeWidth={2} />
              )}
            </g>
          );
        })}
        <rect x={m.l} y={m.t} width={iw} height={ih} fill="transparent" onMouseMove={onMove} onMouseLeave={() => setHover(null)} data-testid="oee-trend-hit" />
      </svg>
      {hover !== null && (
        <div className="oee-tip" style={flip ? { right: W - tipLeft + 10, top: 8 } : { left: tipLeft + 10, top: 8 }} data-testid="oee-trend-tip">
          <div className="oee-tip-head">{props.tips[hover]}</div>
          {props.lines.every((ln) => ln.values[hover] === null) && <div className="muted">{t("oee.no_data_point")}</div>}
          {props.lines.map((ln) => (
            <div key={ln.key} className="oee-tip-row">
              <span className="oee-dot" style={{ background: ln.color }} />{ln.name}
              <b>{pct(ln.values[hover] ?? null)}</b>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ───────────────────────── Pareto (gorizontal ustunlar) ─────────────────────────
export function ParetoChart(props: { items: ParetoItem[]; lang: string; idleCode: string }) {
  const { t } = useTranslation();
  const [tip, setTip] = useState<{ it: ParetoItem; x: number; y: number } | null>(null);
  if (!props.items.length) return <div className="oee-empty" data-testid="oee-pareto-empty">{t("oee.no_downtime")}</div>;
  const max = Math.max(...props.items.map((i) => i.minutes), 1);
  const h = t("oee.u.h"), mn = t("oee.u.min");
  return (
    <div className="oee-pareto" data-testid="oee-pareto">
      {props.items.map((it) => {
        const name = it.reason === props.idleCode ? t("oee.idle_name") : reasonName(it, props.lang, it.reason);
        return (
          <div key={it.reason} className="oee-par-row" data-testid={`oee-par-${it.reason}`}
            onMouseMove={(e) => setTip({ it, x: e.clientX / uiZoom(), y: e.clientY / uiZoom() })} onMouseLeave={() => setTip(null)}>
            <div className="oee-par-name" title={name}>{name}</div>
            <div className="oee-par-track">
              <div className="oee-par-bar" style={{ width: `${Math.max(1.5, (it.minutes / max) * 100)}%`,
                background: it.reason === props.idleCode ? NEUTRAL_BAR : LINE_COLORS.oee }} />
            </div>
            <div className="oee-par-val">{fmtMin(it.minutes, h, mn)}</div>
            <div className="oee-par-share">{pct(it.share ?? 0, 0)}</div>
            <div className="oee-par-cum" title={t("oee.cumulative")}>Σ {pct(it.cumulative ?? 0, 0)}</div>
          </div>
        );
      })}
      {tip && (
        <div className="oee-tip oee-tip-fixed" style={{ left: tip.x + 14, top: tip.y + 14 }}>
          <div className="oee-tip-head">{tip.it.reason === props.idleCode ? t("oee.idle_name") : reasonName(tip.it, props.lang, tip.it.reason)}</div>
          <div className="oee-tip-row">{t("oee.tip.minutes")}<b>{tip.it.minutes}</b></div>
          <div className="oee-tip-row">{t("oee.tip.count")}<b>{tip.it.count}</b></div>
          <div className="oee-tip-row">{t("oee.tip.share")}<b>{pct(tip.it.share ?? 0)}</b></div>
          <div className="oee-tip-row">{t("oee.cumulative")}<b>{pct(tip.it.cumulative ?? 0)}</b></div>
        </div>
      )}
    </div>
  );
}
