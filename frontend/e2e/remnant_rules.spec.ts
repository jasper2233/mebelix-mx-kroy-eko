// «Правила остатков» (2026-10-24): foiz qoidasi sahifasi, ombor holati, qo'lda qo'shishda «m² / %», CS belgisi
// «Использовать остатки со склада» — qoldiq bo'lmasa «на складе нет подходящего остатка».
import { expect, test } from "@playwright/test";

test("qoidalar sahifasi: tur foizi saqlanadi, ombor jadvali va qo'lda qo'shish", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page.getByTestId("side-settings").click();
  await page.getByTestId("settings-remnant_rules").click();
  await expect(page.getByTestId("remnant-rules")).toBeVisible();
  const pct = page.getByTestId("rr-pct-LDSP");
  await pct.fill("30");
  await pct.press("Enter");
  await page.getByTestId("rr-save").click();
  await expect.poll(async () => (await (await request.get("/api/settings/remnant_rules/default")).json()).types)
    .toEqual([{ type: "LDSP", keep_percent: 30 }]);
  // ombor: qo'lda qo'shishda m² va list foizi
  await page.getByTestId("settings-remnants").click();
  await page.getByTestId("rem-add").click();
  await expect(page.getByTestId("rem-add-calc")).toContainText("0.6");
  await expect(page.getByTestId("rem-add-calc")).toContainText("11.9");          // 1000×600 / 2750×1830
  await page.keyboard.press("Escape");
  await page.getByTestId("rem-history").click();
  await expect(page.getByTestId("rem-history-dlg")).toBeVisible();
  await request.put("/api/settings/remnant_rules/default", { data: {} });
  expect(errors).toEqual([]);
});

test("belgi qo'yilgan, mos qoldiq yo'q — xabar", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const code = `NOREM${Date.now() % 1e8}`;
  const pr = await (await request.post("/api/projects", { data: { name: "NOREM" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code, name: "LDSP NOREM" } })).json();
  const cs = p.operations[0].id;
  await request.patch(`/api/projects/${pr.id}/operations/${cs}`, { data: { cs_material: { thickness: 16 }, cs_cut: { use_warehouse: true } } });
  await request.put(`/api/projects/${pr.id}/operations/${cs}/sheets`, { data: [{ id: "full", length: 2750, width: 1830, qty: 10000 }] });
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "A", length: 1000, width: 600, qty: 9 }] });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP NOREM" }).first().click();
  await page.getByTestId("cs-tab-cut").click();
  await page.getByTestId("btn-cut").click();
  await expect(page.getByText(/нет подходящего остатка|mos qoldiq yo'q/)).toBeVisible({ timeout: 30000 });
  await expect(page.getByTestId("remnant-offer")).toHaveCount(0);
  expect(errors).toEqual([]);
});
