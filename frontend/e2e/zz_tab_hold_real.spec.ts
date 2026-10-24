// Haqiqiy klaviatura takrori (CDP autoRepeat, ≈ 30 ms) bilan TAB bosib turish: jadval oxirida qotib qolmaydi — qatorlar bittadan
// qo'shilib, kursor yangi qatorda davom etadi (foydalanuvchi shikoyati 2026-10-21: «pastga qator qo'shilishi qotib qolyapti»).
import { expect, test } from "@playwright/test";

test("bosib turilgan TAB (haqiqiy takror) — qator qo'shish qotmaydi", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "HOLD" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "a", length: 700, width: 500, qty: 1 }] });
  const n = async () => (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0].parts.length;
  const focus = () => page.evaluate(() => {
    const a = document.activeElement as HTMLElement | null;
    return `${a?.closest(".ag-row")?.getAttribute("row-index")}:${a?.closest(".ag-cell")?.getAttribute("col-id")}:${a?.tagName}`;
  });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  await page.locator(".parts-grid").first().locator('.ag-row[row-index="0"] [col-id="name"]').first().click();
  const cdp = await page.context().newCDPSession(page);
  const key = (type: string, rep = false) => cdp.send("Input.dispatchKeyEvent",
    { type, key: "Tab", code: "Tab", windowsVirtualKeyCode: 9, nativeVirtualKeyCode: 9, autoRepeat: rep });
  const hold = async (ms: number) => {
    await key("rawKeyDown");
    const t0 = Date.now();
    await page.waitForTimeout(500);
    while (Date.now() - t0 < ms) { await key("rawKeyDown", true); await page.waitForTimeout(33); }
    await key("keyUp");
  };
  const log: string[] = [];
  await hold(6000); await page.waitForTimeout(800);
  log.push(`hold1 n=${await n()} f=${await focus()}`);
  // yangi qatorlar ekranda darhol, serverga fonda yoziladi — server soni ekrandagiga yetguncha kutiladi
  await expect.poll(async () => Number((await focus()).split(":")[0]) - ((await n()) - 1)).toBe(0);
  const after1 = await n();
  expect(after1).toBeGreaterThanOrEqual(2);                  // oxiridan o'tdi — yangi qator(lar); kursor oxirgi (yangi) qatorda
  // qatorlar bittadan: har yangi qatorga kursor kirgan (bo'sh nomli qatorlar soni = qo'shilganlar)
  for (let i = 0; i < 3; i++) { await key("rawKeyDown"); await key("keyUp"); await page.waitForTimeout(700); log.push(`tap${i} n=${await n()} f=${await focus()}`); }
  await hold(6000); await page.waitForTimeout(800);
  log.push(`hold2 n=${await n()} f=${await focus()}`);
  for (let i = 0; i < 20; i++) { await key("rawKeyDown"); await key("keyUp"); await page.waitForTimeout(250); }
  await page.waitForTimeout(800);
  log.push(`taps20 n=${await n()} f=${await focus()}`);
  console.log(log.join("\n"));
  expect(await n()).toBeGreaterThan(2);
});
