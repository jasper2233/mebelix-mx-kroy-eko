"""DXF (ASCII) → XNC dasturi: kichik o'z parser (tashqi kutubxonasiz). Ixtiyoriy funksiya (W1).

Qoidalar yordamda yo'q (qatlam / rang ma'nosi noma'lum) — bu yerdagi qoidalar **bizniki**:
  • LINE, ARC, LWPOLYLINE (bulge bilan), POLYLINE+VERTEX, CIRCLE o'qiladi; boshqa obyektlar (ELLIPSE, SPLINE, INSERT, matn…)
    o'tkazib yuboriladi va ogohlantiriladi. Qatlam / rang e'tiborsiz.
  • Chiziq va yoylar uchlari mos tushsa (tol) zanjir-kontur bo'ladi: MillStart + MillLine / MillArcCenter.
  • CIRCLE: `drill_max_d` berilgan va diametr undan kichik / teng bo'lsa — frontal teshik (DrillFront), aks holda to'liq aylana kontur.
  • Koordinatalar: `origin="bbox"` — chizma chap-yuqori burchagi (0, 0) ga ko'chiriladi; `"zero"` — DXF koordinatalari o'zgarmaydi
    (faqat Y aks etadi: DXF da Y yuqoriga, XNC da pastga — `height` = detal eni yoki chizma balandligi). `flip_y=False` — Y aks etmaydi.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..i18n import _
from ..models import XncCommand

MAX_ENTITIES = 20_000
MAX_BYTES = 8_000_000


class DxfError(ValueError):
    pass


@dataclass
class Seg:
    kind: str                     # "line" | "arc"
    a: tuple[float, float]
    b: tuple[float, float]
    c: tuple[float, float] | None = None      # arc markazi
    ccw: bool = True                          # DXF (Y yuqoriga) bo'yicha soat miliga teskari

    def reversed(self) -> "Seg":
        return Seg(self.kind, self.b, self.a, self.c, (not self.ccw) if self.kind == "arc" else self.ccw)


def _decode(data: bytes) -> str:
    if data[:22].startswith(b"AutoCAD Binary DXF"):
        raise DxfError(_("xnc_dxf_binary"))
    for enc in ("utf-8-sig", "cp1251", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise DxfError(_("xnc_dxf_bad"))


def _pairs(text: str) -> list[tuple[int, str]]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = []
    for i in range(0, len(lines) - 1, 2):
        try:
            out.append((int(lines[i].strip()), lines[i + 1].strip()))
        except ValueError:
            raise DxfError(_("xnc_dxf_bad")) from None
    return out


def _f(v: str) -> float:
    try:
        x = float(v)
    except ValueError:
        raise DxfError(_("xnc_dxf_bad")) from None
    if not math.isfinite(x) or abs(x) > 1e7:
        raise DxfError(_("xnc_dxf_bad"))
    return x


def _bulge_arc(p1, p2, bulge: float) -> Seg:
    if abs(bulge) < 1e-9:
        return Seg("line", p1, p2)
    theta = 4 * math.atan(bulge)                           # imzoli markaziy burchak (CCW > 0)
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    chord = math.hypot(dx, dy)
    if chord < 1e-12:
        return Seg("line", p1, p2)
    nx, ny = -dy / chord, dx / chord                       # chap normal
    k = (chord / 2) / math.tan(theta / 2)
    mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    return Seg("arc", p1, p2, (mid[0] + nx * k, mid[1] + ny * k), bulge > 0)


def parse(data: bytes) -> tuple[list[Seg], list[tuple[float, float, float]], dict]:
    """(segmentlar, aylanalar [(cx, cy, r)], statistika {entities, skipped: {tur: soni}})."""
    if len(data) > MAX_BYTES:
        raise DxfError(_("xnc_dxf_big"))
    pairs = _pairs(_decode(data))
    # ENTITIES bo'limi
    start = next((i for i, (c, v) in enumerate(pairs) if c == 2 and v == "ENTITIES"), None)
    if start is None:
        raise DxfError(_("xnc_dxf_no_entities"))
    end = next((i for i in range(start, len(pairs)) if pairs[i] == (0, "ENDSEC")), len(pairs))
    body = pairs[start + 1:end]
    ents: list[tuple[str, list[tuple[int, str]]]] = []
    for c, v in body:
        if c == 0:
            ents.append((v, []))
        elif ents:
            ents[-1][1].append((c, v))
    if len(ents) > MAX_ENTITIES:
        raise DxfError(_("xnc_dxf_big"))
    segs: list[Seg] = []
    circles: list[tuple[float, float, float]] = []
    skipped: dict[str, int] = {}
    poly_verts: list[tuple[float, float, float]] | None = None
    poly_closed = False

    def flush_poly(vs, closed):
        n = len(vs)
        for i in range(n - 1 + (1 if closed else 0)):
            x1, y1, b = vs[i]
            x2, y2, _b = vs[(i + 1) % n]
            if (x1, y1) != (x2, y2):
                segs.append(_bulge_arc((x1, y1), (x2, y2), b))

    for kind, codes in ents:
        g = {}
        for c, v in codes:
            g.setdefault(c, []).append(v)
        first = lambda c, d=None: g[c][0] if c in g else d      # noqa: E731
        if kind == "LINE":
            p1, p2 = (_f(first(10, "0")), _f(first(20, "0"))), (_f(first(11, "0")), _f(first(21, "0")))
            if p1 != p2:
                segs.append(Seg("line", p1, p2))
        elif kind == "ARC":
            cx, cy, r = _f(first(10, "0")), _f(first(20, "0")), _f(first(40, "0"))
            a0, a1 = math.radians(_f(first(50, "0"))), math.radians(_f(first(51, "0")))
            if r > 0:
                segs.append(Seg("arc", (cx + r * math.cos(a0), cy + r * math.sin(a0)),
                                (cx + r * math.cos(a1), cy + r * math.sin(a1)), (cx, cy), True))
        elif kind == "CIRCLE":
            r = _f(first(40, "0"))
            if r > 0:
                circles.append((_f(first(10, "0")), _f(first(20, "0")), r))
        elif kind == "LWPOLYLINE":
            xs, ys = g.get(10, []), g.get(20, [])
            # bulge (42) har tepaga tegishli: kodlar tartibi bo'yicha qayta o'qiladi
            vs: list[list[float]] = []
            for c, v in codes:
                if c == 10:
                    vs.append([_f(v), 0.0, 0.0])
                elif c == 20 and vs:
                    vs[-1][1] = _f(v)
                elif c == 42 and vs:
                    vs[-1][2] = _f(v)
            if len(xs) != len(ys):
                raise DxfError(_("xnc_dxf_bad"))
            flush_poly([(a, b, c) for a, b, c in vs], int(first(70, "0") or 0) & 1 == 1)
        elif kind == "POLYLINE":
            poly_verts, poly_closed = [], int(first(70, "0") or 0) & 1 == 1
        elif kind == "VERTEX" and poly_verts is not None:
            poly_verts.append((_f(first(10, "0")), _f(first(20, "0")), _f(first(42, "0"))))
        elif kind == "SEQEND" and poly_verts is not None:
            flush_poly(poly_verts, poly_closed)
            poly_verts = None
        elif kind in ("POINT", "TEXT", "MTEXT", "DIMENSION", "HATCH", "LEADER", "SOLID", "VIEWPORT", "ATTRIB"):
            skipped[kind] = skipped.get(kind, 0) + 1
        else:
            skipped[kind] = skipped.get(kind, 0) + 1
    return segs, circles, dict(entities=len(ents), skipped=skipped)


def chains(segs: list[Seg], tol: float = 0.01) -> list[list[Seg]]:
    """Uchlari mos tushgan segmentlarni zanjirlarga (konturlarga) bog'laydi."""
    left = list(segs)
    out: list[list[Seg]] = []

    def near(p, q):
        return math.dist(p, q) <= tol

    def grow(chain: list[Seg]) -> None:
        while True:
            tail = chain[-1].b
            for i, s in enumerate(left):
                if near(s.a, tail):
                    chain.append(left.pop(i)); break
                if near(s.b, tail):
                    chain.append(left.pop(i).reversed()); break
            else:
                return
            if near(chain[-1].b, chain[0].a):
                return

    while left:
        chain = [left.pop(0)]
        grow(chain)
        if not near(chain[-1].b, chain[0].a):                      # ochiq — boshidan ham uzaytirish
            n0 = len(chain)
            chain = [s.reversed() for s in reversed(chain)]
            grow(chain)
            if len(chain) == n0:                                   # boshida davomi yo'q — asl yo'nalish saqlanadi
                chain = [s.reversed() for s in reversed(chain)]
        out.append(chain)
    return out


def _arc_extremes(s: Seg) -> list[tuple[float, float]]:
    """Yoyning chegara qutisiga ta'sir qiladigan o'q uchlari (0°, 90°, 180°, 270° yoy ichida bo'lsa)."""
    assert s.c is not None
    r = math.dist(s.a, s.c)
    a0 = math.atan2(s.a[1] - s.c[1], s.a[0] - s.c[0])
    a1 = math.atan2(s.b[1] - s.c[1], s.b[0] - s.c[0])
    sw = ((a1 - a0) if s.ccw else (a0 - a1)) % (2 * math.pi)
    out = []
    for k in range(4):
        th = k * math.pi / 2
        t = ((th - a0) if s.ccw else (a0 - th)) % (2 * math.pi)
        if t <= sw + 1e-12:
            out.append((s.c[0] + r * math.cos(th), s.c[1] + r * math.sin(th)))
    return out


def _r(v: float) -> float:
    r = round(v, 4)
    return 0.0 if r == 0 else r


def to_program(data: bytes, *, origin: str = "bbox", flip_y: bool = True, height: float | None = None, depth: str = "dz",
               tool_d: float = 6.0, correction: int = 0, drill_max_d: float | None = None, drill_depth: str = "dz",
               tol: float = 0.01) -> tuple[list[XncCommand], list[str], dict]:
    """DXF → (buyruqlar, ogohlantirishlar, statistika). `height` — Y aks ettirish balandligi (origin='zero' da; yo'q bo'lsa
    chizma balandligi). Tool nomlari: `Mill` (konturlar), `Bore<d>` (teshiklar)."""
    segs, circles, info = parse(data)
    warnings: list[str] = []
    for k, n in sorted(info["skipped"].items()):
        warnings.append(_("xnc_dxf_skipped", kind=k, n=n))
    if not segs and not circles:
        raise DxfError(_("xnc_dxf_empty"))
    pts = [p for s in segs for p in (s.a, s.b)] + [(cx + dx, cy + dy) for cx, cy, r in circles
                                                  for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r))]
    for s in segs:                                                       # yoy chegarasi: faqat yoy ichiga tushgan o'q uchlari
        if s.kind == "arc" and s.c:
            pts += _arc_extremes(s)
    minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
    miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
    ox = minx if origin == "bbox" else 0.0
    h = (maxy if origin == "bbox" else (height if height is not None else maxy))

    def tf(p):
        return (_r(p[0] - ox), _r((h - p[1]) if flip_y else (p[1] - (miny if origin == "bbox" else 0.0))))

    prog: list[XncCommand] = []
    cmd = lambda c, **p: XncCommand(cmd=c, params=p)     # noqa: E731
    dirs = lambda ccw: "false" if (ccw == flip_y) else "true"   # noqa: E731  (Y aks etilsa yo'nalish teskari)
    contours = chains(segs, tol)
    drills = [(c, r) for c, r in ((cc[:2], cc[2]) for cc in circles) if drill_max_d is not None and 2 * r <= drill_max_d + 1e-9]
    rings = [cc for cc in circles if not (drill_max_d is not None and 2 * cc[2] <= drill_max_d + 1e-9)]
    if contours or rings:
        prog.append(cmd("Tool", N="Mill", D=tool_d))
    for ch in contours:
        sx, sy = tf(ch[0].a)
        prog.append(cmd("MillStart", X=sx, Y=sy, DP=depth, T="Mill", C=correction))
        for s in ch:
            ex, ey = tf(s.b)
            if s.kind == "line":
                prog.append(cmd("MillLine", X=ex, Y=ey))
            else:
                cx, cy = tf(s.c)
                prog.append(cmd("MillArcCenter", X=ex, Y=ey, CX=cx, CY=cy, DIR=dirs(s.ccw)))
    for cx, cy, r in rings:
        sx, sy = tf((cx - r, cy))
        ccx, ccy = tf((cx, cy))
        prog.append(cmd("MillStart", X=sx, Y=sy, DP=depth, T="Mill", C=correction))
        prog.append(cmd("MillArcCenter", X=sx, Y=sy, CX=ccx, CY=ccy, DIR=dirs(True)))
    seen: dict[float, str] = {}
    for (cx, cy), r in drills:
        d = _r(2 * r)
        if d not in seen:
            seen[d] = f"Bore{d:g}"
            prog.append(cmd("Tool", N=seen[d], D=d))
        x, y = tf((cx, cy))
        prog.append(cmd("DrillFront", X=x, Y=y, DP=drill_depth, T=seen[d]))
    open_n = sum(1 for ch in contours if math.dist(ch[-1].b, ch[0].a) > tol)
    if open_n:
        warnings.append(_("xnc_dxf_open", n=open_n))
    stats = dict(entities=info["entities"], contours=len(contours), circles=len(rings), drills=len(drills), open=open_n,
                 bbox=[_r(minx), _r(miny), _r(maxx), _r(maxy)], size=[_r(maxx - minx), _r(maxy - miny)])
    return prog, warnings, stats
