// CL kroy kartasi (1D, SVG): polosa gorizontal; detallar — to'q sariq (raqam + uzunlik), otxod / деловой otxod — ko'k (Д№ + uzunlik),
// torsovka zonalari — kulrang, propil — qora chiziq, kromka (ОВ/ОН — usti/osti, ОЛ/ОП — uchlari) — EL rangida.
// Balandlik qoidasi backend `services/cl_render.py` bilan bir xil (clHooks.viewHeight).
import { useMemo, useRef, type MouseEvent } from "react";
import type { CutMap, Operation, Part, Project } from "../../api/types";
import { COLORS, clipText } from "../cs/MapView";
import { viewHeight } from "./clHooks";

type Side = "top" | "bottom" | "left" | "right";
interface EdgeMark { color: string; symbol: string }

export interface StripPick {
  /** bosilgan detalning kartadagi tartib raqami (0 dan); bo'sh joy — null */
  index: number | null;
  /** bo'sh joyga bosilganda: shu nuqtadan chapda nechta detal bor (qo'yish pozitsiyasi) */
  insertAt: number;
  x: number; button: number; shift: boolean; ctrl: boolean; alt: boolean;
}

const fmt = (v: number) => String(Math.round(v * 100) / 100);

/** Karta geometriyasi: (T_boshi, T_oxiri) mm — kartaga yozilgan (CLE da o'zgargan bo'lishi mumkin), bo'lmasa operatsiya qiymati. */
export function mapTrims(m: CutMap, op: Operation): [number, number] {
  const cl = op.cl;
  const trim = cl?.trim ?? 0;
  const ts = m.trim_length ?? trim;
  const te = m.end_offset_right ?? (cl?.end_offset ?? trim);
  return [ts, te];
}

export function StripMap(props: {
  map: CutMap; project: Project; op: Operation; thumb?: boolean; label?: "number" | "name" | "number_name";
  showEdges?: boolean; selectedIndex?: number | null; highlightPartId?: string | null;
  onPick?: (p: StripPick) => void; onPart?: (partId: string | null, double: boolean) => void;
  className?: string; testid?: string;
}) {
  const { map: m, project, op, thumb } = props;
  const svg = useRef<SVGSVGElement>(null);
  const L = m.sheet_length, W = m.sheet_width;
  const k = op.cl?.kerf ?? 3;
  const fs = Math.max(L / 70, 10);
  const H = viewHeight(L, W, fs);
  const [ts, te] = mapTrims(m, op);
  const label = props.label ?? "number_name";
  const parts = useMemo(() => new Map<string, Part>(op.parts.map((p) => [p.id, p])), [op.parts]);
  const edgeOps = useMemo(() => {
    const e = new Map<string, EdgeMark>();
    for (const o of project.operations) if (o.type === "EL" && o.el) e.set(o.id, { color: o.el.color && o.el.color !== "#000000" ? o.el.color : "#1b2733", symbol: o.el.symbol });
    return e;
  }, [project.operations]);
  const pls = m.placements;
  const cutW = Math.max(k, fs / 8);
  const cuts: number[] = [];
  if (ts > 0) cuts.push(ts);
  for (const p of pls) cuts.push(p.x + p.length);
  if (op.cl?.waste_incl_trim && te > 0) for (const o of m.offcuts) if (o.kind === "remnant") cuts.push(o.x + o.length);

  const toX = (e: MouseEvent<SVGSVGElement>): number | null => {
    if (!svg.current) return null;
    const pt = svg.current.createSVGPoint();
    pt.x = e.clientX; pt.y = e.clientY;
    const ctm = svg.current.getScreenCTM();
    return ctm ? pt.matrixTransform(ctm.inverse()).x : null;
  };
  const hit = (x: number): number | null => {
    const i = pls.findIndex((p) => x >= p.x - 0.01 && x <= p.x + p.length + 0.01);
    return i >= 0 ? i : null;
  };
  const down = (e: MouseEvent<SVGSVGElement>) => {
    if (!props.onPick) return;
    const x = toX(e);
    if (x === null) return;
    e.preventDefault();
    props.onPick({ index: hit(x), insertAt: pls.filter((p) => p.x + p.length / 2 < x).length, x, button: e.button,
      shift: e.shiftKey, ctrl: e.ctrlKey || e.metaKey, alt: e.altKey });
  };
  const click = (e: MouseEvent<SVGSVGElement>) => {
    if (!props.onPart) return;
    const x = toX(e);
    if (x === null) return;
    const i = hit(x);
    props.onPart(i === null ? null : pls[i].part_id, e.detail >= 2);
  };

  return (
    <svg ref={svg} className={props.className ?? "mapsvg cl-strip"} viewBox={`0 0 ${L} ${H}`} preserveAspectRatio="xMidYMid meet"
      data-testid={props.testid} onMouseDown={props.onPick ? down : undefined} onClick={props.onPart ? click : undefined}
      onContextMenu={props.onPick ? (e) => e.preventDefault() : undefined} fontFamily="Arial, Helvetica, sans-serif">
      <rect x={0} y={0} width={L} height={H} fill={COLORS.trim} stroke="#222" strokeWidth={1} vectorEffect="non-scaling-stroke" />
      <rect x={ts} y={0} width={Math.max(0, L - ts - te)} height={H} fill={COLORS.waste} />
      {m.offcuts.filter((o) => o.kind === "remnant").map((o, i) => (
        <g key={`r${i}`}>
          <rect x={o.x} y={0} width={o.length} height={H} fill={o.business ? COLORS.remnant : COLORS.remnantSmall}
            stroke="#3b6ea5" strokeWidth={1} vectorEffect="non-scaling-stroke" />
          {!thumb && o.length > fs * 4 && (
            <>
              <text x={o.x + o.length / 2} y={H * 0.28} fontSize={fs} fill="#1f3f66" textAnchor="middle" dominantBaseline="middle">Д{o.number}</text>
              <text x={o.x + o.length / 2} y={H * 0.56} fontSize={fs} fill="#1f3f66" textAnchor="middle" dominantBaseline="middle">{fmt(o.length)}</text>
            </>
          )}
        </g>
      ))}
      {pls.map((p, i) => {
        const part = parts.get(p.part_id);
        const hi = props.highlightPartId && p.part_id === props.highlightPartId;
        const selected = props.selectedIndex === i;
        const cx = p.x + p.length / 2;
        const num = String(p.part_uid);
        const edges: Partial<Record<Side, EdgeMark>> = {};
        if (props.showEdges !== false && part && !thumb) {
          (["top", "bottom", "left", "right"] as Side[]).forEach((s) => {
            const id = part[`edge_${s}`]?.op_id;
            const em = id ? edgeOps.get(id) : undefined;
            if (em) edges[s] = em;
          });
        }
        const ew = fs / 4;
        const seg: Record<Side, [number, number, number, number]> = {
          top: [p.x, ew / 2, p.x + p.length, ew / 2], bottom: [p.x, H - ew / 2, p.x + p.length, H - ew / 2],
          left: [p.x + ew / 2, 0, p.x + ew / 2, H], right: [p.x + p.length - ew / 2, 0, p.x + p.length - ew / 2, H],
        };
        const wide = p.length * (props.thumb ? 0 : 1);
        return (
          <g key={`p${i}`} className="map-part" data-testid={props.testid ? `${props.testid}-p${i}` : undefined}>
            <rect x={p.x} y={0} width={p.length} height={H} fill={hi ? COLORS.partSel : COLORS.part}
              stroke={COLORS.partStroke} strokeWidth={1} vectorEffect="non-scaling-stroke" />
            {(Object.keys(edges) as Side[]).map((s) => {
              const em = edges[s];
              if (!em) return null;
              const [a, b, c, d] = seg[s];
              return <line key={s} x1={a} y1={b} x2={c} y2={d} stroke={em.color} strokeWidth={ew} />;
            })}
            {!thumb && (
              <>
                {(label === "number" || label === "number_name") && wide > fs * (num.length + 1) && (
                  <text x={cx} y={H * 0.28} fontSize={fs * 1.15} fontWeight="bold" fill="#241400" textAnchor="middle"
                    dominantBaseline="middle">{num}</text>
                )}
                {wide > fs * (fmt(p.length).length * 0.6 + 1) && (
                  <text x={cx} y={H * 0.56} fontSize={fs} fill="#241400" textAnchor="middle" dominantBaseline="middle">{fmt(p.length)}</text>
                )}
                {(label === "name" || label === "number_name") && part?.name && wide > fs * 8 && (
                  <text x={cx} y={H * 0.82} fontSize={fs * 0.8} fill="#3a2600" textAnchor="middle" dominantBaseline="middle">
                    {clipText(part.name, Math.max(3, Math.floor(wide / (fs * 0.6))))}</text>
                )}
              </>
            )}
            {selected && (
              <rect x={p.x} y={0} width={p.length} height={H} fill="none" stroke={COLORS.select} strokeWidth={fs / 2.5}
                strokeDasharray={`${fs} ${fs / 2}`} pointerEvents="none" data-testid="strip-selected" />
            )}
          </g>
        );
      })}
      {cuts.map((c, i) => <rect key={`c${i}`} x={c} y={0} width={cutW} height={H} fill="#111" pointerEvents="none" />)}
    </svg>
  );
}
