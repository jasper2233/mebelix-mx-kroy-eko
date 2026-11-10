// Ochiq onlayn loyihada (faqat sinov papkasida — drayver tekshiradi) berilgan operatsiyani «Раскроить» va ko'rsatkichlarni qaytaradi.
//   GIBLAB_ALLOW_WRITE=1 node tools/giblab/gl.mjs run tools/giblab/steps/cut_op_stats.mjs <op raqami> [--nocut]
export default async ({ page, drv, args }) => {
  const n = Number(args[0] || 1);
  await drv.selectOperation(n);
  await page.waitForTimeout(1500);
  const st = args[1] === "--nocut" ? await drv.cuttingStats() : await drv.cut();
  return { op: n, ...st, raw: (st.raw || []).slice(0, 40) };
};
