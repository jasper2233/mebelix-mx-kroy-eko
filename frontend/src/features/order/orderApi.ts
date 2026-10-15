// «Заказать» oqimi: backend (`GET/POST /projects/{id}/order`) turlari va yordamchilari (W14).
import { useQuery } from "@tanstack/react-query";
import { get } from "../../api/client";
import type { OrderLogEntry, OrderStatus, Project } from "../../api/types";

export interface OrderWarning { code: string; n: number; text: string }

export interface OrderTransition {
  to: OrderStatus; kind: "forward" | "skip" | "back"; allowed: boolean; reason: string | null;
  needs_ready_date: boolean; warnings: OrderWarning[];
}

export interface OrderState {
  status: OrderStatus; order_date: string; ready_date: string; ready_set: boolean; executor: string; comment: string;
  transitions: OrderTransition[]; can_change: boolean; can_back: boolean; edit_warning: boolean;
  lock: { from_status: number | null; active: boolean }; log: OrderLogEntry[];
}

/** Loyiha o'zgarganda qayta so'raladigan kalit (holat, sana, tarix uzunligi). */
export const orderStamp = (p: Pick<Project, "status" | "ready_date" | "order_log">) =>
  `${p.status}|${p.ready_date}|${p.order_log?.length ?? 0}`;

export const useOrderState = (project: Pick<Project, "id" | "status" | "ready_date" | "order_log">, enabled = true) =>
  useQuery({ queryKey: ["order", project.id, orderStamp(project)], enabled,
    queryFn: () => get<OrderState>(`/projects/${project.id}/order`) });

/** «Заказать» tugmasi navbatdagi qadam: 0→1, 1→2, 2→3, 3→yo'q. */
export function nextStatus(s: OrderStatus): OrderStatus | null {
  return s >= 3 ? null : ((s + 1) as OrderStatus);
}

const p2 = (n: number) => String(n).padStart(2, "0");

/** ISO (UTC, «Z» bilan) → mahalliy «dd.MM.yyyy HH:mm»; bo'sh/noto'g'ri — bo'sh matn. */
export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return `${p2(d.getDate())}.${p2(d.getMonth() + 1)}.${d.getFullYear()} ${p2(d.getHours())}:${p2(d.getMinutes())}`;
}

/** «YYYY-MM-DD» → «dd.MM.yyyy». */
export function fmtDate(s: string | null | undefined): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s ?? "");
  return m ? `${m[3]}.${m[2]}.${m[1]}` : (s ?? "");
}
