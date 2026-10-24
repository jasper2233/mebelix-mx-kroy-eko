// Detallar jadvalida qator belgilash (onlayn tizim): oddiy bosish, Shift+bosish, Ctrl+bosish, Shift+Ctrl+bosish, Shift+strelka;
// bosib turilgan TAB (klaviatura takrori, CDP autoRepeat). Faqat belgilash va fokus — hech narsa o'zgartirilmaydi va o'chirilmaydi.
//   run sel_probe.mjs <papka>
import path from "node:path";
export default async ({ page, args }) => {
  const [dir] = args;
  const fr = page.frames().find((f) => f.url().includes("giblab")) ?? page.mainFrame();
  const rowsSrc = `(() => [...document.querySelectorAll("tr")].filter((r) => r.cells.length > 8 && r.getBoundingClientRect().height > 0 && r.getBoundingClientRect().top > 410 && /^\\d+'?$/.test((r.cells[0].innerText || "").trim())))`;
  const sel = () => fr.evaluate((src) => {
    const rows = eval(src)();
    const bg = rows.map((r) => getComputedStyle(r.cells[2]).backgroundColor + "|" + r.className);
    const cnt = {};
    bg.forEach((b) => { cnt[b] = (cnt[b] || 0) + 1; });
    const common = Object.entries(cnt).sort((a, b) => b[1] - a[1])[0]?.[0];
    const a = document.activeElement, td = a?.closest?.("td"), tr = td?.closest("tr");
    return { n: rows.length, selected: rows.map((r, i) => (bg[i] !== common ? (r.cells[0].innerText || "").trim() : null)).filter(Boolean),
      focus: tr ? `${(tr.cells[0].innerText || "").trim()}:${[...tr.cells].indexOf(td)}` : String(a?.tagName) };
  }, rowsSrc);
  const cell = (i, c = 2) => fr.evaluate(([src, i, c]) => {
    const r = eval(src)()[i]; r.scrollIntoView({ block: "center" }); const b = r.cells[c].getBoundingClientRect();
    return { x: b.x + Math.min(30, b.width / 2), y: b.y + b.height / 2 };
  }, [rowsSrc, i, c]);
  const click = async (i, mods = []) => {
    const p = await cell(i);
    for (const m of mods) await page.keyboard.down(m);
    await page.mouse.click(p.x, p.y);
    for (const m of mods.reverse()) await page.keyboard.up(m);
    await page.waitForTimeout(700);
  };
  const log = [];
  await click(1); log.push({ k: "click r2", ...(await sel()) });
  await click(4, ["Shift"]); log.push({ k: "shift+click r5", ...(await sel()) });
  await click(7, ["Control"]); log.push({ k: "ctrl+click r8", ...(await sel()) });
  await click(9, ["Shift", "Control"]); log.push({ k: "shift+ctrl+click r10", ...(await sel()) });
  await page.screenshot({ path: path.join(dir, "sel_mouse.png") });
  await click(2); log.push({ k: "click r3", ...(await sel()) });
  for (let i = 0; i < 2; i++) { await page.keyboard.press("Shift+ArrowDown"); await page.waitForTimeout(500); }
  log.push({ k: "shift+down x2", ...(await sel()) });
  await page.keyboard.press("Shift+ArrowUp"); await page.waitForTimeout(500);
  log.push({ k: "shift+up", ...(await sel()) });
  await page.keyboard.press("ArrowDown"); await page.waitForTimeout(500);
  log.push({ k: "down", ...(await sel()) });
  await page.screenshot({ path: path.join(dir, "sel_keys.png") });
  // bosib turilgan TAB: birinchi keyDown, keyin 0.5 s kutish, so'ng har 33 ms autoRepeat (≈ OS takrori) — jami 1.6 s
  await click(1);
  const cdp = await page.context().newCDPSession(page);
  const kd = (rep) => cdp.send("Input.dispatchKeyEvent", { type: "rawKeyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9, autoRepeat: rep });
  const trail = [];
  await kd(false); trail.push(["0", (await sel()).focus]);
  await page.waitForTimeout(500);
  for (let t = 0; t < 33; t++) { await kd(true); await page.waitForTimeout(33); if (t % 6 === 0) trail.push([`r${t}`, (await sel()).focus]); }
  await cdp.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
  await page.waitForTimeout(500);
  trail.push(["up", (await sel()).focus]);
  log.push({ k: "hold tab", trail });
  await page.keyboard.press("Escape");
  return log;
};
