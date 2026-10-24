// Oyna kichraytirilganda (2026-10-22, foydalanuvchi skrinlari): butun interfeys mutanosib kichrayadi (shared/uiZoom), sarlavha
// qatorlarga bo'linmaydi, jadvalning oxirgi qatori ko'rinadi va bosiladi, kromka ro'yxati katak ostida ochiladi; detal
// «XNC Редактор» oynasi — dastur tepada, chizma pastda (onlayn tartib), «Чертеж» varag'i — «Операция» tanlovi va varaq.
import { expect, test } from "@playwright/test";

test.use({ viewport: { width: 850, height: 610 } });

test("tor oyna: masshtab, sarlavha, oxirgi qator, XNC Редактор va Чертеж", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "ZOOM", customer: "Mijoz" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  const rows = Array.from({ length: 24 }, (_, i) => ({ name: `d${i + 1}`, length: 500 + i, width: 300, qty: 1 }));
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: rows });

  await page.goto(`/#/p/${pr.id}`);
  const z = Number(await page.evaluate(() => document.documentElement.dataset.uiZoom));
  expect(z).toBeGreaterThan(0.5);
  expect(z).toBeLessThan(0.8);                                           // 850 / 1200
  // sarlavha ikki qatordan oshmaydi (avval tor oynada 4 qatorga bo'linib, ~240 px edi)
  const hb = await page.getByTestId("project-header").boundingBox();
  expect(hb!.height).toBeLessThan(70);

  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  await expect(page.locator(".ag-row").filter({ hasText: "d1" }).first()).toBeVisible();
  // oxirgi qatorgacha aylantirib bosish — to'liq ko'rinadi va tanlanadi
  const grid = page.locator(".ag-row").filter({ hasText: "d1" }).first();
  const gb = await grid.boundingBox();
  await page.mouse.move(gb!.x + 200, gb!.y + 5);
  await page.mouse.wheel(0, 1500);
  const last = page.locator(".ag-row").filter({ hasText: "d24" }).first();
  await expect(last).toBeVisible();
  const lb = await last.boundingBox();
  const vh = page.viewportSize()!.height;
  expect(lb!.y + lb!.height).toBeLessThan(vh);
  await page.mouse.click(lb!.x + 80, lb!.y + lb!.height / 2);
  await expect(last).toHaveClass(/ag-row-selected/);

  // detal «XNC Редактор»: dastur ro'yxati chizmadan yuqorida, chizma keng
  await page.locator('button[title="XNC Редактор"]').first().click();
  const dlg = page.getByTestId("part-xnc-dialog");
  await expect(dlg).toBeVisible();
  await dlg.getByTestId("part-xnc-drills").locator("button").first().click();
  await page.getByTestId("pdrill-x").fill("100");
  await page.getByTestId("pdrill-y").fill("37");
  await page.getByTestId("pdrill-ok").click();
  const prog = await dlg.locator(".xnc-prog").boundingBox();
  const draw = await dlg.locator(".xnc-draw-box").boundingBox();
  expect(prog!.y + prog!.height).toBeLessThanOrEqual(draw!.y + 2);
  expect(draw!.width).toBeGreaterThan(prog!.width * 0.8);
  const head = await dlg.getByTestId("pxd-head").boundingBox();
  expect(head!.height).toBeLessThan(25);                                 // «DX=…» qatori cho'zilmaydi

  // «Чертеж»: «Операция» tanlovi va varaq (o'lchamlar, raqamlar, shtamp)
  await dlg.getByTestId("pxd-tab-sheet").click();
  await expect(dlg.getByTestId("pxd-sheet-op")).toBeVisible();
  const sheet = page.frameLocator('[data-testid="pxd-sheet"]');
  await expect(sheet.locator(".xnc-sheet-dims")).toHaveCount(1);
  await expect(sheet.locator(".xnc-num")).toHaveCount(1);
  await expect(sheet.locator("[data-testid=sh-stamp]")).toContainText("Кол");
  await dlg.getByTestId("part-xnc-cancel").click();
  expect(errors).toEqual([]);
});

test("tor oyna: ustun chegarasi sudralganda kursor ostida qoladi", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "ZOOM2", customer: "Mijoz" } })).json();
  await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } });
  await page.goto(`/#/p/${pr.id}`);
  const z = Number(await page.evaluate(() => document.documentElement.dataset.uiZoom));
  expect(z).toBeLessThan(0.8);
  const cell = page.locator(".ag-header-cell").filter({ has: page.locator(".ag-header-cell-resize") }).nth(1);
  const h = cell.locator(".ag-header-cell-resize");
  const before = (await cell.boundingBox())!;
  const hb = (await h.boundingBox())!;
  await page.mouse.move(hb.x + hb.width / 2, hb.y + hb.height / 2);
  await page.mouse.down();
  for (let i = 1; i <= 10; i++) await page.mouse.move(hb.x + hb.width / 2 + i * 10, hb.y + hb.height / 2);
  await page.mouse.up();
  const after = (await cell.boundingBox())!;
  expect(Math.abs(after.width - before.width - 100)).toBeLessThan(6);   // ekranda ham 100 px (avval ~70 px)
});
