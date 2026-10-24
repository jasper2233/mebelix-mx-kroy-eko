// Sinov papkasida (GIBLAB_WORK_FOLDER, standart «test uchun»): har faylni import → har CS operatsiyani «Раскроить» → «Экспортировать».
//   GIBLAB_ALLOW_WRITE=1 run import_cut_export.mjs <chiqish papkasi> <ro'yxat.txt (har qatorda fayl yo'li)> [--here]
// Onlayn tizimda import loyiha ichidan: «Добавить» (yangi bo'sh loyiha) → «Импортировать». --here — ochiq loyihaga (1-fayl).
// Har loyiha natijasi <chiqish>/progress.json ga darhol yoziladi (uzilib qolsa ham yo'qolmaydi).
import fs from "node:fs";
import path from "node:path";
// Sinov papkasiga ishonchli kirish: allaqachon ichida bo'lsa — joyida; aks holda ildiz ro'yxati to'liq yuklanib, papka qatori
// ko'ringuncha kutiladi (xodimlar papkalari bilan ildiz bir necha daqiqa yuklanishi mumkin).
async function ensureFolder(drv, page) {
  const want = process.env.GIBLAB_WORK_FOLDER || "test uchun";
  await drv.gotoProjects();
  for (let k = 0; k < 72; k++) {
    const list = await drv.projects().catch(() => null);
    if (list?.path?.includes(want)) return;
    if (list?.rows?.some((r) => r.kind === "folder" && r.name.trim() === want)) { await drv.openFolderPath(want); continue; }
    if (k % 12 === 0) await drv.openFolderPath("/").catch(() => null);
    await page.waitForTimeout(5000);
  }
  throw new Error(`«${want}» papkasiga kirib bo'lmadi`);
}

export default async ({ page, drv, args }) => {
  const [outDir, listFile] = args;
  fs.mkdirSync(outDir, { recursive: true });
  const prog = path.join(outDir, "progress.json");
  const res = fs.existsSync(prog) ? JSON.parse(fs.readFileSync(prog, "utf8")) : [];
  const done = new Set(res.filter((r) => r.file).map((r) => r.src));
  const files = fs.readFileSync(listFile, "utf8").split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
  for (const [i, src] of files.entries()) {
    if (done.has(src)) continue;
    const rec = { n: i + 1, src, cuts: [] };
    try {
      if (!(args[2] === "--here" && i === 0)) {
        await ensureFolder(drv, page);
        await drv.clickText("Добавить");
        await page.waitForURL(/#project$/, { timeout: 120_000 });
        await page.waitForTimeout(3000);
      }
      const ops = await drv.importProject(src);
      await page.waitForTimeout(3000);
      const cs = (ops ?? []).filter((o) => o.type === "CS");
      for (const o of cs) {
        await drv.selectOperation(Number(o.n));
        await page.waitForTimeout(1500);
        const st = await drv.cut();
        rec.cuts.push({ op: o.n, sheets: st.sheets ?? null });
      }
      const f = await drv.exportProject(outDir);
      const dst = path.join(outDir, `gl_${String(i + 1).padStart(2, "0")}.project`);
      fs.renameSync(f, dst);
      rec.file = dst;
      await drv.closeProject();
      await page.waitForTimeout(1500);
    } catch (e) {
      rec.error = String(e).slice(0, 300);
      try { await drv.closeProject(); } catch { /* */ }
    }
    res.push(rec);
    fs.writeFileSync(prog, JSON.stringify(res, null, 1));
  }
  return res.map((r) => ({ n: r.n, cuts: r.cuts?.length, ok: !!r.file, error: r.error }));
};
