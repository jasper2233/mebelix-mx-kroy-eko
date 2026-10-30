// «По умолчанию» (2026-10-26, foydalanuvchi qoidasi): CS va EL parametrlarida tugma MebeliX Kroy tavsiya qilgan parametrlarni
// qo'yadi (kroy sifati, zich joylash, arrada qulay kesish); qalinlik, narx, tekstura o'zgarmaydi; keyingi loyihalar uchun ham standart.
import { expect, test } from "@playwright/test";

test("CS / EL «По умолчанию» — tavsiya qilingan parametrlar", async ({ page, request }) => {
  const base = { cs: await (await request.get("/api/settings/cs_defaults/default")).json(),
    el: await (await request.get("/api/settings/el_defaults/default")).json() };
  try {
    const pr = await (await request.post("/api/projects", { data: { name: "Tavsiya" } })).json();
    let p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", name: "LDSP tavsiya" } })).json();
    const cs = p.operations.at(-1).id;
    p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "EL", name: "kromka tavsiya" } })).json();
    const el = p.operations.at(-1).id;
    await request.patch(`/api/projects/${pr.id}/operations/${cs}`, { data: { cs_cut: { trim_length: 9, kerf: 4.4, max_rotations: 6 },
      cs_material: { thickness: 18, min_part_size: 50 } } });
    await request.patch(`/api/projects/${pr.id}/operations/${el}`, { data: { el: { overhang: 12, min_glue_length: 0, width: 22 } } });
    await page.goto(`/#/p/${pr.id}`);
    await page.locator(".ag-row").filter({ hasText: "LDSP tavsiya" }).first().click();
    await page.getByTestId("cs-apply-default").click();
    await page.getByTestId("ask-ok").click();
    await expect.poll(async () => {
      const o = (await (await request.get(`/api/projects/${pr.id}`)).json()).operations.find((x: { id: string }) => x.id === cs);
      return [o.cs_cut.trim_length, o.cs_cut.kerf, o.cs_cut.max_rotations, o.cs_material.min_part_size, o.cs_material.thickness];
    }).toEqual([2, 3, 4, 30, 18]);
    await page.locator(".ag-row").filter({ hasText: "kromka tavsiya" }).first().click();
    await page.getByTestId("el-apply-default").click();
    await page.getByTestId("ask-ok").click();
    await expect.poll(async () => {
      const o = (await (await request.get(`/api/projects/${pr.id}`)).json()).operations.find((x: { id: string }) => x.id === el);
      return [o.el.overhang, o.el.min_glue_length, o.el.min_perp_side, o.el.width];
    }).toEqual([30, 100, 40, 22]);
    // keyingi yangi CS — material parametrlari tavsiyadan; stanok parametrlari (pila, вращения …) — stanok standartidan
    // (2026-10-30: operator / tavsiya tugmasi stanok standartini o'zgartirmaydi — faqat «Раскроечные станки», parol bilan)
    const sm = await (await request.get("/api/saw-machines")).json();
    const std = sm.machines.find((m: { id: string }) => m.id === sm.my_machine_id).cut;
    p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", name: "keyingi" } })).json();
    expect(p.operations.at(-1).cs_cut.max_rotations).toBe(std.max_rotations);
    expect(p.operations.at(-1).cs_material.min_part_size).toBe(30);
  } finally {
    await request.put("/api/settings/cs_defaults/default", { data: base.cs });
    await request.put("/api/settings/el_defaults/default", { data: base.el });
  }
});
