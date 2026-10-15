// Tasdiqlash / matn so'rash oynalari (Promise asosida) va xabarnomalar.
import { useEffect, useRef, useState, type ReactNode } from "react";
import { create } from "zustand";
import { useTranslation } from "react-i18next";
import { TriangleAlert, CircleCheck, Info, X } from "lucide-react";
import { Btn, Modal } from "./ui";
import { useUI } from "../store/ui";
import { ApiError } from "../api/client";
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
  const toasts = useUI((s) => s.toasts);
  const drop = useUI((s) => s.dropToast);
  return (
    <div className="toasts">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.kind}`} data-testid={`toast-${t.kind}`}>
          {t.kind === "error" ? <TriangleAlert size={16} /> : t.kind === "ok" ? <CircleCheck size={16} /> : <Info size={16} />}
          <div className="toast-text">
            {t.text}
            {t.details && t.details.length > 1 && (
              <ul>{t.details.slice(0, 5).map((d, i) => <li key={i}>{d}</li>)}</ul>
            )}
          </div>
          <button type="button" className="ibtn" onClick={() => drop(t.id)}><X size={14} /></button>
        </div>
      ))}
    </div>
  );
}

/** Xatoni foydalanuvchiga ko'rsatish. */
export function showError(e: unknown) {
  const ui = useUI.getState();
  if (e instanceof ApiError) ui.toast(e.message, "error", e.details);
  else if (e instanceof Error) ui.toast(e.message, "error");
  else ui.toast(String(e), "error");
}
