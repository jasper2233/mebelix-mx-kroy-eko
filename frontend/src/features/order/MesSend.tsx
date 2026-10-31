// «Отправить в MES»: kroy tugagach paket MES buyurtmasiga ketadi va texnolog o'z MES oynasiga — shu buyurtmaga — qaytadi.
// MES dan ochilgan loyihada buyurtma ma'lum; MX da ochilganida avval uzatilmagan buyurtmalar ro'yxatidan tanlanadi. Ikkala
// holatda ham yuborishdan oldin tasdiq: buyurtma va mijoz MES dan, mos kelmasa ogohlantirish — kroy boshqa buyurtmaga ketmasin.
// MX oynasini MES ochgan bo'lsa (`window.opener`): MES xabarni oladi, buyurtmani ochadi va bu oynani yopadi — brauzer o'zini
// ochgan tabga qaytadi (Chrome boshqa tabga fokusni dasturdan bermaydi). MES oynasi yopilgan yoki MX to'g'ridan-to'g'ri
// ochilgan bo'lsa — shu oynaning o'zi MES buyurtmasiga o'tadi (`QAYTISH_MS` kutib).
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Send, TriangleAlert } from "lucide-react";
import { get, post } from "../../api/client";
import { applyProject } from "../../api/hooks";
import type { Project } from "../../api/types";
import { askConfirm, showError } from "../../shared/dialogs";
import { Btn, Modal, cx } from "../../shared/ui";
import { fmtDate, fmtDateTime } from "./orderApi";

interface SendResult {
  order_id: number; order_number: string; redirect_url: string; version: number; message?: string; warnings?: string[];
  mes_url: string; project: Project;
}

interface MesOrder {
  id: number; number: string; nom: string; mijoz: string; muddat: string | null; kroy_bor: boolean; versiya: number | null;
  mx_loyiha: string | null; mx_raqam: string | null;
}

interface MesCheck {
  buyurtma: MesOrder; mahsulotlar: string[]; turlar: number; nusxalar: number; listlar: number; avvalgi: string | null;
  ogoh: string[];
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

function SendDialog({ project, onClose }: { project: Project; onClose: () => void }) {
  const { t } = useTranslation();
  const bound = !!project.mes_order_ref;
  const [q, setQ] = useState("");
  const [orders, setOrders] = useState<MesOrder[] | null>(null);
  const [tanlangan, setTanlangan] = useState<MesOrder | null>(null);
  const [tekshir, setTekshir] = useState<MesCheck | null>(null);
  const [xato, setXato] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const xabar = (e: unknown) => setXato(e instanceof Error ? e.message : String(e));

  const korish = async (o: MesOrder | null) => {
    setBusy(true); setXato(null);
    try {
      setTekshir(await post<MesCheck>(`/projects/${project.id}/mes-check`,
        o ? { order_id: o.id, order_number: o.number } : {}));
      setTanlangan(o);
    } catch (e) {
      xabar(e);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {                                       // bog'langan loyiha: to'g'ridan-to'g'ri tasdiqqa
    if (bound) void korish(null);
  }, []);                                                 // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {                                       // ro'yxat: qidiruv yozilganda kechikish bilan
    if (bound) return;
    const h = window.setTimeout(() => {
      get<MesOrder[]>(`/projects/${project.id}/mes-orders`, { q }).then(setOrders).catch(xabar);
    }, q ? 250 : 0);
    return () => window.clearTimeout(h);
  }, [q, bound, project.id]);

  const yubor = async () => {
    setBusy(true); setXato(null);
    try {
      const r = await post<SendResult>(`/projects/${project.id}/mes-send`,
        tanlangan ? { order_id: tanlangan.id, order_number: tanlangan.number } : {});
      applyProject(r.project);
      backToMes(r);
    } catch (e) {
      xabar(e);
      setBusy(false);
    }
  };

  const footer = tekshir ? <>
    <Btn kind="primary" label={busy ? t("mes.sending") : t("mes.send_ok")} disabled={busy} onClick={() => void yubor()} testid="mes-send-ok" />
    {!bound && <Btn label={t("mes.back")} disabled={busy} onClick={() => { setTekshir(null); setXato(null); }} testid="mes-back" />}
    <Btn label={t("app.cancel")} disabled={busy} onClick={onClose} testid="mes-cancel" />
  </> : <Btn label={t("app.cancel")} onClick={onClose} testid="mes-cancel" />;

  return (
    <Modal title={<span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}><Send size={15} /> {t("mes.send")}</span>}
      onClose={onClose} width={760} testid="mes-send-dialog" footer={footer}>
      <div className="mes-dlg">
        {xato && <div className="mes-xato" data-testid="mes-error"><TriangleAlert size={14} /> {xato}</div>}
        {!tekshir && !bound && <>
          <div className="mes-sar">{t("mes.pick")}</div>
          <input className="mes-qidir" autoFocus value={q} placeholder={t("mes.search")} data-testid="mes-search"
            onChange={(e) => setQ(e.target.value)} />
          <div className="mes-royxat">
            <table className="mes-jadval">
              <thead><tr><th>{t("mes.col.order")}</th><th>{t("mes.col.client")}</th><th>{t("mes.col.name")}</th><th>{t("mes.col.deadline")}</th><th>{t("mes.col.cut")}</th></tr></thead>
              <tbody>
                {(orders ?? []).map((o) => (
                  <tr key={o.id} className={cx(busy && "off")} data-testid={`mes-order-${o.number}`} onClick={() => !busy && void korish(o)}>
                    <td className="mes-raqam">{o.number}</td>
                    <td>{o.mijoz}</td>
                    <td>{o.nom || "—"}</td>
                    <td>{o.muddat ? fmtDate(o.muddat) : "—"}</td>
                    <td className={o.kroy_bor ? "mes-bor" : ""}>{o.kroy_bor ? (o.versiya ? t("mes.cut_version", { v: o.versiya }) : t("mes.cut_file")) : t("mes.cut_none")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {orders?.length === 0 && <div className="mes-bosh">{t("mes.no_orders")}</div>}
          </div>
        </>}
        {!tekshir && bound && !xato && <div className="mes-bosh">{t("mes.checking")}</div>}
        {tekshir && <>
          <div className="mes-sar">{t("mes.confirm_q")}</div>
          <table className="mes-kv" data-testid="mes-confirm">
            <tbody>
              <tr><td>{t("mes.col.order")}</td><td className="mes-katta">{tekshir.buyurtma.number}</td></tr>
              <tr><td>{t("mes.col.client")}</td><td className="mes-katta">{tekshir.buyurtma.mijoz}</td></tr>
              {tekshir.buyurtma.nom && <tr><td>{t("mes.col.name")}</td><td>{tekshir.buyurtma.nom}</td></tr>}
              <tr><td>{t("mes.project")}</td><td>№ {project.number} · {project.name}</td></tr>
              <tr><td>{t("mes.content")}</td><td>{t("mes.content_val", { p: tekshir.mahsulotlar.join(", ") || "—", d: tekshir.turlar, n: tekshir.nusxalar, s: tekshir.listlar })}</td></tr>
            </tbody>
          </table>
          {tekshir.ogoh.length > 0 && (
            <div className="mes-ogoh" data-testid="mes-warnings">
              {tekshir.ogoh.map((w) => <div key={w}><TriangleAlert size={14} /> {w}</div>)}
            </div>
          )}
        </>}
      </div>
    </Modal>
  );
}

export function MesSend({ project }: { project: Project }) {
  const { t } = useTranslation();
  const [dlg, setDlg] = useState(false);
  const sent = project.mes_sent;

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
      <button type="button" className="mes-send" onClick={() => setDlg(true)} data-testid="mes-send">
        <Send size={14} /> {t("mes.send")}
      </button>
      {dlg && <SendDialog project={project} onClose={() => setDlg(false)} />}
    </div>
  );
}
