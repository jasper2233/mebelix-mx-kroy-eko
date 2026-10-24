// Joriy (ochiq) papkadagi loyihalarni ID bo'yicha .project faylga yuklab olish — faqat o'qish: ochish → «Экспортировать» → yopish.
//   run export_ids.mjs <chiqish papkasi> "<id1,id2,…>"
// Yopilgandan keyin papka ro'yxati qayta yuklanadi (xodimlar papkasida ~2 daqiqa) — keyingi ID ko'ringuncha kutiladi.
export default async ({ page, drv, args }) => {
  const [outDir, ids] = args;
  const res = [];
  const waitRow = async (id) => {
    for (let k = 0; k < 480; k++) {
      const l = await drv.projects();
      const r = l?.rows.find((x) => x.id === id);
      if (r) return r;
      await page.waitForTimeout(500);
    }
    return null;
  };
  for (const id of ids.split(",").filter(Boolean)) {
    const t0 = Date.now();
    try {
      const row = await waitRow(id);
      if (!row) { res.push({ id, error: "ro'yxatda topilmadi" }); continue; }
      await drv.openProject(id);
      await page.waitForTimeout(3000);
      const file = await drv.exportProject(outDir);
      res.push({ id, name: row.name, date: row.date, file, s: Math.round((Date.now() - t0) / 1000) });
      await drv.closeProject();
    } catch (e) {
      res.push({ id, error: String(e).slice(0, 200) });
      try { await drv.closeProject(); } catch { /* */ }
    }
    console.error(JSON.stringify(res[res.length - 1]));
  }
  return res;
};
