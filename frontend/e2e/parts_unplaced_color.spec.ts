// Kroyga kirmagan detal (Ост > 0) — onlayn tizimdagidek: qator foni yo'q, yozuv va raqamlar #FF6600, ID — oddiy rangda; tanlanganda
// fon boshqa qatorlardagidek ko'k (2026-10-23, foydalanuvchi skrini: «2108 Muzaffar», 01_039 XDF 2269×2299 listga sig'maydi).
import { expect, test } from "@playwright/test";

test("sig'magan detal qatori: #FF6600 yozuv, fon yo'q, tanlanganda ko'k", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "UNPLACED" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "XDF", name: "XDF 2800x2070" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [
    { name: "01_039 XDF ort", length: 2269, width: 2299, qty: 1, grain: false },
    { name: "01_040 XDF ort", length: 1224, width: 859, qty: 1, grain: false }] });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "XDF 2800x2070" }).first().click();
  await page.getByTestId("cs-tab-cut").click();
  await page.getByTestId("btn-cut-big").click();
  await expect(page.getByTestId("cut-status")).toBeVisible({ timeout: 60_000 });
  await page.getByTestId("cs-tab-parts").click();
  const bad = page.locator(".bottom .ag-row").filter({ hasText: "01_039" }).first();
  const good = page.locator(".bottom .ag-row").filter({ hasText: "01_040" }).first();
  await expect(bad).toHaveClass(/row-left/);
  const style = (row: typeof bad, col: string) => row.locator(`[col-id="${col}"]`).evaluate((c) => {
    const s = getComputedStyle(c); return [s.color, s.backgroundColor];
  });
  expect((await style(bad, "length"))[0]).toBe("rgb(255, 102, 0)");
  expect((await style(bad, "name"))[0]).toBe("rgb(255, 102, 0)");
  expect((await style(bad, "uid"))[0]).not.toBe("rgb(255, 102, 0)");
  expect((await style(good, "length"))[0]).not.toBe("rgb(255, 102, 0)");
  const bg = (await style(bad, "name"))[1];
  expect(bg === "rgba(0, 0, 0, 0)" || bg === "rgb(255, 255, 255)").toBeTruthy();             // sariq fon yo'q
  await good.click();
  await bad.locator('[col-id="name"]').click();
  await expect(bad).toHaveClass(/ag-row-selected/);
  expect((await style(bad, "length"))[0]).toBe("rgb(255, 102, 0)");                          // tanlanganda ham raqam qizil
});
