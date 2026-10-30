// Kroy tahriri sharpasi uchun serverdagi tekshiruvning nusxasi (editor._place_free): detallarning ANIQ joylaridan gilyotina
// daraxti (editor_pack._build), darajalar (optimizer._normalize/_depth) va ichki qirindi ≥ «Минимальная обрезка»
// (optimizer._trim_violations). Server baribir o'zi tekshiradi — bu faqat sharpa rangi to'g'ri bo'lishi uchun.

export interface Box { x: number; y: number; l: number; w: number }
interface GNode extends Box { k: "C" | "P" | "W"; a?: "x" | "y"; c?: GNode[] }

const TOL = 0.01;
const EPS = 1e-6;

const other = (ax: "x" | "y"): "x" | "y" => (ax === "x" ? "y" : "x");
const span = (p: Box, ax: "x" | "y"): [number, number] => (ax === "x" ? [p.x, p.x + p.l] : [p.y, p.y + p.w]);
const spanOf = (ps: Box[], ax: "x" | "y"): [number, number] =>
  [Math.min(...ps.map((p) => span(p, ax)[0])), Math.max(...ps.map((p) => span(p, ax)[1]))];

function split(parts: Box[], ax: "x" | "y", kerf: number): Box[][] {
  const out: Box[][] = [];
  let end: number | null = null;
  for (const p of [...parts].sort((a, b) => span(a, ax)[0] - span(b, ax)[0])) {
    const [s, e] = span(p, ax);
    if (end === null || s - end < kerf - TOL) {
      if (end === null) out.push([]);
      out[out.length - 1].push(p);
      end = end === null ? e : Math.max(end, e);
    } else {
      out.push([p]);
      end = e;
    }
  }
  return out;
}

function build(parts: Box[], x: number, y: number, l: number, w: number, ax: "x" | "y", kerf: number,
  depth = 0, switched = false): GNode | null {
  if (depth > 60) return null;
  if (parts.length === 1) {
    const p = parts[0];
    if (Math.abs(p.l - l) <= TOL && Math.abs(p.w - w) <= TOL) return { x, y, l, w, k: "P" };
  }
  const a0 = ax === "x" ? x : y, a1 = a0 + (ax === "x" ? l : w);
  const groups = split(parts, ax, kerf);
  if (groups.length === 1) {
    const [lo, hi] = spanOf(parts, ax);
    if (lo <= a0 + TOL && hi >= a1 - TOL) {
      if (switched) return null;
      return build(parts, x, y, l, w, other(ax), kerf, depth + 1, true);
    }
  }
  const strip = (s0: number, s1: number): Box => (ax === "x" ? { x: s0, y, l: s1 - s0, w } : { x, y: s0, l, w: s1 - s0 });
  const kids: GNode[] = [];
  let cur = a0;
  for (const g of groups) {
    const [lo, hi] = spanOf(g, ax);
    let s0: number;
    if (lo - kerf - cur > EPS) {
      kids.push({ ...strip(cur, lo - kerf), k: "W" });
      s0 = lo;
    } else {
      s0 = Math.min(lo - cur < kerf - TOL ? cur : lo, lo);
    }
    const b = strip(s0, hi);
    const ch = build(g, b.x, b.y, b.l, b.w, other(ax), kerf, depth + 1);
    if (!ch) return null;
    kids.push(ch);
    cur = hi + kerf;
  }
  if (a1 - cur > EPS) kids.push({ ...strip(cur, a1), k: "W" });
  return { x, y, l, w, k: "C", a: ax, c: kids };
}

const same = (a: Box, b: Box) => Math.abs(a.x - b.x) <= EPS && Math.abs(a.y - b.y) <= EPS && Math.abs(a.l - b.l) <= EPS && Math.abs(a.w - b.w) <= EPS;

/** Darajali daraxtda detalning eng chuqur darajasi (= kerakli burilishlar soni). */
function depthOf(root: GNode): number {
  const flat = (n: GNode): GNode => {
    if (n.k !== "C") return n;
    const kids: GNode[] = [];
    for (let ch of n.c ?? []) {
      ch = flat(ch);
      if (ch.k === "C" && (ch.c?.length ?? 0) === 1 && same(ch, ch.c![0])) ch = ch.c![0];
      if (ch.k === "C" && ch.a === n.a) kids.push(...(ch.c ?? []));
      else kids.push(ch);
    }
    n.c = kids.filter((k) => !(k.k === "W" && (k.l <= EPS || k.w <= EPS)));
    if (n.c.length === 1 && n.c[0].k === "C" && same(n, n.c[0])) return n.c[0];
    return n;
  };
  const r = flat(root);
  const deep = (n: GNode, lvl: number): number => (n.k !== "C" ? lvl : Math.max(lvl, ...(n.c ?? []).map((c) => deep(c, lvl + 1))));
  return r.k === "C" ? deep(r, 0) : 1;
}

/** Ichki kesimlarda «Минимальная обрезка» dan tor qirindi bormi (list chetidagi qirindi hisobga olinmaydi). */
function trimBad(root: GNode, zone: Box, mt: number): boolean {
  const walk = (n: GNode): boolean => {
    if (n.k !== "C") return false;
    const ax = n.a ?? "x";
    const end = ax === "x" ? n.x + n.l : n.y + n.w;
    const raw = end >= (ax === "x" ? zone.x + zone.l : zone.y + zone.w) - EPS;
    const body = (n.c ?? []).filter((c) => c.k !== "W");
    if (body.length && !raw) {
      const last = Math.max(...body.map((c) => (ax === "x" ? c.x + c.l : c.y + c.w)));
      const rest = end - last;
      if (rest > EPS && rest < mt - EPS) return true;
    }
    return (n.c ?? []).some(walk);
  };
  return walk(root);
}

/** Detallar (yangisi bilan) shu joylarda gilyotina bilan kesiladimi: burilishlar ≤ maxRot, ichki qirindi 0 yoki ≥ minTrim. */
export function cuttable(parts: Box[], zone: Box, firstAxis: "x" | "y", kerf: number, minTrim: number, maxRot: number): boolean {
  for (const ax of [firstAxis, other(firstAxis)]) {
    const t = build(parts.map((p) => ({ ...p })), zone.x, zone.y, zone.l, zone.w, ax, kerf);
    if (!t) continue;
    if (depthOf(JSON.parse(JSON.stringify(t)) as GNode) > Math.max(1, maxRot)) continue;
    if (trimBad(t, zone, minTrim)) continue;
    return true;
  }
  return false;
}
