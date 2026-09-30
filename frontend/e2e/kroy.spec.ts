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

  // kromka: 6-detal (480×800) ОВ va ОН
  for (const col of ["edge_top", "edge_bottom"]) {
    await rowCell(page, 5, col).click();
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("list-editor")).toBeVisible();
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("Enter");
    await expect(rowCell(page, 5, col)).toContainText("Кромка 1");
  }

  // Раскрой
  await page.getByTestId("cs-tab-cut").click();
  await page.getByTestId("btn-cut-big").click();
  const dlg = page.getByTestId("remnant-commit");
  await expect(dlg).toBeVisible();
  await page.getByTestId("remnant-commit-ok").click();
  await expect(page.getByTestId("cut-status")).toContainText("№: 1/2");
  await expect(page.getByTestId("cut-status")).toContainText("Cp:");
  const fill = await page.getByTestId("cut-fill").textContent();
  const first = Number((fill ?? "").split("%")[0]);
  expect(first).toBeGreaterThanOrEqual(91);          // benchmark: 2 list, 1-list ≥ 91 %
  await expect(page.locator('[data-testid="cut-map"] .map-part')).not.toHaveCount(0);
  await page.getByTestId("toggle-commands").click();
  await expect(page.getByTestId("commands-table")).toContainText("T1");

  // Hisobot
  await page.getByTestId("side-print").click();
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
  await paste(page, "A\t600\t400\t2\nB\t800\t500\t1");
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
  const later = page.getByRole("button", { name: "Позже" });
  if (await later.isVisible().catch(() => false)) await later.click();
  await expect(page.getByTestId("cut-status")).toContainText("№: 1/1");

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
