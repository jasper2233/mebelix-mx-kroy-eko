// Bazis MCP ko'prigiga bitta buyruq: node bazis_rpc.mjs <buyruq> [params.json | -] — natija JSON (kalit chiqarilmaydi)
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const [command, arg] = process.argv.slice(2);
const cfg = JSON.parse(fs.readFileSync(path.join(os.homedir(), ".bazis-mcp", "bridge.json"), "utf8"));
let params = {};
if (arg === "-") params = JSON.parse(fs.readFileSync(0, "utf8"));
else if (arg) params = JSON.parse(fs.readFileSync(arg, "utf8"));
const r = await fetch(`http://127.0.0.1:${cfg.port}/rpc`, {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${cfg.token}` },
  body: JSON.stringify({ command, params }),
});
console.log(JSON.stringify(await r.json(), null, 2));
