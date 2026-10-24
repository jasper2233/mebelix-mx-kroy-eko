"""LB shablonini ZPL II (Zebra) matniga o'girish (W15 · LB-D). Printerga to'g'ridan yuborilmaydi — faqat `.zpl` fayl.

Hamma narsa noldan, W4 shablon dvigatelining o'zi bilan: `ZplRenderer` — `label_tpl.Renderer` ning avlodi (ifodalarni hisoblash,
`if/group/var`, matnni sig'dirish/qatorlarga bo'lish — bitta manba); faqat chizish buyruqlari SVG o'rniga ZPL yozadi.
Etiketka — `^XA … ^XZ` bloki; o'lchamlar mm → nuqta (`dpi` 203 yoki 300).

    shablon elementi        ZPL
    text                    ^FO x,y ^A0N,h,w ^FD…^FS   (qatorlar alohida maydon; markaz/o'ng tekislash — ^FB; oq matn — ^FR)
    rect                    ^GB w,h,qalinlik,B|W,yumaloqlash   (to'ldirilgan quyuq rang — qalinlik = kichik tomon)
    line                    ^GB (gorizontal/vertikal) yoki ^GD (qiyshiq)
    barcode qr              ^BQN,2,<modul> + ^FD<EC>A,<ma'lumot>
    barcode code128         ^BY<modul> + ^BC<yo'nalish>,<balandlik>,<matn Y|N>,N,N,A
    part, edges             ^GB / ^GD / matn (o'zimizcha chizilgan detal chizmasi va kromka sxemasi)
    polyline, arc           ^GB / ^GD kesmalari (yoy — 10° li xordalar bilan: taxminiy); ellipse — ^GE / ^GC
    group                   koordinata siljishi + burish (faqat 90° ga karrali burish aniq; boshqasi yaqin 90° ga yaxlitlanadi)
    image                   o'tkaziladi (ogohlantirish `image`)

Taxminiy joylar (printerda tekshirilmagan — T_LB_W15 hujjatidagi savollar): shrift balandligi (`TEXT_H_K`), matn kengligi
(o'rnatilgan shrift 0 Arial dan torroq), burilgan matn/shtrixkodning `^FO` boshi (aylantirilgan chegaraviy to'rtburchakning chap-yuqori
burchagi deb olinadi). Matndagi `^`, `~`, `_` belgilari `^FH_` + `_5E` kabi hex ko'rinishda yoziladi (maydon ichida buyruq chiqmaydi).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Optional

from ..i18n import LANG, _
from ..models import LB_MAX_LABELS, LBParams, Project
from . import expr
from .barcode import code128_widths, qr_cells
from .label_print import LabelsLimit, resolve_template
from .label_schema import ZplSettings
from .label_tpl import Renderer, TemplateError, _Fail, label_text, normalize_template, text_width
from .label_vars import EnvBuilder, count_items, iter_items, sample_env
from .render import safe_color

TEXT_H_K = 1.0                 # ZPL shrift balandligi (nuqta) = SVG shrift o'lchami (mm) × dpi/25.4 × TEXT_H_K
TEXT_W_K = 1.0                 # ZPL shrift kengligi = balandlik × TEXT_W_K (1 — shrift o'z nisbatida)
MIN_FONT_DOTS = 10             # ^A: eng kichik balandlik
ARC_STEP_DEG = 10.0            # yoy xordalari qadami
WHITE_LUM = 0.97                # shundan yorqin rang — «oq» (matn: ^FR teskari bosma; to'ldirish/chiziq: W)
PREVIEW_LABELS = 3             # oldindan ko'rishda ko'rsatiladigan etiketkalar
PREVIEW_SCAN = 300             # ogohlantirish qidirish uchun hisoblanadigan etiketkalar
_HEX_NEED = re.compile(r"[\^~_]")
_LATIN1_OK = re.compile(r"^[\x20-\x7e\xa0-\xff]*$")
_NAMED_LUM = {"white": 1.0, "black": 0.0, "silver": 0.75, "lightgray": 0.83, "lightgrey": 0.83, "gray": 0.5, "grey": 0.5,
              "whitesmoke": 0.96, "ivory": 0.99, "snow": 0.99, "none": 1.0, "transparent": 1.0}


def color_lum(c) -> float:
    """CSS rang → yorqinlik 0…1 (rang nomi noma'lum bo'lsa — qora tomonga, 0.25)."""
    c = (c or "").strip().lower() if isinstance(c, str) else ""
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", c)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        return (0.299 * r + 0.587 * g + 0.114 * b) / 255
    m = re.fullmatch(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)[^)]*\)", c)
    if m:
        r, g, b = (min(255, int(x)) for x in m.groups())
        return (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return _NAMED_LUM.get(c, 0.25)


_TILDE_CMD = re.compile(r"~[A-Za-z]{2}[^\^~\n]*")


def split_header(header: str) -> tuple[list[str], str]:
    """«ZPL Header» → (`~` buyruqlari ro'yxati, qolgan matn): tilda buyruqlari formatdan oldin yoziladi."""
    pre = [m.group(0).strip() for m in _TILDE_CMD.finditer(header or "")]
    rest = _TILDE_CMD.sub("", header or "")
    rest = "\n".join(ln for ln in (x.strip() for x in rest.split("\n")) if ln)
    return [p for p in pre if p], rest


def zpl_escape(s: str) -> tuple[str, bool]:
    """`^FD` ma'lumotidagi `^`, `~`, `_` → `_5E`, `_7E`, `_5F` (`^FH_` bilan o'qiladi). Qaytaradi: (matn, hex ishlatildimi)."""
    if not _HEX_NEED.search(s):
        return s, False
    return "".join(f"_{ord(ch):02X}" if ch in "^~_" else ch for ch in s), True


# ───────────────────────── Affin matritsa: (a, b, c, d, e, f): x' = a·x + c·y + e, y' = b·x + d·y + f ─────────────────────────
Mat = tuple[float, float, float, float, float, float]
IDENT: Mat = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mat_mul(m1: Mat, m2: Mat) -> Mat:
    """m1 · m2 (avval m2, keyin m1 qo'llanadi)."""
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2, a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def mat_translate(x: float, y: float) -> Mat:
    return (1.0, 0.0, 0.0, 1.0, x, y)


def mat_rotate(deg: float) -> Mat:
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return (c, s, -s, c, 0.0, 0.0)


@dataclass
class ZplLabelWarn:
    code: str
    key: str = ""
    count: int = 1


class ZplRenderer(Renderer):
    """Bir chop uchun: `zpl(env)` — bitta etiketka `^XA … ^XZ` bloki. `zwarn` — ogohlantirishlar (kod → soni va birinchi kalit)."""

    def __init__(self, tpl: dict, *, width_mm: float, height_mm: float, params: Optional[dict] = None, lang: str = "ru",
                 settings: Optional[ZplSettings] = None, rotate_page: int = 0, fast_qr: bool = False, clock=None):
        super().__init__(tpl, width_mm=width_mm, height_mm=height_mm, params=params, lang=lang, fast_qr=fast_qr, clock=clock)
        self.zs = settings or ZplSettings()
        self.dpmm = self.zs.dpi / 25.4
        self.page_rot = 90 if rotate_page == 90 else 0
        if self.page_rot:       # sahifa 90° burilgan: fizik etiketka eni = H, uzunligi = W (HTML `.rot` bilan bir xil)
            self._root: Mat = (0.0, 1.0, -1.0, 0.0, self.H, 0.0)
            self.pw_mm, self.ll_mm = self.H, self.W
        else:
            self._root = IDENT
            self.pw_mm, self.ll_mm = self.W, self.H
        self._m: Mat = self._root
        self.zwarn: dict[str, ZplLabelWarn] = {}
        self._handlers = {
            "text": self._ztext, "rect": self._zrect, "line": self._zline, "image": self._zimage, "barcode": self._zbarcode,
            "part": self._zpart, "edges": self._zedges, "group": self._zgroup, "if": self._if, "var": self._var,
            "polyline": self._zpolyline, "arc": self._zarc, "ellipse": self._zellipse, "bezier": self._zbezier,
        }

    # — yordamchilar —
    def zw(self, code: str, key: str = "") -> None:
        w = self.zwarn.get(code)
        if w is None:
            self.zwarn[code] = ZplLabelWarn(code, key[:60])
        else:
            w.count += 1

    def zwarnings(self) -> list[dict]:
        """ZPL ogohlantirishlari (matn — chaqiruv vaqtidagi tilda)."""
        return [{"code": w.code, "key": w.key, "count": w.count, "message": _(f"lb.zpl_w_{w.code}", k=w.key)}
                for w in self.zwarn.values()]

    def d(self, mm: float) -> int:
        return int(round(mm * self.dpmm))

    def pt(self, x: float, y: float) -> tuple[float, float]:
        a, b, c, d, e, f = self._m
        return a * x + c * y + e, b * x + d * y + f

    def aabb(self, x0: float, y0: float, x1: float, y1: float) -> tuple[float, float, float, float]:
        """Mahalliy to'rtburchak → etiketka (mm) dagi chegaraviy to'rtburchak (minx, miny, maxx, maxy)."""
        pts = [self.pt(x0, y0), self.pt(x1, y0), self.pt(x0, y1), self.pt(x1, y1)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)

    @staticmethod
    def own_rect(x0: float, y0: float, x1: float, y1: float, pivot: tuple[float, float], rot: float) -> tuple[float, float, float, float]:
        """To'rtburchakni `pivot` atrofida `rot` gradusga (soat strelkasi bo'yicha) burib, chegaraviy to'rtburchagini qaytaradi."""
        if not rot:
            return x0, y0, x1, y1
        m = mat_mul(mat_translate(*pivot), mat_mul(mat_rotate(rot), mat_translate(-pivot[0], -pivot[1])))
        a, b, c, d, e, f = m
        pts = [(a * px + c * py + e, b * px + d * py + f) for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)

    def orient(self, own_rot: float) -> tuple[str, int]:
        """Elementning o'z burilishi + matritsa burilishi → (ZPL yo'nalishi N|R|I|B, chorak soni). 90° ga karrali bo'lmasa — ogohlantirish."""
        a, b = self._m[0], self._m[1]
        total = own_rot + math.degrees(math.atan2(b, a))
        q = int(round(total / 90.0))
        if abs(total - 90.0 * q) > 1.0:
            self.zw("rotate", f"{total:.0f}°")
        q %= 4
        return "NRIB"[q], q

    def fo(self, x_mm: float, y_mm: float) -> str:
        xd, yd = self.d(x_mm), self.d(y_mm)
        if xd < 0 or yd < 0:
            self.zw("clip")
            xd, yd = max(xd, 0), max(yd, 0)
        return f"^FO{xd},{yd}"

    def fo_dots(self, xd: int, yd: int) -> str:
        if xd < 0 or yd < 0:
            self.zw("clip")
            xd, yd = max(xd, 0), max(yd, 0)
        return f"^FO{xd},{yd}"

    # — matn —
    def prep_text(self, s: str) -> str:
        """Chiqish kodlashiga moslash: UTF-8 yoqilmagan bo'lsa — translit (ASCII), o'rnatilgan shriftda Latin-1 dan tashqari belgilar — ogohlantirish."""
        s = s.replace("\t", " ")
        if not self.zs.utf8:
            if not s.isascii():
                self.zw("nonascii")
                try:
                    s = str(expr.evaluate("translit(s)", {"s": s}))
                except ValueError:
                    pass
                s = "".join(ch if ord(ch) < 128 else "?" for ch in s)
            return s
        if not _LATIN1_OK.match(s) and ":" not in self.zs.font:        # o'rnatilgan shriftlarda kirill/«…»/«№» yo'q: printer TTF kerak
            self.zw("font")
        return s

    def font_cmd(self, ori: str, hd: int, wd: int) -> str:
        f = self.zs.font
        return f"^A@{ori},{hd},{wd},{f}" if ":" in f else f"^A{f}{ori},{hd},{wd}"

    def put_text(self, out: list, text: str, size: float, x: float, y_top: float, anchor: str = "start", rot: float = 0.0,
                 color: str = "#000", maxw: float = 0.0, pivot: Optional[tuple[float, float]] = None,
                 rect: Optional[tuple[float, float, float, float]] = None) -> None:
        """Bitta qatorli matn maydoni. (x, y_top) — SVG dagi kabi: x — tayanch nuqta (anchor), y_top — matn qutisining yuqori cheti;
        `rot` — shu nuqta (yoki `pivot`) atrofida burish. `rect` berilsa — burishdan keyingi mahalliy chegaraviy to'rtburchak tayyor."""
        text = self.prep_text(text)
        if not text.strip():
            return
        ori, q = self.orient(rot)
        hd = max(MIN_FONT_DOTS, int(round(self.d(size) * TEXT_H_K)))
        wd = max(MIN_FONT_DOTS, int(round(hd * TEXT_W_K)))
        reverse = color_lum(color) >= WHITE_LUM
        wtxt = text_width(text, size, False)
        esc, hexed = zpl_escape(text)
        tail = ("^FH_" if hexed else "") + f"^FD{esc}^FS"
        cmd = self.font_cmd(ori, hd, wd) + ("^FR" if reverse else "")
        if q == 0 and anchor in ("middle", "end") and rect is None:
            ax, ay = self.pt(x, y_top)
            if maxw > 0:
                bw = maxw
                fx = ax - bw / 2 if anchor == "middle" else ax - bw
            else:
                half = min(ax, self.pw_mm - ax)
                bw, fx = (2 * half, ax - half) if anchor == "middle" else (ax, 0.0)
            if bw >= max(1.0, wtxt):
                out.append(self.fo(fx, ay) + cmd + f"^FB{self.d(bw)},1,0,{'C' if anchor == 'middle' else 'R'},0" + tail)
                return
        if rect is None:
            x0 = x - wtxt / 2 if anchor == "middle" else (x - wtxt if anchor == "end" else x)
            rect = self.own_rect(x0, y_top, x0 + wtxt, y_top + size, pivot or (x, y_top), rot)
        mx, my, _x1, _y1 = self.aabb(*rect)
        out.append(self.fo(mx, my) + cmd + tail)

    def _ztext(self, el, env, out, p) -> None:
        m = self.text_model(el, env, p)
        for i, line in enumerate(m["lines"]):
            if line:
                self.put_text(out, line, m["size"], m["x"], m["y"] + i * m["lh"], m["anchor"], m["rot"], m["color"], m["maxw"],
                              pivot=(m["x"], m["y"]))

    def _placeholder(self, out: list, p: str) -> None:
        keep, self._m = self._m, self._root
        try:
            self.put_text(out, f"#ERR {p}", 2.2, 1.0, 0.4 + 2.4 * self._ph)
        finally:
            self._m = keep
        self._ph += 1

    # — to'rtburchak, chiziq, ellips —
    def put_rect(self, out: list, x: float, y: float, w: float, h: float, sw: float, stroke: str, fill: str, radius: float = 0.0) -> None:
        x0, y0, x1, y1 = self.aabb(x, y, x + w, y + h)
        wd, hd = max(1, self.d(x1 - x0)), max(1, self.d(y1 - y0))
        rnd = 0
        if radius > 0:
            rnd = max(0, min(8, int(round(radius / max(min(w, h) / 2, 0.01) * 8))))
        solid = None
        if fill and fill != "none":
            lum = color_lum(fill)
            solid = "B" if lum < 0.45 else ("W" if lum >= WHITE_LUM else None)
        if solid:
            out.append(self.fo(x0, y0) + f"^GB{wd},{hd},{min(wd, hd)},{solid},{rnd}^FS")
        t = max(1, self.d(sw)) if sw > 0 else 0
        if t and not (solid == "B" and color_lum(stroke) < WHITE_LUM):
            col = "W" if color_lum(stroke) >= WHITE_LUM else "B"
            out.append(self.fo(x0, y0) + f"^GB{max(wd, t)},{max(hd, t)},{t},{col},{rnd}^FS")

    def put_line(self, out: list, x1: float, y1: float, x2: float, y2: float, sw: float, color: str) -> None:
        ax, ay = self.pt(x1, y1)
        bx, by = self.pt(x2, y2)
        t = max(1, self.d(sw))
        col = "W" if color_lum(color) >= WHITE_LUM else "B"
        dx, dy = abs(bx - ax) * self.dpmm, abs(by - ay) * self.dpmm
        xmin, ymin = min(ax, bx) * self.dpmm, min(ay, by) * self.dpmm
        if dx < 1.0 and dy < 1.0:
            return
        if dy < 1.0:                                    # gorizontal
            out.append(self.fo_dots(int(round(xmin)), int(round(ay * self.dpmm - t / 2))) + f"^GB{max(1, int(round(dx)))},{t},{t},{col},0^FS")
        elif dx < 1.0:                                  # vertikal
            out.append(self.fo_dots(int(round(ax * self.dpmm - t / 2)), int(round(ymin))) + f"^GB{t},{max(1, int(round(dy)))},{t},{col},0^FS")
        else:                                           # qiyshiq: o'ngga-yuqoriga — «R» (/), o'ngga-pastga — «L» (\)
            orient = "R" if (bx - ax) * (by - ay) < 0 else "L"
            out.append(self.fo_dots(int(round(xmin)), int(round(ymin)))
                       + f"^GD{max(3, int(round(dx)))},{max(3, int(round(dy)))},{t},{col},{orient}^FS")

    def _zrect(self, el, env, out, p) -> None:
        x, y = self._num(el, "x", env, p), self._num(el, "y", env, p)
        w, h = self._num(el, "w", env, p, lo=0), self._num(el, "h", env, p, lo=0)
        sw, sc = self._stroke(el, env, p, 0.2 if el.get("stroke") is not None else 0.0)
        fill = el.get("fill")
        fill_c = safe_color(fill, "none") if fill and fill != "none" else "none"
        rx = self._num(el, "radius", env, p, 0.0, 0.0, 100.0)
        self.put_rect(out, x, y, w, h, sw, sc, fill_c, rx)

    def _zline(self, el, env, out, p) -> None:
        x1, y1 = self._num(el, "x1", env, p), self._num(el, "y1", env, p)
        x2, y2 = self._num(el, "x2", env, p), self._num(el, "y2", env, p)
        sw, sc = self._stroke(el, env, p, 0.2)
        self.put_line(out, x1, y1, x2, y2, max(sw, 0.05), sc)

    def _zpolyline(self, el, env, out, p) -> None:
        pts = self.poly_points(el, env, p)
        closed = self._flag(el, "closed", env, p)
        sw, sc, fill_c = self._outline(el, env, p)
        if fill_c != "none":
            self.zw("fill", p)
        if sw <= 0:
            sw, sc = 0.2, "#000"
        seq = pts + ([pts[0]] if closed and len(pts) > 2 else [])
        for (xa, ya), (xb, yb) in zip(seq, seq[1:]):
            self.put_line(out, xa, ya, xb, yb, sw, sc)

    def _zbezier(self, el, env, out, p) -> None:
        pts = self.bezier_sample(self.bezier_points(el, env, p))
        sw, sc, _fill = self._outline(el, env, p)
        if sw <= 0:
            sw, sc = 0.2, "#000"
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            self.put_line(out, xa, ya, xb, yb, sw, sc)

    def _zarc(self, el, env, out, p) -> None:
        cx, cy, r, a1, sweep = self.arc_geometry(el, env, p)
        sw, sc, fill_c = self._outline(el, env, p)
        if r <= 0 or sweep == 0:
            return
        if abs(sweep) >= 359.999:
            self._put_ellipse(out, cx, cy, r, r, sw, sc, fill_c)
            return
        if fill_c != "none":
            self.zw("fill", p)
        if sw <= 0:
            sw, sc = 0.2, "#000"
        self.zw("arc", p)
        n = max(2, int(math.ceil(abs(sweep) / ARC_STEP_DEG)))
        prev = None
        for i in range(n + 1):
            t = math.radians(a1 + sweep * i / n)
            cur = (cx + r * math.cos(t), cy + r * math.sin(t))
            if prev is not None:
                self.put_line(out, prev[0], prev[1], cur[0], cur[1], sw, sc)
            prev = cur

    def _put_ellipse(self, out, cx, cy, rx, ry, sw, sc, fill_c) -> None:
        x0, y0, x1, y1 = self.aabb(cx - rx, cy - ry, cx + rx, cy + ry)
        wd, hd = max(1, self.d(x1 - x0)), max(1, self.d(y1 - y0))
        solid = None
        if fill_c != "none":
            lum = color_lum(fill_c)
            solid = "B" if lum < 0.45 else ("W" if lum >= WHITE_LUM else None)
        t = max(1, self.d(sw)) if sw > 0 else 0
        thick = min(wd, hd) if solid else t
        if not thick:
            return
        col = solid or ("W" if color_lum(sc) >= WHITE_LUM else "B")
        if wd == hd:
            out.append(self.fo(x0, y0) + f"^GC{wd},{thick},{col}^FS")
        else:
            out.append(self.fo(x0, y0) + f"^GE{wd},{hd},{thick},{col}^FS")

    def _zellipse(self, el, env, out, p) -> None:
        cx, cy = self._num(el, "cx", env, p), self._num(el, "cy", env, p)
        rx, ry = self._num(el, "rx", env, p, lo=0.0), self._num(el, "ry", env, p, lo=0.0)
        sw, sc, fill_c = self._outline(el, env, p)
        if rx > 0 and ry > 0:
            self._put_ellipse(out, cx, cy, rx, ry, sw, sc, fill_c)

    def _zimage(self, el, env, out, p) -> None:
        self.zw("image", p)

    # — shtrixkodlar —
    def _zbarcode(self, el, env, out, p) -> None:
        kind = str(el.get("kind", "qr")).lower()
        data = self._text_val(el, "data", env, p, "")
        x, y = self._num(el, "x", env, p), self._num(el, "y", env, p)
        rot = self._num(el, "rotate", env, p, 0.0, -360.0, 360.0)
        try:
            if kind == "qr":
                size = self._num(el, "size", env, p, min(self.W, self.H) * 0.4, 1.0, 500.0)
                quiet = int(self._num(el, "quiet", env, p, 1.0, 0.0, 10.0))
                ec = str(el.get("ec", "m")).lower()
                ec = ec if ec in ("l", "m", "q", "h") else "m"
                n_mod = qr_cells(data, ec, self.fast_qr)[0]
                mag = self.d(size) // (n_mod + 2 * quiet)
                if mag < 1:
                    self.zw("qr_small", p)
                    mag = 1
                mag = min(mag, 10)
                sym = n_mod * mag
                rx0, ry0, rx1, ry1 = self.own_rect(x, y, x + size, y + size, (x, y), rot)
                bx0, by0, bx1, by1 = self.aabb(rx0, ry0, rx1, ry1)
                fx = int(round((bx0 + bx1) / 2 * self.dpmm - sym / 2))
                fy = int(round((by0 + by1) / 2 * self.dpmm - sym / 2))
                esc, hexed = zpl_escape(data)
                out.append(self.fo_dots(fx, fy) + f"^BQN,2,{mag}" + ("^FH_" if hexed else "") + f"^FD{ec.upper()}A,{esc}^FS")
            else:
                w = self._num(el, "w", env, p, lo=1.0, hi=500.0)
                h = self._num(el, "h", env, p, lo=1.0, hi=500.0)
                quiet = int(self._num(el, "quiet", env, p, 10.0, 0.0, 20.0))
                cap = self._flag(el, "caption", env, p)
                modules = sum(code128_widths(data))
                avail = self.d(w) // (modules + 2 * quiet)
                if avail < 1:
                    self.zw("bc_dense", p)
                mw = max(1, min(avail, 10))
                used_mm = modules * mw / self.dpmm
                cap_h = min(h * 0.28, 3.2) if cap else 0.0
                bar_d = max(1, self.d(h - cap_h))
                lx0 = x + max(0.0, (w - used_mm) / 2)                    # sig'masa — chap chetdan boshlanadi (ogohlantirish bilan)
                rx0, ry0, rx1, ry1 = self.own_rect(lx0, y, lx0 + used_mm, y + h, (x, y), rot)
                bx0, by0, _bx1, _by1 = self.aabb(rx0, ry0, rx1, ry1)
                ori, _q = self.orient(rot)
                esc, hexed = zpl_escape(data)
                out.append(f"^BY{mw}")
                out.append(self.fo(bx0, by0) + f"^BC{ori},{bar_d},{'Y' if cap else 'N'},N,N,A" + ("^FH_" if hexed else "")
                           + f"^FD{esc}^FS")
        except ValueError as e:
            self.error(p, "data", data[:60], str(e))
            raise _Fail() from None

    # — detal chizmasi va kromka sxemasi —
    def _zpart(self, el, env, out, p) -> None:
        """`label_tpl.Renderer._part` geometriyasining ZPL nusxasi: nisbatga mos to'rtburchak, kromka — qalin chiziq + belgi, o'lchamlar."""
        x, y = self._num(el, "x", env, p), self._num(el, "y", env, p)
        w, h = self._num(el, "w", env, p, lo=2.0), self._num(el, "h", env, p, lo=2.0)
        try:
            L, Wd = float(env.get("part.length") or 0), float(env.get("part.width") or 0)
        except (TypeError, ValueError):
            L = Wd = 0.0
        fs = max(1.3, min(2.4, h * 0.13))
        aw, ah = w - fs * 1.8, h - fs * 1.7
        if L <= 0 or Wd <= 0 or aw <= 1 or ah <= 1:
            self.put_rect(out, x, y, w, h, 0.2, "#999", "none")
            return
        k = min(aw / L, ah / Wd)
        rw, rh = L * k, Wd * k
        x0, y0 = x + (aw - rw) / 2, y + (ah - rh) / 2
        self.put_rect(out, x0, y0, rw, rh, 0.2, "#666", "none")
        sw = max(0.25, min(0.9, min(rw, rh) * 0.12))
        seg = {"top": (x0, y0, x0 + rw, y0), "bottom": (x0, y0 + rh, x0 + rw, y0 + rh),
               "left": (x0, y0, x0, y0 + rh), "right": (x0 + rw, y0, x0 + rw, y0 + rh)}
        sfs = max(1.0, min(fs, sw * 3.2))
        for s, (a, b, c, d) in seg.items():
            if not env.get(f"edge.{s}.has"):
                continue
            if int(env.get(f"edge.{s}.lines") or 0) > 0:
                self.put_line(out, a, b, c, d, sw, "#000")
            sym = label_text(env.get(f"edge.{s}.symbol"))
            tx, ty = {"top": ((a + c) / 2, b + sfs * 1.5 + sw / 2), "bottom": ((a + c) / 2, b - sw / 2 - sfs * 0.4),
                      "left": (a + sw / 2 + sfs * 0.7, (b + d) / 2 + sfs * 0.35),
                      "right": (a - sw / 2 - sfs * 0.7, (b + d) / 2 + sfs * 0.35)}[s]
            self.put_text(out, sym, sfs, tx, ty - sfs * 0.82, "middle")
        self.put_text(out, label_text(L), fs, x0 + rw / 2, y0 + rh + fs * 1.15 - fs * 0.82, "middle")
        tx, ty = x0 + rw + fs * 1.05, y0 + rh / 2                       # eni — o'ngda, 90° burilgan (SVG dagi kabi)
        wt = text_width(label_text(Wd), fs, False)
        rect = self.own_rect(tx - wt / 2, ty - fs * 0.82, tx + wt / 2, ty + fs * 0.18, (tx, ty), 90.0)
        self.put_text(out, label_text(Wd), fs, tx, ty, "middle", 90.0, rect=rect)

    def _zedges(self, el, env, out, p) -> None:
        """Kromka sxemasi (`labels.edge_icon_parts` geometriyasi): to'rtburchak + kromkali tomonlarda qalin chiziq va belgi."""
        x, y = self._num(el, "x", env, p), self._num(el, "y", env, p)
        w, h = self._num(el, "w", env, p, lo=0.5), self._num(el, "h", env, p, lo=0.5)
        iw, ih = 34 * 1.6, 34.0
        s = min(w / iw, h / ih)
        ox, oy = x + w - iw * s, y                                       # preserveAspectRatio="xMaxYMin meet"
        self.put_rect(out, ox + 4 * s, oy + 4 * s, (iw - 8) * s, (ih - 8) * s, 1 * s, "#999", "none")
        seg = {"top": (4, 4, iw - 4, 4), "bottom": (4, ih - 4, iw - 4, ih - 4), "left": (4, 4, 4, ih - 4), "right": (iw - 4, 4, iw - 4, ih - 4)}
        txt = {"top": (iw / 2, 12), "bottom": (iw / 2, ih - 7), "left": (10, ih / 2 + 3), "right": (iw - 10, ih / 2 + 3)}
        for sd in ("top", "bottom", "left", "right"):
            if not env.get(f"edge.{sd}.has"):
                continue
            x1, y1, x2, y2 = seg[sd]
            if int(env.get(f"edge.{sd}.lines") or 0) > 0:
                self.put_line(out, ox + x1 * s, oy + y1 * s, ox + x2 * s, oy + y2 * s, 3.5 * s, "#000")
            tx, ty = txt[sd]
            self.put_text(out, label_text(env.get(f"edge.{sd}.symbol")), 8 * s, ox + tx * s, oy + ty * s - 8 * s * 0.82, "middle")

    # — guruh (siljish + burish) —
    def _zgroup(self, el, env, out, p) -> None:
        rot = self._num(el, "rotate", env, p, 0.0, -360.0, 360.0)
        ox, oy = 0.0, 0.0
        o = el.get("origin")
        if o:
            ox = self._num({"v": o[0]}, "v", env, p, 0.0)
            oy = self._num({"v": o[1]}, "v", env, p, 0.0)
        saved = self._m
        self._m = mat_mul(saved, mat_mul(mat_translate(ox, oy), mat_rotate(rot)))
        try:
            self._elements(el.get("elements") or [], env, out, p + ".elements.")
        finally:
            self._m = saved

    # — etiketka bloki —
    def header_lines(self) -> list[str]:
        """`~` buyruqlari (masalan `~SD15` — qoraytirish: darhol bajariladigan boshqaruv buyruqlari) `^XA` dan OLDIN, qolgan sarlavha
        (`^PR`, `^MD`, `^CW` …) o'lcham buyruqlaridan keyin yoziladi."""
        z = self.zs
        pre, rest = split_header(z.header)
        head = [*pre, "^XA"]
        if z.utf8:
            head.append("^CI28")
        if z.emit_size:
            head.append(f"^PW{self.d(self.pw_mm)}")
            head.append(f"^LL{self.d(self.ll_mm)}")
        head.append("^LH0,0")
        if rest:
            head.append(rest)
        return head

    def zpl(self, env: dict) -> str:
        """Bitta etiketka: `^XA … ^XZ`."""
        self._m = self._root
        body = self.render_parts(env)
        return "\n".join([*self.header_lines(), *body, "^XZ"]) + "\n"


# ───────────────────────── Chop: loyiha qatorlari → ZPL fayl ─────────────────────────
@dataclass
class ZplResult:
    zpl: str = ""
    total: int = 0                 # chop etiketkalari jami
    rendered: int = 0              # matnda bor
    warnings: list = field(default_factory=list)       # [{code, key, count, message}]
    errors: list = field(default_factory=list)         # shablon ifoda xatolari (label_tpl bilan bir xil)
    template: str = ""
    template_name: str = ""
    truncated: bool = False
    dpi: int = 203


def _merge_warns(*lists: list[dict]) -> list[dict]:
    out: list[dict] = []
    seen: dict[tuple, dict] = {}
    for lst in lists:
        for w in lst:
            k = (w["code"], w.get("key", ""))
            if k in seen:
                seen[k]["count"] += w["count"]
            else:
                seen[k] = dict(w)
                out.append(seen[k])
    return out


def render_zpl(project: Project, lb: LBParams, settings: Optional[ZplSettings] = None, *, lang: str = "ru",
               limit: Optional[int] = None, scan: Optional[int] = None) -> ZplResult:
    """Loyiha qatorlari (`LBParams`) → ZPL. `limit` — matnga yoziladigan etiketkalar (None = hammasi, ≤ LB_MAX_LABELS: oshsa LabelsLimit);
    `scan` — ogohlantirish/xato qidirish uchun qo'shimcha hisoblanadigan (yozilmaydigan) etiketkalar."""
    lang = lang if lang in ("ru", "uz") else "ru"
    lb = lb.effective()                  # A4 rejimi: etiketka o'lchami sahifa va to'rdan hisoblanadi (LBParams.label_size)
    token = LANG.set(lang)
    try:
        settings = settings or ZplSettings()
        counts = count_items(project, lb)
        total = counts["total"]
        if limit is None and total > LB_MAX_LABELS:
            raise LabelsLimit(total)
        res = ZplResult(total=total, dpi=settings.dpi)
        try:
            tpl, src, warns = resolve_template(lb, lang)
        except TemplateError as e:
            res.errors.append({"path": "", "field": "", "expr": "", "message": str(e), "count": 1})
            return res
        res.template, res.template_name = src, str(tpl.get("name", ""))
        n_show = LB_MAX_LABELS if limit is None else limit
        n_run = n_show if limit is None else max(n_show, scan or 0)
        r = ZplRenderer(tpl, width_mm=lb.width_mm, height_mm=lb.height_mm, params=lb.params, lang=lang, settings=settings,
                        rotate_page=lb.rotate_page, fast_qr=total > 400)
        eb = EnvBuilder(project, lb, total, lang)
        blocks: list[str] = []
        ran = 0
        for it in iter_items(project, lb):
            if ran >= n_run:
                break
            z = r.zpl(eb.env(it))
            if ran < n_show:
                blocks.append(z)
            ran += 1
        res.zpl = "".join(blocks)
        res.rendered = len(blocks)
        res.truncated = total > len(blocks)
        res.errors = list(r.errors.values())
        res.warnings = _merge_warns([{"code": "tpl", "key": "", "count": 1, "message": w} for w in warns], r.zwarnings())
        return res
    finally:
        LANG.reset(token)


def render_zpl_sample(template: dict, *, width_mm: float, height_mm: float, params: Optional[dict] = None, kind: str = "part",
                      lang: str = "ru", settings: Optional[ZplSettings] = None, rotate_page: int = 0,
                      env: Optional[dict] = None) -> ZplResult:
    """Shablon + namuna ma'lumot (loyihasiz) → bitta etiketka ZPL (redaktor)."""
    lang = lang if lang in ("ru", "uz") else "ru"
    token = LANG.set(lang)
    try:
        settings = settings or ZplSettings()
        tpl = normalize_template(template)
        r = ZplRenderer(tpl, width_mm=width_mm, height_mm=height_mm, params=params, lang=lang, settings=settings,
                        rotate_page=rotate_page)
        e = dict(env) if env is not None else sample_env(kind, lang)
        z = r.zpl(e)
        return ZplResult(zpl=z, total=1, rendered=1, warnings=r.zwarnings(), errors=list(r.errors.values()),
                         template="embedded", template_name=str(tpl.get("name", "")), dpi=settings.dpi)
    finally:
        LANG.reset(token)

