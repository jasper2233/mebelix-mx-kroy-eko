// XNC buyruqlari: ma'lum parametrlar va ularning tahrirlash turi (matn / mantiqiy / tanlov). Backend: services/xnc.py.
import type { XncCommand } from "../../api/types";

export type PKind = "text" | "bool" | "enum";
export interface PDef {
  key: string; kind?: PKind;
  /** enum variantlari: qiymat → i18n kaliti */
  options?: { value: number | string; label: string }[];
}

const bool = (key: string): PDef => ({ key, kind: "bool" });
const corr = (n: number): PDef => ({ key: "C", kind: "enum", options: Array.from({ length: n }, (_, i) => ({ value: i, label: `xnc.opt.corr${i}` })) });
const inout = (key: "IN" | "OUT"): PDef => ({ key, kind: "enum", options: [0, 1].map((i) => ({ value: i, label: `xnc.opt.${key.toLowerCase()}${i}` })) });
const T = (...keys: string[]): PDef[] => keys.map((key) => ({ key }));

export const PAR_TYPES = ["double", "integer", "boolean", "string"] as const;
const typeDef = (opts: readonly string[]): PDef => ({ key: "type", kind: "enum", options: opts.map((v) => ({ value: v, label: `xnc.type.${v}` })) });

/** `Par` ning `value` maydoni matn turida (type=string) — matn sifatida saqlanadi (son bo'lib ketmaydi, «007» o'zgarmaydi). */
export function isTextParam(c: XncCommand, key: string): boolean {
  return c.cmd === "Par" && key === "value" && ["string", "str", "text"].includes(String(c.params.type ?? "").trim().toLowerCase());
}

/** Har buyruq uchun ma'lum parametrlar (tartib — ko'rsatish tartibi). */
export const SCHEMA: Record<string, PDef[]> = {
  Com: [],
  Par: [...T("name", "value", "label"), typeDef(PAR_TYPES), ...T("visible", "suffix", "readonly")],
  Var: [...T("name", "value"), typeDef(["double", "integer", "string"])],
  Set: T("name", "value"),
  If: T("cond"), Else: T("cond"), While: T("cond"), DoWhile: T("cond"),
  Break: [], Continue: [], Ret: [],
  Sub: T("name"), Call: T("name"), Msg: T("text"), Err: T("text"),
  Tool: T("N", "D"),
  DrillFront: [...T("X", "Y", "DP", "T", "D", "AC", "AS"), bool("AV")],
  DrillLeft: [...T("Y", "Z"), bool("M"), ...T("DP", "T", "D")],
  DrillRight: [...T("Y", "Z"), bool("M"), ...T("DP", "T", "D")],
  DrillTop: [...T("X", "Z"), bool("M"), ...T("DP", "T", "D")],
  DrillBottom: [...T("X", "Z"), bool("M"), ...T("DP", "T", "D")],
  MillStart: [...T("X", "Y", "DP", "T", "D"), corr(4), ...T("SDP", "SXY"), inout("IN"), inout("OUT")],
  MillLine: T("X", "Y", "DP"),
  MillArc: [...T("X", "Y", "R", "DP"), bool("DIR")],
  MillArcCenter: [...T("X", "Y", "CX", "CY", "DP"), bool("DIR")],
  MillArc3P: T("X", "Y", "X2", "Y2", "DP"),
  MillFillet: T("R"),
  MillRect: [...T("X", "Y", "L", "W", "A", "R", "DP", "T", "D"), corr(4)],
  MillEllipse: [...T("X", "Y", "RL", "RW", "A", "DP", "T", "D"), corr(4)],
  Groove: [...T("X1", "Y1", "X2", "Y2", "W", "DP", "T", "D"), corr(3)],
  Origin: T("X", "Y"),
};

export function defOf(cmd: string, key: string): PDef | undefined {
  return SCHEMA[cmd]?.find((d) => d.key === key);
}

/** Ma'lum, lekin buyruqda hali yo'q parametrlar. */
export function missingKeys(c: XncCommand): string[] {
  return (SCHEMA[c.cmd] ?? []).map((d) => d.key).filter((k) => !(k in c.params));
}

/** Qatorning qisqa mazmuni (daraxtda): Par — `nom = qiymat`, blok — shart, boshqalar — `k=v`. */
export function summary(c: XncCommand): string {
  const p = c.params;
  if (c.cmd === "Par") return `${p.name ?? ""} = ${p.value ?? ""}${p.label ? `  «${p.label}»` : ""}`;
  if (c.cmd === "Var" || c.cmd === "Set") return `${p.name ?? ""} = ${p.value ?? ""}`;
  if (c.cmd === "If" || c.cmd === "Else" || c.cmd === "While" || c.cmd === "DoWhile") return String(p.cond ?? "");
  if (c.cmd === "Sub" || c.cmd === "Call") return String(p.name ?? "");
  return Object.entries(p).map(([k, v]) => `${k}=${v}`).join(" ");
}
