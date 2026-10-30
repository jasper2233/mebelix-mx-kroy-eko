// Kroy kartasi (SVG): detallar — to'q sariq (#ffa500), chiqindi va torsovka — neytral kulrang, qoldiq — ko'k; raqam va o'lchamlar.
// Tanlangan detal — to'qroq to'q sariq to'ldirish (kontur o'zgarmaydi); ID va o'lchamlar — bir xil kichik qalin monospace.
// Tahrir rejimida (onPick/onBand): ko'p tanlash ajratilgan manzillar (`selectedPaths`) va sichqoncha ramkasi (CSE-019).
import { useEffect, useMemo, useRef, useState, type MouseEvent } from "react";
import i18n from "i18next";
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

function partLeaves(n: TreeNode, out: TreeNode[] = []): TreeNode[] {
  for (const c of n.c ?? []) { if (c.k === "P") out.push(c); else if (c.k === "C") partLeaves(c, out); }
  return out;
}

/** Detal bitta bo'sh katakka sig'maganda — bosilgan katakni qoplaydigan, boshqa detallarga (propil bilan) tegmaydigan joy
 * (server `editor.free_anchors` bilan bir xil burchaklar). Topilmasa null. */
export function mergedSpot(root: TreeNode, leaf: TreeNode, l: number, w: number, kerf: number,
  pt?: { x: number; y: number }): { x: number; y: number } | null {
  const e = 0.01;
  const xs = [leaf.x, leaf.x + leaf.l - l, root.x, root.x + root.l - l];
  const ys = [leaf.y, leaf.y + leaf.w - w, root.y, root.y + root.w - w];
  if (pt) {
    xs.push(Math.min(Math.max(pt.x - l / 2, root.x), root.x + root.l - l));
    ys.push(Math.min(Math.max(pt.y - w / 2, root.y), root.y + root.w - w));
  }
  const parts = partLeaves(root);
  for (const x of xs) for (const y of ys) {
    if (x > leaf.x + leaf.l - e || x + l < leaf.x + e || y > leaf.y + leaf.w - e || y + w < leaf.y + e) continue;
    if (x < root.x - e || y < root.y - e || x + l > root.x + root.l + e || y + w > root.y + root.w + e) continue;
    if (parts.some((p) => x < p.x + p.l + kerf - e && p.x < x + l + kerf - e && y < p.y + p.w + kerf - e && p.y < y + w + kerf - e)) continue;
    return { x, y };
  }
  return null;
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
/** Karta yozuvlari (detal raqami, o'lchamlar, qoldiq) ekrandagi balandligi, px — hamma kartada bir xil */
const MAP_FONT_PX = 16;      // onlayn tizim kartasidagi bilan bir xil (o'lchab solishtirilgan, 2026-10-19)
const MAP_REF_SCALE = 0.3;   // px/mm: shundan kichik masshtabda yozuvlar karta bilan birga kichrayadi (1904 px oynada ≈ 0.41)
const MAP_FONT_MIN_PX = 5;

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

const RP = () => i18n.t("rem.p");      // qoldiq raqami prefiksi («Д5» / «Q5») — tanlangan tilda

export function MapView(props: {
  map: CutMap; project: Project; op: Operation; thumb?: boolean; label?: "number" | "name" | "number_name";
  showEdges?: boolean; selectedPath?: number[] | null; selectedPaths?: number[][]; highlightPartId?: string | null;
  onPick?: (p: PickInfo) => void; className?: string; testid?: string;
  /** O'lcham yoniga kromka harflarini qo'shish (chop/hisobot ko'rinishi); ekran kartasida — standart o'chiq. */
  edgeLetters?: boolean;
  /** Chap tugma bilan sudralganda ramka: berilsa — bosish `mouseup` da hal qilinadi (ramka va bosishni ajratish uchun). */
  onBand?: (b: BandInfo) => void;
  /** Ko'rish rejimi: detalni bosish (double — ikki marta bosish); bo'sh joy — null. */
  /** `right` — o'ng tugma: onlayn tizimdagidek detalni tanlaydi (menyu ochilmaydi) */
  onPart?: (partId: string | null, double: boolean, right?: boolean) => void;
  /** Tahrir: ro'yxatdan tanlangan detal «sharpasi» (Shift bosilganda kursor ortidan yuradi; o'lcham — burilgan holatda) */
  ghost?: { l: number; w: number } | null;
  /** Tahrir: Shift + sudrash — kartadagi detalni boshqa bo'sh joyga ko'chirish (tushirilgan nuqta, list koordinatalarida) */
  onMove?: (path: number[], q: { x: number; y: number }) => void;
  /** sudralayotgan detal Ctrl bilan aylantirilganmi (sharpa o'lchami almashadi) */
  ghostRot?: boolean;
  /** Tahrir oynasi: bo'sh (chiqindi) joylarda kichik kulrang o'lcham yozuvlari (onlayn tizim muharriridagidek) */
  wasteDims?: boolean;
}) {
  const { map: m, project, op, thumb } = props;
  const mk = props.edgeLetters ? marks : () => "";                      // ekranda — faqat raqam (QA #18)
  const svg = useRef<SVGSVGElement>(null);
  const L = m.sheet_length, W = m.sheet_width;
  // yozuvlar: ekranda har kartada bir xil (≈13 px) — list o'lchamidan qat'i nazar (kichik qoldiq listida ham sonlar kattalashmaydi);
  // o'lcham hali ma'lum bo'lmasa / miniatyurada — list o'lchamidan
  const [scale, setScale] = useState<number | null>(null);
  useEffect(() => {
    const el = svg.current;
    if (thumb || !el || typeof ResizeObserver === "undefined") return;
    const upd = () => { const w = el.clientWidth, h = el.clientHeight; if (w > 0 && h > 0) setScale(Math.min(w / L, h / W)); };
    upd();
    const ro = new ResizeObserver(upd);
    ro.observe(el);
    return () => ro.disconnect();
  }, [L, W, thumb]);
  // oyna kichrayib karta odatdagidan (≈ MAP_REF_SCALE px/mm) kichik chizilsa — yozuvlar ham u bilan birga mutanosib kichrayadi
  // (foydalanuvchi: kartalar va yozuvlar «sinxron kichrayadi»); odatdagi va katta oynada — o'zgarmas MAP_FONT_PX
  const fontPx = scale ? Math.max(MAP_FONT_MIN_PX, Math.min(MAP_FONT_PX, MAP_FONT_PX * scale / MAP_REF_SCALE)) : MAP_FONT_PX;
  const fs = !thumb && scale ? fontPx / scale : Math.max(16, Math.min(L, W) / 34);
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
  // Shift + sudrash (detal ko'chirish) va sharpa: kursor nuqtasi list koordinatalarida
  const [hover, setHover] = useState<{ x: number; y: number } | null>(null);
  const [drag, setDrag] = useState<{ path: number[]; node: TreeNode } | null>(null);
  const startDrag = (e: MouseEvent<SVGSVGElement>): boolean => {
    if (!props.onMove || !root || e.button !== 0 || !e.shiftKey) return false;
    const start = toSvg(e.clientX, e.clientY);
    const path = start ? hitTest(root, start.x, start.y) : null;
    const node = path ? nodeAt(root, path) : null;
    if (!start || !path || !node || node.k !== "P") return false;
    e.preventDefault();
    const sx = e.clientX, sy = e.clientY;
    let moved = false;
    setDrag({ path, node }); setHover(start);
    const move = (ev: globalThis.MouseEvent) => {
      if (!moved && Math.hypot(ev.clientX - sx, ev.clientY - sy) < 5) return;
      moved = true;
      const q = toSvg(ev.clientX, ev.clientY);
      if (q) setHover(q);
    };
    const up = (ev: globalThis.MouseEvent) => {
      cleanup.current?.();
      setDrag(null);
      const q = toSvg(ev.clientX, ev.clientY) ?? start;
      if (moved) props.onMove?.(path, q); else pickAt(start, ev);
    };
    cleanup.current = () => {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
      cleanup.current = null;
    };
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
    return true;
  };
  // sharpa: kursor ostidagi bo'sh joyning burchagiga (kesish chizig'iga) yopishadi; sig'masa — qizil
  const ghostRect = useMemo(() => {
    if (!root || !hover) return null;
    const size = drag ? (props.ghostRot ? [drag.node.w, drag.node.l] : [drag.node.l, drag.node.w])
      : props.ghost ? [props.ghost.l, props.ghost.w] : null;
    if (!size) return null;
    const path = hitTest(root, hover.x, hover.y);
    let leaf = path ? nodeAt(root, path) : null;
    if (drag && path && samePath(path.slice(0, drag.path.length), drag.path)) leaf = drag.node;   // o'z joyi ham bo'sh
    const free = !!leaf && (leaf.k === "W" || leaf === drag?.node);
    if (free && leaf) {
      const fits = size[0] <= leaf.l + 0.01 && size[1] <= leaf.w + 0.01;
      // birinchi kesim yo'nalishi kursor bilan tanlanadi (foydalanuvchi qarori): o'ng tomonda — gorizontal, pastda — vertikal
      const vertical = hover.x - (leaf.x + size[0]) <= hover.y - (leaf.y + size[1]);
      if (!fits && !drag) {
        // bitta katakka sig'masa: qo'shni bo'sh kataklar birlashgan joy (server kesish daraxtini detallar joyidan qayta quradi);
        // bo'lmasa — maydon yetsa list qayta joylanadi (sariq)
        const m = mergedSpot(root, leaf, size[0], size[1], op.cs_cut?.kerf ?? 0, hover);
        if (m) return { x: m.x, y: m.y, l: size[0], w: size[1], ok: true, merged: true };
        const used = partLeaves(root).reduce((a, p) => a + p.l * p.w, 0);
        if (used + size[0] * size[1] <= root.l * root.w + 0.01)
          return { x: leaf.x, y: leaf.y, l: size[0], w: size[1], ok: false, maybe: true };
      }
      return { x: leaf.x, y: leaf.y, l: size[0], w: size[1], ok: fits, leaf, vertical };
    }
    return { x: hover.x - size[0] / 2, y: hover.y - size[1] / 2, l: size[0], w: size[1], ok: false };
  }, [root, hover, drag, props.ghost, props.ghostRot]);
  const track = !!props.onMove || props.ghost !== undefined;
  const onHover = (e: MouseEvent<SVGSVGElement>) => {
    if (!track || drag) return;
    if (!props.ghost) { if (hover) setHover(null); return; }
    setHover(toSvg(e.clientX, e.clientY));
  };

  const onDown = (e: MouseEvent<SVGSVGElement>) => {
    if (!props.onPick) return;
    if (startDrag(e)) return;
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
    const right = e.type === "contextmenu";
    if (right) e.preventDefault();
    props.onPart(hit ? hit.part_id : null, !right && e.detail >= 2, right);
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

  // Arra kesish chiziqlari (gilyotina): har bir kesish OTA hududining boshidan oxirigacha chiziladi — chiqindi (kulrang)
  // ustidan ham o'tadi, detal chetida to'xtamaydi; torsovka chiziqlari — butun list bo'ylab. Kesish daraxtidan (`strips`).
  const cutLines = useMemo(() => {
    const out: [number, number, number, number][] = [];
    if (!root || thumb) return out;
    const eps = 0.01;
    if (root.x > eps) out.push([root.x, 0, root.x, W]);
    if (root.x + root.l < L - eps) out.push([root.x + root.l, 0, root.x + root.l, W]);
    if (root.y > eps) out.push([root.x, root.y, root.x + root.l, root.y]);
    if (root.y + root.w < W - eps) out.push([root.x, root.y + root.w, root.x + root.l, root.y + root.w]);
    const walk = (n: TreeNode, depth: number) => {
      if (depth > 64 || n.k !== "C" || !n.c) return;
      const kids = n.c;
      kids.forEach((c, i) => {
        if (n.a === "x") {
          const e = Math.min(c.x + c.l + k2, n.x + n.l);         // propil o'rtasi — vertikal kesish (ota bo'yi bo'ylab)
          if (i < kids.length - 1 || c.x + c.l < n.x + n.l - eps) out.push([e, n.y, e, n.y + n.w]);
        } else {
          const e = Math.min(c.y + c.w + k2, n.y + n.w);         // propil o'rtasi — gorizontal kesish (ota eni bo'ylab)
          if (i < kids.length - 1 || c.y + c.w < n.y + n.w - eps) out.push([n.x, e, n.x + n.l, e]);
        }
        walk(c, depth + 1);
      });
    };
    walk(root, 0);
    return out;
  }, [root, thumb, L, W, k2]);

  // tanlangan tugunlar (bitta `selectedPath` yoki ko'p tanlash `selectedPaths`)
  const selNodes = useMemo(() => {
    if (!root) return [] as TreeNode[];
    const ps = props.selectedPaths ?? (props.selectedPath ? [props.selectedPath] : []);
    return ps.map((p) => nodeAt(root, p)).filter((n): n is TreeNode => !!n);
  }, [root, props.selectedPath, props.selectedPaths]);
  return (
    <svg ref={svg} className={props.className ?? "mapsvg"} viewBox={`0 0 ${L} ${W}`} preserveAspectRatio="xMidYMid meet"
      data-testid={props.testid} onMouseDown={props.onPick ? onDown : undefined} onClick={props.onPart ? clickPart : undefined}
      onContextMenu={props.onPick ? (e) => e.preventDefault() : props.onPart ? clickPart : undefined} fontFamily="Arial, Helvetica, sans-serif"
      onMouseMove={track ? onHover : undefined} onMouseLeave={track ? () => { if (!drag) setHover(null); } : undefined}>
      <rect x={0} y={0} width={L} height={W} fill={COLORS.trim} stroke="#222" strokeWidth={1} vectorEffect="non-scaling-stroke" />
      {root && <rect x={root.x} y={root.y} width={root.l} height={root.w} fill={COLORS.waste} />}
      {m.offcuts.filter((o) => o.kind === "remnant").map((o, i) => (
        <g key={`r${i}`}>
          <rect x={o.x} y={o.y} width={o.length} height={o.width} fill={o.business ? COLORS.remnant : COLORS.remnantSmall}
            stroke="#3b6ea5" strokeWidth={1} vectorEffect="non-scaling-stroke" />
          {!thumb && o.width > fs * 1.6 && (() => {
            // qoldiq yozuvi: to'liq («Д3 600×400») sig'sa — to'liq, aks holda faqat raqam, u ham sig'masa — yozuvsiz
            const full = `${RP()}${o.number} ${fmt(o.length)}×${fmt(o.width)}`, short = `${RP()}${o.number}`;
            const fit = (s: string) => s.length * fs * 0.6 + fs * 0.5 <= o.length;
            const txt = fit(full) ? full : fit(short) ? short : "";
            return txt ? (
              <text x={o.x + o.length / 2} y={o.y + o.width / 2} fontSize={fs} fill="#1f3f66" textAnchor="middle"
                fontFamily={MONO} fontWeight="bold"
                dominantBaseline="middle"><title>{full}</title>{txt}</text>
            ) : null;
          })()}
        </g>
      ))}
      <g className="map-cuts" pointerEvents="none" data-testid="map-cuts">
        {cutLines.map(([x1, y1, x2, y2], i) => (
          <line key={`c${i}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke={COLORS.partStroke} strokeWidth={1} vectorEffect="non-scaling-stroke" />
        ))}
      </g>
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
        const stackFits = p.width > wChars.length * fs * 0.95 + fs * 0.9 && p.length > fs * 0.9;   // ingichka (≈1 belgi) detalda ham ustma-ust
        const wx = p.x + p.length - fs * 0.3;
        // uzunlik gorizontal sig'masa — tik (ustma-ust); en ham tik bo'lsa ikkalasiga joy yetishi kerak
        const lChars = [...`${fmt(p.length)}${mk(edges.top, edges.bottom)}`.replace(/\s/g, "")];
        const lStackFits = p.length > fs * 0.9 && p.width > (lChars.length + (stackFits ? wChars.length : 0)) * fs * 0.95 + fs * 1.6;
        // ID — markazda, o'lcham yozuvlari bilan bir xil o'lchamdagi qalin monospace (detal kattaligiga qarab o'smaydi)
        const showNum = (label === "number" || label === "number_name") && p.length > fs * 0.62 * num.length && p.width > fs * 0.9;
        // ingichka polosa (balandligi ~1 qator): onlayn tizimdagidek bitta qatorda — chapda uzunlik, markazda raqam, o'ngda en
        if (p.width < fs * 1.4 && p.width >= fs * 0.7) {
          const ls = `${fmt(p.length)}${mk(edges.top, edges.bottom)}`, ws = `${fmt(p.width)}${mk(edges.left, edges.right)}`;
          const wantNum = label === "number" || label === "number_name";
          const fits = (ls.length + ws.length + (wantNum ? num.length : 0)) * fs * 0.62 + fs * 2 <= p.length;
          const yy = p.y + p.width / 2;
          return (
            <g key={`t${i}`} className="map-part-label" pointerEvents="none" fill="#000" fontFamily={MONO} fontWeight="bold" data-testid="dim-row">
              {fits && <text x={p.x + fs * 0.3} y={yy} fontSize={fs} dominantBaseline="middle">{ls}</text>}
              {wantNum && p.length > fs * 0.62 * num.length && <text x={cx} y={yy} fontSize={fs} textAnchor="middle" dominantBaseline="middle">{num}</text>}
              {fits && <text x={p.x + p.length - fs * 0.3} y={yy} fontSize={fs} textAnchor="end" dominantBaseline="middle">{ws}</text>}
            </g>
          );
        }
        return (
          <g key={`t${i}`} className="map-part-label" pointerEvents="none" fill="#000" fontFamily={MONO} fontWeight="bold">
            {showNum && (
              <text x={cx} y={cy} fontSize={fs} textAnchor="middle" dominantBaseline="middle">{num}</text>
            )}
            {(label === "name" || label === "number_name") && name && p.width > fs * 3.2 && p.length > fs * 6 && (
              <text x={cx} y={cy + (label === "number_name" ? fs * 1.1 : 0)} fontSize={fs * 0.85} fontWeight="normal"
                fontFamily="Arial, Helvetica, sans-serif" textAnchor="middle" dominantBaseline="middle">{clipText(name, maxChars)}</text>
            )}
            {p.length > `${fmt(p.length)}${mk(edges.top, edges.bottom)}`.length * fs * 0.62 + fs * 0.7 && p.width > fs * 1.4 ? (
              // uzunlik — pastki chap burchakda (yozuv detal enidan oshsa — chiqarilmaydi: qo'shni detalga o'tmasin)
              <text x={p.x + fs * 0.35} y={p.y + p.width - fs * 0.35} fontSize={fs}>
                {fmt(p.length)}{mk(edges.top, edges.bottom)}</text>
            ) : lStackFits && (
              // tik ingichka detal (masalan 101×1430): uzunlik ham tik — pastki-chap burchakda, raqamlar ustma-ust
              <text x={p.x + fs * 0.3} y={p.y + p.width - fs * 0.35 - (lChars.length - 1) * fs * 0.95} fontSize={fs} data-testid="dim-l-v">
                {lChars.map((ch, k) => <tspan key={k} x={p.x + fs * 0.3} dy={k ? fs * 0.95 : 0}>{ch}</tspan>)}
              </text>
            )}
            {stackFits ? (
              <text x={wx} y={p.y + fs * 1.05} fontSize={fs} textAnchor="end">
                {wChars.map((ch, k) => <tspan key={k} x={wx} dy={k ? fs * 0.95 : 0}>{ch}</tspan>)}
              </text>
            ) : p.width > fs * 1.15 && p.length > (wChars.length + `${fmt(p.length)}${mk(edges.top, edges.bottom)}`.length) * fs * 0.62 + fs * 1.5 ? (
              // ingichka uzun detal (masalan 2325×140): en — yuqori-o'ng burchakda GORIZONTAL (uzunlik pastki-chapda qoladi)
              <text x={wx} y={p.y + fs * 0.95} fontSize={fs} textAnchor="end" data-testid="dim-w-h">
                {fmt(p.width)}{mk(edges.left, edges.right)}</text>
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
      {ghostRect && (props.ghost || drag) && (
        <rect x={ghostRect.x} y={ghostRect.y} width={ghostRect.l} height={ghostRect.w} pointerEvents="none" data-testid="map-ghost"
          data-state={ghostRect.ok ? "ok" : "maybe" in ghostRect && ghostRect.maybe ? "maybe" : "no"}
          fill={ghostRect.ok ? "rgba(46,160,67,.45)" : "maybe" in ghostRect && ghostRect.maybe ? "rgba(230,160,20,.45)" : "rgba(220,53,69,.40)"}
          stroke={ghostRect.ok ? "#1e7a34" : "maybe" in ghostRect && ghostRect.maybe ? "#a86b00" : "#b02a37"}
          strokeWidth={fs / 5} strokeDasharray={`${fs / 2} ${fs / 3}`} />
      )}
      {/* kesim chiziqlari oldindan: birinchi (to'liq) kesim — qalin, ikkinchisi — ingichka (yashil) */}
      {ghostRect?.ok && "leaf" in ghostRect && ghostRect.leaf && props.ghost && !drag && (() => {
        const g = ghostRect, lf = g.leaf, xr = g.x + g.l, yb = g.y + g.w;
        const [a, b] = g.vertical
          ? [[xr, lf.y, xr, lf.y + lf.w], [g.x, yb, xr, yb]]
          : [[g.x, yb, lf.x + lf.l, yb], [xr, g.y, xr, yb]];
        return (
          <g pointerEvents="none" data-testid="map-ghost-cut" data-dir={g.vertical ? "V" : "H"}>
            <line x1={a[0]} y1={a[1]} x2={a[2]} y2={a[3]} stroke="#1e9e3a" strokeWidth={fs / 3} />
            <line x1={b[0]} y1={b[1]} x2={b[2]} y2={b[3]} stroke="#1e9e3a" strokeWidth={fs / 6} />
          </g>
        );
      })()}
      {props.wasteDims && root && <WasteDims root={root} fs={fs * 0.7} />}
      {band && (
        <rect x={Math.min(band.x0, band.x1)} y={Math.min(band.y0, band.y1)} width={Math.abs(band.x1 - band.x0)}
          height={Math.abs(band.y1 - band.y0)} fill="rgba(11,87,208,.10)" stroke={COLORS.select} strokeWidth={fs / 4}
          strokeDasharray={`${fs / 2} ${fs / 3}`} pointerEvents="none" data-testid="map-band" />
      )}
    </svg>
  );
}

/** Bo'sh (W) barglar o'lchamlari: uzunlik — pastki-chapda, en — o'ngda ustma-ust; sig'maganlari chiqmaydi. */
function WasteDims({ root, fs }: { root: TreeNode; fs: number }) {
  const out: TreeNode[] = [];
  const walk = (n: TreeNode) => (n.c ?? []).forEach((c) => { if (c.k === "W") out.push(c); else if (c.k === "C") walk(c); });
  walk(root);
  const f = (v: number) => String(Math.round(v * 10) / 10);
  return (
    <g className="map-waste-dims" pointerEvents="none" fill="#555" fontFamily={MONO} data-testid="waste-dims">
      {out.map((w, i) => {
        const ls = f(w.l), ws = [...f(w.w)];
        const lFit = w.l > ls.length * fs * 0.62 + fs * 0.6 && w.w > fs * 1.2;
        const wFit = w.w > ws.length * fs * 0.95 + fs * (lFit ? 1.6 : 0.6) && w.l > fs * 0.9;
        const wx = w.x + w.l - fs * 0.25;
        return (
          <g key={i}>
            {lFit && <text x={w.x + fs * 0.3} y={w.y + w.w - fs * 0.3} fontSize={fs}>{ls}</text>}
            {wFit && <text x={wx} y={w.y + fs * 1.0} fontSize={fs} textAnchor="end">
              {ws.map((ch, k) => <tspan key={k} x={wx} dy={k ? fs * 0.95 : 0}>{ch}</tspan>)}</text>}
          </g>
        );
      })}
    </g>
  );
}
