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
