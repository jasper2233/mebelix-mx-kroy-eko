// Tasdiqlash / matn so'rash oynalari (Promise asosida) va xabarnomalar.
import { useEffect, useRef, useState, type ReactNode } from "react";
import { create } from "zustand";
import { useTranslation } from "react-i18next";
import { TriangleAlert, CircleCheck, CircleX, Info, X } from "lucide-react";
import i18n from "i18next";
import { Btn, Modal } from "./ui";
import { useUI } from "../store/ui";
import { ApiError, statusText } from "../api/client";
import { useHotkeys } from "./hotkeys";

interface Ask {
  kind: "confirm" | "prompt";
  title: ReactNode;
  text?: ReactNode;
  value?: string;
  ok?: string;
  danger?: boolean;
  multiline?: boolean;
  resolve: (v: string | boolean | null) => void;
}

const useAsk = create<{ ask: Ask | null; set: (a: Ask | null) => void }>((set) => ({ ask: null, set: (a) => set({ ask: a }) }));

export function askConfirm(title: ReactNode, text?: ReactNode, opts: { ok?: string; danger?: boolean } = {}): Promise<boolean> {
  return new Promise((resolve) => useAsk.getState().set({ kind: "confirm", title, text, ...opts,
    resolve: (v) => resolve(Boolean(v)) }));
}

export function askText(title: ReactNode, value = "", opts: { text?: ReactNode; ok?: string; multiline?: boolean } = {}):
  Promise<string | null> {
  return new Promise((resolve) => useAsk.getState().set({ kind: "prompt", title, value, ...opts,
    resolve: (v) => resolve(v === null ? null : String(v)) }));
}

export function DialogHost() {
  const { t } = useTranslation();
  const ask = useAsk((s) => s.ask);
  const set = useAsk((s) => s.set);
  const [val, setVal] = useState("");
  const inp = useRef<HTMLInputElement & HTMLTextAreaElement>(null);
  useEffect(() => {
    if (ask?.kind === "prompt") {
      setVal(ask.value ?? "");
      setTimeout(() => { inp.current?.focus(); inp.current?.select(); }, 30);
    } else if (ask?.kind === "confirm") {       // fokus tasdiqlash tugmasida: Enter tasdiqlaydi, Tab modal ichida qoladi
      setTimeout(() => document.querySelector<HTMLButtonElement>('[data-testid="ask-ok"]')?.focus(), 30);
    }
  }, [ask]);
  useHotkeys("ask", {
    enter: () => { const a = useAsk.getState().ask; if (a?.kind === "confirm") { set(null); a.resolve(true); } },
  }, ask?.kind === "confirm");
  if (!ask) return null;
  const done = (v: string | boolean | null) => { set(null); ask.resolve(v); };
  return (
    <Modal title={ask.title} onClose={() => done(ask.kind === "confirm" ? false : null)} width={440} scope="ask"
      testid="ask-dialog"
      footer={<>
        <Btn kind={ask.danger ? "danger" : "primary"} label={ask.ok ?? t("app.ok")} testid="ask-ok"
          onClick={() => done(ask.kind === "confirm" ? true : val)} />
        <Btn label={t("app.cancel")} onClick={() => done(ask.kind === "confirm" ? false : null)} />
      </>}>
      {ask.text && <div className="ask-text">{ask.text}</div>}
      {ask.kind === "prompt" && (ask.multiline
        ? <textarea ref={inp} className="inp area" rows={4} value={val} data-testid="ask-input" onChange={(e) => setVal(e.target.value)} />
        : <input ref={inp} className="inp" style={{ width: "100%" }} value={val} data-testid="ask-input"
            onChange={(e) => setVal(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") done(val); }} />)}
    </Modal>
  );
}

export function Toasts() {
  const { t: tr } = useTranslation();
  const toasts = useUI((s) => s.toasts);
  const drop = useUI((s) => s.dropToast);
  const hold = useUI((s) => s.holdToast);
  return (
    <div className="toasts" aria-live="polite">
      {toasts.map((t) => {
        const det = t.details ?? [];
        // tafsilotlar: matnni takrorlamaydigan qatorlar (ko'pi bilan 5, qolgani «+N»)
        const all = det.filter((d) => d && d !== t.text);
        const shown = all.slice(0, 5);
        return (
          <div key={t.id} className={`toast toast-${t.kind}`} data-testid={`toast-${t.kind}`}
            role={t.kind === "error" || t.kind === "warn" ? "alert" : "status"}
            onMouseEnter={() => hold(t.id, true)} onMouseLeave={() => hold(t.id, false)}>
            {t.kind === "error" ? <CircleX size={16} className="toast-ico" />
              : t.kind === "warn" ? <TriangleAlert size={16} className="toast-ico" />
              : t.kind === "ok" ? <CircleCheck size={16} className="toast-ico" /> : <Info size={16} className="toast-ico" />}
            <div className="toast-text">
              {t.title && <div className="toast-title" data-testid="toast-title">{t.title}</div>}
              <div className="toast-msg">{t.text}{(t.count ?? 1) > 1 && <span className="toast-count"> ×{t.count}</span>}</div>
              {shown.length > 0 && (
                <ul>
                  {shown.map((d, i) => <li key={i}>{d}</li>)}
                  {all.length > shown.length && <li className="muted">{tr("app.more_n", { n: all.length - shown.length })}</li>}
                </ul>
              )}
              {t.action && (
                <div className="toast-actions">
                  <Btn small kind="primary" label={t.action.label} testid={t.action.testid ?? "toast-action"}
                    onClick={() => { const a = t.action!; drop(t.id); a.run(); }} />
                </div>
              )}
            </div>
            <button type="button" className="ibtn" aria-label={tr("app.close")} title={tr("app.close")} onClick={() => drop(t.id)}><X size={14} /></button>
          </div>
        );
      })}
    </div>
  );
}

/** Xatoni foydalanuvchiga ko'rsatish. Server xatosi — o'z matni (tilga mos), brauzer / tarmoq xatosi — umumiy tushunarli xabar. */
export function showError(e: unknown) {
  const ui = useUI.getState();
  // sarlavha «Ошибка» (qizil, qalin) — server 4xx (masalan «Нет листов для раскроя») va boshqa xatolar bir xil ko'rinishda
  const x = { title: i18n.t("app.error_title") };
  if (e instanceof ApiError) ui.toast(e.message || statusText(e.status), "error", e.details, x);
  else if (e instanceof TypeError && /fetch|network/i.test(e.message)) ui.toast(statusText(0), "error", undefined, x);
  else if (e instanceof Error) ui.toast(e.message || i18n.t("err.unknown"), "error", undefined, x);
  else ui.toast(String(e ?? "") || i18n.t("err.unknown"), "error", undefined, x);
}
