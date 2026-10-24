// XNC «Кодирование» (2026-10-23, onlayn tizimdagidek): savol — Настройки / Ок / Отмена; sozlamalarda ifoda va namuna kod;
// «Ок» — detalga bog'langan XNC kodlari qayta yaratiladi (ifoda + XNC tartib raqami).
import { expect, test } from "@playwright/test";

test("XNC Кодирование: sozlamalar, namuna, qayta kodlash", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "5000 kupe" } })).json();
  let p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L", name: "LMDF" } })).json();
  const cs = p.operations[0].id;
  p = await (await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "tom", length: 1950, width: 600, qty: 1 }] })).json();
  const part = p.operations[0].parts[0];
  p = await (await request.post(`/api/projects/${pr.id}/operations/${cs}/parts/${part.id}/xnc`)).json();
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "XNC" }).first().click();
  await page.getByTestId("xnc-coding-btn").click();
  await expect(page.getByTestId("xnc-coding")).toContainText("Коды XNC обработок будут перекодированы");
  await page.getByTestId("xnc-coding-settings").click();
  await expect(page.getByTestId("xnc-coding-sample")).toHaveText(new RegExp(`^[0-9]{12}25652${String(part.uid).padStart(4, "0")}1$`));
  await page.getByTestId("xnc-coding-expr").fill("'T'+rspace(part.id,3,'0')");
  await page.getByTestId("xnc-coding-side").check();
  await expect(page.getByTestId("xnc-coding-sample")).toHaveText(`T${String(part.uid).padStart(3, "0")}11`);
  await page.getByTestId("xnc-coding-set-ok").click();
  await page.getByTestId("xnc-coding-ok").click();
  const code = `T${String(part.uid).padStart(3, "0")}11`;
  await expect(page.locator('[data-testid="ops-grid"] .ag-row').filter({ hasText: code })).toHaveCount(1);
  // «По умолчанию» — onlayn standart ifoda qaytadi (saqlangani keyingi ochilishda ko'rinadi)
  await page.getByTestId("xnc-coding-btn").click();
  await page.getByTestId("xnc-coding-settings").click();
  await expect(page.getByTestId("xnc-coding-expr")).toHaveValue("'T'+rspace(part.id,3,'0')");
  await page.getByTestId("xnc-coding-default").click();
  await expect(page.getByTestId("xnc-coding-expr")).toHaveValue("now('yyMMddHHmmss')+rspace(crc16(project.name),5,'0')+rspace(part.id,4,'0')");
  await page.getByTestId("xnc-coding-set-ok").click();
  await page.getByTestId("xnc-coding-cancel").click();
});

test("Печать отчета: kodi bo'sh XNC bo'lsa — «Обнаружена XNC операция с пустым кодом!» va «Кодирование»", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "PRINTCODE" } })).json();
  let p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L", name: "LMDF" } })).json();
  const cs = p.operations[0].id;
  p = await (await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "tom", length: 1950, width: 600, qty: 1 }] })).json();
  p = await (await request.post(`/api/projects/${pr.id}/operations/${cs}/parts/${p.operations[0].parts[0].id}/xnc`)).json();
  const xop = p.operations[p.operations.length - 1].id;
  await request.patch(`/api/projects/${pr.id}/operations/${xop}`, { data: { code: "" } });
  await page.goto(`/#/p/${pr.id}`);
  await page.getByRole("button", { name: "Печать отчета" }).first().click();
  await expect(page.getByTestId("xnc-coding-note")).toHaveText("Обнаружена XNC операция с пустым кодом!");
  await page.getByTestId("xnc-coding-ok").click();
  await expect.poll(async () => {
    const pj = await (await request.get(`/api/projects/${pr.id}`)).json();
    return pj.operations.find((o: { id: string }) => o.id === xop).code.length;
  }).toBe(22);
});
