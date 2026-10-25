import { expect, test } from "@playwright/test";
// Qator tanlash katagi bosilganda qator belgilanadi (avval Grid.selectOnDown belgilab, katak bosilishi qaytarib olardi — 2026-10-25)
test("qoldiq tanlash oynasi: katak bilan belgilash", async ({ page, request }) => {
  const code = `PK${Date.now() % 1e7}`;
  const pr = await (await request.post("/api/projects", { data: { name: "P" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code, name: "LDSP PK" } })).json();
  const cs = p.operations[0].id;
  await request.patch(`/api/projects/${pr.id}/operations/${cs}`, { data: { cs_material: { thickness: 16 } } });
  await request.post("/api/remnants", { data: { material_code: code, length: 2000, width: 900, thickness: 16, qty: 1 } });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP PK" }).first().click();
  await page.getByTestId("cs-tab-sheets").click();
  await page.getByRole("button", { name: "Добавить остатки со склада" }).click();
  const dlg = page.getByTestId("remnant-picker");
  await expect(dlg).toBeVisible();
  await dlg.locator('.ag-row[row-index="0"] .ag-selection-checkbox input').click();
  await page.waitForTimeout(400);
  await expect(page.getByTestId("remnant-add")).toBeEnabled();
});
