// «Раскрой» → «Редактирование раскроя» oynasini ochish va rasm (o'zgartirmaydi): run editor_open.mjs <op> <rasm.png>
export default async ({ page, drv, args }) => {
  await drv.selectOperation(Number(args[0])); await page.waitForTimeout(1200);
  await drv.tab("Раскрой"); await page.waitForTimeout(2500);
  const b = await drv.evaluate(`(() => { const e = [...document.querySelectorAll("[title]")].filter((x) => x.title === "Редактирование раскроя" && x.getBoundingClientRect().width > 0 && x.getBoundingClientRect().y > 0).pop();
    if (!e) return null; const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; })()`);
  if (!b) return "tugma yo'q";
  await drv.clickXY(b.x, b.y); await page.waitForTimeout(3000);
  await page.bringToFront().catch(() => {});
  await page.screenshot({ path: args[1], timeout: 120_000 });
  const canv = await drv.evaluate(`[...document.querySelectorAll("canvas")].filter((c) => c.getBoundingClientRect().width > 300).map((c) => { const r = c.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })`);
  return { canv, dialogs: (await drv.gl("dialogs()")).map((d) => d.title) };
};
