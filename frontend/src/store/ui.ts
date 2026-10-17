// Interfeys holati (Zustand). Server ma'lumotlari — TanStack Query da.
import { create } from "zustand";

export type View = "main" | "print" | "settings" | "help" | "workshop";
export type Section = "lang" | "project" | "print" | "mes" | "settings" | "help";
export type CsTab = "params" | "parts" | "sheets" | "cut";
export type ElTab = "params" | "parts";
export type XncTab = "params" | "program" | "cost";

export interface Toast { id: number; kind: "info" | "ok" | "warn" | "error"; text: string; details?: string[]; count?: number }

/** Xabarnoma ko'rinish vaqti (ms): turi bo'yicha + matn uzunligiga qarab (o'qishga ulgurilsin); sichqoncha ustida — to'xtaydi. */
export function toastTtl(t: Pick<Toast, "kind" | "text" | "details">): number {
  const base = { ok: 3500, info: 5000, warn: 8000, error: 10000 }[t.kind];
  const len = t.text.length + (t.details ?? []).slice(0, 5).join(" ").length;
  return Math.min(base + Math.max(0, len - 80) * 40, 30000);
}
const TOAST_MAX = 4;                                   // bir vaqtda ko'pi bilan; eskisi (xato emas) avval yopiladi
const toastTimers = new Map<number, ReturnType<typeof setTimeout>>();

function load<T>(key: string, dflt: T): T {
  try {
    const v = localStorage.getItem(key);
    return v === null ? dflt : (JSON.parse(v) as T);
  } catch {
    return dflt;
  }
}

function save(key: string, v: unknown) {
  try { localStorage.setItem(key, JSON.stringify(v)); } catch { /* yo'q */ }
}

interface UI {
  lang: "ru" | "uz";
  projectId: string | null;
  folderId: string | null;
  view: View;
  section: Section;
  topTab: "ops" | "products";
  opId: string | null;
  productId: string | null;
  csTab: CsTab;
  elTab: ElTab;
  xncTab: XncTab;
  partSel: string[];
  mapIndex: number;
  topHeight: number;              // yuqori jadval balandligi (px)
  columnProfile: number | null;   // «Настройки колонок» profili (null — standart)
  gridColumnProfiles: Record<string, number | null>;   // boshqa jadvallar «Настройки» profili: scope → id (o_columns, el_columns …)
  showCommands: boolean;          // Раскрой: miniatyuralar ↔ buyruqlar jadvali
  mapLabel: "number" | "name" | "number_name";   // Раскрой: detal yozuvi
  mapEdges: boolean;              // Раскрой: kromka belgilari
  cutIndicators: string[];        // Раскрой: status qatoridagi ko'rsatkichlar (№ S C Cp LT F R CT T AP AM AW)
  productHidden: string[];        // Изделия: yashirilgan ustunlar
  editorOpen: boolean;
  zeroFilter: boolean;            // Ctrl+F — nol sonlilarni yashirish (Изделия)
  toasts: Toast[];
  set: (p: Partial<UI>) => void;
  openProject: (id: string | null) => void;
  setLang: (l: "ru" | "uz") => void;
  toast: (text: string, kind?: Toast["kind"], details?: string[]) => void;
  dropToast: (id: number) => void;
  /** sichqoncha xabarnoma ustida — avtomatik yopilish to'xtaydi (hold=true), chiqqanda qayta boshlanadi */
  holdToast: (id: number, hold: boolean) => void;
}

let toastSeq = 1;

export const useUI = create<UI>((set, get) => ({
  lang: load("mxk_lang", "ru"),
  projectId: load("mxk_project", null),
  folderId: load("mxk_folder", null),
  view: "main",
  section: load<string | null>("mxk_project", null) ? "project" : "project",
  topTab: "ops",
  opId: null,
  productId: null,
  csTab: load("mxk_cs_tab", "parts"),
  elTab: "params",
  xncTab: "params",
  partSel: [],
  mapIndex: 1,
  topHeight: load("mxk_top_h", 246),          // ≈ 8 operatsiya qatori ko'rinadi (21px qatorlar)
  columnProfile: load("mxk_col_profile", null),
  gridColumnProfiles: load("mxk_grid_col_profiles", {}),
  showCommands: load("mxk_show_cmds", false),
  mapLabel: load("mxk_map_label", "number"),      // standart — faqat ID raqami (onlayn tizimdagidek); nom — «Подпись детали» sozlamasi
  mapEdges: load("mxk_map_edges", true),
  cutIndicators: load("mxk_cut_ind", ["num", "S", "C", "Cp", "LT", "F"]),
  productHidden: load("mxk_prod_hidden", []),
  editorOpen: false,
  zeroFilter: false,
  toasts: [],
  set: (p) => {
    set(p);
    if (p.topHeight !== undefined) save("mxk_top_h", p.topHeight);
    if (p.folderId !== undefined) save("mxk_folder", p.folderId);
    if (p.csTab !== undefined) save("mxk_cs_tab", p.csTab);
    if (p.columnProfile !== undefined) save("mxk_col_profile", p.columnProfile);
    if (p.gridColumnProfiles !== undefined) save("mxk_grid_col_profiles", p.gridColumnProfiles);
    if (p.showCommands !== undefined) save("mxk_show_cmds", p.showCommands);
    if (p.mapLabel !== undefined) save("mxk_map_label", p.mapLabel);
    if (p.mapEdges !== undefined) save("mxk_map_edges", p.mapEdges);
    if (p.cutIndicators !== undefined) save("mxk_cut_ind", p.cutIndicators);
    if (p.productHidden !== undefined) save("mxk_prod_hidden", p.productHidden);
  },
  openProject: (id) => {
    save("mxk_project", id);
    // loyiha ochilganda pastki panel doim «Параметры» yorlig'ida (oldingi seansdagi yorliq tiklanmaydi)
    if (id) save("mxk_cs_tab", "params");
    set({ projectId: id, opId: null, productId: null, partSel: [], mapIndex: 1, view: "main", section: "project",
          editorOpen: false, ...(id ? { csTab: "params" as CsTab, elTab: "params" as ElTab, xncTab: "params" as XncTab } : {}) });
  },
  setLang: (l) => {
    save("mxk_lang", l);
    set({ lang: l });
  },
  toast: (text, kind = "info", details) => {
    text = String(text ?? "");
    const list = get().toasts;
    // aynan shu xabar allaqachon ko'rinib turibdi — yangisi qo'shilmaydi, hisoblagich (×2) va vaqt yangilanadi
    const same = list.find((t) => t.kind === kind && t.text === text);
    if (same) {
      set({ toasts: list.map((t) => (t.id === same.id ? { ...t, details, count: (t.count ?? 1) + 1 } : t)) });
      get().holdToast(same.id, false);
      return;
    }
    const id = toastSeq++;
    let next = [...list, { id, kind, text, details }];
    while (next.length > TOAST_MAX) {
      const old = next.find((t) => t.kind !== "error") ?? next[0];
      next = next.filter((t) => t !== old);
      const tm = toastTimers.get(old.id); if (tm) clearTimeout(tm); toastTimers.delete(old.id);
    }
    set({ toasts: next });
    get().holdToast(id, false);
  },
  holdToast: (id, hold) => {
    const tm = toastTimers.get(id);
    if (tm) clearTimeout(tm);
    toastTimers.delete(id);
    const t = get().toasts.find((x) => x.id === id);
    if (!t || hold) return;
    toastTimers.set(id, setTimeout(() => get().dropToast(id), toastTtl(t)));
  },
  dropToast: (id) => {
    const tm = toastTimers.get(id); if (tm) clearTimeout(tm); toastTimers.delete(id);
    set({ toasts: get().toasts.filter((t) => t.id !== id) });
  },
}));
