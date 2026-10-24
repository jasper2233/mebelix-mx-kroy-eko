import { useTranslation } from "react-i18next";
import type { LucideIcon } from "lucide-react";
import { IcoCL, IcoCN, IcoCS, IcoEL, IcoGR, IcoLB, IcoO, IcoSP, IcoXNC } from "../../shared/opIcons";
import type { OpType, Operation, Project } from "../../api/types";

export const OP_ICONS: Record<OpType, LucideIcon> = {
  O: IcoO, CS: IcoCS, CN: IcoCN, CL: IcoCL, EL: IcoEL, SP: IcoSP, GR: IcoGR, XNC: IcoXNC, LB: IcoLB,
};

export const OP_COLORS: Record<OpType, string> = {
  O: "#6b7a89", CS: "#b86e00", CN: "#8a5a00", CL: "#6b4f9e", EL: "#1f6feb", SP: "#0e7d78", GR: "#7a5c2e",
  XNC: "#7d3cc9", LB: "#4b5563",
};

export const IMPLEMENTED: OpType[] = ["O", "CS", "CN", "CL", "EL", "SP", "GR", "XNC", "LB"];

/** Operatsiya turi: rangli belgi + oddiy qora matn («CS», `paren` — «(CS)»: holat qatori). */
export function OpBadge({ type, paren }: { type: OpType; paren?: boolean }) {
  const Icon = OP_ICONS[type];
  const { t } = useTranslation();
  return (
    <span className="opbadge" title={t(`optype.tip.${type}`, { defaultValue: type })}>
      <Icon size={15} /> {paren ? `(${type})` : type}
    </span>
  );
}

export function edgeOps(project: Project): Operation[] {
  return project.operations.filter((o) => o.type === "EL");
}

export function opById(project: Project, id: string | null | undefined): Operation | undefined {
  return id ? project.operations.find((o) => o.id === id) : undefined;
}
