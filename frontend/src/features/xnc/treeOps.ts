// XNC dasturi daraxti ustida sof (toza) amallar: yo'l (`path: number[]`) bo'yicha topish, qo'shish, o'chirish, ko'chirish,
// nusxalash, chekinish (ichiga / tashqariga). Kirishni o'zgartirmaydi — har amal yangi dastur qaytaradi.
import type { XncCommand } from "../../api/types";

export type Path = number[];

/** Ichiga buyruq qo'yish mumkin bo'lgan (blok) buyruqlar. Boshqa buyruq `children` ga ega bo'lsa ham shunday ko'rsatiladi. */
export const CONTAINERS = new Set(["If", "Else", "While", "DoWhile", "Sub"]);

export const isContainer = (c: XncCommand | null | undefined): boolean => !!c && CONTAINERS.has(c.cmd);

export const pathKey = (p: Path): string => p.join(".");
export const samePath = (a: Path | null, b: Path | null): boolean => !!a && !!b && a.length === b.length && a.every((v, i) => v === b[i]);
export const isAncestor = (a: Path, b: Path): boolean => a.length < b.length && a.every((v, i) => v === b[i]);

const clone = <T,>(x: T): T => JSON.parse(JSON.stringify(x)) as T;

/** `path` bo'yicha buyruq (yo'q bo'lsa null). */
export function getAt(prog: XncCommand[], path: Path): XncCommand | null {
  let list = prog;
  let cur: XncCommand | null = null;
  for (const i of path) {
    cur = list[i] ?? null;
    if (!cur) return null;
    list = cur.children ?? [];
  }
  return cur;
}

/** Ota ro'yxati (ildiz yoki `children`) — o'zgartirish uchun nusxa daraxt ichida. */
function listIn(root: XncCommand[], parent: Path): XncCommand[] | null {
  let list = root;
  for (const i of parent) {
    const c = list[i];
    if (!c) return null;
    c.children = c.children ?? [];
    list = c.children;
  }
  return list;
}

export interface Edit { prog: XncCommand[]; sel: Path | null }

/** Buyruqni (qisman) yangilash. */
export function updateAt(prog: XncCommand[], path: Path, f: (c: XncCommand) => Partial<XncCommand>): XncCommand[] {
  const next = clone(prog);
  const parent = listIn(next, path.slice(0, -1));
  const i = path[path.length - 1];
  if (!parent || !parent[i]) return prog;
  parent[i] = { ...parent[i], ...f(parent[i]) };
  return next;
}

/** `parent` ichiga `index` o'rniga qo'shish (index yo'q — oxiriga). Yangi buyruq yo'lini ham qaytaradi. */
export function insertAt(prog: XncCommand[], parent: Path, index: number | undefined, cmd: XncCommand): Edit {
  const next = clone(prog);
  const list = listIn(next, parent);
  if (!list) return { prog, sel: null };
  const at = index === undefined ? list.length : Math.max(0, Math.min(index, list.length));
  list.splice(at, 0, clone(cmd));
  return { prog: next, sel: [...parent, at] };
}

/** O'chirish; keyingi tanlov — shu o'rindagi (yoki oldingi) qo'shni, bo'lmasa ota. */
export function removeAt(prog: XncCommand[], path: Path): Edit {
  const next = clone(prog);
  const parentPath = path.slice(0, -1);
  const list = listIn(next, parentPath);
  const i = path[path.length - 1];
  if (!list || !list[i]) return { prog, sel: null };
  list.splice(i, 1);
  if (list.length) return { prog: next, sel: [...parentPath, Math.min(i, list.length - 1)] };
  return { prog: next, sel: parentPath.length ? parentPath : null };
}

/** Nusxalash (o'zidan keyin, ichidagilari bilan); tanlov — nusxa. */
export function cloneAt(prog: XncCommand[], path: Path): Edit {
  const src = getAt(prog, path);
  if (!src) return { prog, sel: null };
  const parent = path.slice(0, -1);
  return insertAt(prog, parent, path[path.length - 1] + 1, src);
}

/** Qo'shnilar orasida yuqoriga / pastga (chegarada — o'zgarmaydi). */
export function moveSibling(prog: XncCommand[], path: Path, d: -1 | 1): Edit {
  const parentPath = path.slice(0, -1);
  const i = path[path.length - 1];
  const next = clone(prog);
  const list = listIn(next, parentPath);
  const j = i + d;
  if (!list || !list[i] || j < 0 || j >= list.length) return { prog, sel: path };
  [list[i], list[j]] = [list[j], list[i]];
  return { prog: next, sel: [...parentPath, j] };
}

/** Ichiga: oldingi qo'shni blok (If/While/…) bo'lsa — uning oxiriga o'tkaziladi. */
export function indent(prog: XncCommand[], path: Path): Edit {
  const i = path[path.length - 1];
  if (i === 0) return { prog, sel: path };
  const parentPath = path.slice(0, -1);
  const prevPath = [...parentPath, i - 1];
  const prev = getAt(prog, prevPath);
  if (!prev || !isContainer(prev)) return { prog, sel: path };
  const src = getAt(prog, path);
  if (!src) return { prog, sel: path };
  const removed = removeAt(prog, path).prog;
  return insertAt(removed, prevPath, undefined, src);
}

/** Tashqariga: ota blokdan chiqarib, uning keyingi qo'shnisi sifatida qo'yiladi. */
export function outdent(prog: XncCommand[], path: Path): Edit {
  if (path.length < 2) return { prog, sel: path };
  const src = getAt(prog, path);
  if (!src) return { prog, sel: path };
  const parentPath = path.slice(0, -1);
  const removed = removeAt(prog, path).prog;
  return insertAt(removed, parentPath.slice(0, -1), parentPath[parentPath.length - 1] + 1, src);
}

/** Sudrab ko'chirishda tashlash joyi: nishon buyruqdan oldin / keyin (shu darajada) yoki blok (If/While/…) ichiga (oxiriga). */
export type DropPos = "before" | "after" | "inside";

/**
 * Sichqoncha bilan sudrab ko'chirish (W18): `from` dagi buyruq (ichidagilari bilan) `target` ga nisbatan `pos` joyga qo'yiladi.
 * Tanlov — ko'chirilgan buyruqning yangi yo'li. Qaytaradi `null` agar: yo'l noto'g'ri; o'zini yoki o'z ichiga tashlash (nishon
 * `from` ning avlodi); «ichiga» faqat blok buyruqqa; natija o'zgarishsiz (shu joyning o'zi). Yo'llar hamma vaqt ko'chirishdan OLDINGI
 * daraxtga nisbatan beriladi — ko'chirilgan elementdan keyingi qo'shnilar indeksi o'chirilgach moslanadi.
 */
export function moveTo(prog: XncCommand[], from: Path, target: Path, pos: DropPos): Edit | null {
  const src = getAt(prog, from);
  const tgt = getAt(prog, target);
  if (!src || !tgt || !from.length || !target.length) return null;
  if (samePath(from, target) || isAncestor(from, target)) return null;
  if (pos === "inside" && !isContainer(tgt)) return null;
  const dest = pos === "inside"
    ? { parent: target, index: (tgt.children ?? []).length }
    : { parent: target.slice(0, -1), index: target[target.length - 1] + (pos === "after" ? 1 : 0) };
  const fp = from.slice(0, -1);
  const fi = from[from.length - 1];
  if (samePath(dest.parent, fp) && (dest.index === fi || dest.index === fi + 1)) return null;     // joyi o'zgarmaydi
  const dp = dest.parent.slice();
  let di = dest.index;
  if (dp.length >= fp.length && fp.every((v, i) => dp[i] === v)) {            // o'chirilgach, shu ro'yxatdagi keyingi qo'shnilar siljiydi
    if (dp.length === fp.length) { if (di > fi) di -= 1; }
    else if (dp[fp.length] > fi) dp[fp.length] -= 1;
  }
  const removed = removeAt(prog, from).prog;
  return insertAt(removed, dp, di, src);
}

export const canDrop = (prog: XncCommand[], from: Path, target: Path, pos: DropPos): boolean => moveTo(prog, from, target, pos) !== null;

export interface Row { path: Path; cmd: XncCommand; depth: number; hasChildren: boolean; collapsed: boolean }

/** Ko'rinadigan qatorlar (yig'ilgan bloklarning bolalari yashirin). */
export function flatten(prog: XncCommand[], collapsed: Set<string>): Row[] {
  const out: Row[] = [];
  const walk = (list: XncCommand[], base: Path) => {
    list.forEach((cmd, i) => {
      const path = [...base, i];
      const kids = cmd.children ?? [];
      const col = collapsed.has(pathKey(path));
      out.push({ path, cmd, depth: base.length, hasChildren: kids.length > 0, collapsed: col });
      if (kids.length && !col) walk(kids, path);
    });
  };
  walk(prog, []);
  return out;
}

/** Tanlangan yo'l ko'rinadigan bo'lishi uchun ajdodlarni ochadi. */
export function reveal(collapsed: Set<string>, path: Path): Set<string> {
  let changed = false;
  const next = new Set(collapsed);
  for (let n = 1; n < path.length; n++) {
    if (next.delete(pathKey(path.slice(0, n)))) changed = true;
  }
  return changed ? next : collapsed;
}

/** Barcha buyruqlar soni (ichma-ichlari bilan). */
export function countAll(prog: XncCommand[]): number {
  return prog.reduce((n, c) => n + 1 + countAll(c.children ?? []), 0);
}
