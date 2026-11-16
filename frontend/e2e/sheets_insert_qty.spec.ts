// Xodim videosi 2026-11-16 («1299»): «Листы и остатки» da «+» (Вставить) qoldiq qo'shish uchun bosilganda yangi qator 10000 dona
// bo'lib qo'shilardi. Onlayn tizimdagidek: tanlangan qator o'lchami, soni 1; ro'yxatda cheksiz list bo'lmasa — cheksiz.
import { expect, test } from "@playwright/test";

test("Листы: «+» — tanlangan qator o'lchami, soni 1", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "INS" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.put(`/api/projects/${pr.id}/operations/${cs}/sheets`, { data: [{ id: "full", length: 2750, width: 1830, qty: 10000 }] });
  const sheets = async () => (await (await request.get(`/api/projects/${pr.id}`)).json())
    .operations.find((o: { id: string }) => o.id === cs).sheets as { length: number; width: number; qty: number }[];
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-sheets").click();
  await page.locator('[data-testid="sheets-grid"] .ag-row[row-index="0"] [col-id="length"]').first().click();
  await page.getByTestId("sheets-insert").click();
  await expect.poll(async () => (await sheets()).map((s) => `${s.length}x${s.width}:${s.qty}`))
    .toEqual(["2750x1830:1", "2750x1830:10000"]);
});
