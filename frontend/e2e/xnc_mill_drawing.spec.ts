// XNC frezalash chizmasi (2026-10-21): freza izi, boshlanish nuqtasi, skvoz kesim ajratadigan bo'lak (och).
// «Подрезка на выходе» 2026-10-22 da olib tashlandi — chizmada ham, ish panelida ham yo'q.
import { expect, test } from "@playwright/test";

test("XNC: freza izi va ajratilgan bo'lak, oldindan kesim yo'q", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "XPC" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "XNC", code: "STOL", name: "stoleshnitsa" } })).json();
  const xop = p.operations[0].id;
  const program = [
    { cmd: "MillStart", params: { X: -30, Y: 550, DP: "dz", T: "Mill4", D: 4, C: 1 }, comment: "", enabled: true, children: [] },
    { cmd: "MillLine", params: { X: 700, Y: 550 }, comment: "", enabled: true, children: [] },
    { cmd: "MillArcCenter", params: { X: 950, Y: 800, CX: 700, CY: 800, DIR: "true" }, comment: "", enabled: true, children: [] },
    { cmd: "MillLine", params: { X: 950, Y: 1430 }, comment: "", enabled: true, children: [] }];
  await request.patch(`/api/projects/${pr.id}/operations/${xop}`, { data: { xnc: { by_part_size: false, length: 1500, width: 1400, thickness: 16, program } } });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "stoleshnitsa" }).first().click();
  const draw = page.getByTestId("xnc-drawing");
  await expect(draw.locator(".xnc-band")).toHaveCount(1);
  await expect(draw.locator(".xnc-mill-start")).toHaveCount(1);
  await expect(draw.locator(".xnc-cutoff")).toHaveCount(1);
  await expect(draw.locator(".xnc-precut")).toHaveCount(0);
  await expect(page.getByTestId("xnc-precut")).toHaveCount(0);
  await page.getByTestId("xnc-tab-program").click();
  await expect(page.getByTestId("xnc-precut-btn")).toHaveCount(0);
  expect(errors).toEqual([]);
});
