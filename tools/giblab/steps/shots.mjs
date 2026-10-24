// Ochiq loyihada ekranlar rasmi: `run shots.mjs <papka> <op1:Varaq1,Varaq2;op2:...>` — operatsiya (tartib raqami) tanlanadi,
// varaqlari birma-bir ochiladi, har biri <papka>/gl_<op>_<varaq>.png. Faqat ko'rish (hech narsa o'zgartirilmaydi).
import path from "node:path";
import fs from "node:fs";
export default async ({ page, drv, args }) => {
  const [dir, spec] = args;
  fs.mkdirSync(dir, { recursive: true });
  const done = [];
  for (const part of spec.split(";").filter(Boolean)) {
    const [op, tabs] = part.split(":");
    await drv.selectOperation(Number(op));
    await page.waitForTimeout(1200);
    for (const t of (tabs || "").split(",").filter(Boolean)) {
      if (t !== "-") { await drv.tab(t); await page.waitForTimeout(1800); }
      const f = path.join(dir, `gl_${op}_${t.replace(/[^\wа-яА-Я]+/g, "_")}.png`);
      await page.bringToFront().catch(() => {});
      await page.screenshot({ path: f, timeout: 180_000 });
      done.push(f);
    }
  }
  return done;
};
