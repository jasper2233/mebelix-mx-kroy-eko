// «Детали на остаток» (2026-10-25): «Остатки: расход» → qoldiq yonida tugma → oyna: avto / qo'lda tanlov (soni bilan);
// tanlov detallar ro'yxatiga yoziladi; sig'masa — «не помещаются», kroy boshlanmaydi.
import { expect, test, type APIRequestContext } from "@playwright/test";

const SHOT = process.env.SIM_DIR;
const P4421: [string, number, number, number][] = [["D1", 459, 520, 3], ["D2", 2385, 427, 1], ["D3", 2385, 449, 1], ["D4", 1400, 100, 2],
  ["D5", 1400, 70, 2], ["D6", 1377, 330, 2], ["D7", 1400, 330, 2], ["D8", 459, 485, 3]];

async function setup(request: APIRequestContext) {
  const mat = `LDSP RA ${Date.now() % 1e7}`;
  const pr = await (await request.post("/api/projects", { data: { name: "Qoldiqqa detal" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", name: mat } })).json();
  const cs = p.operations[0].id;
  await request.patch(`/api/projects/${pr.id}/operations/${cs}`, { data: { cs_material: { thickness: 16, price: 650000, cost_by_sheets: true }, cs_cut: { use_grain: false } } });
  await request.put(`/api/projects/${pr.id}/operations/${cs}/sheets`, { data: [{ id: "full", length: 2750, width: 1830, qty: 10000 }] });
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: P4421.map(([name, length, width, qty]) => ({ name, length, width, qty, grain: false })) });
  const rem = await (await request.post("/api/remnants", { data: { material_code: mat, length: 2500, width: 650, thickness: 16, qty: 1 } })).json();
  return { pid: pr.id as string, cs: cs as string, rid: rem.id as number, mat };
}

test("qoldiqqa detal: avto tanlash va kesish; sig'maydigan qo'lda tanlov — xabar", async ({ page, request }) => {
  test.setTimeout(180000);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const { pid, cs, rid, mat } = await setup(request);
  await page.goto(`/#/p/${pid}`);
  await page.getByTestId("tab-ops").click();
  await page.locator(".ag-row").filter({ hasText: mat }).first().click();
  await page.getByTestId("tab-rem-out").click();
  await page.getByTestId(`rt-fitting-pick-${rid}`).click();
  const dlg = page.getByTestId("remnant-assign");
  await expect(dlg).toBeVisible();
  if (SHOT) await page.screenshot({ path: `${SHOT}/a1_oyna.png` });
  // qo'lda: D2 + D3 (2385 lik ikkalasi) — 650 ga sig'maydi
  const op0 = (await (await request.get(`/api/projects/${pid}`)).json()).operations[0];
  const id = (n: string) => op0.parts.find((x: { name: string }) => x.name === n).id as string;
  await page.getByTestId(`ra-check-${id("D2")}`).check();
  await page.getByTestId(`ra-check-${id("D3")}`).check();
  await page.getByTestId("ra-save-cut").click();
  await expect(page.getByTestId("ra-err")).toContainText(/не помещаются|sig'maydi/);
  if (SHOT) await page.screenshot({ path: `${SHOT}/a2_sigmaydi.png` });
  const after0 = (await (await request.get(`/api/projects/${pid}`)).json()).operations[0];
  expect(after0.parts.every((x: { remnant_id: number | null }) => x.remnant_id == null)).toBe(true);   // hech narsa saqlanmadi
  // avto
  await page.getByTestId("ra-auto").click();
  await expect(page.getByTestId("ra-note")).toBeVisible({ timeout: 60000 });
  if (SHOT) await page.screenshot({ path: `${SHOT}/a3_avto.png` });
  await page.getByTestId("ra-save-cut").click();
  await expect(dlg).toBeHidden({ timeout: 60000 });
  const op = (await (await request.get(`/api/projects/${pid}`)).json()).operations[0];
  const remSheet = op.sheets.find((s: { source_remnant_id: number | null }) => s.source_remnant_id === rid).id;
  expect(op.result.maps.length).toBe(2);
  expect(op.result.maps.some((m: { sheet_id: string }) => m.sheet_id === remSheet)).toBe(true);
  expect(op.parts.some((x: { remnant_id: number | null }) => x.remnant_id === rid)).toBe(true);
  await expect(page.getByTestId("rt-bound")).toBeVisible();
  if (SHOT) await page.screenshot({ path: `${SHOT}/a4_kesildi.png` });
  void cs;
  expect(errors).toEqual([]);
});
