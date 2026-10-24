// «Остатки: приход / расход» (2026-10-24): yuqori panel varaqlari — kirim: foiz bo'yicha va texnolog tanlovi bilan bazaga yozish;
// chiqim: bazadagi aynan shu material qoldiqlari (tejaydiganlari + detallari sig'adiganlari) → «В раскрой».
import { expect, test, type APIRequestContext } from "@playwright/test";

const SHOT = process.env.SIM_DIR;

async function project(request: APIRequestContext, name: string, opName: string, parts: [number, number, number][]) {
  const pr = await (await request.post("/api/projects", { data: { name } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", name: opName } })).json();
  const cs = p.operations[0].id;
  await request.patch(`/api/projects/${pr.id}/operations/${cs}`, { data: {
    cs_material: { thickness: 16, price: 650000, cost_by_sheets: true }, cs_cut: { use_grain: false } } });
  await request.put(`/api/projects/${pr.id}/operations/${cs}/sheets`, { data: [{ id: "full", length: 2750, width: 1830, qty: 10000 }] });
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`,
    { data: parts.map(([length, width, qty], i) => ({ name: `D${i + 1}`, length, width, qty, grain: false })) });
  await request.post(`/api/projects/${pr.id}/operations/${cs}/optimize?quality=fast`);
  return { pid: pr.id as string, cs: cs as string };
}

test("qoldiq: kirim va chiqim varaqlari", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const mat = `LDSP TABS ${Date.now() % 1e7}`;
  await request.put("/api/settings/remnant_rules/default", { data: { types: [{ type: "LDSP", keep_percent: 30 }] } });
  try {
    // 1) kirim
    const a = await project(request, "Buyurtma A", mat, [[1000, 600, 3], [700, 300, 1]]);
    await page.goto(`/#/p/${a.pid}`);
    await page.locator(".ag-row").filter({ hasText: mat }).first().click();
    await page.getByTestId("tab-rem-in").click();
    await expect(page.getByTestId("rt-in-table")).toBeVisible();
    await expect(page.getByTestId("rt-in")).toContainText("30 %");
    if (SHOT) await page.screenshot({ path: `${SHOT}/t1_kirim.png` });
    // texnolog: mijozga ketadigan bo'lakni omborga olish
    const clientRow = page.locator("tr.rt-client").first();
    const hasClient = await clientRow.count();
    if (hasClient) {
      await clientRow.locator("input[type=radio]").first().click();
      await expect(page.locator("tr.rt-client")).toHaveCount(0);
    }
    if (SHOT) await page.screenshot({ path: `${SHOT}/t2_kirim_tanlov.png` });
    await page.getByTestId("rt-commit").click();
    await expect(page.getByTestId("rt-rollback")).toBeVisible();
    const rows = await (await request.get("/api/remnants", { params: { material_code: mat } })).json();
    expect(rows.length).toBeGreaterThan(0);
    if (SHOT) await page.screenshot({ path: `${SHOT}/t3_kirim_yozildi.png` });

    // 2) chiqim — boshqa buyurtma, nomi kichik harfda
    const b = await project(request, "Buyurtma B", mat.toLowerCase(), [[1000, 600, 9]]);
    await page.goto(`/#/p/${b.pid}`);
    await page.getByTestId("tab-ops").click();
    await page.locator(".ag-row").filter({ hasText: mat.toLowerCase() }).first().click();
    await page.getByTestId("tab-rem-out").click();
    await expect(page.getByTestId("rt-fitting")).toBeVisible({ timeout: 30000 });
    await expect(page.getByTestId("rt-saving")).toBeVisible();
    if (SHOT) await page.screenshot({ path: `${SHOT}/t4_chiqim.png` });
    const big = rows.sort((x: { area_m2: number }, y: { area_m2: number }) => y.area_m2 - x.area_m2)[0];
    await page.getByTestId("rt-saving").getByTestId(`rt-use-${big.id}`).click();
    await expect.poll(async () => (await (await request.get(`/api/projects/${b.pid}`)).json()).operations[0].result?.maps
      ?.some((m: { sheet_id: string }) => m.sheet_id !== "full") ?? false, { timeout: 60000 }).toBe(true);
    await page.waitForTimeout(1500);
    if (SHOT) await page.screenshot({ path: `${SHOT}/t5_chiqim_kroyda.png` });
    await page.getByTestId("tab-rem-in").click();
    await expect(page.getByTestId("rt-in")).toContainText(String(big.id));          // ishlatilgan (sotiladigan) qoldiq
    if (SHOT) await page.screenshot({ path: `${SHOT}/t6_sotiladi.png` });
    expect(errors).toEqual([]);
  } finally {
    await request.put("/api/settings/remnant_rules/default", { data: {} });
  }
});

test("hammasi mijozga — «Записать в базу» o'chiq; sig'may qolgan detallarga mos qoldiq", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const mat = `LDSP LEFT ${Date.now() % 1e7}`;
  await request.put("/api/settings/remnant_rules/default", { data: { types: [{ type: "LDSP", keep_percent: 30 }] } });
  try {
    const a = await project(request, "A", mat, [[1000, 600, 3]]);
    await page.goto(`/#/p/${a.pid}`);
    await page.getByTestId("tab-ops").click();
    await page.locator(".ag-row").filter({ hasText: mat }).first().click();
    await page.getByTestId("tab-rem-in").click();
    for (const row of await page.locator("tr.rt-keep").all()) await row.locator("input[type=radio]").nth(1).click();
    await expect(page.locator("tr.rt-keep")).toHaveCount(0);
    await expect(page.getByTestId("rt-commit")).toBeDisabled();
    await expect(page.getByTestId("rt-nothing")).toBeVisible();
    // ombordagi qoldiq + list soni cheklangan buyurtma: 2 detal sig'maydi
    await request.post("/api/remnants", { data: { material_code: mat, length: 2100, width: 1300, thickness: 16, qty: 1 } });
    const b = await project(request, "B", mat, [[1000, 600, 8]]);
    await request.put(`/api/projects/${b.pid}/operations/${b.cs}/sheets`, { data: [{ id: "one", length: 2750, width: 1830, qty: 1 }] });
    await request.post(`/api/projects/${b.pid}/operations/${b.cs}/optimize?quality=fast`);
    await page.goto(`/#/p/${b.pid}`);
    await page.getByTestId("tab-ops").click();
    await page.locator(".ag-row").filter({ hasText: mat }).first().click();
    await page.getByTestId("tab-rem-out").click();
    await expect(page.getByTestId("rt-left")).toBeVisible({ timeout: 30000 });
    await page.getByTestId("rt-left").locator("button").first().click();
    await expect.poll(async () => (await (await request.get(`/api/projects/${b.pid}`)).json()).operations[0].result?.unplaced?.length ?? -1,
      { timeout: 60000 }).toBe(0);
    expect(errors).toEqual([]);
  } finally {
    await request.put("/api/settings/remnant_rules/default", { data: {} });
  }
});
