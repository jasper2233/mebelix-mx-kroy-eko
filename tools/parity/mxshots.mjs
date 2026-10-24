// MX Kroy: ochiq loyihada ekranlar rasmi (onlayn tizim rasmlari bilan yonma-yon solishtirish uchun, tools/giblab/steps/shots.mjs juftligi).
//   node tools/parity/mxshots.mjs <loyiha id> <papka> "<op1:Varaq1,Varaq2;op2:->" [kenglik x balandlik]
// Faqat ko'rish: operatsiya qatori bosiladi va varaqlar ochiladi, hech narsa o'zgartirilmaydi.
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
const require = createRequire("D:/cloude giblab jasur/MebeliX_Kroy/frontend/package.json");
const { chromium } = require("playwright");
const [pid, dir, spec, size = "1904x945", base = "http://127.0.0.1:8000"] = process.argv.slice(2);
const [w, h] = size.split("x").map(Number);
fs.mkdirSync(dir, { recursive: true });
const browser = await chromium.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe" });
const page = await (await browser.newContext({ viewport: { width: w, height: h } })).newPage();
const errs = []; page.on("pageerror", (e) => errs.push(e.message));
await page.goto(`${base}/#/p/${pid}`); await page.waitForTimeout(2500);
for (const part of spec.split(";").filter(Boolean)) {
  const [op, tabs] = part.split(":");
  await page.locator(`.ops-grid .ag-row[row-index="${Number(op) - 1}"], .ag-row[row-index="${Number(op) - 1}"]`).first().click();
  await page.waitForTimeout(1200);
  for (const t of (tabs || "").split(",").filter(Boolean)) {
    if (t !== "-") { await page.locator(".tabs button, .tabs [role=tab], .tabs .tab").filter({ hasText: t }).first().click(); await page.waitForTimeout(1500); }
    const f = path.join(dir, `mx_${op}_${t.replace(/[^\wа-яА-Я]+/g, "_")}.png`);
    await page.screenshot({ path: f });
    console.log(f);
  }
}
if (errs.length) console.log("pageerror:", errs);
await browser.close();
