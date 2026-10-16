// Sana yordamchilari: hafta kunining qisqa nomi (ru — «пн … вс», uz — «Du … Ya»).
// Brauzerda `uz-Latn` uchun hafta kunlari ma'lumoti yo'q (inglizchaga tushib ketadi), shuning uchun o'zimizning jadval.

const WD_RU = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"];       // Date.getDay(): 0 — yakshanba
const WD_UZ = ["Ya", "Du", "Se", "Ch", "Pa", "Ju", "Sh"];

/** ISO sana (yyyy-mm-dd…) → mahalliy sana obyekti (vaqt zonasi siljishisiz) yoki null. */
export function parseIsoDate(iso: string | undefined): Date | null {
  if (!iso) return null;
  const d = new Date(`${iso.slice(0, 10)}T00:00:00`);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** Hafta kuni qisqa nomi: «чт» (ru) / «Pa» (uz). */
export function weekdayShort(d: Date, lang: string): string {
  return (lang === "uz" ? WD_UZ : WD_RU)[d.getDay()];
}

/** «чт 16.07.2026» / «Pa 16.07.2026» — hafta kuni + kun.oy.yil (xodimlarga tanish ko'rinish). */
export function fmtDateWd(iso: string | undefined, lang: string): string {
  if (!iso) return "";
  const d = parseIsoDate(iso);
  if (!d) return iso;
  const p2 = (n: number) => String(n).padStart(2, "0");
  return `${weekdayShort(d, lang)} ${p2(d.getDate())}.${p2(d.getMonth() + 1)}.${d.getFullYear()}`;
}
