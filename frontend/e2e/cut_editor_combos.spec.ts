// «Редактирование листового раскроя» — onlayn yordamdagi barcha sichqoncha / klaviatura kombinatsiyalari haqiqiy brauzerda
// (2026-10-23 audit): Ctrl+bosish (ko'p tanlash), Del / o'ng tugma, Ctrl+Z / Ctrl+Y, Ctrl+C, Ctrl+R, Ctrl+F, Ctrl+←/→,
// Home / End / ↑ / ↓ (kartalar), Ctrl+↑/↓ (karta tartibi), Shift+bosish (qo'yish), Shift+Ctrl / Shift+Alt (burib qo'yish),
// Shift+A (ko'p qo'yish), Shift+W (blok), F9.
import { expect, test, type Page } from "@playwright/test";

const parts = (page: Page) => page.locator('[data-testid="editor-map"] .map-part');
const svgHtml = (page: Page) => page.getByTestId("editor-map").evaluate((e) => e.innerHTML);
const activeThumb = (page: Page) => page.locator(".thumb-active span").innerText();

async function freeSpot(page: Page, fx = 0.82, fy = 0.8) {
  const b = (await page.getByTestId("editor-map").boundingBox())!;
  return { x: b.x + b.width * fx, y: b.y + b.height * fy };
}

test("kroy muharriri: barcha kombinatsiyalar", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "CSE combos" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [
    { name: "A", length: 500, width: 300, qty: 12, grain: false }, { name: "B", length: 400, width: 200, qty: 12, grain: false }] });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-cut").click();
  await page.getByTestId("btn-edit-cut-empty").click();
  const ed = page.getByTestId("cut-editor");
  await page.getByTestId("ed-add-map").click();
  const rowA = ed.locator("tbody tr").filter({ hasText: "500" }).first();
  const rowB = ed.locator("tbody tr").filter({ hasText: "400" }).first();
  await rowA.click();
  await page.getByTestId("ed-auto").click();                       // A — 1 dona avtomatik
  await expect(parts(page)).toHaveCount(1);

  // Shift+bosish — tanlangan detal bo'sh joyga qo'yiladi
  let s = await freeSpot(page);
  await page.keyboard.down("Shift");
  await page.mouse.click(s.x, s.y);
  await page.keyboard.up("Shift");
  await expect(parts(page)).toHaveCount(2);
  // Shift+Ctrl+bosish — burib qo'yish (B)
  await rowB.click();
  s = await freeSpot(page, 0.55, 0.85);
  await page.keyboard.down("Shift"); await page.keyboard.down("Control");
  await page.mouse.click(s.x, s.y);
  await page.keyboard.up("Control"); await page.keyboard.up("Shift");
  await expect(parts(page)).toHaveCount(3);
  // Shift+A+bosish — ko'p qo'yish (bo'sh joy to'ladi: 1 tadan ko'p)
  s = await freeSpot(page, 0.9, 0.3);
  await page.keyboard.down("Shift"); await page.keyboard.down("a");
  await page.mouse.click(s.x, s.y);
  await page.keyboard.up("a"); await page.keyboard.up("Shift");
  await expect.poll(() => parts(page).count()).toBeGreaterThan(4);
  const nAfterMulti = await parts(page).count();

  // Ctrl+bosish — 2 ta detal tanlash; Del; Ctrl+Z; Ctrl+Y; Ctrl+Z
  const p0 = (await parts(page).nth(0).boundingBox())!, p1 = (await parts(page).nth(1).boundingBox())!;
  await page.mouse.click(p0.x + p0.width / 2, p0.y + p0.height / 2);
  await page.keyboard.down("Control");
  await page.mouse.click(p1.x + p1.width / 2, p1.y + p1.height / 2);
  await page.keyboard.up("Control");
  await expect(page.getByTestId("ed-sel-count")).toContainText("2");
  await page.keyboard.press("Delete");
  await expect(parts(page)).toHaveCount(nAfterMulti - 2);
  await page.keyboard.press("Control+z");
  await expect(parts(page)).toHaveCount(nAfterMulti);
  await page.keyboard.press("Control+y");
  await expect(parts(page)).toHaveCount(nAfterMulti - 2);
  await page.keyboard.press("Control+z");
  await expect(parts(page)).toHaveCount(nAfterMulti);
  // o'ng tugma — o'chirish
  const p2 = (await parts(page).last().boundingBox())!;
  await page.mouse.click(p2.x + p2.width / 2, p2.y + p2.height / 2, { button: "right" });
  await expect(parts(page)).toHaveCount(nAfterMulti - 1);
  await page.keyboard.press("Control+z");
  await expect(parts(page)).toHaveCount(nAfterMulti);
  // Ctrl+C — klonlash (bo'sh joy bor)
  await page.mouse.click(p0.x + p0.width / 2, p0.y + p0.height / 2);
  await page.keyboard.press("Control+c");
  await expect(parts(page)).toHaveCount(nAfterMulti + 1);
  // Ctrl+→ / Ctrl+← — chizma o'zgaradi
  const selX = () => page.getByTestId("map-sel").first().getAttribute("x");
  await page.mouse.click(p0.x + p0.width / 2, p0.y + p0.height / 2);
  await expect.poll(selX).toBe("5");
  await page.keyboard.press("Control+ArrowRight");                   // tanlov detal bilan birga o'ngga
  await expect.poll(selX).not.toBe("5");
  await page.keyboard.press("Control+ArrowLeft");
  await expect.poll(selX).toBe("5");
  let h: string;
  // Ctrl+R — tanlovsiz butun list aylantiriladi
  s = await freeSpot(page, 0.5, 0.93);                                // list darajasidagi bo'sh joy — tanlov yo'qoladi
  await page.mouse.click(s.x, s.y);
  await expect(page.getByTestId("map-sel")).toHaveCount(0);
  h = await svgHtml(page);
  await page.keyboard.press("Control+r");
  await expect.poll(() => svgHtml(page)).not.toBe(h);
  await page.keyboard.press("Control+z");
  // Ctrl+F — faqat qolgan detallar filtri (standart: yoqilgan, onlayndagidek)
  await expect(page.getByTestId("ed-only-left")).toHaveClass(/ibtn-active/);
  await page.keyboard.press("Control+f");
  await expect(page.getByTestId("ed-only-left")).not.toHaveClass(/ibtn-active/);
  await page.keyboard.press("Control+f");
  await expect(page.getByTestId("ed-only-left")).toHaveClass(/ibtn-active/);

  // kartalar: yana 2 ta karta; Home / End / ↑ / ↓; Ctrl+↑ / Ctrl+↓
  await page.getByTestId("ed-add-map").click();
  await page.getByTestId("ed-add-map").click();
  await expect(page.locator(".thumbs-row .thumb")).toHaveCount(3);
  await page.getByTestId("editor-map").hover();
  await page.keyboard.press("Home");
  await expect.poll(() => activeThumb(page)).toContain("№1");
  await page.keyboard.press("End");
  await expect.poll(() => activeThumb(page)).toContain("№3");
  await page.keyboard.press("ArrowUp");
  await expect.poll(() => activeThumb(page)).toContain("№2");
  await page.keyboard.press("ArrowDown");
  await expect.poll(() => activeThumb(page)).toContain("№3");
  await page.keyboard.press("Home");
  const n1 = await parts(page).count();
  await page.keyboard.press("Control+ArrowDown");                    // 1-karta pastga → endi №2
  await expect.poll(() => activeThumb(page)).toContain("№2");
  await expect(parts(page)).toHaveCount(n1);
  await page.keyboard.press("Control+ArrowUp");
  await expect.poll(() => activeThumb(page)).toContain("№1");

  // Shift+W+bosish (blok) — xatosiz; F9 — to'liq ekran almashadi
  const pb = (await parts(page).first().boundingBox())!;
  await page.keyboard.down("Shift"); await page.keyboard.down("w");
  await page.mouse.click(pb.x + pb.width / 2, pb.y + pb.height / 2);
  await page.keyboard.up("w"); await page.keyboard.up("Shift");
  await page.keyboard.press("F9");
  await page.keyboard.press("F9");
  await expect(ed).toBeVisible();
  expect(errors).toEqual([]);
});
