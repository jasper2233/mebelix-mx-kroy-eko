// Detallar jadvali (pastki panel ochiq, jadval tepada): ekran koordinatalari bilan belgilash va har qadam rasmi. Faqat belgilash / fokus.
//   run sel_probe2.mjs <papka>
import path from "node:path";
export default async ({ page, drv, args }) => {
  const [dir] = args;
  const y = (row) => 428 + 20 * (row - 1);       // 1-qator markazi (1904×945 oynada)
  const X = 600;
  const cdp = await page.context().newCDPSession(page);
  const fs = await import("node:fs");
  const shot = async (n) => {
    const r = await cdp.send("Page.captureScreenshot", { format: "png", clip: { x: 220, y: 395, width: 900, height: 330, scale: 1 } });
    fs.writeFileSync(path.join(dir, `s_${n}.png`), Buffer.from(r.data, "base64"));
  };
  const click = async (row, mods = []) => {
    for (const m of mods) await page.keyboard.down(m);
    await page.mouse.click(X, y(row));
    for (const m of [...mods].reverse()) await page.keyboard.up(m);
    await page.waitForTimeout(800);
  };
  await click(2); await shot("1_click2");
  await click(5, ["Shift"]); await shot("2_shift5");
  await click(8, ["Control"]); await shot("3_ctrl8");
  await click(10, ["Shift", "Control"]); await shot("4_shiftctrl10");
  await click(3); await shot("5_click3");
  await page.keyboard.press("Shift+ArrowDown"); await page.waitForTimeout(500);
  await page.keyboard.press("Shift+ArrowDown"); await page.waitForTimeout(500); await shot("6_shiftdown2");
  await page.keyboard.press("Shift+ArrowUp"); await page.waitForTimeout(500); await shot("7_shiftup");
  await click(12, ["Control"]); await shot("8_ctrl12");
  await click(12, ["Control"]); await shot("9_ctrl12_again");
  return "ok";
};
