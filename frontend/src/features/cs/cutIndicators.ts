// Kroy holat qatori ko'rsatkichlari (Ctrl+P da yoqiladi / o'chiriladi): karta qiymati / umumiy. «Раскрой» va
// «Редактирование раскроя» oynalari uchun umumiy.
import type { CutMap, CuttingResult } from "../../api/types";
import { fmt } from "../../shared/ui";

export const INDICATORS = ["num", "S", "C", "Cp", "LT", "F", "R", "CT", "T", "AP", "AM", "AW"];
export const IND_DEFAULT = ["num", "S", "C", "Cp", "LT", "F"];
/** «Ш-на» standart qiymatlari (onlayn «Настройки» oynasidagi kabi) — holat qatorida katakning nisbiy kengligi. */
export const IND_WIDTH: Record<string, number> = { num: 10, S: 15, C: 12, Cp: 15, LT: 15, F: 16, R: 16, CT: 14, T: 12, AP: 16, AM: 16, AW: 16 };

/** Foydalanuvchi tartibi (▲▼) + yangi / tushib qolgan ko'rsatkichlar oxirida. */
export function indOrder(order: string[]): string[] {
  return [...new Set([...order.filter((k) => INDICATORS.includes(k)), ...INDICATORS])];
}

/** Holat qatorida ko'rinadigan ko'rsatkichlar — «Настройки» tartibida. */
export function shownIndicators(s: { cutIndicators: string[]; cutIndOrder: string[] }): string[] {
  return indOrder(s.cutIndOrder).filter((k) => s.cutIndicators.includes(k));
}

export const indWidth = (k: string, w: Record<string, number>) => (w[k] > 0 ? w[k] : IND_WIDTH[k] ?? 12);

export function indicator(k: string, m: CutMap, res: CuttingResult, nMaps: number): string {
  const waste = (sheet: number, parts: number, bus: number) => (sheet > 0 ? (100 * (sheet - parts - bus)) / sheet : 0);
  switch (k) {
    case "num": return `${m.index}/${nMaps}`;
    case "S": return `${fmt(m.sheet_length)}/${fmt(m.sheet_width)}`;
    case "C": return `${m.copies}/${res.total_sheets}`;
    case "Cp": return `${m.parts_count}/${res.total_parts}`;
    case "LT": return `${fmt(m.cut_length_m)}/${fmt(res.total_cut_length_m)}`;
    case "F": return `${fmt(m.fill_percent)}%/${fmt(res.total_fill_percent)}%`;
    case "R": return `${fmt(waste(m.sheet_area_m2, m.parts_area_m2, m.remnant_area_m2))}%/${fmt(
      waste(res.material_area_m2, res.parts_area_m2, res.remnant_area_m2))}%`;
    case "CT": return `${m.cuts_count}/${res.total_cuts}`;
    case "T": {
      const tr = m.commands.filter((c) => c.code === "T");
      return `${fmt(tr.find((c) => c.level === 1)?.size ?? 0)}/${fmt(tr.find((c) => c.level === 2)?.size ?? 0)}`;
    }
    case "AP": return `${fmt(m.parts_area_m2, 3)}/${fmt(res.parts_area_m2, 3)}`;
    case "AM": return `${fmt(m.sheet_area_m2, 3)}/${fmt(res.material_area_m2, 3)}`;
    case "AW": return `${fmt(m.remnant_area_m2, 3)}/${fmt(res.remnant_area_m2, 3)}`;
    default: return "";
  }
}
