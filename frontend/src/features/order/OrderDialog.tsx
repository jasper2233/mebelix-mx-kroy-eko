// «Заказать» / «Состояние заказа» oynasi (W14, ORD-005/006): maqsad holat, tayyorlik sanasi («Утвержден» da majburiy),
// ijrochi va izoh (faqat ichki matn — hech qayerga yuborilmaydi), ogohlantirishlar, holatlar tarixi.
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { ArrowRight, ShoppingCart } from "lucide-react";
import { call, qc } from "../../api/hooks";
import { post } from "../../api/client";
import type { OrderStatus, Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, Modal, cx } from "../../shared/ui";
import { StatusBadge } from "./StatusBadge";
import { fmtDate, fmtDateTime, useOrderState } from "./orderApi";
import "./order.css";

export function OrderDialog({ project, target, onClose }: { project: Project; target: OrderStatus; onClose: () => void }) {
  const { t } = useTranslation();
  const q = useOrderState(project);
  const st = q.data;
  const [to, setTo] = useState<OrderStatus>(target);
  const [executor, setExecutor] = useState("");
  const [comment, setComment] = useState("");
  const [ready, setReady] = useState<string | null>(null);          // null — tegilmagan: mavjud sana ko'rsatiladi
  const touched = useRef(false);
  const busy = useRef(false);

  useEffect(() => {                                                   // oxirgi ijrochi — taklif sifatida (bir marta)
    if (st && !touched.current && executor === "") setExecutor(st.executor);
  }, [st]);                                                           // eslint-disable-line react-hooks/exhaustive-deps

  const tr = st?.transitions.find((x) => x.to === to);
  const needsDate = to === 2;
  const readyVal = ready ?? (st?.ready_set ? st.ready_date : "");
  const dateMissing = needsDate && !readyVal;
  const canApply = !!st && !!tr && tr.allowed && !dateMissing;

  const apply = async () => {
    if (!canApply || busy.current) return;
    busy.current = true;
    const r = await call(() => post<Project>(`/projects/${project.id}/order`, {
      status: to, ready_date: needsDate ? readyVal : undefined, executor, comment,
    }));
    busy.current = false;
    if (r) {
      void qc.invalidateQueries({ queryKey: ["order", project.id] });
      useUI.getState().toast(t("order.done", { status: t(`status.${to}`) }), "ok");
      onClose();
    }
  };

  const title = target === 1 && project.status === 0 ? t("order.title_order") : t("order.title_state");
  return (
    <Modal title={<span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}><ShoppingCart size={15} /> {title}</span>}
      onClose={onClose} width={620} testid="order-dialog"
      footer={<>
        <Btn kind="primary" label={to === 1 && project.status === 0 ? t("order.action.1") : t("order.confirm")}
          disabled={!canApply} onClick={() => void apply()} testid="order-confirm" />
        <Btn label={t("app.cancel")} onClick={onClose} testid="order-cancel" />
      </>}>
      <div className="ord-dlg">
        <div className="ord-proj">№ {project.number} · {project.name}</div>
        <div className="ord-flow">
          <span className="muted">{t("order.current")}:</span> <StatusBadge status={project.status} testid="order-current" />
          <ArrowRight size={14} className="arrow" />
          <StatusBadge status={to} testid="order-target" />
        </div>

        {!st && <div className="muted">{t("app.loading")}</div>}
        {st && (
          <>
            <div className="ord-choices" role="radiogroup" aria-label={t("order.new_state")}>
              {st.transitions.map((x) => (
                <label key={x.to} className={cx("ord-choice", to === x.to && "on", !x.allowed && "off")}
                  title={x.allowed ? undefined : (x.reason ?? undefined)} data-testid={`order-choice-${x.to}`}>
                  <input type="radio" name="order-to" checked={to === x.to} disabled={!x.allowed}
                    onChange={() => setTo(x.to)} />
                  <span>{t(`status.${x.to}`)}<small>{x.kind === "back" ? t("order.kind.back") : x.kind === "skip" ? t("order.kind.skip") : t("order.kind.forward")}</small></span>
                </label>
              ))}
            </div>

            {tr && !tr.allowed && <div className="ord-err" data-testid="order-reason">{tr.reason}</div>}

            <div className="ord-form">
              {needsDate && (
                <>
                  <label htmlFor="order-ready">{t("order.ready_date")} *</label>
                  <div>
                    <input id="order-ready" type="date" className="inp" value={readyVal} data-testid="order-ready-date"
                      onChange={(e) => setReady(e.target.value)} />
                    {dateMissing && <div className="ord-hint" style={{ gridColumn: "auto", color: "var(--danger)" }}>{t("order.ready_required")}</div>}
                  </div>
                </>
              )}
              <label htmlFor="order-executor">{t("order.executor")}</label>
              <input id="order-executor" className="inp" value={executor} maxLength={200} placeholder={t("order.executor_ph")}
                data-testid="order-executor" onChange={(e) => { touched.current = true; setExecutor(e.target.value); }} />
              <label htmlFor="order-comment">{t("order.comment")}</label>
              <textarea id="order-comment" className="inp" value={comment} maxLength={1000} data-testid="order-comment"
                onChange={(e) => setComment(e.target.value)} />
              <div className="ord-hint">{t("order.internal_hint")}</div>
            </div>

            {tr && tr.allowed && tr.warnings.length > 0 && (
              <div className="ord-warns" data-testid="order-warnings">
                <b>{t("order.warnings")}</b>
                <ul>{tr.warnings.map((w) => <li key={w.code}>{w.text}</li>)}</ul>
              </div>
            )}
            {st.lock.active && <div className="ord-err">{t("order.lock_on", { status: t(`status.${project.status}`) })}</div>}

            <div>
              <div className="form-h">{t("order.history")}</div>
              {st.log.length === 0 ? <div className="muted">{t("order.history_empty")}</div> : (
                <div className="ord-hist" data-testid="order-history">
                  <table className="simple">
                    <thead><tr><th>{t("order.col.when")}</th><th>{t("order.col.user")}</th><th>{t("order.col.change")}</th><th>{t("order.col.note")}</th></tr></thead>
                    <tbody>
                      {st.log.map((e, i) => (
                        <tr key={i}>
                          <td>{fmtDateTime(e.at)}</td><td>{e.user}</td>
                          <td><StatusBadge status={e.from_status} /><span className="arrow">→</span><StatusBadge status={e.to_status} /></td>
                          <td>{[e.executor, e.comment, e.ready_date ? `${t("order.ready_date")}: ${fmtDate(e.ready_date)}` : ""].filter(Boolean).join(" · ")}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
