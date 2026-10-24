// Qatorlarni tez-tez bosganda ko'k qator kursordan orqada qolmasin (foydalanuvchi shikoyati 2026-10-21): tanlov tugma BOSILGANDA
// (pointerdown) bo'ladi — avval jadval kutubxonasi uni `click` da (qo'yib yuborilganda, ≈ 60–90 ms keyin) qilardi.
import { expect, test } from "@playwright/test";

test("tez bosishda tanlov kechikishi", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "LAG" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`,
    { data: Array.from({ length: 120 }, (_, i) => ({ name: `p${i}`, length: 300 + i, width: 200, qty: 1 })) });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  const grid = page.locator(".parts-grid").first();
  await grid.locator('.ag-row[row-index="0"] [col-id="length"]').first().click();
  await page.waitForTimeout(500);
  await page.evaluate(() => {
    const w = window as unknown as { __lag: { t: number; ev: string }[] };
    w.__lag = [];
    const t0 = performance.now();
    document.addEventListener("pointerdown", (e) => {
      const r = (e.target as HTMLElement).closest(".ag-row")?.getAttribute("row-index");
      w.__lag.push({ t: performance.now() - t0, ev: `down ${r}` });
    }, true);
    new MutationObserver((ms) => {
      for (const m of ms) {
        const el = m.target as HTMLElement;
        if (m.attributeName !== "class") continue;
        const r = el.getAttribute("row-index") ?? el.closest(".ag-row")?.getAttribute("row-index");
        if (el.classList.contains("ag-row-selected") && !(m.oldValue ?? "").includes("ag-row-selected")) w.__lag.push({ t: performance.now() - t0, ev: `sel ${r}` });
        if (el.classList.contains("ag-cell-focus") && !(m.oldValue ?? "").includes("ag-cell-focus")) w.__lag.push({ t: performance.now() - t0, ev: `focus ${r}` });
      }
    }).observe(document.querySelector(".parts-grid")!, { attributes: true, attributeOldValue: true, subtree: true, attributeFilter: ["class"] });
  });
  for (let i = 1; i <= 10; i++) {
    const b = (await grid.locator(`.ag-row[row-index="${i}"] [col-id="length"]`).first().boundingBox())!;
    await page.mouse.move(b.x + 20, b.y + b.height / 2);
    await page.mouse.down(); await page.waitForTimeout(80); await page.mouse.up();
    await page.waitForTimeout(90);
  }
  await page.waitForTimeout(1500);
  const lag = await page.evaluate(() => (window as unknown as { __lag: { t: number; ev: string }[] }).__lag);
  const downs: Record<string, number> = {};
  const out: string[] = [];
  for (const x of lag) {
    const [k, r] = x.ev.split(" ");
    if (k === "down") downs[r] = x.t;
    else if (downs[r] !== undefined) out.push(`${k} r${r} +${Math.round(x.t - downs[r])}ms`);
  }
  const sel = out.filter((x) => x.startsWith("sel")).map((x) => Number(/\+(\d+)ms/.exec(x)![1]));
  expect(sel.length).toBe(10);
  expect(Math.max(...sel)).toBeLessThan(30);                   // tugma hali bosilib turganda (80 ms) ko'k bo'lgan
});
