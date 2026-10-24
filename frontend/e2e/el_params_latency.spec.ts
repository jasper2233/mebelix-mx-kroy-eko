// (EL) «Параметры»: sekin tarmoqda (tunnel) ketma-ket Enter bilan saqlangan qiymatlar ekranda eskisiga qaytmaydi (2026-10-23).
// Oldingi PATCH javobi keyingisidan KEYIN kelsa, eski loyiha keshga yozilib, «Мин. размер стороны» 40 → eski 0 ga qaytardi
// (bazada to'g'ri edi). Endi loyiha `rev` bilan: eskiroq javob keshga yozilmaydi.
import { expect, test } from "@playwright/test";

test("EL: kechikkan javoblar kiritilgan qiymatni qaytarmaydi", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "EL lat" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "EL", name: "kromka 1-19" } })).json();
  const oid = p.operations[0].id;
  await request.patch(`/api/projects/${pr.id}/operations/${oid}`, { data: { el: { overhang: 20, min_glue_length: 0, min_perp_side: 0 } } });
  let k = 0;
  await page.route("**/api/**", async (route) => {
    const r = await route.fetch();
    const body = await r.body();
    const d = route.request().method() === "PATCH" ? [1500, 300, 900][k++ % 3] : 200;   // javoblar tartibsiz
    await new Promise((res) => setTimeout(res, d));
    await route.fulfill({ response: r, body });
  });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "kromka 1-19" }).first().click();
  const fld = (label: string) => page.locator(".field").filter({ hasText: label }).locator("input").first();
  await expect(fld("Длина остатка по краям")).toHaveValue("20");
  const L: [string, string][] = [["Длина остатка по краям", "30"], ["Мин. оклеиваемая длина", "100"], ["Минимальный размер стороны", "40"]];
  for (const [lab, v] of L) {
    const i = fld(lab);
    await i.click(); await i.fill(v); await i.press("Enter");
    await page.waitForTimeout(150);
  }
  await page.waitForTimeout(3500);                       // hamma javoblar kelib bo'ldi
  for (const [lab, v] of L) await expect(fld(lab)).toHaveValue(v);
  const el = (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0].el;
  expect([el.overhang, el.min_glue_length, el.min_perp_side]).toEqual([30, 100, 40]);
});
