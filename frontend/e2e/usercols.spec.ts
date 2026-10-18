// Jadval «Настройки» → foydalanuvchi ustunlari (O «Материалы»): «Настроенный Параметры» (butun son) qiymati qayta yuklashdan keyin
// saqlanadi, «Выражение» (Кол*2) to'g'ri hisoblanadi; o'ng tugma menyusi «Настройки» oynasini ochadi va tanlovni o'zgartirmaydi.
import { expect, test, type Page } from "@playwright/test";

async function newProject(page: Page, name: string) {
  await page.goto("/");
  await page.getByTestId("btn-new-project").click();
  await page.getByTestId("ask-input").fill(name);
  await page.getByTestId("ask-ok").click();
  await expect(page.getByTestId("project-name")).toHaveValue(name);
}

const saved = (page: Page) => page.waitForResponse((r) => r.url().includes("/o/materials") && r.request().method() === "PUT"
  && r.status() === 200);

test("O «Материалы»: foydalanuvchi ustunlari — parametr saqlanadi, ifoda hisoblanadi, o'ng tugma menyusi", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  page.on("response", (r) => { if (r.status() >= 500) errors.push(`HTTP ${r.status()} ${r.url()}`); });
  await newProject(page, "E2E usercols");
  await page.getByTestId("add-op").click();
  await page.getByTestId("op-type-dialog").getByRole("button", { name: /\(O\)/ }).click();
  await expect(page.getByTestId("op-type-dialog")).toHaveCount(0);
  const grid = page.getByTestId("o-grid");
  const cell = (row: number, col: string) => grid.locator(`.ag-row[row-index="${row}"] .ag-cell[col-id="${col}"]`);

  // ikki material qatori: Кол = 3 va 5
  for (const [i, name, qty] of [[0, "Ruchka", "3"], [1, "Petlya", "5"]] as const) {
    let w = saved(page);
    await page.getByTestId("o-add").click();
    await w;
    w = saved(page);
    await expect(cell(i, "name").locator("input")).toBeVisible();        // qo'shilgan qatorda «Наименование» tahrirda
    await page.keyboard.type(name);
    await page.keyboard.press("Enter");
    await expect(cell(i, "name")).toHaveText(name);
    await cell(i, "qty").dblclick();
    await page.keyboard.press("Control+a");
    await page.keyboard.type(qty);
    await page.keyboard.press("Enter");
    await w;
    await expect(cell(i, "qty")).toHaveText(qty);
  }

  // o'ng tugma: menyu «Настройки» (Ctrl+P) — tanlov o'zgarmaydi
  await cell(0, "name").click();
  await expect(grid.locator('.ag-row[row-index="0"]')).toHaveClass(/ag-row-selected/);
  await cell(1, "name").click({ button: "right" });
  const menu = page.getByTestId("o-grid-menu");
  await expect(menu).toBeVisible();
  await expect(menu).toContainText("Настройки");
  await expect(menu).toContainText("[CTRL]+[P]");
  await expect(menu).toContainText("Справка");
  await expect(grid.locator('.ag-row[row-index="0"]')).toHaveClass(/ag-row-selected/);
  await expect(grid.locator('.ag-row[row-index="1"]')).not.toHaveClass(/ag-row-selected/);
  await page.getByTestId("ctx-o-settings").click();
  const dlg = page.getByTestId("o_columns-settings");
  await expect(dlg).toBeVisible();

  // «Добавить»: «Настроенный Параметры», butun son
  await page.getByTestId("cols-add").click();
  const ucol = page.getByTestId("ucol-dialog");
  await expect(ucol).toBeVisible();
  await expect(page.getByTestId("ucol-name")).toHaveValue("material.name1");
  await expect(page.getByTestId("ucol-expr")).toBeDisabled();
  await page.getByTestId("ucol-vtype").selectOption("int");
  await page.getByTestId("ucol-title").fill("Rang");
  await page.getByTestId("ucol-desc").fill("Rang kodi");
  await page.getByTestId("ucol-ok").click();
  await expect(ucol).toHaveCount(0);
  await expect(page.getByTestId("cols-row-material.name1")).toBeVisible();

  // «Добавить»: «Выражение» = Кол*2 («Vs» ro'yxatidan)
  await page.getByTestId("cols-add").click();
  await expect(page.getByTestId("ucol-name")).toHaveValue("material.name2");
  await page.getByTestId("ucol-kind").selectOption("expr");
  await expect(page.getByTestId("ucol-note")).toContainText("integer()");
  await page.getByTestId("ucol-vtype").selectOption("double");
  await page.getByTestId("ucol-vs").click();
  await page.getByTestId("ucol-vars").locator("code", { hasText: /^Кол$/ }).click();
  await page.getByTestId("ucol-expr").press("End");
  await page.keyboard.type("*2");
  await expect(page.getByTestId("ucol-expr")).toHaveValue("Кол*2");
  await page.getByTestId("ucol-title").fill("Ikki baravar");
  await page.getByTestId("ucol-ok").click();

  // o'rnatilgan ustunni o'chirib bo'lmaydi; foydalanuvchinikini — mumkin (bu yerda o'chirilmaydi)
  await page.getByTestId("cols-row-code").click();
  await expect(page.getByTestId("cols-del")).toBeDisabled();
  await page.getByTestId("cols-row-material.name2").click();
  await expect(page.getByTestId("cols-del")).toBeEnabled();

  await page.getByTestId("cols-ok").click();
  await page.getByTestId("ask-input").fill("E2E foydalanuvchi ustunlari");
  await page.getByTestId("ask-ok").click();
  await expect(dlg).toHaveCount(0);

  const hdr = (id: string) => grid.locator(`.ag-header-cell[col-id="${id}"]`);
  await expect(hdr("material.name1")).toContainText("Rang");
  await expect(hdr("material.name2")).toContainText("Ikki baravar");
  await expect(cell(0, "material.name2")).toHaveText("6");
  await expect(cell(1, "material.name2")).toHaveText("10");

  // parametr qiymati (butun son): 42.7 → 43
  const w = saved(page);
  await cell(0, "material.name1").dblclick();
  await page.keyboard.type("42.7");
  await page.keyboard.press("Enter");
  await w;
  await expect(cell(0, "material.name1")).toHaveText("43");

  // qayta yuklash: profil va qiymat saqlangan, ifoda qayta hisoblanadi
  await page.reload();
  await page.getByTestId("ops-grid").locator('.ag-cell[col-id="type"]', { hasText: /^\s*O\s*$/ }).first().click();
  await expect(grid).toBeVisible();
  await expect(cell(0, "material.name1")).toHaveText("43");
  await expect(cell(1, "material.name1")).toHaveText("");
  await expect(cell(0, "material.name2")).toHaveText("6");
  await expect(cell(1, "material.name2")).toHaveText("10");
  expect(errors).toEqual([]);
});

test("CS «Детали»: логический параметр part.* va «Выражение»; EL «Детали» — o'ng tugma menyusi «Настройки»", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  page.on("response", (r) => { if (r.status() >= 500) errors.push(`HTTP ${r.status()} ${r.url()}`); });
  await newProject(page, "E2E usercols CS");
  await page.getByTestId("add-el").click();
  await expect(page.locator('[data-testid="ops-grid"] .ag-row')).toHaveCount(1);
  await page.getByTestId("add-cs").click();
  await expect(page.locator('[data-testid="ops-grid"] .ag-row')).toHaveCount(2);
  const grid = page.getByTestId("parts-grid");
  const cell = (row: number, col: string) => grid.locator(`.ag-row[row-index="${row}"] [col-id="${col}"]`).first();
  await grid.locator('.ag-grid-pinned-bottom-rows [col-id="name"]').click();
  await page.keyboard.type("Yon");
  await page.keyboard.press("Enter");
  await page.keyboard.type("700");
  await page.keyboard.press("Enter");
  await page.keyboard.type("500");
  await page.keyboard.press("Enter");
  await expect(cell(0, "width")).toHaveText("500");

  // o'ng tugma → «Настройки» → «Добавить» (Логический) va «Выражение» Длина*Ширина/1000
  await cell(0, "name").click({ button: "right" });
  await page.getByTestId("ctx-part-settings").click();
  await expect(page.getByTestId("column-settings")).toBeVisible();
  await page.getByTestId("cols-add").click();
  await expect(page.getByTestId("ucol-name")).toHaveValue("part.name1");
  await page.getByTestId("ucol-vtype").selectOption("bool");
  await page.getByTestId("ucol-ok").click();
  await page.getByTestId("cols-add").click();
  await page.getByTestId("ucol-kind").selectOption("expr");
  await page.getByTestId("ucol-vtype").selectOption("double");
  await page.getByTestId("ucol-expr").fill("Длина*Ширина/1000 + integer(boolean(part.name1))");
  await page.getByTestId("ucol-ok").click();
  await page.getByTestId("cols-ok").click();
  await page.getByTestId("ask-input").fill("E2E CS ustunlar");
  await page.getByTestId("ask-ok").click();
  await expect(page.getByTestId("column-settings")).toHaveCount(0);
  await expect(cell(0, "part.name2")).toHaveText("350");

  const upd = page.waitForResponse((r) => r.url().includes("/parts/batch-update") && r.status() === 200);
  await cell(0, "part.name1").locator("input").click();
  await upd;
  await expect(cell(0, "part.name1").locator("input")).toBeChecked();
  await expect(cell(0, "part.name2")).toHaveText("351");
  const pid = await page.evaluate(() => JSON.parse(localStorage.getItem("mxk_project") ?? "null"));
  const proj = await (await page.request.get(`/api/projects/${pid}`)).json();
  const cs = proj.operations.find((o: { type: string }) => o.type === "CS");
  expect(cs.parts[0].user_params).toEqual({ "part.name1": "true" });

  // EL «Детали»: o'ng tugma menyusi
  await page.getByTestId("ops-grid").locator('.ag-cell[col-id="type"]', { hasText: /^\s*EL\s*$/ }).first().click();
  await page.getByTestId("el-tab-parts").click();
  await page.getByTestId("el-parts").locator(".ag-header-cell").first().click({ button: "right" });
  const menu = page.getByTestId("el-parts-menu");
  await expect(menu).toContainText("Настройки");
  await expect(menu).toContainText("Справка");
  await page.getByTestId("el-parts-ctx-settings").click();
  await expect(page.getByTestId("el_columns-settings")).toBeVisible();
  expect(errors).toEqual([]);
});
