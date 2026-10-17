// OEE paneli: davr va stanok tanlovi, 4 ta katta ko'rsatkich (OEE, A, P, Q), trend, to'xtash Pareto, stanoklar va smenalar jadvali.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { FlaskConical, Plus, RefreshCw, TriangleAlert, ArrowUpFromLine } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { download, post } from "../../api/client";
import { useUI } from "../../store/ui";
import { Btn, Check, Sel, cx } from "../../shared/ui";
import { BAND_COLOR, KpiTile, LINE_COLORS, ParetoChart, TrendChart, type Line } from "./charts";
import {
  PERIOD_LIST, axisLabel, fmtMin, fmtNum, pct, periodQuery, useOeeDashboard, useOeeMachines, useOeeMeta, useOeeUI,
  type Band, type Dashboard, type Group, type Period,
} from "./oeeApi";

const IDLE = "idle";
const GROUPS: Group[] = ["hour", "shift", "day", "week"];

export function bandOf(v: number | null | undefined, b: { low: number; high: number }): Band {
  if (v === null || v === undefined) return "none";
  if (v < b.low - 1e-9) return "low";
  if (v < b.high - 1e-9) return "mid";
  return "high";
}

/** Foizli katak: holat rangi nuqtasi + raqam (rang yolg'iz emas — raqam doim bor). */
export function PctCell({ v, bands }: { v: number | null | undefined; bands: { low: number; high: number } }) {
  const b = bandOf(v, bands);
  return <span className="oee-pc"><i style={{ background: BAND_COLOR[b] }} />{pct(v)}</span>;
}

/** Davr va stanok tanlovi (panel va hodisalar uchun umumiy). */
export function OeeFilters({ showGroup }: { showGroup?: boolean }) {
  const { t } = useTranslation();
  const ui = useOeeUI();
  const machines = useOeeMachines();
  return (
    <div className="oee-filters" data-testid="oee-filters">
      <div className="oee-periods" role="group" aria-label={t("oee.period_label")}>
        {PERIOD_LIST.map((p: Period) => (
          <Btn key={p} small label={t(`oee.period.${p}`)} active={ui.period === p} testid={`oee-period-${p}`}
            onClick={() => ui.set({ period: p })} />
        ))}
      </div>
      {ui.period === "custom" && (
        <span className="row gap">
          <input type="date" className="inp" value={ui.from} data-testid="oee-from" onChange={(e) => ui.set({ from: e.target.value })} />
          <span>—</span>
          <input type="date" className="inp" value={ui.to} data-testid="oee-to" onChange={(e) => ui.set({ to: e.target.value })} />
        </span>
      )}
      <Sel value={ui.machine} width={220} testid="oee-machine" onChange={(v) => ui.set({ machine: v })}
        options={[{ value: "", label: t("oee.all_machines") }, ...(machines.data ?? []).map((m) => ({ value: m.key, label: m.name }))]} />
      {showGroup && (
        <Sel value={ui.group} width={150} testid="oee-group" onChange={(v) => ui.set({ group: v })}
          options={GROUPS.map((g) => ({ value: g, label: t(`oee.group.${g}`) }))} />
      )}
    </div>
  );
}

export function OeeDashboard() {
  const { t } = useTranslation();
  const lang = useUI((s) => s.lang);
  const ui = useOeeUI();
  const machines = useOeeMachines();
  const meta = useOeeMeta();
  const pq = periodQuery(ui);
  const q = useOeeDashboard(ui.machine, ui.group, pq);
  const [tableView, setTableView] = useState(false);
  const d = q.data;
  const h = t("oee.u.h"), mn = t("oee.u.min");
  const noMachines = machines.data && machines.data.length === 0;

  const seed = async () => {
    const r = await call(() => post<{ events: number }>("/oee/demo-seed", undefined, { days: 14 }));
    if (r) { void qc.invalidateQueries({ queryKey: ["oee"] }); useUI.getState().toast(t("oee.demo_done", { n: r.events }), "ok"); }
  };

  if (noMachines) {
    return (
      <div className="oee-body" data-testid="oee-empty-machines">
        <div className="oee-card oee-hello">
          <h3>{t("oee.empty_title")}</h3>
          <p>{t("oee.empty_text")}</p>
          <div className="row gap">
            <Btn kind="primary" icon={Plus} label={t("oee.add_machine")} testid="oee-goto-machines" onClick={() => ui.set({ tab: "machines" })} />
            {meta.data?.demo_enabled && <Btn icon={FlaskConical} label={t("oee.demo_seed")} testid="oee-demo-seed" onClick={() => void seed()} />}
          </div>
        </div>
      </div>
    );
  }
  if (!d) return <div className="oee-body"><OeeFilters showGroup /><div className="oee-empty">{q.isError ? t("oee.load_error") : t("app.loading")}</div></div>;

  const s = d.summary;
  const bands = d.bands;
  const hasData = s.machines > 0;
  const lines: Line[] = (["oee", "availability", "performance", "quality"] as const)
    .filter((k) => ui.lines.includes(k))
    .map((k) => ({ key: k, name: t(`oee.line.${k}`), color: LINE_COLORS[k], values: d.series.map((p) => p[k]) }));
  const toggleLine = (k: string) => {
    const next = ui.lines.includes(k) ? ui.lines.filter((x) => x !== k) : [...ui.lines, k];
    ui.set({ lines: next.length ? next : ["oee"] });
  };
  const tips = d.series.map((p) => (ui.group === "shift" ? `${p.date} · ${p.name}` : p.label));
  const labels = d.series.map((p) => axisLabel(p, ui.group));
  const shiftRows: Dashboard["series"] = d.extra_series.shift ?? (ui.group === "shift" ? d.series : []);
  const unitLabel = t(`oee.unit_short.${d.config.unit}`);

  return (
    <div className="oee-body" data-testid="oee-dashboard">
      <div className="oee-bar">
        <OeeFilters showGroup />
        <span className="grow" />
        <Btn small icon={RefreshCw} label={t("oee.refresh")} testid="oee-refresh" onClick={() => void qc.invalidateQueries({ queryKey: ["oee"] })} />
        <Btn small icon={ArrowUpFromLine} label={t("oee.csv")} testid="oee-csv"
          onClick={() => void download("/oee/export.csv", { kind: "series", machine: ui.machine || undefined, group_by: ui.group, ...pq }, "oee_series.csv")} />
      </div>

      {d.warnings.length > 0 && (
        <div className="oee-warns" data-testid="oee-warnings">
          {d.warnings.map((w) => (
            <div key={w.code} className="oee-warn"><TriangleAlert size={14} />
              {t(`oee.warn.${w.code}`, { count: w.count ?? 0, machines: (w.machines ?? []).join(", "), defaultValue: w.code })}</div>
          ))}
        </div>
      )}

      <div className="oee-kpis">
        <KpiTile hero testid="kpi-oee" label={t("oee.kpi.oee")} value={s.oee} band={s.band.oee}
          hint={t("oee.kpi.oee_hint")}
          sub={hasData ? <>{pct(s.availability)} × {pct(s.performance)} × {pct(s.quality)}</> : t("oee.no_events")} />
        <KpiTile testid="kpi-a" label={t("oee.kpi.a")} value={s.availability} band={s.band.availability} hint={t("oee.kpi.a_hint")}
          sub={hasData ? <>{t("oee.kpi.a_sub", { run: fmtMin(s.run_min, h, mn), plan: fmtMin(s.planned_min, h, mn) })}<br />
            {t("oee.kpi.a_stop", { stop: fmtMin(s.stop_min, h, mn), idle: fmtMin(s.idle_min, h, mn) })}</> : undefined} />
        <KpiTile testid="kpi-p" label={t("oee.kpi.p")} value={s.performance} band={s.band.performance} hint={t("oee.kpi.p_hint")}
          sub={hasData ? <>{t("oee.kpi.p_sub", { avg: fmtNum(s.avg_cycle_s, 0), ideal: fmtNum(s.ideal_cycle_s, 0), unit: unitLabel })}
            {s.capped && <><br />{t("oee.kpi.p_capped", { raw: pct(s.performance_raw, 0) })}</>}</> : undefined} />
        <KpiTile testid="kpi-q" label={t("oee.kpi.q")} value={s.quality} band={s.band.quality} hint={t("oee.kpi.q_hint")}
          sub={hasData ? t("oee.kpi.q_sub", { good: fmtNum(s.good, 0), total: fmtNum(s.produced, 0), bad: pct(s.produced ? s.rejected / s.produced : null), unit: unitLabel }) : undefined} />
      </div>

      {d.material && d.material.sheets > 0 && (
        <div className="oee-mat" data-testid="oee-material" title={t("oee.mat.hint")}>
          <b>{t("oee.mat.title")}</b>
          <span>{t("oee.mat.fill")}: <b data-testid="oee-mat-fill">{pct(d.material.fill)}</b></span>
          <span>{t("oee.mat.waste")}: <b data-testid="oee-mat-waste">{pct(d.material.waste)}</b></span>
          <span className="muted">{t("oee.mat.sub", { sheets: fmtNum(d.material.sheets, 0), m2: fmtNum(d.material.sheet_m2, 1), rem: fmtNum(d.material.remnant_m2, 1) })}</span>
        </div>
      )}

      <div className="oee-card" data-testid="oee-trend-card">
        <div className="oee-card-head">
          <h3>{t("oee.trend")}</h3>
          <div className="oee-lines">
            {(["oee", "availability", "performance", "quality"] as const).map((k) => (
              <label key={k} className={cx("oee-linechip", ui.lines.includes(k) && "on")} data-testid={`oee-chip-${k}`}>
                <input type="checkbox" checked={ui.lines.includes(k)} onChange={() => toggleLine(k)} />
                <span className="oee-dot" style={{ background: LINE_COLORS[k] }} />{t(`oee.line.${k}`)}
              </label>
            ))}
          </div>
          <Check checked={tableView} label={t("oee.table_view")} onChange={setTableView} testid="oee-table-view" />
        </div>
        {tableView ? (
          <div className="scroll oee-tablewrap" data-testid="oee-trend-table">
            <table className="simple">
              <thead><tr><th>{t("oee.col.period")}</th>{lines.map((l) => <th key={l.key}>{l.name}</th>)}</tr></thead>
              <tbody>{d.series.map((p, i) => (
                <tr key={p.start}><td>{tips[i]}</td>{lines.map((l) => <td key={l.key} className="num">{pct(l.values[i])}</td>)}</tr>
              ))}</tbody>
            </table>
          </div>
        ) : <TrendChart labels={labels} tips={tips} lines={lines} bands={bands} ariaLabel={t("oee.trend")} />}
      </div>

      <div className={cx("oee-two", d.machines.length > 1 && !ui.machine && "oee-two-split")}>
        <div className="oee-card" data-testid="oee-pareto-card">
          <div className="oee-card-head"><h3>{t("oee.pareto")}</h3>
            <span className="muted">{t("oee.pareto_total", { v: fmtMin(d.pareto_total_min, h, mn) })}</span></div>
          <ParetoChart items={d.pareto} lang={lang} idleCode={IDLE} />
          {d.planned_losses.length > 0 && (
            <p className="muted oee-note" data-testid="oee-planned-note">
              {t("oee.planned_note")}: {d.planned_losses.map((p) => `${lang === "uz" ? p.name_uz : p.name_ru} ${fmtMin(p.minutes, h, mn)}`).join("; ")}
            </p>
          )}
        </div>
        {d.machines.length > 1 && !ui.machine && (
          <div className="oee-card" data-testid="oee-machines-card">
            <div className="oee-card-head"><h3>{t("oee.by_machine")}</h3></div>
            <table className="simple oee-table">
              <thead><tr><th>{t("oee.col.machine")}</th><th>OEE</th><th>A</th><th>P</th><th>Q</th><th>{t("oee.col.stop")}</th></tr></thead>
              <tbody>{d.machines.map((m) => (
                <tr key={m.machine} className="oee-click" data-testid={`oee-mrow-${m.machine}`} onClick={() => ui.set({ machine: m.machine })}>
                  <td>{m.name}</td>
                  {m.has_data ? <>
                    <td><PctCell v={m.oee} bands={bands} /></td><td className="num">{pct(m.availability)}</td>
                    <td className="num">{pct(m.performance)}</td><td className="num">{pct(m.quality)}</td>
                    <td className="num">{fmtMin(m.stop_min, h, mn)}</td></> : <td colSpan={5} className="muted">{t("oee.no_events")}</td>}
                </tr>))}</tbody>
            </table>
          </div>
        )}
      </div>

      <div className="oee-card" data-testid="oee-shifts-card">
        <div className="oee-card-head"><h3>{t("oee.shift_table")}</h3></div>
        {shiftRows.length === 0 ? <div className="oee-empty">{t("oee.no_shifts")}</div> : (
          <div className="scroll oee-tablewrap">
            <table className="simple oee-table" data-testid="oee-shift-table">
              <thead><tr>
                <th>{t("oee.col.date")}</th><th>{t("oee.col.shift")}</th><th>{t("oee.col.planned")}</th><th>{t("oee.col.run")}</th>
                <th>{t("oee.col.stop")}</th><th>OEE</th><th>A</th><th>P</th><th>Q</th><th>{t("oee.col.produced")}</th><th>{t("oee.col.rejected")}</th>
              </tr></thead>
              <tbody>{[...shiftRows].reverse().map((p) => (
                <tr key={p.start}>
                  <td>{p.date}</td><td>{p.name}</td><td className="num">{fmtMin(p.planned_min, h, mn)}</td><td className="num">{fmtMin(p.run_min, h, mn)}</td>
                  <td className="num">{fmtMin(p.stop_min, h, mn)}</td><td><PctCell v={p.oee} bands={bands} /></td>
                  <td className="num">{pct(p.availability)}</td><td className="num">{pct(p.performance)}</td><td className="num">{pct(p.quality)}</td>
                  <td className="num">{fmtNum(p.produced, 0)}</td><td className="num">{pct(p.produced ? p.rejected / p.produced : null)}</td>
                </tr>))}</tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
