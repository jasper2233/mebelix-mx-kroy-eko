// Ochiq loyiha: sarlavha, yuqori jadval (Операции / Изделия), splitter, pastki panel (operatsiya turiga qarab).
import { useEffect, useState } from "react";
import { RemnantInPanel, RemnantOutPanel } from "./RemnantTabs";
import { XncWorkPanel } from "./XncWorkPanel";
import { useTranslation } from "react-i18next";
import { Package } from "lucide-react";
import type { Project } from "../../api/types";
import { useUI } from "../../store/ui";
import { useHotkeys } from "../../shared/hotkeys";
import { Empty, Splitter } from "../../shared/ui";
import { Header } from "./Header";
import { OperationsTable } from "./OperationsTable";
import { ProductsTable } from "./ProductsTable";
import { OpBadge } from "./opmeta";
import { redo, undo } from "./ProjectMenu";
import { CsPanel } from "../cs/CsPanel";
import { ClPanel } from "../cl/ClPanel";
import { CnPanel } from "../cn/CnPanel";
import { ElPanel } from "../el/ElPanel";
import { XncPanel } from "../xnc/XncPanel";
import { GrPanel } from "../el/GrPanel";
import { OPanel } from "../o/OPanel";
import { LbPanel } from "../print/LabelsPanel";
import { SpPanel } from "../sp/SpPanel";
import { layoutHeight } from "../../shared/uiZoom";

export function ProjectView({ project }: { project: Project }) {
  const { t } = useTranslation();
  const ui = useUI();
  // yuqori panel — oyna balandligining ulushi: oyna kichraysa / kattalashsa ikkala panel birga, nisbatni saqlab o'zgaradi
  // (foydalanuvchi, 2026-10-21: onlayn tizimdagidek; avval qat'iy px edi — kichrayish faqat pastki panelga tushardi)
  const [vh, setVh] = useState(() => layoutHeight());       // #root ichidagi px (oyna masshtabi hisobga olingan)
  useEffect(() => {
    const on = () => setVh(layoutHeight());
    window.addEventListener("resize", on);
    return () => window.removeEventListener("resize", on);
  }, []);
  const topPx = Math.max(90, Math.round(ui.topFrac * vh));
  const op = project.operations.find((o) => o.id === ui.opId);
  const prod = project.products.find((p) => p.id === ui.productId) ?? project.products[0];

  useEffect(() => {
    if (!op && project.operations.length) ui.set({ opId: project.operations[0].id });
  }, [op, project.operations, ui]);

  useHotkeys("global", {
    "ctrl+z": () => void undo(project.id),
    "ctrl+y,ctrl+shift+z": () => void redo(project.id),
  });

  let panel = <Empty>{t("project.no_op")}</Empty>;
  if (op?.type === "CS") panel = <CsPanel project={project} op={op} />;
  else if (op?.type === "CL") panel = <ClPanel project={project} op={op} />;
  else if (op?.type === "CN") panel = <CnPanel project={project} op={op} />;
  else if (op?.type === "EL") panel = <ElPanel project={project} op={op} />;
  else if (op?.type === "XNC") panel = <XncPanel project={project} op={op} />;
  else if (op?.type === "GR") panel = <GrPanel project={project} op={op} />;
  else if (op?.type === "SP") panel = <SpPanel project={project} op={op} />;
  else if (op?.type === "O") panel = <OPanel project={project} op={op} />;
  else if (op?.type === "LB") panel = <LbPanel project={project} op={op} />;
  else if (op) panel = <Empty>{t("ops.later")}</Empty>;

  return (
    <div className="project">
      <Header project={project} />
      <div className="top" style={{ height: topPx }}>
        {ui.topTab === "ops" ? <OperationsTable project={project} /> : ui.topTab === "rem_in" ? <RemnantInPanel project={project} />
          : ui.topTab === "rem_out" ? <RemnantOutPanel project={project} />
          : ui.topTab === "xnc_work" ? <XncWorkPanel project={project} /> : <ProductsTable project={project} />}
      </div>
      <Splitter value={topPx} onChange={(v) => ui.set({ topHeight: v, topFrac: v / vh })} min={90} />
      <div className="midbar">
        <div className="midbar-op">{op ? <><OpBadge type={op.type} paren /> {op.name || op.code}</> : null}</div>
        <div className="midbar-prod" title={t("project.current_product")}>
          {prod && <><Package size={13} /> №{project.products.indexOf(prod) + 1} {prod.name} ({prod.qty} {t("app.pcs")})</>}
        </div>
      </div>
      <div className="bottom">{panel}</div>
    </div>
  );
}
