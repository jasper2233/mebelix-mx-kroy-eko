// O'lchov: bosib turilgan TAB (haqiqiy takror) — har katakka o'tish vaqti; yangi qator qo'shilishidagi pauza.
import { test } from "@playwright/test";

test("TAB hold timing", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "TIME" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "a", length: 700, width: 500, qty: 1 }] });
  // xodimlar tunnelidagidek: detal qo'shish so'roviga 500 ms kechikish
  await page.route("**/operations/*/parts", async (route) => {
    if (route.request().method() === "POST") await new Promise((r) => setTimeout(r, 500));
    await route.continue();
  });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  await page.locator(".parts-grid").first().locator('.ag-row[row-index="0"] [col-id="name"]').first().click();
  await page.evaluate(() => {
    const w = window as unknown as { __log: string[] };
    w.__log = [];
    let last = "";
    const t0 = performance.now();
    const tick = () => {
      const a = document.activeElement as HTMLElement | null;
      const k = `${a?.closest(".ag-row")?.getAttribute("row-index")}:${a?.closest(".ag-cell")?.getAttribute("col-id")}`;
      if (k !== last) { w.__log.push(`${Math.round(performance.now() - t0)} ${k}`); last = k; }
      requestAnimationFrame(tick);
    };
    tick();
    const of = window.fetch;
    window.fetch = async (...args) => { const s = performance.now(); const r = await of(...args);
      w.__log.push(`${Math.round(s - t0)}-${Math.round(performance.now() - t0)} FETCH ${String(args[0]).replace(/^.*\/api/, "")} ${(args[1] as RequestInit | undefined)?.method ?? "GET"}`); return r; };
  });
  const cdp = await page.context().newCDPSession(page);
  const key = (type: string, rep = false) => cdp.send("Input.dispatchKeyEvent", { type, key: "Tab", code: "Tab", windowsVirtualKeyCode: 9, autoRepeat: rep });
  await key("rawKeyDown");
  const t0 = Date.now();
  await page.waitForTimeout(500);
  while (Date.now() - t0 < 5000) { await key("rawKeyDown", true); await page.waitForTimeout(33); }
  await key("keyUp");
  console.log((await page.evaluate(() => (window as unknown as { __log: string[] }).__log)).join("\n"));
});
