// Bosib turilgan TAB bilan qatorlar qo'shilganda (tunneldagidek 500 ms server kechikishi) — ko'k qator kursor bilan birga yuradi
// (foydalanuvchi skrini 2026-10-21: kursor 19-qatorda, ko'k fon 9-qatorda qolib ketgan).
import { expect, test } from "@playwright/test";

test("TAB bosib turilganda ko'k qator kursordan qolmaydi", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "SYNC" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`,
    { data: Array.from({ length: 17 }, (_, i) => ({ name: "", length: 600 + i, width: 300, qty: 1 })) });
  await page.route("**/operations/*/parts**", async (route) => {
    if (route.request().method() === "POST") await new Promise((r) => setTimeout(r, 500));
    await route.continue();
  });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  const grid = page.locator(".parts-grid").first();
  await grid.locator('.ag-row[row-index="8"] [col-id="length"]').first().click();          // 9-qator
  await grid.locator('.ag-row[row-index="16"] [col-id="name"]').first().click();           // oxirgi qator
  const st = () => page.evaluate(() => {
    const a = document.activeElement as HTMLElement | null;
    const f = a?.closest(".ag-row")?.getAttribute("row-index");
    const sel = [...new Set([...document.querySelectorAll(".parts-grid .ag-row.ag-row-selected")]
      .filter((r) => !r.closest(".ag-floating-bottom")).map((r) => r.getAttribute("row-index")))];
    return { f, sel };
  });
  const cdp = await page.context().newCDPSession(page);
  // sekin kompyuter: protsessor ×6 (E2E_CPU bilan o'zgartiriladi)
  await cdp.send("Emulation.setCPUThrottlingRate", { rate: Number(process.env.E2E_CPU || 6) });
  const key = (type: string, rep = false) => cdp.send("Input.dispatchKeyEvent", { type, key: "Tab", code: "Tab", windowsVirtualKeyCode: 9, autoRepeat: rep });
  const bad: string[] = [];
  await key("rawKeyDown");
  const t0 = Date.now();
  await page.waitForTimeout(500);
  while (Date.now() - t0 < 6000) {
    await key("rawKeyDown", true); await page.waitForTimeout(33);
    const s = await st();
    if (s.f != null && (s.sel.length !== 1 || s.sel[0] !== s.f)) bad.push(`${Date.now() - t0}ms f=${s.f} sel=${s.sel.join(",")}`);
  }
  await key("keyUp");
  // server javoblari hali kelayotgan paytda (qayta chizish) — sichqoncha bilan tez bosish
  for (const r of [3, 12, 7, 15, 1]) {
    const b = (await grid.locator(`.ag-row[row-index="${r}"] [col-id="width"]`).first().boundingBox())!;
    await page.mouse.move(b.x + 15, b.y + b.height / 2);
    await page.mouse.down(); await page.waitForTimeout(70); await page.mouse.up();
    await page.waitForTimeout(60);
    const s = await st();
    if (s.sel.length !== 1 || s.sel[0] !== String(r)) bad.push(`click r${r}: f=${s.f} sel=${s.sel.join(",")}`);
  }
  await page.waitForTimeout(2500);
  const end = await st();
  console.log("BAD", bad.length, bad.slice(0, 12).join(" | "));
  console.log("END", JSON.stringify(end));
  expect(end.sel).toEqual([end.f]);
  expect(bad).toEqual([]);
});
