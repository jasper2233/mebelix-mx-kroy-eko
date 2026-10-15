// Material bazasi tekshiruvi va buyurtmalar navbati (2026-10-15): `GET /projects/{id}/material-check`, `GET /queue`.
import { useQuery } from "@tanstack/react-query";
import { get } from "../../api/client";
import type { MaterialCheck, Project, QueueInfo } from "../../api/types";

/** Natija (listlar soni) yoki material o'zgarsa qayta so'raladi. */
export const materialStamp = (p: Pick<Project, "operations">) =>
  p.operations.map((o) => `${o.id}:${o.material_id ?? ""}:${o.code}:${o.result?.total_sheets ?? "-"}:${o.parts.length}`).join("|");

export const useMaterialCheck = (project: Pick<Project, "id" | "operations">, enabled = true) =>
  useQuery({ queryKey: ["material-check", project.id, materialStamp(project)], enabled, staleTime: 30_000,
    queryFn: () => get<MaterialCheck>(`/projects/${project.id}/material-check`) });

export const useQueue = (statuses: string, enabled = true) =>
  useQuery({ queryKey: ["queue", statuses], enabled, staleTime: 0,
    queryFn: () => get<QueueInfo>("/queue", { statuses, limit: 300 }) });
