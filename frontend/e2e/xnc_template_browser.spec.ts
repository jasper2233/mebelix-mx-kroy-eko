// XNC «Шаблон» → «Добавить» (onlayn «Открыть шаблоны обработки» oynasidagidek, 2026-10-23): papkalar, rasmli shablonlar,
// «Открыть» — dastur oxiriga qo'shiladi; foydalanuvchi papkasi yaratish; o'rnatilgan papka — faqat o'qish.
import { expect, test } from "@playwright/test";

const SP = process.env.AUDIT_SHOT_DIR;

test("Открыть шаблоны обработки: papkalar, eskiz, oxiriga qo'shish", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "TPLB" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "XNC", code: "F", name: "fasad" } })).json();
  const xop = p.operations[0].id;
  const start = [{ cmd: "DrillFront", params: { X: 50, Y: 50, DP: 12, T: "Bore8", D: 8 }, comment: "", enabled: true, children: [] }];
  await request.patch(`/api/projects/${pr.id}/operations/${xop}`,
    { data: { xnc: { by_part_size: false, length: 400, width: 700, thickness: 16, program: start } } });
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "fasad" }).first().click();
  await page.getByTestId("xnc-tab-program").click();
  await page.getByTestId("xnc-tpl-add").click();
  const dlg = page.getByTestId("xtb");
  await expect(dlg).toContainText("Открыть шаблоны обработки");
  for (const f of ["Типовые фрезеровки", "Фасады МДФ", "Образцы MebeliX"]) await expect(dlg.getByTestId(`xtb-folder-${f}`)).toBeVisible();
  if (SP) await page.screenshot({ path: `${SP}/xtb_root.png` });
  await dlg.getByTestId("xtb-folder-Фасады МДФ").dblclick();
  await expect(dlg.getByTestId("xtb-path")).toHaveText("Фасады МДФ /");
  const arch = dlg.getByTestId("xtb-tpl-lib:f_arch");
  await expect(arch.locator("svg")).toHaveCount(1);                              // eskiz
  await expect(dlg.locator(".xtb-tile")).toHaveCount(9);
  if (SP) await page.screenshot({ path: `${SP}/xtb_fasad.png` });
  // o'rnatilgan papkada «Удалить» / «Переименовать» — faqat o'qish
  await arch.click();
  await expect(dlg.getByTestId("xtb-name")).toHaveValue("Арка");
  await expect(dlg.getByTestId("xtb-move")).toBeDisabled();
  await dlg.getByTestId("xtb-open").click();
  await expect(dlg).toHaveCount(0);
  await expect.poll(async () => {
    const pj = await (await request.get(`/api/projects/${pr.id}`)).json();
    const prog = pj.operations.find((o: { id: string }) => o.id === xop).xnc.program as { cmd: string }[];
    return [prog.length > 5, prog[0].cmd, prog.some((c) => c.cmd === "MillArc3P")];
  }).toEqual([true, "DrillFront", true]);                                         // eski buyruq qoldi, arka oxiriga qo'shildi

  // papka: yaratish, ichiga kirish, yuqoriga / boshiga
  await page.getByTestId("xnc-tpl-add").click();
  await dlg.getByTestId("xtb-add-folder").click();
  await page.getByTestId("ask-input").fill("Кухни");
  await page.getByTestId("ask-ok").click();
  await expect(dlg.getByTestId("xtb-folder-Кухни")).toBeVisible();
  await dlg.getByTestId("xtb-folder-Кухни").dblclick();
  await expect(dlg).toContainText("Папка пуста");
  await dlg.getByTestId("xtb-home").click();
  await expect(dlg.getByTestId("xtb-folder-Типовые фрезеровки")).toBeVisible();
  await dlg.getByTestId("xtb-folder-Типовые фрезеровки").dblclick();
  await expect(dlg.locator(".xtb-tile")).toHaveCount(14);
  if (SP) await page.screenshot({ path: `${SP}/xtb_mill.png` });
  await dlg.getByTestId("xtb-up").click();
  await dlg.getByTestId("xtb-folder-Кухни").click();
  await dlg.getByTestId("xtb-delete").click();
  await page.getByTestId("ask-ok").click();
  await expect(dlg.getByTestId("xtb-folder-Кухни")).toHaveCount(0);
  await dlg.getByTestId("xtb-cancel").click();
  expect(errors).toEqual([]);
});
