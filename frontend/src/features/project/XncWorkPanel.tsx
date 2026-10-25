// «XNC ishi» (2026-10-25): buyurtma bo'yicha XNC ishi asbob kesimida — har parma teshiklari, freza / arra metri, nechta detalda,
// MES kodi va MES ga ketadimi (sozlama: «Настройки → MES интеграция → XNC → MES»).
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { get } from "../../api/client";
import type { Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { Empty, Tabs } from "../../shared/ui";
import { XncWorkTable, type XncWork } from "../settings/XncMes";
import { topTabs } from "./topTabs";

export function XncWorkPanel({ project }: { project: Project }) {
  const { t } = useTranslation();
  const ui = useUI();
  const stamp = project.operations.filter((o) => o.type === "XNC").map((o) => `${o.id}:${o.xnc?.qty}:${o.xnc?.program.length}`).join(",");
  const q = useQuery({ queryKey: ["xnc-work", project.id, stamp], queryFn: () => get<XncWork>(`/projects/${project.id}/xnc-tools`) });
  return (
    <div className="panel rt" data-testid="xnc-work">
      <Tabs tabs={topTabs(t)} value="xnc_work" onChange={(k) => ui.set({ topTab: k })} />
      <div className="rt-body">
        {!q.data ? <Empty>…</Empty> : <XncWorkTable work={q.data} testid="xnc-work-table" />}
      </div>
    </div>
  );
}
