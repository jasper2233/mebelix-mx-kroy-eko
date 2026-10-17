/**
 * Tutun testi: server stdio orqali ishga tushiriladi, MCP mijozi bilan vositalar chaqiriladi.
 *   MX_URL — ishlayotgan MebeliX Kroy (standart http://127.0.0.1:8000); server yo'q bo'lsa mx_* testlari o'tkazib yuboriladi.
 *   MX_TEST_PROJECT_FILE — `.project` fayli (ixtiyoriy): compare_project tekshiruvi.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { decodeXmlBytes, parseProjectXml } from "../src/compare/projectfile.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const MX_URL = process.env.MX_URL || "http://127.0.0.1:8000";

async function mxAlive(): Promise<boolean> {
  try { const r = await fetch(MX_URL + "/api/health", { signal: AbortSignal.timeout(3000) }); return r.ok; } catch { return false; }
}

async function connect(): Promise<Client> {
  // `node --import tsx src/server.ts` — yo'lda bo'sh joy bo'lsa ham ishlaydi (cmd /c orqali .cmd chaqirish buziladi)
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: ["--import", "tsx", path.join(here, "..", "src", "server.ts")],
    cwd: path.join(here, ".."),
    env: { ...process.env, MX_URL, GIBLAB_MODE: "off" } as Record<string, string>,
    stderr: "pipe",
  });
  transport.stderr?.on("data", (d: Buffer) => process.stderr.write("[server] " + d.toString()));
  const client = new Client({ name: "smoke", version: "0" });
  await client.connect(transport);
  return client;
}

const textOf = (r: unknown): string => ((r as { content: Array<{ type: string; text?: string }> }).content || []).map((c) => c.text || "").join("\n");

test("projectfile parser: operations, saved stats, entities", () => {
  const xml = `<?xml version="1.0"?><project name="T &amp; 1" version="23051701" currency="UZS">
  <good typeId="product" id="1" name="P"><part id="10" count="2" dl="500" dw="300"/><part id="11" count="1" dl="700" dw="100"/></good>
  <good typeId="tool.cutting" id="2" swSawthick="3" swMaxturns="4" swMinPruning="5"/>
  <good typeId="sheet" id="3" name="LDSP &quot;A&quot;" code="C1" l="2750" w="1830" t="16"><part count="10000" id="30" l="2750" w="1830" usedCount="1"/><part l="1000" w="500" count="1" waste="true" business="true" id="31"/></good>
  <operation typeId="CS" id="5" tool1="2" cTrimL="2" cTrimW="2" csTexture="true" cPartCount="3" cMaterialCount="1" cFilling="0.5123" cBusinessWasteAmount="0.5" cTrimLength="12.5" cTrimCount="7" l="2750" w="1830" t="16"><material id="3" used="base"/><part id="10"/><part id="11"/></operation>
  <operation typeId="EL" id="6" typeName="Кромка"/>
  <operation typeId="XNC" id="7" code="X1" program="&lt;program/&gt;"><part id="10"/></operation>
  </project>`;
  const pf = parseProjectXml(xml, "t.project");
  assert.equal(pf.name, "T & 1");
  assert.deepEqual(pf.counts, { CS: 1, EL: 1, XNC: 1 });
  assert.equal(pf.products, 1);
  assert.equal(pf.partsTotal, 3);
  const cs = pf.operations[0];
  assert.equal(cs.type, "CS");
  assert.equal(cs.name, 'LDSP "A"');
  assert.equal(cs.partsRefs, 2);
  assert.equal(cs.partsQty, 3);
  assert.deepEqual(cs.sheet, { length: 2750, width: 1830, thickness: 16 });
  assert.equal(cs.stock.length, 2);
  assert.equal(cs.stock[1].waste, true);
  assert.equal(cs.cut.kerf, 3);
  assert.equal(cs.cut.maxTurns, 4);
  assert.equal(cs.saved?.sheets, 1);
  assert.equal(cs.saved?.fill, 51.23);
  assert.equal(cs.saved?.parts, 3);
  assert.equal(cs.saved?.cutLengthM, 12.5);
  assert.equal(pf.operations[2].partsRefs, 1);
  assert.equal(pf.operations[2].saved, null);
});

test("projectfile decoder: windows-1251 declaration (old files) and utf-8", () => {
  // «Гранит» windows-1251 baytlari: C3 F0 E0 ED E8 F2
  const head = Buffer.from(`<?xml version="1.0" encoding="windows-1251"?><project name="`, "latin1");
  const body = Buffer.from([0xc3, 0xf0, 0xe0, 0xed, 0xe8, 0xf2]);
  const tail = Buffer.from(`"></project>`, "latin1");
  assert.equal(parseProjectXml(decodeXmlBytes(Buffer.concat([head, body, tail]))).name, "Гранит");
  assert.equal(parseProjectXml(decodeXmlBytes(Buffer.from(`<?xml version="1.0" encoding="UTF-8"?><project name="Гранит"></project>`, "utf8"))).name, "Гранит");
  assert.equal(parseProjectXml(decodeXmlBytes(Buffer.from(`<project name="Гранит"></project>`, "utf8"))).name, "Гранит");
});

test("server: tools list and mx_* round trip", async (t) => {
  const client = await connect();
  try {
    const tools = await client.listTools();
    const names = tools.tools.map((x) => x.name);
    for (const n of ["mx_health", "mx_projects", "mx_project", "mx_cut", "mx_result", "mx_warehouse", "mx_catalog", "mx_postprocess", "mx_mes_export", "compare_project", "giblab_status", "giblab_pagelib"])
      assert.ok(names.includes(n), `vosita yo'q: ${n}`);
    assert.ok(names.length >= 60, `vositalar kam: ${names.length}`);
    const lib = await client.callTool({ name: "giblab_pagelib", arguments: {} });
    assert.match(textOf(lib), /window\.__gl/);
    const off = await client.callTool({ name: "giblab_status", arguments: {} });
    assert.ok(off.isError, "GIBLAB_MODE=off da xato qaytishi kerak");
    assert.match(textOf(off), /GIBLAB_MODE/);

    if (!(await mxAlive())) { t.diagnostic(`MebeliX Kroy ${MX_URL} ishlamayapti — mx_* testlari o'tkazib yuborildi`); return; }
    const h = await client.callTool({ name: "mx_health", arguments: {} });
    assert.match(textOf(h), /MebeliX Kroy/);
    const created = await client.callTool({ name: "mx_project_create", arguments: { name: "MCP smoke" } });
    const pid = (JSON.parse(textOf(created)) as { id: string }).id;
    assert.ok(pid);
    try {
      await client.callTool({ name: "mx_operation_add", arguments: { pid, type: "CS", name: "LDSP 16" } });
      const summ = textOf(await client.callTool({ name: "mx_project", arguments: { pid } }));
      assert.match(summ, /MCP smoke/);
      const opId = /\|\s*CS\s*\|[^\n]*\|\s*([0-9a-f]{12})\s*\|\s*$/m.exec(summ)?.[1];
      assert.ok(opId, "CS operatsiya id topilmadi: " + summ);
      const added = textOf(await client.callTool({ name: "mx_parts_add", arguments: { pid, oid: opId, parts: [{ name: "A", length: 600, width: 400, qty: 3 }, { name: "B", length: 900, width: 300, qty: 2, grain: true }] } }));
      assert.match(added, /Σ 5/);
      const sheets = textOf(await client.callTool({ name: "mx_sheets", arguments: { pid, oid: opId } }));
      assert.match(sheets, /2750/);
      const cut = textOf(await client.callTool({ name: "mx_cut", arguments: { pid, quality: "fast" } }));
      assert.match(cut, /\|\s*1\s*\|/, "1 list kutildi: " + cut);
      const res = JSON.parse(textOf(await client.callTool({ name: "mx_result", arguments: { pid, oid: opId } })));
      assert.equal(res.sheets, 1);
      assert.equal(res.parts_placed, 5);
      const maps = textOf(await client.callTool({ name: "mx_result", arguments: { pid, oid: opId, detail: "maps" } }));
      assert.match(maps, /2750×1830/);
      const rem = JSON.parse(textOf(await client.callTool({ name: "mx_remnants_proposed", arguments: { pid, oid: opId } })));
      assert.ok(rem !== null);
      const mes = JSON.parse(textOf(await client.callTool({ name: "mx_mes_export", arguments: { pid } })));
      assert.ok(mes && typeof mes === "object");
      const pp = JSON.parse(textOf(await client.callTool({ name: "mx_postprocessors", arguments: {} })));
      assert.ok(Array.isArray(pp.native) && pp.native.length > 20, "o'rnatilgan formatlar");
      const csv = JSON.parse(textOf(await client.callTool({ name: "mx_postprocess", arguments: { pid, oid: opId, key: "csv" } })));
      assert.ok(csv.saved && csv.bytes > 10);
      const exp = JSON.parse(textOf(await client.callTool({ name: "mx_project_export", arguments: { pid, format: "project" } })));
      assert.ok(exp.saved.endsWith(".project"));
      const info = textOf(await client.callTool({ name: "compare_file_info", arguments: { path: exp.saved } }));
      assert.match(info, /CS/);
      const bad = await client.callTool({ name: "mx_project", arguments: { pid: "no-such-id" } });
      assert.ok(bad.isError);
      assert.match(textOf(bad), /404/);
    } finally {
      await client.callTool({ name: "mx_project_delete", arguments: { pid, confirm: true } });
    }
    const file = process.env.MX_TEST_PROJECT_FILE;
    if (file) {
      const cmp = textOf(await client.callTool({ name: "compare_project", arguments: { path: file, quality: "fast", keep: false } }));
      assert.match(cmp, /listlar \d+ vs avvalgi/);
      t.diagnostic(cmp.split("\n")[0]);
    }
  } finally {
    await client.close();
  }
});
