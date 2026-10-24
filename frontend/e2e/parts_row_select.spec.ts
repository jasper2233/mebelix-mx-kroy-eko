// CS «Детали»: qatorlarni belgilash onlayn tizimdagidek (2026-10-21 jonli o'lchandi, 6 qatorli jadval):
// bosish — bitta; Shift+bosish — oraliq; Ctrl+bosish — qo'shish / olib tashlash; Shift+Ctrl+bosish — oraliq mavjudiga qo'shiladi;
// Shift+↓/↑ — oraliqni kengaytirish / qisqartirish; ↓ — bitta qatorga; Del — belgilanganlar o'chiriladi.
import { expect, test } from "@playwright/test";

test("qator belgilash: Shift / Ctrl / Shift+Ctrl / Shift+strelka / Del", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "SEL" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`,
    { data: [1, 2, 3, 4, 5, 6].map((i) => ({ name: `p${i}`, length: 300 + i, width: 200, qty: 1 })) });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  const grid = page.locator(".parts-grid").first();
  const row = (i: number) => grid.locator(`.ag-row[row-index="${i - 1}"] [col-id="length"]`).first();
  const sel = async () => [...new Set(await grid.locator(".ag-row.ag-row-selected").evaluateAll(
    (rs) => rs.filter((r) => !r.closest(".ag-floating-bottom")).map((r) => Number(r.getAttribute("row-index")) + 1)))].sort((a, b) => a - b);
  await row(1).click();
  await expect.poll(sel).toEqual([1]);
  await row(3).click({ modifiers: ["Shift"] });
  await expect.poll(sel).toEqual([1, 2, 3]);
  await row(5).click({ modifiers: ["Control"] });
  await expect.poll(sel).toEqual([1, 2, 3, 5]);
  await row(6).click({ modifiers: ["Shift", "Control"] });
  await expect.poll(sel).toEqual([1, 2, 3, 5, 6]);
  await row(5).click({ modifiers: ["Control"] });
  await expect.poll(sel).toEqual([1, 2, 3, 6]);
  await row(2).click();
  await expect.poll(sel).toEqual([2]);
  await page.keyboard.press("Shift+ArrowDown");
  await page.keyboard.press("Shift+ArrowDown");
  await expect.poll(sel).toEqual([2, 3, 4]);
  await page.keyboard.press("Shift+ArrowUp");
  await expect.poll(sel).toEqual([2, 3]);
  await page.keyboard.press("ArrowDown");
  await expect.poll(sel).toEqual([4]);
  // Shift+↑ yuqoriga ham kengayadi
  await page.keyboard.press("Shift+ArrowUp");
  await page.keyboard.press("Shift+ArrowUp");
  await expect.poll(sel).toEqual([2, 3, 4]);
  // «№» ustunida sichqoncha bilan sudrash — oraliq belgilanadi
  const num = (i: number) => grid.locator(`.ag-row[row-index="${i - 1}"] [col-id="num"]`).first();
  const b1 = (await num(1).boundingBox())!, b4 = (await num(4).boundingBox())!;
  await page.mouse.move(b1.x + b1.width / 2, b1.y + b1.height / 2);
  await page.mouse.down();
  await page.mouse.move(b1.x + b1.width / 2, b4.y + b4.height / 2, { steps: 8 });
  await page.mouse.up();
  await expect.poll(sel).toEqual([1, 2, 3, 4]);
  await row(4).click();
  await expect.poll(sel).toEqual([4]);
  await expect.poll(() => page.evaluate(() => document.activeElement?.closest(".ag-row")?.getAttribute("row-index"))).toBe("3");
  await page.keyboard.press("Shift+ArrowUp");
  await page.keyboard.press("Shift+ArrowUp");
  await expect.poll(sel).toEqual([2, 3, 4]);
  // Del — belgilanganlar o'chiriladi (tasdiq oynasi bo'lsa — tasdiqlanadi)
  await page.keyboard.press("Delete");
  const ok = page.getByRole("button", { name: /^(Да|Ok|ОК|Удалить)$/ });
  if (await ok.first().isVisible().catch(() => false)) await ok.first().click();
  await expect.poll(async () => (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0].parts.map((x: { name: string }) => x.name))
    .toEqual(["p1", "p5", "p6"]);
  expect(errors).toEqual([]);
});
