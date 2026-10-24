// XNC dasturlar kodlari noyobligi: stanok fayl nomlari to'qnashmasligi uchun (Общие действия → Перекодировать XNC).
import type { Project } from "../../api/types";

/** Oldingi XNC operatsiyalar bilan bir xil (bo'sh bo'lmagan) kodli XNC operatsiyalar soni. */
export function xncDuplicates(p: Project): number {
  const seen = new Set<string>();
  let n = 0;
  for (const o of p.operations) {
    if (o.type !== "XNC" || !o.code) continue;
    if (seen.has(o.code)) n++;
    else seen.add(o.code);
  }
  return n;
}

/** Kodi bo'sh XNC operatsiyalari soni (onlayn tizim hisobotdan oldin: «Обнаружена XNC операция с пустым кодом!»). */
export function xncEmptyCodes(p: Project): number {
  return p.operations.filter((o) => o.type === "XNC" && !(o.code ?? "").trim()).length;
}
