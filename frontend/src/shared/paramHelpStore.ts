// Parametr yonidagi «?» va F1: qaysi parametr yordami ochiq / qaysi parametr fokusda (CS-048).
import { create } from "zustand";

export const useParamHelp = create<{ key: string | null; open: (key: string) => void; close: () => void }>((set) => ({
  key: null, open: (key) => set({ key }), close: () => set({ key: null }),
}));

// Fokusdagi parametr (Field `help` bilan): F1 bosilganda shu parametrning yordami ochiladi.
let focused: string | null = null;

export function setFocusedParam(key: string | null) {
  focused = key;
}

/** F1: fokusdagi parametr bo'lsa uning yordamini ochadi (true), aks holda false — umumiy «Справка». */
export function openFocusedParamHelp(): boolean {
  if (!focused) return false;
  useParamHelp.getState().open(focused);
  return true;
}
