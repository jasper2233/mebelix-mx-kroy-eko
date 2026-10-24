// Detallar jadvalida TAB / Shift+TAB xatti-harakati (onlayn tizim): har bosishdan keyin fokusdagi katak va qatorlar soni (faqat o'qish + klaviatura).
//   run tab_probe.mjs <papka> <tab soni> [shift+tab soni]
import path from "node:path";
export default async ({ page, args }) => {
  const [dir, nTab, nBack = "3"] = args;
  const fr = page.frames().find((f) => f.url().includes("giblab")) ?? page.mainFrame();
  const rowsOf = () => [...document.querySelectorAll("tr")].filter((r) => r.cells.length > 8 && r.getBoundingClientRect().height > 0 && /^\d+'?$/.test((r.cells[0].innerText || "").trim()));
  const state = () => fr.evaluate((src) => {
    const rowsOf = eval(src);
    const rows = rowsOf();
    const hdr = [...document.querySelectorAll("tr")].find((r) => r.cells.length > 8 && (r.cells[0].innerText || "").trim() === "№" && r.getBoundingClientRect().height > 0);
    const a = document.activeElement;
    let td = a && a.closest ? a.closest("td") : null;
    if (!td || !rows.includes(td.closest("tr"))) td = rows.flatMap((r) => [...r.cells]).find((c) => /select|focus|current|edit/i.test(c.className + " " + (c.firstElementChild?.className || ""))) || td;
    const tr = td && td.closest("tr");
    const ci = td && tr ? [...tr.cells].indexOf(td) : -1;
    return { rows: rows.length, active: a ? `${a.tagName}.${String(a.className).slice(0, 25)}` : "", row: tr ? (tr.cells[0].innerText || "").trim() : "",
      col: hdr && ci >= 0 ? (hdr.cells[ci]?.innerText || "").trim() : ci, val: td ? (a?.value ?? td.innerText ?? "").toString().trim().slice(0, 20) : "" };
  }, `(${rowsOf.toString()})`);
  const pos = await fr.evaluate((src) => { const rows = eval(src)(); const r = rows[rows.length - 1]; r.scrollIntoView({ block: "center" });
    const c = r.cells[1].getBoundingClientRect(); return { x: c.x + 20, y: c.y + c.height / 2, n: rows.length }; }, `(${rowsOf.toString()})`);
  await page.mouse.click(pos.x, pos.y); await page.waitForTimeout(600);
  const log = [{ k: "click", ...(await state()) }];
  for (let i = 0; i < Number(nTab); i++) { await page.keyboard.press("Tab"); await page.waitForTimeout(500); log.push({ k: `tab${i + 1}`, ...(await state()) }); }
  await page.screenshot({ path: path.join(dir, "tab_end.png"), timeout: 120_000 });
  for (let i = 0; i < Number(nBack); i++) { await page.keyboard.press("Shift+Tab"); await page.waitForTimeout(500); log.push({ k: `stab${i + 1}`, ...(await state()) }); }
  return log;
};
