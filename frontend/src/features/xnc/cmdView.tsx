// XNC dastur daraxti qatori: buyruq turi belgisi (o'z chizmamiz, 16×16 SVG) + asosiy parametrlar (kalitlar qalin). Standart
// qiymatli atributlar (AC=1, AV=false, M=true → Z, C=0, IN=0, OUT=1, DIR=false …) qatorda ko'rsatilmaydi — to'liq ro'yxat
// xossalar muharririda qoladi. Buyruq nomi matni o'rniga belgi (nom — qator maslahatida).
import type { ReactNode } from "react";
import type { XncCommand } from "../../api/types";
import { SCHEMA } from "./xncSchema";

type Params = Record<string, string | number>;
const s = (v: unknown) => String(v ?? "");
const isFalse = (v: unknown) => ["false", "0", ""].includes(s(v).trim().toLowerCase());
const isNum = (v: unknown, n: number) => s(v).trim() !== "" && Number(s(v).replace(",", ".")) === n;

/** Qatorda yashiriladigan (standart) qiymatlar: kalit → (qiymat, barcha parametrlar) → yashirinsinmi. */
const HIDE: Record<string, (v: unknown, p: Params) => boolean> = {
  AC: (v) => isNum(v, 1) || s(v).trim() === "",
  AS: (_v, p) => p.AC === undefined || isNum(p.AC, 1),          // qadam — faqat massivda (AC > 1)
  AV: (v) => isFalse(v),
  M: (v) => !isFalse(v),                                        // «qalinlik o'rtasida» — standart
  Z: (_v, p) => p.M !== undefined && !isFalse(p.M),             // M=true bo'lsa Z e'tiborsiz
  C: (v) => isNum(v, 0) || s(v).trim() === "",
  IN: (v) => isNum(v, 0) || s(v).trim() === "",
  OUT: (v) => isNum(v, 1) || s(v).trim() === "",
  DIR: (v) => isFalse(v),
  SDP: (v) => isNum(v, 0) || s(v).trim() === "",
  SXY: (v) => s(v).trim() === "",
  A: (v) => isNum(v, 0),
  R: (v, p) => ("L" in p || "RL" in p) && isNum(v, 0),          // MillRect burchak radiusi 0
  VER: () => true,                                              // import qilingan ichki atributlar
  P: (v) => isNum(v, 0),
};

const KW: Record<string, string> = {
  If: "if", Else: "else", While: "while", DoWhile: "do…while", Break: "break", Continue: "continue",
  Sub: "sub", Call: "call", Ret: "return", Msg: "msg", Err: "err", Set: "set",
};

/** Qator matni: `Var`/`Par` — «double nom=qiymat», boshqaruv — kalit so'z + shart/nom, geometriya — «X=… Y=… DP=… T=…». */
export function cmdLine(c: XncCommand): ReactNode {
  const p = c.params;
  switch (c.cmd) {
    case "Var":
    case "Par":
      return (
        <>
          {p.type !== undefined && p.type !== "" && <span className="muted">{s(p.type)} </span>}
          <b>{s(p.name)}</b>={s(p.value)}
          {c.cmd === "Par" && p.label ? <span className="muted"> «{s(p.label)}»</span> : null}
        </>
      );
    case "Set":
      return <><span className="prog-kw">{KW.Set}</span><b>{s(p.name)}</b>={s(p.value)}</>;
    case "If": case "Else": case "While": case "DoWhile":
      return <><span className="prog-kw">{KW[c.cmd]}</span>{s(p.cond)}</>;
    case "Sub": case "Call":
      return <><span className="prog-kw">{KW[c.cmd]}</span><b>{s(p.name)}</b></>;
    case "Msg": case "Err":
      return <><span className="prog-kw">{KW[c.cmd]}</span>{s(p.text)}</>;
    case "Break": case "Continue": case "Ret":
      return <span className="prog-kw">{KW[c.cmd]}</span>;
    case "Com":
      return null;
    default: {
      const order = (SCHEMA[c.cmd] ?? []).map((d) => d.key);
      let keys = [...order.filter((k) => k in p), ...Object.keys(p).filter((k) => !order.includes(k))].filter((k) => !HIDE[k]?.(p[k], p));
      // Qirra teshigi (M bayrog'i bor buyruq): Z chuqurlikdan keyin — «Y=70 DP=34.0 Z=middle T=…»; M=true bo'lsa Z o'rniga «middle»
      const side = order.includes("M") || "M" in p;
      const mid = side && p.M !== undefined && !isFalse(p.M);      // backend kabi: M yozilmagan — Z aniq qiymat
      if (side) {
        keys = keys.filter((k) => k !== "Z" && k !== "M");
        if (mid || "Z" in p) {
          const at = keys.indexOf("DP");
          keys.splice(at >= 0 ? at + 1 : keys.length, 0, "Z");
        }
      }
      return <>{keys.map((k) => <span key={k} className="pv"><b>{k}</b>={k === "Z" && mid ? "middle" : s(p[k])}</span>)}</>;
    }
  }
}

const DRILL = "#7a4a00", MILL = "#7d3cc9", GROOVE = "#3a2a00", CTRL = "#1f4e8c";

function I({ children, color = CTRL }: { children: ReactNode; color?: string }) {
  return (
    <svg className="cmd-ico" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth={1.5}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{children}</svg>
  );
}

/** Buyruq turi belgilari (noldan chizilgan): asbob, tik teshik, qirra teshigi (4 tomon), paz, freza (boshlanish / chiziq / yoy …), boshqaruv. */
const ICONS: Record<string, ReactNode> = {
  Tool: <I color={DRILL}><path d="M6 1.5h4v3H6zM6.5 4.5h3v4h-3zM8 8.5v3.5l-1.2 2.5h2.4L8 12" /></I>,
  DrillFront: <I color={DRILL}><circle cx="8" cy="8" r="4.5" /><path d="M8 1.5v13M1.5 8h13" /></I>,
  DrillLeft: <I color={DRILL}><rect x="5" y="2.5" width="9.5" height="11" /><path d="M1 8h6.5" strokeWidth={2} /></I>,
  DrillRight: <I color={DRILL}><rect x="1.5" y="2.5" width="9.5" height="11" /><path d="M15 8H8.5" strokeWidth={2} /></I>,
  DrillTop: <I color={DRILL}><rect x="2.5" y="5" width="11" height="9.5" /><path d="M8 1v6.5" strokeWidth={2} /></I>,
  DrillBottom: <I color={DRILL}><rect x="2.5" y="1.5" width="11" height="9.5" /><path d="M8 15V8.5" strokeWidth={2} /></I>,
  Groove: <I color={GROOVE}><rect x="1.5" y="2.5" width="13" height="11" /><path d="M1.5 6.8h13M1.5 9.2h13" /></I>,
  MillStart: <I color={MILL}><circle cx="4" cy="12" r="2" fill={MILL} /><path d="M6 10l6-6M8.5 4H12v3.5" /></I>,
  MillLine: <I color={MILL}><circle cx="3" cy="13" r="1.5" /><circle cx="13" cy="3" r="1.5" /><path d="M4 12l8-8" /></I>,
  MillArc: <I color={MILL}><circle cx="3" cy="13" r="1.5" /><circle cx="13" cy="3" r="1.5" /><path d="M3.5 11.5A9 9 0 0 1 11.5 3.5" /></I>,
  MillArcCenter: <I color={MILL}><path d="M3 13A10 10 0 0 1 13 3" /><path d="M11 13h4M13 11v4" /></I>,
  MillArc3P: (
    <I color={MILL}>
      <path d="M2 12Q8 0 14 12" /><circle cx="2" cy="12" r="1.3" fill={MILL} /><circle cx="8" cy="6" r="1.3" fill={MILL} />
      <circle cx="14" cy="12" r="1.3" fill={MILL} />
    </I>
  ),
  MillFillet: <I color={MILL}><path d="M2 14V7a5 5 0 0 1 5-5h7" /></I>,
  MillRect: <I color={MILL}><rect x="2" y="3" width="12" height="10" rx="2" /></I>,
  MillEllipse: <I color={MILL}><ellipse cx="8" cy="8" rx="6.5" ry="4.5" /></I>,
  Origin: <I><path d="M2 14h11M2 14V3" /><path d="M11 12l2 2-2 2M0 5l2-2 2 2" /></I>,
  Com: <I color="#777"><path d="M2 3h12v8H7l-3 3v-3H2z" /></I>,
  Par: <I><path d="M2 8h12" /><circle cx="10" cy="8" r="2.5" fill="#fff" /></I>,
  Var: (
    <I>
      <text x="8" y="12.5" fontSize={13} fontStyle="italic" fontFamily="Georgia, serif" textAnchor="middle" fill={CTRL} stroke="none">x</text>
    </I>
  ),
  Set: <I><path d="M3 6h10M3 10h10" /></I>,
  If: <I><path d="M8 1.5l6.5 6.5L8 14.5 1.5 8z" /></I>,
  Else: <I><path d="M8 1.5l6.5 6.5L8 14.5 1.5 8z" /><path d="M5 11l6-6" /></I>,
  While: <I><path d="M13 8A5 5 0 1 1 10.5 3.7" /><path d="M9.5 1.5l1.3 2.4-2.6 1" /></I>,
  DoWhile: <I><path d="M13 8A5 5 0 1 1 10.5 3.7" /><path d="M9.5 1.5l1.3 2.4-2.6 1" /><circle cx="8" cy="8" r="1.5" fill={CTRL} /></I>,
  Break: <I><path d="M2 8h4M10 8h4M6.5 4.5l3 7" /></I>,
  Continue: <I><path d="M2 12h7a4 4 0 0 0 0-8H5" /><path d="M7 2L4.5 4 7 6" /></I>,
  Sub: <I><rect x="2" y="3" width="12" height="10" rx="1" /><path d="M5 8h6" /></I>,
  Call: <I><rect x="6" y="3" width="8" height="10" rx="1" /><path d="M1 8h5M4 6l2 2-2 2" /></I>,
  Ret: <I><rect x="2" y="3" width="8" height="10" rx="1" /><path d="M15 8h-5M12 6l-2 2 2 2" /></I>,
  Msg: <I><circle cx="8" cy="8" r="6.5" /><path d="M8 7v4M8 4.5v.3" /></I>,
  Err: <I color="#c0392b"><path d="M8 2l6.5 11.5h-13z" /><path d="M8 6.5v3.5M8 12v.3" /></I>,
};

export function CmdIcon({ cmd }: { cmd: string }) {
  return <span className="cmd-ico-w">{ICONS[cmd] ?? <I><rect x="3" y="3" width="10" height="10" /></I>}</span>;
}
