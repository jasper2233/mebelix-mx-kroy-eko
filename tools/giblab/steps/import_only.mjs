// Sinov papkasida yangi loyiha ochib faylni import qiladi (kroy qilinmaydi): GIBLAB_ALLOW_WRITE=1 run import_only.mjs <fayl>
export default async ({ page, drv, args }) => {
  const want = process.env.GIBLAB_WORK_FOLDER || "test uchun";
  await drv.gotoProjects();
  for (let k = 0; k < 40; k++) {
    const list = await drv.projects().catch(() => null);
    if (list?.path?.includes(want)) break;
    if (list?.rows?.some((r) => r.kind === "folder" && r.name.trim() === want)) { await drv.openFolderPath(want); continue; }
    if (k % 10 === 0) await drv.openFolderPath("/").catch(() => null);
    await page.waitForTimeout(4000);
  }
  await drv.clickText("Добавить");
  await page.waitForURL(/#project$/, { timeout: 120_000 });
  await page.waitForTimeout(3000);
  const ops = await drv.importProject(args[0]);
  await page.waitForTimeout(3000);
  return (ops ?? []).filter((o) => o.type !== "XNC").map((o) => [o.n, o.type, o.name]);
};
