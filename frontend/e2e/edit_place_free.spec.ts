// Kroy tahriri (xodim loyihasi «1275», 2026-10-30): 3-sokl o'ngdagi umumiy bo'sh ustunga (3 qator oxiridagi 3 katak) Shift bilan.
// Sharpa: sokl 1120 — yashil (kataklar birlashadi, detallar joyida); sokl 1150 — sariq: shu joyda pastki qatorda 1 mm qirindi
// qolardi (< «Минимальная обрезка»), shuning uchun list qayta joylanadi. Ikkala holatda 14 detal bitta listda.
import { expect, test, type Page } from "@playwright/test";

type Node = { k: string; a?: string; u?: number; o?: number; x: number; y: number; l: number; w: number; c?: Node[] };
const parts = (n: Node, out: Node[] = []): Node[] => { (n.c ?? []).forEach((c) => (c.k === "P" ? out.push(c) : c.k === "C" && parts(c, out))); return out; };

async function toScreen(page: Page, x: number, y: number) {
  return page.getByTestId("editor-map").evaluate((svg, [px, py]) => {
    const s = svg as unknown as SVGSVGElement;
    const pt = s.createSVGPoint(); pt.x = px; pt.y = py;
    const r = pt.matrixTransform(s.getScreenCTM()!);
    return { x: r.x, y: r.y };
  }, [x, y]);
}

for (const [sl, state] of [[1120, "ok"], [1150, "maybe"]] as const) {
  test(`tahrir: sokl ${sl} o'ngdagi umumiy bo'sh ustunga — sharpa ${state}`, async ({ page, request }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    const pr = await (await request.post("/api/projects", { data: { name: `SOKL ${sl}` } })).json();
    const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "AK", name: "AKRIL" } })).json();
    const cs = p.operations[0].id;
    await request.patch(`/api/projects/${pr.id}/operations/${cs}`, { data: { cs_cut: { kerf: 3, trim_length: 2, trim_width: 2,
      use_grain: false, max_rotations: 4, min_trim_cut: 5 } } });
    const sid = p.operations[0].sheets[0].id;
    await request.put(`/api/projects/${pr.id}/operations/${cs}/sheets`, { data: [{ id: sid, length: 2440, width: 1220, qty: 10000 }] });
    await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [
      { name: "sokl", length: 100, width: sl, qty: 3, grain: false }, { name: "fasad", length: 717, width: 337, qty: 8, grain: false },
      { name: "fasad2", length: 237, width: 604, qty: 3, grain: false }] });
    await request.post(`/api/projects/${pr.id}/operations/${cs}/optimize?quality=fast`);
    const op = (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0];
    const uid = Object.fromEntries(op.parts.map((x: { name: string; uid: number }) => [x.name, x.uid]));
    const P = (x: number, y: number, l: number, w: number, u: number, o = 1): Node => ({ x, y, l, w, k: "P", u, ...(o ? { o: 1 } : {}) });
    const W = (x: number, y: number, l: number, w: number): Node => ({ x, y, l, w, k: "W" });
    const e3 = 5 + 2 * sl + 3;
    const root: Node = { x: 5, y: 5, l: 2430, w: 1210, k: "C", a: "y", c: [
      { x: 5, y: 5, l: 2430, w: 717, k: "C", a: "x", c: [...[0, 1, 2, 3, 4].map((i) => P(5 + 340 * i, 5, 337, 717, uid.fasad)),
        { x: 1705, y: 5, l: 604, w: 717, k: "C", a: "y", c: [0, 1, 2].map((i) => P(1705, 5 + 240 * i, 604, 237, uid.fasad2)) },
        W(2312, 5, 123, 717)] },
      { x: 5, y: 725, l: 2430, w: 337, k: "C", a: "x", c: [...[0, 1, 2].map((i) => P(5 + 720 * i, 725, 717, 337, uid.fasad, 0)), W(2165, 725, 270, 337)] },
      { x: 5, y: 1065, l: 2430, w: 100, k: "C", a: "x", c: [P(5, 1065, sl, 100, uid.sokl), P(8 + sl, 1065, sl, 100, uid.sokl), W(e3 + 3, 1065, 2435 - e3 - 3, 100)] },
      W(5, 1168, 2430, 47)] };
    const put = await request.put(`/api/projects/${pr.id}/operations/${cs}/result`,
      { data: { ...op.result, maps: [{ ...op.result.maps[0], strips: [root], placements: [] }], unplaced: [] } });
    expect(put.status()).toBe(200);

    await page.goto(`/#/p/${pr.id}`);
    await page.locator(".ag-row").filter({ hasText: "AKRIL" }).first().click();
    await page.getByTestId("cs-tab-cut").click();
    await page.getByTestId("btn-edit-cut").click();
    const ed = page.getByTestId("cut-editor");
    await expect(ed).toBeVisible();
    await expect(page.locator('[data-testid="editor-map"] .map-part')).toHaveCount(13);
    await ed.locator("tbody tr").filter({ hasText: String(sl) }).first().click();
    const s = await toScreen(page, 2370, 100);
    await page.mouse.move(s.x - 20, s.y - 20);
    await page.keyboard.down("Shift");
    await page.mouse.move(s.x, s.y, { steps: 5 });
    await expect(page.getByTestId("map-ghost")).toHaveAttribute("data-state", state);
    await page.mouse.click(s.x, s.y);
    await page.keyboard.up("Shift");
    await expect(page.locator('[data-testid="editor-map"] .map-part')).toHaveCount(14);
    await page.getByTestId("editor-ok").click();
    await expect(ed).toHaveCount(0);
    const m = (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0].result;
    expect(m.maps.length).toBe(1);
    expect(parts(m.maps[0].strips[0]).length).toBe(14);
    expect(errors).toEqual([]);
  });
}
