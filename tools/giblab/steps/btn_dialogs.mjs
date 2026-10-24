// Operatsiya varag'idagi tugmalar (title bo'yicha) ochadigan oynalarni rasmga olish va «Отмена» bilan yopish (faqat ko'rish).
//   run btn_dialogs.mjs <papka> <operatsiya> <varaq> "<title1|title2|…>"   — birinchi qator oldindan tanlanadi
import path from "node:path";
export default async ({ page, drv, args }) => {
  const [dir, op, tab, titles] = args;
  await drv.selectOperation(Number(op)); await page.waitForTimeout(1200);
  await drv.tab(tab); await page.waitForTimeout(1500);
  const out = [];
  for (const title of titles.split("|")) {
    const b = await drv.evaluate(`(() => { const e = [...document.querySelectorAll("[title]")].filter((x) => x.title === ${JSON.stringify(title)}).map((e) => {
      const r = e.getBoundingClientRect(); if (!r.width || r.y < 0 || r.y > innerHeight) return null; const at = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
      return at && (at === e || e.contains(at) || at.contains(e)) ? { x: r.x + r.width / 2, y: r.y + r.height / 2 } : null; }).filter(Boolean).pop(); return e || null; })()`);
    if (!b) { out.push({ title, err: "tugma topilmadi" }); continue; }
    await drv.clickXY(b.x, b.y); await page.waitForTimeout(1800);
    const f = path.join(dir, `gl_${title.replace(/[^\wа-яА-Я]+/g, "_").slice(0, 40)}.png`);
    await page.bringToFront().catch(() => {});
    await page.screenshot({ path: f, timeout: 120_000 });
    const d = await drv.gl("dialogs()");
    out.push({ title, file: f, dialog: d.map((x) => x.title) });
    if (!(await drv.gl(`dialogButton("Отмена")`))) await drv.gl(`dialogButton("Закрыть")`);
    await page.waitForTimeout(800);
  }
  return out;
};
