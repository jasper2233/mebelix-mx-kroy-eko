// Interfeys holati (Zustand). Server ma'lumotlari — TanStack Query da.
import { create } from "zustand";

export type View = "main" | "print" | "settings" | "help" | "workshop";
export type Section = "lang" | "project" | "print" | "settings" | "help";
export type CsTab = "params" | "parts" | "sheets" | "cut";
export type ElTab = "params" | "parts";
export type XncTab = "params" | "program" | "cost";

export interface Toast { id: number; kind: "info" | "ok" | "error"; text: string; details?: string[] }

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
  showCommands: boolean;          // Раскрой: miniatyuralar ↔ buyruqlar jadvali
  editorOpen: boolean;
  zeroFilter: boolean;            // Ctrl+F — nol sonlilarni yashirish (Изделия)
  toasts: Toast[];
  set: (p: Partial<UI>) => void;
  openProject: (id: string | null) => void;
  setLang: (l: "ru" | "uz") => void;
  toast: (text: string, kind?: Toast["kind"], details?: string[]) => void;
  dropToast: (id: number) => void;
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
  topHeight: load("mxk_top_h", 210),
  columnProfile: load("mxk_col_profile", null),
  showCommands: false,
  editorOpen: false,
  zeroFilter: false,
  toasts: [],
  set: (p) => {
    set(p);
    if (p.topHeight !== undefined) save("mxk_top_h", p.topHeight);
    if (p.folderId !== undefined) save("mxk_folder", p.folderId);
    if (p.csTab !== undefined) save("mxk_cs_tab", p.csTab);
    if (p.columnProfile !== undefined) save("mxk_col_profile", p.columnProfile);
  },
  openProject: (id) => {
    save("mxk_project", id);
    set({ projectId: id, opId: null, productId: null, partSel: [], mapIndex: 1, view: "main", section: "project",
          editorOpen: false });
  },
  setLang: (l) => {
    save("mxk_lang", l);
    set({ lang: l });
  },
  toast: (text, kind = "info", details) => {
    const id = toastSeq++;
    set({ toasts: [...get().toasts, { id, kind, text, details }] });
    setTimeout(() => get().dropToast(id), kind === "error" ? 9000 : 3500);
  },
  dropToast: (id) => set({ toasts: get().toasts.filter((t) => t.id !== id) }),
}));
