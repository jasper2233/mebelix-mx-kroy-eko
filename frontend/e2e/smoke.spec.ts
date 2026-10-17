// «Tutun» testi (v2.3): barcha operatsiya turlari va yangi sozlama/dialog ekranlari ochiladi va sahifa xatosiz qoladi.
import { expect, test, type Page } from "@playwright/test";

async function newProject(page: Page, name: string) {
  await page.goto("/");
  await page.getByTestId("btn-new-project").click();
  await page.getByTestId("ask-input").fill(name);
  await page.getByTestId("ask-ok").click();
  await expect(page.getByTestId("project-name")).toHaveValue(name);
}

function watch(page: Page) {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  page.on("response", (r) => { if (r.status() >= 500) errors.push(`HTTP ${r.status()} ${r.url()}`); });
  return errors;
}

async function addType(page: Page, ty: string) {
  await page.getByTestId("add-op").click();
  await expect(page.getByTestId("op-type-dialog")).toBeVisible();
  await page.getByTestId("op-type-dialog").getByRole("button", { name: new RegExp(`\\(${ty}\\)`) }).click();
  await expect(page.getByTestId("op-type-dialog")).toHaveCount(0);
}

test("v2.3: barcha operatsiya turlari ochiladi (CS, CN, CL, EL, SP, GR, XNC, LB, O) — xatosiz", async ({ page }) => {
  const errors = watch(page);
  await newProject(page, "SMOKE ops");
  const before = await page.locator('[data-testid="ops-grid"] .ag-row').count();
  for (const ty of ["CS", "CN", "CL", "EL", "SP", "GR", "XNC", "LB", "O"]) {
    await addType(page, ty);
    await page.waitForTimeout(400);
    // panel ko'rinadi (yorliqlar yoki forma) va xato chegarasi (ErrorBoundary) ishlamagan
    await expect(page.locator(".panel").first()).toBeVisible();
    await expect(page.getByText(/Something went wrong|Произошла ошибка/)).toHaveCount(0);
  }
  await page.getByTestId("tab-ops").click();
  await expect(page.locator('[data-testid="ops-grid"] .ag-row')).toHaveCount(before + 9);
  expect(errors).toEqual([]);
});

test("v2.4: OEE (Производство), XNC sozlamalari va MES → OEE xatosiz ochiladi", async ({ page }) => {
  const errors = watch(page);
  await page.goto("/");
  await page.getByTestId("side-settings").click();
  for (const p of ["xnc", "production"]) {
    await page.getByTestId(`settings-${p}`).click();
    await page.waitForTimeout(500);
    await expect(page.locator(".page").first()).toBeVisible();
  }
  // MES yoqiladi → «OEE» punkti
  await page.getByTestId("settings-mes").click();
  const flag = page.getByTestId("mes-enable");
  if (!(await flag.isChecked())) await flag.click();
  await expect(page.getByTestId("side-mes")).toBeEnabled();
  await page.getByTestId("side-mes").click();
  const oee = page.getByTestId("mes-oee");
  await expect(oee).toBeVisible();
  await oee.click();
  await page.waitForTimeout(600);
  await expect(page.locator(".page").first()).toBeVisible();
  // tozalash: MES qayta o'chiriladi
  await page.getByTestId("side-settings").click();
  await page.getByTestId("settings-mes").click();
  if (await page.getByTestId("mes-enable").isChecked()) await page.getByTestId("mes-enable").click();
  expect(errors).toEqual([]);
});

test("v2.4: etiketka vizual redaktori va ZPL oynasi ochiladi (LB operatsiyasi)", async ({ page }) => {
  const errors = watch(page);
  await newProject(page, "SMOKE labels");
  await addType(page, "LB");
  await page.waitForTimeout(500);
  const tab = page.getByTestId("lb-tab-designer");
  if (await tab.count()) {
    await tab.click();
    await page.waitForTimeout(700);
    await expect(page.getByTestId("lbd-paper")).toBeVisible();
  }
  const zpl = page.getByTestId("lb-zpl");
  if (await zpl.count()) {
    await zpl.click();
    await page.waitForTimeout(500);
    await page.keyboard.press("Escape");
  }
  expect(errors).toEqual([]);
});

test("v2.3: sozlamalar sahifalari va MES/postprotsessor/XNC bo'limlari xatosiz ochiladi", async ({ page }) => {
  const errors = watch(page);
  await page.goto("/");
  await page.getByTestId("side-settings").click();
  for (const p of ["general", "pp", "remnants", "catalog", "mes", "backup"]) {
    await page.getByTestId(`settings-${p}`).click();
    await page.waitForTimeout(300);
    await expect(page.locator(".page").first()).toBeVisible();
  }
  // postprotsessor: stanok sozlamalari (ParamGrid) ochiladi
  await page.getByTestId("settings-pp").click();
  await page.getByTestId("pp-machine-scm_wincut").click();
  await expect(page.getByTestId("pp-machine-pane")).toContainText("SCM WinCut");
  // XNC sozlamalari (agar menyuda bo'lsa)
  const xs = page.getByTestId("settings-xnc");
  if (await xs.count()) {
    await xs.click();
    await expect(page.locator(".page").first()).toBeVisible();
  }
  expect(errors).toEqual([]);
});

test("v2.3: «Заказать», eksport va «Справка → Выражения» dialoglari ochiladi", async ({ page }) => {
  const errors = watch(page);
  await newProject(page, "SMOKE dialogs");
  // «Заказать» oynasi
  const order = page.getByRole("button", { name: "Заказать" }).first();
  if (await order.count()) {
    await order.click();
    await page.waitForTimeout(400);
    await page.keyboard.press("Escape");
  }
  // eksport tanlov oynasi
  const exp = page.getByRole("button", { name: "Экспортировать" }).first();
  if (await exp.count()) {
    await exp.click();
    await page.waitForTimeout(400);
    await page.keyboard.press("Escape");
  }
  // yordam
  await page.keyboard.press("F1");
  await page.waitForTimeout(400);
  await expect(page.locator(".page, .help").first()).toBeVisible();
  expect(errors).toEqual([]);
});

test("XNC: tanlangan buyruq geometriyasi chizmada qizil, chizmadan bosish — buyruqni tanlaydi (SVG qayta so'ralmaydi)", async ({ page }) => {
  const errors = watch(page);
  await newProject(page, "SMOKE xnc hl");
  await addType(page, "XNC");
  const params = page.getByTestId("xnc-params");
  for (const [lab, v] of [["Длина (DX)", "600"], ["Ширина (DY)", "400"]] as const) {
    const inp = params.locator("label.field", { hasText: lab }).locator("input");
    await inp.fill(v);
    await inp.press("Enter");
  }
  await page.getByTestId("xnc-tab-program").click();
  // dastur: teshik (0), DoWhile (1) ichida teshik (1.0)
  await page.getByTestId("pal-DrillFront").click();
  await page.getByTestId("pal-DoWhile").click();
  await page.getByTestId("pal-DrillFront").click();
  await expect(page.getByTestId("prog-item-1.0")).toBeVisible();
  const draw = page.getByTestId("xnc-drawing");
  const top = draw.locator('[data-cmd="0"]');
  const inner = draw.locator('[data-cmd="1.0"]');
  await expect(top).toHaveCount(1);
  await expect(inner).toHaveCount(1);
  let svgReq = 0;
  page.on("request", (r) => { if (r.url().includes("xnc.svg")) svgReq += 1; });
  await page.getByTestId("prog-item-0").click();
  await expect(top).toHaveClass(/xnc-hl/);
  await expect(inner).not.toHaveClass(/xnc-hl/);
  // sof qizil chiziq, ichki to'ldirish o'zgarmaydi
  expect(await top.locator("circle").evaluate((e) => getComputedStyle(e).stroke)).toBe("rgb(255, 0, 0)");
  expect(await top.locator("circle").evaluate((e) => getComputedStyle(e).fill)).toBe("none");
  await page.getByTestId("prog-item-1").click();                               // blok (DoWhile) — ichidagi geometriya
  await expect(inner).toHaveClass(/xnc-hl/);
  await expect(top).not.toHaveClass(/xnc-hl/);
  await page.getByTestId("prog-item-0").click({ modifiers: ["Control"] });     // ko'p tanlov
  await expect(top).toHaveClass(/xnc-hl/);
  await expect(inner).toHaveClass(/xnc-hl/);
  await inner.locator("circle").dispatchEvent("click");                       // chizmadan → daraxtdagi qator
  await expect(page.getByTestId("prog-item-1.0")).toHaveClass(/prog-sel/);
  await expect(top).not.toHaveClass(/xnc-hl/);
  expect(svgReq).toBe(0);
  expect(errors).toEqual([]);
});

test("XNC: Shift oralig'i oxirgi bosilgan qatordan, Ctrl tanlovlari saqlanadi; ko'p tanlov qatorlari bir xil rangda", async ({ page }) => {
  const errors = watch(page);
  await newProject(page, "SMOKE xnc shift");
  await addType(page, "XNC");
  const params = page.getByTestId("xnc-params");
  for (const [lab, v] of [["Длина (DX)", "600"], ["Ширина (DY)", "400"]] as const) {
    const inp = params.locator("label.field", { hasText: lab }).locator("input");
    await inp.fill(v);
    await inp.press("Enter");
  }
  await page.getByTestId("xnc-tab-program").click();
  for (let i = 0; i < 5; i++) await page.getByTestId("pal-DrillFront").click();
  await expect(page.getByTestId("prog-item-4")).toBeVisible();
  const item = (i: number) => page.getByTestId(`prog-item-${i}`);
  await item(0).click();
  await item(2).click({ modifiers: ["Control"] });
  await item(4).click({ modifiers: ["Shift"] });                 // 2…4 + 0 (1 — tanlanmaydi)
  for (const i of [0, 2, 3, 4]) await expect(item(i)).toHaveClass(/prog-sel/);
  await expect(item(1)).not.toHaveClass(/prog-sel/);
  const bg = async (i: number) => item(i).evaluate((e) => getComputedStyle(e).backgroundColor);
  expect(await bg(3)).toBe(await bg(0));
  await expect(page.getByTestId("xnc-drawing").locator(".xnc-hl")).toHaveCount(4);
  expect(errors).toEqual([]);
});

test("Jadvallar: ochilganda birinchi qator tanlangan; o'ng tugma menyusi yorliqlar bilan (tanlov o'zgarmaydi)", async ({ page, request }) => {
  const errors = watch(page);
  for (const n of ["Alfa CTXM", "Beta CTXM"]) await request.post("/api/projects", { data: { name: n } });
  await page.goto("/");
  await page.getByTestId("projects-search").fill("CTXM");
  const prow = (i: number) => page.locator(`[data-testid="projects-grid"] .ag-row[row-index="${i}"]`);
  await expect(page.locator('[data-testid="projects-grid"] .ag-row')).toHaveCount(2);
  await expect(prow(0)).toHaveClass(/ag-row-selected/);                       // boshlang'ich tanlov
  await prow(1).click({ button: "right" });
  const pm = page.getByTestId("projects-grid-menu");
  await expect(pm).toBeVisible();
  await expect(pm).toContainText("F2");
  await expect(pm).toContainText("Ctrl+A");
  await expect(prow(0)).toHaveClass(/ag-row-selected/);                       // o'ng tugma tanlovni o'zgartirmadi
  await expect(prow(1)).not.toHaveClass(/ag-row-selected/);
  await page.keyboard.press("Escape");
  await expect(pm).toHaveCount(0);

  await newProject(page, "SMOKE ctx");
  await page.getByTestId("add-cs").click();
  const orow = (i: number) => page.locator(`[data-testid="ops-grid"] .ag-row[row-index="${i}"]`);
  await expect(orow(0)).toHaveClass(/ag-row-selected/);
  await orow(0).click({ button: "right" });
  const om = page.getByTestId("ops-grid-menu");
  await expect(om).toContainText("Ctrl+K");
  await expect(om).toContainText("Del");
  await page.getByTestId("ctx-op-clone").click();
  await expect(om).toHaveCount(0);
  await expect(page.locator('[data-testid="ops-grid"] .ag-row')).toHaveCount(2);
  // detallar jadvali: menyu ochiladi, tashqarida bosish yopadi
  await page.getByTestId("parts-grid").click({ button: "right", position: { x: 200, y: 60 } });
  const dm = page.getByTestId("parts-grid-menu");
  await expect(dm).toContainText("Ctrl+V");
  await page.getByTestId("project-name").click();
  await expect(dm).toHaveCount(0);
  expect(errors).toEqual([]);
});
