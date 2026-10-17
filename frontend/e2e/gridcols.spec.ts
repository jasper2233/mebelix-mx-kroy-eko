// Jadvallar «Настройки» (Ctrl+P): O «Материалы» — ustunni yashirish profil orqali jadvalga qo'llanadi.
import { expect, test, type Page } from "@playwright/test";

async function newProject(page: Page, name: string) {
  await page.goto("/");
  await page.getByTestId("btn-new-project").click();
  await page.getByTestId("ask-input").fill(name);
  await page.getByTestId("ask-ok").click();
  await expect(page.getByTestId("project-name")).toHaveValue(name);
}

test("O «Материалы»: «Настройки» — «ИК» o'chirilsa ustun yo'qoladi, sarlavha maslahati = tavsif", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  page.on("response", (r) => { if (r.status() >= 500) errors.push(`HTTP ${r.status()} ${r.url()}`); });
  await newProject(page, "E2E gridcols");
  await page.getByTestId("add-op").click();
  await page.getByTestId("op-type-dialog").getByRole("button", { name: /\(O\)/ }).click();
  await expect(page.getByTestId("op-type-dialog")).toHaveCount(0);
  const grid = page.getByTestId("o-grid");
  const hdr = (id: string) => grid.locator(`.ag-header-cell[col-id="${id}"]`);
  await expect(hdr("used")).toHaveCount(1);
  await expect(hdr("code")).toHaveCount(1);
  await hdr("unit").hover();                                                // sarlavha maslahati — «Описание»
  await expect(page.locator(".ag-tooltip")).toContainText("Единица измерения");

  // standart ro'yxat: 8 ta ustun, kenglik belgilarda
  await page.getByTestId("o-columns").click();
  const dlg = page.getByTestId("o_columns-settings");
  await expect(dlg).toBeVisible();
  await expect(dlg.locator("tbody tr")).toHaveCount(8);
  await expect(page.getByTestId("cols-row-used")).toContainText("Изделие - Количество");
  await expect(page.getByTestId("cols-row-code").locator("input.num")).toHaveValue("20");
  await expect(page.getByTestId("cols-row-name").locator("input.num")).toHaveValue("35");

  // «ИК» o'chiriladi → OK → yangi profil nomi so'raladi
  await page.getByTestId("cols-on-used").uncheck();
  await page.getByTestId("cols-ok").click();
  await page.getByTestId("ask-input").fill("E2E profil");
  await page.getByTestId("ask-ok").click();
  await expect(dlg).toHaveCount(0);
  await expect(hdr("used")).toHaveCount(0);
  await expect(hdr("total")).toHaveCount(1);

  // Ctrl+P (jadval maydonida) — oyna qayta ochiladi, profil tanlangan, «ИК» o'chiq
  await grid.locator(".ag-header-cell").first().click();
  await page.keyboard.press("Control+p");
  await expect(dlg).toBeVisible();
  await expect(page.getByTestId("cols-on-used")).not.toBeChecked();
  await page.getByTestId("cols-on-used").check();
  await page.getByTestId("cols-ok").click();
  await expect(dlg).toHaveCount(0);
  await expect(hdr("used")).toHaveCount(1);
  expect(errors).toEqual([]);
});
