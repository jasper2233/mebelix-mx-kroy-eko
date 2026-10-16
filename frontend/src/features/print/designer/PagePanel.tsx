// Etiketka vizual redaktori: hech narsa tanlanmaganda — sahifa (etiketka) sozlamalari: o'lcham, A4 to'r / rulon, shablon parametrlari va o'zgaruvchilari.
import { useTranslation } from "react-i18next";
import { Plus, Trash } from "lucide-react";
import type { LBParams } from "../../../api/types";
import { Check, Num, Sel, Txt, cx } from "../../../shared/ui";
import { LB_MARGIN_MM, borderKind, lbAutoSize, lbSize } from "../labelsApi";
import type { LabelIssue, LabelTemplate, TplParam } from "../labelsApi";
import { FxInput } from "./FxInput";

interface Props {
  tpl: LabelTemplate; lb: LBParams; errors: LabelIssue[];
  onTpl: (fn: (t: LabelTemplate) => void, merge?: string) => void;
  onLb: (p: Partial<LBParams>) => void;
  onFx: (current: string, apply: (v: string) => void) => void;
}

const TYPES: TplParam["type"][] = ["double", "integer", "string", "boolean"];

export function PagePanel({ tpl, lb, errors, onTpl, onLb, onFx }: Props) {
  const { t } = useTranslation();
  const sheet = lb.mode === "sheet";
  const auto = lbAutoSize(lb);            // A4 (rows ≥ 1): o'lcham sahifa va to'rdan hisoblanadi — faqat ko'rsatiladi
  const size = lbSize(lb);
  const errOf = (path: string) => errors.find((e) => e.path === path)?.message;
  const setSize = (w: number, h: number) => {
    onLb({ width_mm: w, height_mm: h });
    onTpl((x) => { x.size = { w, h }; }, "size");
  };
  const setParamValue = (p: TplParam, v: string | number | boolean) => onLb({ params: { ...lb.params, [p.name]: v } });
  return (
    <div className="lbd-insp" data-testid="lbd-page">
      <div className="lbd-insp-h"><b>{t("lbd.page")}</b></div>
      <label className="lbd-f"><span>{t("lbd.tpl_name")}</span>
        <Txt value={tpl.name ?? ""} width="100%" testid="lbd-tpl-name" onCommit={(s) => onTpl((x) => { x.name = s; }, "name")} /></label>
      <div className="lbd-fields">
        <label className="lbd-f lbd-half"><span>{t("lb.width")}</span>
          <Num value={size.w} min={1} max={500} testid="lbd-w" disabled={auto}
            onCommit={(v) => setSize(v ?? 58, lb.height_mm)} /></label>
        <label className="lbd-f lbd-half"><span>{t("lb.height")}</span>
          <Num value={size.h} min={1} max={500} testid="lbd-h" disabled={auto}
            onCommit={(v) => setSize(lb.width_mm, v ?? 40)} /></label>
        <label className="lbd-f lbd-half"><span>{t("lb.print_mode")}</span>
          <Sel<string> value={lb.mode} width="100%" testid="lbd-mode" onChange={(v) => onLb({ mode: v === "roll" ? "roll" : "sheet" })}
            options={[{ value: "sheet", label: t("lb.mode.sheet") }, { value: "roll", label: t("lb.mode.roll") }]} /></label>
        <div className="lbd-f lbd-half lbd-flag"><Check checked={lb.rotate_page === 90} label={t("lb.rotate")} onChange={(v) => onLb({ rotate_page: v ? 90 : 0 })} /></div>
        {sheet && <>
          <label className="lbd-f lbd-half"><span>{t("lb.columns")}</span>
            <Num value={lb.columns} min={1} max={20} testid="lbd-columns" onCommit={(v) => onLb({ columns: Math.max(1, Math.round(v ?? 1)) })} /></label>
          <label className="lbd-f lbd-half"><span>{t("lb.rows")}</span>
            <Num value={lb.rows} min={1} max={50} testid="lbd-rows" onCommit={(v) => onLb({ rows: Math.max(1, Math.round(v ?? 1)) })} /></label>
          <label className="lbd-f lbd-half"><span>{t("lb.gap")}</span>
            <Num value={lb.gap_mm} min={0} max={50} onCommit={(v) => onLb({ gap_mm: v ?? 0 })} /></label>
          <div className="lbd-f lbd-half lbd-flag"><Check checked={lb.margin_mm !== null} label={t("lb.margin_on")} onChange={(v) => onLb({ margin_mm: v ? LB_MARGIN_MM : null })} />
            <Num value={lb.margin_mm} min={0} max={50} width={52} disabled={lb.margin_mm === null} onCommit={(v) => onLb({ margin_mm: v ?? LB_MARGIN_MM })} /></div>
        </>}
        <label className="lbd-f lbd-half"><span>{t("lb.border")}</span>
          <Sel<string> value={borderKind(lb)} width="100%" testid="lbd-border"
            onChange={(v) => onLb({ border_mode: v === "none" ? "none" : "perimeter", border: v !== "none" })}
            options={[{ value: "none", label: t("lb.border_none") }, { value: "perimeter", label: t("lb.border_perimeter") }]} /></label>
      </div>

      <div className="lbd-sec"><b>{t("lb.tpl_params")}</b>
        <button type="button" className="lbd-add" data-testid="lbd-param-add"
          onClick={() => onTpl((x) => { x.params.push({ name: `p${x.params.length + 1}`, type: "double", default: 0, title: "" }); })}><Plus size={12} /></button></div>
      {tpl.params.map((p, i) => {
        const v = lb.params[p.name] ?? p.default;
        return (
          <div key={i} className="lbd-prm" data-testid="lbd-param">
            <Txt value={p.name} width={78} testid={`lbd-param-name-${i}`} onCommit={(s) => onTpl((x) => { x.params[i].name = s; })} />
            <Sel<string> value={p.type} width={72} onChange={(v2) => onTpl((x) => { x.params[i].type = v2 as TplParam["type"]; })}
              options={TYPES.map((tp) => ({ value: tp, label: tp }))} />
            <Txt value={String(p.default ?? "")} width={54} placeholder={t("lbd.default")}
              onCommit={(s) => onTpl((x) => { x.params[i].default = x.params[i].type === "boolean" ? s === "true" : x.params[i].type === "string" ? s : Number(s.replace(",", ".")) || 0; })} />
            {p.type === "boolean"
              ? <Check checked={Boolean(v)} onChange={(c) => setParamValue(p, c)} title={t("lbd.param_value")} />
              : p.type === "string"
                ? <Txt value={String(v ?? "")} width={70} onCommit={(s) => setParamValue(p, s)} />
                : <Num value={Number(v ?? 0)} width={54} onCommit={(n2) => setParamValue(p, n2 ?? 0)} />}
            <button type="button" className="lbd-fxbtn" title={t("app.delete")} onClick={() => onTpl((x) => { x.params.splice(i, 1); })}><Trash size={11} /></button>
          </div>);
      })}

      <div className="lbd-sec"><b>{t("lb.tpl_vars")}</b>
        <button type="button" className="lbd-add" data-testid="lbd-var-add"
          onClick={() => onTpl((x) => { x.vars.push({ name: `v${x.vars.length + 1}`, expr: "1" }); })}><Plus size={12} /></button></div>
      {tpl.vars.map((v, i) => {
        const e = errOf(`vars.${v.name}`);
        return (
          <div key={i} className={cx("lbd-prm", "lbd-var")} data-testid="lbd-var">
            <Txt value={v.name} width={80} testid={`lbd-var-name-${i}`} onCommit={(s) => onTpl((x) => { x.vars[i].name = s; })} />
            <FxInput value={String(v.expr ?? "")} error={e} testid={`lbd-var-expr-${i}`} onFx={onFx} mono onCommit={(s) => onTpl((x) => { x.vars[i].expr = s; })} />
            <button type="button" className="lbd-fxbtn" title={t("app.delete")} onClick={() => onTpl((x) => { x.vars.splice(i, 1); })}><Trash size={11} /></button>
          </div>);
      })}
    </div>
  );
}
