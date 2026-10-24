// Operatsiya detallari qatorlari soni (faqat o'qish). run op_rows.mjs <op>
export default async ({ page, drv, args }) => {
  await drv.selectOperation(Number(args[0])); await page.waitForTimeout(2500);
  return drv.evaluate(`[...document.querySelectorAll("tr")].filter((r) => r.cells.length > 8 && r.getBoundingClientRect().height > 0 && r.getBoundingClientRect().y > 400 && /^\d+'?$/.test((r.cells[0].innerText || "").trim())).map((r) => (r.innerText || "").replace(/\s+/g, " ").slice(0, 40))`);
};
