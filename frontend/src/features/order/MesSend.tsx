// «Отправить в MES»: kroy tugagach paket MES buyurtmasiga ketadi va texnolog o'z MES oynasiga — shu buyurtmaga — qaytadi.
// MX oynasini MES ochgan (`window.opener`): MES xabarni oladi, buyurtmani ochadi va bu oynani yopadi — brauzer o'zini ochgan tabga
// qaytadi (Chrome boshqa tabga fokusni dasturdan bermaydi, `focus()` faqat ruxsat bergan brauzerlarda ishlaydi). MES oynasi
// yopilgan yoki MX to'g'ridan-to'g'ri ochilgan bo'lsa — shu oynaning o'zi MES buyurtmasiga o'tadi (`QAYTISH_MS` kutib).
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Send } from "lucide-react";
import { post } from "../../api/client";
import { applyProject } from "../../api/hooks";
import type { Project } from "../../api/types";
import { askConfirm, showError } from "../../shared/dialogs";
import { fmtDateTime } from "./orderApi";

interface SendResult {
  order_id: number; order_number: string; redirect_url: string; version: number; message?: string; warnings?: string[];
  mes_url: string; project: Project;
}

const QAYTISH_MS = 1500;

function backToMes(r: SendResult) {
  const mes = window.opener as Window | null;
  if (mes && !mes.closed) {
    mes.focus();
    mes.postMessage({ type: "mx-kroy-yuborildi", order_id: r.order_id, order_number: r.order_number, version: r.version,
      warnings: r.warnings ?? [] }, "*");
  }
  window.setTimeout(() => { window.location.href = r.mes_url; }, QAYTISH_MS);
}

export function MesSend({ project }: { project: Project }) {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  const sent = project.mes_sent;

  const send = async () => {
    setBusy(true);
    try {
      const r = await post<SendResult>(`/projects/${project.id}/mes-send`);
      applyProject(r.project);
      backToMes(r);
    } catch (e) {
      showError(e);
      setBusy(false);
    }
  };

  const reopen = async () => {
    if (!await askConfirm(t("mes.reopen_q"), t("mes.reopen_text"), { ok: t("mes.reopen") })) return;
    try {
      applyProject(await post<Project>(`/projects/${project.id}/mes-reopen`));
    } catch (e) {
      showError(e);
    }
  };

  if (sent) {
    return (
      <div className="side-mes" data-testid="mes-sent">
        <span className="mes-sent-info" title={`${sent.by} · ${fmtDateTime(sent.at)}`}>{t("mes.sent", { v: sent.version })}</span>
        <button type="button" className="mes-reopen" onClick={() => void reopen()} data-testid="mes-reopen">{t("mes.reopen")}</button>
      </div>
    );
  }
  return (
    <div className="side-mes">
      <button type="button" className="mes-send" disabled={busy} onClick={() => void send()} data-testid="mes-send">
        <Send size={14} /> {busy ? t("mes.sending") : t("mes.send")}
      </button>
    </div>
  );
}
