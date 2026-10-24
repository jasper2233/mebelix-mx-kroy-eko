// Bir nechta papkadan eng yangi loyihalarni .project fayl sifatida yuklab olish (faqat o'qish: ochish → «Экспортировать» → yopish).
//   run export_many.mjs <chiqish papkasi> "<papka1|papka2|…>" <har papkadan soni>
// Natija: [{ folder, name, id, file }]. Fayllar korxonaniki — repoga / ommaviy joyga chiqarilmaydi.
const parseDate = (s) => { const m = /(\d{2})\.(\d{2})\.(\d{4})/.exec(s || ""); return m ? Number(m[3] + m[2] + m[1]) : 0; };

export default async ({ page, drv, args }) => {
  const [outDir, folders, perStr] = args;
  const per = Number(perStr || 2);
  const res = [];
  for (const folder of folders.split("|").filter(Boolean)) {
    await drv.gotoProjects();
    await drv.openFolderPath("/");
    const list = await drv.openFolderPath(folder);
    const rows = (list?.rows ?? []).filter((r) => r.kind === "project").sort((a, b) => parseDate(b.date) - parseDate(a.date)).slice(0, per);
    for (const r of rows) {
      try {
        await drv.openFolderPath("/"); await drv.openFolderPath(folder);
        await drv.openProject(r.id);
        await page.waitForTimeout(2500);
        const file = await drv.exportProject(outDir);
        res.push({ folder, name: r.name, id: r.id, date: r.date, file });
        await drv.closeProject();
        await page.waitForTimeout(1500);
      } catch (e) {
        res.push({ folder, name: r.name, id: r.id, error: String(e).slice(0, 200) });
        try { await drv.closeProject(); } catch { /* */ }
      }
    }
  }
  return res;
};
