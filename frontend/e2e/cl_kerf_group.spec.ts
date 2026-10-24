// (CL) «Толщина пилы для групповых деталей» — onlayndagidek tahrirlanadi va saqlanadi; bo'shatilsa — asosiy propil (null).
import { expect, test } from "@playwright/test";

test("CL: guruh propili tahrirlanadi", async ({ page, request }) => {
  const pr = await (await request.post("/api/projects", { data: { name: "CLKG" } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CL", code: "PL", name: "Plintus" } })).json();
  const op = p.operations[0].id;
  const cl = async () => (await (await request.get(`/api/projects/${pr.id}`)).json()).operations[0].cl;
  await page.goto(`/#/p/${pr.id}`);
  await page.locator(".ag-row").filter({ hasText: "Plintus" }).first().click();
  await page.getByTestId("cl-tab-params").click();
  const inp = page.getByTestId("cl-kerf-group");
  await expect(inp).toBeEnabled();
  await expect(inp).toHaveValue("");
  await inp.fill("2.5");
  await inp.press("Enter");
  await expect.poll(async () => (await cl()).kerf_group).toBe(2.5);
  await inp.fill("");
  await inp.press("Enter");
  await expect.poll(async () => (await cl()).kerf_group).toBeNull();
  expect(op).toBeTruthy();
});
