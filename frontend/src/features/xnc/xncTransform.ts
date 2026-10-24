// XNC dasturi buyruqlarini geometrik o'zgartirish (onlayn tizimdagi «отзеркаливание» / «перенос с копированием»):
//   akslantirish — X → «dx-X» (gorizontal), Y → «dy-Y» (vertikal); ikki marta akslantirish asl qiymatni qaytaradi;
//   yon teshiklar tomoni almashadi (chap ↔ o'ng, yuqori ↔ past), yoy yo'nalishi teskari bo'ladi (DIR yoki R ishorasi);
//   siljitish — X → X+ΔX, Y → Y+ΔY (son bo'lsa — hisoblanadi, ifoda bo'lsa — «(ifoda)+Δ»).
import type { XncCommand } from "../../api/types";

const X_KEYS = ["X", "X1", "X2", "CX"];
const Y_KEYS = ["Y", "Y1", "Y2", "CY"];
const SWAP_X: Record<string, string> = { DrillLeft: "DrillRight", DrillRight: "DrillLeft" };
const SWAP_Y: Record<string, string> = { DrillTop: "DrillBottom", DrillBottom: "DrillTop" };
const ARCS = new Set(["MillArc", "MillArcCenter"]);
// frezaning korreksiya tomoni (C: 1 — o'ngda, 2 — chapda) akslantirishda almashadi — kontur yo'nalishi teskari bo'ladi
const CORR = new Set(["MillStart", "MillRect", "MillEllipse", "Groove"]);
const ANGLED = new Set(["MillRect", "MillEllipse"]);
/** Akslantirish mumkin bo'lgan (geometrik) buyruqlar — xizmat buyruqlari (Tool, Var, If …) o'zgarmaydi. */
export const MIRRORABLE = new Set(["DrillFront", "DrillLeft", "DrillRight", "DrillTop", "DrillBottom", "MillStart", "MillLine",
  "MillArc", "MillArcCenter", "MillArc3P", "MillFillet", "MillRect", "MillEllipse", "Groove"]);

type Val = string | number;
const isNum = (v: Val) => typeof v === "number" || (typeof v === "string" && v.trim() !== "" && Number.isFinite(Number(v)));
const fmt = (n: number) => String(Math.round(n * 1000) / 1000);

/** «dx-384» ↔ 384: o'lcham bo'yicha akslantirish (`lim` — «dx» yoki «dy»). */
export function mirrorVal(v: Val, lim: "dx" | "dy"): Val {
  if (v === "" || v === null || v === undefined) return v;
  const s = String(v).trim();
  const m = new RegExp(`^${lim}\\s*-\\s*(.+)$`).exec(s);
  if (m) {
    const inner = m[1].trim().replace(/^\((.*)\)$/, "$1");
    return isNum(inner) ? Number(inner) : inner;
  }
  if (isNum(s)) { const n = Number(s); return n === 0 ? lim : `${lim}-${fmt(n)}`; }
  if (s === lim) return 0;
  return `${lim}-(${s})`;
}

export function shiftVal(v: Val, d: number): Val {
  if (!d || v === "" || v === null || v === undefined) return v;
  if (isNum(v)) return Number(fmt(Number(v) + d));
  return `(${v})${d >= 0 ? "+" : "-"}${fmt(Math.abs(d))}`;
}

/** Buyruqni (ichki buyruqlari bilan) akslantirish. */
export function mirrorCmd(c: XncCommand, axis: "x" | "y"): XncCommand {
  const keys = axis === "x" ? X_KEYS : Y_KEYS;
  const lim = axis === "x" ? "dx" : "dy";
  const params: Record<string, Val> = { ...c.params };
  for (const k of keys) if (k in params) params[k] = mirrorVal(params[k], lim);
  if (CORR.has(c.cmd) && "C" in params) {
    const cv = Number(params.C);
    if (cv === 1 || cv === 2) params.C = 3 - cv;
  }
  if (ANGLED.has(c.cmd) && "A" in params && params.A !== "") {
    params.A = isNum(params.A) ? (Number(params.A) === 0 ? 0 : -Number(params.A)) : `-(${params.A})`;
  }
  if (ARCS.has(c.cmd)) {
    if ("DIR" in params && params.DIR !== "") params.DIR = String(params.DIR) === "true" ? "false" : "true";
    else if (c.cmd === "MillArc" && isNum(params.R)) params.R = -Number(params.R);
  }
  const cmd = (axis === "x" ? SWAP_X : SWAP_Y)[c.cmd] ?? c.cmd;
  return { ...c, cmd, params, children: (c.children ?? []).map((ch) => mirrorCmd(ch, axis)) };
}

export function shiftCmd(c: XncCommand, dx: number, dy: number): XncCommand {
  const params: Record<string, Val> = { ...c.params };
  for (const k of X_KEYS) if (k in params) params[k] = shiftVal(params[k], dx);
  for (const k of Y_KEYS) if (k in params) params[k] = shiftVal(params[k], dy);
  return { ...c, params, children: (c.children ?? []).map((ch) => shiftCmd(ch, dx, dy)) };
}

export const mirrorProgram = (prog: XncCommand[], axis: "x" | "y") => prog.map((c) => mirrorCmd(c, axis));
