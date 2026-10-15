"""Shtrixkodlar (faqat SVG): Code128 (noldan yozilgan kodlash) va QR (segno matritsasidan yig'ilgan yo'l).

Chiqish — `<g>` / `<path>` bo'laklari (mm koordinatalarida): matn yo'q, tashqi resurs yo'q, skript yo'q. Kirish ma'lumoti
uzunligi va alifbosi tekshiriladi (ValueError — foydalanuvchi tilida, jim bo'sh chiqmaydi).

Code128: A to'plami ishlatilmaydi (boshqaruv belgilari kerak emas): B (ASCII 32..126) va C (raqam juftlari) o'rtasida
avtomatik almashadi — 4 va undan ko'p ketma-ket raqam (juft qismi) C bilan siqiladi.
"""
from __future__ import annotations

from functools import lru_cache
from html import escape

from ..i18n import _

MAX_DATA = 200            # shtrixkod ma'lumotining eng katta uzunligi (belgi)
QUIET_MODULES = 10        # Code128: har tomonda bo'sh zona (modul)

# ───────────────────────── Code128 ─────────────────────────
# Har belgi: 6 raqam — bar, bo'shliq, bar, bo'shliq, bar, bo'shliq kengliklari (jami 11 modul); to'xtash belgisi — 7 raqam (13 modul).
_PATTERNS = """
212222 222122 222221 121223 121322 131222 122213 122312 132212 221213
221312 231212 112232 122132 122231 113222 123122 123221 223211 221132
221231 213212 223112 312131 311222 321122 321221 312212 322112 322211
212123 212321 232121 111323 131123 131321 112313 132113 132311 211313
231113 231311 112133 112331 132131 113123 113321 133121 313121 211331
231131 213113 213311 213131 311123 311321 331121 312113 312311 332111
314111 221411 431111 111224 111422 121124 121421 141122 141221 112214
112412 122114 122411 142112 142211 241211 221114 413111 241112 134111
111242 121142 121241 114212 124112 124211 411212 421112 421211 212141
214121 412121 111143 111341 131141 114113 114311 411113 411311 113141
114131 311141 411131 211412 211214 211232 2331112
""".split()
START_B, START_C, STOP = 104, 105, 106
CODE_B, CODE_C = 100, 99
PATTERNS: list[tuple[int, ...]] = [tuple(int(c) for c in p) for p in _PATTERNS]


def code128_codes(data: str) -> list[int]:
    """Matn → Code128 qiymatlari ro'yxati (boshlang'ich belgi va nazorat yig'indisi bilan, to'xtash belgisiz)."""
    if not data:
        raise ValueError(_("lb.e_bc_empty"))
    if len(data) > MAX_DATA:
        raise ValueError(_("lb.e_bc_long", n=MAX_DATA))
    for ch in data:
        if not 32 <= ord(ch) <= 126:
            raise ValueError(_("lb.e_bc_chars"))
    n = len(data)
    # raqam yugurishlari: i dan boshlab ketma-ket raqamlar soni
    run = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        run[i] = run[i + 1] + 1 if data[i].isdigit() and data[i].isascii() else 0
    codes: list[int] = []
    i, mode = 0, ""
    while i < n:
        r = run[i]
        if mode != "C" and r >= 4 and (i == 0 or r >= 6 or i + r == n):
            # C ga o'tish (o'rtada — faqat uzun yugurish yoki oxirgi bo'lak uchun foydali)
            if r % 2:                                  # toq: birinchi raqam B da, qolgani juft — C da
                if mode == "":
                    codes.append(START_B); mode = "B"
                codes.append(ord(data[i]) - 32)
                i += 1
            codes.append(START_C if mode == "" else CODE_C)
            mode = "C"
            continue
        if mode == "C":
            if run[i] >= 2:
                codes.append(int(data[i:i + 2]))
                i += 2
                continue
            codes.append(CODE_B)                       # raqam yugurishi tugadi (yoki 1 ta qoldi) — B ga qaytish
            mode = "B"
            continue
        if mode == "":
            codes.append(START_B); mode = "B"
        codes.append(ord(data[i]) - 32)
        i += 1
    check = codes[0]
    for pos, c in enumerate(codes[1:], 1):
        check += c * pos
    codes.append(check % 103)
    return codes


def code128_widths(data: str) -> list[int]:
    """Matn → modul kengliklari ketma-ketligi (bar, bo'shliq, bar, …; to'xtash belgisi bilan, bo'sh zonasiz)."""
    out: list[int] = []
    for c in code128_codes(data) + [STOP]:
        out.extend(PATTERNS[c])
    return out


def code128_total_modules(data: str) -> int:
    return sum(code128_widths(data))


def code128_group(data: str, x: float, y: float, w: float, h: float, *, caption: bool = False, quiet: int = QUIET_MODULES,
                  color: str = "#000", font: str = "Arial, Helvetica, sans-serif") -> tuple[str, float]:
    """Code128 SVG bo'lagi: (x, y) chap-yuqori, `w` — bo'sh zonalar bilan umumiy eni (mm), `h` — umumiy balandlik (matn bilan).
    Qaytaradi: (svg, modul kengligi mm) — chaqiruvchi juda ingichka modul haqida ogohlantiradi."""
    widths = code128_widths(data)
    total = sum(widths) + 2 * quiet
    mw = w / total
    cap_h = min(h * 0.28, 3.2) if caption else 0.0
    bar_h = max(h - cap_h, 0.1)
    parts, pos, bar = [], float(quiet), True
    for wd in widths:
        if bar:
            parts.append(f"M{pos:g} 0h{wd}v{bar_h:.3f}h-{wd}z")
        pos += wd
        bar = not bar
    g = [f'<g transform="translate({x:.3f} {y:.3f})">',
         f'<path transform="scale({mw:.5f} 1)" d="{"".join(parts)}" fill="{color}" shape-rendering="crispEdges"/>']
    if caption:
        g.append(f'<text x="{w / 2:.3f}" y="{bar_h + cap_h * 0.82:.3f}" font-size="{cap_h * 0.9:.3f}" text-anchor="middle" '
                 f'font-family="{font}" fill="{color}">{escape(data)}</text>')
    g.append("</g>")
    return "".join(g), mw


def decode_widths(widths: list[int]) -> str:
    """Teskari tekshiruv (testlar uchun): modul kengliklari → matn; nazorat yig'indisi va to'xtash belgisi tekshiriladi."""
    table = {p: i for i, p in enumerate(PATTERNS)}
    syms, i = [], 0
    while i < len(widths):
        if i + 7 <= len(widths) and tuple(widths[i:i + 7]) == PATTERNS[STOP]:
            syms.append(STOP)
            i += 7
            break
        syms.append(table[tuple(widths[i:i + 6])])
        i += 6
    if i != len(widths) or syms[-1] != STOP:
        raise ValueError("stop")
    body, check = syms[:-2], syms[-2]
    total = body[0]
    for pos, c in enumerate(body[1:], 1):
        total += c * pos
    if total % 103 != check:
        raise ValueError("checksum")
    mode = {START_B: "B", START_C: "C"}[body[0]]
    out = []
    for c in body[1:]:
        if mode == "C":                                # C to'plamida: 0…99 — raqam juftlari, 100 — B ga o'tish
            if c == CODE_B:
                mode = "B"
            else:
                out.append(f"{c:02d}")
        elif c == CODE_C:                              # B to'plamida: 99 — C ga o'tish
            mode = "C"
        else:
            out.append(chr(c + 32))
    return "".join(out)


# ───────────────────────── QR ─────────────────────────
@lru_cache(maxsize=4096)
def qr_cells(data: str, ec: str = "m", fast: bool = False) -> tuple[int, str]:
    """QR matritsasi → (modullar soni, yo'l «M x y h w v 1 h -w z» — modul birliklarida, gorizontal yugurishlar bilan).
    `fast=True` — niqob qidiruvi o'tkazib yuboriladi (≈ 5× tez; ko'p etiketkali chop uchun)."""
    if not data:
        raise ValueError(_("lb.e_bc_empty"))
    if len(data) > 1000:
        raise ValueError(_("lb.e_bc_long", n=1000))
    import segno
    kw = {"error": ec, "micro": False}
    if fast:
        kw.update(mask=2, boost_error=False)
    try:
        q = segno.make(data, **kw)
    except Exception as e:  # noqa: BLE001 — segno: ma'lumot sig'maydi va h.k.
        raise ValueError(_("lb.e_bc_qr", e=str(e)[:80])) from e
    rows = [list(r) for r in q.matrix]
    parts = []
    for y, row in enumerate(rows):
        x, n = 0, len(row)
        while x < n:
            if row[x]:
                x0 = x
                while x < n and row[x]:
                    x += 1
                parts.append(f"M{x0} {y}h{x - x0}v1h-{x - x0}z")
            else:
                x += 1
    return len(rows), "".join(parts)


def qr_group(data: str, x: float, y: float, size: float, *, quiet: int = 1, ec: str = "m", fast: bool = False,
             color: str = "#000") -> str:
    """QR SVG bo'lagi: (x, y) chap-yuqori, `size` — bo'sh zona bilan umumiy tomon (mm)."""
    n, d = qr_cells(data, ec, fast)
    k = size / (n + 2 * quiet)
    return (f'<g transform="translate({x:.3f} {y:.3f}) scale({k:.5f}) translate({quiet} {quiet})">'
            f'<path d="{d}" fill="{color}" shape-rendering="crispEdges"/></g>')
