// CS «Параметры» (UI_SPEC §5.1): chap — material parametrlari, o'ng — kroy parametrlari.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { CircleQuestionMark, RotateCcw, Save } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { get, patch, put } from "../../api/client";
import type { CSCutParams, CSMaterialParams, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Check, Field, IconBtn, Modal, Num, Sel, money } from "../../shared/ui";
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
  // «Количество материала»: listlar bo'yicha — listlar soni, aks holda m² (listlar − деловой qoldiqlar)
  const matQty = res ? (m.cost_by_sheets ? res.total_sheets : res.material_qty_m2) : null;
  const multiplicity = m.thickness > 0 ? Math.max(1, Math.floor((c.pack_height + 1e-9) / m.thickness)) : 1;
  const [offsets, setOffsets] = useState(false);
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
          <Field label={t("cs.p.price")} hint={t("cs.p.price_hint")}
            unit={<>{cur} {m.cost_by_sheets ? t("cs.p.per_sheet") : t("cs.p.per_m2")}</>}>
            <Num value={m.price} onCommit={(v) => pm({ price: n(v) })} testid="cs-price" /></Field>
          <Field label={t("cs.p.est_fill")} unit="%" hint={t("cs.p.est_fill_hint")}><Num value={m.est_fill_percent} min={1} max={100} onCommit={(v) => pm({ est_fill_percent: n(v, 90) })} /></Field>
          <Field label={t("cs.p.material_qty")} unit={m.cost_by_sheets ? t("cs.p.sheets_u") : t("u.m2")} hint={t("cs.p.material_qty_hint")}>
            <Num value={matQty} readOnly onCommit={() => undefined} testid="cs-material-qty" /></Field>
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
          <Field label={t("cs.p.min_part")} unit={t("u.mm")} hint={t("cs.p.min_part_hint")}><Num value={m.min_part_size} onCommit={(v) => pm({ min_part_size: n(v, 30) })} /></Field>
        </div>
        <div className="form-col">
          <div className="form-h">{t("cs.p.cut")}</div>
          <Field label={t("cs.p.kerf")} unit={t("u.mm")}><Num value={c.kerf} min={0} onCommit={(v) => pc({ kerf: n(v, 3) })} testid="cs-kerf" /></Field>
          <Field label={t("cs.p.kerf_group")} unit={t("u.mm")} hint={t("cs.p.kerf_group_hint")}><Num value={c.kerf_group} allowEmpty onCommit={(v) => pc({ kerf_group: v })} /></Field>
          <Field label={t("cs.p.trim_l")} unit={t("u.mm")} hint={t("cs.p.trim_l_hint")}><Num value={c.trim_length} min={0} onCommit={(v) => pc({ trim_length: n(v) })} /></Field>
          <Field label={t("cs.p.trim_w")} unit={t("u.mm")} hint={t("cs.p.trim_w_hint")}><Num value={c.trim_width} min={0} onCommit={(v) => pc({ trim_width: n(v) })} /></Field>
          <Field label=" "><Check checked={c.trim_includes_kerf} label={t("cs.p.trim_kerf")} onChange={(v) => pc({ trim_includes_kerf: v })} /></Field>
          <Field label=" " hint={t("cs.p.end_offset_hint")}>
            <button className="link" data-testid="cs-end-offsets" onClick={() => setOffsets(true)}>
              {t("cs.p.end_offset")}: {t("cs.p.offset_bottom_s")} {c.end_offset_bottom ?? c.trim_length},{" "}
              {t("cs.p.offset_right_s")} {c.end_offset_right ?? c.trim_width} {t("u.mm")}</button></Field>
          <Field label={t("cs.p.first_cut")}>
            <Sel value={c.first_cut} width={190} onChange={(v) => pc({ first_cut: v })}
              options={[0, 1, 2, 3, 4].map((v) => ({ value: v as 0, label: t(`cs.first.${v}`) }))} /></Field>
          <Field label=" "><span className="checks">
            <Check checked={c.use_grain} label={t("cs.p.use_grain")} onChange={(v) => pc({ use_grain: v })} />
            <Check checked={c.complex_strips} label={t("cs.p.complex")} title={t("cs.p.complex_hint")} onChange={(v) => pc({ complex_strips: v })} />
          </span></Field>
          <Field label={t("cs.p.max_rot")}>
            <Sel value={c.max_rotations} width={80} onChange={(v) => pc({ max_rotations: v })}
              options={[2, 3, 4, 5, 6].map((v) => ({ value: v, label: String(v) }))} /></Field>
          <Field label={t("cs.p.pack_h")} unit={t("u.mm")} hint={t("cs.p.pack_hint")}><Num value={c.pack_height} onCommit={(v) => pc({ pack_height: n(v, 40) })} /></Field>
          <Field label={t("cs.p.mult")} unit={t("u.pcs")} hint={t("cs.p.mult_hint")}><Num value={multiplicity} readOnly onCommit={() => undefined} testid="cs-mult" /></Field>
          <Field label={t("cs.p.fill_packet")} unit="%" hint={t("cs.p.fill_packet_hint")}><Num value={c.fill_packet} min={0} max={100} onCommit={(v) => pc({ fill_packet: n(v, 90) })} /></Field>
          <Field label={t("cs.p.max_types")}>
            <Sel value={c.max_part_types_per_map} width={150} onChange={(v) => pc({ max_part_types_per_map: v })}
              options={[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((v) => ({ value: v, label: v ? String(v) : t("cs.p.unlimited") }))} /></Field>
          <div className="form-h">{t("cs.p.prefs")}</div>
          <Field label=" " hint={t("cs.p.big_pack_hint")}><Check checked={c.prefer_big_pack} label={t("cs.p.big_pack")} onChange={(v) => pc({ prefer_big_pack: v })} /></Field>
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
          <Field label=" "><Check checked label={t("cs.p.merge")} disabled title={t("cs.p.merge_hint")} onChange={() => undefined} /></Field>
          <Field label=" "><Check checked label={t("cs.p.save_draw")} disabled title={t("cs.p.save_draw_hint")} onChange={() => undefined} /></Field>
          <Field label={t("cs.p.allowance")} unit={t("u.mm")}><Num value={c.machining_allowance} min={0} onCommit={(v) => pc({ machining_allowance: n(v) })} /></Field>
        </div>
      </div>
      {offsets && <EndOffsets cut={c} onClose={() => setOffsets(false)} onSave={(f) => { pc(f); setOffsets(false); }} />}
    </div>
  );
}

/** «Минимальный отступ в конце»: belgilanmagan qiymat — torsovka bilan bir xil (null). */
function EndOffsets({ cut, onClose, onSave }: { cut: CSCutParams; onClose: () => void;
  onSave: (f: Partial<CSCutParams>) => void }) {
  const { t } = useTranslation();
  const [bOn, setBOn] = useState(cut.end_offset_bottom !== null);
  const [rOn, setROn] = useState(cut.end_offset_right !== null);
  const [b, setB] = useState<number | null>(cut.end_offset_bottom ?? cut.trim_length);
  const [r, setR] = useState<number | null>(cut.end_offset_right ?? cut.trim_width);
  return (
    <Modal title={t("cs.p.end_offset")} onClose={onClose} footer={<>
      <Btn kind="primary" label={t("app.ok")} testid="offsets-ok" onClick={() => onSave({
        end_offset_bottom: bOn ? Math.max(0, b ?? 0) : null, end_offset_right: rOn ? Math.max(0, r ?? 0) : null })} />
      <Btn label={t("app.cancel")} onClick={onClose} /></>}>
      <div className="form-col" data-testid="offsets-dialog">
        <Field label={<Check checked={bOn} label={t("cs.p.offset_bottom")} onChange={setBOn} />} unit={t("u.mm")}>
          <Num value={bOn ? b : cut.trim_length} disabled={!bOn} min={0} onCommit={setB} /></Field>
        <Field label={<Check checked={rOn} label={t("cs.p.offset_right")} onChange={setROn} />} unit={t("u.mm")}>
          <Num value={rOn ? r : cut.trim_width} disabled={!rOn} min={0} onCommit={setR} /></Field>
        <div className="hint">{t("cs.p.end_offset_hint")}</div>
      </div>
    </Modal>
  );
}
