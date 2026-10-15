// Umumiy interfeys elementlari (MebeliX uslubi).
import { useEffect, useRef, useState, type ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { X } from "lucide-react";
import { useModalScope, useHotkeys } from "./hotkeys";
import { setFocusedParam, useParamHelp } from "./paramHelpStore";
import i18n from "../i18n";

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
      props.active && "btn-active")} title={props.title} onClick={props.onClick} disabled={props.disabled}
      data-testid={props.testid}>
      {Icon && <Icon size={props.small ? 14 : 16} strokeWidth={2} />}
      {props.label && <span>{props.label}</span>}
    </button>
  );
}

/** Toolbar ikonkasi: title — yordam matni va yorliq (masalan «Клонировать (Ctrl+K)»). */
export function IconBtn(props: { icon: LucideIcon; title: string; onClick?: () => void; disabled?: boolean;
  color?: string; active?: boolean; testid?: string; label?: string }) {
  const Icon = props.icon;
  return (
    <button type="button" className={cx("ibtn", props.active && "ibtn-active", props.label && "ibtn-label")}
      title={props.title} aria-label={props.title} onClick={props.onClick} disabled={props.disabled}
      data-testid={props.testid}>
      <Icon size={16} strokeWidth={2} color={props.disabled ? undefined : props.color} />
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
          <button key={t.key} type="button" className={cx("tab", props.value === t.key && "tab-active")}
            onClick={() => props.onChange(t.key)} data-testid={t.testid}>
            {Icon && <Icon size={14} />} {t.label}
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
    <button type="button" className="qmark" title={`${i18n.t("phelp.open")} (F1)`} aria-label={i18n.t("phelp.open")}
      data-testid={`qmark-${help}`} tabIndex={-1}
      onClick={(e) => { e.preventDefault(); e.stopPropagation(); useParamHelp.getState().open(help); }}>?</button>
  );
}

/** `help` — parametr yordami kaliti: yorliq yonida «?» va parametr fokusda bo'lganda F1 shu yordamni ochadi (CS-048). */
export function Field(props: { label: ReactNode; children: ReactNode; unit?: ReactNode; hint?: string; wide?: boolean;
  help?: string }) {
  const help = props.help;
  return (
    <label className={cx("field", props.wide && "field-wide")} title={props.hint}
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

/** Son maydoni: Enter yoki fokus yo'qolganda saqlanadi (vergul ham qabul qilinadi). */
export function Num(props: { value: number | null | undefined; onCommit: (v: number | null) => void; disabled?: boolean;
  allowEmpty?: boolean; min?: number; max?: number; width?: number; testid?: string; readOnly?: boolean }) {
  const [s, setS] = useState(props.value == null ? "" : String(props.value));
  useEffect(() => { setS(props.value == null ? "" : String(props.value)); }, [props.value]);
  const commit = () => {
    const n = parseNum(s);
    if (n === null && !props.allowEmpty) { setS(props.value == null ? "" : String(props.value)); return; }
    let v = n;
    if (v !== null && props.min !== undefined) v = Math.max(props.min, v);
    if (v !== null && props.max !== undefined) v = Math.min(props.max, v);
    if (v !== props.value) props.onCommit(v);
    else setS(v == null ? "" : String(v));
  };
  return (
    <input className="inp num" value={s} disabled={props.disabled} readOnly={props.readOnly} style={{ width: props.width }}
      onChange={(e) => setS(e.target.value)} onBlur={commit} data-testid={props.testid}
      onKeyDown={(e) => { if (e.key === "Enter") { commit(); (e.target as HTMLInputElement).select(); } }} />
  );
}

export function Txt(props: { value: string; onCommit: (v: string) => void; disabled?: boolean; placeholder?: string;
  width?: number | string; testid?: string; maxLength?: number }) {
  const [s, setS] = useState(props.value);
  useEffect(() => { setS(props.value); }, [props.value]);
  const commit = () => { if (s !== props.value) props.onCommit(s); };
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
    <select className="inp sel" value={String(props.value)} disabled={props.disabled} style={{ width: props.width }}
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
  return (
    <div className="modal-back" onMouseDown={(e) => { if (e.target === e.currentTarget) props.onClose(); }}>
      <div className={cx("modal", props.full && "modal-full")} style={{ width: props.width, height: props.height }}
        data-testid={props.testid} role="dialog">
        <div className="modal-head">
          <div className="modal-title">{props.title}</div>
          <div className="modal-head-right">{props.headerRight}</div>
          <button type="button" className="ibtn" onClick={props.onClose} aria-label={i18n.t("app.close")}><X size={16} /></button>
        </div>
        <div className="modal-body">{props.children}</div>
        {props.footer && <div className="modal-foot">{props.footer}</div>}
      </div>
    </div>
  );
}

/** Yuqori jadval / pastki panel orasidagi sudraladigan chegara. */
export function Splitter(props: { value: number; onChange: (v: number) => void; min?: number; max?: number }) {
  const start = useRef<{ y: number; v: number } | null>(null);
  useEffect(() => {
    const move = (e: MouseEvent) => {
      if (!start.current) return;
      const v = start.current.v + (e.clientY - start.current.y);
      props.onChange(Math.max(props.min ?? 80, Math.min(props.max ?? window.innerHeight - 200, v)));
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
      <button type="button" className={cx("ibtn", props.label && "ibtn-label", open && "ibtn-active")} title={props.title}
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

/** Narx doim 2 kasr bilan («0.00») — «Изделия» jadvali, xodimlar o'rgangan tizimdagidek. */
export function money2(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "";
  return v.toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).replace(/\s/g, " ").replace(",", ".");
}

export function money(v: number | null | undefined): string {
  if (v === null || v === undefined) return "";
  return v.toLocaleString("ru-RU", { maximumFractionDigits: 2 }).replace(/ /g, " ");
}
