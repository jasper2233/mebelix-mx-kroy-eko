// Maydon tekshiruvi va manzil (2026-10-17): son maydoni chegaradan tashqari qiymatni jimgina qisqartirmaydi — eski qiymat
// qoladi, sabab ko'rsatiladi, fokus maydonga qaytadi; «#/p/<id>» manzili localStorage dagi oxirgi loyihadan ustun.
import { expect, test, type Page } from "@playwright/test";

async function newProject(page: Page, name: string) {
  await page.goto("/");
  await page.getByTestId("btn-new-project").click();
  await page.getByTestId("ask-input").fill(name);
  await page.getByTestId("ask-ok").click();
  await expect(page.getByTestId("project-name")).toHaveValue(name);
}

test("CS «Толщина»: chegaradan tashqari qiymat — eski qiymat qoladi, sabab va fokus", async ({ page }) => {
  await newProject(page, "VAL thickness");
  await page.getByTestId("add-cs").click();
  await expect(page.locator('[data-testid="ops-grid"] .ag-row')).toHaveCount(1);
  await page.getByTestId("cs-tab-params").click();
  const th = page.getByTestId("cs-thickness");
  await expect(th).toHaveValue("16");
  await expect(page.getByTestId("cs-mult")).toHaveValue("2");                 // 40 / 16

  // 99999 → qisqartirilmaydi (200 emas): 16 qoladi, qizil chegara + maslahat, ogohlantirish, fokus qaytadi
  await th.fill("99999");
  await th.press("Tab");
  await expect(th).toHaveValue("16");
  await expect(th).toHaveClass(/inp-bad/);
  await expect(th).toHaveAttribute("title", /0\.1 – 200 мм/);
  await expect(page.getByTestId("toast-warn")).toContainText("Толщина: допустимо 0.1 – 200 мм");
  await expect(th).toBeFocused();
  await expect(page.getByTestId("cs-mult")).toHaveValue("2");                  // kratnost o'zgarmagan

  // manfiy — xuddi shunday
  await th.fill("-5");
  await th.press("Enter");
  await expect(th).toHaveValue("16");
  await expect(th).toHaveClass(/inp-bad/);

  // paket balandligidan (40) katta — maydonlararo qoida
  await th.fill("50");
  await th.press("Enter");
  await expect(th).toHaveValue("16");
  await expect(page.getByTestId("toast-warn").filter({ hasText: "высоты пакета (40 мм)" })).toBeVisible();

  // to'g'ri qiymat — saqlanadi, qizil belgi yo'qoladi
  await th.fill("18");
  await th.press("Enter");
  await expect(th).toHaveValue("18");
  await expect(th).not.toHaveClass(/inp-bad/);
  await expect(page.getByTestId("cs-mult")).toHaveValue("2");                  // 40 / 18
});

test("#/p/<id> va #/p/<raqam> manzili shu loyihani ochadi (localStorage dagidan ustun)", async ({ page, request }) => {
  await newProject(page, "VAL URL A");
  const a = page.getByTestId("project-name");
  // ochiq loyiha manzilda ko'rinadi
  await expect(page).toHaveURL(/#\/p\/[0-9a-z]+$/);
  const r = await request.post("/api/projects", { data: { name: "VAL URL B" } });
  expect(r.ok()).toBe(true);
  const b = (await r.json()) as { id: string; number: number };

  // to'liq yuklash: localStorage da A, manzilda B — B ochiladi
  await page.goto("about:blank");
  await page.goto(`/#/p/${b.id}`);
  await expect(a).toHaveValue("VAL URL B");

  // shu sahifada manzil o'zgarsa (hashchange) — loyiha raqami bilan ham
  const listA = await request.get("/api/projects", { params: { q: "VAL URL A" } });
  const rowA = ((await listA.json()) as { id: string; number: number; name: string }[]).find((x) => x.name === "VAL URL A")!;
  await page.evaluate((n) => { window.location.hash = `#/p/${n}`; }, rowA.number);
  await expect(a).toHaveValue("VAL URL A");
  await expect(page).toHaveURL(new RegExp(`#/p/${rowA.id}$`));                    // raqam id ga almashadi

  // mavjud bo'lmagan loyiha — xabar va ro'yxat (oq ekran emas)
  await page.evaluate(() => { window.location.hash = "#/p/zzzz_no_such"; });
  await expect(page.getByTestId("btn-new-project")).toBeVisible();
});
