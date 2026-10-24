// Oyna kichraytirilsa / kattalashtirilsa (Windows «Восстановить» / «Развернуть») yuqori (Операции) va pastki panel nisbati saqlanadi —
// onlayn tizimdagidek (foydalanuvchi, 2026-10-21). Avval yuqori panel qat'iy px edi: kichrayish faqat pastki panelga tushardi.
import { expect, test } from "@playwright/test";

test("oyna o'lchami o'zgarganda panellar nisbati saqlanadi", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "RATIO" } })).json();
  await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } });
  await page.setViewportSize({ width: 1904, height: 945 });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  const top = () => page.locator(".project > .top").evaluate((e) => e.getBoundingClientRect().height);
  const h1 = await top();
  await page.setViewportSize({ width: 1280, height: 600 });
  await expect.poll(top).toBeLessThan(h1);
  expect(Math.abs((await top()) / 600 - h1 / 945)).toBeLessThan(0.02);
  await page.setViewportSize({ width: 1904, height: 945 });
  await expect.poll(top).toBeCloseTo(h1, 0);
});
