// Detallar paneli → «XNC Редактор»: detal ishlovi alohida oynada (onlayn tizimdagidek) — «Сверление» ro'yxatidan teshik qo'shish,
// «Отмена» — dialog yaratgan XNC operatsiyasi o'chadi, «Ok» — saqlanadi.
import { expect, test } from "@playwright/test";

test("detal uchun XNC Редактор oynasi: teshik qo'shish, Отмена / Ok", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pr = await (await request.post("/api/projects", { data: { name: "PXNC" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "pol", length: 700, width: 500, qty: 1 }] });
  const ops = async () => ((await (await request.get(`/api/projects/${pr.id}`)).json()).operations as { type: string;
    xnc?: { program: { cmd: string; params: Record<string, unknown> }[] } }[]);

  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-parts").click();
  const open = async () => {
    await page.locator('button[title="XNC Редактор"]').first().click();
    await expect(page.getByTestId("part-xnc-dialog")).toBeVisible();
    await expect(page.getByTestId("part-xnc-drills")).toContainText("Фронтальное");
  };
  const addDrill = async () => {
    await page.getByTestId("part-xnc-drills").locator("button").first().click();
    await page.getByTestId("pdrill-x").fill("100");
    await page.getByTestId("pdrill-y").fill("37");
    await page.getByTestId("pdrill-ok").click();
    await expect.poll(async () => (await ops()).find((o) => o.type === "XNC")?.xnc?.program.length ?? 0).toBe(1);
  };
  // Отмена — hammasi qaytadi
  await open();
  await addDrill();
  await page.getByTestId("part-xnc-cancel").click();
  await expect(page.getByTestId("part-xnc-dialog")).toHaveCount(0);
  await expect.poll(async () => (await ops()).filter((o) => o.type === "XNC").length).toBe(0);
  // Ok — saqlanadi
  await open();
  await addDrill();
  await page.getByTestId("part-xnc-ok").click();
  await expect(page.getByTestId("part-xnc-dialog")).toHaveCount(0);
  const x = (await ops()).find((o) => o.type === "XNC");
  expect(x?.xnc?.program[0]).toMatchObject({ cmd: "DrillFront", params: { X: 100, Y: 37 } });
  expect(errors).toEqual([]);
});
