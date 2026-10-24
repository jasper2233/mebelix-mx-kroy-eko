// Menyu bandini bosib ochilgan oynani rasmga olish va yopish (faqat ko'rish): run dialog_shot.mjs <rasm.png> "<menyu matni>" ["<yopish tugmasi>"]
// Yopish: berilgan tugma (masalan «Отмена» / «Закрыть»), bo'lmasa oyna sarlavhasidagi X.
export default async ({ page, drv, args }) => {
  const [out, item, close = "Отмена"] = args;
  if (item.startsWith("tab:")) { await drv.tab(item.slice(4)); }
  else if (!(await drv.clickText(item))) return `topilmadi: ${item}`;
  await page.waitForTimeout(2500);
  await page.bringToFront().catch(() => {});
  await page.screenshot({ path: out, timeout: 180_000 });
  const dlg = await drv.gl("dialogs()");
  if (!item.startsWith("tab:")) {
    if (!(await drv.gl(`dialogButton(${JSON.stringify(close)})`))) await page.keyboard.press("Escape");
    await page.waitForTimeout(800);
  }
  return { out, dialogs: dlg };
};
