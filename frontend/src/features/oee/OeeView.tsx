// OEE sahifasi: «Обзор» (panel), hodisalar, stanoklar, smenalar, sabablar, parametrlar. Ikki joydan ochiladi (bir xil holat):
// chap paneldagi «MES» → «OEE» (MES integratsiyasi yoqilganda) va «Настройки → Производство» (MES o'chiq bo'lsa ham).
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { CalendarDays, Factory, Gauge, ListChecks, OctagonPause, Settings2 } from "lucide-react";
import { Tabs } from "../../shared/ui";
import { OeeDashboard } from "./OeeDashboard";
import { OeeEvents } from "./OeeEvents";
import { OeeMachines, OeeParams, OeeReasons, OeeShifts } from "./OeeSetup";
import { useOeeMachines, useOeeUI, type OeeTab } from "./oeeApi";
import "./oee.css";

export function OeeView() {
  const { t } = useTranslation();
  const tab = useOeeUI((s) => s.tab);
  const machine = useOeeUI((s) => s.machine);
  const set = useOeeUI((s) => s.set);
  const machines = useOeeMachines();
  // brauzerda eslab qolingan stanok o'chirilgan bo'lsa — «hamma stanoklar»ga qaytish
  useEffect(() => {
    if (machines.data && machine && !machines.data.some((m) => m.key === machine)) set({ machine: "" });
  }, [machines.data, machine, set]);
  const tabs: { key: OeeTab; label: string; icon: typeof Gauge }[] = [
    { key: "overview", label: t("oee.tab.overview"), icon: Gauge }, { key: "events", label: t("oee.tab.events"), icon: ListChecks },
    { key: "machines", label: t("oee.tab.machines"), icon: Factory }, { key: "shifts", label: t("oee.tab.shifts"), icon: CalendarDays },
    { key: "reasons", label: t("oee.tab.reasons"), icon: OctagonPause }, { key: "params", label: t("oee.tab.params"), icon: Settings2 },
  ];
  return (
    <div className="page oee-page" data-testid="oee-view">
      <div className="page-head"><h2>{t("oee.title")}</h2><span className="muted">{t("oee.subtitle")}</span></div>
      <Tabs tabs={tabs.map((x) => ({ key: x.key, label: x.label, icon: x.icon, testid: `oee-tab-${x.key}` }))} value={tab} onChange={(k) => set({ tab: k })} />
      <div className="scroll grow oee-scroll">
        {tab === "overview" && <OeeDashboard />}
        {tab === "events" && <OeeEvents />}
        {tab === "machines" && <OeeMachines />}
        {tab === "shifts" && <OeeShifts />}
        {tab === "reasons" && <OeeReasons />}
        {tab === "params" && <OeeParams />}
      </div>
    </div>
  );
}
