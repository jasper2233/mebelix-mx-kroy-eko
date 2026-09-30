// CS «Параметры» (UI_SPEC §5.1): chap — material parametrlari, o'ng — kroy parametrlari.
import { useTranslation } from "react-i18next";
import { CircleQuestionMark, RotateCcw, Save } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { get, patch, put } from "../../api/client";
import type { CSCutParams, CSMaterialParams, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Check, Field, IconBtn, Num, Sel, money } from "../../shared/ui";
import { CsTabs } from "./CsPanel";

const ROUNDING = ["11", "12", "13", "14", "22", "23", "24", "32", "33", "34"];

export function CsParams({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const m = op.cs_material!;
  const c = op.cs_cut!;
  const cur = project.currency;
  const pm = (f: Partial<CSMaterialParams>) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { cs_material: f }));
  const pc = (f: Partial<CSCutParams>) => void call(() => patch(`/projects/${project.id}/operations/${op.id}`, { cs_cut: f }));
  const res = op.result;
  const sheetsQty = res ? res.total_sheets : null;
  const saveDefault = async () => {
    const r = await call(() => put("/settings/cs_defaults/default", { material: m, cut: c }));
    if (r) { useUI.getState().toast(t("cs.defaults_saved"), "ok"); void qc.invalidateQueries({ queryKey: ["defaults"] }); }
  };
  const applyDefault = async () => {
    const d = await call(() => get<{ material: CSMaterialParams; cut: CSCutParams }>("/settings/cs_defaults/default"));
    if (!d) return;
    const { thickness: _th, price: _pr, ...mat } = d.material;   // material qalinligi va narxi o'zgarmaydi
    await call(() => patch(`/projects/${project.id}/operations/${op.id}`, { cs_material: mat, cs_cut: d.cut }));
  };
  const n = (v: number | null, dflt = 0) => (v === null ? dflt : v);
  return (
    <div className="panel">
      <CsTabs right={<>
        <IconBtn icon={Save} title={t("cs.save_default")} onClick={() => void saveDefault()} testid="cs-save-default" />
        <IconBtn icon={RotateCcw} title={t("cs.apply_default")} onClick={() => void applyDefault()} />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} (F1)`} onClick={() => useUI.getState().set({ section: "help" })} />
      </>} />
      <div className="form2 scroll" data-testid="cs-params">
        <div className="form-col">
          <div className="form-h">{t("cs.p.material")}</div>
          <Field label={t("cs.p.thickness")} unit={t("u.mm")}><Num value={m.thickness} onCommit={(v) => pm({ thickness: n(v, 16) })} /></Field>
          <div className="form-h">{t("cs.p.cost")}</div>
          <Field label={t("cs.p.price")} unit={<>{cur} <Check checked={m.price_per_m2} label={t("cs.p.per_m2")} onChange={(v) => pm({ price_per_m2: v })} /></>}>
            <Num value={m.price} onCommit={(v) => pm({ price: n(v) })} testid="cs-price" /></Field>
          <Field label={t("cs.p.est_fill")} unit="%"><Num value={m.est_fill_percent} min={1} max={100} onCommit={(v) => pm({ est_fill_percent: n(v, 90) })} /></Field>
          <Field label={t("cs.p.material_qty")} unit={t("cs.p.sheets_u")}><Num value={sheetsQty} readOnly onCommit={() => undefined} /></Field>
          <Field label=" "><Check checked={m.cost_by_sheets} label={t("cs.p.cost_by_sheets")} onChange={(v) => pm({ cost_by_sheets: v })} /></Field>
          <Field label={t("cs.p.rounding")}>
            <Sel value={m.sheet_rounding} width={190} onChange={(v) => pm({ sheet_rounding: v })}
              options={ROUNDING.map((r) => ({ value: r, label: t(`cs.round.${r}`) }))} /></Field>
          <Field label={t("cs.p.cost_material")} unit={cur}><span className="ro">{money(op.cost_material)}</span></Field>
          <Field label={t("cs.p.op_base")}>
            <Sel value={m.op_cost_base} width={190} onChange={(v) => pm({ op_cost_base: v })}
              options={[0, 1, 2, 3].map((v) => ({ value: v, label: t(`cs.opbase.${v}`) }))} /></Field>
          <Field label={t("cs.p.op_price")} unit={cur}><Num value={m.op_price} onCommit={(v) => pm({ op_price: n(v) })} /></Field>
          <Field label={t("cs.p.cost_op")} unit={cur}><span className="ro">{money(op.cost_operation)}</span></Field>
          <div className="form-h">{t("cs.p.remnant")}</div>
          <Field label={t("cs.p.rem1")} unit={t("u.mm")}><Num value={m.remnant_min_side1} onCommit={(v) => pm({ remnant_min_side1: n(v, 1000) })} /></Field>
          <Field label={t("cs.p.rem2")} unit={t("u.mm")}><Num value={m.remnant_min_side2} onCommit={(v) => pm({ remnant_min_side2: n(v, 500) })} /></Field>
          <Field label={t("cs.p.rem_area")} unit={t("u.m2")}><Num value={m.remnant_min_area} onCommit={(v) => pm({ remnant_min_area: n(v, 0.5) })} /></Field>
          <Field label=" "><Check checked={m.remnant_size_incl_trim} label={t("cs.p.rem_trim")} onChange={(v) => pm({ remnant_size_incl_trim: v })} /></Field>
          <div className="form-h">{t("cs.p.limits")}</div>
          <Field label={t("cs.p.min_part")} unit={t("u.mm")}><Num value={m.min_part_size} onCommit={(v) => pm({ min_part_size: n(v, 30) })} /></Field>
        </div>
        <div className="form-col">
          <div className="form-h">{t("cs.p.cut")}</div>
          <Field label={t("cs.p.kerf")} unit={t("u.mm")}><Num value={c.kerf} min={0} onCommit={(v) => pc({ kerf: n(v, 3) })} testid="cs-kerf" /></Field>
          <Field label={t("cs.p.kerf_group")} unit={t("u.mm")}><Num value={c.kerf_group} allowEmpty onCommit={(v) => pc({ kerf_group: v })} /></Field>
          <Field label={t("cs.p.trim_l")} unit={t("u.mm")} hint={t("cs.p.trim_l_hint")}><Num value={c.trim_length} min={0} onCommit={(v) => pc({ trim_length: n(v) })} /></Field>
          <Field label={t("cs.p.trim_w")} unit={t("u.mm")} hint={t("cs.p.trim_w_hint")}><Num value={c.trim_width} min={0} onCommit={(v) => pc({ trim_width: n(v) })} /></Field>
          <Field label=" "><Check checked={c.trim_includes_kerf} label={t("cs.p.trim_kerf")} onChange={(v) => pc({ trim_includes_kerf: v })} /></Field>
          <Field label=" "><Check checked={c.trim_both_sides} label={t("cs.p.trim_both")} onChange={(v) => pc({ trim_both_sides: v })} /></Field>
          <Field label={t("cs.p.end_offset")} unit={t("u.mm")}><Num value={c.min_end_offset} min={0} onCommit={(v) => pc({ min_end_offset: n(v) })} /></Field>
          <Field label={t("cs.p.first_cut")}>
            <Sel value={c.first_cut} width={190} onChange={(v) => pc({ first_cut: v })}
              options={[0, 1, 2, 3, 4].map((v) => ({ value: v as 0, label: t(`cs.first.${v}`) }))} /></Field>
          <Field label=" "><span className="checks">
            <Check checked={c.use_grain} label={t("cs.p.use_grain")} onChange={(v) => pc({ use_grain: v })} />
            <Check checked={c.complex_strips} label={t("cs.p.complex")} onChange={(v) => pc({ complex_strips: v })} />
          </span></Field>
          <Field label={t("cs.p.max_rot")}>
            <Sel value={c.max_rotations} width={80} onChange={(v) => pc({ max_rotations: v })}
              options={[2, 3, 4, 5, 6].map((v) => ({ value: v, label: String(v) }))} /></Field>
          <Field label={t("cs.p.pack_h")} unit={t("u.mm")}><Num value={c.pack_height} onCommit={(v) => pc({ pack_height: n(v, 40) })} /></Field>
          <Field label={t("cs.p.mult")} unit={t("u.pcs")}><Num value={c.multiplicity} min={1} onCommit={(v) => pc({ multiplicity: n(v, 2) })} /></Field>
          <Field label={t("cs.p.fill_packet")} unit="%"><Num value={c.fill_packet} min={0} max={100} onCommit={(v) => pc({ fill_packet: n(v, 90) })} /></Field>
          <Field label={t("cs.p.max_types")}>
            <Sel value={c.max_part_types_per_map} width={150} onChange={(v) => pc({ max_part_types_per_map: v })}
              options={[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((v) => ({ value: v, label: v ? String(v) : t("cs.p.unlimited") }))} /></Field>
          <div className="form-h">{t("cs.p.prefs")}</div>
          <Field label=" "><Check checked={c.prefer_big_pack} label={t("cs.p.big_pack")} onChange={(v) => pc({ prefer_big_pack: v })} /></Field>
          <Field label={t("cs.p.quality")} hint={t("cs.p.quality_hint")}>
            <Sel value={c.quality} width={150} onChange={(v) => pc({ quality: v })} testid="cs-quality"
              options={(["fast", "normal", "max"] as const).map((v) => ({ value: v, label: t(`cs.quality.${v}`) }))} /></Field>
          <div className="form-h">{t("cs.p.sorting")}</div>
          <Field label={t("cs.p.sort_strips")}>
            <Sel value={c.strip_sort} width={170} onChange={(v) => pc({ strip_sort: v })}
              options={[0, 1, 2, 3].map((v) => ({ value: v as 0, label: t(`cs.sort.${v}`) }))} /></Field>
          <Field label={t("cs.p.sort_in")}>
            <Sel value={c.in_strip_sort} width={170} onChange={(v) => pc({ in_strip_sort: v })}
              options={[0, 1, 2, 3].map((v) => ({ value: v as 0, label: t(`cs.sort.${v}`) }))} /></Field>
          <Field label={t("cs.p.min_strip")} unit={t("u.mm")}><Num value={c.min_strip_width} min={0} onCommit={(v) => pc({ min_strip_width: n(v) })} /></Field>
          <Field label={t("cs.p.max_strip")} unit={t("u.mm")}><Num value={c.max_strip_width} min={0} onCommit={(v) => pc({ max_strip_width: n(v) })} /></Field>
          <Field label={t("cs.p.max_strip_len")} unit={t("u.mm")}><Num value={c.max_strip_length} min={0} onCommit={(v) => pc({ max_strip_length: n(v, 10000) })} /></Field>
          <Field label={t("cs.p.min_trim")} unit={t("u.mm")} hint={t("cs.p.min_trim_hint")}><Num value={c.min_trim_cut} min={0} onCommit={(v) => pc({ min_trim_cut: n(v, 5) })} /></Field>
          <Field label=" "><Check checked={c.merge_parts} label={t("cs.p.merge")} onChange={(v) => pc({ merge_parts: v })} /></Field>
          <Field label=" "><Check checked={c.save_drawings} label={t("cs.p.save_draw")} onChange={(v) => pc({ save_drawings: v })} /></Field>
          <Field label={t("cs.p.allowance")} unit={t("u.mm")}><Num value={c.machining_allowance} min={0} onCommit={(v) => pc({ machining_allowance: n(v) })} /></Field>
        </div>
      </div>
    </div>
  );
}
