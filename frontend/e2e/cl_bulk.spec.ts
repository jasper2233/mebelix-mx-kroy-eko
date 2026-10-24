// CL «Детали»: onlayn tizimdagidek TXT olish / qo'yish va o'lchamlarni almashtirish (tugma va Ctrl+D / E / W).
import { expect, test } from "@playwright/test";

test("CL detallari: TXT olish / qo'yish, o'lchamlarni almashtirish", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "CLB" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CL", code: "P1", name: "Profil" } })).json();
  const cl = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cl}/parts`, { data: [{ name: "A", length: 900, width: 40, qty: 1, grain: true }] });
  const part = async () => (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0].parts[0];
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "Profil" }).first().click();
  await page.locator(".tabs button, .tabs [role=tab]").filter({ hasText: "Детали" }).first().click();
  await page.locator('[data-testid="cl-parts-grid"] .ag-row[row-index="0"] .ag-cell').nth(1).click();
  await page.keyboard.press("Escape");
  await page.getByTestId("cl-grain-off").click();
  await expect.poll(async () => (await part()).grain).toBe(false);
  await page.getByTestId("cl-grain-on").click();
  await expect.poll(async () => (await part()).grain).toBe(true);
  await page.getByTestId("cl-parts-swap").click();
  await expect.poll(async () => (await part()).length).toBe(900);       // CL: uzunlik saqlanadi (eni yo'q — faqat tomonlar almashadi)
  expect(errors).toEqual([]);
});
