/**
 * Onlayn tizim (giblab.com) brauzer drayveri — Playwright.
 *  - cdp:     foydalanuvchining ishlayotgan Chrome iga ulanadi (chrome.exe --remote-debugging-port=9222) — uning kirgan sessiyasi ishlatiladi
 *  - profile: o'z doimiy profili bilan Chrome ochadi (birinchi marta foydalanuvchi o'zi kiradi; parol so'ralmaydi, saqlanmaydi)
 * Faqat DOM o'qiladi va sichqoncha/klaviatura hodisalari yuboriladi; tizim kodi/resurslari ko'chirilmaydi.
 * Yozish amallari (import, kroy, o'chirish, postprotsessor) — `cfg.giblabAllowWrite` va ish papkasi tekshiruvi bilan.
 */
import fs from "node:fs/promises";
import path from "node:path";
import { chromium, type Browser, type BrowserContext, type Dialog, type Page } from "playwright";
import type { Config } from "../config.js";
import { PAGELIB } from "./pagelib.js";
import { ensureDir, safeName } from "../util.js";

export interface GlRow { i: number; cells: string[]; r: { x: number; y: number; w: number; h: number; cx: number; cy: number } }
export interface GlProjectRow { i: number; n: string; id: string; owner: string; status: string; date: string; cost: string; name: string; kind: "project" | "folder"; r: GlRow["r"] }
export interface GlOperation { i: number; n: string; type: string; code: string; name: string; costMat: string; costOp: string; cost: string; r: GlRow["r"]; selected: boolean }
export interface CutStats { name: string; type: string; sheets: number | null; fill: number | null; cutLengthM: number | null; business: number | null; maps: number | null; raw: string[] }

export class GiblabDriver {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private page: Page | null = null;
  readonly dialogLog: Array<{ type: string; message: string; action: string; at: string }> = [];
  /** Brauzerning tizim oynalariga javob siyosati: prompt → standart qiymat (8 belgili dastur nomi), alert/confirm → OK. */
  promptAnswer = "MXKROY01";

  constructor(private cfg: Config) {}

  get connected(): boolean { return !!this.page && !this.page.isClosed(); }

  async ensure(): Promise<Page> {
    if (this.connected) return this.page!;
    if (this.cfg.giblabMode === "cdp") {
      this.browser = await chromium.connectOverCDP(this.cfg.giblabCdpUrl);
      const ctx = this.browser.contexts()[0] ?? (await this.browser.newContext());
      this.context = ctx;
      const existing = ctx.pages().find((p) => p.url().includes("giblab.com"));
      this.page = existing ?? (await ctx.newPage());
      if (!existing) await this.page.goto(this.cfg.giblabUrl);
    } else if (this.cfg.giblabMode === "profile") {
      await ensureDir(this.cfg.giblabProfileDir);
      this.context = await chromium.launchPersistentContext(this.cfg.giblabProfileDir, { channel: "chrome", headless: this.cfg.giblabHeadless, viewport: { width: 1400, height: 900 }, acceptDownloads: true });
      this.page = this.context.pages()[0] ?? (await this.context.newPage());
      if (!this.page.url().includes("giblab.com")) await this.page.goto(this.cfg.giblabUrl);
    } else {
      throw new Error("GIBLAB_MODE=off");
    }
    this.page.setDefaultTimeout(20_000);
    this.page.on("dialog", (d) => this.onDialog(d));
    this.humanize(this.page);
    await this.settle();
    return this.page;
  }

  /** Sahifa (GWT ilovasi) yuklanib bo'lishini kutish: tarmoq tinchiydi va ko'rinadigan yozuvlar paydo bo'ladi (≤ 20 s). */
  async settle(maxMs = 20_000): Promise<void> {
    const p = this.page!;
    await p.waitForLoadState("networkidle", { timeout: maxMs }).catch(() => {});
    const t0 = Date.now();
    while (Date.now() - t0 < maxMs) {
      await p.evaluate(PAGELIB).catch(() => {});
      const n = await p.evaluate("(window.__gl ? window.__gl.inventory().length : 0)").catch(() => 0) as number;
      if (n > 3) return;
      await p.waitForTimeout(500);
    }
  }

  /** Odam tezligi (foydalanuvchi talabi, 2026-10-21): tez ketma-ket bosishlarda onlayn tizim qulflanadi / qotadi.
   *  Har sichqoncha bosishi, tugma bosishi va matn yozishdan oldin `giblabPaceMs` tanaffus, bosish o'zi ham 60–90 ms davom etadi;
   *  kursor harakati bir necha qadamda. Qadam skriptlari `page.mouse` / `page.keyboard` ni to'g'ridan-to'g'ri chaqirgani uchun
   *  shu yerda — sahifa obyektida — o'raladi. */
  private humanize(p: Page): void {
    const pace = this.cfg.giblabPaceMs;
    if (!pace || (p as unknown as { __mxPaced?: boolean }).__mxPaced) return;
    (p as unknown as { __mxPaced?: boolean }).__mxPaced = true;
    const nap = (k = 1) => new Promise((r) => setTimeout(r, Math.round(pace * k * (0.8 + Math.random() * 0.4))));
    const m = p.mouse, kb = p.keyboard;
    const click = m.click.bind(m), dbl = m.dblclick.bind(m), down = m.down.bind(m), up = m.up.bind(m), move = m.move.bind(m), wheel = m.wheel.bind(m);
    const press = kb.press.bind(kb), kdown = kb.down.bind(kb), kup = kb.up.bind(kb), type = kb.type.bind(kb), ins = kb.insertText.bind(kb);
    m.click = async (x, y, o = {}) => { await nap(); await move(x, y, { steps: 4 }); await nap(0.3); return click(x, y, { delay: 70, ...o }); };
    m.dblclick = async (x, y, o = {}) => { await nap(); await move(x, y, { steps: 4 }); await nap(0.3); return dbl(x, y, { delay: 60, ...o }); };
    m.down = async (o) => { await nap(0.5); return down(o); };
    m.up = async (o) => { await nap(0.3); return up(o); };
    m.move = async (x, y, o = {}) => move(x, y, { steps: 3, ...o });
    m.wheel = async (dx, dy) => { await nap(0.5); return wheel(dx, dy); };
    kb.press = async (k, o = {}) => { await nap(); return press(k, { delay: 60, ...o }); };
    kb.down = async (k) => { await nap(0.5); return kdown(k); };
    kb.up = async (k) => { await nap(0.3); return kup(k); };
    kb.type = async (t, o = {}) => { await nap(); return type(t, { delay: 45, ...o }); };
    kb.insertText = async (t) => { await nap(); return ins(t); };
  }

  private onDialog(d: Dialog): void {
    const msg = d.message();
    let action = "accept";
    if (d.type() === "prompt") { void d.accept(d.defaultValue() || this.promptAnswer); action = `accept(${d.defaultValue() || this.promptAnswer})`; }
    else { void d.accept(); }
    this.dialogLog.push({ type: d.type(), message: msg, action, at: new Date().toISOString() });
  }

  async close(): Promise<void> {
    try {
      if (this.cfg.giblabMode === "profile") await this.context?.close();
      else await this.browser?.close();            // CDP: faqat ulanish yopiladi, Chrome qoladi
    } catch { /* ignore */ }
    this.page = null; this.context = null; this.browser = null;
  }

  /** Sahifa kutubxonasini kiritish (har sahifa yuklanganda qayta). */
  async lib(): Promise<void> {
    const p = await this.ensure();
    await p.evaluate(PAGELIB);
  }

  async gl<T = unknown>(expr: string): Promise<T> {
    const p = await this.ensure();
    await this.lib();
    return (await p.evaluate(`(() => { const r = window.__gl.${expr}; return JSON.parse(JSON.stringify(r === undefined ? null : r)); })()`)) as T;
  }

  async wait(ms: number): Promise<void> { await (await this.ensure()).waitForTimeout(ms); }

  /** Haqiqiy sichqoncha bosishi (GWT ba'zi joylarda sintetik hodisani qabul qilmaydi). */
  async clickXY(x: number, y: number, opts: { dbl?: boolean } = {}): Promise<void> {
    const p = await this.ensure();
    if (opts.dbl) await p.mouse.dblclick(x, y); else await p.mouse.click(x, y);
  }

  async clickText(text: string, partial = false): Promise<boolean> {
    const hits = await this.gl<Array<{ r: GlRow["r"] }>>(`find(${JSON.stringify(text)}, ${partial})`);
    if (!hits.length) return false;
    await this.clickXY(hits[0].r.cx, hits[0].r.cy);
    return true;
  }

  // ───── holat ─────
  async status(): Promise<{ mode: string; url: string; loggedIn: boolean; user: string; project: string | null; selectedOp: string | null; dialogs: unknown[]; nativeDialogs: number }> {
    const p = await this.ensure();
    const txt = await this.gl<string>("text()");
    const m = /(\d{4,})\s+(\S+@\S+)/.exec(txt);
    const h = await this.gl<{ name: string; selectedOp: string }>("header()");
    const onProject = p.url().includes("#project") && !p.url().includes("#projects");
    return { mode: this.cfg.giblabMode, url: p.url(), loggedIn: !!m, user: m ? `${m[1]} ${m[2]}` : "", project: onProject ? h.name : null, selectedOp: onProject ? h.selectedOp || null : null, dialogs: await this.gl("dialogs()"), nativeDialogs: this.dialogLog.length };
  }

  // ───── loyihalar ro'yxati ─────
  async gotoProjects(): Promise<void> {
    const p = await this.ensure();
    if (!p.url().includes("#projects")) { await p.goto(this.cfg.giblabUrl.replace(/\/$/, "") + "/#projects"); await this.wait(1200); await this.lib(); }
  }

  async projects(): Promise<{ path: string; rows: GlProjectRow[] } | null> {
    return this.gl<{ path: string; rows: GlProjectRow[] } | null>("projects()");
  }

  /** Papkaga kirish: nom bo'yicha qatorni ikki marta bosish. `/` — ildiz. */
  async openFolderPath(folderPath: string): Promise<{ path: string; rows: GlProjectRow[] } | null> {
    await this.gotoProjects();
    const parts = folderPath.split("/").map((s) => s.trim()).filter(Boolean);
    if (!parts.length || folderPath.trim() === "/") {
      // ildizga: «uy» tugmasi (yuqori chap, ikkinchi belgi) — matnsiz; birinchi qatorda «Dropbox» ko'rinsa — ildiz
      // ildizga: ro'yxat ustidagi ikkinchi belgi («Домой»; birinchisi — «yuqori papka»); ro'yxat o'zgarguncha kutiladi
      const before = JSON.stringify((await this.projects())?.rows.map((r) => r.name));
      const home = await this.evaluate(`(() => { const im = [...document.querySelectorAll("img")].filter((e) => { const r = e.getBoundingClientRect();
        return r.y >= 0 && r.y < 45 && r.x > 215 && r.x < 340 && r.width >= 20; }).sort((a, b) => a.getBoundingClientRect().x - b.getBoundingClientRect().x);
        const e = im[1] || im[0]; if (!e) return null; const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; })()`) as { x: number; y: number } | null;
      if (home) await this.clickXY(home.x, home.y);
      for (let k = 0; k < 30; k++) {
        await this.wait(500);
        const now = await this.projects();
        if (now && now.rows.length && (JSON.stringify(now.rows.map((r) => r.name)) !== before || now.rows.some((r) => r.name === "Dropbox"))) break;
      }
      return this.projects();
    }
    for (const name of parts) {
      const list = await this.projects();
      const row = list?.rows.find((r) => r.kind === "folder" && r.name.trim() === name);
      if (!row) throw new Error(`Papka topilmadi: ${name} (bor: ${list?.rows.filter((r) => r.kind === "folder").map((r) => r.name).join(", ")})`);
      const before = JSON.stringify(list?.rows.map((r) => r.name));
      const vis = (await this.revealRow(row.name)) ?? row;
      await this.clickXY(vis.r.x + Math.min(600, vis.r.w / 2), vis.r.cy);
      await this.wait(400);
      await this.clickText("Открыть");
      // papka ro'yxati serverdan keladi — o'zgarguncha kutiladi (xodimlar papkalari ~2 daqiqa yuklanadi; ≤ 4 daqiqa)
      for (let k = 0; k < 480; k++) {
        await this.wait(500);
        const now = await this.projects();
        if (now && now.rows.length && JSON.stringify(now.rows.map((r) => r.name)) !== before) break;
      }
    }
    return this.projects();
  }

  /** Ro'yxatdagi qatorni (ID yoki nom bo'yicha) ko'rinadigan joyga aylantirib, yangi koordinatasini qaytaradi. */
  async revealRow(key: string): Promise<GlProjectRow | null> {
    const js = "(() => { const want = " + JSON.stringify(key) + ";" +
      " const tr = [...document.querySelectorAll('tr')].find((r) => [...r.cells].some((c) => (c.innerText || '').trim() === want) && r.getBoundingClientRect().height > 0);" +
      " if (tr) tr.scrollIntoView({ block: 'center' }); return !!tr; })()";
    await this.evaluate(js);
    await this.wait(300);
    const l = await this.projects();
    return l?.rows.find((r) => r.id === key || r.name.trim() === key.trim()) ?? null;
  }

  async openProject(nameOrId: string): Promise<GlOperation[] | null> {
    const list = await this.projects();
    const row = list?.rows.find((r) => r.kind === "project" && (r.id === nameOrId || r.name.trim() === nameOrId.trim()));
    if (!row) throw new Error(`Loyiha topilmadi: ${nameOrId}`);
    // ikki marta bosish har doim ham ishlamaydi — qatorni ko'rinadigan joyga aylantirib tanlaymiz, keyin «Открыть»
    const vis = (await this.revealRow(row.id)) ?? row;
    await this.clickXY(vis.r.x + Math.min(600, vis.r.w / 2), vis.r.cy);
    await this.wait(400);
    await this.clickText("Открыть");
    const p = await this.ensure();
    await p.waitForURL(/#project$/, { timeout: 240_000 }).catch(() => {});
    for (let k = 0; k < 240; k++) {                   // operatsiyalar jadvali paydo bo'lguncha (katta loyiha — uzoq)
      await this.wait(500);
      const ops = await this.operations().catch(() => null);
      if (ops && ops.length) {
        const name = await this.evaluate(`[...document.querySelectorAll("input")].filter((i) => i.getBoundingClientRect().width > 0).map((i) => i.value).find((v) => v && !/^[A-Z]{3}$/.test(v) && !/\d{2}\.\d{2}\.\d{4}/.test(v)) || ""`) as string;
        if (row.name.trim() && name.trim() !== row.name.trim()) throw new Error(`Boshqa loyiha ochildi: «${name}» (kutilgan «${row.name}») — yopib qayta urinish kerak`);
        return ops;
      }
    }
    return this.operations();
  }

  async closeProject(): Promise<void> {
    await this.clickText("Закрыть проект");
    await this.wait(1000);
    await this.lib();
  }

  // ───── loyiha sahifasi ─────
  async operations(): Promise<GlOperation[] | null> { return this.gl<GlOperation[] | null>("operations()"); }

  async selectOperation(indexOrName: number | string): Promise<GlOperation> {
    const ops = (await this.operations()) || [];
    const op = typeof indexOrName === "number" ? ops.find((o) => o.n === String(indexOrName)) : ops.find((o) => o.name.trim() === String(indexOrName).trim() || o.n === String(indexOrName));
    if (!op) throw new Error(`Operatsiya topilmadi: ${indexOrName}`);
    // ko'rinadigan joyda bo'lmasa (jadvalda ~8 qator ko'rinadi) — avval aylantiriladi, keyin yangi koordinata bilan bosiladi
    const js = "(() => { const want = " + JSON.stringify(op.n) + "; const tr = [...document.querySelectorAll('tr')].find((r) => r.cells.length > 5 &&" +
      " (r.cells[0].innerText || '').trim() === want && /^(CS|CL|CN|EL|GR|XNC|SP|O|LB)$/.test((r.cells[1].innerText || '').trim()) && r.getBoundingClientRect().height > 0);" +
      " if (tr) tr.scrollIntoView({ block: 'center' }); return !!tr; })()";
    await this.evaluate(js);
    await this.wait(300);
    const fresh = ((await this.operations()) || []).find((o) => o.n === op.n) ?? op;
    await this.clickXY(fresh.r.x + Math.min(400, fresh.r.w / 2), fresh.r.cy);
    await this.wait(600);
    return op;
  }

  async tab(name: string): Promise<boolean> {
    const tabs = await this.gl<Array<{ text: string; r: GlRow["r"]; selected: boolean }>>("tabs()");
    const t = tabs.find((x) => x.text === name);
    if (!t) return false;
    await this.clickXY(t.r.cx, t.r.cy);
    await this.wait(700);
    return true;
  }

  async table(needles: string[], limit = 5000): Promise<{ header: string[]; rows: GlRow[] } | null> {
    return this.gl(`table(${JSON.stringify(needles)}, ${limit})`);
  }

  /** Tanlangan kroy operatsiyasining «Раскрой» ko'rsatkichlari (matndan). */
  async cuttingStats(): Promise<CutStats> {
    await this.tab("Раскрой");
    const h = await this.gl<{ selectedOp: string }>("header()");
    const texts = await this.gl<string[]>("cutPanel()");
    const joined = texts.join(" ¦ ");
    const num = (re: RegExp): number | null => { const m = re.exec(joined); return m ? Number(m[1].replace(",", ".")) : null; };
    const m = /^\((\w+)\)\s*(.*)$/.exec(h.selectedOp || "");
    return {
      name: m ? m[2] : h.selectedOp, type: m ? m[1] : "",
      sheets: num(/Количество листов[^\d]*(\d+)/) ?? num(/S\s*[:=]?\s*(\d+)/),
      fill: num(/F\s*[:=]?\s*([\d.,]+)\s*%/) ?? num(/Заполнение[^\d]*([\d.,]+)/),
      cutLengthM: num(/LT\s*[:=]?\s*([\d.,]+)/) ?? num(/Длина реза[^\d]*([\d.,]+)/),
      business: num(/Деловой[^\d]*([\d.,]+)/) ?? num(/деловых остатков[^\d]*([\d.,]+)/i),
      maps: num(/Количество карт[^\d]*(\d+)/),
      raw: texts.slice(0, 80),
    };
  }

  async cuttingStatsAll(): Promise<CutStats[]> {
    const ops = (await this.operations()) || [];
    const out: CutStats[] = [];
    for (const o of ops) {
      if (o.type !== "CS" && o.type !== "CL") continue;
      await this.selectOperation(o.i);
      const s = await this.cuttingStats();
      out.push({ ...s, name: o.name, type: o.type });
    }
    return out;
  }

  // ───── yozish amallari (himoyalangan) ─────
  async assertWrite(action: string): Promise<void> {
    if (!this.cfg.giblabAllowWrite) throw new Error(`«${action}» onlayn loyihani o'zgartiradi — GIBLAB_ALLOW_WRITE=1 bering (va GIBLAB_WORK_FOLDER bilan sinov papkasini cheklang)`);
    if (this.cfg.giblabWorkFolder) {
      const list = await this.projects().catch(() => null);
      const crumb = list?.path ?? "";
      const p = await this.ensure();
      if (p.url().includes("#projects") && !crumb.includes(this.cfg.giblabWorkFolder)) throw new Error(`«${action}» faqat «${this.cfg.giblabWorkFolder}» papkasida ruxsat etilgan (hozir: ${crumb || "ildiz"})`);
    }
  }

  async cut(): Promise<CutStats> {
    await this.assertWrite("Раскроить");
    await this.tab("Раскрой");
    const ok = await this.clickText("Раскроить");
    if (!ok) throw new Error("«Раскроить» topilmadi (operatsiya tanlanganmi?)");
    const p = await this.ensure();
    for (let i = 0; i < 120; i++) {            // kroy tugashini kutish (≤ 2 daqiqa): dialog yo'q va ko'rsatkichlar paydo bo'ldi
      await this.wait(1000);
      const d = await this.gl<unknown[]>("dialogs()");
      if (d.length) continue;
      const s = await this.cuttingStats();
      if (s.sheets !== null) return s;
    }
    void p;
    return this.cuttingStats();
  }

  async importProject(filePath: string): Promise<GlOperation[] | null> {
    await this.assertWrite("Импортировать");
    const p = await this.ensure();
    const [chooser] = await Promise.all([p.waitForEvent("filechooser", { timeout: 15_000 }), this.clickText("Импортировать")]);
    await chooser.setFiles(filePath);
    await p.waitForURL(/#project$/, { timeout: 60_000 }).catch(() => {});
    await this.wait(2000);
    await this.lib();
    return this.operations();
  }

  async exportProject(outDir: string): Promise<string> {
    const p = await this.ensure();
    // menyu bandi onlayn tizimda «Експортировать» (Е bilan) yozilgan — ikkala yozuv ham sinaladi
    const click = async () => (await this.clickText("Експортировать")) || (await this.clickText("Экспортировать"));
    const [dl] = await Promise.all([p.waitForEvent("download", { timeout: 60_000 }), click()]);
    await ensureDir(outDir);
    const target = path.join(outDir, safeName(dl.suggestedFilename() || "export.project"));
    await dl.saveAs(target);
    return target;
  }

  async screenshot(outPath: string): Promise<string> {
    const p = await this.ensure();
    await ensureDir(path.dirname(outPath));
    await p.screenshot({ path: outPath, fullPage: false });
    return outPath;
  }

  async inventory(outPath?: string): Promise<Array<[string, string]>> {
    const inv = await this.gl<Array<[string, string]>>("inventory()");
    if (outPath) { await ensureDir(path.dirname(outPath)); await fs.writeFile(outPath, JSON.stringify(inv), "utf8"); }
    return inv;
  }

  async evaluate(js: string): Promise<unknown> {
    const p = await this.ensure();
    return p.evaluate(js);
  }

  async pressKey(key: string): Promise<void> { await (await this.ensure()).keyboard.press(key); }
}
