// Kroy qilinmagan operatsiyada «Редактирование раскроя» (onlayn tizimdagidek): bo'sh natijadan karta qo'shib, detalni qo'lda joylash.
import { expect, test } from "@playwright/test";

test("kroysiz «Редактирование раскроя»: karta qo'shish, detal joylash, saqlash", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "EDE" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "A", length: 700, width: 500, qty: 2 }] });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-cut").click();
  await page.getByTestId("btn-edit-cut-empty").click();
  await expect(page.getByTestId("cut-editor")).toBeVisible();
  await page.getByTestId("ed-add-map").click();
  await expect(page.getByTestId("editor-map")).toBeVisible();
  await page.locator('[data-testid="cut-editor"] tbody tr').filter({ hasText: "700" }).first().click();
  await page.getByTestId("ed-auto").click();
  await expect(page.locator('[data-testid="editor-map"] .map-part')).toHaveCount(1);
  await page.getByTestId("editor-ok").click();
  await expect(page.getByTestId("cut-editor")).toHaveCount(0);
  const op = (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0];
  expect(op.result?.maps?.length).toBe(1);
  expect(errors).toEqual([]);
});
