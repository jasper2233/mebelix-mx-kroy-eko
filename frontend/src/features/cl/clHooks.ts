// (CL) so'rovlar: kroygacha / keyin material uzunligi, polosalar, kesim uzunligi va narx (backend `cl_calc.cl_cost`).
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { get } from "../../api/client";
import type { ClQuantities, Operation, Project } from "../../api/types";

/** Polosa balandligi (SVG ko'rinishi): eniga mutanosib, lekin yozuvlar o'qilishi uchun pastdan cheklangan — backend `cl_render.view_height` bilan bir xil. */
export const VIEW_RATIO = 14;

export function viewHeight(L: number, W: number, fs: number): number {
  return Math.max(W, L / VIEW_RATIO, 3.4 * fs);
}

export function useClQuantities(project: Project, op: Operation) {
  const edgeSizes = useMemo(() => project.operations.filter((o) => o.type === "EL").map((o) => [o.id, o.el?.thickness, o.el?.jointing_width]),
    [project.operations]);
  const stamp = useMemo(() => JSON.stringify([project.size_mode, op.cl, op.sheets.map((s) => [s.length, s.qty, s.is_remnant, s.source_remnant_id]),
    op.parts.map((p) => [p.length, p.qty, p.minus_qty, p.product_id, p.allow_left, p.allow_right,
      p.edge_top.op_id, p.edge_bottom.op_id, p.edge_left.op_id, p.edge_right.op_id]),
    project.products.map((p) => [p.id, p.qty]), edgeSizes, op.result?.total_sheets ?? null, op.result?.material_len_m ?? null]),
  [project.size_mode, project.products, op.cl, op.sheets, op.parts, op.result, edgeSizes]);
  return useQuery({
    queryKey: ["cl-quantities", project.id, op.id, stamp],
    queryFn: () => get<ClQuantities>(`/projects/${project.id}/operations/${op.id}/cl-quantities`),
    placeholderData: (prev) => prev,
  });
}
