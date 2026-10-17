// (CN) «Параметры»: chap — material, narx, qoldiq qoidalari, cheklov; o'ng — asbob va masofalar, burilishlar, tekstura, optimizatsiya. CL/CS paneli namunasida.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { CircleQuestionMark, RotateCcw, Save } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { get, patch, put } from "../../api/client";
import type { CNParams, Operation, Project, Quality } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { openFocusedParamHelp } from "../../shared/paramHelpStore";
import { Check, Field, IconBtn, Num, Sel, fmt, money } from "../../shared/ui";
import { CnTabs } from "./CnPanel";
import { useCnQuantities } from "./cnHooks";

// backend `cn_calc` bilan mos: nesting natijasini eskirtirmaydigan maydonlar (narx / sifat / hisoblangan)
const CN_NON = new Set(["quality", "time_limit_s", "thickness", "price", "cost_by_sheets", "sheet_rounding", "est_fill_percent",
  "op_cost_base", "op_price", "usage_m2", "multiplicity"]);
const ROUNDING = ["11", "12", "13", "14", "22", "23", "24", "32", "33", "34"];

/** Detallar orasidagi talab etilgan masofa (backend `CNParams.spacing`): max(D, 2·ofset) + qo'shimcha masofa. */
export const cnSpacing = (c: CNParams) => Math.max(c.tool_diameter, 2 * (c.tool_offset ?? c.tool_diameter / 2)) + c.part_gap;

export function CnParams({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const c = op.cn!;
  const cur = project.currency;
  const res = op.result;
  useHotkeys("params", { f1: () => { if (!openFocusedParamHelp()) useUI.getState().set({ section: "help" }); } });
  const staleChange = (f: Record<string, unknown>) => !!res && res.maps.length > 0
    && Object.keys(f).some((k) => !CN_NON.has(k) && (c as unknown as Record<string, unknown>)[k] !== f[k]);
  const [rk, setRk] = useState(0);                 // bekor qilinsa maydonlar qayta quriladi (kiritilgan qiymat eskisiga qaytadi)
  const guarded = async (f: Partial<CNParams>) => {
    if (staleChange(f) && !(await askConfirm(t("cn.params_invalidate_q"),
      res?.remnants_saved ? t("cs.params_invalidate_rem") : t("cs.params_invalidate_text"), { danger: true, ok: t("app.ok") }))) { setRk((k) => k + 1); return; }
    await call(() => patch(`/projects/${project.id}/operations/${op.id}`, { cn: f }));
  };
  const p = (f: Partial<CNParams>) => void guarded(f);
  const q = useCnQuantities(project, op).data;
  const approx = !res || !res.maps.length;
  const matQty = q ? q.material_qty_m2 : c.usage_m2;
  const sheets = q ? q.sheets : null;
  const qtyText = (v: number | null, d = 3) => (v === null ? "" : `${approx ? "≈ " : ""}${fmt(v, d)}`);
  const saveDefault = async () => {
    const r = await call(() => put("/settings/cn_defaults/default", c));
    if (r) { useUI.getState().toast(t("cn.defaults_saved"), "ok"); void qc.invalidateQueries({ queryKey: ["defaults"] }); }
  };
  const applyDefault = async () => {
    const d = await call(() => get<CNParams>("/settings/cn_defaults/default"));
    if (!d) return;
    const { thickness: _th, price: _pr, usage_m2: _u, multiplicity: _m, ...rest } = d;       // material qalinligi va narxi o'zgarmaydi
    await guarded(rest);
  };
  const n = (v: number | null, dflt = 0) => (v === null ? dflt : v);
  const spacing = cnSpacing(c);
  return (
    <div className="panel" {...scopeProps("params")}>
      <CnTabs right={<>
        <IconBtn icon={Save} title={t("cn.save_default")} onClick={() => void saveDefault()} testid="cn-save-default" />
        <IconBtn icon={RotateCcw} title={t("cn.apply_default")} onClick={() => void applyDefault()} testid="cn-apply-default" />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => useUI.getState().set({ section: "help" })} />
      </>} />
      <div className="form2 scroll" data-testid="cn-params" key={rk}>
        <div className="form-col">
          <div className="form-h">{t("cn.p.material")}</div>
          <Field label={t("cn.p.thickness")} unit={t("u.mm")} hint={t("cn.p.thickness_hint")} help="cn_thickness">
            <Num value={c.thickness} min={0.1} max={1000} onCommit={(v) => p({ thickness: n(v, 16) })} testid="cn-thickness" /></Field>
          <div className="form-h">{t("cn.p.cost")}</div>
          <Field label={t("cn.p.price")} help="cn_price" hint={t("cn.p.price_hint")}
            unit={<>{cur} {c.cost_by_sheets ? t("cn.p.per_sheet") : t("cn.p.per_m2")}</>}>
            <Num value={c.price} min={0} max={1e9} onCommit={(v) => p({ price: n(v) })} testid="cn-price" /></Field>
          <Field label={t("cn.p.est_fill")} unit="%" hint={t("cn.p.est_fill_hint")} help="cn_est_fill">
            <Num value={c.est_fill_percent} min={0} max={100} onCommit={(v) => p({ est_fill_percent: n(v, 80) })} testid="cn-est-fill" /></Field>
          <Field label={t("cn.p.material_qty")} unit={t("u.m2")} hint={`${t("cn.p.material_qty_hint")}${approx ? `\n${t("cs.p.estimated_hint")}` : ""}`}
            help="cn_material_qty">
            <span className="ro" data-testid="cn-material-qty">{qtyText(matQty)}</span></Field>
          <Field label={t("cn.p.sheets_qty")} unit={t("u.pcs")} hint={t("cn.p.sheets_qty_hint")} help="cn_sheets_qty">
            <span className="ro" data-testid="cn-sheets-qty">{qtyText(sheets, 0)}</span></Field>
          <Field label=" "><Check checked={c.cost_by_sheets} label={t("cn.p.cost_by_sheets")} onChange={(v) => p({ cost_by_sheets: v })}
            help="cn_cost_by_sheets" testid="cn-by-sheets" /></Field>
          <Field label={t("cn.p.rounding")} help="cn_rounding">
            <Sel value={c.sheet_rounding} width={190} onChange={(v) => p({ sheet_rounding: v })} testid="cn-rounding"
              options={ROUNDING.map((r) => ({ value: r, label: t(`cs.round.${r}`) }))} /></Field>
          <Field label={t("cn.p.cost_material")} unit={cur} help="cn_cost_material">
            <span className="ro" data-testid="cn-cost-material">{money(op.cost_material)}</span></Field>
          <Field label={t("cn.p.op_base")} help="cn_op_base">
            <Sel value={c.op_cost_base} width={230} onChange={(v) => p({ op_cost_base: v })} testid="cn-op-base"
              options={([0, 1, 2, 3] as const).map((v) => ({ value: v, label: t(`cn.opbase.${v}`) }))} /></Field>
          <Field label={t("cn.p.op_price")} unit={cur} hint={t("cn.p.op_price_hint")} help="cn_op_price">
            <Num value={c.op_price} min={0} max={1e9} onCommit={(v) => p({ op_price: n(v) })} testid="cn-op-price" /></Field>
          <Field label={t("cn.p.cut_length")} unit={t("u.m")} hint={t("cn.p.cut_length_hint")} help="cn_cut_length">
            <span className="ro" data-testid="cn-cut-length">{q ? `${approx ? "≈ " : ""}${fmt(q.cut_length_m, 2)}` : ""}</span></Field>
          <Field label={t("cn.p.cost_op")} unit={cur} help="cn_cost_op"><span className="ro" data-testid="cn-cost-op">{money(op.cost_operation)}</span></Field>
          <div className="form-h">{t("cn.p.remnant")}</div>
          <Field label={t("cn.p.rem1")} unit={t("u.mm")} hint={t("cn.p.rem_hint")} help="cn_rem1">
            <Num value={c.remnant_min_side1} min={0} max={20000} onCommit={(v) => p({ remnant_min_side1: n(v, 300) })} testid="cn-rem1" /></Field>
          <Field label={t("cn.p.rem2")} unit={t("u.mm")} help="cn_rem2">
            <Num value={c.remnant_min_side2} min={0} max={20000} onCommit={(v) => p({ remnant_min_side2: n(v, 150) })} testid="cn-rem2" /></Field>
          <Field label={t("cn.p.rem_area")} unit={t("u.m2")} hint={t("cn.p.rem_area_hint")} help="cn_rem_area">
            <Num value={c.remnant_min_area} min={0} max={1000} onCommit={(v) => p({ remnant_min_area: n(v, 0.1) })} testid="cn-rem-area" /></Field>
          <div className="form-h">{t("cn.p.limits")}</div>
          <Field label={t("cn.p.min_part")} unit={t("u.mm")} hint={t("cn.p.min_part_hint")} help="cn_min_part">
            <Num value={c.min_part_size} min={0} max={10000} onCommit={(v) => p({ min_part_size: n(v) })} testid="cn-min-part" /></Field>
        </div>
        <div className="form-col">
          <div className="form-h">{t("cn.p.tool")}</div>
          <Field label={t("cn.p.tool_d")} unit={t("u.mm")} hint={t("cn.p.tool_d_hint")} help="cn_tool_d">
            <Num value={c.tool_diameter} min={0.1} max={100} onCommit={(v) => p({ tool_diameter: n(v, 6) })} testid="cn-tool-d" /></Field>
          <Field label={t("cn.p.tool_offset")} hint={t("cn.p.tool_offset_hint")} help="cn_tool_offset"
            unit={<>{t("u.mm")}{c.tool_offset === null ? ` (${t("cn.p.as_half")}: ${fmt(c.tool_diameter / 2, 3)})` : ""}</>}>
            <Num value={c.tool_offset} allowEmpty min={0} max={100} onCommit={(v) => p({ tool_offset: v })} testid="cn-tool-offset" /></Field>
          <Field label={t("cn.p.part_gap")} unit={t("u.mm")} hint={t("cn.p.part_gap_hint")} help="cn_part_gap">
            <Num value={c.part_gap} min={0} max={500} onCommit={(v) => p({ part_gap: n(v) })} testid="cn-part-gap" /></Field>
          <Field label={t("cn.p.min_gap")} hint={t("cn.p.min_gap_hint", { arc: c.arc_tol })} help="cn_min_gap"
            unit={<>{t("u.mm")} (+ {fmt(c.arc_tol, 3)})</>}>
            <span className="ro" data-testid="cn-min-gap">{fmt(spacing, 3)}</span></Field>
          <Field label={t("cn.p.margin")} unit={t("u.mm")} hint={t("cn.p.margin_hint")} help="cn_margin">
            <Num value={c.margin} min={0} max={500} onCommit={(v) => p({ margin: n(v, 5) })} testid="cn-margin" /></Field>
          <Field label={t("cn.p.arc_tol")} unit={t("u.mm")} hint={t("cn.p.arc_tol_hint")} help="cn_arc_tol">
            <Num value={c.arc_tol} min={0.02} max={1} onCommit={(v) => p({ arc_tol: n(v, 0.25) })} testid="cn-arc-tol" /></Field>
          <div className="form-h">{t("cn.p.rotation")}</div>
          <Field label=" "><Check checked={c.rot90} label={t("cn.p.rot90")} title={t("cn.p.rot90_hint")} onChange={(v) => p({ rot90: v })}
            help="cn_rot90" testid="cn-rot90" /></Field>
          <Field label={t("cn.p.rot_step")} unit={t("cn.p.deg")} hint={t("cn.p.rot_step_hint")} help="cn_rot_step">
            <Num value={c.rot_step} min={0} max={90} onCommit={(v) => p({ rot_step: n(v) })} testid="cn-rot-step" /></Field>
          <Field label=" "><span className="checks">
            <Check checked={c.use_grain} label={t("cn.p.use_grain")} title={t("cn.p.use_grain_hint")} onChange={(v) => p({ use_grain: v })}
              help="cn_use_grain" testid="cn-use-grain" />
            <Check checked={c.use_xnc_contours} label={t("cn.p.use_xnc")} title={t("cn.p.use_xnc_hint")} onChange={(v) => p({ use_xnc_contours: v })}
              help="cn_use_xnc" testid="cn-use-xnc" />
          </span></Field>
          <div className="form-h">{t("cn.p.label")}</div>
          <Field label={t("cn.p.label_w")} unit={t("u.mm")} hint={t("cn.p.label_hint")} help="cn_label">
            <Num value={c.label_w} min={0} max={1000} onCommit={(v) => p({ label_w: n(v, 40) })} testid="cn-label-w" /></Field>
          <Field label={t("cn.p.label_h")} unit={t("u.mm")} help="cn_label">
            <Num value={c.label_h} min={0} max={1000} onCommit={(v) => p({ label_h: n(v, 20) })} testid="cn-label-h" /></Field>
          <div className="form-h">{t("cn.p.prefs")}</div>
          <Field label={t("cn.p.quality")} hint={t("cn.p.quality_hint")} help="cn_quality">
            <Sel<Quality> value={c.quality} width={150} onChange={(v) => p({ quality: v })} testid="cn-quality"
              options={(["fast", "normal", "max"] as const).map((v) => ({ value: v, label: t(`cs.quality.${v}`) }))} /></Field>
          <Field label={t("cn.p.sort_mode")} hint={t("cn.p.sort_mode_hint")} help="cn_sort_mode">
            <Sel<"auto" | "list"> value={c.sort_mode ?? "auto"} width={190} onChange={(v) => p({ sort_mode: v })} testid="cn-sort-mode"
              options={(["auto", "list"] as const).map((v) => ({ value: v, label: t(`cn.sort.${v}`) }))} /></Field>
          <Field label={t("cn.p.time_limit")} unit={t("cn.p.sec")} hint={t("cn.p.time_limit_hint")} help="cn_time_limit">
            <Num value={c.time_limit_s} min={0} max={600} onCommit={(v) => p({ time_limit_s: n(v) })} testid="cn-time-limit" /></Field>
          <div className="hint">{t("cn.p.note")}</div>
        </div>
      </div>
    </div>
  );
}
