import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
const require = createRequire("D:/cloude giblab jasur/MebeliX_Kroy/frontend/package.json");
const { chromium } = require("playwright");
const BASE = "http://127.0.0.1:8766";
const browser = await chromium.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe" });
const page = await (await browser.newContext({ viewport: { width: 1568, height: 760 } })).newPage();
const errs = []; page.on("pageerror", (e) => errs.push(e.message));
const inv = async (name) => {
  await page.waitForTimeout(700);
  const out = await page.evaluate(() => {
    const out = [], seen = new Set();
    const add = (k, t) => { t = (t || "").replace(/\s+/g, " ").trim(); if (t.length < 1 || t.length > 120) return; const key = k + "|" + t; if (seen.has(key)) return; seen.add(key); out.push([k, t]); };
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    for (const e of document.querySelectorAll("body *")) {
      if (!vis(e)) continue;
      if (e.title) add("title", e.title);
      const al = e.getAttribute && e.getAttribute("aria-label"); if (al) add("title", al);
      if (e.tagName === "SELECT") { for (const o of e.options) add("option", o.text); continue; }
      if (e.tagName === "INPUT") { if (e.placeholder) add("ph", e.placeholder); add("input", e.type); continue; }
      if (e.childElementCount === 0 && !["OPTION", "SCRIPT", "STYLE"].includes(e.tagName)) add("text", e.textContent);
      else if (!["OPTION", "SCRIPT", "STYLE", "SELECT"].includes(e.tagName))
        for (const n of e.childNodes) if (n.nodeType === 3) add("text", n.textContent);      // ikonka yonidagi matn tugunlari
    }
    return out;
  });
  writeFileSync(`inv/mx/${name}.json`, JSON.stringify(out));
  await page.screenshot({ path: `inv/mx/${name}.png` });
  console.log(name, out.length);
};
const row = (t) => page.locator(".ag-row").filter({ hasText: t }).first();
const tab = async (t) => { await page.locator(".tabs >> text=" + JSON.stringify(t)).first().click(); };
const step = async (name, fn) => { try { await fn(); await inv(name); } catch (e) { console.log("FAIL", name, String(e).slice(0, 160)); } };
await page.goto(BASE + "/"); await page.waitForTimeout(1500);
await step("projects", async () => {});
await row("1000014").dblclick(); await page.waitForTimeout(1800);
await step("cs_params", async () => { await row("LDSP Beliy").click(); await tab("Параметры"); });
await step("cs_parts", async () => { await tab("Детали"); });
await step("cs_sheets", async () => { await tab("Листы и остатки"); });
await step("cs_cut", async () => { await tab("Раскрой"); });
await step("el_main", async () => { await row("KP-1/19-BA").click(); });
await step("xnc_params", async () => { await row("100602_01_001").click(); });
await step("xnc_template", async () => { await tab("Шаблон"); });
await step("xnc_cost", async () => { await tab("Стоимость"); });
await step("products", async () => { await tab("Изделия"); });
await step("dlg_common", async () => { await page.getByText("Общие действия", { exact: true }).first().click(); });
await page.keyboard.press("Escape");
await step("menu_print", async () => { await page.getByText("Печать отчета", { exact: true }).first().click(); });
await step("menu_settings", async () => { await page.getByText("Настройки", { exact: true }).first().click(); });
console.log("errors", errs.length, errs.slice(0, 2));
await browser.close();
