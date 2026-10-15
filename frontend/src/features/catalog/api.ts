// «Товары» (material katalogi): daraxt, materiallar ro'yxati va bitta qator (rasm bilan) uchun so'rovlar.
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { get } from "../../api/client";
import type { CatalogItem } from "../../api/types";

export interface CatalogNode {
  id: string; parent_id: string | null; name: string; code: string; kind: "folder"; count: number; children: CatalogNode[];
}
export interface CatalogTree { nodes: CatalogNode[]; total: number; unfiled: number }
export type CatalogSel = { type: "all" } | { type: "unfiled" } | { type: "folder"; id: string };
export type CatalogDetail = CatalogItem & { image: string | null };

export const CATALOG_KINDS = ["sheet", "edge", "linear", "surface"] as const;
export const ITEM_LIMIT = 2000;

export const useCatalogTree = (kind: string, q: string) =>
  useQuery({ queryKey: ["catalog", "tree", kind, q],
    queryFn: () => get<CatalogTree>("/catalog/tree", { kind: kind || undefined, q: q || undefined }) });

export const useCatalogItems = (kind: string, q: string, node: CatalogSel) =>
  useQuery({ queryKey: ["catalog", "items", kind, q, node],
    queryFn: () => get<CatalogItem[]>("/catalog", {
      kind: kind || undefined, q: q || undefined, folders: false, limit: ITEM_LIMIT,
      ...(node.type === "unfiled" ? { unfiled: true } : node.type === "folder" ? { parent_id: node.id, recursive: true } : {}),
    }) });

export const useCatalogItem = (id: string | null) =>
  useQuery({ queryKey: ["catalog", "item", id], queryFn: () => get<CatalogDetail>(`/catalog/${encodeURIComponent(id ?? "")}`), enabled: !!id });

/** Qidiruv matnini kechiktirish (har harfda so'rov ketmasin). */
export function useDebounced<T>(value: T, ms = 250): T {
  const [v, setV] = useState(value);
  useEffect(() => { const h = setTimeout(() => setV(value), ms); return () => clearTimeout(h); }, [value, ms]);
  return v;
}

/** Rasm manbai xavfsizligi (serverda ham tekshiriladi): faqat tasdiqlangan `data:image/…` yoki http(s) havola. */
const IMG_OK = /^(data:image\/(png|jpeg|gif|webp);base64,[A-Za-z0-9+/=]+|https?:\/\/[^\s"'<>\\]+)$/;
export const safeImage = (src: string | null | undefined): string | null => (src && IMG_OK.test(src) ? src : null);
