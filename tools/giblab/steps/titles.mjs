// Har panel / varaqdagi ko'rinadigan tugma maslahatlari (title) — MX bilan tugmalar to'liqligini solishtirish uchun (faqat ko'rish).
//   run titles.mjs <chiqish.json> "<op:Varaq1,Varaq2;op:->"     (op — operatsiya raqami; «-» — varaqni bosmasdan)
import fs from "node:fs";
export default async ({ page, drv, args }) => {
  const [out, spec] = args;
  const res = {};
  const grab = () => drv.evaluate(`[...new Set([...document.querySelectorAll("[title]")].filter((e) => { const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.x > 215 && r.y >= 0 && r.y < innerHeight; }).map((e) => e.title.trim()).filter(Boolean))]`);
  for (const part of spec.split(";").filter(Boolean)) {
    const [op, tabs] = part.split(":");
    await drv.selectOperation(Number(op)); await page.waitForTimeout(1200);
    for (const t of (tabs || "-").split(",")) {
      if (t !== "-") { await drv.tab(t); await page.waitForTimeout(1500); }
      const ops = await drv.operations();
      const type = ops?.find((o) => o.n === op)?.type ?? "?";
      res[`${type}:${t}`] = await grab();
    }
  }
  fs.writeFileSync(out, JSON.stringify(res, null, 1));
  return Object.fromEntries(Object.entries(res).map(([k, v]) => [k, v.length]));
};
