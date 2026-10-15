// Mahsulot «Свойства» oynasi (Ctrl+Space): Общие · Данные заказа · Дополнительные параметры · Описание · Сообщения.
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Plus, X } from "lucide-react";
import { call } from "../../api/hooks";
import { patch } from "../../api/client";
import type { Product } from "../../api/types";
import { Btn, IconBtn, Modal, Tabs } from "../../shared/ui";
import { ProductProgram } from "./ProductProgram";

type Extra = { k: string; v: string }[];
type PTab = "props" | "program";
const LEVEL_MARK = { info: "ⓘ", warning: "⚠", error: "✖" } as const;

export function ProductProps({ pid, product, onClose }: { pid: string; product: Product; onClose: () => void }) {
  const { t } = useTranslation();
  const [tab, setTab] = useState<PTab>("props");
  // «Сообщения»: import / hisob xabarlari + mahsulot dasturi (Msg / Err / xatolar, W12)
  const msgs = [...(product.messages ?? []), ...(product.prog_messages ?? []).map((m) => `${LEVEL_MARK[m.level]} ${m.text}`)];
  const [f, setF] = useState({
    name: product.name, code: product.code, order_info: product.order_info ?? "", ready_date: product.ready_date ?? "",
    phone1: product.phone1 ?? "", phone2: product.phone2 ?? "", description: product.description ?? "",
  });
  const [extra, setExtra] = useState<Extra>(() => Object.entries(product.extra ?? {}).map(([k, v]) => ({ k, v })));
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF((s) => ({ ...s, [k]: e.target.value }));
  const row = (label: string, k: keyof typeof f, testid: string) => (
    <tr><th>{label}</th><td><input className="inp" style={{ width: "100%" }} value={f[k]} onChange={set(k)} data-testid={testid} /></td></tr>
  );
  const ok = async () => {
    const ex: Record<string, string> = {};
    for (const { k, v } of extra) if (k.trim()) ex[k.trim()] = v;
    const body = { ...f, name: f.name.trim() || product.name, extra: ex };
    await call(() => patch(`/projects/${pid}/products/${product.id}`, body));
    onClose();
  };
  const progErr = (product.prog_messages ?? []).filter((m) => m.level !== "info").length;
  return (
    <Modal title={t("pprops.title")} onClose={onClose} width={tab === "program" ? 1080 : 560} height={tab === "program" ? 700 : undefined}
      scope="pprops" testid="product-props"
      footer={<>
        <Btn kind="primary" label={t("app.ok")} onClick={() => void ok()} testid="pprops-ok" />
        <Btn label={t("app.cancel")} onClick={onClose} />
      </>}>
      <Tabs<PTab> value={tab} onChange={setTab} tabs={[
        { key: "props", label: t("pprops.tab"), testid: "pprops-tab-props" },
        { key: "program", label: <>{t("pprog.tab")}{progErr > 0 && <span className="stat warn"> ⚠ {progErr}</span>}</>, testid: "pprops-tab-program" }]} />
      {tab === "program" && <ProductProgram pid={pid} product={product} scope="pprops" />}
      {tab === "props" && <><table className="simple pprops">
        <tbody>
          <tr className="pp-group"><td colSpan={2}>{t("pprops.g.general")}</td></tr>
          {row(t("pprops.name"), "name", "pprops-name")}
          {row(t("pprops.code"), "code", "pprops-code")}
          <tr className="pp-group"><td colSpan={2}>{t("pprops.g.order")}</td></tr>
          {row(t("pprops.order_info"), "order_info", "pprops-order")}
          {row(t("pprops.ready_date"), "ready_date", "pprops-ready")}
          {row(t("pprops.phone1"), "phone1", "pprops-phone1")}
          {row(t("pprops.phone2"), "phone2", "pprops-phone2")}
          <tr className="pp-group"><td colSpan={2}>{t("pprops.g.extra")}</td></tr>
          {extra.map((e, i) => (
            <tr key={i}>
              <th><input className="inp" style={{ width: "100%" }} value={e.k} placeholder={t("pprops.key")} data-testid={`pprops-key-${i}`}
                onChange={(ev) => setExtra(extra.map((x, j) => (j === i ? { ...x, k: ev.target.value } : x)))} /></th>
              <td className="row gap">
                <input className="inp grow" value={e.v} placeholder={t("pprops.value")} data-testid={`pprops-val-${i}`}
                  onChange={(ev) => setExtra(extra.map((x, j) => (j === i ? { ...x, v: ev.target.value } : x)))} />
                <IconBtn icon={X} title={t("app.delete")} onClick={() => setExtra(extra.filter((_, j) => j !== i))} />
              </td>
            </tr>
          ))}
          <tr><td colSpan={2}><Btn icon={Plus} small kind="ghost" label={t("pprops.add_param")} testid="pprops-add"
            onClick={() => setExtra([...extra, { k: "", v: "" }])} /></td></tr>
        </tbody>
      </table>
      <div className="pp-label">{t("pprops.description")}</div>
      <textarea className="inp area" rows={3} style={{ width: "100%" }} value={f.description} onChange={set("description")} data-testid="pprops-desc" />
      <div className="pp-label">{t("pprops.messages")}</div>
      <select className="inp" style={{ width: "100%" }} data-testid="pprops-messages">
        {msgs.length === 0
          ? <option>{t("pprops.no_messages")}</option>
          : msgs.map((m, i) => <option key={i}>{m}</option>)}
      </select></>}
    </Modal>
  );
}
