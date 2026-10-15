// GR paz hisobi (server: GET …/operations/{id}/groove-usage) — «Детали» jadvali va hisoblangan ko'rsatkichlar.
import { useQuery } from "@tanstack/react-query";
import { get } from "../../api/client";

export interface GrooveRow {
  part_id: string; uid: number; material: string; length: number; width: number; qty: number;
  top: number; bottom: number; left: number; right: number;      // 0 — paz yo'q, 1 — lits tomonda, 2 — orqa tomonda
  groove_len_m: number; name: string;
}
export interface GrooveUsage { rows: GrooveRow[]; usage: number; cut_length: number; passes: number; cost: number }

export const useGrooveUsage = (pid: string, oid: string, stamp: unknown) =>
  useQuery({ queryKey: ["groove-usage", pid, oid, stamp], queryFn: () => get<GrooveUsage>(`/projects/${pid}/operations/${oid}/groove-usage`) });
