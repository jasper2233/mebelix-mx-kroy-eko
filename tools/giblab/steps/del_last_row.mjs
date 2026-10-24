// Ochiq detallar jadvalidagi oxirgi (sinovda qo'shilgan, o'lchamsiz) qatorni o'chirish — faqat Д-на = Ш-на = 0 bo'lsa.
export default async ({ page }) => {
  const fr = page.mainFrame();
  const pos = await fr.evaluate(() => {
    const rows = [...document.querySelectorAll("tr")].filter((r) => r.cells.length > 8 && r.getBoundingClientRect().height > 0 && /^\d+'?$/.test((r.cells[0].innerText || "").trim()));
    const r = rows[rows.length - 1]; const t = (r.innerText || "").replace(/\s+/g, " ").trim();
    if (!/^\d+ 0 0 1/.test(t)) return { skip: t };
    const c = r.cells[0].getBoundingClientRect(); return { x: c.x + c.width / 2, y: c.y + c.height / 2, t };
  });
  if (pos.skip) return pos;
  await page.mouse.click(pos.x, pos.y); await page.waitForTimeout(500);
  await page.keyboard.press("Delete"); await page.waitForTimeout(1500);
  const after = await fr.evaluate(() => [...document.querySelectorAll("tr")].filter((r) => r.cells.length > 8 && r.getBoundingClientRect().height > 0 && /^\d+'?$/.test((r.cells[0].innerText || "").trim())).map((r) => (r.innerText || "").replace(/\s+/g, " ").slice(0, 30)).slice(-3));
  const dlg = await fr.evaluate(() => [...document.querySelectorAll(".gwt-DialogBox")].filter((d) => d.getBoundingClientRect().height > 0).map((d) => d.innerText.slice(0, 120)));
  return { clicked: pos.t, after, dlg };
};
