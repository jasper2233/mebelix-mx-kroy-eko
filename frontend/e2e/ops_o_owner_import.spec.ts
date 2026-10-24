// «Код/Изделие» (O) — egasi mahsulot nomi (onlayn tizimdagidek). 2026-10-23: loyiha fayli ochiq loyihaga import qilinganda katak
// bo'sh qolardi (jadval qatorlari eski mahsulotlar ro'yxati bilan chizilardi) — endi import va nom o'zgarishida ham ko'rinadi.
import { expect, test } from "@playwright/test";

test("(O) egasi nomi import qilingan loyihada va mahsulot nomi o'zgarganda", async ({ page, request }) => {
  const src = await (await request.post("/api/projects", { data: { name: "O manba" } })).json();
  let p = await (await request.post(`/api/projects/${src.id}/products`, { data: { name: "Модель2", qty: 1 } })).json();
  const prod = p.products[p.products.length - 1].id;
  p = await (await request.post(`/api/projects/${src.id}/operations`, { data: { type: "O", code: "", name: "Комплектующие" } })).json();
  const o = p.operations[p.operations.length - 1];
  await request.patch(`/api/projects/${src.id}/operations/${o.id}`, { data: { o: { ...o.o, owner_product_id: prod } } });
  const json = Buffer.from(JSON.stringify(await (await request.get(`/api/projects/${src.id}`)).json()));

  await page.goto("/");
  await page.getByTestId("btn-new-project").click();
  await page.getByTestId("ask-input").fill("O yig'ma");
  await page.getByTestId("ask-ok").click();
  await expect(page.getByTestId("project-name")).toHaveValue("O yig'ma");
  const chooser = page.waitForEvent("filechooser");
  await page.getByTestId("menu-import").click();
  await (await chooser).setFiles([{ name: "a.mxk.json", mimeType: "application/json", buffer: json }]);
  const row = page.locator('[data-testid="ops-grid"] .ag-row').filter({ hasText: "Комплектующие" });
  await expect(row.locator('[col-id="code"]')).toHaveText("Модель2");
});
