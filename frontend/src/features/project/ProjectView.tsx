// Ochiq loyiha: sarlavha, yuqori jadval (Операции / Изделия), splitter, pastki panel (operatsiya turiga qarab).
import { useEffect } from "react";
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
import { ElPanel } from "../el/ElPanel";
import { XncPanel } from "../xnc/XncPanel";
import { GrPanel } from "../el/GrPanel";

export function ProjectView({ project }: { project: Project }) {
  const { t } = useTranslation();
  const ui = useUI();
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
  else if (op?.type === "EL") panel = <ElPanel project={project} op={op} />;
  else if (op?.type === "XNC") panel = <XncPanel project={project} op={op} />;
  else if (op?.type === "GR") panel = <GrPanel project={project} op={op} />;
  else if (op) panel = <Empty>{t("ops.later")}</Empty>;

  return (
    <div className="project">
      <Header project={project} />
      <div className="top" style={{ height: ui.topHeight }}>
        {ui.topTab === "ops" ? <OperationsTable project={project} /> : <ProductsTable project={project} />}
      </div>
      <Splitter value={ui.topHeight} onChange={(v) => ui.set({ topHeight: v })} min={90} />
      <div className="midbar">
        <div className="midbar-op">{op ? <><OpBadge type={op.type} /> {op.name || op.code}</> : null}</div>
        <div className="midbar-prod" title={t("project.current_product")}>
          {prod && <><Package size={13} /> №{project.products.indexOf(prod) + 1} {prod.name} ({prod.qty} {t("app.pcs")})</>}
        </div>
      </div>
      <div className="bottom">{panel}</div>
    </div>
  );
}
