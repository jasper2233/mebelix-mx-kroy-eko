// Kroy kartasi (SVG): detallar — to'q sariq, chiqindi — kulrang, qoldiq — ko'k; raqam va o'lchamlar.
import { useMemo, useRef, type MouseEvent } from "react";
import type { CutMap, Operation, Part, Project, TreeNode } from "../../api/types";

export const COLORS = {
  part: "#f2a541", partStroke: "#5a3a0a", waste: "#cbced3", remnant: "#86b4e6", remnantSmall: "#b9d3ef",
  trim: "#a9aeb6", select: "#0b57d0", hi: "#d92f2f",
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

const fmt = (v: number) => String(Math.round(v * 100) / 100);

export function MapView(props: {
  map: CutMap; project: Project; op: Operation; thumb?: boolean; label?: "number" | "name" | "number_name";
  showEdges?: boolean; selectedPath?: number[] | null; highlightPartId?: string | null;
  onPick?: (p: PickInfo) => void; className?: string; testid?: string;
}) {
  const { map: m, project, op, thumb } = props;
  const svg = useRef<SVGSVGElement>(null);
  const L = m.sheet_length, W = m.sheet_width;
  const fs = Math.max(16, Math.min(L, W) / 42);
  const parts = useMemo(() => new Map<string, Part>(op.parts.map((p) => [p.id, p])), [op.parts]);
  const edgeOps = useMemo(() => {
    const e = new Map<string, EdgeMark>();
    for (const o of project.operations) if (o.type === "EL" && o.el) e.set(o.id, { color: o.el.color && o.el.color !== "#000000" ? o.el.color : "#1b2733", symbol: o.el.symbol });
    return e;
  }, [project.operations]);
  const root = m.strips?.[0];
  const label = props.label ?? "number_name";

  const pick = (e: MouseEvent<SVGSVGElement>) => {
    if (!props.onPick || !svg.current || !root) return;
    const pt = svg.current.createSVGPoint();
    pt.x = e.clientX; pt.y = e.clientY;
    const ctm = svg.current.getScreenCTM();
    if (!ctm) return;
    const p = pt.matrixTransform(ctm.inverse());
    const path = hitTest(root, p.x, p.y);
    if (path === null) return;
    e.preventDefault();
    props.onPick({ path, node: nodeAt(root, path), x: p.x, y: p.y, button: e.button, alt: e.altKey, ctrl: e.ctrlKey || e.metaKey, shift: e.shiftKey });
  };

  const sel = props.selectedPath && root ? nodeAt(root, props.selectedPath) : null;
  return (
    <svg ref={svg} className={props.className ?? "mapsvg"} viewBox={`0 0 ${L} ${W}`} preserveAspectRatio="xMidYMid meet"
      data-testid={props.testid} onMouseDown={props.onPick ? pick : undefined}
      onContextMenu={props.onPick ? (e) => e.preventDefault() : undefined} fontFamily="Arial, Helvetica, sans-serif">
      <rect x={0} y={0} width={L} height={W} fill={COLORS.trim} stroke="#222" strokeWidth={fs / 5} />
      {root && <rect x={root.x} y={root.y} width={root.l} height={root.w} fill={COLORS.waste} />}
      {m.offcuts.filter((o) => o.kind === "remnant").map((o, i) => (
        <g key={`r${i}`}>
          <rect x={o.x} y={o.y} width={o.length} height={o.width} fill={o.business ? COLORS.remnant : COLORS.remnantSmall}
            stroke="#3b6ea5" strokeWidth={fs / 8} />
          {!thumb && o.length > fs * 4 && o.width > fs * 1.6 && (
            <text x={o.x + o.length / 2} y={o.y + o.width / 2} fontSize={fs * 1.1} fill="#1f3f66" textAnchor="middle"
              dominantBaseline="middle">Д{o.number} {fmt(o.length)}×{fmt(o.width)}</text>
          )}
        </g>
      ))}
      {m.placements.map((p, i) => {
        const part = parts.get(p.part_id);
        const hi = props.highlightPartId && p.part_id === props.highlightPartId;
        const cx = p.x + p.length / 2, cy = p.y + p.width / 2;
        const num = String(p.part_uid);
        const big = Math.min(fs * 2, p.width * 0.45, (p.length / Math.max(1, num.length)) * 0.9);
        let edges: Partial<Record<Side, EdgeMark>> = {};
        if (props.showEdges !== false && part && !thumb) {
          const e: Partial<Record<Side, EdgeMark>> = {};
          (["top", "bottom", "left", "right"] as Side[]).forEach((s) => {
            const id = part[`edge_${s}`]?.op_id;
            const em = id ? edgeOps.get(id) : undefined;
            if (em) e[s] = em;
          });
          edges = rotateEdges(e, p.rotated);
        }
        const sw = fs / 3, ins = sw / 2 + fs / 10;
        const seg: Record<Side, [number, number, number, number]> = {
          top: [p.x + ins, p.y + ins, p.x + p.length - ins, p.y + ins],
          bottom: [p.x + ins, p.y + p.width - ins, p.x + p.length - ins, p.y + p.width - ins],
          left: [p.x + ins, p.y + ins, p.x + ins, p.y + p.width - ins],
          right: [p.x + p.length - ins, p.y + ins, p.x + p.length - ins, p.y + p.width - ins],
        };
        const name = part?.name ?? "";
        const maxChars = Math.max(3, Math.floor(p.length / (fs * 0.62)));
        return (
          <g key={`p${i}`} className="map-part">
            <rect x={p.x} y={p.y} width={p.length} height={p.width} fill={COLORS.part}
              stroke={hi ? COLORS.hi : COLORS.partStroke} strokeWidth={hi ? fs / 2.5 : fs / 7} />
            {(Object.keys(edges) as Side[]).map((s) => {
              const em = edges[s];
              if (!em) return null;
              const [a, b, c, d] = seg[s];
              return <line key={s} x1={a} y1={b} x2={c} y2={d} stroke={em.color} strokeWidth={sw} />;
            })}
            {!thumb && (
              <>
                {(label === "number" || label === "number_name") && (
                  <text x={cx} y={cy} fontSize={big} fontWeight="bold" fill="#241400" textAnchor="middle" dominantBaseline="middle">{num}</text>
                )}
                {(label === "name" || label === "number_name") && name && p.width > fs * 3.2 && p.length > fs * 6 && (
                  <text x={cx} y={cy + (label === "number_name" ? big * 0.9 : 0)} fontSize={fs * 0.85} fill="#3a2600"
                    textAnchor="middle" dominantBaseline="middle">{name.slice(0, maxChars)}</text>
                )}
                {p.length > fs * 3 && p.width > fs * 1.4 && (
                  <text x={p.x + fs * 0.35} y={p.y + p.width - fs * 0.35} fontSize={fs} fill="#241400">{fmt(p.length)}</text>
                )}
                {p.width > fs * 3 && p.length > fs * 1.4 && (
                  <text x={p.x + p.length - fs * 0.4} y={p.y + fs * 0.35} fontSize={fs} fill="#241400"
                    transform={`rotate(90 ${p.x + p.length - fs * 0.4} ${p.y + fs * 0.35})`}>{fmt(p.width)}</text>
                )}
              </>
            )}
          </g>
        );
      })}
      {sel && (
        <rect x={sel.x} y={sel.y} width={sel.l} height={sel.w} fill={sel.k === "W" ? "rgba(11,87,208,.18)" : "none"}
          stroke={COLORS.select} strokeWidth={fs / 2.2} strokeDasharray={`${fs} ${fs / 2}`} pointerEvents="none" />
      )}
    </svg>
  );
}
