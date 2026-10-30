// «Раскроечные станки» (2026-10-30, xodim loyihasi «1275»): operator pilani 3 → 6 qilsa — faqat shu loyihada, sariq
// ogohlantirish va «Вернуть стандарт станка»; keyingi import yana stanok standarti (3). Sintetik Bazis fayli (pila yozilmagan).
import { expect, test } from "@playwright/test";

const BAZIS = `<?xml version="1.0" encoding="UTF-8"?>
<project name="Pila standarti" currency="UZS" version="1">
 <good typeId="product" id="2" count="1" name="Shkaf"><part id="18" name="polka" dl="951" dw="500" count="1"/></good>
 <good typeId="sheet" id="4" t="16" name="LDSP pila" l="2750" w="1830" count="10000" cost="0"/>
 <good typeId="tool.cutting" id="6"/>
 <operation typeId="CS" id="3" tool1="6" l="2750" w="1830" t="16"><material id="4"/><part id="18"/></operation>
</project>`;

test("CS: operator o'zgartirgan pila keyingi loyihaga o'tmaydi, standartga qaytarish tugmasi", async ({ page, request }) => {
  const imp = async () => (await request.post("/api/projects/import", {
    multipart: { file: { name: "pila.project", mimeType: "application/xml", buffer: Buffer.from(BAZIS) } } })).json();
  const sm = await (await request.get("/api/saw-machines")).json();
  const std = sm.machines.find((m: { id: string }) => m.id === sm.my_machine_id).cut.kerf;
  const pr = await imp();
  const cs = pr.operations.find((o: { type: string }) => o.type === "CS");
  expect(cs.cs_cut.kerf).toBe(std);
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP pila" }).first().click();
  await page.getByText("Параметры", { exact: true }).first().click();
  await expect(page.getByTestId("cs-machine")).toBeVisible();
  await expect(page.getByTestId("cs-machine-diff")).toHaveCount(0);
  const kerf = page.getByTestId("cs-kerf");
  await kerf.fill(String(std + 3)); await kerf.press("Enter");
  await expect(page.getByTestId("cs-machine-diff")).toBeVisible();
  // keyingi import — stanok standarti
  const pr2 = await imp();
  expect(pr2.operations.find((o: { type: string }) => o.type === "CS").cs_cut.kerf).toBe(std);
  // «Вернуть стандарт станка»
  await page.getByTestId("cs-machine-restore").click();
  await expect(page.getByTestId("cs-machine-diff")).toHaveCount(0);
  await expect(kerf).toHaveValue(String(std));
  // «Сохранить по умолчанию» oynasi — stanok farqi yo'q
  await page.getByTestId("cs-save-default").click();
  await expect(page.getByTestId("cs-save-std")).toBeVisible();
  await page.getByText("Отмена", { exact: true }).last().click();
});
