// «Справка» holati: tanlangan bo'lim va sakrash uchun langar (anchor). Panellardagi «?» tugmalari shu orqali kerakli bandni ochadi.
import { create } from "zustand";
import { useUI } from "../../store/ui";

export type HelpTopic = "keys" | "flow" | "cut" | "editor" | "cl" | "edge" | "el" | "gr" | "o" | "lb" | "remnants" | "expr" | "machines" | "mes"
  | "whatsnew" | "about";
export const HELP_TOPICS: HelpTopic[] = ["keys", "flow", "cut", "editor", "cl", "edge", "el", "gr", "o", "lb", "remnants", "expr", "machines", "mes",
  "whatsnew", "about"];

interface HelpState {
  topic: HelpTopic;
  anchor: string | null;
  set: (t: HelpTopic) => void;
  clearAnchor: () => void;
}

export const useHelp = create<HelpState>((set) => ({
  topic: "keys",
  anchor: null,
  set: (topic) => set({ topic, anchor: null }),
  clearAnchor: () => set({ anchor: null }),
}));

/** «Справка» oynasini ochadi: bo'lim va (ixtiyoriy) shu bo'limdagi band langari (`id`). */
export function openHelp(topic: HelpTopic, anchor?: string) {
  useHelp.setState({ topic, anchor: anchor ?? null });
  useUI.getState().set({ helpModal: true });         // «Справка» oynasi (joriy ekran ustida)
}

/** Parametr yordami ro'yxati: id → yorliq kaliti (nomi) — yordam bo'limi va panel «?» tugmalari uchun umumiy. */
export const EL_HELP: { id: string; label: string }[] = [
  { id: "count_material", label: "el.p.count_material" }, { id: "width", label: "el.p.width" }, { id: "thickness", label: "el.p.thickness" },
  { id: "jointing", label: "el.p.jointing" }, { id: "waste", label: "el.p.waste" }, { id: "overhang", label: "el.p.overhang" },
  { id: "min_glue", label: "el.p.min_glue" }, { id: "symbol", label: "el.p.symbol" }, { id: "color", label: "el.p.color" },
  { id: "lines", label: "el.p.lines" }, { id: "min_perp", label: "el.p.min_perp" }, { id: "price", label: "el.p.price" },
  { id: "mat_round", label: "el.p.mat_round" }, { id: "mat_len", label: "el.p.mat_len" }, { id: "mat_cost", label: "el.p.mat_cost" },
  { id: "op_price", label: "el.p.op_price" }, { id: "work_round", label: "el.p.work_round" }, { id: "work_len", label: "el.p.work_len" },
  { id: "op_cost", label: "el.p.op_cost" }, { id: "cost", label: "el.p.cost" },
];

export const GR_HELP: { id: string; label: string }[] = [
  { id: "width", label: "gr.p.width" }, { id: "depth", label: "gr.p.depth" }, { id: "offset", label: "gr.p.offset" },
  { id: "offset_incl", label: "gr.p.offset_incl" }, { id: "saw", label: "gr.p.saw" }, { id: "price", label: "gr.p.price" },
  { id: "usage", label: "gr.p.usage" }, { id: "passes", label: "gr.p.passes" }, { id: "cut", label: "gr.p.cut" }, { id: "cost", label: "gr.p.cost" },
];
