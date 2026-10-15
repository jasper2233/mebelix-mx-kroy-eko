// Buyruq satri: `.project` faylini MebeliX Kroy ga import qilib kesadi va fayldagi avvalgi tizim natijasi bilan solishtiradi.
//   node scripts/compare-file.mjs <fayl.project> [fast|normal|max] [--keep]
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const [file, quality = "normal", ...rest] = process.argv.slice(2);
if (!file) { console.error("foydalanish: node scripts/compare-file.mjs <fayl.project> [fast|normal|max] [--keep]"); process.exit(2); }
const transport = new StdioClientTransport({ command: process.execPath, args: [path.join(here, "..", "dist", "server.js")],
  env: { ...process.env, GIBLAB_MODE: "off", MX_URL: process.env.MX_URL || "http://127.0.0.1:8000" } });
const client = new Client({ name: "compare-file", version: "0" });
await client.connect(transport);
try {
  const r = await client.callTool({ name: "compare_project", arguments: { path: file, quality, keep: rest.includes("--keep") } }, undefined, { timeout: 1_800_000 });
  console.log(r.content.map((x) => x.text).join("\n"));
  if (r.isError) process.exitCode = 1;
} finally {
  await client.close();
}
