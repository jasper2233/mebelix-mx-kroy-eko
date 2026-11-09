// Xodim videolari 2026-11-09 (lokal tizim ↔ MX):
// 1) «Операции»: qator Ctrl+↑/↓ bilan ko'chirilganda kursor o'sha qator bilan birga yuradi — keyingi Ctrl+↑ / strelka aynan shu
//    operatsiyadan davom etadi (avval kursor eski joyda qolib, keyingi bosish boshqa operatsiyani ko'chirardi).
// 2) «Детали»: kursor katagidagi matn belgilangan; ← / → — matn ichiga kirib tahrirlash (eski matn saqlanadi), Ctrl+C — katak
//    matni buferga, Ctrl+V — fokusdagi katakka (F2 siz).
import { expect, test } from "@playwright/test";

test("Операции: ko'chirilgan qator kursorni o'zi bilan olib yuradi", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "OPMOVE" } })).json();
  for (const n of ["A1", "B2", "C3", "D4"]) await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: n, name: n } });
  const names = async () => (await (await request.get(`/api/projects/${pr.id}`)).json()).operations.map((o: { name: string }) => o.name);
  await page.goto(`/#/p/${pr.id}`);
  const grid = page.getByTestId("ops-grid");
  await grid.locator('.ag-row[row-index="3"] [col-id="name"]').first().click();
  await page.keyboard.press("Control+ArrowUp");
  await expect.poll(names).toEqual(["A1", "B2", "D4", "C3"]);
  await page.keyboard.press("Control+ArrowUp");
  await expect.poll(names).toEqual(["A1", "D4", "B2", "C3"]);
  // kursor (oq katak) va tanlov ko'chirilgan qatorda
  await expect(grid.locator('.ag-row[row-index="1"] .ag-cell-focus')).toHaveCount(1);
  await expect(grid.locator('.ag-row-selected [col-id="name"]')).toHaveText("D4");
  // oddiy ↓ — ko'chirilgan qatordan keyingisiga
  await page.keyboard.press("ArrowDown");
  await expect(grid.locator('.ag-row-selected [col-id="name"]')).toHaveText("B2");
  expect(errors).toEqual([]);
});

test("Детали: matn belgilangan, ← / → bilan tahrir, Ctrl+C / Ctrl+V", async ({ page, request, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "TXTED" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [
    { name: "18_004 pl", length: 304, width: 80, qty: 1 }, { name: "polka", length: 600, width: 400, qty: 4 }] });
  const parts = async () => (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0].parts as { name: string }[];
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  const grid = page.locator(".parts-grid").first();
  await grid.locator('.ag-row[row-index="1"] [col-id="name"]').first().click();
  // matn belgilangan
  await expect.poll(() => page.evaluate(() => window.getSelection()?.toString())).toBe("polka");
  // → — tahrir, eski matn saqlanadi, oxiriga qo'shiladi
  await page.keyboard.press("ArrowRight");
  await page.waitForTimeout(150);                       // odam tezligi (muharrir ochilishi)
  await page.keyboard.type("#");
  await page.keyboard.press("Enter");
  await expect.poll(async () => (await parts())[1].name).toBe("polka#");
  // Ctrl+C yuqori qatordan, ↓, Ctrl+V — pastki qator nomi almashadi
  await grid.locator('.ag-row[row-index="1"] [col-id="name"]').first().click();
  await page.keyboard.press("ArrowUp");
  await expect.poll(() => page.evaluate(() => window.getSelection()?.toString())).toBe("18_004 pl");
  await page.keyboard.press("Control+c");
  await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe("18_004 pl");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Control+v");
  await expect.poll(async () => (await parts())[1].name).toBe("18_004 pl");
  // harf yozilsa — belgilangan matn almashadi (avvalgidek)
  await page.keyboard.type("z");
  await page.keyboard.press("Enter");
  await expect.poll(async () => (await parts())[1].name).toBe("z");
  expect(errors).toEqual([]);
});
