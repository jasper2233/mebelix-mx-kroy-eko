// «Проект → Импортировать»: Ctrl bilan bir nechta loyiha fayli tanlanadi — hammasi ochiq loyihaga qo'shiladi (onlayn tizimdagidek).
import { expect, test } from "@playwright/test";

test("bir nechta loyiha faylini ochiq loyihaga import qilish", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  // manba loyiha: CS + EL + 2 detal (API orqali), JSON sifatida «fayl»
  const src = await (await request.post("/api/projects", { data: { name: "IMP manba" } })).json();
  let p = await (await request.post(`/api/projects/${src.id}/operations`, { data: { type: "EL", code: "K1", name: "Kromka" } })).json();
  p = await (await request.post(`/api/projects/${src.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[p.operations.length - 1].id;
  await request.post(`/api/projects/${src.id}/operations/${cs}/parts`, { data: [{ name: "Yon", length: 700, width: 400, qty: 2 },
    { name: "Polka", length: 500, width: 300, qty: 3 }] });
  const json = Buffer.from(JSON.stringify(await (await request.get(`/api/projects/${src.id}`)).json()));

  await page.goto("/");
  await page.getByTestId("btn-new-project").click();
  await page.getByTestId("ask-input").fill("IMP yig'ma");
  await page.getByTestId("ask-ok").click();
  await expect(page.getByTestId("project-name")).toHaveValue("IMP yig'ma");
  const chooser = page.waitForEvent("filechooser");
  await page.getByTestId("menu-import").click();
  const fc = await chooser;
  expect(fc.isMultiple()).toBe(true);
  await fc.setFiles([{ name: "a.mxk.json", mimeType: "application/json", buffer: json },
    { name: "b.mxk.json", mimeType: "application/json", buffer: json }]);
  await expect(page.locator('[data-testid="ops-grid"] .ag-row')).toHaveCount(4);
  await expect(page.getByTestId("project-name")).toHaveValue("IMP yig'ma");      // loyiha o'zi o'zgarmaydi
  expect(errors).toEqual([]);
});
