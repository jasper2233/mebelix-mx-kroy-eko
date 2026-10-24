// Onlayn yordamdagi jadval navigatsiyasi (2026-10-21): [HOME] / [END] — birinchi / oxirgi qator; «Листы»: [CTRL]+[ENTER] —
// pastga, oxirgi qatordan keyin — yangi qator.
import { expect, test } from "@playwright/test";

test("jadvallar: Home/End qatorlar bo'yicha, «Листы» Ctrl+Enter — yangi qator", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "NAV" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: Array.from({ length: 6 }, (_, i) => ({ name: `d${i}`, length: 500 + i, width: 300, qty: 1 })) });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  const grid = page.getByTestId("parts-grid");
  await grid.locator('.ag-row[row-index="2"] .ag-cell').nth(2).click();
  await page.keyboard.press("End");
  await expect(grid.locator(".ag-cell-focus")).toHaveCount(1);
  await expect(grid.locator('.ag-row[row-index="5"] .ag-cell-focus')).toHaveCount(1);
  await page.keyboard.press("Home");
  await expect(grid.locator('.ag-row[row-index="0"] .ag-cell-focus')).toHaveCount(1);
  // «Листы и остатки»: oxirgi qatorda Ctrl+Enter — yangi list qatori
  await page.getByTestId("cs-tab-sheets").click();
  const sg = page.getByTestId("sheets-grid");
  const n0 = (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0].sheets.length;
  await sg.locator(`.ag-row[row-index="${n0 - 1}"] .ag-cell`).nth(1).click();
  await page.keyboard.press("Control+Enter");
  await expect.poll(async () => (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0].sheets.length).toBe(n0 + 1);
  expect(errors).toEqual([]);
});
