// «Раскрой» kartasi: sichqoncha g'ildiragi — kursor turgan nuqta atrofida kattalashtirish / kichraytirish (nuqta joyida qoladi).
import { expect, test } from "@playwright/test";

test("kroy kartasi: g'ildirak bilan kursor nuqtasi atrofida zoom", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "ZOOM" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "a", length: 700, width: 500, qty: 8 }, { name: "b", length: 300, width: 200, qty: 10 }] });
  await request.post(`/api/projects/${pr.id}/operations/${cs}/optimize`, { data: { quality: "fast" } });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.locator(".tabs button").filter({ hasText: "Раскрой" }).first().click();
  const vp = page.getByTestId("cut-viewport");
  await expect(vp).toBeVisible();
  const box = (await vp.boundingBox())!;
  const mx = box.x + box.width * 0.7, my = box.y + box.height * 0.6;
  const svgPt = () => page.evaluate(([x, y]) => {
    const svg = document.querySelector('[data-testid="cut-map"]') as SVGSVGElement;
    const pt = svg.createSVGPoint(); pt.x = x; pt.y = y;
    const q = pt.matrixTransform(svg.getScreenCTM()!.inverse()); return [q.x, q.y];
  }, [mx, my]);
  const before = await svgPt();
  await page.mouse.move(mx, my);
  for (let i = 0; i < 4; i++) { await page.mouse.wheel(0, -100); await page.waitForTimeout(80); }
  await expect.poll(async () => Number(await vp.getAttribute("data-zoom"))).toBeGreaterThan(1.5);
  const after = await svgPt();                                          // kursor ostidagi list nuqtasi o'zgarmadi
  expect(Math.abs(after[0] - before[0])).toBeLessThan(40);
  expect(Math.abs(after[1] - before[1])).toBeLessThan(40);
  for (let i = 0; i < 8; i++) { await page.mouse.wheel(0, 100); await page.waitForTimeout(60); }
  await expect.poll(async () => Number(await vp.getAttribute("data-zoom"))).toBe(1);
});
