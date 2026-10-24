// Detal «XNC Редактор» oynasi: asboblar panelidagi tugmalarni sinash (dastur qatorlari oldin/keyin), har biridan keyin «Отменить»;
// oxirida oyna «Отмена» bilan yopiladi (loyiha o'zgarmaydi). run xnc_tools_probe.mjs <papka> <op> <detal qatori №>
import path from "node:path";
export default async ({ page, drv, args }) => {
  const [dir, op, rowN] = args;
  const shot = (n) => page.screenshot({ path: path.join(dir, n), timeout: 120_000 });
  await drv.selectOperation(Number(op)); await page.waitForTimeout(1000);
  await drv.tab("Детали"); await page.waitForTimeout(1500);
  const row = await drv.evaluate(`(() => { const tr = [...document.querySelectorAll("tr")].find((r) => r.cells.length > 8 && (r.cells[0].innerText || "").trim().replace("'", "") === ${JSON.stringify(rowN)} && r.getBoundingClientRect().height > 0 && r.getBoundingClientRect().y > 380);
    if (!tr) return null; tr.scrollIntoView({ block: "center" }); const r = tr.getBoundingClientRect(); return { x: r.x + 300, y: r.y + r.height / 2 }; })()`);
  if (!row) return "detal qatori topilmadi";
  await page.mouse.click(row.x, row.y); await page.waitForTimeout(600);
  const btn = async (title) => drv.evaluate(`(() => { const e = [...document.querySelectorAll("[title]")].filter((x) => x.title === ${JSON.stringify(title)}).map((e) => { const r = e.getBoundingClientRect();
    if (!r.width || r.y < 0 || r.y > innerHeight) return null; const at = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    return at && (at === e || e.contains(at) || at.contains(e)) ? { x: r.x + r.width / 2, y: r.y + r.height / 2 } : null; }).filter(Boolean).pop(); return e || null; })()`);
  const click = async (title) => { const b = await btn(title); if (!b) return false; await page.mouse.click(b.x, b.y); await page.waitForTimeout(1200); return true; };
  if (!(await click("XNC Редактор"))) return "XNC Редактор tugmasi yo'q";
  await page.waitForTimeout(2000);
  const prog = () => drv.evaluate(`[...document.querySelectorAll("tr.row")].filter((r) => r.querySelector("td.num") && r.getBoundingClientRect().height > 0)
    .map((r) => (r.querySelector("td.cell") || r.cells[1] || {}).innerText.trim())`);
  const titles = await drv.evaluate(`[...[...document.querySelectorAll(".gwt-DialogBox")].pop().querySelectorAll("[title]")].filter((e) => e.getBoundingClientRect().width > 0).map((e) => e.title)`);
  const out = { titles, before: await prog() };
  await shot("xp_0.png");
  // birinchi dastur qatorini tanlash
  const p1 = await drv.evaluate(`(() => { const tr = [...document.querySelectorAll("tr.row")].find((r) => r.querySelector("td.num") && r.getBoundingClientRect().height > 0);
    if (!tr) return null; const r = tr.getBoundingClientRect(); return { x: r.x + 200, y: r.y + r.height / 2 }; })()`);
  if (p1) { await page.mouse.click(p1.x, p1.y); await page.waitForTimeout(600); }
  for (const t of ["Горизонтальное отзеркаливание выделенных элементов с копированием", "Вертикальное отзеркаливание выделенных элементов с копированием",
    "Горизонтальное отзеркаливание", "Вертикальное отзеркаливание", "Обратная сторона"]) {
    const ok = await click(t);
    const after = await prog();
    const head = await drv.evaluate(`[...[...document.querySelectorAll(".gwt-DialogBox")].pop().querySelectorAll("div, td")].map((e) => (e.childElementCount === 0 ? (e.innerText || "").trim() : "")).find((s) => /^DX=/.test(s)) || ""`);
    out[t] = { ok, after, head };
    await shot(`xp_${t.slice(0, 12).replace(/\s+/g, "_")}.png`);
    await click("Отменить [CTRL]+[Z]");
    if (p1) { await page.mouse.click(p1.x, p1.y); await page.waitForTimeout(400); }
  }
  // «Перенос выделенных элементов с копированием» — oyna
  await click("Перенос выделенных элементов с копированием");
  await shot("xp_move.png");
  out.moveDlg = (await drv.gl("dialogs()")).map((d) => ({ t: d.title, text: d.text.slice(0, 400), b: d.buttons }));
  await drv.gl(`dialogButton("Отмена")`); await page.waitForTimeout(800);
  // «Чертеж» varag'i
  const tabs = await drv.gl("tabs()");
  const ch = tabs.find((x) => x.text === "Чертеж");
  if (ch) { await page.mouse.click(ch.r.cx, ch.r.cy); await page.waitForTimeout(2500); await shot("xp_chertezh.png"); }
  // yopish — «Отмена» (o'zgarishlar saqlanmaydi)
  await drv.gl(`dialogButton("Отмена")`); await page.waitForTimeout(1200);
  out.left = (await drv.gl("dialogs()")).map((d) => d.title);
  return out;
};
