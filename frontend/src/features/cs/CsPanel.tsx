// CS — Листовой раскрой: 4 ta tab (Параметры, Детали, Листы и остатки, Раскрой).
import { useEffect, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Layers, LayoutGrid, Settings2, SquareStack } from "lucide-react";
import type { Operation, Project } from "../../api/types";
import { useUI, type CsTab } from "../../store/ui";
import { Tabs } from "../../shared/ui";
import { CsParams } from "./CsParams";
import { CsParts } from "./CsParts";
import { CsSheets } from "./CsSheets";
import { CsCut } from "./CsCut";
import { setScope } from "../../shared/hotkeys";
import { ParamHelpHost } from "../../shared/ParamHelp";
import "./csW2.css";

export function CsTabs({ right }: { right?: ReactNode }) {
  const { t } = useTranslation();
  const ui = useUI();
  return (
    <Tabs<CsTab> value={ui.csTab} onChange={(k) => { ui.set({ csTab: k }); setScope(k); }} right={right} tabs={[
      { key: "params", label: t("cs.tab.params"), icon: Settings2, testid: "cs-tab-params" },
      { key: "parts", label: t("cs.tab.parts"), icon: Layers, testid: "cs-tab-parts" },
      { key: "sheets", label: t("cs.tab.sheets"), icon: SquareStack, testid: "cs-tab-sheets" },
      { key: "cut", label: t("cs.tab.cut"), icon: LayoutGrid, testid: "cs-tab-cut" },
    ]} />
  );
}

let initialScopeDone = false;     // sahifa ochilganda bir marta: tiklangan tab yorliqlari darhol ishlasin

export function CsPanel({ project, op }: { project: Project; op: Operation }) {
  const tab = useUI((s) => s.csTab);
  useEffect(() => {
    if (!initialScopeDone) { initialScopeDone = true; if (tab !== "params") setScope(tab); }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <>
      {tab === "params" ? <CsParams project={project} op={op} /> : tab === "sheets" ? <CsSheets project={project} op={op} />
        : tab === "cut" ? <CsCut project={project} op={op} /> : <CsParts project={project} op={op} />}
      <ParamHelpHost />
    </>
  );
}
