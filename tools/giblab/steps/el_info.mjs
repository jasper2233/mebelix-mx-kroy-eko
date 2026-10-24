// EL «Детали» birinchi qatorlari va «Изделия» ro'yxati (faqat o'qish): run el_info.mjs <EL operatsiya raqami>
export default async ({ page, drv, args }) => {
  await drv.selectOperation(Number(args[0]));
  await page.waitForTimeout(1200);
  await drv.tab("Детали");
  await page.waitForTimeout(1500);
  const el = await drv.table(["Товар", "Длина"], 4);
  await drv.tab("Изделия").catch(() => false);
  await page.waitForTimeout(1200);
  const pr = await drv.table(["Код", "Наименование", "Кол"], 10);
  await drv.tab("Операции").catch(() => false);
  return { el: el && el.rows.map((r) => r.cells.slice(0, 3).join(" | ")), products: pr && pr.rows.map((r) => r.cells.slice(0, 4).join(" | ")) };
};
