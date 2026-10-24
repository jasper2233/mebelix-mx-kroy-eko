// Varaq ochilganda klaviatura fokusi jadvalning 1-qatorida (TAB yuqoridagi yorliq / tugmalardan emas, ro'yxatdan boshlanadi);
// detal qatori ustida sichqoncha turganda ma'lumot oynasi chiqmaydi.
import { expect, test } from "@playwright/test";

test("Детали / Листы / EL / O: fokus 1-qatorda, qator ustida hover-oyna yo'q", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "FOC" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  const el = (await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "EL", code: "K1", name: "kromka" } })).json())
    .operations.find((o: { type: string }) => o.type === "EL").id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "a", length: 700, width: 500, qty: 1, edge_top: { op_id: el } },
    { name: "b", length: 600, width: 400, qty: 1 }] });
  const focus = () => page.evaluate(() => {
    const a = document.activeElement as HTMLElement | null; const r = a?.closest(".ag-row");
    return `${a?.closest(".grid-wrap")?.getAttribute("data-testid")}:${r?.getAttribute("row-index")}:${a?.closest(".ag-cell")?.getAttribute("col-id")}`;
  });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  // onlayn tizimdagidek: fokus 1-qatorda, birinchi TAB — «Наименование», keyin «Д-на»
  await expect.poll(focus).toBe("parts-grid:0:num");
  await page.keyboard.press("Tab");
  await expect.poll(focus).toBe("parts-grid:0:name");
  await page.keyboard.press("Tab");
  await expect.poll(focus).toBe("parts-grid:0:length");
  // qator ustida sichqoncha — ma'lumot oynasi chiqmaydi
  await page.locator('.parts-grid .ag-row[row-index="1"] [col-id="name"]').first().hover();
  await page.waitForTimeout(1200);
  await expect(page.locator(".ag-tooltip, .grid-tip")).toHaveCount(0);
  // «Листы и остатки»
  await page.getByTestId("cs-tab-sheets").click();
  await expect.poll(focus).toMatch(/^sheets-grid:0:/);
  // EL operatsiyasi
  await page.locator(".ag-row").filter({ hasText: "kromka" }).first().click();
  await page.locator(".tabs button, .tabs [role=tab]").filter({ hasText: "Детали" }).first().click();
  await expect.poll(focus).toMatch(/:0:/);
  expect(errors).toEqual([]);
});
