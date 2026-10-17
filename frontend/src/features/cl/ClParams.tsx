// CL «Параметры» (hujjat D-CL2): chap — material, narx, otxod; o'ng — kroy parametrlari. CS paneli (CsParams) namunasida.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { CircleQuestionMark, RotateCcw, Save } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { get, patch, put } from "../../api/client";
import type { CLParams, Operation, Project, Quality } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { openFocusedParamHelp, useParamHelp } from "../../shared/paramHelpStore";
import { Btn, Check, CheckRow, Field, IconBtn, LinkRow, Modal, Num, Sel, fmt, money } from "../../shared/ui";
import { ClTabs } from "./ClPanel";
import { useClQuantities } from "./clHooks";

// backend `cl_calc.CL_NON_CUT` bilan mos: kroy natijasini eskirtirmaydigan maydonlar (narx / ko'rinish / keyingi kroy strategiyasi)
const CL_NON = new Set(["quality", "fill_packet", "pack_height", "thickness", "price", "price_by_strip", "strip_rounding",
  "est_fill_percent", "op_cost_base", "op_price", "usage_m", "multiplicity", "merge_parts", "group_parts", "save_drawings"]);
const ROUNDING = ["11", "32", "33", "34"];

export function ClParams({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const c = op.cl!;
  const cur = project.currency;
  const res = op.result;
  useHotkeys("params", { f1: () => { if (!openFocusedParamHelp()) useUI.getState().set({ section: "help" }); } });
  const staleChange = (f: Record<string, unknown>) => !!res && res.maps.length > 0
    && Object.keys(f).some((k) => !CL_NON.has(k) && (c as unknown as Record<string, unknown>)[k] !== f[k]);
  const guarded = async (f: Partial<CLParams>) => {
    if (staleChange(f) && !(await askConfirm(t("cl.params_invalidate_q"),
      res?.remnants_saved ? t("cs.params_invalidate_rem") : t("cs.params_invalidate_text"), { danger: true, ok: t("app.ok") }))) return;
    await call(() => patch(`/projects/${project.id}/operations/${op.id}`, { cl: f }));
  };
  const p = (f: Partial<CLParams>) => void guarded(f);
  const q = useClQuantities(project, op).data;
  const approx = !res || !res.maps.length;
  const qtyM = q ? q.material_qty_m : c.usage_m;
  const strips = q ? q.strips : null;
  // onlayn tizimdagidek oddiy son («≈» yo'q); baho ekanligi — maydon maslahatida
  const qtyText = (v: number | null, d = 3) => (v === null ? "" : fmt(v, d));
  const r3 = (v: number) => Math.round(v * 1000) / 1000;
  const [offsets, setOffsets] = useState(false);
  const saveDefault = async () => {
    const r = await call(() => put("/settings/cl_defaults/default", c));
    if (r) { useUI.getState().toast(t("cl.defaults_saved"), "ok"); void qc.invalidateQueries({ queryKey: ["defaults"] }); }
  };
  const applyDefault = async () => {
    const d = await call(() => get<CLParams>("/settings/cl_defaults/default"));
    if (!d) return;
    const { width: _w, thickness: _th, price: _pr, usage_m: _u, multiplicity: _m, ...rest } = d;   // material eni / qalinligi / narxi o'zgarmaydi
    await call(() => patch(`/projects/${project.id}/operations/${op.id}`, { cl: rest }));
  };
  const n = (v: number | null, dflt = 0) => (v === null ? dflt : v);
  return (
    <div className="panel" {...scopeProps("params")}>
      <ClTabs right={<>
        <IconBtn icon={Save} title={t("cl.save_default")} onClick={() => void saveDefault()} testid="cl-save-default" />
        <IconBtn icon={RotateCcw} title={t("cl.apply_default")} onClick={() => void applyDefault()} />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => useUI.getState().set({ section: "help" })} />
      </>} />
      <div className="form2 scroll" data-testid="cl-params">
        <div className="form-col">
          <div className="form-h">{t("cl.p.material")}</div>
          <Field label={t("cl.p.width")} unit={t("u.mm")} hint={t("cl.p.width_hint")} help="cl_width">
            <Num value={c.width} min={0.1} max={20000} onCommit={(v) => p({ width: n(v, 100) })} testid="cl-width" /></Field>
          <Field label={t("cl.p.thickness")} unit={t("u.mm")} hint={t("cl.p.thickness_hint")} help="cl_thickness">
            <Num value={c.thickness} min={0} max={1000} onCommit={(v) => p({ thickness: n(v, 16) })} testid="cl-thickness" /></Field>
          <div className="form-h">{t("cl.p.cost")}</div>
          {/* birlik — faqat valyuta (onlayn tizimdagidek); «за м / за полосу» ma'nosi yordamda */}
          <Field label={t("cl.p.price")} help="cl_price" unit={cur}
            hint={c.price_by_strip ? `${cur} ${t("cl.p.per_strip")}` : `${cur} ${t("cl.p.per_m")}`}>
            <Num value={c.price} min={0} max={1e9} onCommit={(v) => p({ price: n(v) })} testid="cl-price" /></Field>
          <Field label={t("cl.p.est_fill")} unit="%" hint={t("cl.p.est_fill_hint")} help="cl_est_fill">
            <Num value={c.est_fill_percent} min={1} max={100} onCommit={(v) => p({ est_fill_percent: n(v, 90) })} /></Field>
          <Field label={t("cl.p.material_qty")} unit={t("u.m")} hint={`${t("cl.p.material_qty_hint")}${approx ? `\n${t("cs.p.estimated_hint")}` : ""}`}
            help="cl_material_qty">
            <span className="ro" data-testid="cl-material-qty">{qtyText(qtyM)}</span></Field>
          <Field label={t("cl.p.strips_qty")} unit={t("u.pcs")} hint={`${t("cl.p.strips_qty_hint")}${approx ? `\n${t("cs.p.estimated_hint")}` : ""}`} help="cl_strips_qty">
            <span className="ro" data-testid="cl-strips-qty">{qtyText(strips, 2)}</span></Field>
          <CheckRow checked={c.price_by_strip} label={t("cl.p.by_strip")} onChange={(v) => p({ price_by_strip: v })}
            help="cl_by_strip" testid="cl-by-strip" />
          <Field label={t("cl.p.rounding")} help="cl_rounding">
            <Sel value={c.strip_rounding} width={190} disabled={!c.price_by_strip} onChange={(v) => p({ strip_rounding: v })}
              options={ROUNDING.map((r) => ({ value: r, label: t(`cl.round.${r}`) }))} /></Field>
          <Field label={t("cl.p.cost_material")} unit={cur} help="cl_cost_material">
            <span className="ro" data-testid="cl-cost-material">{money(op.cost_material)}</span></Field>
          <Field label={t("cl.p.op_base")} help="cl_op_base">
            <Sel value={c.op_cost_base} width={230} onChange={(v) => p({ op_cost_base: v })} testid="cl-op-base"
              options={([0, 1, 2, 3] as const).map((v) => ({ value: v, label: t(`cl.opbase.${v}`) }))} /></Field>
          <Field label={t("cl.p.op_price")} unit={cur} hint={t("cl.p.op_price_hint")} help="cl_op_price">
            <Num value={c.op_price} min={0} max={1e9} onCommit={(v) => p({ op_price: n(v) })} testid="cl-op-price" /></Field>
          <Field label={t("cl.p.cost_op")} unit={cur} help="cl_cost_op"><span className="ro" data-testid="cl-cost-op">{money(op.cost_operation)}</span></Field>
          {/* «Остаток» guruhi (onlayn tizimdagi yorliqlar): min. qoldiq (mm), deloviy qoldiq uzunligi — METRDA ko'rsatiladi
              (10 = 10000 mm; loyihada mm saqlanadi), torsovka bayrog'i */}
          <div className="form-h">{t("cl.p.remnant")}</div>
          <Field label={t("cl.p.rem_min")} unit={t("u.mm")} hint={t("cl.p.waste_min_hint")} help="cl_waste_min">
            <Num value={c.waste_min} min={0} max={20000} onCommit={(v) => p({ waste_min: n(v, 100) })} testid="cl-waste-min" /></Field>
          <Field label={t("cl.p.business_len")} unit={t("u.m")} hint={`${t("cl.p.business_min_hint")}\n${t("cl.p.business_len_hint")}`} help="cl_business_min">
            <Num value={r3(c.business_min / 1000)} min={0} max={20} onCommit={(v) => p({ business_min: Math.round(n(v, 1) * 1000) })}
              testid="cl-business-min" /></Field>
          <CheckRow checked={c.waste_incl_trim} label={t("cl.p.rem_trim")} hint={t("cl.p.rem_trim_hint")}
            onChange={(v) => p({ waste_incl_trim: v })} help="cl_trim_waste" testid="cl-trim-waste" />
          <div className="form-h">{t("cl.p.limits")}</div>
          <Field label={t("cl.p.min_part")} unit={t("u.mm")} hint={t("cl.p.min_part_hint")} help="cl_min_part">
            <Num value={c.min_part_len} min={0} max={10000} onCommit={(v) => p({ min_part_len: n(v) })} /></Field>
        </div>
        <div className="form-col">
          <div className="form-h">{t("cl.p.cut")}</div>
          <Field label={t("cl.p.kerf")} unit={t("u.mm")} hint={t("cl.p.kerf_hint")} help="cl_kerf">
            <Num value={c.kerf} min={0.01} max={50} onCommit={(v) => p({ kerf: n(v, 3) })} testid="cl-kerf" /></Field>
          {/* (CS) dagi kabi bo'sh maydon — pogonaj kroyda guruh detallar yo'q, qiymat ishlatilmaydi (maslahat va «?» tushuntiradi) */}
          <Field label={t("cs.p.kerf_group")} unit={t("u.mm")} hint={t("cl.p.kerf_group_hint")} help="cl_kerf_group">
            <Num value={null} allowEmpty disabled onCommit={() => undefined} testid="cl-kerf-group" /></Field>
          <Field label={t("cl.p.trim")} unit={t("u.mm")} hint={t("cl.p.trim_hint")} help="cl_trim">
            <Num value={c.trim} min={0} max={500} onCommit={(v) => p({ trim: n(v) })} testid="cl-trim" /></Field>
          <Field label={t("cl.p.end_offset")} hint={t("cl.p.end_offset_hint")} help="cl_end_offset">
            <button className="link" data-testid="cl-end-offset" onClick={() => setOffsets(true)}>
              {fmt(c.end_offset ?? c.trim)} {t("u.mm")}{c.end_offset === null ? ` (${t("cl.p.as_trim")})` : ""}</button></Field>
          <Field label={t("cl.p.pack_h")} unit={t("u.mm")} hint={t("cl.p.pack_hint")} help="cl_pack_h">
            <Num value={c.pack_height} min={0} max={1000} onCommit={(v) => p({ pack_height: n(v, 40) })} /></Field>
          <Field label={t("cl.p.mult")} unit={t("u.pcs")} hint={t("cl.p.mult_hint")} help="cl_mult">
            <Num value={c.multiplicity} readOnly onCommit={() => undefined} testid="cl-mult" /></Field>
          <Field label={t("cl.p.max_types")} hint={t("cl.p.max_types_hint")} help="cl_max_types">
            <Sel value={c.max_part_types_per_map ?? 0} width={150} onChange={(v) => p({ max_part_types_per_map: v })} testid="cl-max-types"
              options={[...new Set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, c.max_part_types_per_map ?? 0])].map((v) => ({
                value: v, label: v ? String(v) : t("cl.p.unlimited") }))} /></Field>
          {/* «Сортировка» guruhi (onlayn tizimdagidek): (CS) dagi shu nomli bayroqlar — saqlanadi (loyiha / eksport), 1D kroy natijasiga
              ta'sir qilmaydi (izoh — maslahat va «?» yordamida); «Группировка…» — havola, «Объединение деталей» yoqilganda faol */}
          <div className="form-h">{t("cs.p.sorting")}</div>
          <CheckRow checked={!!c.merge_parts} label={t("cl.p.merge")} hint={t("cl.p.merge_hint")} onChange={(v) => p({ merge_parts: v })}
            help="cl_merge" testid="cl-merge" />
          <LinkRow label={<>{t("cl.p.group_props")}{c.group_parts ? ` (${c.group_parts})` : ""}</>} disabled={!c.merge_parts}
            hint={t("cl.p.group_props_hint")} help="cl_group_props" testid="cl-group-props"
            onClick={() => useParamHelp.getState().open("cl_group_props")} />
          <CheckRow checked={!!c.save_drawings} label={t("cl.p.save_draw")} hint={t("cl.p.save_draw_hint")} onChange={(v) => p({ save_drawings: v })}
            help="cl_save_draw" testid="cl-save-draw" />
          {/* «Припуск на обработку заготовки» (CS dagi kabi): pilniy uzunlikka detalning har uchidan qo'shiladi */}
          <Field label={t("cs.p.allowance")} unit={t("u.mm")} help="allowance">
            <Num value={c.machining_allowance ?? 0} min={0} max={500} onCommit={(v) => p({ machining_allowance: n(v) })}
              testid="cl-allowance" /></Field>
          {/* Bizning qo'shimcha parametrlar — alohida guruhda, panel oxirida; «faqat to'g'ri ko'ndalang kesim» izohi — «Толщина пилы» yordamida */}
          <div className="form-h" title={t("cs.p.extra_hint")}>{t("cs.p.extra")}</div>
          <Field label={t("cl.p.fill_packet")} unit="%" hint={t("cl.p.fill_packet_hint")} help="cl_fill_packet">
            <Num value={c.fill_packet} min={0} max={100} onCommit={(v) => p({ fill_packet: n(v, 90) })} /></Field>
          <Field label={t("cs.p.quality")} hint={t("cs.p.quality_hint")} help="cl_quality">
            <Sel<Quality> value={c.quality} width={150} onChange={(v) => p({ quality: v })} testid="cl-quality"
              options={(["fast", "normal", "max"] as const).map((v) => ({ value: v, label: t(`cs.quality.${v}`) }))} /></Field>
        </div>
      </div>
      {offsets && <EndOffset c={c} onClose={() => setOffsets(false)} onSave={(v) => { p({ end_offset: v }); setOffsets(false); }} />}
    </div>
  );
}

/** «Минимальный отступ в конце»: belgilanmagan qiymat — torsovka bilan bir xil (null). */
function EndOffset({ c, onClose, onSave }: { c: CLParams; onClose: () => void; onSave: (v: number | null) => void }) {
  const { t } = useTranslation();
  const [on, setOn] = useState(c.end_offset !== null);
  const [v, setV] = useState<number | null>(c.end_offset ?? c.trim);
  return (
    <Modal title={t("cl.p.end_offset")} onClose={onClose} footer={<>
      <Btn kind="primary" label={t("app.ok")} testid="cl-offset-ok" onClick={() => onSave(on ? Math.max(0, v ?? 0) : null)} />
      <Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="form-col" data-testid="cl-offset-dialog">
        <Field label={<Check checked={on} label={t("cl.p.end_offset")} onChange={setOn} testid="cl-offset-on" />} unit={t("u.mm")}>
          <Num value={on ? v : c.trim} disabled={!on} min={0} max={500} onCommit={setV} testid="cl-offset-val" /></Field>
        <div className="hint">{t("cl.p.end_offset_hint")}</div>
      </div>
    </Modal>
  );
}
