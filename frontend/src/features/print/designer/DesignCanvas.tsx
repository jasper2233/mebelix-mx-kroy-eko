// Etiketka vizual redaktori: maydon (sahifa). Server chizgan SVG (har element `<g data-p>`) + ustida tanlash/ko'chirish/o'lcham tutqichlari,
// to'r, yo'naltiruvchi chiziqlar. Ifodalar hisoblanmaydi: chegaraviy to'rtburchaklar ko'rinib turgan SVG dan (getBBox + CTM) olinadi.
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { sanitizeSvg } from "./designerApi";
import {
  boxHas, boxesTouch, guideTargets, isLeaf, matInv, matVec, snapMove, snapValue, transformBox, unionBox,
  type Box, type Guide, type Mat, type ResizeMode,
} from "./model";

export interface ElBox {
  hull: Box;                       // etiketka koordinatalarida (mm) chegaraviy to'rtburchak
  m: Mat;                          // mahalliy → etiketka matritsasi (ota guruhlar burilishi/siljishi)
  t: string;                       // element turi
  order: number;                   // hujjat tartibi (yuqorida — kattaroq)
  verts?: [number, number][];      // line/polyline tugunlari (etiketka koordinatalarida)
}
export type ElBoxes = Map<string, ElBox>;

export interface CanvasProps {
  svg: string; pageW: number; pageH: number; scale: number;
  sel: string[];                                            // tanlangan yo'llar («2», «3.then.1» …)
  getResizeMode: (key: string) => ResizeMode;
  grid: number; showGrid: boolean; snap: boolean; guides: boolean; errorKeys: Set<string>;
  onSelect: (keys: string[]) => void;
  onMove: (moves: { key: string; dx: number; dy: number }[]) => void;
  onResize: (key: string, oldLocal: Box, newLocal: Box) => void;
  onVertex: (key: string, index: number, dx: number, dy: number) => void;
  onMeasured: (m: ElBoxes) => void;
  onCursor: (x: number | null, y: number | null) => void;
}

type HandleId = "nw" | "n" | "ne" | "e" | "se" | "s" | "sw" | "w";
const HANDLE_POS: Record<HandleId, [number, number]> = { nw: [0, 0], n: [0.5, 0], ne: [1, 0], e: [1, 0.5], se: [1, 1], s: [0.5, 1], sw: [0, 1], w: [0, 0.5] };
const HANDLE_CURSOR: Record<HandleId, string> = { nw: "nwse-resize", se: "nwse-resize", ne: "nesw-resize", sw: "nesw-resize", n: "ns-resize", s: "ns-resize", e: "ew-resize", w: "ew-resize" };
const handlesFor = (mode: ResizeMode): HandleId[] =>
  mode === "box" ? (Object.keys(HANDLE_POS) as HandleId[]) : mode === "width" ? ["e", "w"] : mode === "uniform" ? ["se"] : [];
const HIT_PX = 6;                 // tutqich / tanlash bag'ishlash radiusi (ekran pikseli)
const MIN_SIZE = 0.5;             // mm

type Drag =
  | { kind: "move"; start: [number, number]; keys: string[]; hulls: Box[]; others: Box[]; moved: boolean }
  | { kind: "resize"; key: string; handle: HandleId; start: [number, number]; old: Box; mode: ResizeMode; others: Box[] }
  | { kind: "vertex"; key: string; index: number; start: [number, number] }
  | { kind: "band"; start: [number, number]; additive: boolean; base: string[] };

interface Overlay { delta: [number, number]; ghost: Box | null; band: Box | null; guides: Guide[]; vertex: { key: string; index: number; at: [number, number] } | null }
const NO_OVERLAY: Overlay = { delta: [0, 0], ghost: null, band: null, guides: [], vertex: null };

function parsePath(d: string): [number, number][] {
  const n = d.match(/-?\d*\.?\d+(?:e-?\d+)?/gi) ?? [];
  const out: [number, number][] = [];
  for (let i = 0; i + 1 < n.length; i += 2) out.push([Number(n[i]), Number(n[i + 1])]);
  return out;
}

function measure(root: SVGSVGElement): ElBoxes {
  const out: ElBoxes = new Map();
  const rc = root.getScreenCTM();
  if (!rc) return out;
  const rinv = rc.inverse();
  let order = 0;
  root.querySelectorAll<SVGGElement>("g[data-p]").forEach((g) => {
    order += 1;
    if (g.childElementCount === 0) return;
    let bb: DOMRect;
    try { bb = g.getBBox(); } catch { return; }
    if (bb.width === 0 && bb.height === 0) return;
    const c = g.getScreenCTM();
    if (!c) return;
    const rel = rinv.multiply(c);
    const m: Mat = { a: rel.a, b: rel.b, c: rel.c, d: rel.d, e: rel.e, f: rel.f };
    const t = g.getAttribute("data-t") ?? "";
    const box: ElBox = { hull: transformBox(m, { x: bb.x, y: bb.y, w: bb.width, h: bb.height }), m, t, order };
    const key = g.getAttribute("data-p") ?? "";
    if (t === "line") {
      const ln = g.querySelector("line");
      if (ln) {
        const p = (a: string, b: string): [number, number] => {
          const x = Number(ln.getAttribute(a)), y = Number(ln.getAttribute(b));
          return [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f];
        };
        box.verts = [p("x1", "y1"), p("x2", "y2")];
      }
    } else if (t === "polyline") {
      const pa = g.querySelector("path");
      if (pa) box.verts = parsePath(pa.getAttribute("d") ?? "").map(([x, y]) => [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f] as [number, number]);
    }
    out.set(key, box);
  });
  return out;
}

function distToSeg(p: [number, number], a: [number, number], b: [number, number]): number {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const l2 = dx * dx + dy * dy;
  const t = l2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2));
  return Math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy));
}

function resizedBox(old: Box, h: HandleId, dx: number, dy: number, uniform: boolean): Box {
  let x0 = old.x, y0 = old.y, x1 = old.x + old.w, y1 = old.y + old.h;
  if (h.includes("w")) x0 += dx;
  if (h.includes("e")) x1 += dx;
  if (h.includes("n")) y0 += dy;
  if (h.includes("s")) y1 += dy;
  if (x1 - x0 < MIN_SIZE) { if (h.includes("w")) x0 = x1 - MIN_SIZE; else x1 = x0 + MIN_SIZE; }
  if (y1 - y0 < MIN_SIZE) { if (h.includes("n")) y0 = y1 - MIN_SIZE; else y1 = y0 + MIN_SIZE; }
  if (uniform && old.w > 0) {
    const nh = (x1 - x0) * (old.h / old.w);
    if (h.includes("n")) y0 = y1 - nh; else y1 = y0 + nh;
  }
  return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
}

export function DesignCanvas(p: CanvasProps) {
  const { scale, pageW, pageH } = p;
  const hostRef = useRef<HTMLDivElement>(null);
  const paperRef = useRef<HTMLDivElement>(null);
  const [boxes, setBoxes] = useState<ElBoxes>(new Map());
  const [ov, setOv] = useState<Overlay>(NO_OVERLAY);
  const drag = useRef<Drag | null>(null);
  const live = useRef<{ dx: number; dy: number }>({ dx: 0, dy: 0 });
  const ghostRef = useRef<Box | null>(null);
  const vertexRef = useRef<{ key: string; index: number; at: [number, number] } | null>(null);
  const props = useRef(p);
  props.current = p;

  // server SVG → hujjat (xavfsiz) + o'lchash
  useLayoutEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    host.replaceChildren();
    const el = sanitizeSvg(p.svg);
    if (!el) { setBoxes(new Map()); props.current.onMeasured(new Map()); return; }
    el.setAttribute("width", String(pageW * scale));
    el.setAttribute("height", String(pageH * scale));
    el.style.display = "block";
    host.appendChild(el);
    const m = measure(el);
    setBoxes(m);
    props.current.onMeasured(m);
    setOv(NO_OVERLAY);
  }, [p.svg]); // eslint-disable-line react-hooks/exhaustive-deps

  useLayoutEffect(() => {   // masshtab/o'lcham o'zgardi: SVG o'lchami (chegaraviy to'rtburchaklar mm da — qayta o'lchash shart emas)
    const el = hostRef.current?.querySelector("svg");
    if (!el) return;
    el.setAttribute("width", String(pageW * scale));
    el.setAttribute("height", String(pageH * scale));
  }, [scale, pageW, pageH]);

  const toMm = useCallback((e: { clientX: number; clientY: number }): [number, number] => {
    const r = paperRef.current!.getBoundingClientRect();
    return [(e.clientX - r.left) / props.current.scale, (e.clientY - r.top) / props.current.scale];
  }, []);

  const hitTest = (pt: [number, number]): string | null => {
    const tol = HIT_PX / props.current.scale;
    let best: string | null = null, bo = -1;
    boxes.forEach((b, k) => {
      if (!isLeaf(b.t) || b.order < bo) return;
      let hit: boolean;
      if (b.t === "line" && b.verts && b.verts.length === 2) hit = distToSeg(pt, b.verts[0], b.verts[1]) <= tol + 0.4;
      else hit = boxHas(b.hull, pt[0], pt[1], tol * 0.5);
      if (hit) { best = k; bo = b.order; }
    });
    return best;
  };

  const otherBoxes = (excl: string[]): Box[] => {
    const out: Box[] = [];
    boxes.forEach((b, k) => { if (isLeaf(b.t) && !excl.includes(k)) out.push(b.hull); });
    return out;
  };

  const setLive = (keys: string[], dx: number, dy: number) => {
    const host = hostRef.current;
    if (!host) return;
    for (const k of keys) {
      const b = boxes.get(k);
      const g = host.querySelector(`g[data-p="${k}"]`);
      if (!b || !g) continue;
      const [lx, ly] = matVec(matInv(b.m), dx, dy);
      if (Math.abs(lx) + Math.abs(ly) < 1e-9) g.removeAttribute("transform");
      else g.setAttribute("transform", `translate(${lx} ${ly})`);
    }
  };
  const clearLive = (keys: string[]) => {
    const host = hostRef.current;
    if (!host) return;
    for (const k of keys) host.querySelector(`g[data-p="${k}"]`)?.removeAttribute("transform");
  };

  const selBox = (): Box | null => {
    const bs = p.sel.map((k) => boxes.get(k)?.hull).filter((b): b is Box => !!b);
    return bs.length ? unionBox(bs) : null;
  };

  // tutqichlar (ekran koordinatalarida emas — mm da hisoblab, chizishda px ga o'giriladi)
  const single = p.sel.length === 1 ? p.sel[0] : null;
  const singleBox = single ? boxes.get(single) ?? null : null;
  const mode: ResizeMode = single ? p.getResizeMode(single) : "none";

  const handleAt = (pt: [number, number]): { kind: "handle"; id: HandleId } | { kind: "vertex"; index: number } | null => {
    if (!single || !singleBox) return null;
    const tol = (HIT_PX + 2) / props.current.scale;
    if (singleBox.verts && (singleBox.t === "line" || singleBox.t === "polyline")) {
      for (let i = 0; i < singleBox.verts.length; i++) {
        const v = singleBox.verts[i];
        if (Math.hypot(pt[0] - v[0], pt[1] - v[1]) <= tol) return { kind: "vertex", index: i };
      }
    }
    const h = singleBox.hull;
    for (const id of handlesFor(mode)) {
      const [fx, fy] = HANDLE_POS[id];
      if (Math.hypot(pt[0] - (h.x + h.w * fx), pt[1] - (h.y + h.h * fy)) <= tol) return { kind: "handle", id };
    }
    return null;
  };

  const onDown = (e: React.PointerEvent) => {
    if (e.button !== 0) return;
    const pt = toMm(e);
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    const additive = e.shiftKey || e.ctrlKey || e.metaKey;
    const hh = handleAt(pt);
    if (hh && single && singleBox) {
      if (hh.kind === "vertex") drag.current = { kind: "vertex", key: single, index: hh.index, start: pt };
      else drag.current = { kind: "resize", key: single, handle: hh.id, start: pt, old: singleBox.hull, mode, others: otherBoxes([single]) };
      return;
    }
    const hit = hitTest(pt);
    if (hit) {
      let keys = p.sel;
      if (additive) {
        keys = p.sel.includes(hit) ? p.sel.filter((k) => k !== hit) : [...p.sel, hit];
        p.onSelect(keys);
        drag.current = null;
        return;
      }
      if (!p.sel.some((k) => k === hit || hit.startsWith(`${k}.`))) { keys = [hit]; p.onSelect(keys); }   // tanlangan guruh ichidagini bossa — guruh ko'chadi
      const hulls = keys.map((k) => boxes.get(k)?.hull).filter((b): b is Box => !!b);
      drag.current = { kind: "move", start: pt, keys, hulls, others: otherBoxes(keys), moved: false };
      return;
    }
    if (!additive) p.onSelect([]);
    drag.current = { kind: "band", start: pt, additive, base: p.sel };
  };

  const onMovePtr = (e: React.PointerEvent) => {
    const pt = toMm(e);
    p.onCursor(pt[0], pt[1]);
    const d = drag.current;
    if (!d) return;
    const noSnap = e.altKey;
    const tol = 6 / p.scale;
    if (d.kind === "move") {
      let dx = pt[0] - d.start[0], dy = pt[1] - d.start[1];
      if (!d.moved && Math.hypot(dx, dy) * p.scale < 3) return;
      d.moved = true;
      const u = unionBox(d.hulls);
      let guides: Guide[] = [];
      if (!noSnap && (p.snap || p.guides)) {
        const s = snapMove({ ...u, x: u.x + dx, y: u.y + dy }, d.others, { w: pageW, h: pageH }, { grid: p.snap ? p.grid : 0, guides: p.guides, tol });
        dx += s.dx; dy += s.dy; guides = s.guides;
      }
      live.current = { dx, dy };
      setLive(d.keys, dx, dy);
      setOv({ ...NO_OVERLAY, delta: [dx, dy], guides });
    } else if (d.kind === "resize") {
      let dx = pt[0] - d.start[0], dy = pt[1] - d.start[1];
      const guides: Guide[] = [];
      if (!noSnap && (p.snap || p.guides)) {
        const page = { w: pageW, h: pageH };
        const grid = p.snap ? p.grid : 0;
        const snapEdge = (axis: "x" | "y", edge: number, delta: number): number => {
          const s = snapValue(edge + delta, p.guides ? guideTargets(d.others, page, axis) : [], grid, tol);
          if (s.hit !== null) guides.push(axis === "x" ? { axis: "x", at: s.hit, from: 0, to: pageH } : { axis: "y", at: s.hit, from: 0, to: pageW });
          return s.v - edge;
        };
        if (d.handle.includes("w")) dx = snapEdge("x", d.old.x, dx);
        else if (d.handle.includes("e")) dx = snapEdge("x", d.old.x + d.old.w, dx);
        if (d.handle.includes("n")) dy = snapEdge("y", d.old.y, dy);
        else if (d.handle.includes("s")) dy = snapEdge("y", d.old.y + d.old.h, dy);
      }
      const nb = d.mode === "width" ? resizedBox(d.old, d.handle, dx, 0, false) : resizedBox(d.old, d.handle, dx, dy, d.mode === "uniform");
      ghostRef.current = nb;
      setOv({ ...NO_OVERLAY, ghost: nb, guides });
    } else if (d.kind === "vertex") {
      let at: [number, number] = [pt[0], pt[1]];
      let guides: Guide[] = [];
      if (!noSnap && (p.snap || p.guides)) {
        const page = { w: pageW, h: pageH };
        const grid = p.snap ? p.grid : 0;
        const sx = snapValue(at[0], p.guides ? guideTargets(otherBoxes([d.key]), page, "x") : [], grid, tol);
        const sy = snapValue(at[1], p.guides ? guideTargets(otherBoxes([d.key]), page, "y") : [], grid, tol);
        at = [sx.v, sy.v];
        if (sx.hit !== null) guides.push({ axis: "x", at: sx.hit, from: 0, to: pageH });
        if (sy.hit !== null) guides.push({ axis: "y", at: sy.hit, from: 0, to: pageW });
      }
      guides = guides.slice(0, 2);
      vertexRef.current = { key: d.key, index: d.index, at };
      setOv({ ...NO_OVERLAY, guides, vertex: vertexRef.current });
    } else {
      const x = Math.min(d.start[0], pt[0]), y = Math.min(d.start[1], pt[1]);
      setOv({ ...NO_OVERLAY, band: { x, y, w: Math.abs(pt[0] - d.start[0]), h: Math.abs(pt[1] - d.start[1]) } });
    }
  };

  const onUp = (e: React.PointerEvent) => {
    const d = drag.current;
    drag.current = null;
    try { (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId); } catch { /* yopilgan */ }
    if (!d) return;
    const pt = toMm(e);
    if (d.kind === "move") {
      clearLive(d.keys);
      if (d.moved) {
        const { dx, dy } = live.current;
        p.onMove(d.keys.map((k) => {
          const b = boxes.get(k);
          const [lx, ly] = b ? matVec(matInv(b.m), dx, dy) : [dx, dy];
          return { key: k, dx: lx, dy: ly };
        }));
      }
    } else if (d.kind === "resize" && ghostRef.current) {
      const b = boxes.get(d.key);
      if (b) {
        const inv = matInv(b.m);
        p.onResize(d.key, transformBox(inv, d.old), transformBox(inv, ghostRef.current));
      }
    } else if (d.kind === "vertex" && vertexRef.current) {
      const b = boxes.get(d.key);
      const v = b?.verts?.[d.index];
      const at = vertexRef.current.at;
      if (b && v) {
        const [lx, ly] = matVec(matInv(b.m), at[0] - v[0], at[1] - v[1]);
        if (Math.abs(lx) + Math.abs(ly) > 1e-6) p.onVertex(d.key, d.index, lx, ly);
      }
    } else if (d.kind === "band") {
      const x = Math.min(d.start[0], pt[0]), y = Math.min(d.start[1], pt[1]);
      const band: Box = { x, y, w: Math.abs(pt[0] - d.start[0]), h: Math.abs(pt[1] - d.start[1]) };
      if (band.w * p.scale > 3 || band.h * p.scale > 3) {
        const hit: string[] = [];
        boxes.forEach((b, k) => { if (isLeaf(b.t) && boxesTouch(band, b.hull)) hit.push(k); });
        p.onSelect(d.additive ? Array.from(new Set([...d.base, ...hit])) : hit);
      }
    }
    ghostRef.current = null;
    vertexRef.current = null;
    setOv(NO_OVERLAY);
  };

  useEffect(() => () => { drag.current = null; }, []);

  // ── chizish (overlay: px koordinatalari) ──
  const s = scale;
  const W = pageW * s, H = pageH * s;
  let gridStep = p.grid;
  while (gridStep * s < 6 && gridStep > 0) gridStep *= 5;
  const handles: { id: HandleId; x: number; y: number }[] = [];
  const base = singleBox ? singleBox.hull : null;
  if (base && single) {
    const hb: Box = ov.ghost && drag.current?.kind === "resize" ? ov.ghost : { x: base.x + ov.delta[0], y: base.y + ov.delta[1], w: base.w, h: base.h };
    for (const id of handlesFor(mode)) handles.push({ id, x: (hb.x + hb.w * HANDLE_POS[id][0]) * s, y: (hb.y + hb.h * HANDLE_POS[id][1]) * s });
  }
  const cursor = (() => {
    const d = drag.current;
    if (d?.kind === "move") return "move";
    return "default";
  })();
  const sb = selBox();
  return (
    <div className="lbd-paper" ref={paperRef} style={{ width: W, height: H }} data-testid="lbd-paper"
      onPointerDown={onDown} onPointerMove={onMovePtr} onPointerUp={onUp} onPointerCancel={onUp}
      onPointerLeave={() => { if (!drag.current) p.onCursor(null, null); }}>
      <div className="lbd-svg" ref={hostRef} data-testid="lbd-svg" />
      <svg className="lbd-ov" width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ cursor }}>
        {p.showGrid && gridStep > 0 && (
          <>
            <defs>
              <pattern id="lbd-grid" width={gridStep * s} height={gridStep * s} patternUnits="userSpaceOnUse">
                <path d={`M ${gridStep * s} 0 H 0 V ${gridStep * s}`} fill="none" stroke="rgba(29,111,184,.22)" strokeWidth={1} />
              </pattern>
            </defs>
            <rect width={W} height={H} fill="url(#lbd-grid)" pointerEvents="none" />
          </>
        )}
        {Array.from(p.errorKeys).map((k) => {
          const b = boxes.get(k)?.hull;
          return b ? <rect key={`e${k}`} x={b.x * s - 2} y={b.y * s - 2} width={b.w * s + 4} height={b.h * s + 4} fill="none" stroke="#d01f1f"
            strokeWidth={1.5} strokeDasharray="4 3" /> : null;
        })}
        {p.sel.map((k) => {
          const b = boxes.get(k)?.hull;
          if (!b) return null;
          const x = (b.x + ov.delta[0]) * s, y = (b.y + ov.delta[1]) * s;
          return <rect key={`s${k}`} x={x - 1} y={y - 1} width={b.w * s + 2} height={b.h * s + 2} fill="rgba(29,111,184,.06)" stroke="#1d6fb8" strokeWidth={1.4}
            data-testid="lbd-sel" />;
        })}
        {p.sel.length > 1 && sb && (
          <rect x={(sb.x + ov.delta[0]) * s - 3} y={(sb.y + ov.delta[1]) * s - 3} width={sb.w * s + 6} height={sb.h * s + 6} fill="none" stroke="#1d6fb8"
            strokeWidth={1} strokeDasharray="5 3" />
        )}
        {ov.ghost && <rect x={ov.ghost.x * s} y={ov.ghost.y * s} width={ov.ghost.w * s} height={ov.ghost.h * s} fill="rgba(29,111,184,.08)" stroke="#1d6fb8"
          strokeWidth={1.2} strokeDasharray="5 3" />}
        {singleBox?.verts && (singleBox.t === "line" || singleBox.t === "polyline") && singleBox.verts.map((v, i) => {
          const at = ov.vertex && ov.vertex.index === i && ov.vertex.key === single ? ov.vertex.at : v;
          return <circle key={`v${i}`} cx={at[0] * s} cy={at[1] * s} r={5} fill="#fff" stroke="#1d6fb8" strokeWidth={1.6} data-testid="lbd-vertex" style={{ cursor: "crosshair" }} />;
        })}
        {handles.map((h) => (
          <rect key={h.id} x={h.x - 4} y={h.y - 4} width={8} height={8} fill="#fff" stroke="#1d6fb8" strokeWidth={1.4} data-testid={`lbd-h-${h.id}`}
            style={{ cursor: HANDLE_CURSOR[h.id] }} />
        ))}
        {ov.guides.map((g, i) => g.axis === "x"
          ? <line key={`g${i}`} x1={g.at * s} y1={Math.max(0, g.from) * s - 6} x2={g.at * s} y2={Math.min(pageH, g.to) * s + 6} stroke="#e0245e" strokeWidth={1} />
          : <line key={`g${i}`} x1={Math.max(0, g.from) * s - 6} y1={g.at * s} x2={Math.min(pageW, g.to) * s + 6} y2={g.at * s} stroke="#e0245e" strokeWidth={1} />)}
        {ov.band && <rect x={ov.band.x * s} y={ov.band.y * s} width={ov.band.w * s} height={ov.band.h * s} fill="rgba(29,111,184,.10)" stroke="#1d6fb8"
          strokeWidth={1} strokeDasharray="3 2" />}
      </svg>
    </div>
  );
}
