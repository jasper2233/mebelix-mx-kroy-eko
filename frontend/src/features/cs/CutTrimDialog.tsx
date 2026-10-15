// «Торцовка листа» (CSE-009): shu kartaga alohida torsovka — ТД / ТШ / minimal otstup (pastda, o'ngda).
// Bo'sh maydon — list qatori / operatsiya qiymati (placeholder'da ko'rsatiladi). Foydali zona hisobi `optimizer._zone` bilan bir xil.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { CutMap, Operation } from "../../api/types";
import { Btn, Field, Modal, fmt, parseNum } from "../../shared/ui";
import "./cseW13.css";

export type TrimKey = "trim_length" | "trim_width" | "end_offset_bottom" | "end_offset_right";
export const TRIM_KEYS: TrimKey[] = ["trim_length", "trim_width", "end_offset_bottom", "end_offset_right"];
export type TrimValues = Record<TrimKey, number | null>;

/** Karta uchun amaldagi (yoki berilgan override bilan) torsovka qiymatlari va foydali zona o'lchami. */
export function trimZone(op: Operation, map: CutMap, over: Partial<TrimValues>) {
  const cut = op.cs_cut;
  const sh = op.sheets.find((s) => s.id === map.sheet_id);
  const pick = (k: TrimKey): number | null | undefined => (k in over ? over[k] : map[k]);
  const tl = pick("trim_length") ?? sh?.trim_length ?? cut?.trim_length ?? 0;
  const tw = pick("trim_width") ?? sh?.trim_width ?? cut?.trim_width ?? 0;
  const eb = pick("end_offset_bottom") ?? sh?.end_offset_bottom ?? cut?.end_offset_bottom ?? tl;
  const er = pick("end_offset_right") ?? sh?.end_offset_right ?? cut?.end_offset_right ?? tw;
  const add = cut?.trim_includes_kerf ? 0 : (cut?.kerf ?? 0);
  const oy = tl > 0 ? tl + add : 0, ox = tw > 0 ? tw + add : 0;
  const fy = eb > 0 ? eb + add : 0, fx = er > 0 ? er + add : 0;
  return { tl, tw, eb, er, UL: map.sheet_length - ox - fx, UW: map.sheet_width - oy - fy };
}

export function CutTrimDialog({ op, map, onApply, onClose }: { op: Operation; map: CutMap;
  onApply: (changes: Partial<TrimValues>) => void; onClose: () => void }) {
  const { t } = useTranslation();
  const init = (k: TrimKey) => (map[k] === null || map[k] === undefined ? "" : String(map[k]));
  const [vals, setVals] = useState<Record<TrimKey, string>>({
    trim_length: init("trim_length"), trim_width: init("trim_width"),
    end_offset_bottom: init("end_offset_bottom"), end_offset_right: init("end_offset_right"),
  });
  const parsed = (k: TrimKey): number | null | "bad" => {
    const s = vals[k].trim();
    if (s === "") return null;
    const n = parseNum(s);
    return n === null || n < 0 || n > 500 ? "bad" : n;
  };
  const over: Partial<TrimValues> = {};
  let invalid = false;
  for (const k of TRIM_KEYS) {
    const v = parsed(k);
    if (v === "bad") invalid = true; else over[k] = v;
  }
  const z = trimZone(op, map, invalid ? {} : over);
  // placeholder: har maydon uchun «meros» qiymat (list qatori / operatsiya); otstup torsovkaga ergashadi
  const nul: TrimValues = { trim_length: null, trim_width: null, end_offset_bottom: null, end_offset_right: null };
  const base = trimZone(op, map, nul);
  const ptl = parsed("trim_length"), ptw = parsed("trim_width");
  const withTrim = trimZone(op, map, { ...nul, trim_length: typeof ptl === "number" ? ptl : null, trim_width: typeof ptw === "number" ? ptw : null });
  const hint: Record<TrimKey, number> = {
    trim_length: base.tl, trim_width: base.tw, end_offset_bottom: withTrim.eb, end_offset_right: withTrim.er,
  };
  const changes = (): Partial<TrimValues> => {
    const out: Partial<TrimValues> = {};
    for (const k of TRIM_KEYS) {
      const v = over[k] ?? null;
      if (v !== (map[k] ?? null)) out[k] = v;
    }
    return out;
  };
  const apply = () => {
    if (invalid) return;
    const c = changes();
    if (Object.keys(c).length) onApply(c);
    onClose();
  };
  const field = (k: TrimKey, label: string) => (
    <Field label={label} unit={t("u.mm")} hint={t("editor.trim_inherit_hint")}>
      <input className="inp num" value={vals[k]} placeholder={fmt(hint[k])} data-testid={`trim-${k}`}
        style={{ width: 90, borderColor: parsed(k) === "bad" ? "#c0392b" : undefined }}
        onChange={(e) => setVals({ ...vals, [k]: e.target.value })}
        onKeyDown={(e) => { if (e.key === "Enter") apply(); }} />
    </Field>
  );
  return (
    <Modal title={`${t("editor.trim_title")} — №${map.index}`} onClose={onClose} width={440} testid="map-trim-dialog"
      footer={<>
        <Btn small label={t("editor.trim_reset")} onClick={() => setVals({ trim_length: "", trim_width: "", end_offset_bottom: "", end_offset_right: "" })}
          testid="trim-reset" />
        <span style={{ flex: 1 }} />
        <Btn kind="primary" label={t("app.ok")} onClick={apply} disabled={invalid} testid="trim-ok" />
        <Btn label={t("app.cancel")} onClick={onClose} />
      </>}>
      <div className="form1 trim-form">
        <div className="muted">{t("editor.trim_hint")}</div>
        {field("trim_length", t("editor.trim_length"))}
        {field("trim_width", t("editor.trim_width"))}
        {field("end_offset_bottom", t("editor.trim_bottom"))}
        {field("end_offset_right", t("editor.trim_right"))}
        <div className="trim-zone" data-testid="trim-zone">
          {t("editor.trim_zone")}: <b>{fmt(z.UL)} × {fmt(z.UW)}</b>
          <span className="muted"> ({fmt(map.sheet_length)} × {fmt(map.sheet_width)})</span>
          {z.UL <= 0 || z.UW <= 0 ? <span className="warn"> — {t("editor.trim_too_big")}</span> : null}
        </div>
      </div>
    </Modal>
  );
}
