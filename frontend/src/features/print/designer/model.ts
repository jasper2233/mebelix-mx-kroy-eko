// Etiketka vizual redaktori: toza (React'siz) funksiyalar — shablon daraxti, element geometriyasi, ifodani siljitish, yopishish (snap).
// Ma'lumot modeli (W4 JSON shablon) o'zgarmaydi: bu yerda faqat mavjud maydonlar o'qiladi/yoziladi.
import { CHILD_KEYS, cloneTpl, locate, pathLabel, type ElPath, type LabelTemplate, type TplElement } from "../labelsApi";

export type { ElPath };
export interface Box { x: number; y: number; w: number; h: number }
/** Affin matritsa (SVG kabi): x' = a·x + c·y + e, y' = b·x + d·y + f. */
export interface Mat { a: number; b: number; c: number; d: number; e: number; f: number }

export const IDENT: Mat = { a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 };
export const r3 = (n: number): number => Math.round(n * 1000) / 1000;
export const clamp = (v: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, v));

export const MAX_ELEMENTS = 500;
export const MAX_DEPTH = 8;
export const CONTAINERS = new Set(["group", "if"]);
/** Hit-test/tanlash uchun «bargli» (konteyner bo'lmagan va chizmasi bor) elementlar. */
export const isLeaf = (t: string): boolean => !CONTAINERS.has(t) && t !== "var";

// ───────────────────────── Matritsa ─────────────────────────
export function matInv(m: Mat): Mat {
  const det = m.a * m.d - m.b * m.c;
  if (Math.abs(det) < 1e-12) return IDENT;
  return {
    a: m.d / det, b: -m.b / det, c: -m.c / det, d: m.a / det,
    e: (m.c * m.f - m.d * m.e) / det, f: (m.b * m.e - m.a * m.f) / det,
  };
}
export const matApply = (m: Mat, x: number, y: number): [number, number] => [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f];
export const matVec = (m: Mat, x: number, y: number): [number, number] => [m.a * x + m.c * y, m.b * x + m.d * y];

export function boxOfPoints(pts: [number, number][]): Box {
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const x = Math.min(...xs), y = Math.min(...ys);
  return { x, y, w: Math.max(...xs) - x, h: Math.max(...ys) - y };
}
export function transformBox(m: Mat, b: Box): Box {
  return boxOfPoints([matApply(m, b.x, b.y), matApply(m, b.x + b.w, b.y), matApply(m, b.x, b.y + b.h), matApply(m, b.x + b.w, b.y + b.h)]);
}
export const unionBox = (bs: Box[]): Box => boxOfPoints(bs.flatMap((b): [number, number][] => [[b.x, b.y], [b.x + b.w, b.y + b.h]]));
export const boxesTouch = (a: Box, b: Box): boolean => a.x <= b.x + b.w && b.x <= a.x + a.w && a.y <= b.y + b.h && b.y <= a.y + a.h;
export const boxHas = (b: Box, x: number, y: number, tol = 0): boolean => x >= b.x - tol && x <= b.x + b.w + tol && y >= b.y - tol && y <= b.y + b.h + tol;

// ───────────────────────── Son / ifoda ─────────────────────────
const NUM_RE = /^-?\d+(\.\d+)?$/;
export function numLit(v: unknown): number | null {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string" && NUM_RE.test(v.trim())) return Number(v.trim());
  return null;
}
/** Maydon matni → qiymat: raqamga o'xshash — son (JSON toza), aks holda ifoda satri. */
export function parseField(raw: string): number | string {
  const t = raw.trim();
  return NUM_RE.test(t) ? Number(t) : raw;
}

const TAIL_RE = /^(.*?)\s*([+-])\s*(\d+(?:\.\d+)?)\s*$/s;
const OP_END_RE = /[+\-*/%^(,<>=!&|]\s*$/;
/** Qiymatni `d` ga siljitish: son — qo'shiladi; ifoda — oxiridagi «± son» birlashtiriladi (`pad + 3` + 1.5 → `pad + 4.5`),
 *  aks holda `ifoda + d` yoziladi. Ifodani hisoblamaydi (ifoda dvigateli faqat serverda). */
export function shiftExpr(v: unknown, d: number): number | string {
  const n = numLit(v);
  if (n !== null) return r3(n + d);
  if (v === undefined || v === null || v === "") return r3(d);
  const s = String(v).trim();
  if (Math.abs(d) < 1e-9) return s;
  const m = TAIL_RE.exec(s);
  if (m && m[1].trim() && !OP_END_RE.test(m[1])) {
    const nxt = r3((m[2] === "-" ? -1 : 1) * Number(m[3]) + d);
    if (nxt === 0) return m[1].trim();
    return `${m[1].trim()} ${nxt < 0 ? "-" : "+"} ${Math.abs(nxt)}`;
  }
  return `${s} ${d < 0 ? "-" : "+"} ${r3(Math.abs(d))}`;
}
/** Ko'paytirish (QR o'lchamini masshtablash): son — ko'paytiriladi, ifoda — `(ifoda)*k`. */
export function scaleExpr(v: unknown, k: number): number | string {
  const n = numLit(v);
  if (n !== null) return r3(n * k);
  const s = String(v ?? "").trim();
  return s ? `(${s})*${r3(k)}` : r3(k);
}

// ───────────────────────── Element geometriyasi ─────────────────────────
const num = (v: unknown, d = 0): number => numLit(v) ?? d;
const isArr = (v: unknown): v is unknown[] => Array.isArray(v);

/** Elementni mahalliy koordinatalarda (dx, dy) ga siljitish (o'zgartiriladi). Guruh — origin, `if` — ichidagilar. */
export function translateEl(el: TplElement, dx: number, dy: number): void {
  const sh = (k: string, d: number) => { el[k] = shiftExpr(el[k], d); };
  switch (el.t) {
    case "text": case "rect": case "image": case "part": case "edges": case "barcode": sh("x", dx); sh("y", dy); break;
    case "line": sh("x1", dx); sh("y1", dy); sh("x2", dx); sh("y2", dy); break;
    case "arc": case "ellipse": sh("cx", dx); sh("cy", dy); break;
    case "group": {
      const o = isArr(el.origin) ? [...el.origin] : [0, 0];
      el.origin = [shiftExpr(o[0], dx), shiftExpr(o[1], dy)];
      break;
    }
    case "polyline":
      el.points = (isArr(el.points) ? el.points : []).map((p) => (isArr(p) ? [shiftExpr(p[0], dx), shiftExpr(p[1], dy)] : p));
      break;
    case "if":
      for (const k of ["then", "else"]) for (const c of (isArr(el[k]) ? (el[k] as TplElement[]) : [])) translateEl(c, dx, dy);
      break;
    default: break;
  }
}

export type ResizeMode = "box" | "width" | "uniform" | "none";
/** Elementni o'lcham tutqichlari (handles) bilan o'zgartirish usuli. Burilgan element, chiziq/poliliniya (tugun tutqichlari), yoy — «none». */
export function resizeMode(el: TplElement): ResizeMode {
  if (numLit(el.rotate)) return "none";
  switch (el.t) {
    case "rect": case "image": case "part": case "edges": case "ellipse": return "box";
    case "text": return "width";
    case "barcode": return String(el.kind ?? "qr").toLowerCase() === "code128" ? "box" : "uniform";
    default: return "none";
  }
}

/** Mahalliy chegaraviy to'rtburchak `old` → `nu`: element maydonlarini delta bilan yangilaydi (ifodali maydonlar ham). */
export function applyResize(el: TplElement, old: Box, nu: Box): boolean {
  const dx = nu.x - old.x, dy = nu.y - old.y, dw = nu.w - old.w, dh = nu.h - old.h;
  const sh = (k: string, d: number, min?: number) => {
    const v = shiftExpr(el[k], d);
    el[k] = typeof v === "number" && min !== undefined ? Math.max(min, v) : v;
  };
  switch (resizeMode(el)) {
    case "box":
      if (el.t === "ellipse") {
        sh("cx", (nu.x + nu.w / 2) - (old.x + old.w / 2)); sh("cy", (nu.y + nu.h / 2) - (old.y + old.h / 2));
        sh("rx", dw / 2, 0.1); sh("ry", dh / 2, 0.1);
      } else {
        sh("x", dx); sh("y", dy); sh("w", dw, 0.1); sh("h", dh, 0.1);
      }
      return true;
    case "uniform": {
      const k = old.w > 0.01 ? Math.max(0.05, nu.w / old.w) : 1;
      el.size = scaleExpr(el.size ?? 15, k);
      sh("x", dx); sh("y", dy);
      return true;
    }
    case "width": {
      const align = String(el.align ?? "left").toLowerCase();
      const ax = align === "center" || align === "middle" ? (nu.x + nu.w / 2) - (old.x + old.w / 2)
        : align === "right" || align === "end" ? (nu.x + nu.w) - (old.x + old.w) : dx;
      sh("x", ax);
      if (el.maxw === undefined || el.maxw === null || el.maxw === "") el.maxw = Math.max(1, r3(old.w + dw));
      else { sh("maxw", dw, 1); }
      return true;
    }
    default: return false;
  }
}

/** Chiziq/poliliniya tugunini mahalliy (dx, dy) ga siljitish: line — 0/1 (oxiri), polyline — nuqta indeksi. */
export function moveVertex(el: TplElement, index: number, dx: number, dy: number): void {
  if (el.t === "line") {
    const [kx, ky] = index === 0 ? ["x1", "y1"] : ["x2", "y2"];
    el[kx] = shiftExpr(el[kx], dx); el[ky] = shiftExpr(el[ky], dy);
  } else if (el.t === "polyline" && isArr(el.points)) {
    const pts = el.points.map((p) => (isArr(p) ? [...p] : p));
    const p = pts[index];
    if (isArr(p)) { p[0] = shiftExpr(p[0], dx); p[1] = shiftExpr(p[1], dy); }
    el.points = pts;
  }
}

// ───────────────────────── Daraxt amallari ─────────────────────────
export const pathKey = (p: ElPath): string => pathLabel(p);
export function parsePathKey(s: string): ElPath {
  return s.split(".").map((x) => (/^\d+$/.test(x) ? Number(x) - 1 : x));
}
export const samePath = (a: ElPath, b: ElPath): boolean => a.length === b.length && a.every((v, i) => v === b[i]);
const BRANCH_ORDER: Record<string, number> = { elements: 0, then: 0, else: 1 };
/** Hujjat tartibida taqqoslash (−1 / 0 / 1). */
export function comparePaths(a: ElPath, b: ElPath): number {
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    if (a[i] === b[i]) continue;
    if (typeof a[i] === "number" && typeof b[i] === "number") return (a[i] as number) < (b[i] as number) ? -1 : 1;
    return (BRANCH_ORDER[String(a[i])] ?? 0) - (BRANCH_ORDER[String(b[i])] ?? 0) < 0 ? -1 : 1;
  }
  return a.length === b.length ? 0 : a.length < b.length ? -1 : 1;
}
export const isAncestor = (anc: ElPath, p: ElPath): boolean => anc.length < p.length && anc.every((v, i) => v === p[i]);

export function getEl(tpl: LabelTemplate, path: ElPath): TplElement | null {
  const loc = locate(tpl, path);
  return loc ? loc[0][loc[1]] ?? null : null;
}
/** Tanlovni tozalash: bobosi ham tanlangan elementlar tashlanadi, hujjat tartibida saralanadi. */
export function normalizeSel(paths: ElPath[]): ElPath[] {
  const uniq = paths.filter((p, i) => paths.findIndex((q) => samePath(p, q)) === i);
  return uniq.filter((p) => !uniq.some((q) => isAncestor(q, p))).sort(comparePaths);
}

export function countElements(els: TplElement[]): number {
  let n = 0;
  for (const el of els) {
    n += 1;
    for (const k of CHILD_KEYS) if (isArr(el[k])) n += countElements(el[k] as TplElement[]);
  }
  return n;
}
export function depthOf(els: TplElement[], d = 1): number {
  let m = d;
  for (const el of els) for (const k of CHILD_KEYS) if (isArr(el[k])) m = Math.max(m, depthOf(el[k] as TplElement[], d + 1));
  return m;
}
export const cloneEl = (el: TplElement): TplElement => JSON.parse(JSON.stringify(el)) as TplElement;

/** Elementni yo'li bo'yicha o'chiradi; o'chirilgan elementni qaytaradi. */
export function removeAt(tpl: LabelTemplate, path: ElPath): TplElement | null {
  const loc = locate(tpl, path);
  if (!loc || !loc[0][loc[1]]) return null;
  return loc[0].splice(loc[1], 1)[0];
}
/** Konteynerga (parent=null — ildiz) element qo'shadi; yangi elementning yo'lini qaytaradi. */
export function addTo(tpl: LabelTemplate, parent: ElPath | null, key: "elements" | "then" | "else", el: TplElement, index?: number): ElPath {
  let list: TplElement[];
  let base: ElPath;
  if (parent === null) { list = tpl.elements; base = []; }
  else {
    const host = getEl(tpl, parent);
    if (!host) { list = tpl.elements; base = []; }
    else {
      if (!isArr(host[key])) host[key] = [];
      list = host[key] as TplElement[];
      base = [...parent, key];
    }
  }
  const i = index === undefined ? list.length : clamp(index, 0, list.length);
  list.splice(i, 0, el);
  return [...base, i];
}
/** Aka-uka ichida surish (delta −1 / +1); yangi yo'lni qaytaradi (chegarada — null). */
export function moveSibling(tpl: LabelTemplate, path: ElPath, delta: -1 | 1): ElPath | null {
  const loc = locate(tpl, path);
  if (!loc) return null;
  const [list, i] = loc;
  const j = i + delta;
  if (j < 0 || j >= list.length) return null;
  [list[i], list[j]] = [list[j], list[i]];
  return [...path.slice(0, -1), j];
}
export function moveToEdge(tpl: LabelTemplate, path: ElPath, edge: "front" | "back"): ElPath | null {
  const loc = locate(tpl, path);
  if (!loc) return null;
  const [list, i] = loc;
  const j = edge === "front" ? list.length - 1 : 0;
  if (i === j) return null;
  const [el] = list.splice(i, 1);
  list.splice(j, 0, el);
  return [...path.slice(0, -1), j];
}

/** Tanlangan elementlar tartibini (z-order) o'zgartirish: bir ro'yxatdagilar birga suriladi; yangi yo'llarni qaytaradi. */
export function reorderSiblings(tpl: LabelTemplate, paths: ElPath[], op: "forward" | "backward" | "front" | "back"): ElPath[] {
  const groups = new Map<string, ElPath[]>();
  for (const p of normalizeSel(paths)) {
    const k = p.slice(0, -1).join("|");
    groups.set(k, [...(groups.get(k) ?? []), p]);
  }
  const out: ElPath[] = [];
  groups.forEach((ps) => {
    const loc = locate(tpl, ps[0]);
    if (!loc) return;
    const list = loc[0];
    const on = new Set(ps.map((p) => p[p.length - 1] as number));
    let arr = list.map((el, i) => ({ el, sel: on.has(i) }));
    if (op === "front") arr = [...arr.filter((x) => !x.sel), ...arr.filter((x) => x.sel)];
    else if (op === "back") arr = [...arr.filter((x) => x.sel), ...arr.filter((x) => !x.sel)];
    else if (op === "forward") for (let i = arr.length - 2; i >= 0; i--) { if (arr[i].sel && !arr[i + 1].sel) [arr[i], arr[i + 1]] = [arr[i + 1], arr[i]]; }
    else for (let i = 1; i < arr.length; i++) { if (arr[i].sel && !arr[i - 1].sel) [arr[i], arr[i - 1]] = [arr[i - 1], arr[i]]; }
    list.splice(0, list.length, ...arr.map((x) => x.el));
    arr.forEach((x, i) => { if (x.sel) out.push([...ps[0].slice(0, -1), i]); });
  });
  return out;
}

/** Tanlangan aka-ukalarni guruhga o'raydi (origin 0,0 — ko'rinish o'zgarmaydi). Hammasi bitta ro'yxatda bo'lishi shart. */
export function groupSiblings(tpl: LabelTemplate, paths: ElPath[], kind: "group" | "if"): ElPath | null {
  const sel = normalizeSel(paths);
  if (!sel.length) return null;
  const parent = sel[0].slice(0, -1);
  if (!sel.every((p) => p.length === sel[0].length && samePath(p.slice(0, -1), parent))) return null;
  const idxs = sel.map((p) => p[p.length - 1] as number);
  const loc = locate(tpl, sel[0]);
  if (!loc) return null;
  const list = loc[0];
  const picked = idxs.map((i) => list[i]);
  for (const i of [...idxs].sort((a, b) => b - a)) list.splice(i, 1);
  const holder: TplElement = kind === "group"
    ? { t: "group", origin: [0, 0], rotate: 0, elements: picked }
    : { t: "if", cond: "true", then: picked, else: [] };
  const at = Math.min(...idxs);
  list.splice(at, 0, holder);
  return [...parent, at];
}

/** Guruh/If ni yoyadi: guruhda ichidagilar origin ga siljitiladi (faqat son origin va burish 0); If da — `then` shoxi. */
export function unwrap(tpl: LabelTemplate, path: ElPath): ElPath[] | null {
  const loc = locate(tpl, path);
  if (!loc) return null;
  const [list, i] = loc;
  const el = list[i];
  let kids: TplElement[];
  if (el.t === "group") {
    const o = isArr(el.origin) ? el.origin : [0, 0];
    const ox = numLit(o[0]), oy = numLit(o[1]);
    if (ox === null || oy === null || (el.rotate !== undefined && el.rotate !== null && numLit(el.rotate) !== 0)) return null;
    kids = (isArr(el.elements) ? (el.elements as TplElement[]) : []).map(cloneEl);
    for (const k of kids) translateEl(k, ox, oy);
  } else if (el.t === "if") {
    kids = (isArr(el.then) ? (el.then as TplElement[]) : []).map(cloneEl);
  } else return null;
  list.splice(i, 1, ...kids);
  return kids.map((_k, j) => [...path.slice(0, -1), i + j]);
}

// ───────────────────────── Yozuvlar (qatlamlar paneli) ─────────────────────────
export function elSummary(el: TplElement): string {
  const s = (v: unknown, n = 26): string => { const t = String(v ?? "").replace(/\s+/g, " "); return t.length > n ? t.slice(0, n - 1) + "…" : t; };
  switch (el.t) {
    case "text": return s(el.text);
    case "barcode": return `${String(el.kind ?? "qr")}: ${s(el.data, 20)}`;
    case "var": return `${s(el.name, 14)} = ${s(el.expr, 16)}`;
    case "if": return s(el.cond);
    case "rect": case "image": case "part": case "edges": return `${s(el.x, 6)}, ${s(el.y, 6)}`;
    case "line": return `${s(el.x1, 5)},${s(el.y1, 5)} → ${s(el.x2, 5)},${s(el.y2, 5)}`;
    case "polyline": return `${isArr(el.points) ? el.points.length : 0} pt`;
    case "arc": case "ellipse": return `${s(el.cx, 6)}, ${s(el.cy, 6)}`;
    case "group": return `${isArr(el.elements) ? el.elements.length : 0}`;
    default: return "";
  }
}

// ───────────────────────── Yopishish (snap) va yo'naltiruvchi chiziqlar ─────────────────────────
export interface Guide { axis: "x" | "y"; at: number; from: number; to: number }
export interface SnapOpts { grid: number; guides: boolean; tol: number }

function nearest(v: number, targets: number[], tol: number): { d: number; t: number } | null {
  let best: { d: number; t: number } | null = null;
  for (const t of targets) {
    const d = t - v;
    if (Math.abs(d) <= tol && (best === null || Math.abs(d) < Math.abs(best.d))) best = { d, t };
  }
  return best;
}
const xs = (b: Box): number[] => [b.x, b.x + b.w / 2, b.x + b.w];
const ys = (b: Box): number[] => [b.y, b.y + b.h / 2, b.y + b.h];

/** Ko'chirish: `box` (ko'chirishdan keyin) ni boshqa elementlar/sahifa chetlari/markazlariga va to'rga yopishtiradi. */
export function snapMove(box: Box, others: Box[], page: { w: number; h: number }, o: SnapOpts): { dx: number; dy: number; guides: Guide[] } {
  const pageBox: Box = { x: 0, y: 0, w: page.w, h: page.h };
  const cands = o.guides ? [pageBox, ...others] : [];
  const tx = cands.flatMap(xs), ty = cands.flatMap(ys);
  let dx = 0, dy = 0;
  const guides: Guide[] = [];
  let hx: { d: number; t: number } | null = null;
  for (const v of xs(box)) { const h = nearest(v, tx, o.tol); if (h && (!hx || Math.abs(h.d) < Math.abs(hx.d))) hx = h; }
  let hy: { d: number; t: number } | null = null;
  for (const v of ys(box)) { const h = nearest(v, ty, o.tol); if (h && (!hy || Math.abs(h.d) < Math.abs(hy.d))) hy = h; }
  if (hx) dx = hx.d;
  else if (o.grid > 0) dx = Math.round(box.x / o.grid) * o.grid - box.x;
  if (hy) dy = hy.d;
  else if (o.grid > 0) dy = Math.round(box.y / o.grid) * o.grid - box.y;
  const moved: Box = { ...box, x: box.x + dx, y: box.y + dy };
  if (hx) {
    const hit = cands.filter((c) => xs(c).some((v) => Math.abs(v - hx!.t) < 1e-6));
    const all = [moved, ...hit];
    guides.push({ axis: "x", at: hx.t, from: Math.min(...all.map((b) => b.y)), to: Math.max(...all.map((b) => b.y + b.h)) });
  }
  if (hy) {
    const hit = cands.filter((c) => ys(c).some((v) => Math.abs(v - hy!.t) < 1e-6));
    const all = [moved, ...hit];
    guides.push({ axis: "y", at: hy.t, from: Math.min(...all.map((b) => b.x)), to: Math.max(...all.map((b) => b.x + b.w)) });
  }
  return { dx, dy, guides };
}

/** Bitta qiymatni (qirra yoki tugun koordinatasi) yopishtirish: avval nishonlar (boshqa elementlar/sahifa), keyin to'r. */
export function snapValue(v: number, targets: number[], grid: number, tol: number): { v: number; hit: number | null } {
  const h = nearest(v, targets, tol);
  if (h) return { v: h.t, hit: h.t };
  return { v: grid > 0 ? Math.round(v / grid) * grid : v, hit: null };
}
export const guideTargets = (others: Box[], page: { w: number; h: number }, axis: "x" | "y"): number[] =>
  [{ x: 0, y: 0, w: page.w, h: page.h } as Box, ...others].flatMap(axis === "x" ? xs : ys);

/** Ko'p tanlovni tekislash. */
export type AlignKind = "left" | "centerH" | "right" | "top" | "centerV" | "bottom";
export function alignDeltas(boxes: Box[], kind: AlignKind): [number, number][] {
  const u = unionBox(boxes);
  return boxes.map((b) => {
    switch (kind) {
      case "left": return [u.x - b.x, 0];
      case "right": return [u.x + u.w - (b.x + b.w), 0];
      case "centerH": return [u.x + u.w / 2 - (b.x + b.w / 2), 0];
      case "top": return [0, u.y - b.y];
      case "bottom": return [0, u.y + u.h - (b.y + b.h)];
      default: return [0, u.y + u.h / 2 - (b.y + b.h / 2)];
    }
  });
}

/** Xossalar paneli: chiziq qalinligi/rangi (stroke — son yoki {w, color}). */
export function getStroke(el: TplElement): { w: unknown; color: string } {
  const st = el.stroke;
  if (st && typeof st === "object" && !isArr(st)) {
    const o = st as { w?: unknown; color?: unknown };
    return { w: o.w ?? "", color: typeof o.color === "string" ? o.color : "" };
  }
  return { w: st ?? "", color: "" };
}
export function setStroke(el: TplElement, w: unknown, color: string): void {
  const wNum = w === "" || w === undefined || w === null;
  if (wNum && !color) { delete el.stroke; return; }
  el.stroke = { ...(wNum ? {} : { w }), ...(color ? { color } : {}) };
}

export { cloneTpl, num };
