"""W16 (CN) testlari uchun yordamchilar: shakllar va MUSTAQIL (skalyar, numpy'siz) geometriya tekshiruvchisi.

`cn_validate` (numpy, vektorlashtirilgan) dan KOD jihatdan alohida yozilgan: segment kesishishi — orientatsiya testi, masofa — nuqta-segment
masofalari; ikkalasi bir-birini tekshiradi."""
from __future__ import annotations

import math

from app.services import cn_geometry as G


# ───────────────────────── Shakllar ─────────────────────────
def circle_ring(cx: float, cy: float, r: float, n: int = 28):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def shape_circle(r: float, n: int = 28) -> G.Shape:
    return G.Shape(outer=G.orient_ring(circle_ring(r, r, r, n), True), kind="contour", src=(2 * r, 2 * r))


def shape_L(a: float, b: float, t: float) -> G.Shape:
    return G.Shape(outer=[(0, 0), (a, 0), (a, t), (t, t), (t, b), (0, b)], kind="contour", src=(a, b))


def shape_ring(L: float, W: float, hl: float, hw: float) -> G.Shape:
    """To'rtburchak (L × W) o'rtasida hl × hw teshik."""
    x0, y0 = (L - hl) / 2, (W - hw) / 2
    hole = [(x0, y0), (x0, y0 + hw), (x0 + hl, y0 + hw), (x0 + hl, y0)]          # manfiy orientatsiya
    return G.Shape(outer=G.rect_ring(L, W), holes=[G.orient_ring(hole, False)], kind="contour", src=(L, W))


def shape_round_hole(L: float, W: float, hr: float, n: int = 28) -> G.Shape:
    hole = G.orient_ring(circle_ring(L / 2, W / 2, hr, n), False)
    return G.Shape(outer=G.rect_ring(L, W), holes=[hole], kind="contour", src=(L, W))


# ───────────────────────── Skalyar geometriya ─────────────────────────
def _orient(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def seg_cross_strict(a, b, c, d) -> bool:
    """AB va CD QAT'IY kesishadimi (ikkalasining ichki nuqtasida; uchlari tegishi hisobga olinmaydi)."""
    o1, o2, o3, o4 = _orient(a, b, c), _orient(a, b, d), _orient(c, d, a), _orient(c, d, b)
    return ((o1 > 1e-9 and o2 < -1e-9) or (o1 < -1e-9 and o2 > 1e-9)) and ((o3 > 1e-9 and o4 < -1e-9) or (o3 < -1e-9 and o4 > 1e-9))


def pt_seg_dist(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def seg_seg_dist(a, b, c, d) -> float:
    if seg_cross_strict(a, b, c, d):
        return 0.0
    return min(pt_seg_dist(a, c, d), pt_seg_dist(b, c, d), pt_seg_dist(c, a, b), pt_seg_dist(d, a, b))


def point_in_ring(p, ring) -> bool:
    x, y = p
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                inside = not inside
    return inside


def in_material(p, outer, holes) -> bool:
    return point_in_ring(p, outer) and not any(point_in_ring(p, h) for h in holes)


def _segs(ring):
    return [(ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring))]


def _seg_box(s, pad=0.0):
    (x1, y1), (x2, y2) = s
    return min(x1, x2) - pad, min(y1, y2) - pad, max(x1, x2) + pad, max(y1, y2) + pad


def poly_gap(A, B, limit: float) -> float:
    """A = (outer, holes), B = (outer, holes): konturlar orasidagi eng kichik masofa, lekin `limit` dan katta bo'lsa — limit (tez)."""
    sa = [s for r in (A[0], *A[1]) for s in _segs(r)]
    sb = [s for r in (B[0], *B[1]) for s in _segs(r)]
    best = limit
    boxes_b = [_seg_box(s, limit) for s in sb]
    for s in sa:
        bx0, by0, bx1, by1 = _seg_box(s)
        for t, bb in zip(sb, boxes_b):
            if bx1 < bb[0] or bx0 > bb[2] or by1 < bb[1] or by0 > bb[3]:
                continue
            d = seg_seg_dist(s[0], s[1], t[0], t[1])
            if d < best:
                best = d
                if best == 0.0:
                    return 0.0
    return best


def bbox_of(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def check_sheet(polys, length, width, margin, spacing, eps: float = 1e-3) -> list[str]:
    """polys: [(outer, holes)] bitta list. Xatolar ro'yxati (bo'sh — to'g'ri)."""
    errs: list[str] = []
    for i, (o, h) in enumerate(polys):
        x0, y0, x1, y1 = bbox_of(o)
        if x0 < margin - eps or y0 < margin - eps or x1 > length - margin + eps or y1 > width - margin + eps:
            errs.append(f"outside:{i}")
    for i in range(len(polys)):
        bi = bbox_of(polys[i][0])
        for j in range(i + 1, len(polys)):
            bj = bbox_of(polys[j][0])
            if bj[0] > bi[2] + spacing + 1 or bi[0] > bj[2] + spacing + 1 or bj[1] > bi[3] + spacing + 1 or bi[1] > bj[3] + spacing + 1:
                continue
            A, B = polys[i], polys[j]
            # kesishish / bir-birining materialida yotish
            if any(seg_cross_strict(s[0], s[1], t[0], t[1]) for s in (u for r in (A[0], *A[1]) for u in _segs(r))
                   for t in (u for r in (B[0], *B[1]) for u in _segs(r))):
                errs.append(f"cross:{i}-{j}")
                continue
            if in_material(A[0][0], B[0], B[1]) or in_material(B[0][0], A[0], A[1]):
                errs.append(f"inside:{i}-{j}")
                continue
            d = poly_gap(A, B, spacing + 1.0)
            if d < spacing - eps:
                errs.append(f"gap:{i}-{j}:{d:.3f}<{spacing}")
    return errs
