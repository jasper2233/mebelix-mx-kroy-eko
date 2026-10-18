// Brauzer transliteratori (src/i18n/translit.ts) va Python manbasi (backend/app/uz_translit.py) mosligi:
// uz.json dagi har bir qiymat TS da o'girilib, Python yaratgan uz-Cyrl.json bilan solishtiriladi.
// Ishga tushirish: `node scripts/check_translit_parity.mjs` (Node ≥ 23 — TypeScript turlarini o'zi olib tashlaydi).
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { toCyrillic } from "../src/i18n/translit.ts";

const rd = (f) => JSON.parse(readFileSync(fileURLToPath(new URL(`../src/i18n/${f}`, import.meta.url)), "utf8"));
const flat = (d, p = "", o = {}) => {
  for (const [k, v] of Object.entries(d)) (v && typeof v === "object") ? flat(v, `${p}${k}.`, o) : (o[`${p}${k}`] = v);
  return o;
};
const uz = flat(rd("uz.json"));
const cy = flat(rd("uz-Cyrl.json"));
let bad = 0, n = 0;
for (const [k, v] of Object.entries(uz)) {
  if (typeof v !== "string") continue;
  n++;
  const got = toCyrillic(v);
  if (got !== cy[k]) {
    bad++;
    if (bad <= 15) console.log(`≠ ${k}\n  py: ${cy[k]}\n  ts: ${got}`);
  }
}
// backend testlaridagi namuna holatlar (tests/fixtures) — kutilgan kirill qiymat bilan
const fx = (f) => JSON.parse(readFileSync(fileURLToPath(new URL(`../../backend/tests/fixtures/${f}`, import.meta.url)), "utf8"));
const cases = [...fx("uz_translit_cases.json"), ...Object.entries(fx("uz_translit_words.json"))];
for (const [src, want] of cases) {
  n++;
  const got = toCyrillic(src);
  if (got !== want) { bad++; console.log(`≠ ${JSON.stringify(src)}\n  kutilgan: ${want}\n  ts: ${got}`); }
}
console.log(`moslik: ${n - bad}/${n}`);
process.exit(bad ? 1 : 0);
