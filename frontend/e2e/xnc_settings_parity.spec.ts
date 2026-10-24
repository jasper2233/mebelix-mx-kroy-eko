// «Настройки → XNC Редактор» onlayn oynadagidek (2026-10-23): «Режим» — Выключить / Не строго / Строго; ikki gorizontal teshik guruhi
// (frontal tekislikkacha va detal chetigacha); «Палитра» → «Сверление» paneli — o'chirilsa detal XNC oynasida o'ng panel yo'q.
import { expect, test } from "@playwright/test";

test("XNC sozlamalari: rejim nomlari, yangi cheklov guruhi, «Сверление» paneli", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "XSET" } })).json();
  let p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  p = await (await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "bok", length: 700, width: 400, qty: 1 }] })).json();
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  await page.locator('button[title="XNC Редактор"]').first().click();
  const dlg = page.getByTestId("part-xnc-dialog");
  await expect(dlg.getByTestId("part-xnc-drills")).toBeVisible();
  await dlg.getByTestId("part-xnc-cancel").click();

  // sozlamalar oynasi (XNC operatsiyasi «Параметры» dagi tugma orqali)
  await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "XNC", code: "X", name: "xnc" } });
  await page.reload();
  await page.locator(".ag-row").filter({ hasText: "xnc" }).first().click();
  await page.getByTestId("xnc-editor-settings").click();
  const st = page.getByTestId("xnc-settings");
  await st.getByTestId("xs-tab-limits").click();
  await expect(st.getByTestId("xs-c-mode").locator("option")).toHaveText(["Выключить", "Не строго", "Строго"]);
  await expect(st).toContainText("Минимальное расстояние между центром горизонтального отверстия и краем детали");
  for (const s of ["top", "bottom", "left", "right"]) await expect(st.getByTestId(`xs-c-hole_end_${s}`)).toBeVisible();
  await st.getByTestId("xs-tab-palette").click();
  await expect(st.getByTestId("xs-panels")).toContainText("Сверление");
  await st.getByTestId("xs-panel-drill").uncheck();
  await st.getByTestId("xs-ok").click();
  await expect(st).toHaveCount(0);
  await expect.poll(async () => (await (await request.get("/api/settings/xnc_palette/default")).json()).panels[0].enabled).toBe(false);

  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  await page.locator('button[title="XNC Редактор"]').first().click();
  await expect(page.getByTestId("part-xnc-dialog")).toBeVisible();
  await expect(page.getByTestId("part-xnc-drills")).toHaveCount(0);
  await page.getByTestId("part-xnc-cancel").click();
  await request.put("/api/settings/xnc_palette/default", { data: { items: null, panels: [{ key: "drill", enabled: true }] } });
});
