// Varaq yorlig'i sichqoncha bilan bosilgandan keyin TAB fokusi va qator ustidagi hover-oyna (onlayn tizim, faqat o'qish + klaviatura).
//   run tab_start2.mjs <op> <Varaq> [tab soni] <skrin.png>
export default async ({ page, drv, args }) => {
  const [op, tab, n = "4", shot] = args;
  const fr = page.mainFrame();
  await page.keyboard.press("Escape");
  await drv.selectOperation(Number(op)); await page.waitForTimeout(1500);
  const where = () => fr.evaluate(() => {
    const a = document.activeElement; const tr = a?.closest?.("tr"); const td = a?.closest?.("td");
    return `${a?.tagName}.${String(a?.className || "").slice(0, 18)} tr0=${tr ? (tr.cells[0]?.innerText || "").trim().slice(0, 14) : "-"} ci=${td && tr ? [...tr.cells].indexOf(td) : "-"} y=${a ? Math.round(a.getBoundingClientRect().y) : "-"} t=${((a?.value ?? a?.innerText) || "").toString().trim().slice(0, 16)}`;
  });
  const box = await fr.evaluate((label) => { const e = [...document.querySelectorAll("div, td, span")].filter((x) => (x.innerText || "").trim() === label && x.getBoundingClientRect().y > 330 && x.getBoundingClientRect().y < 370 && x.childElementCount < 3).pop();
    const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; }, tab);
  await page.mouse.click(box.x, box.y); await page.waitForTimeout(2500);
  const log = [`click ${await where()}`];
  for (let i = 0; i < Number(n); i++) { await page.keyboard.press("Tab"); await page.waitForTimeout(400); log.push(`tab${i + 1} ${await where()}`); }
  await page.keyboard.press("Escape");
  // qator ustida sichqoncha: title / suzuvchi oyna
  const cell = await fr.evaluate(() => { const r = [...document.querySelectorAll("tr")].filter((x) => x.cells.length > 8 && x.getBoundingClientRect().y > 400 && /^\d+'?$/.test((x.cells[0].innerText || "").trim()))[0];
    const c = r.cells[1].getBoundingClientRect(); return { x: c.x + 30, y: c.y + c.height / 2, title: r.title || r.cells[1].title || "" }; });
  await page.mouse.move(cell.x, cell.y); await page.waitForTimeout(1800);
  if (shot) await page.screenshot({ path: shot, timeout: 120_000 });
  log.push(`hover title="${cell.title.replace(/\s+/g, " ").slice(0, 80)}"`);
  return log;
};
