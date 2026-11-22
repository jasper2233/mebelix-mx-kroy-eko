// Bazis eksport skriptini (yangi js / GibLabExport 2.00 MX) Bazis ICHIDA oynasiz ishga tushirish — MCP ko'prigi orqali.
//
//   node tools/bazis/bazis_eksport.mjs <model.b3d> <natija.project> [skript.js] [sozlamalar.prop]
//
// Talab: Bazis ochiq va unda «Скрипты → MCP_bridge» ishga tushirilgan (port va kalit ~/.bazis-mcp/bridge.json da).
// Skript matni o'zgartirilmaydi — faqat Bazis muloqotlari almashtiriladi: sozlamalar paneli o'rniga .prop qiymatlari,
// «Сохранить как» o'rniga berilgan fayl, alert/confirm — jurnalga. Natija: eksport qilingan .project va jurnal (JSON).
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const [model, out, script = "D:/yangi js/yangi js.js", prop = "D:/yangi js/GibLabExport200.prop"] = process.argv.slice(2);
if (!model || !out) {
  console.error("ishlatish: node bazis_eksport.mjs <model.b3d> <natija.project> [skript.js] [sozlamalar.prop]");
  process.exit(2);
}

function propValues(file) {
  // <Item Name="..."> [<Value>..</Value>] — ichma-ich guruhlar; qiymati yo'q element — false / 0 (Bazis shunday saqlaydi)
  const xml = fs.readFileSync(file, "utf8").replace(/^\uFEFF/, "");
  const dec = (s) => s.replace(/&quot;/g, '"').replace(/&gt;/g, ">").replace(/&lt;/g, "<").replace(/&amp;/g, "&");
  const map = {};
  const re = /<Item Name="([^"]*)"\s*(\/>|>)/g;
  let m;
  while ((m = re.exec(xml))) {
    const name = dec(m[1]);
    if (m[2] === "/>") { map[name] = null; continue; }
    // shu elementning o'z <Value> si: ichki <Items> dan keyin keladi — mos yopilish tegigacha qidiriladi
    let depth = 1, i = re.lastIndex, val = null;
    const tag = /<(\/?)Item\b[^>]*?(\/?)>|<Value>([\s\S]*?)<\/Value>/g;
    tag.lastIndex = i;
    let t;
    while ((t = tag.exec(xml))) {
      if (t[3] !== undefined) { if (depth === 1) val = dec(t[3]); continue; }
      if (t[1] === "/") { depth--; if (depth === 0) break; } else if (t[2] !== "/") depth++;
    }
    map[name] = val;
  }
  return map;
}

const cfg = JSON.parse(fs.readFileSync(path.join(os.homedir(), ".bazis-mcp", "bridge.json"), "utf8"));
async function rpc(command, params) {
  const r = await fetch(`http://127.0.0.1:${cfg.port}/rpc`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${cfg.token}` },
    body: JSON.stringify({ command, params }),
  });
  return r.json();
}

const values = propValues(prop);
const code = `
var MXLOG = [];
var alert = function (s) { MXLOG.push('ALERT: ' + String(s)); };
var confirm = function (s) { MXLOG.push('CONFIRM: ' + String(s)); return true; };
var MX_OUT = ${JSON.stringify(out.replace(/\\/g, "/"))};
var MX_VALUES = ${JSON.stringify(values)};
var MX_ITEMS = [];
function MXNode(name) {
  var n = { Value: false, Name: name };
  ['NewButton', 'NewNumber', 'NewBool', 'NewGroup', 'NewString', 'NewCombo'].forEach(function (k) {
    n[k] = function (nm) { var c = MXNode(nm); c.kind = k; MX_ITEMS.push(c); return c; };
  });
  n.Load = function () {}; n.Save = function () {};
  return n;
}
var MXP = MXNode('root');
var ok = Action.LoadModel(${JSON.stringify(model.replace(/\\/g, "/"))});
if (ok === false) throw new Error('LoadModel false');
var MX_SRC = require('fs').readFileSync(${JSON.stringify(script.replace(/\\/g, "/"))}, 'utf8').replace(/^\\uFEFF/, '');
function mxRep(a, b) { if (MX_SRC.indexOf(a) < 0) throw new Error('skriptda topilmadi: ' + a); MX_SRC = MX_SRC.split(a).join(b); }
mxRep('Prop = Action.Properties;', 'Prop = MXP;');
mxRep('Action.Properties.Load(FileOptions);', '');
mxRep('Action.Continue();', '');
mxRep("fileName = system.askFileNameSave('project');", 'fileName = MX_OUT;');
mxRep('return Action.Control.Owner.Controls[0].Article.Name;', ${JSON.stringify(
    `try { return Action.Control.Owner.Controls[0].Article.Name; } catch (e) { return ${JSON.stringify(path.basename(model, ".b3d"))}; }`)});
eval(MX_SRC);
var applied = 0, missing = [];
MX_ITEMS.forEach(function (it) {
  if (!MX_VALUES.hasOwnProperty(it.Name)) { missing.push(it.Name); return; }
  var v = MX_VALUES[it.Name];
  if (it.kind === 'NewBool') it.Value = (v === 'Y');
  else if (it.kind === 'NewNumber') it.Value = (v === null || v === '') ? 0 : Number(String(v).replace(',', '.'));
  else if (it.kind !== 'NewGroup' && it.kind !== 'NewButton') it.Value = v === null ? '' : v;
  applied++;
});
var t0 = Date.now();
exportGibLab();
({ out: MX_OUT, exists: require('fs').existsSync(MX_OUT), size: require('fs').existsSync(MX_OUT) ? require('fs').statSync(MX_OUT).size : 0,
   ms: Date.now() - t0, applied: applied, missing: missing, log: MXLOG,
   mx: { figure: typeof cbMxFigure !== 'undefined' && cbMxFigure.Value, noSmCht: typeof cbMxNoSmCht !== 'undefined' && cbMxNoSmCht.Value } })
`;
const res = await rpc("run_script", { code, commit: false });
console.log(JSON.stringify(res, null, 2));
process.exit(res.ok ? 0 : 1);
