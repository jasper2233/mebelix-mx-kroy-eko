// XNC dastur ro'yxati o'ng tugma menyusi: «Горизонтальное / Вертикальное отзеркаливание» (2026-10-23, onlayn tizim bilan jonli
// solishtirildi): «С копированием» — akslantirilgan nusxa tanlangan buyruqdan keyin, «Без копирования» — buyruqning o'zi;
// «dx-975» ↔ 975, chap teshik ↔ o'ng teshik; MX qo'shimchasi — yoy yo'nalishi va korreksiya tomoni ham almashadi, ko'p tanlov.
import { expect, test, type Page } from "@playwright/test";

const C = (cmd: string, params: Record<string, string | number>) => ({ cmd, params, comment: "", enabled: true, children: [] });

async function program(page: Page, pid: string, oid: string) {
  const p = await (await page.request.get(`/api/projects/${pid}`)).json();
  return p.operations.find((o: { id: string }) => o.id === oid).xnc.program as { cmd: string; params: Record<string, unknown> }[];
}

test("XNC: dastur menyusidan akslantirish (nusxa bilan / nusxasiz, ko'p tanlov)", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "MIRROR" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "XNC", code: "T", name: "tom" } })).json();
  const xop = p.operations[0].id;
  const prog = [
    C("Tool", { N: "Bore8", D: 8 }),
    C("DrillFront", { X: 975, Y: 70, DP: 12, T: "Bore8" }),
    C("DrillLeft", { Y: 100, DP: 30, T: "Bore8" }),
    C("MillStart", { X: 100, Y: 150, DP: 5, T: "Mill8", D: 8, C: 1 }),
    C("MillLine", { X: 400, Y: 150 }),
    C("MillArc", { X: 600, Y: 350, R: 300, DIR: "true" })];
  await request.patch(`/api/projects/${pr.id}/operations/${xop}`,
    { data: { xnc: { by_part_size: false, length: 1950, width: 600, thickness: 16, program: prog } } });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "tom" }).first().click();
  await page.getByTestId("xnc-tab-program").click();

  // xizmat buyrug'i (Tool) — akslantirib bo'lmaydi
  await page.getByTestId("prog-item-0").click({ button: "right" });
  await expect(page.getByTestId("xnc-ctx-mirror-h")).toBeDisabled();
  await page.keyboard.press("Escape");

  // 1) frontal teshik, «С копированием»: nusxa X=dx-975 asl buyruqdan keyin
  await page.getByTestId("prog-item-1").click();
  await page.getByTestId("prog-item-1").click({ button: "right" });
  await page.getByTestId("xnc-ctx-mirror-h").click();
  await expect(page.getByTestId("ask-dialog")).toContainText("Отзеркалить с копированием?");
  await page.getByTestId("ask-ok").click();
  await expect.poll(async () => (await program(page, pr.id, xop)).length).toBe(7);
  let pg = await program(page, pr.id, xop);
  expect(pg[1].params.X).toBe(975);
  expect(pg[2].cmd).toBe("DrillFront");
  expect(pg[2].params.X).toBe("dx-975");

  // 2) nusxani yana akslantirish, «Без копирования»: dx-975 → 975 (ikki marta akslantirish — asl qiymat)
  await page.getByTestId("prog-item-2").click();
  await page.getByTestId("prog-item-2").click({ button: "right" });
  await page.getByTestId("xnc-ctx-mirror-h").click();
  await page.getByTestId("ask-no").click();
  await expect.poll(async () => (await program(page, pr.id, xop))[2].params.X).toBe(975);

  // 3) chap teshik → o'ng teshik (vertikal — Y = dy-100)
  await page.getByTestId("prog-item-3").click();
  await page.getByTestId("prog-item-3").click({ button: "right" });
  await page.getByTestId("xnc-ctx-mirror-h").click();
  await page.getByTestId("ask-no").click();
  await expect.poll(async () => (await program(page, pr.id, xop))[3].cmd).toBe("DrillRight");
  await page.getByTestId("prog-item-3").click({ button: "right" });
  await page.getByTestId("xnc-ctx-mirror-v").click();
  await page.getByTestId("ask-no").click();
  await expect.poll(async () => (await program(page, pr.id, xop))[3].params.Y).toBe("dy-100");

  // 4) kontur (MillStart + MillLine + MillArc) — Shift bilan uchtasi, nusxa konturdan keyin, yoy yo'nalishi va C almashadi
  await page.getByTestId("prog-item-4").click();
  await page.getByTestId("prog-item-6").click({ modifiers: ["Shift"] });
  await page.getByTestId("prog-item-6").click({ button: "right" });
  await page.getByTestId("xnc-ctx-mirror-h").click();
  await page.getByTestId("ask-ok").click();
  await expect.poll(async () => (await program(page, pr.id, xop)).length).toBe(10);
  pg = await program(page, pr.id, xop);
  expect(pg.slice(7).map((c) => c.cmd)).toEqual(["MillStart", "MillLine", "MillArc"]);
  expect(pg[7].params).toMatchObject({ X: "dx-100", Y: 150, C: 2 });
  expect(pg[8].params.X).toBe("dx-400");
  expect(pg[9].params).toMatchObject({ X: "dx-600", DIR: "false" });
  expect(pg[6].params.DIR).toBe("true");                                    // asl kontur o'zgarmagan

  // Esc / «Отмена» — hech narsa o'zgarmaydi
  await page.getByTestId("prog-item-1").click();
  await page.getByTestId("prog-item-1").click({ button: "right" });
  await page.getByTestId("xnc-ctx-mirror-v").click();
  await page.keyboard.press("Escape");
  await expect(page.getByTestId("ask-dialog")).toHaveCount(0);
  expect((await program(page, pr.id, xop)).length).toBe(10);

  // ko'p tanlov: Ctrl+C / Ctrl+V — uchala kontur qatori; Del — tasdiqlash bilan uchalasi o'chadi
  await page.getByTestId("prog-item-7").click();
  await page.getByTestId("prog-item-9").click({ modifiers: ["Shift"] });
  await page.keyboard.press("Control+c");
  await page.keyboard.press("Control+v");
  await expect.poll(async () => (await program(page, pr.id, xop)).length).toBe(13);
  await page.getByTestId("prog-item-10").click();
  await page.getByTestId("prog-item-12").click({ modifiers: ["Shift"] });
  await page.keyboard.press("Delete");
  await expect(page.getByTestId("ask-dialog")).toContainText("(3)");
  await page.getByTestId("ask-ok").click();
  await expect.poll(async () => (await program(page, pr.id, xop)).length).toBe(10);
  expect(errors).toEqual([]);
});

test("XNC: palitradan qo'shilganda «Свойства» darhol ochiladi; yangi buyruqda «Отмена» — buyruq olib tashlanadi", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "PALPROPS" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "XNC", code: "T", name: "tom" } })).json();
  const xop = p.operations[0].id;
  await request.patch(`/api/projects/${pr.id}/operations/${xop}`,
    { data: { xnc: { by_part_size: false, length: 600, width: 400, thickness: 16, program: [] } } });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "tom" }).first().click();
  await page.getByTestId("xnc-tab-program").click();
  await page.getByTestId("pal-DrillFront").click();
  await expect(page.getByTestId("xnc-props")).toBeVisible();
  await page.getByTestId("xnc-props-ok").click();
  await expect.poll(async () => (await program(page, pr.id, xop)).length).toBe(1);
  await page.getByTestId("pal-MillRect").click();
  await expect(page.getByTestId("xnc-props")).toBeVisible();
  await expect.poll(async () => (await program(page, pr.id, xop)).length).toBe(2);
  await page.getByTestId("xnc-props-cancel").click();
  await expect(page.getByTestId("xnc-props")).toHaveCount(0);
  await expect.poll(async () => (await program(page, pr.id, xop)).map((c) => c.cmd)).toEqual(["DrillFront"]);
  // mavjud buyruqda «Отмена» — buyruq qoladi (faqat o'zgarishlar bekor)
  await page.getByTestId("prog-item-0").dblclick();
  await page.getByTestId("xnc-props-cancel").click();
  expect((await program(page, pr.id, xop)).length).toBe(1);
});
