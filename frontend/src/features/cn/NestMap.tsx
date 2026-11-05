// (CN) Nesting kartasi (SVG): list (kulrang), foydali zona chegarasi (punktir), detallar — haqiqiy kontur (`fill-rule="evenodd"`: tashqi kontur + ichki kesimlar),
// raqam va nom, qoldiqlar (ko'k; detal ichki kesimidagi qoldiq — shtrixli), etiketka o'rni (ixtiyoriy), tanlash / ajratish, masshtab va siljitish.
import { forwardRef, useEffect, useId, useLayoutEffect, useMemo, useRef, useState, type MouseEvent, type ReactNode } from "react";
import i18n from "i18next";
import type { CutMap, Operation, Part } from "../../api/types";
import { COLORS, clipText } from "../cs/MapView";
import { anchorPoint, bboxOf, placementRing, ringPath } from "./cnGeom";
import { uiZoom } from "../../shared/uiZoom";

export interface NestPick {
  /** `map.placements` ichidagi pozitsiya (0 dan); bo'sh joyga bosilsa — null. */
  idx: number | null;
  /** Bosilgan nuqta (list koordinatalarida, mm). */
  x: number; y: number; button: number; shift: boolean; ctrl: boolean; alt: boolean; detail: number;
  client: [number, number];
}

const fmt = (v: number) => String(Math.round(v * 100) / 100);

/** Matn qutiga (w × h) sig'ishi: avval to'liq matn, so'ng qisqasi; avval gorizontal, so'ng 90° burilgan; shrift 60 % gacha kichrayadi. */
function fitText(texts: string[], size: number, w: number, h: number): { text: string; size: number; rot: boolean } | null {
  for (const text of texts) {
    for (const rot of [false, true]) {
      const [aw, ah] = rot ? [h, w] : [w, h];
      const sz = Math.min(size, (aw * 0.94) / (Math.max(1, text.length) * 0.56));
      if (sz >= size * 0.6 && sz * 1.2 <= ah) return { text, size: sz, rot };
    }
  }
  return null;
}

export interface NestMapProps {
  map: CutMap; op: Operation; thumb?: boolean;
  label?: "number" | "name" | "number_name";
  showLabels?: boolean;                       // etiketka o'rni (punktir to'rtburchak)
  highlightPartId?: string | null;            // shu detalning hamma nusxalari ajratiladi (qizil)
  selected?: number[];                        // tanlangan pozitsiyalar (ko'k)
  drag?: { dx: number; dy: number } | null;   // `selected` ni ekranda siljitish (tortish paytida)
  onDown?: (p: NestPick) => void;
  onClick?: (p: NestPick) => void;
  onDouble?: (p: NestPick) => void;
  onContext?: (p: NestPick) => void;
  onMove?: (p: NestPick) => void;
  className?: string; testid?: string;
  children?: ReactNode;                       // qo'shimcha qatlam (list koordinatalarida): masalan, yopishtirish nuqtalari
}

export const NestMap = forwardRef<SVGSVGElement, NestMapProps>(function NestMap(props, fwd) {
  const { map: m, op, thumb } = props;
  const own = useRef<SVGSVGElement | null>(null);
  const setRef = (el: SVGSVGElement | null) => {
    own.current = el;
    if (typeof fwd === "function") fwd(el); else if (fwd) fwd.current = el;
  };
  const uid = useId().replace(/:/g, "");
  const L = m.sheet_length, W = m.sheet_width;
  const fs = Math.max(16, Math.min(L, W) / 42);
  const margin = op.cn?.margin ?? 0;
  const parts = useMemo(() => new Map<string, Part>(op.parts.map((p) => [p.id, p])), [op.parts]);
  const rowNo = useMemo(() => new Map<string, number>(op.parts.map((p, i) => [p.id, i + 1])), [op.parts]);   // «Детали» №, ID emas (CS kartadagidek)
  const label = props.label ?? "number_name";
  const sel = useMemo(() => new Set(props.selected ?? []), [props.selected]);

  // har bir detal uchun: yo'l, o'rovchi o'lcham, yozuv nuqtasi (ichki kesimlardan tashqarida)
  const geo = useMemo(() => m.placements.map((p) => {
    const ring = placementRing(p);
    const holes = p.holes ?? [];
    const [x0, y0, x1, y1] = bboxOf(ring);
    const d = ringPath([ring, ...holes]);
    const simple = !holes.length && ring.length <= 4;
    return { d, bw: x1 - x0, bh: y1 - y0, simple, anchor: thumb ? ([0, 0, 0] as [number, number, number]) : anchorPoint(ring, holes) };
  }), [m.placements, thumb]);

  const pick = (e: MouseEvent<SVGSVGElement>): NestPick | null => {
    const svg = own.current;
    if (!svg) return null;
    const ctm = svg.getScreenCTM();
    if (!ctm) return null;
    const pt = svg.createSVGPoint();
    pt.x = e.clientX; pt.y = e.clientY;
    const q = pt.matrixTransform(ctm.inverse());
    const g = (e.target as Element).closest?.("[data-idx]");
    const idx = g ? Number(g.getAttribute("data-idx")) : null;
    return { idx: idx !== null && Number.isFinite(idx) ? idx : null, x: q.x, y: q.y, button: e.button, shift: e.shiftKey,
      ctrl: e.ctrlKey || e.metaKey, alt: e.altKey, detail: e.detail, client: [e.clientX, e.clientY] };
  };
  const wrap = (fn?: (p: NestPick) => void) => (fn ? (e: MouseEvent<SVGSVGElement>) => { const p = pick(e); if (p) fn(p); } : undefined);
  // tortish paytida sahifa matni belgilanmasin
  const onDown = props.onDown;
  const down = onDown ? (e: MouseEvent<SVGSVGElement>) => { if (e.button === 0) e.preventDefault(); const p = pick(e); if (p) onDown(p); } : undefined;

  const tx = (i: number) => (props.drag && sel.has(i) ? `translate(${props.drag.dx} ${props.drag.dy})` : undefined);
  const hatch = fs * 0.9;
  return (
    <svg ref={setRef} className={props.className ?? "mapsvg"} viewBox={`0 0 ${L} ${W}`} preserveAspectRatio="xMidYMid meet"
      data-testid={props.testid} fontFamily="Arial, Helvetica, sans-serif"
      onMouseDown={down} onClick={wrap(props.onClick)} onDoubleClick={wrap(props.onDouble)} onMouseMove={wrap(props.onMove)}
      onContextMenu={props.onContext ? (e) => { e.preventDefault(); const p = pick(e); if (p) props.onContext!({ ...p, button: 2 }); } : undefined}>
      <defs>
        <pattern id={`ip${uid}`} width={hatch} height={hatch} patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width={hatch} height={hatch} fill={COLORS.remnantSmall} />
          <line x1={0} y1={0} x2={0} y2={hatch} stroke="#3b6ea5" strokeWidth={fs / 7} />
        </pattern>
      </defs>
      <rect x={0} y={0} width={L} height={W} fill={COLORS.waste} stroke="#222" strokeWidth={fs / 5} />
      {margin > 0 && (
        <rect x={margin} y={margin} width={Math.max(0, L - 2 * margin)} height={Math.max(0, W - 2 * margin)} fill="none"
          stroke="#7a8089" strokeWidth={fs / 12} strokeDasharray={`${fs * 0.7} ${fs * 0.45}`} pointerEvents="none" data-testid="nest-zone" />
      )}
      {m.offcuts.filter((o) => o.kind === "remnant").map((o, i) => {
        const inPart = (o.in_part ?? 0) > 0;
        const short = `${i18n.t("rem.p")}${o.number}${inPart ? `⊂${o.in_part}` : ""}`;
        const fit = thumb ? null : fitText([`${short} ${fmt(o.length)}×${fmt(o.width)}`, short], fs * 1.05, o.length, o.width);
        const cx = o.x + o.length / 2, cy = o.y + o.width / 2;
        return (
          <g key={`r${i}`} data-testid={inPart ? "nest-remnant-in-part" : "nest-remnant"}>
            {!thumb && <title>{`${short} · ${fmt(o.length)}×${fmt(o.width)}`}</title>}
            <rect x={o.x} y={o.y} width={o.length} height={o.width}
              fill={inPart ? `url(#ip${uid})` : (o.business ? COLORS.remnant : COLORS.remnantSmall)}
              stroke="#3b6ea5" strokeWidth={fs / 8} strokeDasharray={inPart ? `${fs * 0.5} ${fs * 0.3}` : undefined} />
            {fit && (
              <text x={cx} y={cy} fontSize={fit.size} fill="#1f3f66" textAnchor="middle" dominantBaseline="middle" pointerEvents="none"
                paintOrder="stroke" stroke="rgba(255,255,255,.75)" strokeWidth={fit.size / 5} transform={fit.rot ? `rotate(-90 ${cx} ${cy})` : undefined}>
                {fit.text}</text>
            )}
          </g>
        );
      })}
      {m.placements.map((p, i) => {
        const part = parts.get(p.part_id);
        const g = geo[i];
        const hi = props.highlightPartId && p.part_id === props.highlightPartId;
        const num = String(rowNo.get(p.part_id) ?? p.part_uid);
        const [ax, ay, clear] = g.anchor;
        // yozuv sig'adigan joy: oddiy to'rtburchakda — o'rovchi o'lcham, konturli detalda — markaz nuqtasidan eng yaqin chetgacha masofa
        const availW = g.simple ? g.bw : 2 * clear, availH = g.simple ? g.bh : 2 * clear;
        const big = Math.min(fs * 2, Math.min(availW, availH) * (g.simple ? 0.4 : 0.6), (availW / Math.max(1, num.length)) * 0.9);
        const name = part?.name ?? "";
        const maxChars = Math.floor(availW / (fs * 0.62));
        const showNum = big >= fs * 0.55 && (label === "number" || label === "number_name");
        const showName = (label === "name" || label === "number_name") && !!name && maxChars >= 3 && availH > fs * (g.simple ? 3.2 : 4.4) && (!g.simple || availW > fs * 6);
        return (
          <g key={`p${i}`} className="nest-part" data-idx={i} transform={tx(i)}>
            {!thumb && <title>{`№${p.part_uid}${name ? ` ${name}` : ""} · ${fmt(g.bw)}×${fmt(g.bh)}${p.angle ? ` · ${fmt(p.angle)}°` : ""}`}</title>}
            <path d={g.d} fillRule="evenodd" fill={hi ? COLORS.partSel : COLORS.part} stroke={COLORS.partStroke} strokeWidth={fs / 7}
              strokeLinejoin="round" />
            {!thumb && props.showLabels && p.label && p.label.length >= 4 && (
              <rect x={p.label[0] - p.label[2] / 2} y={p.label[1] - p.label[3] / 2} width={p.label[2]} height={p.label[3]} fill="rgba(255,255,255,.55)"
                stroke="#5a3a0a" strokeWidth={fs / 14} strokeDasharray={`${fs * 0.45} ${fs * 0.3}`} pointerEvents="none"
                transform={p.label[4] ? `rotate(${p.label[4]} ${p.label[0]} ${p.label[1]})` : undefined} data-testid="nest-label-spot" />
            )}
            {!thumb && showNum && (
              <text x={ax} y={ay} fontSize={big} fontWeight="bold" fill="#241400" textAnchor="middle" dominantBaseline="middle"
                pointerEvents="none">{num}</text>
            )}
            {!thumb && showName && (
              <text x={ax} y={ay + (label === "number_name" ? Math.max(big, fs) * 0.95 : 0)} fontSize={fs * 0.85} fill="#3a2600" textAnchor="middle"
                dominantBaseline="middle" pointerEvents="none">{clipText(name, maxChars)}</text>
            )}
          </g>
        );
      })}
      {m.placements.map((p, i) => (sel.has(i) ? (
        <path key={`s${i}`} d={geo[i].d} fillRule="evenodd" fill="rgba(11,87,208,.2)" stroke={COLORS.select} strokeWidth={fs / 2.4}
          strokeLinejoin="round" pointerEvents="none" transform={tx(i)} data-testid="nest-sel" />
      ) : null))}
      {props.children}
    </svg>
  );
});

/** Masshtab (sichqoncha g'ildiragi — kursor ostida) va siljitish (o'rta tugma yoki bo'sh joyni tortish). Bolalar `svg` — 100% × 100%. */
export function MapViewport({ children, className, testid, resetKey, maxZoom = 12, middleOnly = false }: {
  children: ReactNode; className?: string; testid?: string; resetKey?: unknown; maxZoom?: number;
  /** surish faqat o'rta tugma bilan (chap tugma — sahifaning o'z amallari: ramka bilan tanlash, sudrash) */
  middleOnly?: boolean;
}) {
  const [zoom, setZoom] = useState(1);
  const box = useRef<HTMLDivElement>(null);
  const anchor = useRef<{ rx: number; ry: number; mx: number; my: number } | null>(null);
  const suppress = useRef(false);
  useEffect(() => setZoom(1), [resetKey]);
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const h = (e: WheelEvent) => {
      e.preventDefault();
      const r = el.getBoundingClientRect();
      const mx = (e.clientX - r.left) / uiZoom(), my = (e.clientY - r.top) / uiZoom();   // #root px (scroll birligi)
      anchor.current = { rx: (el.scrollLeft + mx) / Math.max(1, el.scrollWidth), ry: (el.scrollTop + my) / Math.max(1, el.scrollHeight), mx, my };
      setZoom((z) => Math.min(maxZoom, Math.max(1, z * (e.deltaY < 0 ? 1.18 : 1 / 1.18))));
    };
    el.addEventListener("wheel", h, { passive: false });
    return () => el.removeEventListener("wheel", h);
  }, [maxZoom]);
  useLayoutEffect(() => {
    const a = anchor.current, el = box.current;
    if (!a || !el) return;
    el.scrollLeft = a.rx * el.scrollWidth - a.mx;
    el.scrollTop = a.ry * el.scrollHeight - a.my;
    anchor.current = null;
  }, [zoom]);
  const onDown = (e: MouseEvent<HTMLDivElement>) => {
    const onPart = !!(e.target as Element).closest?.("[data-idx], [data-nopan]");
    if (!(e.button === 1 || (e.button === 0 && !onPart && !middleOnly))) return;
    const el = box.current;
    if (!el) return;
    if (e.button === 1) e.preventDefault();
    const sx = e.clientX, sy = e.clientY, sl = el.scrollLeft, st = el.scrollTop;
    let moved = false;
    const mv = (ev: globalThis.MouseEvent) => {
      if (!moved && Math.hypot(ev.clientX - sx, ev.clientY - sy) < 5) return;
      moved = true;
      el.scrollLeft = sl - (ev.clientX - sx) / uiZoom();
      el.scrollTop = st - (ev.clientY - sy) / uiZoom();
    };
    const up = () => {
      window.removeEventListener("mousemove", mv);
      window.removeEventListener("mouseup", up);
      if (moved) { suppress.current = true; setTimeout(() => { suppress.current = false; }, 0); }
    };
    window.addEventListener("mousemove", mv);
    window.addEventListener("mouseup", up);
  };
  return (
    <div ref={box} className={`cn-viewport${className ? ` ${className}` : ""}`} data-testid={testid} data-zoom={zoom.toFixed(2)}
      onMouseDownCapture={onDown} onClickCapture={(e) => { if (suppress.current) { e.stopPropagation(); e.preventDefault(); } }}
      onAuxClick={(e) => { if (e.button === 1) e.preventDefault(); }}>
      <div className="cn-zoom" style={{ width: `${zoom * 100}%`, height: `${zoom * 100}%` }}>{children}</div>
    </div>
  );
}
