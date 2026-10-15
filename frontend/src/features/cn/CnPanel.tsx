// (CN) Нестинговый раскрой: 4 ta tab (Параметры, Детали, Листы и остатки, Раскрой). CL paneli shablonida; tab holati `csTab` (umumiy).
import { useEffect, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Layers, LayoutGrid, Settings2, SquareStack } from "lucide-react";
import type { Operation, Project } from "../../api/types";
import { useUI, type CsTab } from "../../store/ui";
import { Tabs } from "../../shared/ui";
import { setScope } from "../../shared/hotkeys";
import { ParamHelpHost } from "../../shared/ParamHelp";
import { CnParams } from "./CnParams";
import { CnParts } from "./CnParts";
import { CnSheets } from "./CnSheets";
import { CnCut } from "./CnCut";
import { resumeCnJob } from "./cnHooks";
import "./cn.css";

export function CnTabs({ right }: { right?: ReactNode }) {
  const { t } = useTranslation();
  const ui = useUI();
  return (
    <Tabs<CsTab> value={ui.csTab} onChange={(k) => { ui.set({ csTab: k }); setScope(k); }} right={right} tabs={[
      { key: "params", label: t("cn.tab.params"), icon: Settings2, testid: "cn-tab-params" },
      { key: "parts", label: t("cn.tab.parts"), icon: Layers, testid: "cn-tab-parts" },
      { key: "sheets", label: t("cn.tab.sheets"), icon: SquareStack, testid: "cn-tab-sheets" },
      { key: "cut", label: t("cn.tab.cut"), icon: LayoutGrid, testid: "cn-tab-cut" },
    ]} />
  );
}

let initialScopeDone = false;     // sahifa ochilganda bir marta: tiklangan tab yorliqlari darhol ishlasin

export function CnPanel({ project, op }: { project: Project; op: Operation }) {
  const tab = useUI((s) => s.csTab);
  useEffect(() => {
    if (!initialScopeDone) { initialScopeDone = true; if (tab !== "params") setScope(tab); }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  // sahifa qayta yuklangan / operatsiya ochilgan: server tomonda ketayotgan vazifa bo'lsa — progress va «Остановить» tiklanadi
  useEffect(() => { void resumeCnJob(project.id, op.id); }, [project.id, op.id]);
  if (!op.cn) return null;
  return (
    <>
      {tab === "params" ? <CnParams project={project} op={op} /> : tab === "sheets" ? <CnSheets project={project} op={op} />
        : tab === "cut" ? <CnCut project={project} op={op} /> : <CnParts project={project} op={op} />}
      <ParamHelpHost />
    </>
  );
}
