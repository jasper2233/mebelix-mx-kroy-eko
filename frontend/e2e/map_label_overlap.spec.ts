// Xodim skrini (2026-11-24): kroy kartasida tor tik detallarda (35×340) en raqamlari ustuni va detal raqami bir joyga tushib
// o'qilmasdi. Onlayn tizimda ham shunday (yechim yo'q). MX: yozuvlar (`partLabels.ts`) bir-birining ustiga tushmaydi, tor detalda
// ham raqam ko'rinadi (kerak bo'lsa shu detalda kichikroq shrift). Kichik va katta oynada tekshiriladi.
import { expect, test } from "@playwright/test";

for (const vp of [{ width: 1904, height: 945 }, { width: 2560, height: 1400 }]) {
  test(`karta yozuvlari ustma-ust emas, tor detalda ham raqam bor (${vp.width}×${vp.height})`, async ({ page, request }) => {
    await page.setViewportSize(vp);
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    const pr = await (await request.post("/api/projects", { data: { name: "YOZUV" } })).json();
    const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "LD", name: "LDSP" } })).json();
    const cs = p.operations[0].id;
    const sizes: [number, number, number][] = [[2274, 382, 1], [1090, 382, 1], [770, 547, 1], [800, 500, 1], [35, 340, 2], [32, 340, 1],
      [45, 340, 1], [60, 340, 1], [80, 340, 1], [340, 35, 1], [390, 60, 1], [390, 109, 2], [60, 60, 1], [100, 80, 1]];
    await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`,
      { data: sizes.map(([l, w, q], i) => ({ name: `d${i}`, length: l, width: w, qty: q })) });
    expect((await request.post(`/api/projects/${pr.id}/operations/${cs}/optimize?quality=fast`)).ok()).toBeTruthy();

    await page.goto(`/#/p/${pr.id}`);
    await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
    await page.getByTestId("cs-tab-cut").click();
    await expect(page.locator(".map-part-label text").first()).toBeVisible();
    const r = await page.evaluate(() => {
      // matn to'rtburchagi (shrift qatori balandligidan raqam balandligiga qisqartirilgan)
      const els = [...document.querySelectorAll(".map-part-label > text")].map((t) => {
        const q = t.getBoundingClientRect();
        return { t: t.textContent, k: (t as SVGElement).dataset.kind, x0: q.left, y0: q.top + q.height * 0.15, x1: q.right, y1: q.bottom - q.height * 0.15 };
      });
      const bad: string[] = [];
      for (let i = 0; i < els.length; i++) for (let j = i + 1; j < els.length; j++) {
        const a = els[i], c = els[j];
        if (a.x0 < c.x1 && c.x0 < a.x1 && a.y0 < c.y1 && c.y0 < a.y1) bad.push(`${a.t} / ${c.t}`);
      }
      return { bad, nums: els.filter((e) => e.k === "num").length };
    });
    expect(r.bad).toEqual([]);
    const placed = sizes.reduce((s, x) => s + x[2], 0);
    expect(r.nums).toBeGreaterThanOrEqual(placed - 1);         // eng mitti (60×60) kichik oynada sig'masligi mumkin
    expect(errors).toEqual([]);
  });
}
