// Etiketka vizual redaktori: qatlamlar (element daraxti), o'zgaruvchilar paneli (sinov qiymatlari bilan) va ExprHelper oynasi.
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Barcode, Braces, Circle, Group, GitBranch, Image as ImageIcon, LayoutTemplate, Minus, QrCode, Ruler, Spline, Square, Type, TriangleAlert } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Btn, Modal, cx } from "../../../shared/ui";
import { ExprHelper, type ExprValue, type ExprVariable } from "../../../shared/ExprHelper";
import { flatten, useLabelVars, type LabelIssue, type LabelTemplate } from "../labelsApi";
import { fxFocus } from "./FxInput";
import { elSummary, pathKey } from "./model";
import { useUI } from "../../../store/ui";
import type { Lang } from "../../../i18n/lang";

const ICONS: Record<string, LucideIcon> = {
  text: Type, rect: Square, line: Minus, image: ImageIcon, barcode: QrCode, part: LayoutTemplate, edges: Ruler, group: Group, if: GitBranch, var: Braces,
  polyline: Spline, arc: Circle, ellipse: Circle,
};

// ───────────────────────── Qatlamlar ─────────────────────────
export function LayersPanel({ tpl, sel, errors, onSelect }: {
  tpl: LabelTemplate; sel: string[]; errors: LabelIssue[]; onSelect: (keys: string[], additive: boolean) => void;
}) {
  const { t } = useTranslation();
  const flat = useMemo(() => flatten(tpl.elements), [tpl]);
  const bad = new Set(errors.map((e) => e.path));
  if (!flat.length) return <div className="muted lbd-empty">{t("lbd.no_elements")}</div>;
  return (
    <div className="lbd-layers" data-testid="lbd-layers">
      {[...flat].reverse().map((f) => {
        const k = pathKey(f.path);
        const Icon = f.el.t === "barcode" && String(f.el.kind ?? "qr").toLowerCase() === "code128" ? Barcode : ICONS[f.el.t] ?? Square;
        return (
          <button type="button" key={k} className={cx("lbd-layer", sel.includes(k) && "lbd-layer-on", bad.has(k) && "lbd-layer-bad")}
            style={{ paddingLeft: 6 + f.depth * 14 }} data-testid={`lbd-layer-${k}`}
            onClick={(e) => onSelect([k], e.shiftKey || e.ctrlKey || e.metaKey)}>
            <Icon size={13} /><span className="lbd-layer-t">{t(`lb.el.${f.el.t === "barcode" ? (String(f.el.kind ?? "qr").toLowerCase() === "code128" ? "code128" : "qr") : f.el.t}`)}</span>
            <span className="lbd-layer-s muted">{elSummary(f.el)}</span>
            {bad.has(k) && <TriangleAlert size={12} color="#c0392b" />}
            <span className="lbd-layer-n muted">{k}</span>
          </button>);
      })}
    </div>
  );
}

// ───────────────────────── O'zgaruvchilar ─────────────────────────
const shortVal = (v: unknown): string => {
  if (v === null || v === undefined) return "∅";
  const s = typeof v === "string" ? `'${v}'` : String(v);
  return s.length > 28 ? s.slice(0, 27) + "…" : s;
};

export function insertOrCopy(text: string, toast: (m: string) => void, copied: string) {
  if (fxFocus.cur) { fxFocus.cur.insert(text); return; }
  void navigator.clipboard?.writeText(text);
  toast(copied);
}

export function VarsPanel({ lang, values, tplValues, tpl }: {
  lang: Lang; values: Record<string, unknown>; tplValues: Record<string, unknown>; tpl: LabelTemplate;
}) {
  const { t } = useTranslation();
  const vars = useLabelVars(lang);
  const [q, setQ] = useState("");
  const toast = useUI((s) => s.toast);
  const key = q.trim().toLowerCase();
  const pick = (text: string) => insertOrCopy(text, (m) => toast(m, "ok"), t("lb.copied", { s: text }));
  const mine = [...tpl.params.map((p) => p.name), ...tpl.vars.map((v) => v.name)].filter((n) => !key || n.toLowerCase().includes(key));
  const userVars = Object.keys(values).filter((n) => n.startsWith("user.") && (!key || n.toLowerCase().includes(key)));
  return (
    <div className="lbd-vars" data-testid="lbd-vars">
      <input className="inp" placeholder={t("exprh.search")} value={q} onChange={(e) => setQ(e.target.value)} data-testid="lbd-vars-q" />
      <div className="muted lbd-vars-hint">{t("lbd.vars_hint")}</div>
      {mine.length > 0 && (
        <div className="lbd-vgroup"><b>{t("lbd.vars_tpl")}</b>
          {mine.map((n) => (
            <button type="button" key={n} className="lbd-var-row" onMouseDown={(e) => e.preventDefault()} onClick={() => pick(n)} title={n}>
              <code>{n}</code><span className="lbd-var-v">{shortVal(tplValues[n])}</span></button>))}
        </div>)}
      {userVars.length > 0 && (
        <div className="lbd-vgroup"><b>user</b>
          {userVars.map((n) => (
            <button type="button" key={n} className="lbd-var-row" onMouseDown={(e) => e.preventDefault()} onClick={() => pick(n)} title={n}>
              <code>{n}</code><span className="lbd-var-v">{shortVal(values[n])}</span></button>))}
        </div>)}
      {vars.data?.groups.map((g) => {
        const rows = g.vars.filter((v) => !key || v.name.toLowerCase().includes(key) || v.title.toLowerCase().includes(key));
        if (!rows.length) return null;
        return (
          <details key={g.key} className="lbd-vgroup" open={!!key || g.key === "part" || g.key === "label"}>
            <summary><b>{g.key}</b> <span className="muted">{rows.length}</span></summary>
            {rows.map((v) => (
              <button type="button" key={v.name} className="lbd-var-row" onMouseDown={(e) => e.preventDefault()} onClick={() => pick(v.name)} title={`${v.title} (${v.type})`}
                data-testid={`lbd-var-${v.name}`}>
                <code>{v.name}</code><span className="lbd-var-v">{shortVal(values[v.name])}</span></button>))}
          </details>);
      })}
      {vars.data && (
        <details className="lbd-vgroup" open={!!key}>
          <summary><b>f(x)</b> <span className="muted">{vars.data.functions.length}</span></summary>
          <div className="lbd-fns">
            {vars.data.functions.filter((f) => !key || f.name.includes(key) || f.sig.toLowerCase().includes(key)).map((f) => (
              <button type="button" key={f.name} className="lbx-chip lbx-fn" onMouseDown={(e) => e.preventDefault()} onClick={() => pick(f.sig)} title={f.group}>{f.sig}</button>))}
          </div>
        </details>)}
    </div>
  );
}

// ───────────────────────── ExprHelper oynasi ─────────────────────────
const ID_RE = /[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*/g;

export function ExprModal({ initial, context, onApply, onClose }: {
  initial: string; context: Record<string, unknown>; onApply: (v: string) => void; onClose: () => void;
}) {
  const { t } = useTranslation();
  const [val, setVal] = useState(initial);
  const ctx = useMemo(() => {
    const c: Record<string, ExprValue> = {};
    for (const [k, v] of Object.entries(context)) if (v === null || ["string", "number", "boolean"].includes(typeof v)) c[k] = v as ExprValue;
    return c;
  }, [context]);
  const vars = useMemo<ExprVariable[]>(() => {
    const names = Array.from(new Set(initial.match(ID_RE) ?? [])).filter((n) => n in ctx);
    return names.slice(0, 12).map((n) => ({ name: n, sample: ctx[n] }));
  }, [initial, ctx]);
  return (
    <Modal title={t("lbd.fx_title")} width={760} height="80vh" onClose={onClose} testid="lbd-fx-modal"
      footer={<>
        <Btn kind="primary" label={t("lbd.fx_apply")} onClick={() => onApply(val)} testid="lbd-fx-apply" />
        <Btn label={t("app.cancel")} onClick={onClose} />
      </>}>
      <ExprHelper value={val} onChange={setVal} variables={vars} context={ctx} compact />
    </Modal>
  );
}
