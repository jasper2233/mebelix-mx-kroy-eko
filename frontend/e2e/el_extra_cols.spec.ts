// EL «Детали»: onlayn tizimdagidek 60 ta ustun (8 asosiy + 52 qo'shimcha, standart yashirin); qo'shimchalarni «Настройки» da yoqish —
// qiymatlar detal, mahsulot va kromka operatsiyasidan olinadi.
import { expect, test } from "@playwright/test";

test("EL «Детали»: qo'shimcha ustunlar (Изделие-Код, ОВ Код, Пл. Дл.)", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "ELX" } })).json();
  let p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "EL", code: "K-19", name: "Kromka oq" } })).json();
  const el = p.operations[0].id;
  p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[1].id;
  const prod = p.products[0];
  await request.patch(`/api/projects/${pr.id}/products/${prod.id}`, { data: { code: "P-77" } });
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [
    { name: "Yon", length: 700, width: 400, qty: 2, product_id: prod.id, edge_top: { op_id: el } }] });

  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "Kromka oq" }).first().click();
  await page.locator(".tabs button, .tabs [role=tab]").filter({ hasText: "Детали" }).first().click();
  await page.locator('button[title^="Настройки"]').last().click();
  const dlg = page.getByTestId("el_columns-settings");
  await expect(dlg.locator("tbody tr")).toHaveCount(60);
  for (const k of ["product_code", "e_top_code", "saw_l"]) await page.getByTestId(`cols-on-${k}`).check();
  await page.getByTestId("cols-ok").click();
  await page.getByTestId("ask-input").fill("ELX profil");
  await page.getByTestId("ask-ok").click();
  const cell = (id: string) => page.locator(`.ag-row[row-index="0"] [col-id="${id}"]`).first();
  await expect(cell("product_code")).toHaveText("P-77");
  await expect(cell("e_top_code")).toHaveText("K-19");
  await expect(cell("saw_l")).toHaveText(/^\d+/);
  expect(errors).toEqual([]);
});
