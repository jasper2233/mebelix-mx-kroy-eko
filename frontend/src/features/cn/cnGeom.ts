// (CN) Nesting kartasi uchun sof geometriya yordamchilari: poligon yo'li, markaz nuqtasi (yozuv uchun), asosiy uchlar (yopishtirish uchun).
import type { Placement } from "../../api/types";

export type Pt = [number, number];
export type Ring = number[][];

/** Konturlar to'plamidan SVG yo'li (evenodd bilan chiziladi: birinchi — tashqi, qolganlari — ichki kesimlar). */
export function ringPath(rings: Ring[]): string {
  const out: string[] = [];
  for (const r of rings) {
    if (!r || r.length < 3) continue;
    out.push(`M${r.map((p) => `${rnd(p[0])} ${rnd(p[1])}`).join("L")}Z`);
  }
  return out.join("");
}

const rnd = (v: number) => Math.round(v * 100) / 100;

export function bboxOf(r: Ring): [number, number, number, number] {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const p of r) { x0 = Math.min(x0, p[0]); y0 = Math.min(y0, p[1]); x1 = Math.max(x1, p[0]); y1 = Math.max(y1, p[1]); }
  return [x0, y0, x1, y1];
}

export function pointInRing(x: number, y: number, r: Ring): boolean {
  let inside = false;
  for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
    const [xi, yi] = r[i], [xj, yj] = r[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function segDist(px: number, py: number, a: number[], b: number[]): number {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const l2 = dx * dx + dy * dy;
  let t = l2 > 0 ? ((px - a[0]) * dx + (py - a[1]) * dy) / l2 : 0;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(px - (a[0] + t * dx), py - (a[1] + t * dy));
}

function ringDist(px: number, py: number, r: Ring): number {
  let d = Infinity;
  for (let i = 0; i < r.length; i++) d = Math.min(d, segDist(px, py, r[i], r[(i + 1) % r.length]));
  return d;
}

/** Detal ichida (ichki kesimdan tashqarida) joylashgan, chetlaridan eng uzoq nuqta — raqam va nom yozuvi uchun (taxminiy, 18×18 to'r).
 *  Uchinchi qiymat — shu nuqtadan eng yaqin chetgacha masofa (yozuv sig'ishi uchun); oddiy to'rtburchakda — markaz va qisqa tomonning yarmi. */
export function anchorPoint(outline: Ring, holes: Ring[]): [number, number, number] {
  const [x0, y0, x1, y1] = bboxOf(outline);
  let best: Pt = [(x0 + x1) / 2, (y0 + y1) / 2];
  const inside = (x: number, y: number) => pointInRing(x, y, outline) && !holes.some((h) => pointInRing(x, y, h));
  if (!holes.length && outline.length <= 4) return [best[0], best[1], Math.min(x1 - x0, y1 - y0) / 2];          // oddiy to'rtburchak
  const N = 18;
  let bd = -1;
  for (let i = 0; i <= N; i++) for (let j = 0; j <= N; j++) {
    const x = x0 + ((x1 - x0) * (i + 0.5)) / (N + 1), y = y0 + ((y1 - y0) * (j + 0.5)) / (N + 1);
    if (!inside(x, y)) continue;
    let d = ringDist(x, y, outline);
    for (const h of holes) d = Math.min(d, ringDist(x, y, h));
    if (d > bd) { bd = d; best = [x, y]; }
  }
  return [best[0], best[1], Math.max(0, bd)];
}

/** Placement konturi: serverdan kelgan `outline`; bo'sh bo'lsa — o'rovchi to'rtburchak. */
export function placementRing(p: Placement): Ring {
  if (p.outline && p.outline.length >= 3) return p.outline;
  return [[p.x, p.y], [p.x + p.length, p.y], [p.x + p.length, p.y + p.width], [p.x, p.y + p.width]];
}

/** Burchak qiymatlari: poligon uchlaridan «asosiy» nuqtalar — burchaklar (burilish ≥ 20°) va to'g'ri chiziq ↔ yoy o'tish nuqtalari. */
export function keyPoints(r: Ring, maxN = 80): Pt[] {
  const n = r.length;
  if (n < 3) return r.map((p) => [p[0], p[1]] as Pt);
  const out: Pt[] = [];
  for (let i = 0; i < n; i++) {
    const a = r[(i + n - 1) % n], b = r[i], c = r[(i + 1) % n];
    const v1x = b[0] - a[0], v1y = b[1] - a[1], v2x = c[0] - b[0], v2y = c[1] - b[1];
    const l1 = Math.hypot(v1x, v1y), l2 = Math.hypot(v2x, v2y);
    if (l1 < 1e-9 || l2 < 1e-9) continue;
    const cos = Math.max(-1, Math.min(1, (v1x * v2x + v1y * v2y) / (l1 * l2)));
    const turn = (Math.acos(cos) * 180) / Math.PI;
    const ratio = Math.max(l1, l2) / Math.min(l1, l2);
    if (turn >= 20 || (ratio >= 4 && turn >= 1.5)) out.push([b[0], b[1]]);
  }
  if (out.length > maxN) {                                  // juda ko'p bo'lsa — tekis tanlab olinadi
    const step = out.length / maxN;
    return Array.from({ length: maxN }, (_, i) => out[Math.floor(i * step)]);
  }
  return out;
}

/** Placement ning barcha asosiy uchlari (tashqi kontur + ichki kesimlar). */
export function placementKeyPoints(p: Placement): Pt[] {
  return [...keyPoints(placementRing(p)), ...(p.holes ?? []).flatMap((h) => keyPoints(h, 40))];
}

/** Ekran (piksel) → SVG koordinatalari: svg elementining CTM i orqali. */
export function clientToSvg(svg: SVGSVGElement | null, cx: number, cy: number): Pt | null {
  if (!svg) return null;
  const ctm = svg.getScreenCTM();
  if (!ctm) return null;
  const pt = svg.createSVGPoint();
  pt.x = cx; pt.y = cy;
  const q = pt.matrixTransform(ctm.inverse());
  return [q.x, q.y];
}

/** SVG nuqtasi → ekran (piksel) koordinatalari. */
export function svgToClient(svg: SVGSVGElement, x: number, y: number): Pt | null {
  const ctm = svg.getScreenCTM();
  if (!ctm) return null;
  const pt = svg.createSVGPoint();
  pt.x = x; pt.y = y;
  const q = pt.matrixTransform(ctm);
  return [q.x, q.y];
}
