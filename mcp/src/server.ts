#!/usr/bin/env node
/**
 * MebeliX Kroy MCP serveri (stdio).
 *   mx_*       — MebeliX Kroy REST (loyihalar, kroy, qoldiqlar ombori, katalog, hisobot, postprotsessor, MES)
 *   giblab_*   — onlayn tizim (giblab.com) brauzer orqali: o'qish (ro'yxat, operatsiyalar, ko'rsatkichlar, jadvallar),
 *                yozish amallari faqat GIBLAB_ALLOW_WRITE=1 va ish papkasi ichida
 *   compare_*  — MX ↔ fayl (saqlangan natija) / MX ↔ onlayn solishtirish
 * Muhit: MX_URL, MX_TOKEN, MX_OUT_DIR, MX_QUALITY, GIBLAB_MODE (off|cdp|profile), GIBLAB_CDP_URL, GIBLAB_PROFILE_DIR,
 *        GIBLAB_ALLOW_WRITE, GIBLAB_WORK_FOLDER, GIBLAB_HEADLESS.
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { loadConfig } from "./config.js";
import { MxClient } from "./mx/client.js";
import { registerMxTools } from "./mx/tools.js";
import { registerCompareTools } from "./compare/tools.js";
import { GiblabDriver } from "./giblab/driver.js";
import { registerGiblabTools } from "./giblab/tools.js";

export function buildServer(env: NodeJS.ProcessEnv = process.env): { server: McpServer; close: () => Promise<void> } {
  const cfg = loadConfig(env);
  const mx = new MxClient({ baseUrl: cfg.mxUrl, token: cfg.mxToken });
  const server = new McpServer({ name: "mxkroy-mcp", version: "0.1.0" }, {
    instructions: [
      "MebeliX Kroy — listli materiallar kroy dasturi (korxonaning o'z tizimi; qoldiqlar ombori, material katalogi, MES).",
      "mx_* vositalari MebeliX Kroy serveriga (" + cfg.mxUrl + ") murojaat qiladi. Loyihani raqami (masalan 1000009) yoki id si bilan bering.",
      "Ish oqimi: mx_projects → mx_project (op id lar) → mx_parts / mx_sheets → mx_cut → mx_result → mx_report / mx_postprocess / mx_mes_export.",
      "compare_project — `.project` faylini import qilib kesadi va fayldagi avvalgi tizim natijasi bilan solishtiradi (listlar, F, деловой, kesish).",
      "giblab_* — onlayn tizim brauzer orqali (GIBLAB_MODE=cdp|profile). Standart holatda faqat o'qish; yozish (import, kroy, o'chirish, postprotsessor) GIBLAB_ALLOW_WRITE=1 talab qiladi va onlayn loyihani darhol saqlaydi — haqiqiy loyihalarda ishlatmang.",
    ].join("\n"),
  });
  let driver: GiblabDriver | null = null;
  const giblab = async () => {
    if (cfg.giblabMode === "off") throw new Error("Onlayn tizim o'chiq: GIBLAB_MODE=cdp (Chrome --remote-debugging-port=9222) yoki GIBLAB_MODE=profile bering");
    if (!driver) driver = new GiblabDriver(cfg);
    await driver.ensure();
    return driver;
  };
  registerMxTools(server, cfg, mx);
  registerGiblabTools(server, cfg, giblab);
  registerCompareTools(server, cfg, mx, giblab);
  return { server, close: async () => { await driver?.close(); await server.close(); } };
}

async function main() {
  const { server, close } = buildServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  const stop = () => { close().finally(() => process.exit(0)); };
  process.on("SIGINT", stop);
  process.on("SIGTERM", stop);
}

const isMain = process.argv[1] && /server\.(ts|js)$/.test(process.argv[1]);
if (isMain) main().catch((e) => { console.error(e); process.exit(1); });
