// «Очередь заказов» (2026-10-15, foydalanuvchi talabi): loyihalar kelish tartibida, har biri uchun material bazasi tekshiruvi
// (kerak / bazada / yetmaydi); birinchi «material to'liq bor» loyiha — navbatdagi; yetmaganlar uchun «bazani to'ldiring» ogohlantirishi.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { CircleAlert, CircleCheck, CircleHelp, RefreshCw } from "lucide-react";
import { qc } from "../../api/hooks";
import type { MaterialCheck } from "../../api/types";
import { useUI } from "../../store/ui";
import { Btn, IconBtn, Modal, Sel, cx, fmt } from "../../shared/ui";
import { StatusBadge } from "../order/StatusBadge";
import { useQueue } from "../order/materialApi";

const STATUS_SETS: Array<{ value: string; key: string }> = [
  { value: "0,1,2", key: "queue.set.open" }, { value: "1,2", key: "queue.set.ordered" }, { value: "0", key: "queue.set.draft" }, { value: "0,1,2,3", key: "queue.set.all" },
];

export function materialSummary(r: MaterialCheck, t: (k: string, o?: Record<string, unknown>) => string): string {
  if (!r.items.length) return t("queue.no_cut_ops");
  if (r.ok) return t("queue.ok");
  const short = r.items.filter((i) => i.status === "short");
  const unknown = r.items.filter((i) => i.status === "unknown");
  const parts = [];
  if (short.length) parts.push(t("queue.short", { n: short.length, list: short.map((i) => `${i.name} −${fmt(i.short ?? 0, 0)}`).join(", ") }));
  if (unknown.length) parts.push(t("queue.unknown", { n: unknown.length }));
  return parts.join("; ");
}

export function QueueDialog({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const [set, setSet] = useState("0,1,2");
  const q = useQueue(set);
  const data = q.data;
  const open = (id: string) => { onClose(); useUI.getState().openProject(id); };
  return (
    <Modal title={t("queue.title")} onClose={onClose} width={980} height={560} testid="queue-dialog"
      footer={<>
        <Sel<string> value={set} width={200} options={STATUS_SETS.map((s) => ({ value: s.value, label: t(s.key) }))} onChange={setSet} />
        <IconBtn icon={RefreshCw} title={t("menu.refresh")} onClick={() => void qc.invalidateQueries({ queryKey: ["queue"] })} />
        <span className="grow" />
        {data?.next && <Btn kind="primary" label={t("queue.open_next", { n: data.next.number })} onClick={() => open(data.next!.project_id)} testid="queue-open-next" />}
        <Btn label={t("app.close")} onClick={onClose} />
      </>}>
      {q.isLoading && <p className="muted">{t("app.loading")}</p>}
      {data && (
        <div className="queue">
          <p className={cx("queue-msg", data.next ? "ok" : "warn")} data-testid="queue-message">
            {data.next ? <CircleCheck size={15} /> : <CircleAlert size={15} />} {data.message}
          </p>
          <table className="tbl queue-tbl" data-testid="queue-table">
            <thead><tr>
              <th>№</th><th>{t("projects.col.id")}</th><th>{t("projects.col.name")}</th><th>{t("projects.col.status")}</th>
              <th>{t("queue.col.material")}</th><th>{t("queue.col.result")}</th><th></th>
            </tr></thead>
            <tbody>
              {data.rows.map((r) => (
                <tr key={r.project_id} className={cx(r.next && "queue-next", !r.ok && r.known && "queue-short")} data-testid={`queue-row-${r.number}`}>
                  <td className="num">{r.position}</td>
                  <td className="num">{r.number}</td>
                  <td>{r.name}</td>
                  <td><StatusBadge status={r.status} /></td>
                  <td className="queue-mats">
                    {r.items.map((i) => (
                      <div key={i.op_id} className={cx("queue-mat", i.status)} title={`${i.name}${i.thickness ? ` ${fmt(i.thickness, 1)} ${t("u.mm")}` : ""}`}>
                        {i.status === "ok" ? <CircleCheck size={12} /> : i.status === "short" ? <CircleAlert size={12} /> : <CircleHelp size={12} />}
                        {" "}{i.name}: {t("queue.need")} {i.estimated ? "≈ " : ""}{fmt(i.need, 0)}, {t("queue.have")} {i.have === null ? "?" : fmt(i.have, 0)}
                        {i.remnants ? ` (+${i.remnants} ${t("queue.remnants")})` : ""}
                      </div>
                    ))}
                    {!r.items.length && <span className="muted">{t("queue.no_cut_ops")}</span>}
                  </td>
                  <td className={cx("queue-res", r.ok ? "ok" : r.known ? "short" : "unknown")}>{materialSummary(r, t)}{r.next ? ` — ${t("queue.is_next")}` : ""}</td>
                  <td><button type="button" className="link" onClick={() => open(r.project_id)}>{t("menu.open")}</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.warnings.length > 0 && (
            <div className="queue-warn" data-testid="queue-warnings">
              <b>{t("queue.fill_base")}</b>
              <ul>{data.warnings.slice(0, 30).map((w, i) => <li key={i}>{w}</li>)}</ul>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}
