// 2026-10-18: mijoz uchun ochilmagan postprotsessor «Постпроцессоры» oynasida nomi bilan ko'rinadi, kulrang fonda, bosilganda hech
// narsa bo'lmaydi (so'rov ham ketmaydi); ochilgani — ishlaydi (fayl yuklanadi). Ochish/yopish — admin (lokal rejim — admin).
import { expect, test } from "@playwright/test";

const PARTS: [number, number, number][] = [[748, 1468, 1], [200, 1468, 2], [480, 800, 1], [900, 800, 1]];

test("postprotsessor: yopiq — xira va bosilmaydi, ochilgan — ishlaydi", async ({ page, request }) => {
  const p = await (await request.post("/api/projects", { data: { name: "E2E PP ACCESS" } })).json();
  const withCs = await (await request.post(`/api/projects/${p.id}/operations`, { data: { type: "CS", code: "LDSP16", name: "LDSP" } })).json();
  const cs = withCs.operations[withCs.operations.length - 1].id as string;
  await request.post(`/api/projects/${p.id}/operations/${cs}/parts`,
    { data: PARTS.map(([length, width, qty], i) => ({ name: `P${i + 1}`, length, width, qty })) });
  expect((await request.post(`/api/projects/${p.id}/operations/${cs}/optimize?quality=fast`)).ok()).toBe(true);
  // admin: faqat HOLZMA PTX ochiq
  expect((await request.put("/api/postprocessors/access", { data: { open: ["holzma_ptx"] } })).ok()).toBe(true);

  try {
    await page.goto(`/#/p/${p.id}`);
    await expect(page.getByTestId("project-name")).toHaveValue("E2E PP ACCESS");
    await page.locator('[data-testid="ops-grid"] .ag-row[row-index="0"]').click();
    await page.getByTestId("cs-tab-cut").click();
    await page.getByTestId("btn-pp").click();
    await expect(page.getByTestId("pp-dialog")).toBeVisible();

    const closed = page.getByTestId("pp-machine:scm_wincut");
    await expect(closed).toBeVisible();                                       // nomi bilan ro'yxatda
    await expect(closed).toHaveClass(/ppick-closed/);
    await expect(closed).toHaveAttribute("aria-disabled", "true");
    await expect(closed).toHaveAttribute("title", /администратор/);
    await expect(closed).toHaveCSS("background-color", "rgb(236, 239, 242)");  // kulrang fon

    const calls: string[] = [];
    page.on("request", (r) => { if (r.url().includes("/postprocess")) calls.push(r.url()); });
    await closed.click({ force: true });                                      // aria-disabled: Playwright kutmasin, haqiqiy bosish
    await page.waitForTimeout(400);
    expect(calls).toEqual([]);                                                // hech qanday so'rov
    await expect(page.getByTestId("pp-dialog")).toBeVisible();                // oyna yopilmadi

    const open = page.getByTestId("pp-machine:holzma_ptx");
    await expect(open).not.toHaveClass(/ppick-closed/);
    const resp = page.waitForResponse((r) => r.url().includes("/postprocess") && r.url().includes("holzma_ptx"));
    await open.click();
    expect((await resp).status()).toBe(200);                                  // fayl chiqdi
    await expect(page.getByTestId("pp-dialog")).toBeHidden();

    // server ham rad etadi (UI ni chetlab o'tib bo'lmaydi)
    const r = await request.get(`/api/projects/${p.id}/operations/${cs}/postprocess`, { params: { key: "machine:scm_wincut" } });
    expect(r.status()).toBe(403);
  } finally {
    await request.put("/api/postprocessors/access", { data: { open: null } });
  }
});
