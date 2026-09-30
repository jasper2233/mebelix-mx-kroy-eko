import type { LucideIcon } from "lucide-react";
import { Drill, LayoutGrid, Package, PaintBucket, Ribbon, Rows3, Ruler, Shapes, Tag } from "lucide-react";
import type { OpType, Operation, Project } from "../../api/types";

export const OP_ICONS: Record<OpType, LucideIcon> = {
  O: Package, CS: LayoutGrid, CN: Shapes, CL: Ruler, EL: Ribbon, SP: PaintBucket, GR: Rows3, XNC: Drill, LB: Tag,
};

export const OP_COLORS: Record<OpType, string> = {
  O: "#6b7a89", CS: "#b86e00", CN: "#8a5a00", CL: "#6b4f9e", EL: "#1f6feb", SP: "#0e7d78", GR: "#7a5c2e",
  XNC: "#7d3cc9", LB: "#4b5563",
};

export const IMPLEMENTED: OpType[] = ["CS", "EL", "GR", "XNC"];

export function OpBadge({ type }: { type: OpType }) {
  const Icon = OP_ICONS[type];
  return (
    <span className="opbadge" style={{ color: OP_COLORS[type] }}>
      <Icon size={13} /> {type}
    </span>
  );
}

export function edgeOps(project: Project): Operation[] {
  return project.operations.filter((o) => o.type === "EL");
}

export function opById(project: Project, id: string | null | undefined): Operation | undefined {
  return id ? project.operations.find((o) => o.id === id) : undefined;
}
