// Operatsiya jadvalining «Настройки» (ustunlar) oynasidagi qiymatlarni o'qish va «Отмена» bilan yopish (faqat o'qish).
//   run colset.mjs <operatsiya raqami> [varaq nomi]
export default async ({ page, drv, args }) => {
  await drv.selectOperation(Number(args[0]));
  await page.waitForTimeout(1200);
  if (args[1]) { await drv.tab(args[1]); await page.waitForTimeout(1500); }
  // faqat haqiqatan ko'rinib turgan tugma (yashirin panellardagi nusxalar emas): markazidagi element — tugmaning o'zi
  const btns = await drv.evaluate(`[...document.querySelectorAll("[title]")].filter((x) => x.title === "Настройки [CTRL]+[P]").map((e) => {
    const r = e.getBoundingClientRect(); if (!r.width || r.y < 0 || r.y > innerHeight) return null;
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2, at = document.elementFromPoint(cx, cy);
    return at && (at === e || e.contains(at) || at.contains(e)) ? { x: cx, y: cy } : null; }).filter(Boolean)`);
  const out = [];
  for (const b of btns) {
    await drv.clickXY(b.x, b.y);
    await page.waitForTimeout(1500);
    const t = await drv.table(["Вкл", "Имя", "Описание"], 80);
    out.push({ at: [Math.round(b.x), Math.round(b.y)], rows: t ? t.rows.map((r) => r.cells.filter(Boolean).slice(1).join(" | ")) : [] });
    await drv.clickText("Отмена");
    await page.waitForTimeout(800);
  }
  return out;
};
