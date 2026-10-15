// treeOps.ts::moveTo (sichqoncha bilan sudrab ko'chirish, W18) tekshiruvi — frontendda unit-test runner yo'q, shuning uchun
// TypeScript (devDependency) bilan faylni vaqtincha JS ga o'tkazib, tasodifiy daraxtlarda xossalarni tekshiradi.
// Ishga tushirish:  cd frontend; node scripts/check_treeops.mjs     (chiqish kodi 0 — hammasi joyida)
import { createRequire } from "node:module";
import { readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const ts = require("typescript");
const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "features", "xnc", "treeOps.ts"), "utf8");
const js = ts.transpileModule(src, { compilerOptions: { module: ts.ModuleKind.ES2022, target: ts.ScriptTarget.ES2022 } }).outputText;
const tmp = mkdtempSync(join(tmpdir(), "treeops-"));
const file = join(tmp, "treeOps.mjs");
writeFileSync(file, js);
const T = await import(pathToFileURL(file).href);

let n = 0;
const ok = (cond, msg) => { n++; if (!cond) { console.error("XATO:", msg); process.exitCode = 1; } };
const C = (cmd, name, children = []) => ({ cmd, params: { name }, comment: "", enabled: true, children });
const names = (prog) => { const o = []; const w = (l) => l.forEach((c) => { o.push(c.params.name); w(c.children); }); w(prog); return o; };
const json = (x) => JSON.stringify(x);

// ───── qo'lda ─────
const prog = [C("Var", "a"), C("If", "if1", [C("DrillFront", "d1"), C("DrillFront", "d2")]), C("Var", "b"), C("While", "w1", [C("Var", "c")])];
const at = (p) => T.getAt(prog, p)?.params.name;
// d1 ni «b» dan keyin qo'yish
let r = T.moveTo(prog, [1, 0], [2], "after");
ok(json(names(r.prog)) === json(["a", "if1", "d2", "b", "d1", "w1", "c"]) && json(r.sel) === json([3]), "d1 → b dan keyin");
// a ni if1 ning ichiga (oxiriga)
r = T.moveTo(prog, [0], [1], "inside");
ok(json(names(r.prog)) === json(["if1", "d1", "d2", "a", "b", "w1", "c"]) && json(r.sel) === json([0, 2]), "a → if1 ichiga");
// b ni w1 ning ichiga: indekslar siljishi
r = T.moveTo(prog, [2], [3], "inside");
ok(json(r.sel) === json([2, 1]) && T.getAt(r.prog, [2]).params.name === "w1" && T.getAt(r.prog, [2, 1]).params.name === "b", "b → w1 ichiga (siljish)");
// if1 (ichidagilari bilan) w1 dan keyin
r = T.moveTo(prog, [1], [3], "after");
ok(json(names(r.prog)) === json(["a", "b", "w1", "c", "if1", "d1", "d2"]) && json(r.sel) === json([3]), "if1 → w1 dan keyin");
// taqiqlar
ok(T.moveTo(prog, [1], [1, 0], "before") === null, "o'z ichiga tashlash taqiqlangan");
ok(T.moveTo(prog, [1], [1], "after") === null && T.moveTo(prog, [1], [1], "inside") === null, "o'ziga tashlash taqiqlangan");
ok(T.moveTo(prog, [0], [2], "inside") === null, "oddiy buyruq ichiga tashlab bo'lmaydi");
ok(T.moveTo(prog, [1], [2], "before") === null && T.moveTo(prog, [2], [1], "after") === null, "joyi o'zgarmasa — null");
ok(T.moveTo(prog, [1, 1], [1], "inside") === null, "allaqachon oxirgi bola — null");
ok(T.moveTo(prog, [9], [0], "before") === null && T.moveTo(prog, [0], [9], "before") === null && T.moveTo(prog, [], [0], "before") === null, "noto'g'ri yo'l");
ok(T.canDrop(prog, [0], [3], "before") === true && T.canDrop(prog, [3], [3, 0], "before") === false, "canDrop");
// kirish o'zgarmaydi
ok(json(prog) === json([C("Var", "a"), C("If", "if1", [C("DrillFront", "d1"), C("DrillFront", "d2")]), C("Var", "b"), C("While", "w1", [C("Var", "c")])]), "kirish daraxti o'zgarmagan");

// ───── tasodifiy daraxtlar (xossalar) ─────
let seed = 123456789;
const rnd = () => (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296;
const pick = (a) => a[Math.floor(rnd() * a.length)];
let id = 0;
const gen = (depth) => {
  const k = Math.floor(rnd() * 4);
  return Array.from({ length: k }, () => {
    const block = depth < 3 && rnd() < 0.5;
    const nm = `n${id++}`;
    return block ? C(pick(["If", "While", "Sub", "Else", "DoWhile"]), nm, gen(depth + 1)) : C("DrillFront", nm);
  });
};
const paths = (prog) => { const o = []; const w = (l, b) => l.forEach((c, i) => { o.push([...b, i]); w(c.children, [...b, i]); }); w(prog, []); return o; };
let moved = 0, refused = 0;
for (let it = 0; it < 4000; it++) {
  id = 0;
  const p = gen(0);
  const ps = paths(p);
  if (ps.length < 2) continue;
  const from = pick(ps), target = pick(ps), pos = pick(["before", "after", "inside"]);
  const before = json(p);
  const e = T.moveTo(p, from, target, pos);
  ok(json(p) === before, "kirish o'zgardi");
  const src = T.getAt(p, from), tgt = T.getAt(p, target);
  const forbidden = json(from) === json(target) || T.isAncestor(from, target) || (pos === "inside" && !T.isContainer(tgt));
  if (e === null) {
    refused++;
    // rad etilgan bo'lsa — taqiqlangan yoki «joyi o'zgarmaydi» bo'lishi shart (yaroqli ko'chirish rad etilmasin)
    const dpar = pos === "inside" ? target : target.slice(0, -1);
    const di = pos === "inside" ? tgt.children.length : target[target.length - 1] + (pos === "after" ? 1 : 0);
    const fi = from[from.length - 1];
    const noop = json(dpar) === json(from.slice(0, -1)) && (di === fi || di === fi + 1);
    ok(forbidden || noop, `yaroqli ko'chirish rad etildi ${json(from)} → ${json(target)} ${pos}`);
    continue;
  }
  ok(!forbidden, `taqiqlangan holat qabul qilindi ${json(from)} → ${json(target)} ${pos}`);
  moved++;
  // 1) buyruqlar to'plami o'zgarmagan (yo'qolmagan, ko'paymagan)
  ok(json([...names(e.prog)].sort()) === json([...names(p)].sort()), "to'plam o'zgardi");
  // 2) ko'chirilgan buyruq (ichidagilari bilan) yangi yo'lda, aynan o'sha
  ok(json(T.getAt(e.prog, e.sel)) === json(src), "ko'chirilgan buyruq yangi yo'lda emas");
  // 3) joylashuvi: nishonga nisbatan to'g'ri
  const tn = tgt.params.name;
  const tp = paths(e.prog).find((q) => T.getAt(e.prog, q).params.name === tn);
  if (pos === "inside") ok(json(e.sel) === json([...tp, T.getAt(e.prog, tp).children.length - 1]), "ichiga: oxirgi bola emas");
  else ok(json(e.sel.slice(0, -1)) === json(tp.slice(0, -1)) && e.sel[e.sel.length - 1] === tp[tp.length - 1] + (pos === "after" ? 1 : -1),
          `${pos}: nishon qo'shnisi emas ${json(e.sel)} vs ${json(tp)}`);
  // 4) qolgan buyruqlarning nisbiy tartibi saqlangan (ko'chirilgandan tashqari)
  const srcNames = new Set(names([src]));
  const rest = (pr) => names(pr).filter((x) => !srcNames.has(x));
  ok(json(rest(e.prog)) === json(rest(p)), "qolganlar tartibi o'zgardi");
}
ok(moved > 500 && refused > 100, `tasodifiy holatlar yetarli emas (${moved}/${refused})`);
console.log(`treeOps.moveTo: ${n} tekshiruv, ${moved} ko'chirish, ${refused} rad`, process.exitCode ? "— XATOLAR BOR" : "— hammasi joyida");
