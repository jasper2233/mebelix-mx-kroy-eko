// Operatsiya turlari belgilari — o'z chizmamiz (16×16, rangli, foydalanuvchi qarori 2026-10-21: xodimlar tanigan rang uslubida,
// lekin boshqa dastur belgilari nusxalanmaydi). lucide belgilari bilan bir xil interfeys (`size`), shuning uchun `LucideIcon`
// o'rnida ishlatiladi.
import { forwardRef, type ReactNode, type SVGProps } from "react";
import type { LucideIcon } from "lucide-react";

const BOARD = "#ffc66b", BOARD_D = "#a35a00", LINE = "#5a3500";

function mk(name: string, body: ReactNode): LucideIcon {
  const C = forwardRef<SVGSVGElement, SVGProps<SVGSVGElement> & { size?: number | string; strokeWidth?: number | string }>(
    ({ size = 16, color: _c, strokeWidth: _w, ...rest }, ref) => (
      <svg ref={ref} width={size} height={size} viewBox="0 0 16 16" fill="none" strokeLinejoin="round" strokeLinecap="round"
        aria-hidden="true" {...rest}>{body}</svg>
    ));
  C.displayName = name;
  return C as unknown as LucideIcon;
}

/** CS — list kroyi: list bo'laklarga bo'lingan. */
export const IcoCS = mk("IcoCS", <>
  <rect x="1.5" y="2.5" width="13" height="11" fill={BOARD} stroke={BOARD_D} />
  <path d="M8.5 2.5v11M1.5 8.5h7M8.5 6h6" stroke={LINE} />
</>);
/** CN — nesting: list ichida egri shakllar. */
export const IcoCN = mk("IcoCN", <>
  <rect x="1.5" y="2.5" width="13" height="11" fill="#fff3d6" stroke={BOARD_D} />
  <circle cx="5.5" cy="7" r="2.6" fill="#7cc26b" stroke="#2f7a24" />
  <path d="M9 12.5l2.8-6 2.2 6z" fill="#5fa3e8" stroke="#1d5bd1" />
</>);
/** CL — chiziqli kroy: brus va kesish belgilari. */
export const IcoCL = mk("IcoCL", <>
  <rect x="1" y="6" width="14" height="4.5" fill="#c9b3ee" stroke="#6b4f9e" />
  <path d="M5.5 4v8.5M10.5 4v8.5" stroke="#d42020" strokeWidth={1.4} />
</>);
/** EL — kromka: detal va uning chetidagi ko'k lenta. */
export const IcoEL = mk("IcoEL", <>
  <rect x="1.5" y="3" width="10" height="10" fill={BOARD} stroke={BOARD_D} />
  <rect x="11.5" y="2" width="3" height="12" fill="#3d7fe0" stroke="#174a9e" />
</>);
/** SP — bo'yash / plyonka: chelak. */
export const IcoSP = mk("IcoSP", <>
  <path d="M3 5h9l-1.2 9H4.2z" fill="#7fd6cf" stroke="#0e7d78" />
  <path d="M3 5c0-2 9-2 9 0" stroke="#0e7d78" />
  <path d="M13 6.5c1.2 1.6 1.2 3 0 3.4" stroke="#0e7d78" fill="#0e7d78" />
</>);
/** GR — yelimlash (qatlamlar). */
export const IcoGR = mk("IcoGR", <>
  <rect x="2" y="2.5" width="12" height="3.2" fill={BOARD} stroke={BOARD_D} />
  <rect x="2" y="6.4" width="12" height="3.2" fill="#e8a33c" stroke={BOARD_D} />
  <rect x="2" y="10.3" width="12" height="3.2" fill={BOARD} stroke={BOARD_D} />
</>);
/** XNC — stanokda ishlov: detal ustida parma. */
export const IcoXNC = mk("IcoXNC", <>
  <rect x="1.5" y="9" width="13" height="5" fill={BOARD} stroke={BOARD_D} />
  <path d="M6.5 1.5h3v3h-3z" fill="#9db4cf" stroke="#2c4a6e" />
  <path d="M7 4.5h2v3.2L8 9.5 7 7.7z" fill="#5f87b8" stroke="#2c4a6e" />
  <circle cx="11.7" cy="11.5" r="1.1" fill="#fff" stroke={LINE} />
</>);
/** O — material / mahsulotlar (quti). */
export const IcoO = mk("IcoO", <>
  <path d="M2 5.2L8 2.5l6 2.7v6.6L8 14.5 2 11.8z" fill="#e2b679" stroke="#7a4f12" />
  <path d="M2 5.2l6 2.7 6-2.7M8 7.9v6.6" stroke="#7a4f12" />
</>);
/** LB — etiketka: shtrix-kodli yorliq. */
export const IcoLB = mk("IcoLB", <>
  <path d="M1.5 4h9.5l3.5 4-3.5 4H1.5z" fill="#ffe17a" stroke="#9a7300" />
  <path d="M3.5 6v4M5 6v4M6.8 6v4M8.2 6v4" stroke="#333" strokeWidth={0.9} />
</>);
