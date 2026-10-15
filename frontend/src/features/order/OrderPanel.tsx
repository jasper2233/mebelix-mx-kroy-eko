// Chap «Проект» menyusidagi «Заказать» bloki (ORD-003): holat belgisi, tayyorlik sanasi, navbatdagi qadam tugmasi
// («Заказать» → «Утвердить» → «Готов»), «Состояние заказа…» (tarix va boshqa o'tishlar), narxlar.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ShoppingCart } from "lucide-react";
import type { OrderStatus, Project } from "../../api/types";
import { Btn, money } from "../../shared/ui";
import { OrderDialog } from "./OrderDialog";
import { StatusBadge } from "./StatusBadge";
import { fmtDate, nextStatus, useOrderState } from "./orderApi";
import { useMaterialCheck } from "./materialApi";
import "./order.css";

export function OrderPanel({ project }: { project: Project }) {
  const { t } = useTranslation();
  const st = useOrderState(project).data;
  const [dlg, setDlg] = useState<OrderStatus | null>(null);
  const cost_m = project.operations.reduce((s, o) => s + o.cost_material, 0);
  const cost_o = project.operations.reduce((s, o) => s + o.cost_operation, 0);
  const next = nextStatus(project.status);
  const canChange = st?.can_change ?? true;
  // oxirgi holatda («Готов») asosiy tugma yo'q; «Состояние…» oynasi oldingi holatni taklif qiladi
  const manageTarget: OrderStatus = next ?? ((project.status - 1) as OrderStatus);
  const showReady = project.status >= 2 || !!st?.ready_set;
  // Material bazasi (2026-10-15): kroy operatsiyalari uchun bazada list yetarlimi — ✓ / yetmaydi / noma'lum (katalogda yo'q)
  const mat = useMaterialCheck(project, project.operations.some((o) => (o.type === "CS" || o.type === "CL" || o.type === "CN") && o.parts.length > 0)).data;
  const matText = !mat || !mat.items.length ? "" : mat.ok ? t("queue.ok")
    : mat.known ? t("queue.short", { n: mat.items.filter((i) => i.status === "short").length,
      list: mat.items.filter((i) => i.status === "short").map((i) => `${i.name} −${Math.ceil(i.short ?? 0)}`).join(", ") })
      : t("queue.unknown", { n: mat.items.filter((i) => i.status === "unknown").length });
  return (
    <div className="side-order" data-testid="side-order">
      <div className="side-order-title"><ShoppingCart size={14} /> {t("menu.order")}</div>
      <div className="ord-state">
        <StatusBadge status={project.status} testid="order-status-badge" />
      </div>
      {showReady && (
        <div className="ord-ready"><span>{t("order.ready_date")}</span><b data-testid="order-ready-value">{fmtDate(project.ready_date)}</b></div>
      )}
      {next !== null && (
        <div className="ord-act">
          <Btn kind={next === 1 ? "primary" : "default"} label={t(`order.action.${next}`)} disabled={!canChange}
            onClick={() => setDlg(next)} testid="order-btn" />
        </div>
      )}
      <button type="button" className="ord-link" onClick={() => setDlg(manageTarget)} data-testid="order-manage">
        {t("order.manage")}
      </button>
      <table className="mini">
        <tbody>
          <tr><td>{t("menu.order_id")}</td><td>{project.number}</td></tr>
          <tr><td>{t("menu.cost")}</td><td>{money(cost_m + cost_o)} {project.currency}</td></tr>
          <tr><td>{t("menu.cost_mat")}</td><td>{money(cost_m)} {project.currency}</td></tr>
          <tr><td>{t("menu.cost_op")}</td><td>{money(cost_o)} {project.currency}</td></tr>
          {project.mes_order_ref && <tr><td>MES</td><td>{project.mes_order_ref}</td></tr>}
          {matText && <tr className={mat?.ok ? "ord-mat ok" : mat?.known ? "ord-mat short" : "ord-mat unknown"} title={mat?.warnings.join("\n")}
            data-testid="order-material"><td>{t("queue.col.material")}</td><td>{matText}</td></tr>}
        </tbody>
      </table>
      {dlg !== null && <OrderDialog project={project} target={dlg} onClose={() => setDlg(null)} />}
    </div>
  );
}
