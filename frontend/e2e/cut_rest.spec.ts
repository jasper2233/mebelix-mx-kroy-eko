// «До кроить» (onlayn tizimdagidek, 2026-10-21): qolgan detallar tayyor kartaning bo'sh joyiga qaytadi (standart);
// operator «faqat yangi listlarga» ni tanlasa — tayyor kartalar o'zgarmaydi. Tahrir oynasida «Таблица команд».
import { expect, test, type APIRequestContext } from "@playwright/test";

type Node = { k: string; u?: number; c?: Node[] };
const pathsP = (n: Node, pre: number[] = [], out: number[][] = []) => {
  (n.c ?? []).forEach((c, i) => (c.k === "P" ? out.push([...pre, i]) : c.k === "C" && pathsP(c, [...pre, i], out)));
  return out;
};

async function setup(request: APIRequestContext) {
  const pr = await (await request.post("/api/projects", { data: { name: "REST" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", code: "L16", name: "LDSP" } })).json();
  const cs = p.operations[0].id;
  await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [
    { name: "A", length: 700, width: 500, qty: 4, grain: false }, { name: "B", length: 400, width: 300, qty: 6, grain: false }] });
  const res = await (await request.post(`/api/projects/${pr.id}/operations/${cs}/optimize?quality=fast`)).json();
  const paths = pathsP(res.maps[0].strips[0]).slice(0, 2);
  const d = await (await request.post(`/api/projects/${pr.id}/operations/${cs}/edit`,
    { data: { result: res, action: { type: "remove", map: 1, paths } } })).json();
  await request.put(`/api/projects/${pr.id}/operations/${cs}/result`, { data: d });
  return { pid: pr.id, cs, maps: res.maps.length as number };
}

test("«До кроить»: oynasiz, tayyor kartaning bo'sh joyiga qaytarish", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const { pid, maps } = await setup(request);
  const result = async () => (await (await request.get(`/api/projects/${pid}`)).json()).operations[0].result;
  await page.goto(`/#/p/${pid}`);
  await page.locator(".ag-row").filter({ hasText: "LDSP" }).first().click();
  await page.getByTestId("cs-tab-cut").click();
  // tahrir oynasida «Таблица команд»
  await page.getByTestId("btn-edit-cut").click();
  await page.getByTestId("ed-toggle-commands").click();
  await expect(page.getByTestId("ed-commands-table").locator("tbody tr").first()).toBeVisible();
  await page.getByRole("button", { name: "Отмена" }).last().click();
  // «До кроить» — oynasiz, darhol tayyor kartaning bo'sh joyiga (foydalanuvchi qarori)
  await page.getByTestId("btn-cut-rest").click();
  await expect.poll(async () => (await result()).unplaced.length).toBe(0);
  expect((await result()).maps.length).toBe(maps);
  expect(errors).toEqual([]);
});
