// (EL) «Параметры» eslab qolinadi (2026-10-25, foydalanuvchi): qo'yilgan qiymatlar sahifa qayta ochilganda (qayta kirish) ham
// turadi va keyingi import qilingan kromka shu qiymatlar bilan keladi — foydalanuvchi o'zi o'zgartirmaguncha. Onlayn tizimdagidek
// Enter ham, boshqa joyni bosish ham saqlaydi. Sintetik Bazis fayli (EL qiymatlarisiz).
import { expect, test } from "@playwright/test";

const BAZIS = `<?xml version="1.0" encoding="UTF-8"?>
<project name="EL eslab qolish" currency="UZS" version="1">
 <good typeId="product" id="2" count="1" name="Shkaf"><part id="18" name="polka" dl="951" dw="500" count="1" elt="@operation#1"/></good>
 <good typeId="sheet" id="4" t="16" name="LDSP" l="2750" w="1830" count="10000" cost="0"/>
 <good typeId="band" id="5" t="1" w="19" name="1-19 eslab" code="KP-1/19-E"/>
 <operation typeId="CS" id="3" l="2750" w="1830" t="16"><material id="4"/><part id="18"/></operation>
 <operation typeId="EL" id="1" tool1="4"><material id="5"/><part id="18"/></operation>
</project>`;

test("EL: qo'yilgan parametrlar qayta kirishda va keyingi importda saqlanadi", async ({ page, request }) => {
  const base = await (await request.get("/api/settings/el_defaults/default")).json();
  const imp = async () => (await request.post("/api/projects/import", {
    multipart: { file: { name: "el_eslab.project", mimeType: "application/xml", buffer: Buffer.from(BAZIS) } } })).json();
  try {
    await request.put("/api/settings/el_defaults/default", { data: { ...base, overhang: 20, min_glue_length: 0, min_perp_side: 0 } });
    const pr = await imp();
    await page.goto(`/#/p/${pr.id}`);
    await page.locator(".ag-row").filter({ hasText: "1-19 eslab" }).first().click();
    const fld = (label: string) => page.locator(".field").filter({ hasText: label }).locator("input").first();
    await expect(fld("Длина остатка по краям")).toHaveValue("20");
    // 1) Enter bilan, 2) Enter siz — keyingi maydonni bosib, 3) Enter siz — bo'sh joyni bosib
    await fld("Длина остатка по краям").fill("30"); await fld("Длина остатка по краям").press("Enter");
    await fld("Мин. оклеиваемая длина").click(); await fld("Мин. оклеиваемая длина").fill("100");
    await fld("Минимальный размер стороны").click(); await fld("Минимальный размер стороны").fill("40");
    await page.locator(".form-h").first().click();
    await page.waitForTimeout(1200);
    await page.reload();                                                    // qayta kirish
    await page.locator(".ag-row").filter({ hasText: "1-19 eslab" }).first().click();
    await expect(fld("Длина остатка по краям")).toHaveValue("30");
    await expect(fld("Мин. оклеиваемая длина")).toHaveValue("100");
    await expect(fld("Минимальный размер стороны")).toHaveValue("40");
    // keyingi loyiha importi — oxirgi qo'yilgan qiymatlar
    const pr2 = await imp();
    const el2 = pr2.operations.find((o: { type: string }) => o.type === "EL").el;
    expect([el2.overhang, el2.min_glue_length, el2.min_perp_side]).toEqual([30, 100, 40]);
  } finally {
    await request.put("/api/settings/el_defaults/default", { data: base });
  }
});
