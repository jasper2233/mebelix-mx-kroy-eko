// Til tanlovi: «Ўзбекча» (kirill) — menyu va server xabarlari kirillda; «O'zbekcha» (lotin) ga qaytish; tanlov saqlanadi.
import { expect, test } from "@playwright/test";

test("Til: Ўзбекча (kirill) ↔ O'zbekcha (lotin) ↔ Русский — menyu, <html lang>, server xabari, saqlanish", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  await page.goto("/");
  await page.evaluate(() => localStorage.setItem("mxk_lang", JSON.stringify("ru")));
  await page.reload();

  // til bo'limi: uchta tanlov (ru, uz-Cyrl, uz) — kirill lotindan oldin
  await page.getByRole("button", { name: "Язык" }).click();
  const items = page.locator('[data-testid^="lang-"]');
  await expect(items).toHaveCount(3);
  await expect(items.nth(0)).toHaveAttribute("data-testid", "lang-ru");
  await expect(items.nth(1)).toHaveAttribute("data-testid", "lang-uz-Cyrl");
  await expect(items.nth(2)).toHaveAttribute("data-testid", "lang-uz");
  await expect(page.getByTestId("lang-uz-Cyrl")).toContainText("Ўзбекча");

  // Ўзбекча: menyu kirillda
  await page.getByTestId("lang-uz-Cyrl").click();
  await expect(page.getByRole("button", { name: "Тил" })).toBeVisible();
  await expect(page.getByText("Лойиҳалар").first()).toBeVisible();
  await expect(page.getByText("Созламалар").first()).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("lang", "uz-Cyrl");
  expect(await page.evaluate(() => localStorage.getItem("mxk_lang"))).toBe(JSON.stringify("uz-Cyrl"));

  // server xabari ham kirillda (Accept-Language: uz-Cyrl)
  const msg = await page.evaluate(async () => {
    const r = await fetch("/api/projects/yoq-loyiha", { headers: { "Accept-Language": JSON.parse(localStorage.getItem("mxk_lang") ?? '"ru"') } });
    return (await r.json()).detail as string;
  });
  expect(msg).toBe("Лойиҳа топилмади");

  // qayta yuklash — tanlov saqlanadi
  await page.reload();
  await expect(page.getByRole("button", { name: "Тил" })).toBeVisible();

  // O'zbekcha (lotin) ga qaytish
  await page.getByRole("button", { name: "Тил" }).click();
  await page.getByTestId("lang-uz").click();
  await expect(page.getByRole("button", { name: "Til" })).toBeVisible();
  await expect(page.getByText("Loyihalar").first()).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("lang", "uz");

  // Русский
  await page.getByTestId("lang-ru").click();
  await expect(page.getByRole("button", { name: "Язык" })).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("lang", "ru");
  expect(errors).toEqual([]);
});
