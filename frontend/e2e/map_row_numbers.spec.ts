// Xodim videosi «1281 Usmon» (2026-11-05): kartadagi raqam — «Детали» jadvalidagi № (tartib raqami), ID emas.
// ID lar sakrasa (detal o'chirilgan / Bazis importi) ham kartada 1, 2, … — xodim detalni ro'yxatdan shu raqam bilan topadi.
// Detallar bor bo'lsa ro'yxat oxirida «*» qatori yo'q.
import { expect, test } from "@playwright/test";

test("karta raqamlari — jadvaldagi №; ro'yxat oxirida «*» qatori yo'q", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "ROWNO" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "LD", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  const made = await (await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [
    { name: "a", length: 500, width: 400, qty: 1 }, { name: "b", length: 600, width: 300, qty: 1 },
    { name: "c", length: 700, width: 200, qty: 1 }] })).json();
  const parts = made.operations[0].parts as { id: string; uid: number; name: string }[];
  // birinchi detal o'chiriladi — qolganlarning ID si 2, 3, tartib raqami 1, 2
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts/delete`, { data: { ids: [parts.find((x) => x.name === "a")!.id] } });
  await request.post(`/api/projects/${pr.id}/operations/${cs}/optimize?quality=fast`);
  const op = (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0];
  expect(op.parts.map((x: { uid: number }) => x.uid)).toEqual([2, 3]);

  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  await expect(page.locator('[data-testid="parts-grid"] .ag-row[row-index="1"]')).toBeVisible();
  await expect(page.locator('[data-testid="parts-grid"] .ag-grid-pinned-bottom-rows .ag-row')).toHaveCount(0);
  await page.getByTestId("cs-tab-cut").click();
  const labels = page.locator(".map-part-label text");
  await expect(labels.first()).toBeVisible();
  const txt = await labels.allTextContents();
  expect(txt).toContain("1");
  expect(txt).toContain("2");
  expect(txt).not.toContain("3");
  expect(errors).toEqual([]);
});
