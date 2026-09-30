// Detal o'lchamlari (backend services/sizes.py bilan bir xil): detal / prifugovkadan keyin / zagotovka / arra.
import type { ELParams, Operation, Part, Project, SizeMode } from "../../api/types";

export interface Sizes { detail: [number, number]; jointed: [number, number]; blank: [number, number]; saw: [number, number] }

export function edgeParams(project: Project): Map<string, ELParams> {
  const m = new Map<string, ELParams>();
  for (const o of project.operations) if (o.type === "EL" && o.el) m.set(o.id, o.el);
  return m;
}

const r3 = (v: number) => Math.round(v * 1000) / 1000;

export function computeSizes(part: Part, mode: SizeMode, edges: Map<string, ELParams>, allowance = 0): Sizes {
  const e = (side: "top" | "bottom" | "left" | "right") => {
    const id = part[`edge_${side}`]?.op_id;
    return id ? edges.get(id) : undefined;
  };
  const th = (s: "top" | "bottom" | "left" | "right") => e(s)?.thickness ?? 0;
  const jn = (s: "top" | "bottom" | "left" | "right") => e(s)?.jointing_width ?? 0;
  const tl = th("left") + th("right"), tw = th("top") + th("bottom");
  const jl = jn("left") + jn("right"), jw = jn("top") + jn("bottom");
  const L = part.length, W = part.width;
  let detail: [number, number], jointed: [number, number], blank: [number, number];
  if (mode === "detail") {
    detail = [L, W]; jointed = [L - tl, W - tw]; blank = [jointed[0] + jl, jointed[1] + jw];
  } else if (mode === "jointed") {
    jointed = [L, W]; detail = [L + tl, W + tw]; blank = [L + jl, W + jw];
  } else {
    blank = [L, W]; jointed = [L - jl, W - jw]; detail = [jointed[0] + tl, jointed[1] + tw];
  }
  const saw: [number, number] = [blank[0] + part.allow_left + part.allow_right + 2 * allowance,
    blank[1] + part.allow_top + part.allow_bottom + 2 * allowance];
  const f = (a: [number, number]): [number, number] => [r3(a[0]), r3(a[1])];
  return { detail: f(detail), jointed: f(jointed), blank: f(blank), saw: f(saw) };
}

export function productQty(project: Project, part: Part): number {
  if (!part.product_id) return 1;
  return project.products.find((p) => p.id === part.product_id)?.qty ?? 1;
}

export function totalQty(project: Project, part: Part): number {
  return part.qty * productQty(project, part);
}

/** Nomga belgilar: '=' pazlash, '*' frezerlash, '%' teshik (UI_SPEC §5.2). */
export function partMarks(project: Project, part: Part): string {
  let m = "";
  if ((["top", "bottom", "left", "right"] as const).some((s) => part[`groove_${s}`]?.op_id)) m += "=";
  const xnc = project.operations.filter((o) => o.type === "XNC" && o.xnc && part.xnc_op_ids.includes(o.id));
  if (xnc.length) {
    const cmds: string[] = [];
    const walk = (l: { cmd: string; children: unknown[] }[]) => l.forEach((c) => { cmds.push(c.cmd); walk(c.children as never); });
    xnc.forEach((o) => walk(o.xnc!.program as never));
    if (cmds.some((c) => c.startsWith("Mill"))) m += "*";
    if (cmds.some((c) => c.startsWith("Drill"))) m += "%";
    if (cmds.includes("Groove") && !m.includes("=")) m += "=";
  }
  return m;
}

/** Kartalar ro'yxati (detal qaysi kartalarda) — «№ в раскрое». */
export function mapsOfPart(op: Operation, partId: string): number[] {
  const out: number[] = [];
  op.result?.maps.forEach((m) => { if (m.placements.some((p) => p.part_id === partId)) out.push(m.index); });
  return out;
}
