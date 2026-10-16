// CL — Погонажный раскрой: 4 ta tab (Параметры, Детали, Полосы и отходы, Раскрой). CS paneli namunasida; tab holati `csTab` (umumiy).
import { useEffect, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Layers, LayoutGrid, Settings2, SquareStack } from "lucide-react";
import type { Operation, Project } from "../../api/types";
import { useUI, type CsTab } from "../../store/ui";
import { Tabs } from "../../shared/ui";
import { restoreScopeOnce, setScope } from "../../shared/hotkeys";
import { ParamHelpHost } from "../../shared/ParamHelp";
import { ClParams } from "./ClParams";
import { ClParts } from "./ClParts";
import { ClSheets } from "./ClSheets";
import { ClCut } from "./ClCut";
import "./cl.css";

export function ClTabs({ right }: { right?: ReactNode }) {
  const { t } = useTranslation();
  const ui = useUI();
  return (
    <Tabs<CsTab> value={ui.csTab} onChange={(k) => { ui.set({ csTab: k }); setScope(k); }} right={right} tabs={[
      { key: "params", label: t("cl.tab.params"), icon: Settings2, testid: "cl-tab-params" },
      { key: "parts", label: t("cl.tab.parts"), icon: Layers, testid: "cl-tab-parts" },
      { key: "sheets", label: t("cl.tab.sheets"), icon: SquareStack, testid: "cl-tab-sheets" },
      { key: "cut", label: t("cl.tab.cut"), icon: LayoutGrid, testid: "cl-tab-cut" },
    ]} />
  );
}

export function ClPanel({ project, op }: { project: Project; op: Operation }) {
  const tab = useUI((s) => s.csTab);
  // sahifa ochilganda: tiklangan tab yorliqlari darhol ishlasin (faol maydon bo'lsa — unga tegilmaydi, hotkeys.restoreScopeOnce)
  useEffect(() => { if (tab !== "params") restoreScopeOnce(tab); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  if (!op.cl) return null;
  return (
    <>
      {tab === "params" ? <ClParams project={project} op={op} /> : tab === "sheets" ? <ClSheets project={project} op={op} />
        : tab === "cut" ? <ClCut project={project} op={op} /> : <ClParts project={project} op={op} />}
      <ParamHelpHost />
    </>
  );
}
