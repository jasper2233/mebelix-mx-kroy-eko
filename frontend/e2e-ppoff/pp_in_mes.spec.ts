// 2026-11-23: stanok postprotsessorlari MES tizimida — MX da nomi bilan ko'rinadi, xira, bosilmaydi («в системе MES»);
// o'z formatlarimiz (CSV …) ishlaydi; «Настройки → Постпроцессоры» bandi xira. XNC muharriri (sverlo/freza belgilash) o'zgarmagan.
import { expect, test } from "@playwright/test";

const PARTS: [number, number, number][] = [[748, 1468, 1], [200, 1468, 2], [480, 800, 1], [900, 800, 1]];
const SHOT = process.env.PPOFF_SHOT_DIR;

test("postprotsessorlar MES da: stanoklar xira, CSV ishlaydi, sozlamalar bandi xira", async ({ page, request }) => {
  const p = await (await request.post("/api/projects", { data: { name: "E2E PP MES" } })).json();
  const withCs = await (await request.post(`/api/projects/${p.id}/operations`, { data: { type: "CS", code: "LDSP16", name: "LDSP" } })).json();
  const cs = withCs.operations[withCs.operations.length - 1].id as string;
  await request.post(`/api/projects/${p.id}/operations/${cs}/parts`,
    { data: PARTS.map(([length, width, qty], i) => ({ name: `P${i + 1}`, length, width, qty })) });
  expect((await request.post(`/api/projects/${p.id}/operations/${cs}/optimize?quality=fast`)).ok()).toBe(true);
  expect((await (await request.get("/api/postprocessors/access")).json()).in_mes).toBe(true);

  await page.goto(`/#/p/${p.id}`);
  await expect(page.getByTestId("project-name")).toHaveValue("E2E PP MES");
  await page.locator('[data-testid="ops-grid"] .ag-row[row-index="0"]').click();
  await page.getByTestId("cs-tab-cut").click();
  await page.getByTestId("btn-pp").click();
  await expect(page.getByTestId("pp-dialog")).toBeVisible();
  const m = page.getByTestId("pp-machine:holzma_ptx");
  await expect(m).toHaveClass(/ppick-closed/);
  await expect(m).toHaveAttribute("aria-disabled", "true");
  await expect(m).toHaveAttribute("title", /MES/);
  await expect(m).toContainText("MES");
  if (SHOT) await page.getByTestId("pp-dialog").screenshot({ path: `${SHOT}/1-kroy-postprotsessorlar.png` });
  const calls: string[] = [];
  page.on("request", (r) => { if (r.url().includes("/postprocess")) calls.push(r.url()); });
  await m.click({ force: true });
  await page.waitForTimeout(400);
  expect(calls).toEqual([]);                                   // stanok — hech qanday so'rov
  const csv = page.getByTestId("pp-csv");
  await expect(csv).not.toHaveClass(/ppick-closed/);
  const resp = page.waitForResponse((r) => r.url().includes("/postprocess") && r.url().includes("key=csv"));
  await csv.click();
  expect((await resp).status()).toBe(200);                     // o'z formatimiz ishlaydi

  await page.goto("/");
  await page.getByTestId("side-settings").click();
  const item = page.getByTestId("settings-pp");
  await expect(item).toHaveClass(/side-item-mes/);              // boshqa MES bandlari kabi xira, «MES» belgisi bilan
  await expect(item).toContainText("MES");
  await item.click({ force: true });                             // aria-disabled — Playwright kutmasin
  await page.waitForTimeout(300);
  await expect(page.getByTestId("pp-settings")).toHaveCount(0);   // sozlamalar oynasi ochilmaydi
  if (SHOT) await page.locator(".side-menu").first().screenshot({ path: `${SHOT}/2-sozlamalar.png` });
});
