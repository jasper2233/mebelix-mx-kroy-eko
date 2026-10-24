// Onlayn tizim (GibLab online) bilan solishtiruv uchun buyruq qatori: alohida Chrome nusxasiga (start_chrome.ps1, port 9222)
// MCP drayveri (mcp/dist/giblab/driver.js, GIBLAB_MODE=cdp) orqali ulanadi. Brauzerning tizim oynalari (alert / prompt / confirm)
// drayverda avtomatik javoblanadi — sahifa qotmaydi. Har chaqiruv ulanadi → bajaradi → uziladi (Chrome ochiq qoladi).
//
//   node tools/giblab/gl.mjs status
//   node tools/giblab/gl.mjs shot <out.png>
//   node tools/giblab/gl.mjs projects "<papka>"                 (masalan "test uchun")
//   node tools/giblab/gl.mjs open "<papka>" "<loyiha>"
//   node tools/giblab/gl.mjs tab "Раскрой"
//   node tools/giblab/gl.mjs click "<matn>"   |  clickxy <x> <y> [dbl]  |  key <Key>
//   node tools/giblab/gl.mjs eval "<js>"
//   node tools/giblab/gl.mjs run <skript.mjs>                   (export default async ({ page, drv }) => ...)
//
// Yozuvchi amallar (kroy, import, o'chirish) — faqat GIBLAB_ALLOW_WRITE=1 va GIBLAB_WORK_FOLDER ichida (drayver tekshiradi).
// Qotib qolsa: powershell -File tools/giblab/start_chrome.ps1 -Restart
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const mcp = path.resolve(here, "../../mcp");
const require = createRequire(path.join(mcp, "package.json"));
process.env.GIBLAB_MODE = "cdp";
process.env.GIBLAB_WORK_FOLDER ||= "test uchun";
const { loadConfig } = await import(pathToFileURL(path.join(mcp, "dist/config.js")).href);
const { GiblabDriver } = await import(pathToFileURL(path.join(mcp, "dist/giblab/driver.js")).href);
void require;

const [cmd, ...args] = process.argv.slice(2);
const drv = new GiblabDriver(loadConfig(process.env));
const out = (v) => console.log(typeof v === "string" ? v : JSON.stringify(v, null, 1));
const timeout = (ms) => new Promise((_, rej) => setTimeout(() => rej(new Error(`javob yo'q (${ms / 1000} s) — sahifa qotgan bo'lishi mumkin: start_chrome.ps1 -Restart`)), ms));

async function main() {
  const page = await drv.ensure();
  switch (cmd) {
    case "status": return out(await drv.status());
    case "shot": return out(await drv.screenshot(args[0] || path.join(process.cwd(), "gl.png")));
    case "projects": return out(args[0] ? await drv.openFolderPath(args[0] === "root" ? "/" : args[0]) : await drv.projects());
    case "open": if (args[0]) await drv.openFolderPath(args[0]); return out(await drv.openProject(args[1]));
    case "tab": return out(await drv.tab(args[0]));
    case "click": return out(await drv.clickText(args[0], args[1] === "partial"));
    case "clickxy": await drv.clickXY(Number(args[0]), Number(args[1]), { dbl: args[2] === "dbl" }); return out("ok");
    case "key": await drv.pressKey(args[0]); return out("ok");
    case "eval": return out(await drv.evaluate(args[0]));
    case "run": { const mod = await import(pathToFileURL(path.resolve(args[0])).href); return out(await mod.default({ page, drv, args: args.slice(1) })); }
    default: throw new Error(`noma'lum buyruq: ${cmd}`);
  }
}

try {
  await Promise.race([main(), timeout(Number(process.env.GL_TIMEOUT_MS || 120_000))]);
  process.exit(0);
} catch (e) {
  console.error(String(e?.message || e));
  process.exit(1);
}
