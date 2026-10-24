// Xabarlar (2026-10-17): XNC dastur xatosi chizma maydoniga sig'adi va xato bergan qator belgilanadi; server 422 xatosi —
// odam o'qiydigan «maydon: sabab» ko'rinishida (JSON / inglizcha emas); xabarnoma ekrandan chiqmaydi.
import { expect, test, type Page } from "@playwright/test";

/** Palitradan buyruq qo'shish: onlayn tizimdagidek darhol «Свойства» oynasi ochiladi — «Ок» bilan yopiladi. */
async function pal(page: Page, cmd: string) {
  await page.getByTestId(`pal-${cmd}`).click();
  await page.getByTestId("xnc-props-ok").click();
}

async function newProject(page: Page, name: string) {
  await page.goto("/");
  await page.getByTestId("btn-new-project").click();
  await page.getByTestId("ask-input").fill(name);
  await page.getByTestId("ask-ok").click();
  await expect(page.getByTestId("project-name")).toHaveValue(name);
}

async function addType(page: Page, ty: string) {
  await page.getByTestId("add-op").click();
  await expect(page.getByTestId("op-type-dialog")).toBeVisible();
  await page.getByTestId("op-type-dialog").getByRole("button", { name: new RegExp(`\\(${ty}\\)`) }).click();
  await expect(page.getByTestId("op-type-dialog")).toHaveCount(0);
}

const inside = (a: { x: number; y: number; width: number; height: number }, b: { x: number; y: number; width: number; height: number }) =>
  a.x >= b.x - 0.5 && a.y >= b.y - 0.5 && a.x + a.width <= b.x + b.width + 0.5 && a.y + a.height <= b.y + b.height + 0.5;

test("XNC: uzun dastur xatosi chizma ichida (qatorlarga bo'linadi), xato bergan buyruq qatori belgilanadi", async ({ page }) => {
  await newProject(page, "MSG xnc err");
  await addType(page, "XNC");
  const params = page.getByTestId("xnc-params");
  // uzun-ingichka detal: eng noqulay holat (yuza tor — yozuv butun chizma kengligida, bir necha qator)
  for (const [lab, v] of [["Длина (DX)", "2000"], ["Ширина (DY)", "120"]] as const) {
    const inp = params.locator("label.field", { hasText: lab }).locator("input");
    await inp.fill(v);
    await inp.press("Enter");
  }
  const nm = page.getByTestId("xnc-op-name");                       // nom bo'sh bo'lsa birinchi xabar — «nom ko'rsatilmagan»
  await nm.fill("Fillet test");
  await nm.press("Enter");
  await page.getByTestId("xnc-tab-program").click();
  await pal(page, "DrillFront");
  await pal(page, "MillFillet");               // kontursiz yumaloqlash — dastur xatosi (2-qator)
  const draw = page.getByTestId("xnc-drawing");
  const err = draw.locator("g.xnc-error");
  await expect(err).toHaveCount(1);
  await expect(err.locator("title")).toContainText("MillFillet");
  const svgBox = (await draw.locator("svg").boundingBox())!;
  for (const el of [err.locator("rect.xnc-error-bg"), err.locator("text.xnc-error-text")]) {
    const b = (await el.boundingBox())!;
    expect(inside(b, svgBox), `${JSON.stringify(b)} ⊄ ${JSON.stringify(svgBox)}`).toBe(true);
  }
  // matn foni ichida, shrift o'qiladigan (≥ 11 px ekranda)
  const bg = (await err.locator("rect.xnc-error-bg").boundingBox())!;
  for (const ts of await err.locator("tspan").all()) {
    const b = (await ts.boundingBox())!;
    expect(inside(b, bg), `tspan ${JSON.stringify(b)} ⊄ fon ${JSON.stringify(bg)}`).toBe(true);
  }
  const fpx = await err.locator("text.xnc-error-text").evaluate((e) => {
    const svg = e.ownerSVGElement!;
    const k = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
    return parseFloat(e.getAttribute("font-size") ?? "0") * k;
  });
  expect(fpx).toBeGreaterThanOrEqual(10.5);
  // xato bergan qator (MillFillet — 2-buyruq, yo'li «1») qizil belgilangan, ✖ belgisi ustida — xabar matni
  await expect(page.getByTestId("prog-item-1")).toHaveClass(/prog-err/);
  await expect(page.getByTestId("prog-item-0")).not.toHaveClass(/prog-err/);
  await expect(page.getByTestId("prog-err-1")).toHaveAttribute("title", /MillFillet/);
  // chizmadagi xato yozuvini bosish — shu buyruq tanlanadi
  await page.getByTestId("prog-item-0").click();
  await err.locator("rect.xnc-error-bg").dispatchEvent("click");
  await expect(page.getByTestId("prog-item-1")).toHaveClass(/prog-sel/);
});

test("Server 422: xabarnoma «maydon: sabab» (tilga mos), JSON / inglizcha emas, ekrandan chiqmaydi", async ({ page }) => {
  await newProject(page, "MSG 422");
  // loyiha nomini saqlash so'rovini buzib yuboramiz (nom o'rniga son) — haqiqiy server 422 qaytaradi
  await page.route(/\/api\/projects\/[^/]+$/, async (route) => {
    if (route.request().method() !== "PATCH") return route.continue();
    await route.continue({ postData: JSON.stringify({ name: 12345 }) });
  });
  const nm = page.getByTestId("project-name");
  await nm.fill("MSG 422 yangi");
  await nm.press("Enter");
  const toast = page.getByTestId("toast-error");
  await expect(toast).toBeVisible();
  await expect(toast).toContainText("Наименование: должно быть строкой");
  const txt = (await toast.innerText()) ?? "";
  expect(txt).not.toContain("{");
  expect(txt).not.toMatch(/Input should|Unprocessable|string_type|loc/);
  const b = (await toast.boundingBox())!;
  const vp = page.viewportSize()!;
  expect(b.x >= 0 && b.x + b.width <= vp.width && b.y + b.height <= vp.height).toBe(true);
  await page.unroute(/\/api\/projects\/[^/]+$/);
});
