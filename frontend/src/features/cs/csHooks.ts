// W2: CS bo'shliqlari uchun so'rovlar (kroygacha/keyin material va list miqdori).
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { get } from "../../api/client";
import type { CsQuantities, Operation, Project } from "../../api/types";

/** «Количество материала» / «Количество листов» (CS-036/037): kroygacha — taxminiy (`estimated`), keyin — natijadan.
 *  Hisob backendda (`calc.cs_cost`); so'rov detallar/listlar/parametrlar/natija o'zgarganda yangilanadi. */
export function useCsQuantities(project: Project, op: Operation) {
  const edgeSizes = useMemo(() => project.operations.filter((o) => o.type === "EL").map((o) => [o.id, o.el?.thickness, o.el?.jointing_width]),
    [project.operations]);
  const stamp = useMemo(() => JSON.stringify([project.size_mode, op.cs_material, op.cs_cut, op.sheets.map((s) => [s.length, s.width, s.is_remnant, s.source_remnant_id]),
    op.parts.map((p) => [p.length, p.width, p.qty, p.minus_qty, p.product_id, p.allow_top, p.allow_bottom, p.allow_left, p.allow_right,
      p.edge_top.op_id, p.edge_bottom.op_id, p.edge_left.op_id, p.edge_right.op_id]),
    project.products.map((p) => [p.id, p.qty]), edgeSizes, op.result?.total_sheets ?? null, op.result?.material_qty_m2 ?? null]),
  [project.size_mode, project.products, op.cs_material, op.cs_cut, op.sheets, op.parts, op.result, edgeSizes]);
  return useQuery({
    queryKey: ["cs-quantities", project.id, op.id, stamp],
    queryFn: () => get<CsQuantities>(`/projects/${project.id}/operations/${op.id}/cs-quantities`),
    placeholderData: (prev) => prev,
  });
}
