// MX Kroy: har panel / varaqdagi tugma maslahatlari va yozuvlari (onlayn tizim `steps/titles.mjs` juftligi) — faqat ko'rish.
//   node tools/parity/mxtitles.mjs <loyiha id> <chiqish.json> "<op:Varaq1,Varaq2;op:->"
import { createRequire } from "node:module";
import fs from "node:fs";
const require = createRequire("D:/cloude giblab jasur/MebeliX_Kroy/frontend/package.json");
const { chromium } = require("playwright");
const [pid, out, spec] = process.argv.slice(2);
const browser = await chromium.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe" });
const page = await (await browser.newContext({ viewport: { width: 1904, height: 945 } })).newPage();
await page.goto(`http://127.0.0.1:8000/#/p/${pid}`); await page.waitForTimeout(2500);
const res = {};
for (const part of spec.split(";").filter(Boolean)) {
  const [op, tabs] = part.split(":");
  await page.locator(`.ag-row[row-index="${Number(op) - 1}"]`).first().click(); await page.waitForTimeout(1200);
  for (const t of (tabs || "-").split(",")) {
    if (t !== "-") { await page.locator(".tabs button, .tabs [role=tab]").filter({ hasText: t }).first().click(); await page.waitForTimeout(1500); }
    const type = await page.evaluate((i) => document.querySelector(`.ag-row[row-index="${i}"] [col-id="type"]`)?.textContent?.trim() ?? "?", Number(op) - 1);
    res[`${type}:${t}`] = await page.evaluate(() => [...new Set([...document.querySelectorAll("[title], [aria-label], button, th, .ag-header-cell-text, label, .field-label")]
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.x > 215 && r.y >= 0 && r.y < innerHeight; })
      .flatMap((e) => [e.getAttribute("title"), e.getAttribute("aria-label"), e.childElementCount < 3 ? e.textContent : null])
      .map((s) => (s || "").trim()).filter(Boolean))]);
  }
}
fs.writeFileSync(out, JSON.stringify(res, null, 1));
console.log(Object.fromEntries(Object.entries(res).map(([k, v]) => [k, v.length])));
await browser.close();
