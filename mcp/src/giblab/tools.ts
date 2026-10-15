/** `giblab_*` vositalari — onlayn tizim brauzer orqali (o'qish standart; yozish himoyalangan). */
import path from "node:path";
import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { Config } from "../config.js";
import type { GiblabDriver } from "./driver.js";
import { fail, json, table, text, type ToolResult } from "../util.js";
import { PAGELIB } from "./pagelib.js";

export function registerGiblabTools(server: McpServer, cfg: Config, giblab: () => Promise<GiblabDriver>): void {
  const reg = <S extends z.ZodRawShape>(name: string, description: string, shape: S, fn: (g: GiblabDriver, a: z.infer<z.ZodObject<S>>) => Promise<ToolResult>) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    server.registerTool(name, { description, inputSchema: shape }, (async (args: z.infer<z.ZodObject<S>>) => {
      try { return await fn(await giblab(), args); } catch (e) { return fail(`Onlayn tizim: ${String((e as Error)?.message || e)}`); }
    }) as any);

  server.registerTool("giblab_pagelib", { description: "Sahifa kutubxonasi (JS) matni — Claude in Chrome `javascript_tool` ga yuborib `__gl.*` funksiyalarini qo'lda ishlatish uchun (brauzer ulanmagan bo'lsa ham ishlaydi).", inputSchema: {} },
    async () => text(PAGELIB));

  reg("giblab_status", "Ulanish holati: rejim, URL, kirgan foydalanuvchi, ochiq loyiha, tanlangan operatsiya, ochiq dialoglar.", {}, async (g) => json(await g.status()));

  reg("giblab_projects", "Loyihalar ro'yxati (papka yo'li bo'yicha, masalan \"test uchun\" yoki \"1 Behzod/1230 Jamshid\"; bo'sh — joriy ko'rinish).",
    { folder: z.string().optional() },
    async (g, a) => {
      const list = a.folder !== undefined ? await g.openFolderPath(a.folder) : (await g.gotoProjects(), await g.projects());
      if (!list) return fail("Loyihalar jadvali topilmadi (sahifa #projects emasmi?)");
      return text(`Papka: ${list.path || "/"}\n` + table(["№", "Tur", "ID", "Владелец", "Состояние", "Дата", "Стоимость", "Наименование"], list.rows.map((r) => [r.n, r.kind, r.id, r.owner, r.status, r.date, r.cost, r.name])));
    });

  reg("giblab_project_open", "Joriy papkadagi loyihani ochish (nomi yoki ID) → operatsiyalar jadvali.", { name_or_id: z.string(), folder: z.string().optional() },
    async (g, a) => { if (a.folder !== undefined) await g.openFolderPath(a.folder); const ops = await g.openProject(a.name_or_id); return text(opsTable(ops)); });

  reg("giblab_project_close", "«Закрыть проект».", {}, async (g) => { await g.closeProject(); return json(await g.status()); });

  reg("giblab_operations", "Ochiq loyihaning operatsiyalar jadvali (№, Тип, Код/Изделие, Наименование, narxlar).", {}, async (g) => text(opsTable(await g.operations())));

  reg("giblab_select_operation", "Operatsiyani tanlash (jadvaldagi tartib raqami 1.. yoki nomi).", { op: z.union([z.number().int(), z.string()]) },
    async (g, a) => { const o = await g.selectOperation(typeof a.op === "number" ? a.op - 1 : a.op); return json({ selected: o, tabs: await g.gl("tabs()") }); });

  reg("giblab_tab", "Pastki panel varag'ini ochish: Параметры / Детали / Листы и остатки / Раскрой (va boshqa operatsiya turlari varaqlari).", { name: z.string() },
    async (g, a) => (await g.tab(a.name)) ? json({ tabs: await g.gl("tabs()") }) : fail(`Varaq topilmadi: ${a.name}`));

  reg("giblab_table", "Ko'rinayotgan jadvalni o'qish: sarlavha so'zlari bo'yicha (masalan [\"Д-на\", \"Ш-на\"] — «Детали»; [\"Длина\", \"Ширина\", \"Кол\"] — «Листы и остатки»). Bo'sh — barcha jadvallar sarlavhalari.",
    { header: z.array(z.string()).optional(), limit: z.number().int().min(1).max(5000).default(500) },
    async (g, a) => {
      if (!a.header?.length) return json(await g.gl("tables()"));
      const t = await g.table(a.header, a.limit);
      if (!t) return fail("Jadval topilmadi");
      return text(table(t.header, t.rows.map((r) => r.cells)) + `\n${t.rows.length} qator`);
    });

  reg("giblab_cut_stats", "Tanlangan kroy operatsiyasining «Раскрой» ko'rsatkichlari (listlar, F, LT, деловой) — matndan; raw — panel yozuvlari.", { all: z.boolean().default(false) },
    async (g, a) => {
      if (a.all) { const rows = await g.cuttingStatsAll(); return text(table(["Operatsiya", "Tur", "Listlar", "F %", "LT m", "Деловой m²", "Kartalar"], rows.map((r) => [r.name, r.type, r.sheets, r.fill, r.cutLengthM, r.business, r.maps]))); }
      return json(await g.cuttingStats());
    });

  reg("giblab_cut", "[YOZADI] «Раскроить» — tanlangan operatsiyani onlayn tizimda kesish (loyiha darhol saqlanadi). GIBLAB_ALLOW_WRITE=1 kerak.", {},
    async (g) => json(await g.cut()));

  reg("giblab_project_import", "[YOZADI] «Импортировать» — lokal `.project` faylidan onlayn loyiha yaratish (joriy papkada). GIBLAB_ALLOW_WRITE=1 kerak.", { path: z.string(), folder: z.string().optional() },
    async (g, a) => { if (a.folder !== undefined) await g.openFolderPath(a.folder); return text(opsTable(await g.importProject(a.path))); });

  reg("giblab_project_export", "«Экспортировать» — ochiq loyihani `.project` fayl sifatida yuklab olish.", { out_dir: z.string().optional() },
    async (g, a) => json({ saved: await g.exportProject(a.out_dir || cfg.outDir) }));

  reg("giblab_click", "Ko'rinayotgan matnli elementni bosish (menyu bandi, tugma, varaq). Yozuvchi amallar (Раскроить, Удалить, Сохранить, Импортировать…) uchun GIBLAB_ALLOW_WRITE=1 kerak.",
    { text: z.string(), partial: z.boolean().default(false) },
    async (g, a) => {
      if (/^(Раскроить|Удалить|Удаление|Сохранить|Импортировать|Импорт|Заказать|Очистить|Добавить|Переместить|Переименовать|Копировать)/i.test(a.text)) await g.assertWrite(a.text);
      const ok = await g.clickText(a.text, a.partial);
      return ok ? json({ clicked: a.text, dialogs: await g.gl("dialogs()") }) : fail(`Topilmadi: ${a.text}`);
    });

  reg("giblab_dialogs", "Ochiq dialog oynalari (sarlavha, matn, tugmalar); button berilsa — shu tugma bosiladi (masalan «Отмена», «Ок»). key — haqiqiy klaviatura (masalan «Space», «Escape»).",
    { button: z.string().optional(), key: z.string().optional() },
    async (g, a) => {
      if (a.button) { const r = await g.gl<{ cx: number; cy: number } | null>(`dialogButtonRect(${JSON.stringify(a.button)})`); if (!r) return fail(`Tugma topilmadi: ${a.button}`); await g.clickXY(r.cx, r.cy); await g.wait(500); }
      if (a.key) await g.pressKey(a.key);
      return json({ dialogs: await g.gl("dialogs()"), native: g.dialogLog.slice(-5) });
    });

  reg("giblab_menu", "Chap menyu bandlari (faol / xira) va pastki panel varaqlari.", {}, async (g) => json({ menu: await g.gl("menu()"), tabs: await g.gl("tabs()"), header: await g.gl("header()") }));

  reg("giblab_inventory", "Ekran inventari (yozuvlar, maslahatlar, ro'yxat variantlari) — MebeliX Kroy bilan o'xshashlikni o'lchash uchun; out_path berilsa JSON faylga.", { out_path: z.string().optional() },
    async (g, a) => { const inv = await g.inventory(a.out_path); return json({ count: inv.length, saved: a.out_path ?? null, sample: inv.slice(0, 60) }); });

  reg("giblab_screenshot", "Skrinshot faylga.", { out_path: z.string().optional() },
    async (g, a) => json({ saved: await g.screenshot(a.out_path || path.join(cfg.outDir, `giblab_${Date.now()}.png`)) }));

  reg("giblab_text", "Sahifaning ko'rinayotgan matni (qisqartirilgan).", {}, async (g) => text(await g.gl<string>("text()")));

  reg("giblab_eval", "Sahifada JavaScript bajarish (window.__gl.* kutubxonasi mavjud). Ehtiyot: tizimni o'zgartiruvchi amallar uchun ishlatmang.", { js: z.string() },
    async (g, a) => json(await g.evaluate(a.js)));

  reg("giblab_set_prompt_answer", "Brauzer `prompt()` oynasiga (masalan «8-символьное имя программы») avtomatik javob matni.", { value: z.string().max(64) },
    async (g, a) => { g.promptAnswer = a.value; return json({ promptAnswer: a.value }); });
}

function opsTable(ops: Array<{ n: string; type: string; code: string; name: string; costMat: string; costOp: string; cost: string; selected: boolean }> | null): string {
  if (!ops) return "Operatsiyalar jadvali topilmadi (loyiha ochiqmi?)";
  return table(["№", "Тип", "Код/Изделие", "Наименование", "Ст. м-ла", "Ст. оп-и", "Ст-ть", "tanl."], ops.map((o) => [o.n, o.type, o.code, o.name, o.costMat, o.costOp, o.cost, o.selected ? "✓" : ""])) + `\n${ops.length} operatsiya`;
}
