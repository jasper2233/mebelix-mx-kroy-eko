// Kroy kartasi (SVG): detallar — to'q sariq (#ffa500), chiqindi va torsovka — neytral kulrang, qoldiq — ko'k; raqam va o'lchamlar.
// Tanlangan detal — to'qroq to'q sariq to'ldirish (kontur o'zgarmaydi); ID va o'lchamlar — bir xil kichik qalin monospace.
// Tahrir rejimida (onPick/onBand): ko'p tanlash ajratilgan manzillar (`selectedPaths`) va sichqoncha ramkasi (CSE-019).
import { useEffect, useMemo, useRef, useState, type MouseEvent } from "react";
import type { CutMap, Operation, Part, Project, TreeNode } from "../../api/types";

export const COLORS = {
  part: "#ffa500", partStroke: "#404040", waste: "#c8c8c8", remnant: "#86b4e6", remnantSmall: "#b9d3ef",
  trim: "#c8c8c8", select: "#0b57d0", hi: "#d92f2f", partSel: "#ff7800",
};

type Side = "top" | "bottom" | "left" | "right";
interface EdgeMark { color: string; symbol: string }

function rotateEdges(e: Partial<Record<Side, EdgeMark>>, rot: boolean): Partial<Record<Side, EdgeMark>> {
  if (!rot) return e;
  return { top: e.left, bottom: e.right, left: e.bottom, right: e.top };
}

export function nodeAt(root: TreeNode, path: number[]): TreeNode | null {
  let n: TreeNode | undefined = root;
  for (const i of path) { n = n?.c?.[i]; if (!n) return null; }
  return n ?? null;
}

/** Nuqtani o'z ichiga olgan eng chuqur tugun manzili. */
export function hitTest(root: TreeNode, x: number, y: number): number[] | null {
  const inside = (n: TreeNode) => x >= n.x - 0.01 && x <= n.x + n.l + 0.01 && y >= n.y - 0.01 && y <= n.y + n.w + 0.01;
  if (!inside(root)) return null;
  const path: number[] = [];
  let n = root;
  for (;;) {
    const kids = n.c ?? [];
    const i = kids.findIndex(inside);
    if (i < 0) return path;
    path.push(i);
    n = kids[i];
  }
}

export interface PickInfo { path: number[]; node: TreeNode | null; x: number; y: number; button: number; alt: boolean;
  ctrl: boolean; shift: boolean }

/** Sichqoncha ramkasi (list koordinatalarida) va tugma holati. */
export interface BandInfo { x0: number; y0: number; x1: number; y1: number; ctrl: boolean; shift: boolean; alt: boolean }

/** Ramka ichida to'liq turgan eng yuqori darajadagi tugunlar (detal yoki polosa; chiqindi va ildiz emas): manzillar ro'yxati. */
export function nodesInRect(root: TreeNode, r: { x0: number; y0: number; x1: number; y1: number }): number[][] {
  const xa = Math.min(r.x0, r.x1), xb = Math.max(r.x0, r.x1), ya = Math.min(r.y0, r.y1), yb = Math.max(r.y0, r.y1);
  const eps = 0.01;
  const inside = (n: TreeNode) => n.x >= xa - eps && n.y >= ya - eps && n.x + n.l <= xb + eps && n.y + n.w <= yb + eps;
  const out: number[][] = [];
  const walk = (n: TreeNode, path: number[]) => {
    (n.c ?? []).forEach((c, i) => {
      if (c.k === "W") return;
      const p = [...path, i];
      if (inside(c)) out.push(p);
      else if (c.k === "C") walk(c, p);
    });
  };
  walk(root, []);
  return out;
}

/** Matnni `n` belgigacha qisqartirish: sig'masa oxiri «…» (kesilgani ko'rinsin; to'liq nom — jadvalda / tooltipda). */
export const clipText = (s: string, n: number): string => (s.length <= n ? s : n <= 1 ? "…" : `${s.slice(0, n - 1).trimEnd()}…`);

export const samePath = (a: number[], b: number[]) => a.length === b.length && a.every((v, i) => v === b[i]);

const fmt = (v: number) => String(Math.round(v * 100) / 100);
/** O'lcham yozuvlari shrifti — monospace, qalin (xodimlar o'rgangan tizimdagi ko'rinish). */
const MONO = "Consolas, 'Courier New', monospace";

/** Pripusk (detal tomonlari + umumiy «Припуск на обработку заготовки») — joylashgan detalning chap/yuqori/o'ng/past tomonidan
 *  ichkariga qancha (mm). Burilgan detalda tomonlar kromkalar bilan bir xil almashadi (backend `render._allowance_insets`). */
export function allowanceInsets(part: Part, ma: number, rotated: boolean): [number, number, number, number] {
  const t = part.allow_top + ma, b = part.allow_bottom + ma, l = part.allow_left + ma, r = part.allow_right + ma;
  return rotated ? [b, l, t, r] : [l, t, r, b];
}

/** Kromka belgilari (harf) o'lcham yonida: « A», « AB» (D8: «820 A»); kromka yo'q bo'lsa bo'sh.
 *  Ekrandagi kartada ko'rsatilmaydi (xodimlar o'rgangan tizimda ekranda faqat raqam, harflar — chop hisobotida; QA #18):
 *  faqat `edgeLetters` berilganda qo'shiladi. */
function marks(...e: (EdgeMark | undefined)[]): string {
  const s = [...new Set(e.map((x) => x?.symbol).filter(Boolean))].join("");
  return s ? ` ${s}` : "";
}

export function MapView(props: {
  map: CutMap; project: Project; op: Operation; thumb?: boolean; label?: "number" | "name" | "number_name";
  showEdges?: boolean; selectedPath?: number[] | null; selectedPaths?: number[][]; highlightPartId?: string | null;
  onPick?: (p: PickInfo) => void; className?: string; testid?: string;
  /** O'lcham yoniga kromka harflarini qo'shish (chop/hisobot ko'rinishi); ekran kartasida — standart o'chiq. */
  edgeLetters?: boolean;
  /** Chap tugma bilan sudralganda ramka: berilsa — bosish `mouseup` da hal qilinadi (ramka va bosishni ajratish uchun). */
  onBand?: (b: BandInfo) => void;
  /** Ko'rish rejimi: detalni bosish (double — ikki marta bosish); bo'sh joy — null. */
  onPart?: (partId: string | null, double: boolean) => void;
}) {
  const { map: m, project, op, thumb } = props;
  const mk = props.edgeLetters ? marks : () => "";                      // ekranda — faqat raqam (QA #18)
  const svg = useRef<SVGSVGElement>(null);
  const L = m.sheet_length, W = m.sheet_width;
  const fs = Math.max(16, Math.min(L, W) / 34);           // yozuvlar: kartaga sig'dirilganda ≈14px
  const parts = useMemo(() => new Map<string, Part>(op.parts.map((p) => [p.id, p])), [op.parts]);
  const edgeOps = useMemo(() => {
    const e = new Map<string, EdgeMark>();
    for (const o of project.operations) if (o.type === "EL" && o.el) e.set(o.id, { color: o.el.color && o.el.color !== "#000000" ? o.el.color : "#1b2733", symbol: o.el.symbol });
    return e;
  }, [project.operations]);
  const root = m.strips?.[0];
  const label = props.label ?? "number_name";
  const ma = op.cs_cut?.machining_allowance ?? 0;           // umumiy pripusk (DM-010: pripusk detal ichida punktir)
  // detallar orasidagi propil chizilmaydi: to'rtburchak propilning yarmiga kengaytiriladi — qo'shni detallar bitta chiziq
  // bilan ajraladi (ikki chiziq + kulrang tirqish emas); kesish maydonidan (root) chiqmaydi
  const k2 = Math.max(0, (op.cs_cut?.kerf ?? 0) / 2);
  const grow = (x: number, y: number, l: number, w: number) => {
    if (!root || thumb || k2 <= 0) return { x, y, l, w };
    const x0 = Math.max(root.x, x - k2), y0 = Math.max(root.y, y - k2);
    const x1 = Math.min(root.x + root.l, x + l + k2), y1 = Math.min(root.y + root.w, y + w + k2);
    return x1 > x0 && y1 > y0 ? { x: x0, y: y0, l: x1 - x0, w: y1 - y0 } : { x, y, l, w };
  };

  const toSvg = (cx: number, cy: number): { x: number; y: number } | null => {
    if (!svg.current) return null;
    const pt = svg.current.createSVGPoint();
    pt.x = cx; pt.y = cy;
    const ctm = svg.current.getScreenCTM();
    if (!ctm) return null;
    const p = pt.matrixTransform(ctm.inverse());
    return { x: p.x, y: p.y };
  };

  const pickAt = (q: { x: number; y: number }, e: { button: number; altKey: boolean; ctrlKey: boolean; metaKey: boolean;
    shiftKey: boolean }) => {
    if (!props.onPick || !root) return;
    const path = hitTest(root, q.x, q.y);
    if (path === null) return;
    props.onPick({ path, node: nodeAt(root, path), x: q.x, y: q.y, button: e.button, alt: e.altKey, ctrl: e.ctrlKey || e.metaKey, shift: e.shiftKey });
  };

  const pick = (e: MouseEvent<SVGSVGElement>) => {
    if (!props.onPick || !root) return;
    const q = toSvg(e.clientX, e.clientY);
    if (!q || hitTest(root, q.x, q.y) === null) return;
    e.preventDefault();
    pickAt(q, e);
  };

  // Sichqoncha ramkasi: chap tugma bosilib 5 px dan ko'p siljitilsa — ramka; aks holda oddiy bosish (mouseup da)
  const [band, setBand] = useState<{ x0: number; y0: number; x1: number; y1: number } | null>(null);
  const cleanup = useRef<(() => void) | null>(null);
  useEffect(() => () => cleanup.current?.(), []);
  const onDown = (e: MouseEvent<SVGSVGElement>) => {
    if (!props.onPick) return;
    if (e.button !== 0 || !props.onBand) { pick(e); return; }
    const start = toSvg(e.clientX, e.clientY);
    if (!start) return;
    e.preventDefault();
    const sx = e.clientX, sy = e.clientY;
    let dragging = false;
    const move = (ev: globalThis.MouseEvent) => {
      if (!dragging && Math.hypot(ev.clientX - sx, ev.clientY - sy) < 5) return;
      dragging = true;
      const q = toSvg(ev.clientX, ev.clientY);
      if (q) setBand({ x0: start.x, y0: start.y, x1: q.x, y1: q.y });
    };
    const up = (ev: globalThis.MouseEvent) => {
      cleanup.current?.();
      setBand(null);
      const q = toSvg(ev.clientX, ev.clientY) ?? start;
      if (dragging) {
        props.onBand?.({ x0: start.x, y0: start.y, x1: q.x, y1: q.y, ctrl: ev.ctrlKey || ev.metaKey, shift: ev.shiftKey, alt: ev.altKey });
      } else {
        pickAt(start, ev);
      }
    };
    cleanup.current = () => {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
      cleanup.current = null;
    };
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
  };

  const clickPart = (e: MouseEvent<SVGSVGElement>) => {
    if (!props.onPart || !svg.current) return;
    const pt = svg.current.createSVGPoint();
    pt.x = e.clientX; pt.y = e.clientY;
    const ctm = svg.current.getScreenCTM();
    if (!ctm) return;
    const q = pt.matrixTransform(ctm.inverse());
    const hit = m.placements.find((pl) => q.x >= pl.x && q.x <= pl.x + pl.length && q.y >= pl.y && q.y <= pl.y + pl.width);
    props.onPart(hit ? hit.part_id : null, e.detail >= 2);
  };

  /** Joylashuv uchun umumiy qiymatlar (shakl va yozuv o'tishlari uchun bir xil). */
  const placementView = (p: CutMap["placements"][number]) => {
    const part = parts.get(p.part_id);
    const hi = !!props.highlightPartId && p.part_id === props.highlightPartId;
    let edges: Partial<Record<Side, EdgeMark>> = {};
    if (props.showEdges !== false && part && !thumb) {
      const e: Partial<Record<Side, EdgeMark>> = {};
      (["top", "bottom", "left", "right"] as Side[]).forEach((sd) => {
        const id = part[`edge_${sd}`]?.op_id;
        const em = id ? edgeOps.get(id) : undefined;
        if (em) e[sd] = em;
      });
      edges = rotateEdges(e, p.rotated);
    }
    const sw = Math.max(fs / 9, 1), ins = sw / 2 + fs / 12;   // ingichka kromka chizig'i (detal chetidan biroz ichkarida)
    const seg: Record<Side, [number, number, number, number]> = {
      top: [p.x + ins, p.y + ins, p.x + p.length - ins, p.y + ins],
      bottom: [p.x + ins, p.y + p.width - ins, p.x + p.length - ins, p.y + p.width - ins],
      left: [p.x + ins, p.y + ins, p.x + ins, p.y + p.width - ins],
      right: [p.x + p.length - ins, p.y + ins, p.x + p.length - ins, p.y + p.width - ins],
    };
    return { part, hi, edges, sw, seg, name: part?.name ?? "" };
  };

  // tanlangan tugunlar (bitta `selectedPath` yoki ko'p tanlash `selectedPaths`)
  const selNodes = useMemo(() => {
    if (!root) return [] as TreeNode[];
    const ps = props.selectedPaths ?? (props.selectedPath ? [props.selectedPath] : []);
    return ps.map((p) => nodeAt(root, p)).filter((n): n is TreeNode => !!n);
  }, [root, props.selectedPath, props.selectedPaths]);
  return (
    <svg ref={svg} className={props.className ?? "mapsvg"} viewBox={`0 0 ${L} ${W}`} preserveAspectRatio="xMidYMid meet"
      data-testid={props.testid} onMouseDown={props.onPick ? onDown : undefined} onClick={props.onPart ? clickPart : undefined}
      onContextMenu={props.onPick ? (e) => e.preventDefault() : undefined} fontFamily="Arial, Helvetica, sans-serif">
      <rect x={0} y={0} width={L} height={W} fill={COLORS.trim} stroke="#222" strokeWidth={1} vectorEffect="non-scaling-stroke" />
      {root && <rect x={root.x} y={root.y} width={root.l} height={root.w} fill={COLORS.waste} />}
      {m.offcuts.filter((o) => o.kind === "remnant").map((o, i) => (
        <g key={`r${i}`}>
          <rect x={o.x} y={o.y} width={o.length} height={o.width} fill={o.business ? COLORS.remnant : COLORS.remnantSmall}
            stroke="#3b6ea5" strokeWidth={1} vectorEffect="non-scaling-stroke" />
          {!thumb && o.width > fs * 1.6 && (() => {
            // qoldiq yozuvi: to'liq («Д3 600×400») sig'sa — to'liq, aks holda faqat raqam, u ham sig'masa — yozuvsiz
            const full = `Д${o.number} ${fmt(o.length)}×${fmt(o.width)}`, short = `Д${o.number}`;
            const fit = (s: string) => s.length * fs * 1.1 * 0.6 + fs * 0.5 <= o.length;
            const txt = fit(full) ? full : fit(short) ? short : "";
            return txt ? (
              <text x={o.x + o.length / 2} y={o.y + o.width / 2} fontSize={fs * 1.1} fill="#1f3f66" textAnchor="middle"
                dominantBaseline="middle"><title>{full}</title>{txt}</text>
            ) : null;
          })()}
        </g>
      ))}
      {m.placements.map((p, i) => {
        const v = placementView(p);
        const g = grow(p.x, p.y, p.length, p.width);
        return (
          <g key={`p${i}`} className="map-part">
            <rect x={g.x} y={g.y} width={g.l} height={g.w} fill={v.hi ? COLORS.partSel : COLORS.part}
              stroke={COLORS.partStroke} strokeWidth={1} vectorEffect="non-scaling-stroke" data-hi={v.hi ? "1" : undefined} />
            {!thumb && v.part && (ma > 0 || v.part.allow_top > 0 || v.part.allow_bottom > 0 || v.part.allow_left > 0 || v.part.allow_right > 0) && (() => {
              const [il, it, ir, ib] = allowanceInsets(v.part, ma, p.rotated);
              const aw = p.length - il - ir, ah = p.width - it - ib;
              return aw > 0 && ah > 0 ? (
                <rect x={p.x + il} y={p.y + it} width={aw} height={ah} fill="none" stroke={COLORS.partStroke} strokeWidth={fs / 14}
                  strokeDasharray={`${fs * 0.6} ${fs * 0.4}`} pointerEvents="none" data-testid="allowance-rect" />
              ) : null;
            })()}
            {(Object.keys(v.edges) as Side[]).map((sd) => {
              const em = v.edges[sd];
              if (!em) return null;
              const [a, b, c, d] = v.seg[sd];
              return <line key={sd} x1={a} y1={b} x2={c} y2={d} stroke={em.color} strokeWidth={v.sw} />;
            })}
          </g>
        );
      })}
      {/* yozuvlar — barcha detallar va kromka chiziqlaridan KEYIN: raqamlar hech qachon chiziq rangiga bo'yalmaydi (qora) */}
      {!thumb && m.placements.map((p, i) => {
        const v = placementView(p);
        const { edges, name } = v;
        const cx = p.x + p.length / 2, cy = p.y + p.width / 2;
        const num = String(p.part_uid);
        const maxChars = Math.max(3, Math.floor(p.length / (fs * 0.62)));
        // en yozuvi — o'ng chetda raqamlar USTMA-UST (vertikal ustun), sig'masa — 90° burilgan matn
        const wChars = [...`${fmt(p.width)}${mk(edges.left, edges.right)}`.replace(/\s/g, "")];
        const stackFits = p.width > wChars.length * fs * 0.95 + fs * 0.9 && p.length > fs * 1.6;
        const wx = p.x + p.length - fs * 0.3;
        // ID — markazda, o'lcham yozuvlari bilan bir xil o'lchamdagi qalin monospace (detal kattaligiga qarab o'smaydi)
        const showNum = (label === "number" || label === "number_name") && p.length > fs * 0.62 * num.length && p.width > fs * 0.9;
        return (
          <g key={`t${i}`} className="map-part-label" pointerEvents="none" fill="#000" fontFamily={MONO} fontWeight="bold">
            {showNum && (
              <text x={cx} y={cy} fontSize={fs} textAnchor="middle" dominantBaseline="middle">{num}</text>
            )}
            {(label === "name" || label === "number_name") && name && p.width > fs * 3.2 && p.length > fs * 6 && (
              <text x={cx} y={cy + (label === "number_name" ? fs * 1.1 : 0)} fontSize={fs * 0.85} fontWeight="normal"
                fontFamily="Arial, Helvetica, sans-serif" textAnchor="middle" dominantBaseline="middle">{clipText(name, maxChars)}</text>
            )}
            {p.length > `${fmt(p.length)}${mk(edges.top, edges.bottom)}`.length * fs * 0.62 + fs * 0.7 && p.width > fs * 1.4 && (
              // uzunlik — pastki chap burchakda (yozuv detal enidan oshsa — chiqarilmaydi: qo'shni detalga o'tmasin)
              <text x={p.x + fs * 0.35} y={p.y + p.width - fs * 0.35} fontSize={fs}>
                {fmt(p.length)}{mk(edges.top, edges.bottom)}</text>
            )}
            {stackFits ? (
              <text x={wx} y={p.y + fs * 1.05} fontSize={fs} textAnchor="end">
                {wChars.map((ch, k) => <tspan key={k} x={wx} dy={k ? fs * 0.95 : 0}>{ch}</tspan>)}
              </text>
            ) : p.width > fs * 3 && p.length > fs * 1.4 && (
              // vertikal «en»: aylantirilgan matn o'ngga qarab o'sadi — shuning uchun chetdan 1.25·fs ichkarida boshlanadi
              <text x={p.x + p.length - fs * 1.25} y={p.y + fs * 0.35} fontSize={fs}
                transform={`rotate(90 ${p.x + p.length - fs * 1.25} ${p.y + fs * 0.35})`}>
                {fmt(p.width)}{mk(edges.left, edges.right)}</text>
            )}
          </g>
        );
      })}
      {selNodes.map((sel, i) => (
        <rect key={`s${i}`} x={sel.x} y={sel.y} width={sel.l} height={sel.w}
          fill={sel.k === "W" ? "rgba(11,87,208,.18)" : selNodes.length > 1 ? "rgba(11,87,208,.12)" : "none"}
          stroke={COLORS.select} strokeWidth={fs / 2.2} strokeDasharray={`${fs} ${fs / 2}`} pointerEvents="none"
          data-testid="map-sel" />
      ))}
      {band && (
        <rect x={Math.min(band.x0, band.x1)} y={Math.min(band.y0, band.y1)} width={Math.abs(band.x1 - band.x0)}
          height={Math.abs(band.y1 - band.y0)} fill="rgba(11,87,208,.10)" stroke={COLORS.select} strokeWidth={fs / 4}
          strokeDasharray={`${fs / 2} ${fs / 3}`} pointerEvents="none" data-testid="map-band" />
      )}
    </svg>
  );
}
