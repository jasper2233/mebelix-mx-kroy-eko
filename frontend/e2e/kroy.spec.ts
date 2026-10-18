// Asosiy oqim (PROMPT: «loyiha yaratish → CS qo'shish → 14 detal → kromka → Раскроить → hisobot»).
import { expect, test, type Page } from "@playwright/test";

const KRAVAT: [number, number, number][] = [
  [748, 1468, 1], [200, 1468, 2], [154, 748, 1], [154, 1052, 1], [50, 1052, 2], [480, 800, 1], [154, 400, 2],
  [100, 1452, 1], [470, 800, 1], [900, 800, 1], [500, 1452, 1], [116, 552, 1], [100, 350, 2], [100, 503, 2],
];

async function paste(page: Page, text: string) {
  await page.evaluate((t) => {
    const dt = new DataTransfer();
    dt.setData("text/plain", t);
    document.activeElement?.dispatchEvent(new ClipboardEvent("paste", { clipboardData: dt, bubbles: true }));
  }, text);
}

const draftCell = (page: Page, col: string) =>
  page.locator(`[data-testid="parts-grid"] .ag-grid-pinned-bottom-rows [col-id="${col}"]`);
const rowCell = (page: Page, row: number, col: string) =>
  page.locator(`[data-testid="parts-grid"] .ag-row[row-index="${row}"] [col-id="${col}"]`).first();

async function newProject(page: Page, name: string) {
  await page.goto("/");
  await page.getByTestId("btn-new-project").click();
  await page.getByTestId("ask-input").fill(name);
  await page.getByTestId("ask-ok").click();
  await expect(page.getByTestId("project-name")).toHaveValue(name);
}

test("loyiha → CS → 14 detal → kromka → Раскроить → hisobot", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await newProject(page, "E2E Detskiy kravat");
  await page.getByTestId("add-el").click();
  await expect(page.locator('[data-testid="ops-grid"] .ag-row')).toHaveCount(1);
  await page.getByTestId("add-cs").click();
  await expect(page.locator('[data-testid="ops-grid"] .ag-row')).toHaveCount(2);

  // 1-detal klaviaturadan: nom → Enter → uzunlik → Enter → en → Enter (qator yaratiladi) → soni
  await draftCell(page, "name").click();
  await page.keyboard.type("Panel1");
  await page.keyboard.press("Enter");
  await page.keyboard.type("748");
  await page.keyboard.press("Enter");
  await page.keyboard.type("1468");
  await page.keyboard.press("Enter");
  await expect(rowCell(page, 0, "width")).toHaveText("1468");
  await expect(rowCell(page, 0, "length")).toHaveText("748");

  // qolgan 13 tasi Excel dan (Ctrl+V)
  await draftCell(page, "name").click();
  await paste(page, KRAVAT.slice(1).map(([l, w, q], i) => `Panel${i + 2}\t${l}\t${w}\t${q}`).join("\n"));
  await expect(page.getByTestId("parts-count")).toHaveText("19");
  await expect(page.getByTestId("parts-area")).toHaveText("4.777");
  // yangi detallar material teksturasi bo'yicha Ткт ✓ — bu buyurtmada aylantirishga ruxsat (xodimlar odati)
  await expect(rowCell(page, 0, "grain").locator("input")).toBeChecked();
  await expect(rowCell(page, 13, "grain").locator("input")).toBeChecked();
  // ☐TXT — tanlangan detallarga (onlayn tizimdagidek): avval hammasi belgilanadi (Ctrl+A)
  await rowCell(page, 0, "num").click();
  await page.keyboard.press("Control+a");
  await page.getByTestId("grain-off").click();
  await expect(rowCell(page, 0, "grain").locator("input")).not.toBeChecked();
  await expect(rowCell(page, 13, "grain").locator("input")).not.toBeChecked();

  // kromka: 6-detal (480×800) ОВ va ОН
  for (const col of ["edge_top", "edge_bottom"]) {
    await rowCell(page, 5, col).click();
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("list-editor")).toBeVisible();
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("Enter");
    await expect(rowCell(page, 5, col)).toContainText("Кромка 1");
  }
  // ro'yxat muharririda Del — faqat katak tozalanadi (detal o'chmaydi)
  await rowCell(page, 5, "edge_left").click();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("list-editor")).toBeVisible();
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await expect(rowCell(page, 5, "edge_left")).toContainText("Кромка 1");
  await rowCell(page, 5, "edge_left").click();                 // Enter fokusni keyingi katakka o'tkazgan
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("list-editor")).toBeVisible();
  await page.keyboard.press("Delete");
  await expect(rowCell(page, 5, "edge_left")).not.toContainText("Кромка 1");
  await expect(page.getByTestId("parts-count")).toHaveText("19");

  // Раскрой
  await page.getByTestId("cs-tab-cut").click();
  await page.getByTestId("btn-cut-big").click();
  // kroydan keyin oyna o'zi ochilmaydi (standart) — qoldiqlar asboblar panelidagi tugma bilan yoziladi
  await expect(page.getByTestId("cut-status")).toContainText("№: 1/2");
  await page.getByTestId("btn-remnants").click();
  const dlg = page.getByTestId("remnant-commit");
  await expect(dlg).toBeVisible();
  await page.getByTestId("remnant-commit-ok").click();
  await expect(dlg).toHaveCount(0);
  await expect(page.getByTestId("cut-status")).toContainText("№: 1/2");
  await expect(page.getByTestId("cut-status")).toContainText("Cp:");
  // «Раскрой» tabini bosish — uning yorliqlari darhol ishlaydi (↓ / Home)
  await page.keyboard.press("ArrowDown");
  await expect(page.getByTestId("cut-status")).toContainText("№: 2/2");
  await page.keyboard.press("Home");
  await expect(page.getByTestId("cut-status")).toContainText("№: 1/2");
  // Ctrl+P — ko'rinish sozlamalari
  await page.keyboard.press("Control+p");
  await expect(page.getByTestId("cut-view-settings")).toBeVisible();
  await page.getByTestId("cut-view-settings").getByRole("button", { name: "Ок" }).click();
  await expect(page.getByTestId("cut-view-settings")).toHaveCount(0);
  const fill = await page.getByTestId("cut-fill").textContent();
  const first = Number((fill ?? "").split("%")[0]);
  expect(first).toBeGreaterThanOrEqual(91);          // benchmark: 2 list, 1-list ≥ 91 %
  await expect(page.locator('[data-testid="cut-map"] .map-part')).not.toHaveCount(0);
  await page.getByTestId("toggle-commands").click();
  await expect(page.getByTestId("commands-table")).toContainText("T1");

  // Hisobot (sandbox iframe: skriptlar bajarilmaydi)
  await page.getByTestId("side-print").click();
  await expect(page.getByTestId("report-frame")).toHaveAttribute("sandbox", /allow-same-origin/);
  const frame = page.frameLocator('[data-testid="report-frame"]');
  await expect(frame.locator("body")).toContainText("Требование на склад");
  await expect(frame.locator("body")).toContainText("Кромка 1");
  await expect(frame.locator("svg").first()).toBeVisible();
  expect(errors).toEqual([]);
});

test("yorliqlar: Ctrl+K, Del, Ctrl+Z; tahrir; sex rejimi", async ({ page }) => {
  await newProject(page, "E2E yorliqlar");
  await page.getByTestId("add-cs").click();
  await draftCell(page, "name").click();
  await paste(page, "A\t600\t400\t2\n<img src=x onerror=\"window.top.document.title='XSS'\">\t800\t500\t1");
  await expect(page.getByTestId("parts-count")).toHaveText("3");
  await rowCell(page, 0, "code").click();
  await page.keyboard.press("Control+k");
  await expect(page.getByTestId("parts-count")).toHaveText("5");
  await rowCell(page, 1, "code").click();
  await page.keyboard.press("Delete");
  await expect(page.getByTestId("parts-count")).toHaveText("3");
  await page.keyboard.press("Control+z");
  await expect(page.getByTestId("parts-count")).toHaveText("5");

  await page.getByTestId("cs-tab-cut").click();
  await page.getByTestId("btn-cut-big").click();
  await expect(page.getByTestId("cut-status")).toContainText("№: 1/1");
  const later = page.getByRole("button", { name: "Позже" });
  if (await later.waitFor({ state: "visible", timeout: 5000 }).then(() => true, () => false)) await later.click();
  await expect(page.locator(".modal-back")).toHaveCount(0);

  // tahrir: o'ng tugma bilan detalni olib tashlash → ro'yxatda qoldiq 1
  await page.getByTestId("btn-edit-cut").click();
  const map = page.getByTestId("editor-map");
  await expect(map).toBeVisible();
  const box = (await map.boundingBox())!;
  await page.mouse.click(box.x + box.width * 0.1, box.y + box.height * 0.12, { button: "right" });
  await expect(page.locator('[data-testid="cut-editor"]')).toContainText("не вместилось: 1");
  await page.keyboard.press("Control+z");
  await expect(page.locator('[data-testid="cut-editor"]')).not.toContainText("не вместилось");
  await page.getByTestId("editor-ok").click();
  await expect(page.getByTestId("cut-editor")).toHaveCount(0);
  // qo'lda saqlagach деловой qoldiqni omborga yozish taklifi (kroydan keyingidek) — keyinga qoldiriladi
  const later2 = page.getByRole("button", { name: "Позже" });
  if (await later2.waitFor({ state: "visible", timeout: 3000 }).then(() => true, () => false)) await later2.click();
  await expect(page.locator(".modal-back")).toHaveCount(0);

  // hisobotda detal nomi matn sifatida (XSS yo'q)
  await page.getByTestId("side-print").click();
  const rf = page.frameLocator('[data-testid="report-frame"]');
  await expect(rf.locator("body")).toContainText("<img src=x");
  expect(await page.title()).not.toBe("XSS");
  await page.getByTestId("side-project").click();

  // Изделия: Ctrl+P — ustunlar sozlamasi (brauzer chop etish oynasi emas)
  await page.getByTestId("tab-products").click();
  await page.locator('[data-testid="products-grid"] .ag-row[row-index="0"] [col-id="code"]').click();
  await page.keyboard.press("Control+p");
  await expect(page.getByTestId("products-columns")).toBeVisible();
  await page.getByTestId("products-columns").getByRole("button", { name: "Ок" }).click();

  // sex rejimi: karta QR → «Раскроено +1»
  const pid = await page.evaluate(() => JSON.parse(localStorage.getItem("mxk_project") ?? "null"));
  const proj = await (await page.request.get(`/api/projects/${pid}`)).json();
  const cs = proj.operations.find((o: { type: string }) => o.type === "CS");
  await page.goto("/#/sex");
  await page.getByTestId("ws-input").fill(`MXK:${proj.number}:${cs.id}:1`);
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("ws-map")).toContainText("0 / 1");
  await page.getByTestId("ws-done").click();
  await expect(page.getByTestId("ws-map")).toContainText("1 / 1");
});

test("v2: Space / Shift+Space, buferdan yangi kromka, minimal otstup, qoldiqlar jadvali, ko'rsatkichlar", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await newProject(page, "E2E v2");
  await page.getByTestId("add-el").click();
  await page.getByTestId("add-cs").click();
  // QA #16: uzunligi yo'q (o'tkazib yuboriladigan) qatordagi noma'lum kromka uchun yangi EL yaratilmaydi
  await draftCell(page, "name").click();
  await paste(page, "Bad		280	2	1	QA yo'q kromka");
  await expect(page.locator(".toast", { hasText: "Пропущено строк: 1" })).toBeVisible();
  await expect(page.locator('[data-testid="ops-grid"] .ag-row')).toHaveCount(2);      // Кромка 1, CS — yangi EL yo'q
  await expect(page.locator(".toast", { hasText: "QA yo'q kromka" })).toHaveCount(0);
  // Excel dan: nomi, uzunlik, en, soni, Ткт, ОВ — «Ясень 1 мм» ro'yxatda yo'q → yangi kromka yaratiladi
  await draftCell(page, "name").click();
  await paste(page, "Yon\t720\t280\t2\t1\tЯсень 1 мм\nPolka\t564\t499\t4\t0\t");
  await expect(page.getByTestId("parts-count")).toHaveText("6");
  await expect(rowCell(page, 0, "edge_top")).toContainText("Ясень 1 мм");
  await expect(page.locator('[data-testid="ops-grid"] .ag-row')).toHaveCount(3);      // Кромка 1, Ясень, CS

  // Space: Ткт katagida belgi almashadi; kromka katagida navbatdagi kromka
  await expect(rowCell(page, 0, "grain").locator("input")).toBeChecked();         // buferdagi «1»
  await expect(rowCell(page, 1, "grain").locator("input")).not.toBeChecked();     // buferdagi «0»
  await rowCell(page, 1, "qty").click();                                            // fokus (belgini bosmasdan)
  await page.keyboard.press("ArrowRight");
  await page.keyboard.press(" ");
  await expect(rowCell(page, 1, "grain").locator("input")).toBeChecked();
  await page.keyboard.press(" ");
  await expect(rowCell(page, 1, "grain").locator("input")).not.toBeChecked();
  await rowCell(page, 1, "edge_left").click();
  await page.keyboard.press(" ");
  await expect(rowCell(page, 1, "edge_left")).toContainText("Кромка 1");
  // Shift+Space: to'rt tomonga bir xil (keyingi) kromka
  await page.keyboard.press("Shift+ ");
  for (const col of ["edge_top", "edge_bottom", "edge_left", "edge_right"]) {
    await expect(rowCell(page, 1, col)).toContainText("Ясень 1 мм");
  }

  // Параметры: Кратность avtomatik, «Минимальный отступ в конце» oynasi
  await page.getByTestId("cs-tab-params").click();
  await expect(page.getByTestId("cs-mult")).toHaveValue("2");                       // 40 / 16
  await page.getByTestId("cs-end-offsets").click();
  const od = page.getByTestId("offsets-dialog");
  await expect(od).toBeVisible();
  await od.getByRole("checkbox").first().check();
  await page.getByTestId("offsets-ok").click();
  // havola qatorining maslahatida joriy qiymatlar (onlayn tizimdagidek havola — qiymat matnsiz)
  await expect(page.locator(".field", { has: page.getByTestId("cs-end-offsets") })).toHaveAttribute("title", /снизу \d/);

  // Раскрой → Листы и остатки: natijadagi qoldiq qatorlari
  await page.getByTestId("cs-tab-cut").click();
  await page.getByTestId("btn-cut-big").click();
  await expect(page.getByTestId("cut-status")).toContainText("№: 1/1");
  const later = page.getByRole("button", { name: "Позже" });
  if (await later.waitFor({ state: "visible", timeout: 5000 }).then(() => true, () => false)) await later.click();
  await expect(page.locator(".modal-back")).toHaveCount(0);
  // Ctrl+P: «R» ko'rsatkichini yoqish
  await page.keyboard.press("Control+p");
  const ind = page.getByTestId("cut-indicators");
  await expect(ind).toBeVisible();
  await ind.locator("tr", { hasText: "Процент отхода" }).getByRole("checkbox").check();
  await page.getByTestId("cut-view-settings").getByRole("button", { name: "Ок" }).click();
  await expect(page.getByTestId("cut-status")).toContainText("R:");
  // F2 — karta izohi
  await page.keyboard.press("F2");
  await page.getByTestId("ask-input").fill("da");
  await page.getByTestId("ask-ok").click();
  await expect(page.locator(".cut-notes")).toContainText("da");

  await page.getByTestId("cs-tab-sheets").click();
  await expect(page.locator('[data-testid="sheets-grid"] .ag-row')).not.toHaveCount(1);   // list + qoldiq(lar)
  await expect(page.getByTestId("sheets-grid")).toContainText("Деловой остаток");
  expect(errors).toEqual([]);
});


test("v2.1: mahsulot «Свойства» oynasi va ko'p kalitli «Сортировка»", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await newProject(page, "E2E props");
  await page.getByTestId("tab-products").click();
  await page.locator('[data-testid="products-grid"] .ag-row').first().click();
  await page.keyboard.press("Control+Space");
  await expect(page.getByTestId("product-props")).toBeVisible();
  await page.getByTestId("pprops-phone1").fill("+998901112233");
  await page.getByTestId("pprops-add").click();
  await page.getByTestId("pprops-key-0").fill("product.color");
  await page.getByTestId("pprops-val-0").fill("oq");
  await page.getByTestId("pprops-desc").fill("Fasad oq");
  await page.getByTestId("pprops-ok").click();
  await expect(page.getByTestId("product-props")).toBeHidden();
  await page.keyboard.press("Control+Space");                       // qiymatlar saqlanganmi
  await expect(page.getByTestId("pprops-phone1")).toHaveValue("+998901112233");
  await expect(page.getByTestId("pprops-key-0")).toHaveValue("product.color");
  await expect(page.getByTestId("pprops-desc")).toHaveValue("Fasad oq");
  await page.keyboard.press("Escape");

  // ko'p kalitli saralash: ikkita mahsulot qo'shib, soni (kamayish) → nomi
  for (const n of ["B", "A"]) {
    await page.getByTestId("add-product").click();
    await page.getByTestId("ask-input").fill(n);
    await page.getByTestId("ask-ok").click();
  }
  await page.getByTitle("Сортировка").first().click();
  await expect(page.getByTestId("products-sort")).toBeVisible();
  await page.getByTestId("sort-row-name").locator('input[type="checkbox"]').first().check();
  await page.getByTestId("sort-ok").click();
  // kod (hammasi bo'sh) → nomi (kichik harf, Unicode tartibi): lotin harflar kirilldan oldin
  const pname = (i: number) => page.locator(`[data-testid="products-grid"] .ag-row[row-index="${i}"] [col-id="name"]`);
  await expect(pname(0)).toHaveText("A");
  await expect(pname(1)).toHaveText("B");
  await expect(pname(2)).toHaveText("Изделие 1");
  expect(errors).toEqual([]);
});

test("v2.2: «MES» qatori xira → yoqilgach panel; postprotsessor stanoklari ro'yxati", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  const mes = page.getByTestId("side-mes");
  await expect(mes).toBeVisible();
  // sozlama yoqilmaguncha (boshlang'ich holat) qator o'chirilgan
  await page.getByTestId("side-settings").click();
  await page.getByTestId("settings-mes").click();
  const flag = page.getByTestId("mes-enable");
  if (await flag.isChecked()) { await flag.click(); await expect(mes).toBeDisabled(); }
  await expect(mes).toBeDisabled();
  await flag.click();
  await expect(mes).toBeEnabled();
  await mes.click();
  await expect(page.getByTestId("mes-view-overview")).toBeVisible();
  await page.getByTestId("mes-orders").click();
  await expect(page.getByTestId("mes-view-orders")).toBeVisible();
  await expect(page.getByTestId("mes-view-orders").getByRole("button").first()).toBeDisabled();    // karkas: amallar o'chirilgan
  // o'chirsak panel yopilib, qator yana xira bo'ladi
  await page.getByTestId("side-settings").click();
  await page.getByTestId("settings-mes").click();
  await page.getByTestId("mes-enable").click();
  await expect(mes).toBeDisabled();

  // stanoklar: ro'yxat bor, yoqish → «Постпроцессор» ro'yxatida xira ulanmagan stanok
  await page.getByTestId("settings-pp").click();
  await expect(page.getByTestId("pp-group-saw")).toContainText("SCM WinCut");
  await expect(page.getByTestId("pp-group-saw")).toContainText("GlassGCODE");
  await page.getByTestId("pp-machine-holzma_ptx").click();
  await expect(page.getByTestId("pp-machine-pane")).toContainText("HOLZMA PTX");
  // «Постпроцессоры» — oyna: yoqish qoralama (yorliq xira emas), «Ок» saqlaydi; qayta ochib o'chiramiz
  await page.getByTestId("pp-machine-enable").click();
  await expect(page.getByTestId("pp-machine-holzma_ptx")).not.toHaveClass(/pp-off/);
  await page.getByTestId("pp-ok").click();
  await expect(page.getByTestId("pp-settings")).toHaveCount(0);
  await page.getByTestId("settings-pp").click();
  await expect(page.getByTestId("pp-machine-holzma_ptx")).not.toHaveClass(/pp-off/);
  await page.getByTestId("pp-machine-holzma_ptx").click();
  await page.getByTestId("pp-machine-enable").click();
  await expect(page.getByTestId("pp-machine-holzma_ptx")).toHaveClass(/pp-off/);
  await page.getByTestId("pp-ok").click();
  expect(errors).toEqual([]);
});
