// CS «Параметры» (UI_SPEC §5.1): chap — material parametrlari, o'ng — kroy parametrlari.
// W2: kroygacha material/list miqdori (CS-036/037), parametr yonida «?» va F1 (CS-048), optimizatorga ulanmagan sozlamalar halol ko'rsatiladi (CS-020/021/022).
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { CircleQuestionMark, RotateCcw, Save } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { get, patch, put } from "../../api/client";
import type { CSCutParams, CSMaterialParams, Operation, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { askConfirm } from "../../shared/dialogs";
import { scopeProps, useHotkeys } from "../../shared/hotkeys";
import { openFocusedParamHelp, useParamHelp } from "../../shared/paramHelpStore";
import { Btn, Check, CheckRow, Field, IconBtn, LinkRow, Modal, Num, Sel, Sep, fmt, money } from "../../shared/ui";
import { CsTabs } from "./CsPanel";
import { useCsQuantities } from "./csHooks";

const ROUNDING = ["11", "12", "13", "14", "22", "23", "24", "32", "33", "34"];
// backend `main.py::_cs_params_stale` bilan mos: kroy natijasini eskirtiradigan maydonlar
const MAT_CUT = new Set(["remnant_min_side1", "remnant_min_side2", "remnant_min_area", "remnant_size_incl_trim", "min_part_size"]);
const CUT_NON = new Set(["quality", "save_drawings", "prefer_big_pack", "strip_sort", "in_strip_sort", "fill_packet", "use_warehouse"]);

export function CsParams({ project, op }: { project: Project; op: Operation }) {
  const { t } = useTranslation();
  const m = op.cs_material!;
  const c = op.cs_cut!;
  const cur = project.currency;
  const res = op.result;
  // F1: fokusdagi parametr bo'lsa — uning yordami, aks holda umumiy «Справка»
  useHotkeys("params", { f1: () => { if (!openFocusedParamHelp()) useUI.getState().set({ section: "help" }); } });
  // Kroy natijasini eskirtiradigan parametr o'zgarsa (backend `_cs_params_stale` bilan bir xil) — oldindan tasdiq so'raladi:
  // natija va omborga yozilgan qoldiqlar o'chadi (Ctrl+Z qaytaradi)
  const staleChange = (kind: "m" | "c", f: Record<string, unknown>) => !!res && res.maps.length > 0
    && Object.keys(f).some((k) => (kind === "m" ? MAT_CUT.has(k) : !CUT_NON.has(k))
      && (kind === "m" ? (m as unknown as Record<string, unknown>)[k] : (c as unknown as Record<string, unknown>)[k]) !== f[k]);
  const guarded = async (kind: "m" | "c", f: Record<string, unknown>) => {
    if (staleChange(kind, f) && !(await askConfirm(t("cs.params_invalidate_q"),
      res?.remnants_saved ? t("cs.params_invalidate_rem") : t("cs.params_invalidate_text"), { danger: true, ok: t("app.ok") }))) return;
    await call(() => patch(`/projects/${project.id}/operations/${op.id}`, kind === "m" ? { cs_material: f } : { cs_cut: f }));
  };
  // Promise qaytaradi: `Num` tasdiq rad etilganda (yoki server xatosida) maydonni saqlangan qiymatga qaytaradi (#7)
  const pm = (f: Partial<CSMaterialParams>) => guarded("m", f);
  const pc = (f: Partial<CSCutParams>) => guarded("c", f);
  // «Количество материала» (по листам ✓ — листы, ☐ — м²) va «Количество листов» (шт): kroygacha taxminiy (≈, backend `calc.cs_cost`),
  // kroydan keyin — natijadan. So'rov kelguncha — natijadagi qiymat (eski xulq).
  const q = useCsQuantities(project, op).data;
  const approx = !!q && q.estimated;
  const matQty = q ? (m.cost_by_sheets ? q.sheets : q.material_qty_m2) : (res ? (m.cost_by_sheets ? res.total_sheets : res.material_qty_m2) : null);
  const sheetsQty = q ? q.sheets_total : (res ? res.total_sheets : null);
  // onlayn tizimdagidek oddiy son («≈» yo'q); baho ekanligi — maydon maslahatida
  const qtyText = (v: number | null, d = 3) => (v === null ? "" : fmt(v, d));
  const multiplicity = m.thickness > 0 ? Math.max(1, Math.floor((c.pack_height + 1e-9) / m.thickness)) : 1;
  const [offsets, setOffsets] = useState(false);
  const saveDefault = async () => {
    const r = await call(() => put("/settings/cs_defaults/default", { material: m, cut: c }));
    if (r) { useUI.getState().toast(t("cs.defaults_saved"), "ok"); void qc.invalidateQueries({ queryKey: ["defaults"] }); }
  };
  // «По умолчанию» (2026-10-26): MebeliX Kroy tavsiya qilgan parametrlar (kroy sifati, zich joylash, arrada oson kesish) —
  // backend `services/recommended.py`; qalinlik, narx, tekstura o'zgarmaydi. Keyingi loyihalar uchun ham standart bo'ladi.
  const applyDefault = async () => {
    const d = await call(() => get<{ cs_material: Partial<CSMaterialParams>; cs_cut: Partial<CSCutParams> }>("/recommended-params"));
    if (!d) return;
    if (!(await askConfirm(t("cs.apply_default"), t("cs.apply_default_q") + (res && res.maps.length ? `
${t("cs.params_invalidate_text")}` : ""),
      { ok: t("app.ok") }))) return;
    await call(() => patch(`/projects/${project.id}/operations/${op.id}`, { cs_material: d.cs_material, cs_cut: d.cs_cut }));
    useUI.getState().toast(t("cs.apply_default_done"), "ok");
  };
  const n = (v: number | null, dflt = 0) => (v === null ? dflt : v);
  return (
    <div className="panel" {...scopeProps("params")}>
      {/* onlayn tartib: Сохранить по умолчанию, Справка; bizning «Применить стандартные параметры» — oxirida */}
      <CsTabs right={<>
        <IconBtn icon={Save} title={t("cs.save_default")} onClick={() => void saveDefault()} testid="cs-save-default" />
        <IconBtn icon={CircleQuestionMark} title={`${t("menu.help")} [F1]`} onClick={() => useUI.getState().set({ section: "help" })} />
        <Sep />
        <IconBtn icon={RotateCcw} title={t("cs.apply_default")} onClick={() => void applyDefault()} testid="cs-apply-default" />
      </>} />
      <div className="form2 scroll" data-testid="cs-params">
        <div className="form-col">
          <div className="form-h">{t("cs.p.material")}</div>
          {/* qalinlik: 0.1 – 200 mm va paket balandligidan katta emas (kratnost ≥ 1) — aks holda eski qiymat qoladi va sabab ko'rsatiladi */}
          <Field label={t("cs.p.thickness")} unit={t("u.mm")} help="thickness"><Num value={m.thickness} min={0.1} max={200}
            check={(v) => (c.pack_height >= 0.1 && v > c.pack_height ? t("num.thick_pack", { h: fmt(c.pack_height, 2) }) : null)}
            onCommit={(v) => pm({ thickness: n(v, 16) })} testid="cs-thickness" /></Field>
          <div className="form-h">{t("cs.p.cost")}</div>
          {/* birlik — faqat valyuta (onlayn tizimdagidek); «за лист / за м²» ma'nosi maslahatda va yordamda */}
          <Field label={t("cs.p.price")} hint={t("cs.p.price_hint")} help="price" unit={cur}>
            <Num value={m.price} min={0} max={1e9} onCommit={(v) => pm({ price: n(v) })} testid="cs-price" /></Field>
          <Field label={t("cs.p.est_fill")} unit="%" hint={t("cs.p.est_fill_hint")} help="est_fill"><Num value={m.est_fill_percent} min={1} max={100} onCommit={(v) => pm({ est_fill_percent: n(v, 90) })} /></Field>
          <Field label={t("cs.p.material_qty")} unit={m.cost_by_sheets ? t("cs.p.sheets_u") : t("u.m2")} hint={`${t("cs.p.material_qty_hint")}${approx ? `\n${t("cs.p.estimated_hint")}` : ""}`}
            help="material_qty">
            <span className="ro" data-testid="cs-material-qty">{qtyText(matQty)}</span></Field>
          <Field label={t("cs.p.sheets_qty")} unit={t("u.pcs")} hint={`${t("cs.p.sheets_qty_hint")}${approx ? `\n${t("cs.p.estimated_hint")}` : ""}`} help="sheets_qty">
            <span className="ro" data-testid="cs-sheets-qty">{qtyText(sheetsQty, 0)}</span></Field>
          {/* bayroqlar — yorliq ustunida, har biri alohida qator (xodimlar o'rgangan tizim joylashuvi) */}
          <CheckRow checked={m.cost_by_sheets} label={t("cs.p.cost_by_sheets")} onChange={(v) => pm({ cost_by_sheets: v })} help="cost_by_sheets" />
          <Field label={t("cs.p.rounding")} help="rounding">
            <Sel value={m.sheet_rounding} width={190} onChange={(v) => pm({ sheet_rounding: v })}
              options={ROUNDING.map((r) => ({ value: r, label: t(`cs.round.${r}`) }))} /></Field>
          <Field label={t("cs.p.cost_material")} unit={cur} help="cost_material"><span className="ro">{money(op.cost_material)}</span></Field>
          <Field label={t("cs.p.op_base")} help="op_base">
            <Sel value={m.op_cost_base} width={190} onChange={(v) => pm({ op_cost_base: v })}
              options={[0, 1, 2, 3].map((v) => ({ value: v, label: t(`cs.opbase.${v}`) }))} /></Field>
          <Field label={t("cs.p.op_price")} unit={cur} help="op_price"><Num value={m.op_price} min={0} max={1e9} onCommit={(v) => pm({ op_price: n(v) })} /></Field>
          <Field label={t("cs.p.cost_op")} unit={cur} help="cost_op"><span className="ro">{money(op.cost_operation)}</span></Field>
          <div className="form-h">{t("cs.p.remnant")}</div>
          <Field label={t("cs.p.rem1")} unit={t("u.mm")} help="rem1"><Num value={m.remnant_min_side1} min={0} max={20000} onCommit={(v) => pm({ remnant_min_side1: n(v, 1000) })} /></Field>
          <Field label={t("cs.p.rem2")} unit={t("u.mm")} help="rem2"><Num value={m.remnant_min_side2} min={0} max={20000} onCommit={(v) => pm({ remnant_min_side2: n(v, 500) })} /></Field>
          <Field label={t("cs.p.rem_area")} unit={t("u.m2")} help="rem_area"><Num value={m.remnant_min_area} min={0} max={100} onCommit={(v) => pm({ remnant_min_area: n(v, 0.5) })} /></Field>
          <CheckRow checked={m.remnant_size_incl_trim} label={t("cs.p.rem_trim")} onChange={(v) => pm({ remnant_size_incl_trim: v })} help="rem_trim" />
          <div className="form-h">{t("cs.p.limits")}</div>
          <Field label={t("cs.p.min_part")} unit={t("u.mm")} hint={t("cs.p.min_part_hint")} help="min_part"><Num value={m.min_part_size} min={0} max={1000} onCommit={(v) => pm({ min_part_size: n(v, 30) })} /></Field>
        </div>
        <div className="form-col">
          <div className="form-h">{t("cs.p.cut")}</div>
          <Field label={t("cs.p.kerf")} unit={t("u.mm")} help="kerf"><Num value={c.kerf} min={0} max={50} onCommit={(v) => pc({ kerf: n(v, 3) })} testid="cs-kerf" /></Field>
          <Field label={t("cs.p.kerf_group")} unit={t("u.mm")} hint={t("cs.p.kerf_group_hint")} help="kerf_group"><Num value={c.kerf_group} allowEmpty min={0} max={50} onCommit={(v) => pc({ kerf_group: v })} /></Field>
          <Field label={t("cs.p.trim_l")} unit={t("u.mm")} hint={t("cs.p.trim_l_hint")} help="trim_l"><Num value={c.trim_length} min={0} max={500} onCommit={(v) => pc({ trim_length: n(v) })} /></Field>
          <Field label={t("cs.p.trim_w")} unit={t("u.mm")} hint={t("cs.p.trim_w_hint")} help="trim_w"><Num value={c.trim_width} min={0} max={500} onCommit={(v) => pc({ trim_width: n(v) })} /></Field>
          {/* onlayn tizimdagidek — yorliq ustunidagi ko'k havola (oynani ochadi); joriy qiymatlar — maslahatda */}
          <LinkRow label={t("cs.p.end_offset")} help="end_offset" testid="cs-end-offsets" onClick={() => setOffsets(true)}
            hint={`${t("cs.p.end_offset_hint")}\n${t("cs.p.offset_bottom_s")} ${c.end_offset_bottom ?? c.trim_length}, ${t("cs.p.offset_right_s")} ${c.end_offset_right ?? c.trim_width} ${t("u.mm")}`} />
          <Field label={t("cs.p.first_cut")} help="first_cut">
            <Sel value={c.first_cut} width={190} onChange={(v) => pc({ first_cut: v })}
              options={[0, 1, 2, 3, 4].map((v) => ({ value: v as 0, label: t(`cs.first.${v}`) }))} /></Field>
          <CheckRow checked={c.use_grain} label={t("cs.p.use_grain")} onChange={(v) => pc({ use_grain: v })} help="use_grain" />
          <CheckRow checked={c.complex_strips} label={t("cs.p.complex")} hint={t("cs.p.complex_hint")} onChange={(v) => pc({ complex_strips: v })} help="complex" />
          <Field label={t("cs.p.max_rot")} help="max_rot">
            <Sel value={c.max_rotations} width={80} onChange={(v) => pc({ max_rotations: v })}
              options={[1, 2, 3, 4, 5, 6].map((v) => ({ value: v, label: String(v) }))} /></Field>
          <Field label={t("cs.p.pack_h")} unit={t("u.mm")} hint={t("cs.p.pack_hint")} help="pack_h"><Num value={c.pack_height} min={0} max={1000}
            check={(v) => (v > 0 && v < m.thickness ? t("num.pack_thick", { th: fmt(m.thickness, 2) }) : null)}
            onCommit={(v) => pc({ pack_height: n(v, 40) })} testid="cs-pack-height" /></Field>
          <Field label={t("cs.p.mult")} unit={t("u.pcs")} hint={t("cs.p.mult_hint")} help="mult"><Num value={multiplicity} readOnly onCommit={() => undefined} testid="cs-mult" /></Field>
          <Field label={t("cs.p.max_types")} help="max_types">
            <Sel value={c.max_part_types_per_map} width={150} onChange={(v) => pc({ max_part_types_per_map: v })}
              options={[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((v) => ({ value: v, label: v ? String(v) : t("cs.p.unlimited") }))} /></Field>
          <div className="form-h">{t("cs.p.prefs")}</div>
          <CheckRow checked={c.prefer_big_pack} label={t("cs.p.big_pack")} hint={t("cs.p.big_pack_hint")} onChange={(v) => pc({ prefer_big_pack: v })} help="big_pack" />
          <div className="form-h">{t("cs.p.sorting")}</div>
          <Field label={t("cs.p.sort_strips")} help="sort_strips">
            <Sel value={c.strip_sort} width={170} onChange={(v) => pc({ strip_sort: v })}
              options={[0, 1, 2, 3].map((v) => ({ value: v as 0, label: t(`cs.sort.${v}`) }))} /></Field>
          <Field label={t("cs.p.sort_in")} help="sort_in">
            <Sel value={c.in_strip_sort} width={170} onChange={(v) => pc({ in_strip_sort: v })}
              options={[0, 1, 2, 3].map((v) => ({ value: v as 0, label: t(`cs.sort.${v}`) }))} /></Field>
          <Field label={t("cs.p.min_strip")} unit={t("u.mm")} help="min_strip"><Num value={c.min_strip_width} min={0} max={20000} onCommit={(v) => pc({ min_strip_width: n(v) })} /></Field>
          <Field label={t("cs.p.max_strip")} unit={t("u.mm")} hint={t("cs.p.max_strip_hint")} help="max_strip"><Num value={c.max_strip_width} min={0} max={20000} onCommit={(v) => pc({ max_strip_width: n(v) })} /></Field>
          <Field label={t("cs.p.max_strip_len")} unit={t("u.mm")} help="max_strip_len"><Num value={c.max_strip_length} min={0} max={100000} onCommit={(v) => pc({ max_strip_length: n(v, 10000) })} /></Field>
          <Field label={t("cs.p.min_trim")} unit={t("u.mm")} hint={t("cs.p.min_trim_hint")} help="min_trim"><Num value={c.min_trim_cut} min={0} max={500} onCommit={(v) => pc({ min_trim_cut: n(v, 5) })} /></Field>
          {/* Optimizatorga ulanmagan bayroqlar: qiymat loyihada saqlanadi, kroyga ta'sir qilmaydi (izoh — maslahat va «?» yordamida).
              «Группировка деталей по свойствам» — havola, «Объединение деталей» yoqilganda faol (yordam oynasini ochadi) */}
          <CheckRow checked={c.merge_parts} label={t("cs.p.merge")} hint={t("cs.p.merge_hint")} onChange={(v) => pc({ merge_parts: v })}
            help="merge" testid="cs-merge" />
          <LinkRow label={t("cs.p.group_props")} disabled={!c.merge_parts} hint={t("cs.p.group_props_note")} help="group_props"
            testid="cs-group-props" onClick={() => useParamHelp.getState().open("group_props")} />
          <CheckRow checked={c.save_drawings} label={t("cs.p.save_draw")} hint={t("cs.p.save_draw_hint")} onChange={(v) => pc({ save_drawings: v })}
            help="save_draw" testid="cs-save-draw" />
          <Field label={t("cs.p.allowance")} unit={t("u.mm")} help="allowance"><Num value={c.machining_allowance} min={0} max={500} onCommit={(v) => pc({ machining_allowance: n(v) })} /></Field>
          {/* Bizning qo'shimcha parametrlar — alohida guruhda, panel oxirida (asosiy ro'yxat onlayn tizim bilan bir xil) */}
          <div className="form-h" title={t("cs.p.extra_hint")}>{t("cs.p.extra")}</div>
          {/* (2026-10-24) kroydan keyin bazadan oxirgi listlar detallariga yetadigan qoldiq qidiriladi (Настройки → Правила остатков) */}
          <CheckRow checked={!!c.use_warehouse} label={t("cs.p.use_warehouse")} hint={t("cs.p.use_warehouse_hint")}
            onChange={(v) => pc({ use_warehouse: v })} testid="cs-use-warehouse" />
          <CheckRow checked={c.trim_includes_kerf} label={t("cs.p.trim_kerf")} onChange={(v) => pc({ trim_includes_kerf: v })} help="trim_kerf" />
          <Field label={t("cs.p.fill_packet")} unit="%" hint={t("cs.p.fill_packet_hint")} help="fill_packet"><Num value={c.fill_packet} min={0} max={100} onCommit={(v) => pc({ fill_packet: n(v, 90) })} /></Field>
          <Field label={t("cs.p.stock_order")} hint={t("cs.p.stock_order_hint")} help="stock_order">
            <Sel value={c.stock_order ?? "list"} width={190} onChange={(v) => pc({ stock_order: v })} testid="cs-stock-order"
              options={(["list", "economy"] as const).map((v) => ({ value: v, label: t(`cs.stock_order.${v}`) }))} /></Field>
          <Field label={t("cs.p.quality")} hint={t("cs.p.quality_hint")} help="quality">
            <Sel value={c.quality} width={150} onChange={(v) => pc({ quality: v })} testid="cs-quality"
              options={(["fast", "normal", "max"] as const).map((v) => ({ value: v, label: t(`cs.quality.${v}`) }))} /></Field>
        </div>
      </div>
      {offsets && <EndOffsets cut={c} onClose={() => setOffsets(false)} onSave={(f) => { void pc(f); setOffsets(false); }} />}
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
