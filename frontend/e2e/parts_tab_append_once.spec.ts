// CS «Детали»: oxirgi qatorning oxirgi katagidan keyingi TAB har safar FAQAT BITTA yangi qator qo'shadi (foydalanuvchi shikoyati
// 2026-10-21: 1-safar 1 ta, keyingisi 2 ta … qo'shilib ketardi — sabab bosib turilgan TAB takrori; takror e'tiborsiz).
import { expect, test } from "@playwright/test";

test("TAB oxirida har safar bitta qator", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "TAB1" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "a", length: 700, width: 500, qty: 1 }] });
  const n = async () => (await (await request.get(`/api/projects/${pr.id}`)).json()).operations.find((o: { id: string }) => o.id === cs).parts.length;
  const focus = () => page.evaluate(() => {
    const a = document.activeElement as HTMLElement | null;
    return `${a?.closest(".ag-row")?.getAttribute("row-index")}:${a?.closest(".ag-cell")?.getAttribute("col-id")}`;
  });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  await page.locator(".parts-grid").first().locator('.ag-row[row-index="0"] [col-id="name"]').first().click();
  for (let round = 1; round <= 4; round++) {
    const before = await n();
    // oxirgi katakkacha TAB, oxirgi katakda qiymat yoziladi (tahrir holati), keyin TAB
    const lastCol = await page.evaluate(() => { const c = [...document.querySelectorAll('.parts-grid .ag-header-cell[col-id]')]; return c[c.length - 1]?.getAttribute("col-id"); });
    for (let i = 0; i < 40 && !(await focus()).endsWith(`:${lastCol}`); i++) await page.keyboard.press("Tab");
    await page.keyboard.type("1");
    // bosib turilgan TAB: 1 soniyagacha takrorlar e'tiborsiz (joyida, qator qo'shilmaydi)
    const at = await focus();
    for (let k = 0; k < 6; k++) {
      await page.evaluate(() => document.activeElement?.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", code: "Tab", repeat: true, bubbles: true, cancelable: true })));
    }
    await page.waitForTimeout(600);
    expect(await n(), `repeat ${round}`).toBe(before);
    expect(await focus()).toBe(at);
    // 1 soniyadan keyin bir zumda kelgan bir nechta takror — faqat BITTA yangi qator (qotmaydi, ko'paymaydi)
    await page.waitForTimeout(700);
    for (let k = 0; k < 4; k++) {
      await page.evaluate(() => document.activeElement?.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", code: "Tab", repeat: true, bubbles: true, cancelable: true })));
    }
    await page.waitForTimeout(1500);
    await expect.poll(n, `round ${round}`).toBe(before + 1);
    // bosib turilgan TAB yangi qatorga o'tib, yurishda davom etadi (qotmaydi) — kursor yangi qatorda
    await expect.poll(async () => (await focus()).split(":")[0]).toBe(String(before));
    await page.keyboard.press("Escape");
    await page.locator(".parts-grid").first().locator(`.ag-row[row-index="${before}"] [col-id="name"]`).first().click();
    await page.keyboard.type(`r${round}`);
    await page.keyboard.press("Tab"); await page.keyboard.type("300");
    await page.keyboard.press("Tab"); await page.keyboard.type("200");
  }
});

test("TAB 1 soniyadan ko'p bosib turilsa — keyingi kataklarga o'tib boradi", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "TABH" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "a", length: 700, width: 500, qty: 1 }] });
  const focus = () => page.evaluate(() => document.activeElement?.closest(".ag-cell")?.getAttribute("col-id"));
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  await page.locator(".parts-grid").first().locator('.ag-row[row-index="0"] [col-id="name"]').first().click();
  const fire = (rep: boolean) => page.evaluate((rep) => document.activeElement?.dispatchEvent(
    new KeyboardEvent("keydown", { key: "Tab", code: "Tab", repeat: rep, bubbles: true, cancelable: true })), rep);
  await fire(false);
  expect(await focus()).toBe("length");
  for (let k = 0; k < 5; k++) await fire(true);              // < 1 s — joyida
  expect(await focus()).toBe("length");
  await page.waitForTimeout(1100);
  // > 1 s — dastlabki tezlikning 75 %: 4 ta takrordan 3 tasi katakni suradi (1-takror — kutadi)
  await fire(true);
  expect(await focus()).toBe("length");
  await fire(true);
  await expect.poll(focus).toBe("width");
  await fire(true);
  await expect.poll(focus).toBe("qty");
  await fire(true);
  await expect.poll(focus).toBe("grain");
});

test("TAB: qator ko'k, kursor katagi oq; yangi qator belgilanadi; o'chirilsa — oldingi qator", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "TABC" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`,
    { data: [{ name: "a", length: 700, width: 500, qty: 1 }, { name: "b", length: 600, width: 400, qty: 1 }] });
  const n = async () => (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0].parts.length;
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  const grid = page.locator(".parts-grid").first();
  const selRows = () => grid.locator(".ag-row.ag-row-selected").evaluateAll((rs) =>
    [...new Set(rs.filter((r) => !r.closest(".ag-floating-bottom")).map((r) => Number(r.getAttribute("row-index"))))].sort());
  const cellBg = () => page.evaluate(() => {
    const c = document.activeElement?.closest(".ag-cell") as HTMLElement | null;
    const row = c?.closest(".ag-row") as HTMLElement | null;
    const other = row?.querySelector('.ag-cell:not(.ag-cell-focus)') as HTMLElement | null;
    return { focus: c ? getComputedStyle(c).backgroundColor : "", row: row ? (getComputedStyle(row, "::before").backgroundColor !== "rgba(0, 0, 0, 0)" ? getComputedStyle(row, "::before").backgroundColor : getComputedStyle(row).backgroundColor) : "",
      other: other ? getComputedStyle(other).backgroundColor : "", r: row?.getAttribute("row-index") };
  });
  await grid.locator('.ag-row[row-index="0"] [col-id="name"]').first().click();
  // TAB qator oxiridan keyingi qatorga o'tadi — o'sha qator belgilanadi
  for (let i = 0; i < 30 && (await cellBg()).r !== "1"; i++) await page.keyboard.press("Tab");
  await expect.poll(selRows).toEqual([1]);
  const c1 = await cellBg();
  expect(c1.focus).toBe("rgb(255, 255, 255)");               // kursor katagi oq
  expect(c1.other).not.toBe("rgb(255, 255, 255)");           // qatorning boshqa kataklari oq emas (ko'k qator)
  // oxirgi katakdan keyin — yangi qator belgilanadi
  for (let i = 0; i < 30 && (await n()) === 2; i++) { await page.keyboard.press("Tab"); await page.waitForTimeout(60); }
  await expect.poll(n).toBe(3);
  await page.keyboard.press("Escape");
  await expect.poll(selRows).toEqual([2]);
  // yangi qator o'chiriladi — kursor oldingi qatorga, u belgilanadi
  await page.keyboard.press("Delete");
  const ok = page.getByRole("button", { name: /^(Да|Ok|ОК|Удалить)$/ });
  if (await ok.first().isVisible().catch(() => false)) await ok.first().click();
  await expect.poll(n).toBe(2);
  await expect.poll(selRows).toEqual([1]);
  await expect.poll(async () => (await cellBg()).r).toBe("1");
});
