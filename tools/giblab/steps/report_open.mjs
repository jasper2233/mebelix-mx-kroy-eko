// «Печать отчета»: ochish («Кодирование» so'rovi chiqsa — «Отмена»), hisobot yuklanguncha kutish (≤ 6 daqiqa), rasm. Faqat ko'rish.
//   run report_open.mjs <rasm.png>
export default async ({ page, drv, args }) => {
  await drv.clickText("Печать отчета");
  for (let k = 0; k < 10; k++) {
    await page.waitForTimeout(1000);
    const d = await drv.gl("dialogs()");
    if (d.some((x) => /Кодирование/.test(x.title))) { await drv.gl(`dialogButton("Отмена")`); break; }
  }
  const t0 = Date.now();
  let ok = false;
  while (Date.now() - t0 < 360_000) {
    await page.waitForTimeout(3000);
    ok = await drv.evaluate(`!!document.querySelector("iframe, embed, object") && location.hash.includes("report")`);
    const busy = await drv.evaluate(`[...document.querySelectorAll("img, div")].some((e) => /loading|wait/i.test(e.className || "") && e.getBoundingClientRect().width > 0)`);
    if (ok && !busy) break;
  }
  await page.waitForTimeout(3000);
  await page.bringToFront().catch(() => {});
  await page.screenshot({ path: args[0], timeout: 180_000 });
  return { ok, s: Math.round((Date.now() - t0) / 1000), frames: await drv.evaluate(`[...document.querySelectorAll("iframe, embed, object")].map((e) => (e.src || e.data || "").slice(0, 80))`) };
};
