"""MillFillet (burchak yumaloqlash) geometriyasi — W18: chiziq–chiziq, chiziq–yoy, yoy–chiziq va yoy–yoy.

Toza geometriya (DB va XNC buyruqlarisiz): ikki qo'shni kontur segmenti (`Seg`: to'g'ri chiziq yoki markazli yoy) va radius `R` →
R radiusli aylana, ikkala segmentga urinadi va burchakning ichki tomonida yotadi. Natija: urinish nuqtalari `T1` (birinchi segmentda)
va `T2` (ikkinchisida), fillet markazi va yo'nalishi. Birinchi segment `T1` da tugaydi, ikkinchisi `T2` dan boshlanadi.

Qoida (hammasi bitta joyda):
* burilish tomoni `s` = ±1 — segmentlarning P burchagidagi yo'nalishlari vektor ko'paytmasining ishorasi (chapga +1);
* har segmentning `s` tomonga `R` ga siljitilgan nusxasi («offset»): to'g'ri chiziq — parallel chiziq; yoy — shu markazli aylana,
  radiusi `ρ − s·d·R` (`d` = +1 soat millariga teskari, −1 — soat bo'yicha; chapga siljish yoy ichkarisiga qarab bo'ladi);
* fillet markazi — ikkala offset kesishuvi (chiziq–chiziq: 1 nuqta; chiziq–yoy, yoy–yoy: ≤ 2 nuqta);
* nomzod yaroqli: ikkala urinish nuqtasi o'z segmentining ichida (boshi…P va P…oxiri) yotishi kerak; yaroqlilari orasidan P ga
  eng yaqin markaz tanlanadi;
* yaroqli nomzod yo'q: offsetlar umuman kesishmasa (parallel, bir markazli, ajralgan) — `"none"`; kesishsa-yu urinish nuqtalari
  segmentdan tashqarida bo'lsa (R katta) — `"big"`; segmentlar P da urinma yoki orqaga qaytsa (burchak yo'q) — `"flat"` (jim, o'zgarishsiz).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

TWO_PI = 2 * math.pi
FLAT_EPS_LINE = 1e-9          # ikki to'g'ri chiziq: yo'nalishlar vektor ko'paytmasi (burchaksiz deb hisoblash chegarasi)
FLAT_EPS_ARC = 1e-7           # yoy ishtirok etsa: urinma davomi (yoy markazlari qo'shimcha xato beradi)
POS_EPS = 1e-7                # segment ichida yotish tolerantligi (mm / rad)


@dataclass(frozen=True)
class Seg:
    """Kontur segmenti: `c is None` — to'g'ri chiziq a→b; aks holda a→b markazli yoy (`ccw` — soat millariga teskari)."""
    a: tuple[float, float]
    b: tuple[float, float]
    c: tuple[float, float] | None = None
    ccw: bool = True

    @property
    def is_arc(self) -> bool:
        return self.c is not None

    @property
    def d(self) -> int:
        return 1 if self.ccw else -1


@dataclass(frozen=True)
class Fillet:
    t1: tuple[float, float]            # birinchi segmentdagi urinish nuqtasi (u shu yerda tugaydi)
    t2: tuple[float, float]            # ikkinchi segmentdagi urinish nuqtasi (u shu yerdan boshlanadi)
    center: tuple[float, float]
    ccw: bool                          # fillet yoyining yo'nalishi (= burilish tomoni)
    radius: float


def _sub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def _cross(u, v) -> float:
    return u[0] * v[1] - u[1] * v[0]


def _dot(u, v) -> float:
    return u[0] * v[0] + u[1] * v[1]


def _unit(v):
    n = math.hypot(v[0], v[1])
    return (v[0] / n, v[1] / n) if n > 1e-15 else (0.0, 0.0)


def tangent(seg: Seg, p: tuple[float, float]) -> tuple[float, float]:
    """Segment bo'ylab harakat yo'nalishi (birlik vektor) `p` nuqtada."""
    if not seg.is_arc:
        return _unit(_sub(seg.b, seg.a))
    rv = _sub(p, seg.c)                                       # type: ignore[arg-type]
    n = _unit(rv)
    return (-n[1], n[0]) if seg.ccw else (n[1], -n[0])


def _ang(p, c) -> float:
    return math.atan2(p[1] - c[1], p[0] - c[0])


def arc_pos(seg: Seg, p: tuple[float, float]) -> float:
    """Yoy boshidan `p` gacha yoy bo'ylab burchak (rad, 0…2π), yoy yo'nalishida."""
    return (seg.d * (_ang(p, seg.c) - _ang(seg.a, seg.c))) % TWO_PI


def arc_total(seg: Seg) -> float:
    """Yoyning to'liq burilish burchagi (boshi = oxiri — to'liq aylana)."""
    sw = arc_pos(seg, seg.b)
    return TWO_PI if sw <= 1e-9 else sw


def _offset(seg: Seg, s: int, r: float):
    """Segmentning `s` tomoniga (+1 chap, −1 o'ng) `r` ga siljitilgani: ("L", nuqta, yo'nalish) | ("C", markaz, radius) | None."""
    if not seg.is_arc:
        u = _unit(_sub(seg.b, seg.a))
        n = (-u[1], u[0])
        return ("L", (seg.a[0] + s * r * n[0], seg.a[1] + s * r * n[1]), u)
    rho = math.dist(seg.a, seg.c) - s * seg.d * r             # type: ignore[arg-type]
    return ("C", seg.c, rho) if rho > 1e-9 else None


def _inter(o1, o2) -> list[tuple[float, float]]:
    k1, k2 = o1[0], o2[0]
    if k1 == "C" and k2 == "L":
        return _inter(o2, o1)
    if k1 == "L" and k2 == "L":
        (_, p1, u1), (_, p2, u2) = o1, o2
        det = _cross(u1, u2)
        if abs(det) < 1e-12:
            return []
        t = _cross(_sub(p2, p1), u2) / det
        return [(p1[0] + t * u1[0], p1[1] + t * u1[1])]
    if k1 == "L":                                             # chiziq – aylana
        (_, p, u), (_, c, rho) = o1, o2
        w = _sub(p, c)
        b = _dot(u, w)
        disc = b * b - (_dot(w, w) - rho * rho)
        if disc < -1e-9:
            return []
        sq = math.sqrt(max(0.0, disc))
        return [(p[0] + (-b + sg * sq) * u[0], p[1] + (-b + sg * sq) * u[1]) for sg in ((1,) if sq < 1e-12 else (-1, 1))]
    (_, c1, r1), (_, c2, r2) = o1, o2                         # aylana – aylana
    d = math.dist(c1, c2)
    if d < 1e-12 or d > r1 + r2 + 1e-9 or d < abs(r1 - r2) - 1e-9:
        return []
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, r1 * r1 - a * a))
    ux, uy = (c2[0] - c1[0]) / d, (c2[1] - c1[1]) / d
    mx, my = c1[0] + a * ux, c1[1] + a * uy
    if h < 1e-9:
        return [(mx, my)]
    return [(mx - h * uy, my + h * ux), (mx + h * uy, my - h * ux)]


def _foot(seg: Seg, c: tuple[float, float]) -> tuple[float, float]:
    """Fillet markazi `c` dan segmentga urinish nuqtasi (chiziq — tik oyoq, yoy — markazdan `c` tomon radiusning uchi)."""
    if not seg.is_arc:
        u = _unit(_sub(seg.b, seg.a))
        t = _dot(_sub(c, seg.a), u)
        return (seg.a[0] + t * u[0], seg.a[1] + t * u[1])
    r = math.dist(seg.a, seg.c)                               # type: ignore[arg-type]
    n = _unit(_sub(c, seg.c))                                 # type: ignore[arg-type]
    return (seg.c[0] + r * n[0], seg.c[1] + r * n[1])         # type: ignore[index]


def _within(seg: Seg, p: tuple[float, float]) -> bool:
    """`p` (segment chizig'idagi nuqta) segmentning boshi…oxiri oralig'idami."""
    if not seg.is_arc:
        u = _unit(_sub(seg.b, seg.a))
        ln = math.dist(seg.a, seg.b)
        t = _dot(_sub(p, seg.a), u)
        return -POS_EPS <= t <= ln + POS_EPS
    pos = arc_pos(seg, p)
    if pos > TWO_PI - POS_EPS:
        pos = 0.0
    return pos <= arc_total(seg) + POS_EPS


def fillet(s1: Seg, s2: Seg, r: float) -> Fillet | str:
    """`s1` (…→P) va `s2` (P→…) orasidagi P burchagini `r` radius bilan yumaloqlaydi. Qaytaradi: `Fillet` yoki xato kodi:
    "flat" (burchak yo'q), "none" (urinma aylana yo'q), "big" (radius segmentlar uchun katta)."""
    if r <= 0:
        return "flat"
    p = s1.b
    t1v, t2v = tangent(s1, p), tangent(s2, p)
    cr = _cross(t1v, t2v)
    eps = FLAT_EPS_ARC if (s1.is_arc or s2.is_arc) else FLAT_EPS_LINE
    if abs(cr) < eps:
        return "flat"
    s = 1 if cr > 0 else -1
    o1, o2 = _offset(s1, s, r), _offset(s2, s, r)
    if o1 is None or o2 is None:
        return "big"
    cands = _inter(o1, o2)
    if not cands:
        return "none"
    best: tuple[float, Fillet] | None = None
    for c in cands:
        a, b = _foot(s1, c), _foot(s2, c)
        if not (_within(s1, a) and _within(s2, b)):
            continue
        sw = ((_ang(b, c) - _ang(a, c)) * s) % TWO_PI
        if sw < 1e-9 or sw > TWO_PI - 1e-9:
            continue
        dist = math.dist(c, p)
        if best is None or dist < best[0]:
            best = (dist, Fillet(a, b, c, s > 0, r))
    return best[1] if best else "big"
