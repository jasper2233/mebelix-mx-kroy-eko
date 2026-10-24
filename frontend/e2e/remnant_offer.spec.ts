// Ombordagi qoldiq taklifi (2026-10-24): kesish butun listdan; oxirgi list detallari ombordagi qoldiqqa sig'sa — «Остаток со склада»
// oynasi; «Кроить из остатка» — qoldiq qo'shiladi va qayta kesiladi (1 butun list + qoldiq); «Нет, целый лист» — o'zgarmaydi.
import { expect, test, type APIRequestContext } from "@playwright/test";

async function setup(request: APIRequestContext) {
  const code = `RO${Date.now() % 1e8}`;
  const pr = await (await request.post("/api/projects", { data: { name: "RO" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code, name: "LDSP RO" } })).json();
  const cs = p.operations[0].id;
  await request.patch(`/api/projects/${pr.id}/operations/${cs}`, { data: { cs_material: { thickness: 16 } } });
  await request.put(`/api/projects/${pr.id}/operations/${cs}/sheets`, { data: [{ id: "full", length: 2750, width: 1830, qty: 10000 }] });
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "A", length: 1000, width: 600, qty: 9 }] });
  const rem = await (await request.post("/api/remnants", { data: { material_code: code, length: 2100, width: 1300, thickness: 16, qty: 1 } })).json();
  return { pid: pr.id as string, cs: cs as string, rid: rem.id as number };
}

for (const accept of [true, false]) {
  test(`qoldiq taklifi — ${accept ? "qabul" : "rad"}`, async ({ page, request }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    const { pid, rid } = await setup(request);
    const op = async () => (await (await request.get(`/api/projects/${pid}`)).json()).operations[0];
    await page.goto(`/#/p/${pid}`);
    await page.locator(".ag-row").filter({ hasText: "LDSP RO" }).first().click();
    await page.getByTestId("cs-tab-cut").click();
    await page.getByTestId("btn-cut").click();
    await expect(page.getByTestId("remnant-offer")).toBeVisible({ timeout: 30000 });
    await expect(page.getByTestId(`ro-row-${rid}`)).toBeVisible();
    await page.getByTestId(accept ? "ro-use" : "ro-no").click();
    await expect(page.getByTestId("remnant-offer")).toBeHidden();
    if (accept) {
      await expect.poll(async () => (await op()).result?.maps?.map((m: { sheet_id: string }) => m.sheet_id === "full").join(","),
        { timeout: 30000 }).toBe("true,false");
      expect((await op()).sheets.some((s: { source_remnant_id: number | null }) => s.source_remnant_id === rid)).toBe(true);
    } else {
      const o = await op();
      expect(o.result.maps.every((m: { sheet_id: string }) => m.sheet_id === "full")).toBe(true);
      expect(o.sheets.some((s: { source_remnant_id: number | null }) => s.source_remnant_id === rid)).toBe(false);
    }
    expect(errors).toEqual([]);
  });
}
