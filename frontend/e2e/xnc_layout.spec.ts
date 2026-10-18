// XNC «Параметры» joylashuvi (2026-10-18): yorliqlar qatoridagi tugmalar tartibi xodimlar o'rgangan tizimdagidek,
// «Зеркало» — avval gorizontal, «XNC Редактор» shu yerdan oyna bo'lib ochiladi, dastur faylini saqlash / ochish.
import { expect, test, type Page } from "@playwright/test";

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

test("XNC Параметры: tugmalar tartibi, ko'zgu tartibi, XNC Редактор oynasi, dastur faylini saqlash / ochish", async ({ page }) => {
  await newProject(page, "XNC layout");
  await addType(page, "XNC");
  await expect(page.getByTestId("xnc-params")).toBeVisible();
  const bar = page.locator(".tabs-right").filter({ has: page.getByTestId("xnc-pick-part") });
  const ids = await bar.locator("[data-testid]").evaluateAll((els) => els.map((e) => e.getAttribute("data-testid")));
  const order = ["xnc-pick-part", "xnc-editor-settings", "xnc-unlink", "xnc-part-props", "xnc-save-defaults", "xnc-file-open",
    "xnc-file-save", "xnc-pp", "xnc-dxf", "xnc-templates"];
  const pos = order.map((k) => ids.indexOf(k));
  expect(pos.every((p) => p >= 0)).toBeTruthy();
  expect([...pos].sort((a, b) => a - b)).toEqual(pos);          // «Шаблоны» (o'z qo'shimchamiz) — oxirida
  // ko'zgu: avval gorizontal (mirror_x), keyin vertikal
  const mir = await page.locator(".xnc-mirror [data-testid]").evaluateAll((els) => els.map((e) => e.getAttribute("data-testid")));
  expect(mir).toEqual(["xnc-mirror-x", "xnc-mirror-y"]);
  // «XNC Редактор» — oyna, Ок / Отмена
  await page.getByTestId("xnc-editor-settings").click();
  await expect(page.getByTestId("xnc-settings")).toBeVisible();
  await expect(page.getByTestId("xs-ok")).toBeVisible();
  await page.getByTestId("xs-cancel").click();
  await expect(page.getByTestId("xnc-settings")).toHaveCount(0);
  // «Сохранить» — .xnc fayli yuklanadi; «Открыть» — shu faylni qayta yuklaydi
  const [dl] = await Promise.all([page.waitForEvent("download"), page.getByTestId("xnc-file-save").click()]);
  expect(dl.suggestedFilename()).toMatch(/\.xnc$/);
  const path = await dl.path();
  await page.getByTestId("xnc-file-input").setInputFiles(path!);
  await expect(page.locator(".toast").last()).toContainText(/загружена|yuklandi/);
});
