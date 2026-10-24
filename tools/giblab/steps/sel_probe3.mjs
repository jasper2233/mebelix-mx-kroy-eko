// Detallar jadvali («Д-на» sarlavhali jadval) — qator belgilash: oddiy, Shift, Ctrl, Shift+Ctrl bosish, Shift+strelka, Ctrl bilan
// qayta bosish; har qadamdan keyin belgilangan qatorlar (fon rangi) va fokus. Faqat belgilash — hech narsa o'zgartirilmaydi.
//   run sel_probe3.mjs <papka> [sarlavha katagi matni = «Д-на»] [nom prefiksi = «p»]
import fs from "node:fs";
import path from "node:path";
export default async ({ page, args }) => {
  const [dir, head = "Д-на", pre = "p"] = args;
  const cdp = await page.context().newCDPSession(page);
  const shot = async (n) => {
    const r = await cdp.send("Page.captureScreenshot", { format: "png" });
    fs.writeFileSync(path.join(dir, `${pre}_${n}.png`), Buffer.from(r.data, "base64"));
  };
  const info = () => page.evaluate((head) => {
    const hdr = [...document.querySelectorAll("tr")].find((r) => [...r.cells].some((c) => (c.innerText || "").trim() === head)
      && r.getBoundingClientRect().height > 0);
    if (!hdr) return { err: "no header" };
    const top = hdr.getBoundingClientRect().bottom;
    const left = hdr.getBoundingClientRect().left, right = hdr.getBoundingClientRect().right;
    const rows = [...document.querySelectorAll("tr")].filter((r) => {
      const b = r.getBoundingClientRect();
      return b.height > 0 && b.top >= top - 1 && b.top < top + 400 && b.left >= left - 5 && b.right <= right + 5 && r.cells.length >= hdr.cells.length - 1 && r.cells.length > 2 && /^\d+'?$/.test((r.cells[0].innerText || "").trim());
    }).slice(0, 14);
    const bg = rows.map((r) => getComputedStyle(r.cells[1]).backgroundColor);
    const cnt = {}; bg.forEach((b) => { cnt[b] = (cnt[b] || 0) + 1; });
    const common = Object.entries(cnt).sort((a, b) => b[1] - a[1])[0]?.[0];
    return { rows: rows.map((r) => { const b = r.cells[0].getBoundingClientRect(); return { n: (r.cells[0].innerText || "").trim(), x: b.x + b.width / 2, y: b.y + b.height / 2 }; }),
      sel: rows.map((r, i) => (bg[i] !== common ? (r.cells[0].innerText || "").trim() : null)).filter(Boolean), bgs: [...new Set(bg)],
      box: { x: left, y: hdr.getBoundingClientRect().top, w: right - left, h: (rows.length ? rows[rows.length - 1].getBoundingClientRect().bottom : top) - hdr.getBoundingClientRect().top } };
  }, head);
  const i0 = await info();
  if (i0.err) return i0;
  const R = i0.rows;
  if (R.length < 6) return { rows: R.length, note: "kamida 6 qator kerak" };
  const click = async (k, mods = []) => {
    for (const m of mods) await page.keyboard.down(m);
    await page.mouse.click(R[k - 1].x, R[k - 1].y);
    for (const m of [...mods].reverse()) await page.keyboard.up(m);
    await page.waitForTimeout(900);
  };
  const log = [];
  const step = async (name) => { const s = await info(); log.push({ k: name, box: s.box }); await shot(name); };
  await page.keyboard.press("Escape"); await page.waitForTimeout(400);
  await click(1); await step("1_click1");
  await click(3, ["Shift"]); await step("2_shift3");
  await click(5, ["Control"]); await step("3_ctrl5");
  await click(6, ["Shift", "Control"]); await step("4_shiftctrl6");
  await click(5, ["Control"]); await step("5_ctrl5_again");
  await click(2); await step("6_click2");
  await page.keyboard.press("Shift+ArrowDown"); await page.waitForTimeout(600);
  await page.keyboard.press("Shift+ArrowDown"); await page.waitForTimeout(600); await step("7_shiftdown2");
  await page.keyboard.press("Shift+ArrowUp"); await page.waitForTimeout(600); await step("8_shiftup");
  await page.keyboard.press("ArrowDown"); await page.waitForTimeout(600); await step("9_down");
  await page.keyboard.press("Escape");
  return log;
};
