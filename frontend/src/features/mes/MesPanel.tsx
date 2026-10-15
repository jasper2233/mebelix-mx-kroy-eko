// «MES» bo'limi (chap panel): MES integratsiya paneli karkasi. Qator «Настройки → MES интеграция» da yoqilmaguncha xira
// (bosilmaydi). Haqiqiy MES bilan ulanishni korxona MES jamoasi qo'shadi — shu sababli bu yerdagi amallar hozircha o'chirilgan
// (disabled) va faqat qaysi funksiyalar bo'lishini ko'rsatadi; ishlayotgan qism — «Связь и API» (qabul qilish endpointlari, webhook).
import { create } from "zustand";
import { useTranslation } from "react-i18next";
import { ArrowDownToLine, ArrowUpFromLine, ClipboardList, Gauge, Plug, RefreshCw, ScrollText, Warehouse } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Btn, cx } from "../../shared/ui";
import { MesApiDoc } from "../settings/Settings";
import { OeeView } from "../oee/OeeView";

export type MesPage = "overview" | "orders" | "results" | "stock" | "oee" | "log" | "api";
export const MES_PAGES: { key: MesPage; icon: LucideIcon }[] = [
  { key: "overview", icon: Plug }, { key: "orders", icon: ArrowDownToLine }, { key: "results", icon: ArrowUpFromLine },
  { key: "stock", icon: Warehouse }, { key: "oee", icon: Gauge }, { key: "log", icon: ScrollText }, { key: "api", icon: ClipboardList },
];
const useMesPage = create<{ page: MesPage; set: (p: MesPage) => void }>((set) => ({ page: "overview", set: (page) => set({ page }) }));

export function MesMenu() {
  const { t } = useTranslation();
  const { page, set } = useMesPage();
  return (
    <div className="side-menu">
      {MES_PAGES.map(({ key, icon: Icon }) => (
        <button key={key} type="button" className={cx("side-item", page === key && "side-item-active")} onClick={() => set(key)}
          data-testid={`mes-${key}`}><Icon size={14} /> {t(`mes.page.${key}`)}</button>
      ))}
    </div>
  );
}

// Karkas sahifa: sarlavha, qisqa tavsif, rejalashtirilgan amallar (o'chirilgan) va bo'sh jadval.
function Stub(props: { page: Exclude<MesPage, "api" | "overview" | "oee">; actions: string[]; columns: string[] }) {
  const { t } = useTranslation();
  const k = props.page;
  return (
    <div className="page" data-testid={`mes-view-${k}`}>
      <div className="page-head"><h2>{t(`mes.page.${k}`)}</h2>
        {props.actions.map((a) => <Btn key={a} icon={RefreshCw} label={t(`mes.act.${a}`)} disabled />)}
      </div>
      <div className="scroll doc">
        <p>{t(`mes.stub.${k}`)}</p>
        <table className="simple">
          <thead><tr>{props.columns.map((c) => <th key={c}>{t(`mes.col.${c}`)}</th>)}</tr></thead>
          <tbody><tr><td colSpan={props.columns.length} className="muted">{t("mes.stub.empty")}</td></tr></tbody>
        </table>
        <p className="muted">{t("mes.stub.note")}</p>
      </div>
    </div>
  );
}

function Overview() {
  const { t } = useTranslation();
  return (
    <div className="page" data-testid="mes-view-overview">
      <div className="page-head"><h2>{t("mes.page.overview")}</h2></div>
      <div className="scroll doc">
        <table className="simple">
          <tbody>
            <tr><td>{t("mes.ov.state")}</td><td><span className="warn">{t("mes.ov.state_stub")}</span></td></tr>
            <tr><td>{t("mes.ov.rest")}</td><td>{t("mes.ov.rest_v")}</td></tr>
            <tr><td>{t("mes.ov.gibsaw")}</td><td>{t("mes.ov.gibsaw_v")}</td></tr>
          </tbody>
        </table>
        <p>{t("mes.ov.plan")}</p>
        <ul>{(["orders", "results", "stock", "log"] as const).map((k) => <li key={k}><b>{t(`mes.page.${k}`)}</b> — {t(`mes.stub.${k}`)}</li>)}</ul>
        <p className="muted">{t("mes.stub.note")}</p>
      </div>
    </div>
  );
}

export function MesView() {
  const { t } = useTranslation();
  const page = useMesPage((s) => s.page);
  if (page === "orders") return <Stub page="orders" actions={["fetch", "create_project"]} columns={["ref", "project", "status", "date", "received"]} />;
  if (page === "results") return <Stub page="results" actions={["send", "retry"]} columns={["project", "operation", "maps", "status", "sent"]} />;
  if (page === "stock") return <Stub page="stock" actions={["sync_remnants", "sync_catalog"]} columns={["material", "qty", "mes_qty", "diff"]} />;
  if (page === "log") return <Stub page="log" actions={["refresh"]} columns={["time", "direction", "event", "ref", "status"]} />;
  if (page === "oee") return <OeeView />;       // W17: OEE va ishlab chiqarish analitikasi (to'liq ishlaydi)
  if (page === "api") {
    return (
      <div className="page" data-testid="mes-view-api">
        <div className="page-head"><h2>{t("mes.page.api")}</h2></div>
        <div className="scroll doc"><MesApiDoc /></div>
      </div>
    );
  }
  return <Overview />;
}
