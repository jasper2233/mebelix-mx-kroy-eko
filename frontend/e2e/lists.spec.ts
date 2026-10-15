// Loyihalar ro'yxati klaviaturasi va dialoglar (QA tuzatishlari): tanlov fokusga ergashadi, Ctrl+A, Del tasdig'i, Esc.
import { expect, test } from "@playwright/test";

test("v2.2: ro'yxat — tanlov fokusga ergashadi, Ctrl+A, Del tasdig'i, Esc matn maydonida", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  for (const n of ["Zeta LSTX", "Alfa LSTX", "Beta LSTX"]) await request.post("/api/projects", { data: { name: n } });
  await page.goto("/");
  await page.getByTestId("projects-search").fill("LSTX");
  const row = (i: number) => page.locator(`[data-testid="projects-grid"] .ag-row[row-index="${i}"]`);
  await expect(page.locator('[data-testid="projects-grid"] .ag-row')).toHaveCount(3);
  await row(0).click();
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
  await expect(row(2)).toHaveClass(/ag-row-selected/);                     // tanlov fokus bilan birga yurdi
  const third = (await row(2).locator('[col-id="name"]').innerText()).split(" · ")[0].trim();
  await page.keyboard.press("Delete");
  await expect(page.getByTestId("ask-dialog")).toContainText(third);        // aynan fokusdagi loyiha so'raladi
  await page.keyboard.press("Escape");
  await expect(page.getByTestId("ask-dialog")).toBeHidden();
  await row(0).click();
  await page.keyboard.press("Control+a");                                  // hammasini tanlash
  await page.keyboard.press("Delete");
  await expect(page.getByTestId("ask-dialog")).toContainText("3");
  await page.getByTestId("ask-ok").press("Enter");                         // tasdiq tugmasida fokus: Enter tasdiqlaydi
  await expect(page.locator('[data-testid="projects-grid"] .ag-row')).toHaveCount(0);
  // matn maydonida Esc oynani yopadi
  await page.getByTestId("btn-new-project").click();
  await page.getByTestId("ask-input").fill("bekor");
  await page.keyboard.press("Escape");
  await expect(page.getByTestId("ask-dialog")).toBeHidden();
  expect(errors).toEqual([]);
});

