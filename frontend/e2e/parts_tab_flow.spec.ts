// CS «Детали»: onlayn tizimdagidek klaviatura bilan kiritish — TAB qator bo'ylab o'ngga, oxirgi qatorning oxirgi katagidan keyin
// darhol yangi qator (davomiy raqam), Shift+TAB orqaga; TAB bilan kelingan Ткт / ОВ / ОН / ОЛ / ОП katagida probel belgi qo'yadi.
import { expect, test } from "@playwright/test";

test("TAB oxirida yangi qator, Shift+TAB orqaga, probel Ткт va kromkalarda", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "TABF" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  const el = (await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "EL", code: "K1", name: "kromka" } })).json())
    .operations.find((o: { type: string }) => o.type === "EL").id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "a", length: 700, width: 500, qty: 1 }, { name: "b", length: 600, width: 400, qty: 1 }] });
  const parts = async () => (await (await request.get(`/api/projects/${pr.id}`)).json()).operations.find((o: { id: string }) => o.id === cs).parts;
  const focus = () => page.evaluate(() => {
    const a = document.activeElement as HTMLElement | null; const r = a?.closest(".ag-row");
    return `${r?.closest(".ag-floating-bottom") ? "draft" : r?.getAttribute("row-index")}:${a?.closest(".ag-cell")?.getAttribute("col-id")}`;
  });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  const grid = page.locator(".parts-grid").first();
  // o'rtadagi qator: oxirgi katakdan keyin — keyingi qatorning nomi («№» emas); Shift+TAB — orqaga oldingi qator oxiriga
  await grid.locator('.ag-row[row-index="0"] [col-id="name"]').first().click();
  for (let i = 0; i < 30 && !(await focus()).startsWith("1:"); i++) await page.keyboard.press("Tab");
  expect(await focus()).toBe("1:name");
  await page.keyboard.press("Shift+Tab");
  expect(await focus()).not.toMatch(/^1:|:num$/);
  await page.keyboard.press("Tab");
  expect(await focus()).toBe("1:name");
  // oxirgi qatorni o'ngga — oxirgi katakdan keyingi TAB yangi qator yaratadi va nomiga o'tadi
  for (let i = 0; i < 30 && (await parts()).length === 2; i++) {
    await page.keyboard.press("Tab"); await page.waitForTimeout(80);
    expect(await focus()).not.toMatch(/^draft/);
  }
  await expect.poll(async () => (await parts()).length).toBe(3);
  await expect.poll(focus).toBe("2:name");
  await page.keyboard.type("c");
  await page.keyboard.press("Tab"); await page.keyboard.type("300");
  await page.keyboard.press("Tab"); await page.keyboard.type("200");
  await page.keyboard.press("Tab");                          // Кол
  await page.keyboard.press("Tab");                          // Ткт
  await expect.poll(focus).toBe("2:grain");
  const g0 = (await parts())[2].grain;
  await page.keyboard.press("Space");
  await expect.poll(async () => (await parts())[2].grain).toBe(!g0);
  for (const side of ["edge_top", "edge_bottom", "edge_left", "edge_right"]) {
    await page.keyboard.press("Tab");
    await expect.poll(focus).toBe(`2:${side}`);
    await page.keyboard.press("Space");
    await expect.poll(async () => (await parts())[2][side].op_id).toBe(el);
  }
  // Shift+TAB — chapga qaytadi (xatoni tuzatish uchun)
  await page.keyboard.press("Shift+Tab");
  await expect.poll(focus).toBe("2:edge_left");
  await page.keyboard.press("Space");                        // yagona kromka → yana bosilsa olib tashlanadi
  await expect.poll(async () => (await parts())[2].edge_left.op_id).toBe(null);
  const last = (await parts())[2];
  expect([last.name, last.length, last.width]).toEqual(["c", 300, 200]);
  expect(errors).toEqual([]);
});
