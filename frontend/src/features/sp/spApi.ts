// SP sirt ishlovi hisobi (server: GET …/operations/{id}/surface-usage) — «Детали» jadvali va hisoblangan ko'rsatkichlar.
import { useQuery } from "@tanstack/react-query";
import { get } from "../../api/client";
import type { SurfaceUsage } from "../../api/types";

export type SurfaceRow = SurfaceUsage["rows"][number];

export const useSurfaceUsage = (pid: string, oid: string, stamp: unknown) =>
  useQuery({ queryKey: ["surface-usage", pid, oid, stamp], queryFn: () => get<SurfaceUsage>(`/projects/${pid}/operations/${oid}/surface-usage`) });
