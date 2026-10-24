// Jadvalning oxirgi ustuni («ОК») tik aylantirish chizig'i ostida qolmaydi (2026-10-23): ustma-ust (overlay) chiziqli brauzerlarda
// jadval chiziq enini 0 deb hisoblab, ustunni chiziq ostiga cho'zardi — raqamlar ko'rinmasdi (shared/grid/Grid.tsx SCROLLBAR_W).
import { expect, test } from "@playwright/test";

test("oxirgi ustun tik chiziqdan oldin tugaydi", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "LASTCOL" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "d1", length: 500, width: 300, qty: 3 }] });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  const cell = page.locator('.bottom .ag-row [col-id="total"]').first();
  await expect(cell).toHaveText("3");
  // tor oynada ustunlar sig'masa — jadval gorizontal aylanadi: oxirigacha surilganda ham ustun chiziq ostida qolmasin
  const bar = (await page.locator(".bottom .ag-body-vertical-scroll").first().boundingBox())!;
  await expect.poll(async () => {
    await page.locator(".bottom .ag-body-horizontal-scroll-viewport").first().evaluate((e) => { e.scrollLeft = e.scrollWidth; });
    await page.waitForTimeout(150);
    const c = (await cell.boundingBox())!;
    return c.x + c.width - bar.x;
  }).toBeLessThanOrEqual(1);
});
