// Yuqori panel varaqlari: «Операции | Изделия | Остатки: приход | Остатки: расход» (oxirgi ikkisi — 2026-10-24, RemnantTabs.tsx).
export type TopTab = "ops" | "products" | "rem_in" | "rem_out";

export const topTabs = (t: (k: string) => string): { key: TopTab; label: string; testid: string }[] => [
  { key: "ops", label: t("ops.tab"), testid: "tab-ops" },
  { key: "products", label: t("products.tab"), testid: "tab-products" },
  { key: "rem_in", label: t("rt.tab_in"), testid: "tab-rem-in" },
  { key: "rem_out", label: t("rt.tab_out"), testid: "tab-rem-out" },
];
