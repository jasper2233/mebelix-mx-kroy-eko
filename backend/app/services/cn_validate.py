"""(CN) Nesting natijasini MUSTAQIL tekshirish (W16). `cn_nest` raster ishlatadi; bu modul esa ANIQ poligon geometriyasi bilan
(raster niqoblarga tayanmasdan) tekshiradi:

  1. har detal konturi foydali zona ichida (list chetidan ≥ margin);
  2. har ikki detal: konturlar kesishmaydi, bir-birining materialida (tashqi kontur ichida, teshikdan tashqarida) yotmaydi
     va chegaralar orasidagi eng kichik masofa ≥ spacing (ichki kesimdagi kichik detal — teshik chegarasidan ≥ spacing);
  3. aylantirish qoidalari (Ткт, ruxsat etilgan burchaklar), ko'zgu yo'q (faqat burish);
  4. detal soni ≤ ОК − МК, list nusxalari ≤ soni; saqlangan kontur (outline / holes) shakl + (burchak, x, y) dan qayta hisoblangan
     bilan mos.

`check_polys` — sof geometriya (poligonlar ro'yxati → xatolar); testlar uni va o'zining boshqa (skalyar) tekshiruvchisini ishlatadi.
Tolerantlik `EPS` = 1e-4 mm.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..i18n import _
from ..models import CNParams, CuttingResult, StockSheet
from . import cn_geometry as G
from . import cn_messages  # noqa: F401  (xabarlarni i18n.MSG ga qo'shadi)

EPS = 1e-4
UNLIMITED = 10000


@dataclass
class Poly:
    """Joylashgan detal (list koordinatalarida)."""
    uid: int
    outer: G.Ring
    holes: list[G.Ring]
    label: str = ""

    def __post_init__(self):
        a = np.asarray(self.outer, dtype=float)
        self.bb = (a[:, 0].min(), a[:, 1].min(), a[:, 0].max(), a[:, 1].max())
        segs = [a]
        for h in self.holes:
            segs.append(np.asarray(h, dtype=float))
        self.segs = np.concatenate([np.stack([s, np.roll(s, -1, axis=0)], axis=1) for s in segs], axis=0)   # (n, 2, 2)


def _in_ring(p, ring: G.Ring) -> bool:
    x, y = p
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def in_material(p, poly: Poly) -> bool:
    """Nuqta detal materialida (tashqi kontur ichida, ichki kesimlardan tashqarida)."""
    return _in_ring(p, poly.outer) and not any(_in_ring(p, h) for h in poly.holes)


def _cross2(ax, ay, bx, by):
    return ax * by - ay * bx


def segs_cross(A: np.ndarray, B: np.ndarray) -> bool:
    """A (n,2,2) va B (m,2,2) segmentlar orasida QAT'IY kesishuvchi (ikkala segmentning ichki nuqtasida) juftlik bormi."""
    p, r = A[:, 0, :], A[:, 1, :] - A[:, 0, :]
    q, s = B[:, 0, :], B[:, 1, :] - B[:, 0, :]
    rxs = _cross2(r[:, None, 0], r[:, None, 1], s[None, :, 0], s[None, :, 1])
    qp = q[None, :, :] - p[:, None, :]
    t_num = _cross2(qp[..., 0], qp[..., 1], s[None, :, 0], s[None, :, 1])
    u_num = _cross2(qp[..., 0], qp[..., 1], r[:, None, 0], r[:, None, 1])
    nz = np.abs(rxs) > 1e-12
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(nz, t_num / np.where(nz, rxs, 1.0), -1.0)
        u = np.where(nz, u_num / np.where(nz, rxs, 1.0), -1.0)
    e = 1e-9
    return bool(np.any(nz & (t > e) & (t < 1 - e) & (u > e) & (u < 1 - e)))


def _pt_seg_dist(P: np.ndarray, S: np.ndarray) -> np.ndarray:
    """P (k,2) nuqtalardan S (m,2,2) segmentlargacha masofalar (k, m)."""
    a, b = S[:, 0, :], S[:, 1, :]
    ab = b - a
    ab2 = np.maximum((ab ** 2).sum(axis=1), 1e-18)
    ap = P[:, None, :] - a[None, :, :]
    t = np.clip((ap * ab[None, :, :]).sum(axis=2) / ab2[None, :], 0.0, 1.0)
    proj = a[None, :, :] + t[..., None] * ab[None, :, :]
    d = P[:, None, :] - proj
    return np.sqrt((d ** 2).sum(axis=2))


def min_boundary_distance(A: np.ndarray, B: np.ndarray) -> float:
    """Ikki segmentlar to'plami orasidagi eng kichik masofa (kesishsa — 0). Kesishmasa uchlarning masofasi yetarli."""
    if segs_cross(A, B):
        return 0.0
    d1 = _pt_seg_dist(A[:, 0, :], B).min()
    d2 = _pt_seg_dist(B[:, 0, :], A).min()
    d3 = _pt_seg_dist(A[:, 1, :], B).min()
    d4 = _pt_seg_dist(B[:, 1, :], A).min()
    return float(min(d1, d2, d3, d4))


def inside_usable(p: Poly, length: float, width: float, margin: float) -> bool:
    bx0, by0, bx1, by1 = p.bb
    return not (bx0 < margin - EPS or by0 < margin - EPS or bx1 > length - margin + EPS or by1 > width - margin + EPS)


def conflicts(a: Poly, b: Poly, spacing: float) -> bool:
    """Ikki detal ziddiyatdami: kesishadi, bir-birining materialida yotadi yoki masofa < spacing."""
    if b.bb[0] > a.bb[2] + spacing + EPS or a.bb[0] > b.bb[2] + spacing + EPS:
        return False
    if b.bb[1] > a.bb[3] + spacing + EPS or a.bb[1] > b.bb[3] + spacing + EPS:
        return False
    if segs_cross(a.segs, b.segs) or in_material(a.outer[0], b) or in_material(b.outer[0], a):
        return True
    return min_boundary_distance(a.segs, b.segs) < spacing - EPS


def group_ok(moved: list[Poly], others: list[Poly], length: float, width: float, margin: float, spacing: float) -> bool:
    """Ko'chirilgan detallar guruhi: foydali zona ichida, bir-biri bilan va boshqalar bilan ziddiyatsiz (tahrir / sirpantirish uchun tez tekshiruv)."""
    for i, a in enumerate(moved):
        if not inside_usable(a, length, width, margin):
            return False
        for b in moved[i + 1:]:
            if conflicts(a, b, spacing):
                return False
        for b in others:
            if conflicts(a, b, spacing):
                return False
    return True


def check_polys(polys: list[Poly], length: float, width: float, margin: float, spacing: float) -> list[tuple[str, dict]]:
    """Sof geometriya: [(xato kaliti, parametrlar)]. Birinchi 20 ta xato."""
    errs: list[tuple[str, dict]] = []
    x0, y0, x1, y1 = margin - EPS, margin - EPS, length - margin + EPS, width - margin + EPS
    for p in polys:
        bx0, by0, bx1, by1 = p.bb
        if bx0 < x0 or by0 < y0 or bx1 > x1 or by1 > y1:
            errs.append(("cn.v_outside", dict(uid=p.uid, margin=f"{margin:g}")))
    n = len(polys)
    order = sorted(range(n), key=lambda i: polys[i].bb[0])
    for ai in range(n):
        a = polys[order[ai]]
        for bi in range(ai + 1, n):
            b = polys[order[bi]]
            if b.bb[0] > a.bb[2] + spacing + EPS:
                break
            if b.bb[1] > a.bb[3] + spacing + EPS or a.bb[1] > b.bb[3] + spacing + EPS:
                continue
            if segs_cross(a.segs, b.segs):
                errs.append(("cn.v_overlap", dict(a=a.uid, b=b.uid)))
            elif in_material(a.outer[0], b) or in_material(b.outer[0], a):
                errs.append(("cn.v_overlap", dict(a=a.uid, b=b.uid)))
            else:
                d = min_boundary_distance(a.segs, b.segs)
                if d < spacing - EPS:
                    errs.append(("cn.v_gap", dict(a=a.uid, b=b.uid, d=f"{d:.3f}", s=f"{spacing:g}")))
        if len(errs) >= 20:
            break
    return errs[:20]


# ───────────────────────── Natija darajasida ─────────────────────────
def angle_ok(angle: float, grain: bool, cn: CNParams) -> bool:
    """Burilish burchagi qoidalarga mosmi."""
    a = angle % 360.0
    near = lambda v, step: abs(((v + step / 2) % step) - step / 2) < 1e-6
    if grain and cn.use_grain:
        return abs(a) < 1e-6 or abs(a - 180.0) < 1e-6 or abs(a - 360.0) < 1e-6
    if abs(a) < 1e-6 or abs(a - 360.0) < 1e-6:
        return True
    if cn.rot90 and near(a, 90.0):
        return True
    if cn.rot_step > 0 and near(a, cn.rot_step):
        return True
    return False


def validate_cn(res: CuttingResult, shapes: dict[str, G.Shape], need: dict[str, int], grains: dict[str, bool],
                sheets: list[StockSheet], cn: CNParams, spacing: Optional[float] = None, final: bool = True,
                allow_empty: bool = False) -> list[str]:
    """Natijani to'liq tekshirish: xato matnlari ro'yxati (bo'sh — to'g'ri). `shapes` — part_id → Shape; `need` — part_id → ОК − МК.
    `spacing` berilmasa — `cn.spacing + cn.arc_tol` (yoy yaqinlashtirish xatosi zaxirasi)."""
    errs: list[str] = []
    s = (cn.spacing + cn.arc_tol) if spacing is None else spacing
    stock = {sh.id: sh for sh in sheets}
    used: Counter = Counter()
    placed: Counter = Counter()
    for m in res.maps:
        sh = stock.get(m.sheet_id)
        if sh is None:
            errs.append(_("cn.v_no_sheet", map=m.index))
            continue
        used[sh.id] += m.copies
        if not m.placements and not allow_empty:
            errs.append(_("cn.v_map_empty", map=m.index))
        polys: list[Poly] = []
        for pl in m.placements:
            shape = shapes.get(pl.part_id)
            if shape is None:
                errs.append(_("cn.v_no_part", uid=pl.part_uid))
                continue
            placed[pl.part_id] += m.copies
            if not angle_ok(pl.angle, grains.get(pl.part_id, False), cn):
                errs.append(_("cn.v_angle", uid=pl.part_uid, a=f"{pl.angle:g}"))
            outer, holes, _bw, _bh = G.place_shape(shape, pl.angle, pl.x, pl.y)
            if pl.outline:
                if len(pl.outline) != len(outer) or any(abs(a[0] - b[0]) > 1e-2 or abs(a[1] - b[1]) > 1e-2
                                                       for a, b in zip(pl.outline, outer)):
                    errs.append(_("cn.v_outline", uid=pl.part_uid))
            polys.append(Poly(pl.part_uid, outer, holes))
        if polys:
            for key, kw in check_polys(polys, m.sheet_length, m.sheet_width, cn.margin, s):
                errs.append(_(key, map=m.index, **kw))
    for pid, n in placed.items():
        if n > need.get(pid, 0):
            errs.append(_("cn.v_too_many", uid=next((pl.part_uid for m in res.maps for pl in m.placements if pl.part_id == pid), 0),
                          n=n, need=need.get(pid, 0)))
    for sid, n in used.items():
        sh = stock[sid]
        if sh.qty < UNLIMITED and n > sh.qty:
            errs.append(_("cn.v_sheets", size=f"{sh.length:g}×{sh.width:g}", n=n, q=sh.qty))
    return errs
