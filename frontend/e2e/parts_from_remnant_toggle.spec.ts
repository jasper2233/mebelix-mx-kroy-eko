// «Из ост.» va «Ткт» katagi har qatorda bir bosishda almashadi va saqlanadi (2026-10-25)
import { expect, test } from "@playwright/test";
test("detallar: «Из ост.» / «Ткт» katagi har qatorda", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "P" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", name: "LDSP P" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "A", length: 500, width: 400, qty: 1, grain: false }, { name: "B", length: 600, width: 300, qty: 1, grain: false }, { name: "C", length: 700, width: 300, qty: 1, grain: false }] });
  const st = async () => JSON.stringify((await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0].parts.map((x: { name: string; grain: boolean; from_remnant: boolean }) => [x.name, x.grain, x.from_remnant]));
  await request.put("/api/settings/part_columns/default", { data: { columns: ["num", "name", "length", "width", "qty", "grain", "from_remnant"].map((key) => ({ key, visible: true })) } });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP P" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  // «Из ост.» ustunini ko'rsatish (sinov uchun to'g'ridan-to'g'ri)
  for (const i of [1, 2]) { await page.locator(`.ag-row[row-index="${i}"] [col-id="grain"] input`).click(); await page.waitForTimeout(600); }
  expect(await st()).toBe(JSON.stringify([["A", false, false], ["B", true, false], ["C", true, false]]));
  for (const i of [1, 2, 0]) {
    const inp = page.locator(`.ag-row[row-index="${i}"] [col-id="from_remnant"] input`);
    await inp.click();
    await page.waitForTimeout(300);
    await expect(inp).toBeChecked();
    await page.waitForTimeout(1200);
  }
  expect(await st()).toBe(JSON.stringify([["A", false, true], ["B", true, true], ["C", true, true]]));
  await request.put("/api/settings/part_columns/default", { data: { columns: [] } });
});
