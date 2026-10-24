// «Редактирование раскроя» (onlayn tizimdagidek, 2026-10-21): o'ng tugma bilan o'chirishdan keyin karta zichlanadi,
// «Развернуть резы» tanlovsiz — butun list (detallar joyida), kartaning zichlash burchagi.
import { expect, test } from "@playwright/test";

type Node = { k: string; a?: string; u?: number; x: number; y: number; l: number; w: number; c?: Node[] };
const parts = (n: Node, out: Node[] = []): Node[] => { (n.c ?? []).forEach((c) => (c.k === "P" ? out.push(c) : c.k === "C" && parts(c, out))); return out; };

test("tahrir: o'chirish zichlaydi, «Развернуть резы» butun listni aylantiradi, burchak saqlanadi", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "EDP" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [
    { name: "E", length: 2168, width: 434, qty: 1, grain: false }, { name: "F", length: 528, width: 402, qty: 1, grain: false }] });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-cut").click();
  await page.getByTestId("btn-edit-cut-empty").click();
  await page.getByTestId("ed-add-map").click();
  for (const len of ["2168", "528"]) {
    await page.locator('[data-testid="cut-editor"] tbody tr').filter({ hasText: len }).first().click();
    await page.getByTestId("ed-auto").click();
  }
  await expect(page.locator('[data-testid="editor-map"] .map-part')).toHaveCount(2);
  // tanlovsiz «Развернуть резы» → vertikal birinchi kesim; burchak — o'ng pastki
  await page.getByTestId("ed-rotate").click();
  await page.getByTestId("ed-corner").selectOption("RB");
  await page.getByTestId("editor-ok").click();
  await expect(page.getByTestId("cut-editor")).toHaveCount(0);
  const m = (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0].result.maps[0];
  const root = m.strips[0] as Node;
  expect(m.pack_corner).toBe("RB");
  expect(root.a).toBe("x");
  const ps = parts(root);
  expect(ps.length).toBe(2);
  expect(Math.max(...ps.map((z) => z.x + z.l))).toBeCloseTo(root.x + root.l, 0);                     // o'ng chetga zichlangan
  // qayta ochib o'ng tugma bilan o'chirish — qolgan detal burchakka suriladi
  await page.getByTestId("btn-edit-cut").click();
  await expect(page.getByTestId("cut-editor")).toBeVisible();
  const before = await page.locator('[data-testid="editor-map"] .map-part').count();
  expect(before).toBe(2);
  const first = page.locator('[data-testid="editor-map"] .map-part').first();
  await first.click({ button: "right" });
  await expect(page.locator('[data-testid="editor-map"] .map-part')).toHaveCount(1);
  await page.getByTestId("editor-ok").click();
  await expect(page.getByTestId("cut-editor")).toHaveCount(0);
  const m2 = (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0].result.maps[0];
  const r2 = m2.strips[0] as Node;
  const [left] = parts(r2);
  expect(left.x + left.l).toBeCloseTo(r2.x + r2.l, 0);
  expect(left.y + left.w).toBeCloseTo(r2.y + r2.w, 0);
  expect(errors).toEqual([]);
});
