// Kroy tahriri: detalni o'ng tugma bilan olib tashlash → ro'yxatdan tanlash → Shift ushlab kursorni yurgizish (sharpa) → Ctrl → rasmlar.
// Oxirida «Отмена» (loyiha o'zgarmaydi). run editor_shift.mjs <papka> <olib tashlanadigan x> <y> <bo'sh joy x> <y>
import path from "node:path";
export default async ({ page, drv, args }) => {
  const [dir, rx, ry, fx, fy] = args;
  const shot = async (n) => { await page.screenshot({ path: path.join(dir, n), timeout: 120_000 }); return n; };
  const out = [];
  await page.mouse.click(Number(rx), Number(ry), { button: "right" }); await page.waitForTimeout(1500);
  out.push(await shot("gl_ed1_removed.png"));
  // ro'yxatdagi birinchi qator
  const row = await drv.evaluate(`(() => { const d = [...document.querySelectorAll(".gwt-DialogBox")].pop(); const tr = d && [...d.querySelectorAll("tr")].find((r) => r.cells.length >= 6 && /^\d+$/.test((r.cells[0].innerText || "").trim()) && r.getBoundingClientRect().x < 900);
    if (!tr) return null; const r = tr.getBoundingClientRect(); return { x: r.x + 120, y: r.y + r.height / 2 }; })()`);
  if (row) { await page.mouse.click(row.x, row.y); await page.waitForTimeout(800); }
  out.push(await shot("gl_ed2_selected.png"));
  await page.mouse.move(Number(fx) - 40, Number(fy) - 40);
  await page.keyboard.down("Shift"); await page.waitForTimeout(400);
  await page.mouse.move(Number(fx), Number(fy), { steps: 6 }); await page.waitForTimeout(900);
  out.push(await shot("gl_ed3_shift.png"));
  await page.keyboard.down("Control"); await page.waitForTimeout(600);
  await page.mouse.move(Number(fx) + 3, Number(fy) + 3, { steps: 2 }); await page.waitForTimeout(800);
  out.push(await shot("gl_ed4_shift_ctrl.png"));
  await page.keyboard.up("Control"); await page.keyboard.up("Shift"); await page.waitForTimeout(500);
  await drv.gl(`dialogButton("Отмена")`); await page.waitForTimeout(1500);
  const left = (await drv.gl("dialogs()")).map((d) => d.title);
  return { out, row, left };
};
