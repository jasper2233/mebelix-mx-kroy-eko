// Sinov papkasida sintetik loyiha: import → 1-operatsiya «Раскроить» → «Раскрой» varag'i rasmi (loyiha ochiq qoladi).
//   GIBLAB_ALLOW_WRITE=1 run sokl_import_cut.mjs <fayl.project> <rasm.png>
export default async ({ page, drv, args }) => {
  const want = process.env.GIBLAB_WORK_FOLDER || "test uchun";
  await drv.gotoProjects();
  for (let k = 0; k < 72; k++) {
    const list = await drv.projects().catch(() => null);
    if (list?.path?.includes(want)) break;
    if (list?.rows?.some((r) => r.kind === "folder" && r.name.trim() === want)) { await drv.openFolderPath(want); continue; }
    if (k % 12 === 0) await drv.openFolderPath("/").catch(() => null);
    await page.waitForTimeout(5000);
  }
  await drv.clickText("Добавить");
  await page.waitForURL(/#project$/, { timeout: 120_000 });
  await page.waitForTimeout(3000);
  const ops = await drv.importProject(args[0]);
  await page.waitForTimeout(3000);
  await drv.selectOperation(1); await page.waitForTimeout(1500);
  const st = await drv.cut();
  await drv.tab("Раскрой"); await page.waitForTimeout(2500);
  await page.screenshot({ path: args[1], timeout: 120_000 });
  return { ops, st };
};
