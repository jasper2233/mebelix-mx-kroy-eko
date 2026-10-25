// «XNC → MES» (2026-10-25): sozlamada asbobga MES kodi yoziladi, oldindan ko'rishda va loyihaning «XNC ishi» varag'ida ko'rinadi.
import { expect, test } from "@playwright/test";

const SHOT = process.env.SIM_DIR;
const PROG = [
  { cmd: "DrillFront", params: { X: 50, Y: 50, DP: 12, D: 5, T: "Bore5" }, comment: "", children: [] },
  { cmd: "DrillFront", params: { X: 100, Y: 50, DP: 12, D: 5, T: "Bore5" }, comment: "", children: [] },
  { cmd: "DrillLeft", params: { Y: 100, Z: 8, DP: 30, D: 8, T: "Bore8" }, comment: "", children: [] },
  { cmd: "MillStart", params: { X: 100, Y: 100, DP: 8, D: 8, T: "Mill8", C: 0 }, comment: "", children: [] },
  { cmd: "MillLine", params: { X: 300, Y: 100 }, comment: "", children: [] },
  { cmd: "Groove", params: { X1: 0, Y1: 300, X2: 400, Y2: 300, DP: 8, W: 4, D: 4, T: "Cut4" }, comment: "", children: [] },
];

test("XNC → MES: MES kodi, oldindan ko'rish va «XNC ishi»", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const base = await (await request.get("/api/settings/xnc_mes/default")).json();
  const name = `XNC MES ${Date.now() % 1e7}`;
  const pr = await (await request.post("/api/projects", { data: { name } })).json();
  const p = await (await request.post(`/api/projects/${pr.id}/operations`, { data: { type: "CS", name: "LDSP XM" } })).json();
  const cs = p.operations[0].id;
  const p2 = await (await request.post(`/api/projects/${pr.id}/operations/${cs}/parts`, { data: [{ name: "Yon", length: 700, width: 500, qty: 3 }] })).json();
  const part = p2.operations[0].parts[0];
  const p3 = await (await request.post(`/api/projects/${pr.id}/operations/${cs}/parts/${part.id}/xnc`)).json();
  const xid = p3.operations.filter((o: { type: string }) => o.type === "XNC").pop().id;
  await request.patch(`/api/projects/${pr.id}/operations/${xid}`, { data: { xnc: { program: PROG } } });
  try {
    await page.goto("/");
    await page.getByTestId("side-settings").click();
    await page.getByTestId("settings-mes").click();
    await expect(page.getByTestId("xnc-mes")).toBeVisible();
    await page.getByTestId("xm-project").selectOption(pr.id);
    const millKey = "mill|mill8|8||0";
    await expect(page.getByTestId(`xm-code-${millKey}`)).toBeVisible({ timeout: 20000 });
    await page.getByTestId(`xm-code-${millKey}`).fill("FIN-M8");
    await page.getByTestId("xm-code-drill|bore5|5|face|0").fill("FIN-D5");
    await page.getByTestId("xm-save").click();
    await expect(page.getByTestId("xm-preview")).toContainText("FIN-M8", { timeout: 20000 });
    if (SHOT) { await page.getByTestId("xnc-mes").scrollIntoViewIfNeeded(); await page.screenshot({ path: `${SHOT}/x1_sozlama.png`, fullPage: false }); }
    const pkg = await (await request.get(`/api/projects/${pr.id}/mes-package`)).json();
    const codes = Object.fromEntries(pkg.xnc_tools.tools.map((t: { name: string; mes_code: string }) => [t.name, t.mes_code]));
    expect(codes).toMatchObject({ Mill8: "FIN-M8", Bore5: "FIN-D5" });
    // loyiha: «XNC ishi»
    await page.goto(`/#/p/${pr.id}`);
    await page.getByTestId("tab-xnc-work").click();
    await expect(page.getByTestId("xnc-work-table")).toContainText("FIN-D5");
    await expect(page.getByTestId("xnc-work-table")).toContainText("Bore5");
    if (SHOT) await page.screenshot({ path: `${SHOT}/x2_loyiha.png` });
    expect(errors).toEqual([]);
  } finally {
    await request.put("/api/settings/xnc_mes/default", { data: base });
  }
});
