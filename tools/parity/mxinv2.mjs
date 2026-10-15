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
const api = async (m, p, b) => (await fetch(BASE + "/api" + p, { method: m, headers: { "Content-Type": "application/json" }, body: b ? JSON.stringify(b) : undefined })).json();
let list = await api("GET", "/projects");
let pr = list.find((p) => p.name === "parity ops");
if (!pr) {
  pr = await api("POST", "/projects", { name: "parity ops" });
  const names = { CS: "ldsp", EL: "kromka", XNC: "x1", CL: "Материал1", SP: "Материал поверхности1", GR: "Пазование1", O: "", LB: "Этикетки: Детали и остатки" };
  for (const t of ["CS", "EL", "XNC", "CL", "SP", "GR", "O", "LB"]) await api("POST", `/projects/${pr.id}/operations`, { type: t, name: names[t] });
}
await page.goto(BASE + "/"); await page.waitForTimeout(1500);
await step("projects", async () => {});
await row("parity ops").dblclick(); await page.waitForTimeout(1800);
await step("products", async () => { await tab("Изделия"); });
await tab("Операции"); await page.waitForTimeout(500);
const IDX = { CS: 0, EL: 1, XNC: 2, CL: 3, SP: 4, GR: 5, O: 6, LB: 7 };
const opRow = (t) => page.locator(`.ag-center-cols-container .ag-row[row-index="${IDX[t]}"]`).first();
const goOp = async (t) => {            // operatsiyalar jadvalida CS qatoridan klaviatura bilan pastga
  await page.locator('.ag-row[row-index="0"] [col-id="type"]').first().click();
  for (let k = 0; k < IDX[t]; k++) { await page.keyboard.press("ArrowDown"); await page.waitForTimeout(250); }
  await page.waitForTimeout(700);
};
await step("cl_params", async () => { await goOp("CL"); await tab("Параметры"); });
await step("cl_parts", async () => { await tab("Детали"); });
await step("sp_main", async () => { await goOp("SP"); });
await step("gr_main", async () => { await goOp("GR"); });
await step("o_main", async () => { await goOp("O"); });
await step("lb_main", async () => { await goOp("LB"); });
await step("menu_print", async () => { await page.locator(".side >> text=Печать отчета").first().click(); });
await step("menu_settings", async () => { await page.keyboard.press("Escape"); await page.waitForTimeout(300); await page.locator(".side-head, .side button, .side div").filter({ hasText: /^\s*Настройки\s*$/ }).first().click({ force: true }); await page.waitForTimeout(600); });
console.log("errors", errs.length, errs.slice(0, 2));
await browser.close();
