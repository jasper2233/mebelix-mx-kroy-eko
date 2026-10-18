// Ifoda yordamchisi (umumiy komponent): funksiyalar ro'yxati + ifodani serverda tekshirish.
// Ifoda FAQAT serverda hisoblanadi (`POST /api/expr/check`) — frontendda ikkinchi dvigatel yo'q.
// Ishlatuvchilar: «Справка → Выражения»; keyin XNC muharriri (parametr maydonlari) va etiketka shablonlari (maydon ifodalari):
//   <ExprHelper value={expr} onChange={setExpr} variables={[{ name: "dx", sample: 720 }]} onInsert={(s) => insertAtCursor(s)} />
// yoki alohida: <ExprCheck …/> (kiritish + natija) va <ExprFunctions …/> (ro'yxat).
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { CircleAlert, CircleCheck, Search } from "lucide-react";
import { get, post } from "../api/client";
import { useUI } from "../store/ui";
import { cx } from "./ui";
import "./exprHelper.css";
import { pickLang } from "../i18n/lang";

export type ExprValue = number | string | boolean | null;

export interface ExprFunction {
  group: string; name: string; signature: string; description: string; description_ru: string; description_uz: string;
  example: string; example_result: string; example_type: string; pure: boolean;
}
export interface ExprExample { description: string; example: string; example_result: string; example_type: string }
export interface ExprCatalog {
  groups: { key: string; title_ru: string; title_uz: string; count: number }[];
  functions: ExprFunction[];
  constants: (ExprExample & { name: string })[];
  operators: (ExprExample & { operator: string })[];
  limits: { max_length: number; max_steps: number; max_text: number; max_calc_depth: number; max_context: number };
}
export interface ExprCheckResult {
  ok: boolean; type: "integer" | "double" | "boolean" | "string" | "null" | null; value: ExprValue; value_text: string;
  error: string | null; stage: "syntax" | "eval" | null;
}
export interface ExprVariable { name: string; label?: string; sample?: ExprValue }

/** Funksiyalar, konstantalar, operatorlar ro'yxati (til — interfeys tili; server bir marta beradi). */
export function useExprCatalog() {
  const lang = useUI((s) => s.lang);
  return useQuery({ queryKey: ["expr-functions", lang], queryFn: () => get<ExprCatalog>("/expr/functions"), staleTime: Infinity });
}

/** Ifodani serverda tekshiradi (hisoblaydi). `context` — o'zgaruvchi nomi → namuna qiymat. */
export function checkExpr(expr: string, context?: Record<string, ExprValue>, degrees = false): Promise<ExprCheckResult> {
  return post<ExprCheckResult>("/expr/check", { expr, context: context ?? {}, degrees });
}

/** Matn → namuna qiymat: son, true/false, null, aks holda matn. */
export function parseSample(s: string): ExprValue {
  const v = s.trim();
  if (/^-?\d+$/.test(v) && Math.abs(Number(v)) <= 1e15) return Number(v);
  if (/^-?(\d+\.\d*|\.\d+)$/.test(v.replace(",", "."))) return Number(v.replace(",", "."));
  if (v === "true") return true;
  if (v === "false") return false;
  if (v === "null") return null;
  return s;
}

/** Kechiktirilgan (debounce) tekshiruv: yozilayotganda har belgi uchun so'rov yubormaydi, eskirgan javobni tashlaydi. */
export function useExprCheck(expr: string, context?: Record<string, ExprValue>, degrees = false, delay = 350) {
  const [res, setRes] = useState<ExprCheckResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const seq = useRef(0);
  const ctxKey = JSON.stringify(context ?? {});
  useEffect(() => {
    const my = ++seq.current;
    if (!expr.trim()) { setRes(null); setErr(null); setBusy(false); return; }
    setBusy(true);
    const timer = setTimeout(() => {
      checkExpr(expr, JSON.parse(ctxKey) as Record<string, ExprValue>, degrees)
        .then((r) => { if (my === seq.current) { setRes(r); setErr(null); } })
        .catch((e: Error) => { if (my === seq.current) { setRes(null); setErr(e.message); } })
        .finally(() => { if (my === seq.current) setBusy(false); });
    }, delay);
    return () => clearTimeout(timer);
  }, [expr, ctxKey, degrees, delay]);
  return { result: res, error: err, busy };
}

/** Natija chiplari: ✔ tur + qiymat yoki ✖ xato. */
export function ExprResult({ result, error, busy, empty }: { result: ExprCheckResult | null; error?: string | null; busy?: boolean;
  empty?: boolean }) {
  const { t } = useTranslation();
  if (empty) return <div className="expr-res expr-res-idle" data-testid="expr-result">{t("exprh.empty")}</div>;
  if (error) return <div className="expr-res expr-res-bad" data-testid="expr-result"><CircleAlert size={14} /> {error}</div>;
  if (!result) return <div className="expr-res expr-res-idle" data-testid="expr-result">{busy ? t("exprh.checking") : ""}</div>;
  if (!result.ok) {
    return (
      <div className="expr-res expr-res-bad" data-testid="expr-result" data-ok="0">
        <CircleAlert size={14} /> <b>{t(`exprh.stage.${result.stage ?? "eval"}`, { defaultValue: t("exprh.stage.eval") })}:</b> {result.error}
      </div>
    );
  }
  const text = result.type === "string" ? `'${result.value_text}'` : result.type === "null" ? "null" : result.value_text;
  return (
    <div className={cx("expr-res", "expr-res-ok", busy && "expr-res-stale")} data-testid="expr-result" data-ok="1">
      <CircleCheck size={14} /> <span className="expr-type">{t(`exprh.type.${result.type}`, { defaultValue: String(result.type ?? "") })}</span>
      <span className="expr-sep">→</span> <code className="expr-val" data-testid="expr-value">{text}</code>
    </div>
  );
}

/** Ifoda kiritish maydoni + serverda tekshiruv natijasi. `value` berilsa — boshqariladigan, bo'lmasa — ichki holat. */
export function ExprCheck(props: {
  value?: string; onChange?: (v: string) => void; context?: Record<string, ExprValue>; degrees?: boolean; placeholder?: string;
  rows?: number; testid?: string; inputRef?: React.Ref<HTMLTextAreaElement>;
}) {
  const { t } = useTranslation();
  const [own, setOwn] = useState("");
  const value = props.value ?? own;
  const set = (v: string) => { setOwn(v); props.onChange?.(v); };
  const chk = useExprCheck(value, props.context, props.degrees ?? false);
  return (
    <div className="expr-check" data-testid={props.testid ?? "expr-check"}>
      <textarea className="inp expr-input" rows={props.rows ?? 2} spellCheck={false} value={value} ref={props.inputRef}
        placeholder={props.placeholder ?? t("exprh.placeholder")} onChange={(e) => set(e.target.value)} data-testid="expr-input" />
      <ExprResult result={chk.result} error={chk.error} busy={chk.busy} empty={!value.trim()} />
    </div>
  );
}

/** Funksiyalar jadvali: qidiruv, guruhlar. Imzo yoki misolni bosish — `onInsert` / `onExample` chaqiriladi. */
export function ExprFunctions(props: { onInsert?: (text: string) => void; onExample?: (text: string) => void; compact?: boolean }) {
  const { t } = useTranslation();
  const lang = useUI((s) => s.lang);
  const cat = useExprCatalog();
  const [q, setQ] = useState("");
  const [group, setGroup] = useState<string>("");
  const rows = useMemo(() => {
    const k = q.trim().toLowerCase();
    return (cat.data?.functions ?? []).filter((f) => (!group || f.group === group)
      && (!k || f.name.includes(k) || f.signature.toLowerCase().includes(k) || f.description.toLowerCase().includes(k)));
  }, [cat.data, q, group]);
  if (cat.isLoading) return <div className="muted">{t("app.loading")}</div>;
  if (cat.error || !cat.data) return <div className="expr-res expr-res-bad">{String((cat.error as Error | null)?.message ?? "")}</div>;
  const title = (g: { title_ru: string; title_uz: string }) => pickLang(lang, g.title_ru, g.title_uz);
  const fmtEx = (e: { example_result: string; example_type: string }) => (e.example_type === "string" ? `'${e.example_result}'` : e.example_result);
  return (
    <div className={cx("expr-funcs", props.compact && "expr-compact")} data-testid="expr-functions">
      <div className="expr-bar">
        <label className="expr-search"><Search size={14} />
          <input className="inp" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("exprh.search")} data-testid="expr-search" /></label>
        <div className="expr-groups">
          <button type="button" className={cx("chip", !group && "chip-on")} onClick={() => setGroup("")}>{t("exprh.group_all")}</button>
          {cat.data.groups.map((g) => (
            <button key={g.key} type="button" className={cx("chip", group === g.key && "chip-on")} onClick={() => setGroup(g.key)}
              data-testid={`expr-group-${g.key}`}>{title(g)} <span className="muted">{g.count}</span></button>
          ))}
        </div>
      </div>
      <table className="simple expr-table">
        <thead><tr><th>{t("exprh.col.function")}</th><th>{t("exprh.col.description")}</th><th>{t("exprh.col.example")}</th></tr></thead>
        <tbody>
          {rows.map((f) => (
            <tr key={f.name} data-testid={`expr-fn-${f.name}`}>
              <td>
                {props.onInsert
                  ? <button type="button" className="linkbtn expr-sig" title={t("exprh.insert")} onClick={() => props.onInsert?.(f.signature)}>{f.signature}</button>
                  : <code className="expr-sig">{f.signature}</code>}
              </td>
              <td>{f.description}</td>
              <td>
                {props.onExample
                  ? <button type="button" className="linkbtn" onClick={() => props.onExample?.(f.example)}><code>{f.example}</code></button>
                  : <code>{f.example}</code>}
                {" "}<span className="expr-sep">→</span> <code className="expr-val">{fmtEx(f)}</code>
              </td>
            </tr>
          ))}
          {!rows.length && <tr><td colSpan={3} className="muted">{t("exprh.not_found")}</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

/** Konstantalar va operatorlar (til qoidalari) — qisqa jadval. */
export function ExprLanguage() {
  const { t } = useTranslation();
  const cat = useExprCatalog();
  if (!cat.data) return null;
  const fmtEx = (e: { example_result: string; example_type: string }) => (e.example_type === "string" ? `'${e.example_result}'` : e.example_result);
  return (
    <div className="expr-lang" data-testid="expr-language">
      <h3>{t("exprh.operators")}</h3>
      <table className="simple expr-table">
        <tbody>{cat.data.operators.map((o) => (
          <tr key={o.operator}><td><code>{o.operator}</code></td><td>{o.description}</td>
            <td><code>{o.example}</code> <span className="expr-sep">→</span> <code className="expr-val">{fmtEx(o)}</code></td></tr>))}</tbody>
      </table>
      <h3>{t("exprh.constants")}</h3>
      <table className="simple expr-table">
        <tbody>{cat.data.constants.map((c) => (
          <tr key={c.name}><td><code>{c.name}</code></td><td>{c.description}</td>
            <td><code className="expr-val">{c.example_type === "null" ? "null" : fmtEx(c)}</code></td></tr>))}</tbody>
      </table>
    </div>
  );
}

/** To'liq yordamchi: tekshiruv (+ ixtiyoriy o'zgaruvchilar namuna qiymatlari) va funksiyalar ro'yxati. */
export function ExprHelper(props: {
  value?: string; onChange?: (v: string) => void; variables?: ExprVariable[]; context?: Record<string, ExprValue>;
  degrees?: boolean; onInsert?: (text: string) => void; compact?: boolean; testid?: string;
}) {
  const { t } = useTranslation();
  const [own, setOwn] = useState("");
  const value = props.value ?? own;
  const set = (v: string) => { setOwn(v); props.onChange?.(v); };
  const [samples, setSamples] = useState<Record<string, string>>(() =>
    Object.fromEntries((props.variables ?? []).map((v) => [v.name, v.sample === undefined || v.sample === null ? "" : String(v.sample)])));
  const [deg, setDeg] = useState(props.degrees ?? false);
  const ctx = useMemo(() => {
    const c: Record<string, ExprValue> = { ...(props.context ?? {}) };
    for (const v of props.variables ?? []) {
      const s = samples[v.name] ?? "";
      c[v.name] = s === "" && v.sample === null ? null : parseSample(s);
    }
    return c;
  }, [props.context, props.variables, samples]);
  const area = useRef<HTMLTextAreaElement>(null);
  const insert = (text: string) => {
    if (props.onInsert) { props.onInsert(text); return; }
    const el = area.current;
    const a = el?.selectionStart ?? value.length, b = el?.selectionEnd ?? value.length;
    set(value.slice(0, a) + text + value.slice(b));
    requestAnimationFrame(() => { el?.focus(); el?.setSelectionRange(a + text.length, a + text.length); });
  };
  return (
    <div className={cx("expr-helper", props.compact && "expr-compact")} data-testid={props.testid ?? "expr-helper"}>
      <h3>{t("exprh.check_title")}</h3>
      <ExprCheck value={value} onChange={set} context={ctx} degrees={deg} inputRef={area} />
      <div className="expr-opts">
        <label className="check"><input type="checkbox" checked={deg} onChange={(e) => setDeg(e.target.checked)} /><span>{t("exprh.degrees")}</span></label>
        <span className="muted">{t("exprh.server_note")}</span>
      </div>
      {!!props.variables?.length && (
        <div className="expr-vars" data-testid="expr-vars">
          <div className="form-h">{t("exprh.variables")}</div>
          <table className="simple">
            <tbody>{props.variables.map((v) => (
              <tr key={v.name}>
                <td><button type="button" className="linkbtn" title={t("exprh.insert")} onClick={() => insert(v.name)}><code>{v.name}</code></button></td>
                <td className="muted">{v.label ?? ""}</td>
                <td><input className="inp" value={samples[v.name] ?? ""} onChange={(e) => setSamples((s) => ({ ...s, [v.name]: e.target.value }))} /></td>
              </tr>))}</tbody>
          </table>
        </div>
      )}
      <h3>{t("exprh.functions")}</h3>
      <ExprFunctions onInsert={insert} onExample={set} compact={props.compact} />
    </div>
  );
}

