// «Настройки → XNC» (W8): Инструменты (asboblar jadvali), Палитра (buyruqlar belgilari), Ограничения (stanok cheklovlari).
// Hamma o'zgarishlar qoralama; «Сохранить» — standart profilga yozadi (xnc_tools / xnc_palette / xnc_constraints).
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown, ChevronUp, Plus, RotateCcw, Save, Trash, Undo2 } from "lucide-react";
import { call } from "../../api/hooks";
import { askConfirm } from "../../shared/dialogs";
import { useUI } from "../../store/ui";
import { Btn, Check, Field, IconBtn, Num, Sel, Tabs, Txt, cx } from "../../shared/ui";
import { PALETTE } from "./XncProgramTab";
import {
  PLANES, saveDefault, useBuiltinSettings, useXncConstraints, useXncPaletteDoc, useXncTools,
  type CMode, type Corner, type LimitKey, type Plane, type XncConstraints, type XncPaletteItem, type XncToolRow, type XncToolsDoc,
  type XncPaletteDoc,
} from "./xncSettingsApi";
import "./xnc.css";

type TabKey = "tools" | "palette" | "limits";
const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);

// ───────────────────────── Инструменты ─────────────────────────
function badRows(rows: XncToolRow[]): Set<number> {
  const bad = new Set<number>();
  const seen = new Map<string, number>();
  rows.forEach((r, i) => {
    const k = `${r.plane}|${r.name.trim().toLowerCase()}`;
    if (!r.name.trim() || !(r.d > 0) || seen.has(k)) bad.add(i);
    seen.set(k, i);
  });
  return bad;
}

function ToolsTab({ rows, setRows, onDefaults }: { rows: XncToolRow[]; setRows: (r: XncToolRow[]) => void; onDefaults: () => void }) {
  const { t } = useTranslation();
  const [sel, setSel] = useState(0);
  const bad = badRows(rows);
  const upd = (i: number, f: Partial<XncToolRow>) => setRows(rows.map((r, k) => (k === i ? { ...r, ...f } : r)));
  const add = () => {
    const plane: Plane = rows[sel]?.plane ?? "front";
    let n = rows.length + 1;
    while (rows.some((r) => r.plane === plane && r.name === `Tool${n}`)) n++;
    const row: XncToolRow = { plane, d: 8, through: false, name: `Tool${n}`, depth: null, comment: "" };
    const at = rows.length ? Math.min(sel + 1, rows.length) : 0;
    setRows([...rows.slice(0, at), row, ...rows.slice(at)]);
    setSel(at);
  };
  const del = () => {
    if (!rows[sel]) return;
    const n = rows.filter((_, k) => k !== sel);
    setRows(n);
    setSel(Math.max(0, Math.min(sel, n.length - 1)));
  };
  const move = (d: -1 | 1) => {
    const j = sel + d;
    if (j < 0 || j >= rows.length) return;
    const n = [...rows];
    [n[sel], n[j]] = [n[j], n[sel]];
    setRows(n);
    setSel(j);
  };
  return (
    <div className="xs-pane" data-testid="xs-tools">
      <div className="toolbar xs-bar">
        <IconBtn icon={Plus} title={t("app.add")} onClick={add} testid="xs-tool-add" />
        <IconBtn icon={Trash} color="#c0392b" title={t("app.delete")} onClick={del} disabled={!rows[sel]} testid="xs-tool-del" />
        <IconBtn icon={ChevronUp} title={t("app.up")} onClick={() => move(-1)} disabled={sel <= 0} testid="xs-tool-up" />
        <IconBtn icon={ChevronDown} title={t("app.down")} onClick={() => move(1)} disabled={sel >= rows.length - 1} testid="xs-tool-down" />
        <span className="grow" />
        <Btn small icon={RotateCcw} label={t("xs.defaults")} onClick={onDefaults} testid="xs-tool-defaults" />
      </div>
      <p className="muted xs-hint">{t("xs.tools.hint")}</p>
      <div className="scroll xs-table-wrap">
        <table className="simple xs-table">
          <thead>
            <tr><th>№</th><th>{t("xs.col.plane")}</th><th>{t("xs.col.d")}</th><th>{t("xs.col.through")}</th><th>{t("xs.col.name")}</th>
              <th>{t("xs.col.depth")}</th><th>{t("xs.col.comment")}</th></tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className={cx(i === sel && "tr-sel", bad.has(i) && "xs-bad")} onClick={() => setSel(i)} data-testid={`xs-tool-row-${i}`}>
                <td className="num">{i + 1}</td>
                <td><Sel<Plane> value={r.plane} width={112} testid={`xs-tool-plane-${i}`}
                  options={PLANES.map((p) => ({ value: p, label: t(`xs.plane.${p}`) }))}
                  onChange={(v) => upd(i, { plane: v, through: v === "front" ? r.through : false })} /></td>
                <td><Num value={r.d} width={64} min={0} testid={`xs-tool-d-${i}`} onCommit={(v) => upd(i, { d: v ?? r.d })} /></td>
                <td className="xs-c"><Check checked={r.through} disabled={r.plane !== "front"} testid={`xs-tool-through-${i}`}
                  onChange={(v) => upd(i, { through: v })} /></td>
                <td><Txt value={r.name} width={130} maxLength={40} testid={`xs-tool-name-${i}`} onCommit={(v) => upd(i, { name: v })} /></td>
                <td><Num value={r.depth} allowEmpty min={0} width={64} disabled={r.through} testid={`xs-tool-depth-${i}`}
                  onCommit={(v) => upd(i, { depth: v })} /></td>
                <td><Txt value={r.comment} width="100%" maxLength={200} onCommit={(v) => upd(i, { comment: v })} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length && <div className="muted" style={{ padding: 8 }}>{t("xs.tools.empty")}</div>}
      </div>
      {bad.size > 0 && <p className="warn xs-hint" data-testid="xs-tools-bad">{t("xs.tools.invalid")}</p>}
    </div>
  );
}

// ───────────────────────── Палитра ─────────────────────────
function PaletteTab({ items, setItems, onDefaults }: { items: XncPaletteItem[]; setItems: (r: XncPaletteItem[]) => void; onDefaults: () => void }) {
  const { t } = useTranslation();
  const [sel, setSel] = useState(0);
  const icon = new Map(PALETTE.map((p) => [p.cmd, p.short]));
  const move = (d: -1 | 1) => {
    const j = sel + d;
    if (j < 0 || j >= items.length) return;
    const n = [...items];
    [n[sel], n[j]] = [n[j], n[sel]];
    setItems(n);
    setSel(j);
  };
  const on = items.filter((i) => i.enabled).length;
  return (
    <div className="xs-pane" data-testid="xs-palette">
      <div className="toolbar xs-bar">
        <IconBtn icon={ChevronUp} title={t("app.up")} onClick={() => move(-1)} disabled={sel <= 0} testid="xs-pal-up" />
        <IconBtn icon={ChevronDown} title={t("app.down")} onClick={() => move(1)} disabled={sel >= items.length - 1} testid="xs-pal-down" />
        <span className="muted">{t("xs.pal.count", { n: on, m: items.length })}</span>
        <span className="grow" />
        <Btn small label={t("xs.pal.all")} onClick={() => setItems(items.map((i) => ({ ...i, enabled: true })))} testid="xs-pal-all" />
        <Btn small icon={RotateCcw} label={t("xs.defaults")} onClick={onDefaults} testid="xs-pal-defaults" />
      </div>
      <p className="muted xs-hint">{t("xs.pal.hint")}</p>
      <div className="scroll xs-table-wrap">
        <table className="simple xs-table">
          <thead><tr><th>№</th><th>{t("xnc.enabled")}</th><th>{t("xs.col.icon")}</th><th>{t("xs.col.name")}</th></tr></thead>
          <tbody>
            {items.map((it, i) => (
              <tr key={it.cmd} className={cx(i === sel && "tr-sel", !it.enabled && "xs-off-row")} onClick={() => setSel(i)} data-testid={`xs-pal-row-${it.cmd}`}>
                <td className="num">{i + 1}</td>
                <td className="xs-c"><Check checked={it.enabled} testid={`xs-pal-on-${it.cmd}`}
                  onChange={(v) => setItems(items.map((x, k) => (k === i ? { ...x, enabled: v } : x)))} /></td>
                <td className="xs-icon">{icon.get(it.cmd) ?? "·"}</td>
                <td>{t(`xnc.cmd.${it.cmd}`, { defaultValue: it.cmd })} <span className="muted">({it.cmd})</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ───────────────────────── Ограничения ─────────────────────────
type SetC = (f: (c: XncConstraints) => XncConstraints) => void;
const RANGES: [LimitKey, LimitKey][] = [["length_min", "length_max"], ["width_min", "width_max"], ["thickness_min", "thickness_max"]];
/** Yoqilgan minimum maksimumdan katta bo'lsa (backend ham rad etadi). */
const rangeBad = (c: XncConstraints) => RANGES.some(([a, b]) => c[a].enabled && c[b].enabled && c[a].value > c[b].value);
type FlagKey = "groove_horizontal" | "groove_vertical" | "avoid_bottom_horizontal";

function LimitRow({ c, set, k, label }: { c: XncConstraints; set: SetC; k: LimitKey; label: string }) {
  const { t } = useTranslation();
  const l = c[k];
  return (
    <div className="xs-row" data-testid={`xs-c-${k}`}>
      <Check checked={l.enabled} label={label} testid={`xs-c-${k}-on`}
        onChange={(v) => set((x) => ({ ...x, [k]: { ...x[k], enabled: v } }))} />
      <Num value={l.value} width={70} min={0} disabled={!l.enabled} testid={`xs-c-${k}-val`}
        onCommit={(v) => set((x) => ({ ...x, [k]: { ...x[k], value: v ?? x[k].value } }))} />
      <span className="muted">{t("u.mm")}</span>
    </div>
  );
}

function FlagRow({ c, set, k, label, valueLabel }: { c: XncConstraints; set: SetC; k: FlagKey; label: string; valueLabel: string }) {
  const f = c[k];
  return (
    <div className="xs-row xs-flag" data-testid={`xs-c-${k}`}>
      <Check checked={f.enabled} label={label} testid={`xs-c-${k}-on`} onChange={(v) => set((x) => ({ ...x, [k]: { ...x[k], enabled: v } }))} />
      <Check checked={f.value} disabled={!f.enabled} label={valueLabel} testid={`xs-c-${k}-val`}
        onChange={(v) => set((x) => ({ ...x, [k]: { ...x[k], value: v } }))} />
    </div>
  );
}

function LimitsTab({ c, set }: { c: XncConstraints; set: SetC }) {
  const { t } = useTranslation();
  const L = (k: LimitKey, label: string) => <LimitRow key={k} c={c} set={set} k={k} label={label} />;
  const sides = ["top", "bottom", "left", "right"] as const;
  return (
    <div className={cx("xs-pane xs-limits", c.mode === "off" && "xs-dim")} data-testid="xs-limits">
      <div className="xs-modebar">
        <Field label={t("xs.c.mode_label")}>
          <Sel<CMode> value={c.mode} width={230} testid="xs-c-mode" onChange={(v) => set((x) => ({ ...x, mode: v }))}
            options={(["off", "warn", "block"] as const).map((m) => ({ value: m, label: t(`xs.c.mode.${m}`) }))} />
        </Field>
        <p className="muted xs-hint">{t(`xs.c.mode_hint.${c.mode}`)}</p>
        {rangeBad(c) && <p className="warn xs-hint" data-testid="xs-c-range-bad">{t("xs.c.range_bad")}</p>}
      </div>
      <div className="xs-cols">
        <div className="xs-col">
          <div className="form-h">{t("xs.c.size")}</div>
          {L("length_min", t("xs.c.length_min"))}{L("length_max", t("xs.c.length_max"))}
          {L("width_min", t("xs.c.width_min"))}{L("width_max", t("xs.c.width_max"))}
          {L("thickness_min", t("xs.c.thickness_min"))}{L("thickness_max", t("xs.c.thickness_max"))}
          <div className="xs-row xs-flag" data-testid="xs-c-rotate_long_side">
            <Check checked={c.rotate_long_side !== "off"} label={t("xs.c.rotate_long")} testid="xs-c-rotate_long_side-on"
              onChange={(v) => set((x) => ({ ...x, rotate_long_side: v ? "horizontal" : "off" }))} />
            <Sel value={c.rotate_long_side === "off" ? "horizontal" : c.rotate_long_side} width={150} disabled={c.rotate_long_side === "off"}
              testid="xs-c-rotate_long_side-val" onChange={(v) => set((x) => ({ ...x, rotate_long_side: v }))}
              options={(["horizontal", "vertical"] as const).map((v) => ({ value: v, label: t(`xs.c.long.${v}`) }))} />
          </div>
          <div className="xs-row xs-flag" data-testid="xs-c-rotate_corner">
            <Check checked={c.rotate_corner_on} label={t("xs.c.rotate_corner")} testid="xs-c-rotate_corner-on"
              onChange={(v) => set((x) => ({ ...x, rotate_corner_on: v }))} />
            <Sel<Corner> value={c.rotate_corner} width={190} disabled={!c.rotate_corner_on} testid="xs-c-rotate_corner-val"
              onChange={(v) => set((x) => ({ ...x, rotate_corner: v }))}
              options={(["LT", "RT", "LB", "RB"] as const).map((v) => ({ value: v, label: t(`xs.c.corner.${v}`) }))} />
          </div>
          <div className="form-h">{t("xs.c.hole_center")}</div>
          {sides.map((s) => L(`hole_center_${s}`, t(`xs.c.hc.${s}`)))}
        </div>
        <div className="xs-col">
          <div className="form-h">{t("xs.c.groove")}</div>
          <FlagRow c={c} set={set} k="groove_horizontal" label={t("xs.c.groove_h")} valueLabel={t("xs.c.allowed")} />
          <FlagRow c={c} set={set} k="groove_vertical" label={t("xs.c.groove_v")} valueLabel={t("xs.c.allowed")} />
          <div className="form-h">{t("xs.c.groove_margin")}</div>
          {sides.map((s) => L(`groove_margin_${s}`, t(`xs.c.gm.${s}`)))}
          <div className="form-h">{t("xs.c.mill")}</div>
          {L("mill_max_distance", t("xs.c.mill_max"))}
          <div className="form-h">{t("xs.c.drill")}</div>
          <FlagRow c={c} set={set} k="avoid_bottom_horizontal" label={t("xs.c.avoid_bottom")} valueLabel={t("xs.c.preference")} />
          {L("blind_depth_margin", t("xs.c.blind_depth"))}
          {L("hole_gap_min", t("xs.c.hole_gap"))}
          {L("hole_edge_front_min", t("xs.c.edge_front"))}
          {L("hole_edge_horizontal_min", t("xs.c.edge_horizontal"))}
        </div>
      </div>
    </div>
  );
}

// ───────────────────────── Sahifa ─────────────────────────
export function XncSettings() {
  const { t } = useTranslation();
  const ui = useUI();
  const toolsQ = useXncTools(), palQ = useXncPaletteDoc(), consQ = useXncConstraints(), builtinQ = useBuiltinSettings();
  const [tab, setTab] = useState<TabKey>("tools");
  const [tools, setTools] = useState<XncToolRow[] | null>(null);
  const [pal, setPal] = useState<XncPaletteItem[] | null>(null);
  const [cons, setCons] = useState<XncConstraints | null>(null);
  useEffect(() => { if (toolsQ.data) setTools(toolsQ.data.tools); }, [toolsQ.data]);
  useEffect(() => { if (palQ.data) setPal(palQ.data.items); }, [palQ.data]);
  useEffect(() => { if (consQ.data) setCons(consQ.data); }, [consQ.data]);
  if (!tools || !pal || !cons) return null;

  const dirty = { tools: !same(tools, toolsQ.data?.tools), palette: !same(pal, palQ.data?.items), limits: !same(cons, consQ.data) };
  const anyDirty = dirty.tools || dirty.palette || dirty.limits;
  const invalid = badRows(tools).size > 0 || rangeBad(cons);
  const builtin = builtinQ.data as { xnc_tools?: XncToolsDoc; xnc_palette?: XncPaletteDoc; xnc_constraints?: XncConstraints } | undefined;

  const save = async () => {
    let ok = true;
    if (dirty.tools) ok = !!(await call(() => saveDefault("xnc_tools", { tools: tools.map((r) => ({ ...r, name: r.name.trim() })) }))) && ok;
    if (dirty.palette) ok = !!(await call(() => saveDefault("xnc_palette", { items: pal }))) && ok;
    if (dirty.limits) ok = !!(await call(() => saveDefault("xnc_constraints", cons))) && ok;
    if (ok) ui.toast(t("app.saved"), "ok");
  };
  const discard = () => {
    setTools(toolsQ.data?.tools ?? tools); setPal(palQ.data?.items ?? pal); setCons(consQ.data ?? cons);
  };
  const toolDefaults = async () => {
    if (builtin?.xnc_tools && (await askConfirm(t("xs.tools.defaults_q")))) setTools(builtin.xnc_tools.tools);
  };

  return (
    <div className="page xs-page" data-testid="xnc-settings">
      <div className="page-head">
        <h2>{t("settings.page.xnc")}</h2>
        <Btn icon={Save} kind="primary" label={t("app.save")} onClick={() => void save()} disabled={!anyDirty || invalid} testid="xs-save" />
        <Btn icon={Undo2} label={t("xs.discard")} onClick={discard} disabled={!anyDirty} testid="xs-discard" />
        {anyDirty && <span className="warn" data-testid="xs-unsaved">{t("xs.unsaved")}</span>}
      </div>
      <Tabs<TabKey> value={tab} onChange={setTab} tabs={[
        { key: "tools", label: `${t("xs.tab.tools")}${dirty.tools ? " •" : ""}`, testid: "xs-tab-tools" },
        { key: "palette", label: `${t("xs.tab.palette")}${dirty.palette ? " •" : ""}`, testid: "xs-tab-palette" },
        { key: "limits", label: `${t("xs.tab.limits")}${dirty.limits ? " •" : ""}`, testid: "xs-tab-limits" }]} />
      <div className="xs-body">
        {tab === "tools" && <ToolsTab rows={tools} setRows={setTools} onDefaults={() => void toolDefaults()} />}
        {tab === "palette" && <PaletteTab items={pal} setItems={setPal}
          onDefaults={() => { if (builtin?.xnc_palette) setPal(builtin.xnc_palette.items); }} />}
        {tab === "limits" && (
          <>
            <LimitsTab c={cons} set={(f) => setCons((x) => (x ? f(x) : x))} />
            <div className="row gap xs-foot">
              <Btn small icon={RotateCcw} label={t("xs.defaults")} testid="xs-c-defaults"
                onClick={() => { if (builtin?.xnc_constraints) setCons(builtin.xnc_constraints); }} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
