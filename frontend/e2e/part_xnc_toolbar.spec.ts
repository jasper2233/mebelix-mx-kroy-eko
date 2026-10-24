// Detal «XNC Редактор» oynasi: yuqori asboblar panelining HAR BIR tugmasi va «Чертеж» varag'i (onlayn tizimdagidek).
import { expect, test, type APIRequestContext } from "@playwright/test";

type Cmd = { cmd: string; params: Record<string, string | number> };

async function setup(request: APIRequestContext) {
  const pr = await (await request.post("/api/projects", { data: { name: "PXT" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  const p2 = await (await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "bok", length: 700, width: 500, qty: 1 }] })).json();
  const part = p2.operations[0].parts[0];
  const p3 = await (await request.post(`/api/projects/${pr.id}/operations/${cs}/parts/${part.id}/xnc`)).json();
  const xop = p3.operations[p3.operations.length - 1].id;
  const prog = [{ cmd: "DrillFront", params: { X: 100, Y: 37, DP: 12, T: "Bore8" }, comment: "", enabled: true, children: [] },
    { cmd: "DrillLeft", params: { Y: 60, Z: "dz/2", DP: 30, T: "Bore8" }, comment: "", enabled: true, children: [] }];
  await request.patch(`/api/projects/${pr.id}/operations/${xop}`, { data: { xnc: { program: prog } } });
  return { pid: pr.id, xop };
}

test("detal XNC Редактор: barcha asboblar paneli tugmalari va «Чертеж»", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const { pid, xop } = await setup(request);
  const xnc = async () => (await (await request.get(`/api/projects/${pid}`)).json()).operations.find((o: { id: string }) => o.id === xop).xnc;
  const prog = async () => (await xnc()).program as Cmd[];

  await page.goto(`/#/p/${pid}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  await page.locator('button[title="XNC Редактор"]').first().click();
  const dlg = page.getByTestId("part-xnc-dialog");
  await expect(dlg).toBeVisible();
  await expect(page.getByTestId("pxd-head")).toContainText("DX=700 DY=500");
  // 16 ta amal panelda
  for (const id of ["back", "props", "origin", "rotation", "mirror-h", "mirror-v", "move-copy", "mirror-h-copy", "mirror-v-copy",
    "undo", "redo", "del", "up", "down", "tools", "fit", "settings", "help"]) await expect(page.getByTestId(`pxd-${id}`)).toBeVisible();

  const first = page.getByTestId("prog-item-0");
  await first.click();
  // gorizontal ko'zgu nusxa → X = dx-100
  await page.getByTestId("pxd-mirror-h-copy").click();
  await expect.poll(async () => (await prog()).length).toBe(3);
  expect((await prog())[2].params.X).toBe("dx-100");
  // vertikal ko'zgu nusxa → Y = dy-37
  await first.click();
  await page.getByTestId("pxd-mirror-v-copy").click();
  await expect.poll(async () => (await prog()).length).toBe(4);
  expect((await prog())[3].params.Y).toBe("dy-37");
  // siljitib nusxalash: ΔX=32, 2 nusxa → X 132, 164
  await first.click();
  await page.getByTestId("pxd-move-copy").click();
  await page.getByTestId("pxd-move-dx").fill("32");
  await page.getByTestId("pxd-move-n").fill("2");
  await page.getByTestId("pxd-move-ok").click();
  await expect.poll(async () => (await prog()).length).toBe(6);
  expect((await prog()).slice(4).map((c) => c.params.X)).toEqual([132, 164]);
  // butun dastur: gorizontal ko'zgu — X → dx-X, chap teshik → o'ng
  await page.getByTestId("pxd-mirror-h").click();
  await expect.poll(async () => (await prog())[0].params.X).toBe("dx-100");
  expect((await prog())[1].cmd).toBe("DrillRight");
  // vertikal ko'zgu — Y → dy-Y
  await page.getByTestId("pxd-mirror-v").click();
  await expect.poll(async () => (await prog())[0].params.Y).toBe("dy-37");
  // orqaga (Отменить) — vertikal ko'zgu bekor bo'ladi
  await page.getByTestId("pxd-undo").click();
  await expect.poll(async () => (await prog())[0].params.Y).toBe(37);
  await page.getByTestId("pxd-redo").click();
  await expect.poll(async () => (await prog())[0].params.Y).toBe("dy-37");
  // o'chirish / yuqori / pastga
  await page.getByTestId("prog-item-5").click();
  await page.getByTestId("pxd-del").click();
  await expect(page.getByTestId("ask-dialog")).toContainText("удалить команду");   // onlayn kabi tasdiqlash
  await page.getByTestId("ask-ok").click();
  await expect.poll(async () => (await prog()).length).toBe(5);
  await page.getByTestId("prog-item-1").click();
  await page.getByTestId("pxd-up").click();
  await expect.poll(async () => (await prog())[0].cmd).toBe("DrillRight");
  await page.getByTestId("pxd-down").click();
  await expect.poll(async () => (await prog())[1].cmd).toBe("DrillRight");
  // Обратная сторона, Начало координат, Поворот
  await page.getByTestId("pxd-back").click();
  await expect.poll(async () => (await xnc()).face_side).toBe(false);
  await expect(page.getByTestId("pxd-head")).toContainText("Обратная сторона");
  await page.getByTestId("pxd-origin").selectOption("LB");
  await expect.poll(async () => (await xnc()).origin).toBe("LB");
  await page.getByTestId("pxd-rotation").selectOption("90");
  await expect.poll(async () => (await xnc()).rotation).toBe(90);
  // Свойства, Инструменты, Настройки — oynalar ochiladi
  await page.getByTestId("prog-item-0").click();
  await page.getByTestId("pxd-props").click();
  await expect(page.getByTestId("xnc-props")).toBeVisible();
  await page.getByTestId("xnc-props-ok").click();
  await page.getByTestId("pxd-tools").click();
  await expect(page.getByTestId("xnc-tools-dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByTestId("pxd-settings").click();
  await expect(page.getByTestId("xnc-settings")).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByTestId("pxd-fit").click();
  // «Чертеж»: o'lchamli chizma + shtamp
  await page.getByTestId("pxd-tab-sheet").click();
  await expect(page.frameLocator('[data-testid="pxd-sheet"]').locator("body")).toContainText("Рм. заготовки");
  await page.getByTestId("pxd-tab-editor").click();
  // «Отмена» — hammasi oyna ochilgandagi holatga qaytadi
  await page.getByTestId("part-xnc-cancel").click();
  await expect(dlg).toHaveCount(0);
  await expect.poll(async () => (await prog()).length).toBe(2);
  const x = await xnc();
  expect([x.face_side, x.origin, x.rotation]).toEqual([true, "LT", 0]);
  expect(errors).toEqual([]);
});
