// XNC muharriri sozlamalari (W8): asboblar jadvali, palitra, stanok cheklovlari — turlar va hooklar.
// Backend: services/xnc_tools.py, services/xnc_constraints.py; sozlama doiralari xnc_tools / xnc_palette / xnc_constraints
// (`/api/settings/<doira>/default`).
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useDefaults, qc } from "../../api/hooks";
import { get, put } from "../../api/client";

export const PLANES = ["front", "left", "right", "top", "bottom"] as const;
export type Plane = (typeof PLANES)[number];

export interface XncToolRow { plane: Plane; d: number; through: boolean; name: string; depth: number | null; comment: string }
export interface XncToolsDoc { tools: XncToolRow[] }
export interface XncPaletteItem { cmd: string; enabled: boolean }
export interface XncPaletteDoc { items: XncPaletteItem[] }

export interface Limit { enabled: boolean; value: number }
export interface Flag { enabled: boolean; value: boolean }
export type CMode = "off" | "warn" | "block";
export type Corner = "LT" | "RT" | "LB" | "RB";

export const LIMIT_KEYS = [
  "length_min", "length_max", "width_min", "width_max", "thickness_min", "thickness_max",
  "hole_center_top", "hole_center_bottom", "hole_center_left", "hole_center_right",
  "groove_margin_top", "groove_margin_bottom", "groove_margin_left", "groove_margin_right",
  "mill_max_distance", "blind_depth_margin", "hole_gap_min", "hole_edge_front_min", "hole_edge_horizontal_min",
] as const;
export type LimitKey = (typeof LIMIT_KEYS)[number];

export type XncConstraints = {
  mode: CMode;
  rotate_long_side: "off" | "horizontal" | "vertical";
  rotate_corner_on: boolean; rotate_corner: Corner;
  groove_horizontal: Flag; groove_vertical: Flag; avoid_bottom_horizontal: Flag;
} & Record<LimitKey, Limit>;

export interface XncIssue { level: "warn" | "error"; code: string; text: string; text_ru?: string; text_uz?: string; command_path: string; count?: number }

export const useXncTools = () => useDefaults<XncToolsDoc>("xnc_tools");
export const useXncPaletteDoc = () => useDefaults<XncPaletteDoc>("xnc_palette");
export const useXncConstraints = () => useDefaults<XncConstraints>("xnc_constraints");

/** Ichki sozlamalarning o'rnatilgan (standart) qiymatlari: GET /api/settings → {doira: standart}. */
export const useBuiltinSettings = () =>
  useQuery({ queryKey: ["settings-builtin"], staleTime: Infinity, queryFn: () => get<Record<string, unknown>>("/settings") });

/** Standart profilni saqlash (PUT /settings/<doira>/default) va tegishli so'rovlarni yangilash. */
export async function saveDefault(scope: string, data: unknown): Promise<boolean> {
  await put(`/settings/${scope}/default`, data);      // javob — profil qatori; hujjat qayta o'qiladi
  await qc.invalidateQueries({ queryKey: ["defaults", scope] });
  await qc.invalidateQueries({ queryKey: ["xnc-stats"] });
  return true;
}

/** Palitra: yoqilgan buyruqlar tartib bilan; `known` — frontend palitrasidagi barcha buyruqlar (yetishmaganlari oxiriga). */
export function usePaletteOrder(known: string[]): string[] {
  const q = useXncPaletteDoc();
  return useMemo(() => {
    const items = q.data?.items;
    if (!items) return known;
    const ordered = items.filter((i) => known.includes(i.cmd));
    const seen = new Set(ordered.map((i) => i.cmd));
    return [...ordered.filter((i) => i.enabled).map((i) => i.cmd), ...known.filter((c) => !seen.has(c))];
  }, [q.data, known]);
}

/** Buyruq → asboblar jadvalidagi tekislik (T maydoni avtoto'ldirish uchun). */
export const PLANE_OF_CMD: Record<string, Plane> = {
  DrillFront: "front", DrillLeft: "left", DrillRight: "right", DrillTop: "top", DrillBottom: "bottom",
};

/** «2.3» → daraxtdagi yo'l [1, 2] (0 dan). */
export function pathOf(commandPath: string): number[] | null {
  if (!commandPath) return null;
  const p = commandPath.split(".").map((s) => Number(s) - 1);
  return p.every((n) => Number.isInteger(n) && n >= 0) ? p : null;
}
