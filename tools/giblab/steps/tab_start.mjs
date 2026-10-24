// Varaq ochilgandan keyin TAB fokusi qayerdan boshlanadi (onlayn tizim, faqat klaviatura — qiymat kiritilmaydi, oxirida Escape).
//   run tab_start.mjs "<op:Varaq;op:Varaq>" [tab soni]
export default async ({ page, drv, args }) => {
  const [spec, n = "3"] = args;
  const fr = page.mainFrame();
  const where = () => fr.evaluate(() => {
    const a = document.activeElement; const tr = a?.closest?.("tr"); const td = a?.closest?.("td");
    return `${a?.tagName}.${String(a?.className || "").slice(0, 20)} row=${tr ? (tr.cells[0]?.innerText || "").trim().slice(0, 12) : "-"} col=${td && tr ? [...tr.cells].indexOf(td) : "-"} txt=${((a?.value ?? a?.innerText) || "").toString().trim().slice(0, 20)}`;
  });
  const out = {};
  for (const part of spec.split(";").filter(Boolean)) {
    const [op, tab] = part.split(":");
    await drv.selectOperation(Number(op)); await page.waitForTimeout(1500);
    if (tab && tab !== "-") { await drv.tab(tab); await page.waitForTimeout(2500); }
    const log = [`open ${await where()}`];
    for (let i = 0; i < Number(n); i++) { await page.keyboard.press("Tab"); await page.waitForTimeout(400); log.push(`tab${i + 1} ${await where()}`); }
    await page.keyboard.press("Escape"); await page.waitForTimeout(300);
    out[part] = log;
  }
  return out;
};
