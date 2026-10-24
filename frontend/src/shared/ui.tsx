// Umumiy interfeys elementlari (MebeliX uslubi).
import { useEffect, useRef, useState, type ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { X } from "lucide-react";
import { toneProps } from "./iconTone";
import { useModalScope, useHotkeys } from "./hotkeys";
import { fmtTitle } from "./keyLabel";
import { setFocusedParam, useParamHelp } from "./paramHelpStore";
import i18n from "../i18n";
import { focusGridIn } from "./grid/Grid";
import { useUI } from "../store/ui";
import { layoutHeight, uiZoom } from "./uiZoom";

export function cx(...a: (string | false | null | undefined)[]) {
  return a.filter(Boolean).join(" ");
}

export function Btn(props: {
  icon?: LucideIcon; label?: ReactNode; title?: string; onClick?: () => void; disabled?: boolean;
  kind?: "primary" | "default" | "danger" | "ghost" | "big"; small?: boolean; type?: "button" | "submit";
  testid?: string; active?: boolean;
}) {
  const Icon = props.icon;
  return (
    <button type={props.type ?? "button"} className={cx("btn", `btn-${props.kind ?? "default"}`, props.small && "btn-sm",
      props.active && "btn-active")} title={fmtTitle(props.title)} onClick={props.onClick} disabled={props.disabled}
      data-testid={props.testid}>
      {Icon && <Icon size={props.small ? 14 : 16} strokeWidth={2} />}
      {props.label && <span>{props.label}</span>}
    </button>
  );
}

/** Toolbar ikonkasi: title — yordam matni va yorliq («Клонировать (Ctrl+K)» → «Клонировать [CTRL]+[K]», shared/keyLabel.ts). */
export function IconBtn(props: { icon: LucideIcon; title: string; onClick?: () => void; disabled?: boolean;
  color?: string; active?: boolean; testid?: string; label?: string }) {
  const Icon = props.icon;
  const title = fmtTitle(props.title);
  return (
    <button type="button" className={cx("ibtn", props.active && "ibtn-active", props.label && "ibtn-label")}
      title={title} aria-label={title} onClick={props.onClick} disabled={props.disabled}
      data-testid={props.testid}>
      <Icon size={16} strokeWidth={2} {...toneProps(props.icon, props.disabled, props.color)} />
      {props.label && <span>{props.label}</span>}
    </button>
  );
}

export function Toolbar({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cx("toolbar", className)}>{children}</div>;
}

export function Sep() {
  return <span className="tsep" />;
}

export function Tabs<K extends string>(props: { tabs: { key: K; label: ReactNode; icon?: LucideIcon; testid?: string }[];
  value: K; onChange: (k: K) => void; right?: ReactNode }) {
  return (
    <div className="tabs">
      {props.tabs.map((t) => {
        const Icon = t.icon;
        return (
          // yorliqlar TAB tartibida emas (TAB ro'yxat bo'ylab yuradi); bosilganda — shu panel jadvalining 1-qatoriga fokus
          <button key={t.key} type="button" className={cx("tab", props.value === t.key && "tab-active")} tabIndex={-1}
            onClick={(e) => { const panel = e.currentTarget.closest(".tabs"); props.onChange(t.key);
              setTimeout(() => focusGridIn(panel), 120); }} data-testid={t.testid}>
            {Icon && <Icon size={14} {...toneProps(Icon)} />} {t.label}
          </button>
        );
      })}
      <div className="tabs-right">{props.right}</div>
    </div>
  );
}

/** Parametr yonidagi «?» (CS-048): bosilsa shu parametr yordami (i18n `phelp.<kalit>`) ochiladi. */
function QMark({ help }: { help: string }) {
  return (
    <button type="button" className="qmark" title={`${i18n.t("phelp.open")} [F1]`} aria-label={i18n.t("phelp.open")}
      data-testid={`qmark-${help}`} tabIndex={-1}
      onClick={(e) => { e.preventDefault(); e.stopPropagation(); useParamHelp.getState().open(help); }}>?</button>
  );
}

/** `help` — parametr yordami kaliti: yorliq yonida «?» va parametr fokusda bo'lganda F1 shu yordamni ochadi (CS-048). */
export function Field(props: { label: ReactNode; children: ReactNode; unit?: ReactNode; hint?: string; wide?: boolean;
  help?: string; /** yorliq kiritish maydoni USTIDA (tor ustunlar, masalan XNC «Параметры») */ stack?: boolean }) {
  const help = props.help;
  return (
    <label className={cx("field", props.wide && "field-wide", props.stack && "field-stack")} title={props.hint}
      onFocusCapture={help ? () => setFocusedParam(help) : undefined} onBlurCapture={help ? () => setFocusedParam(null) : undefined}>
      <span className="field-label">{props.label}{help && <QMark help={help} />}</span>
      <span className="field-ctl">{props.children}</span>
      <span className="field-unit">{props.unit}</span>
    </label>
  );
}

/** Bayroq qatori (parametr panellari): katakcha va yozuv yorliq ustunida, kiritish ustuni bo'sh — xodimlar o'rgangan
 *  tizimdagi joylashuv. `help` — «?» va F1 yordami kaliti; `hint` — butun qator maslahati. */
export function CheckRow(props: { checked: boolean; onChange: (v: boolean) => void; label: ReactNode; disabled?: boolean;
  testid?: string; hint?: string; help?: string }) {
  return (
    <div className="field field-check" title={props.hint}>
      <span className="field-label">
        <Check checked={props.checked} onChange={props.onChange} label={props.label} disabled={props.disabled}
          testid={props.testid} help={props.help} />
      </span>
      <span className="field-ctl" /><span className="field-unit" />
    </div>
  );
}

/** Havola ko'rinishidagi qator (parametr panellari): ko'k matn yorliq ustunida; `disabled` — xira (faol emas) ko'rinish. */
export function LinkRow(props: { label: ReactNode; onClick?: () => void; disabled?: boolean; testid?: string; hint?: string;
  help?: string }) {
  return (
    <div className="field field-check" title={props.hint}>
      <span className="field-label">
        <button type="button" className="linktext" disabled={props.disabled} onClick={props.onClick} data-testid={props.testid}>
          {props.label}</button>
        {props.help && <QMark help={props.help} />}
      </span>
      <span className="field-ctl" /><span className="field-unit" />
    </div>
  );
}

export function parseNum(s: string): number | null {
  const v = s.replace(/\s/g, "").replace(",", ".");
  if (v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

/** `onCommit` Promise qaytarsa — u tugagach maydon saqlangan qiymatga qaytariladi (rad etilgan / xato bo'lgan
 *  o'zgarish kiritilgan son bilan qolib ketmaydi: CS «Параметры» tasdiqi, sarlavha valyutasi, server 4xx). */
function resyncAfter(r: unknown, reset: () => void) {
  if (r && typeof (r as Promise<unknown>).then === "function") void (r as Promise<unknown>).then(reset, reset);
}

/** Son chegarasini qisqa ko'rinishda (0.1, 200, 1 000 000 emas — 1000000). */
function numTxt(v: number): string { return String(Math.round(v * 1e6) / 1e6); }

/** Maydon yorlig'i va birligi — `Field` ichida bo'lsa uning matnidan (har chaqiruvga alohida yozilmasin). */
function fieldMeta(el: HTMLElement | null): { label: string; unit: string } {
  const f = el?.closest(".field");
  const label = (f?.querySelector(".field-label")?.textContent ?? el?.getAttribute("aria-label") ?? "").replace(/\?$/, "").trim().replace(/:$/, "");
  const unit = (f?.querySelector(".field-unit")?.textContent ?? "").trim();
  return { label, unit };
}

/** Son maydoni: Enter yoki fokus yo'qolganda saqlanadi (vergul ham qabul qilinadi).
 *  Chegaradan tashqari / son bo'lmagan qiymat jimgina qisqartirilmaydi: eski qiymat qoladi, maydon qizil chegarali va
 *  maslahatida sabab, ogohlantirish xabari («Толщина: допустимо 0.1 – 200 мм») chiqadi, fokus maydonga qaytadi.
 *  `check` — qo'shimcha (maydonlararo) qoida: xato matnini qaytaradi, `label` — yorliq `Field` dan olinmasa. */
export function Num(props: { value: number | null | undefined; onCommit: (v: number | null) => unknown;
  disabled?: boolean; allowEmpty?: boolean; min?: number; max?: number; width?: number; testid?: string; readOnly?: boolean;
  check?: (v: number) => string | null | undefined; label?: string }) {
  const [s, setS] = useState(props.value == null ? "" : String(props.value));
  const [bad, setBad] = useState<string | null>(null);
  const ref = useRef<HTMLInputElement>(null);
  const latest = useRef(props.value);
  latest.current = props.value;
  useEffect(() => { setS(props.value == null ? "" : String(props.value)); setBad(null); }, [props.value]);
  const reject = (why: string, refocus: boolean) => {
    const el = ref.current;
    const label = props.label ?? fieldMeta(el).label;
    const text = label ? `${label}: ${why}` : why;
    setS(props.value == null ? "" : String(props.value));
    setBad(why);
    useUI.getState().toast(text, "warn");
    // fokus maydonga qaytadi (boshqa oyna / sahifa tanlangan bo'lsa — yo'q)
    if (refocus) setTimeout(() => {
      if (el && el.isConnected && !el.disabled && document.hasFocus()) { el.focus(); el.select(); }
    }, 0);
  };
  const rangeText = () => {
    const unit = fieldMeta(ref.current).unit;
    const u = unit ? ` ${unit}` : "";
    const lo = props.min, hi = props.max;
    if (lo !== undefined && hi !== undefined) return i18n.t("num.range", { min: numTxt(lo), max: numTxt(hi), u });
    if (lo !== undefined) return i18n.t("num.min", { min: numTxt(lo), u });
    return i18n.t("num.max", { max: numTxt(hi ?? 0), u });
  };
  const commit = (refocus: boolean) => {
    if (props.readOnly || props.disabled) return;
    const n = parseNum(s);
    if (n === null) {
      if (s.trim() === "" && props.allowEmpty) { if (props.value != null) resyncAfter(props.onCommit(null), () => setS(latest.current == null ? "" : String(latest.current))); setBad(null); return; }
      if (s.trim() === "" && props.value == null) return;
      reject(i18n.t(s.trim() === "" ? "num.empty" : "num.nan"), refocus);
      return;
    }
    if ((props.min !== undefined && n < props.min) || (props.max !== undefined && n > props.max)) { reject(rangeText(), refocus); return; }
    const why = props.check?.(n);
    if (why) { reject(why, refocus); return; }
    setBad(null);
    if (n !== props.value) resyncAfter(props.onCommit(n), () => setS(latest.current == null ? "" : String(latest.current)));
    else setS(String(n));
  };
  return (
    <input ref={ref} className={cx("inp num", bad && "inp-bad")} value={s} disabled={props.disabled} readOnly={props.readOnly}
      style={{ width: props.width }} title={bad ?? undefined} aria-invalid={bad ? true : undefined}
      onChange={(e) => { setS(e.target.value); if (bad) setBad(null); }} onBlur={() => commit(true)} data-testid={props.testid}
      onKeyDown={(e) => { if (e.key === "Enter") { commit(false); (e.target as HTMLInputElement).select(); } }} />
  );
}

export function Txt(props: { value: string; onCommit: (v: string) => unknown; disabled?: boolean;
  placeholder?: string; width?: number | string; testid?: string; maxLength?: number }) {
  const [s, setS] = useState(props.value);
  const latest = useRef(props.value);
  latest.current = props.value;
  useEffect(() => { setS(props.value); }, [props.value]);
  const commit = () => { if (s !== props.value) resyncAfter(props.onCommit(s), () => setS(latest.current)); };
  return (
    <input className="inp" value={s} disabled={props.disabled} placeholder={props.placeholder}
      style={{ width: props.width }} maxLength={props.maxLength} data-testid={props.testid}
      onChange={(e) => setS(e.target.value)} onBlur={commit} onKeyDown={(e) => { if (e.key === "Enter") commit(); }} />
  );
}

export function Area(props: { value: string; onCommit: (v: string) => void; rows?: number; placeholder?: string;
  testid?: string }) {
  const [s, setS] = useState(props.value);
  useEffect(() => { setS(props.value); }, [props.value]);
  return (
    <textarea className="inp area" rows={props.rows ?? 3} value={s} placeholder={props.placeholder}
      data-testid={props.testid} onChange={(e) => setS(e.target.value)}
      onBlur={() => { if (s !== props.value) props.onCommit(s); }} />
  );
}

export function Check(props: { checked: boolean; onChange: (v: boolean) => void; label?: ReactNode; disabled?: boolean;
  testid?: string; title?: string; help?: string }) {
  const help = props.help;
  return (
    <label className="check" title={props.title}
      onFocusCapture={help ? () => setFocusedParam(help) : undefined} onBlurCapture={help ? () => setFocusedParam(null) : undefined}>
      <input type="checkbox" checked={props.checked} disabled={props.disabled} data-testid={props.testid}
        onChange={(e) => props.onChange(e.target.checked)} />
      {props.label && <span>{props.label}</span>}
      {help && <QMark help={help} />}
    </label>
  );
}

export function Sel<V extends string | number>(props: { value: V; options: { value: V; label: ReactNode }[];
  onChange: (v: V) => void; disabled?: boolean; width?: number | string; testid?: string }) {
  return (
    <select className={cx("inp sel", typeof props.width === "number" && props.width < 120 && "sel-narrow")} value={String(props.value)} disabled={props.disabled} style={{ width: props.width }}
      data-testid={props.testid}
      onChange={(e) => {
        const o = props.options.find((x) => String(x.value) === e.target.value);
        if (o) props.onChange(o.value);
      }}>
      {props.options.map((o) => <option key={String(o.value)} value={String(o.value)}>{o.label as string}</option>)}
    </select>
  );
}

export function Modal(props: { title: ReactNode; onClose: () => void; children: ReactNode; footer?: ReactNode;
  width?: number | string; height?: number | string; scope?: string; full?: boolean; testid?: string;
  headerRight?: ReactNode }) {
  const scope = props.scope ?? "modal";
  useModalScope(scope);
  useHotkeys(scope, { escape: () => props.onClose() });
  const box = useRef<HTMLDivElement>(null);
  // Ochilganda fokus birinchi matn/son maydoniga; maydon bo'lmasa (yoki to'liq ekranli muharrir) — oynaning o'ziga: shunda
  // Ctrl+Z, Del kabi oyna yorliqlari ishlayveradi (katakcha/tugmaga fokus tushsa yorliqlar «matn kiritish» deb o'tkazib yuborilardi).
  // Tab fokusni oyna ichida aylantiradi (klaviatura / a11y). Kechiktirib: oynani ochgan Enter yangi fokusdagi tugmani bosmasin
  useEffect(() => {
    const tm = setTimeout(() => {
      const el = box.current;
      if (!el || el.contains(document.activeElement)) return;
      const first = props.full ? undefined : focusables(el).find((f) => f.closest(".modal-body") && f.matches(TEXT_FIELD));
      (first ?? el).focus({ preventScroll: true });
    }, 40);
    return () => clearTimeout(tm);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const onTab = (e: React.KeyboardEvent) => {
    if (e.key !== "Tab" || !box.current) return;
    const items = focusables(box.current);
    if (!items.length) { e.preventDefault(); return; }
    const cur = document.activeElement as HTMLElement | null;
    const i = cur ? items.indexOf(cur) : -1;
    const next = e.shiftKey ? (i <= 0 ? items[items.length - 1] : items[i - 1]) : (i < 0 || i >= items.length - 1 ? items[0] : items[i + 1]);
    e.preventDefault();
    e.stopPropagation();          // ichma-ich oynada tashqi oyna qayta ishlamasin
    next.focus();
  };
  return (
    <div className="modal-back" onMouseDown={(e) => { if (e.target === e.currentTarget) props.onClose(); }}>
      <div className={cx("modal", props.full && "modal-full")} style={{ width: props.width, height: props.height }}
        data-testid={props.testid} role="dialog" ref={box} tabIndex={-1} onKeyDown={onTab}>
        <div className="modal-head">
          <div className="modal-title" title={typeof props.title === "string" ? props.title : undefined}>{props.title}</div>
          <div className="modal-head-right">{props.headerRight}</div>
          <button type="button" className="ibtn" onClick={props.onClose} aria-label={i18n.t("app.close")}><X size={16} /></button>
        </div>
        <div className="modal-body">{props.children}</div>
        {props.footer && <div className="modal-foot">{props.footer}</div>}
      </div>
    </div>
  );
}

const TEXT_FIELD = "input:not([type=checkbox]):not([type=radio]):not([type=color]):not([type=file]):not([readonly]), textarea:not([readonly])";
const FOCUSABLE = "input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), a[href], [tabindex]:not([tabindex='-1'])";

/** Oyna ichidagi (ichma-ich oynalarsiz) ko'rinadigan fokuslanuvchi elementlar — Tab aylanishi uchun. */
function focusables(root: HTMLElement): HTMLElement[] {
  return Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE)).filter((e) =>
    e.closest(".modal") === root && e.getAttribute("tabindex") !== "-1" && e.offsetParent !== null);
}

/** Yuqori jadval / pastki panel orasidagi sudraladigan chegara. */
export function Splitter(props: { value: number; onChange: (v: number) => void; min?: number; max?: number }) {
  const start = useRef<{ y: number; v: number } | null>(null);
  useEffect(() => {
    const move = (e: MouseEvent) => {
      if (!start.current) return;
      const v = start.current.v + (e.clientY - start.current.y) / uiZoom();   // ekran px → #root px
      props.onChange(Math.max(props.min ?? 80, Math.min(props.max ?? layoutHeight() - 200, v)));
    };
    const up = () => { start.current = null; document.body.classList.remove("resizing"); };
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
    return () => { window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up); };
  }, [props]);
  return (
    <div className="splitter" onMouseDown={(e) => {
      start.current = { y: e.clientY, v: props.value };
      document.body.classList.add("resizing");
      e.preventDefault();
    }} />
  );
}

/** Ochiladigan menyu (toolbar tugmasi ostida). */
export function Dropdown(props: { icon: LucideIcon; title: string; items: { label: ReactNode; onClick: () => void;
  disabled?: boolean; testid?: string }[]; label?: string; testid?: string; disabled?: boolean }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    window.addEventListener("mousedown", h);
    return () => window.removeEventListener("mousedown", h);
  }, [open]);
  const Icon = props.icon;
  return (
    <div className="dd" ref={ref}>
      <button type="button" className={cx("ibtn", props.label && "ibtn-label", open && "ibtn-active")} title={fmtTitle(props.title)}
        onClick={() => setOpen(!open)} data-testid={props.testid} disabled={props.disabled}>
        <Icon size={16} />{props.label && <span>{props.label}</span>}
      </button>
      {open && (
        <div className="dd-menu">
          {props.items.map((it, i) => (
            <button key={i} type="button" className="dd-item" disabled={it.disabled} data-testid={it.testid}
              onClick={() => { setOpen(false); it.onClick(); }}>{it.label}</button>
          ))}
        </div>
      )}
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>;
}

export function Busy({ text }: { text: ReactNode }) {
  return (
    <div className="busy">
      <div className="spinner" />
      <div>{text}</div>
    </div>
  );
}

export function fmt(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "";
  const r = Math.round(v * 10 ** digits) / 10 ** digits;
  return String(r);
}

/** Pul — hamma joyda bitta ko'rinish: 2 kasr, minglik ajratuvchi — bo'sh joy, kasr — nuqta («64 820.00»):
 *  «Изделия» / «Операции» jadvallari, SP/EL/CS/O panellari, «Заказать», loyihalar ro'yxati. */
/** Pul: bo'sh joy bilan minglik, nuqta, ortiqcha nollarsiz (onlayn tizimdagidek: «0», «4 148.5», «64 820»). */
export function money(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "";
  return v.toLocaleString("ru-RU", { minimumFractionDigits: 0, maximumFractionDigits: 2 }).replace(/\s/g, " ").replace(",", ".");
}

/** Pul — doim 2 xona («0.00»): «Изделия» jadvali (onlayn tizimdagidek). */
export function money2(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "";
  return v.toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).replace(/\s/g, " ").replace(",", ".");
}
