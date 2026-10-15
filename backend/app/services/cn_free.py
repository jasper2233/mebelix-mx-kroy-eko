"""(CN) Bo'sh joy geometriyasi (W16): qoldiq to'rtburchaklar va etiketka o'rni.

1. `free_rectangles` — UPD-001: nesting qoldiqlari. Detallar bilan band bo'lmagan joydagi eng katta to'rtburchaklar — shu jumladan
   detal ICHKI kesimlarida (teshik / oyna). Qidiruv — qo'pol raster (≤ 60 000 katak) + «gistogramma» usulida eng katta bo'sh to'rtburchak;
   topilgani ANIQ geometriya bilan (poligon chegaralarigacha masofa ≥ spacing) har tomonga kengaytiriladi. Qoldiq ham boshqa
   qoldiqdan `spacing` masofada (kesim o'tishi uchun). Ruxsat: ikkala tomon ≥ `min_side1 / min_side2`; maydon ≥ `min_area` — деловой.
2. `find_label_spot` — UPD-002: etiketka o'rni. Detal ichidagi ishlov belgisi (teshik, freza yo'li, paz) va kontur chetidan
   `LABEL_CLEAR` uzoq eng katta bo'sh to'rtburchak; etiketka (w × h) sig'sa — uning markaziga qo'yiladi (oddiy variant).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

from . import cn_geometry as G
from .cn_nest import choose_cell, dilate, raster_rings
from .cn_validate import Poly, _pt_seg_dist, in_material

LABEL_CLEAR = 3.0           # etiketka — kontur va ishlov chetidan eng kam masofa, mm
COARSE_CELLS = 60_000
MAX_FREE = 12


@dataclass
class FreeRect:
    x: float
    y: float
    w: float
    h: float
    raw: tuple[float, float, float, float]      # list chetigacha kengaytirilgan (x0, y0, x1, y1)
    in_part: int = 0                            # ichki kesimi egasi detal uid (0 — detalsiz joy)

    @property
    def area(self) -> float:
        return self.w * self.h


# ───────────────────────── Eng katta bo'sh to'rtburchak (gistogramma) ─────────────────────────
def largest_rect(free: np.ndarray, min_a: int = 1, min_b: int = 1) -> Optional[tuple[int, int, int, int, int]]:
    """Bool xaritadagi eng katta (maydon bo'yicha) bo'sh to'rtburchak: (maydon, r0, c0, r1, c1) (r1, c1 — kiritilmaydi) yoki None.
    Shart: tomonlar (a, b) ≥ (min_a, min_b) har ikki tartibda (a ≥ min_a va b ≥ min_b) yoki (a ≥ min_b va b ≥ min_a)."""
    hgt, wid = free.shape
    heights = np.zeros(wid, dtype=np.int32)
    best = None
    best_area = 0
    hi, lo = max(min_a, min_b), min(min_a, min_b)
    for r in range(hgt):
        heights = np.where(free[r], heights + 1, 0)
        hl = heights.tolist()
        hl.append(0)
        stack: list[tuple[int, int]] = []              # (boshlanish ustuni, balandlik)
        for j, hv in enumerate(hl):
            start = j
            while stack and stack[-1][1] >= hv:
                sj, sh = stack.pop()
                ww = j - sj
                if sh > 0 and ((sh >= hi and ww >= lo) or (sh >= lo and ww >= hi)):
                    ar = sh * ww
                    if ar > best_area:
                        best_area, best = ar, (ar, r - sh + 1, sj, r + 1, sj + ww)
                start = sj
            stack.append((start, hv))
    return best


# ───────────────────────── Aniq masofa predikatlari ─────────────────────────
def _pt_rect_dist(P: np.ndarray, x0: float, y0: float, x1: float, y1: float) -> np.ndarray:
    dx = np.maximum(np.maximum(x0 - P[:, 0], P[:, 0] - x1), 0.0)
    dy = np.maximum(np.maximum(y0 - P[:, 1], P[:, 1] - y1), 0.0)
    return np.hypot(dx, dy)


def _seg_hits_open_rect(S: np.ndarray, x0: float, y0: float, x1: float, y1: float) -> bool:
    """S (n,2,2) segmentlardan birortasi ochiq to'rtburchak ichidan o'tadimi (Liang–Barsky, qat'iy)."""
    e = 1e-9
    xa, ya = S[:, 0, 0], S[:, 0, 1]
    dx, dy = S[:, 1, 0] - xa, S[:, 1, 1] - ya
    t0 = np.zeros(len(S))
    t1 = np.ones(len(S))
    ok = np.ones(len(S), dtype=bool)
    for p, q in ((-dx, xa - x0 - e), (dx, x1 - e - xa), (-dy, ya - y0 - e), (dy, y1 - e - ya)):
        zero = np.abs(p) < 1e-15
        ok &= ~(zero & (q < 0))
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.where(zero, 0.0, q / np.where(zero, 1.0, p))
        neg = (p < 0) & ~zero
        pos = (p > 0) & ~zero
        t0 = np.where(neg, np.maximum(t0, r), t0)
        t1 = np.where(pos, np.minimum(t1, r), t1)
    return bool(np.any(ok & (t0 < t1 - 1e-12)))


def rect_clear(rect: tuple[float, float, float, float], polys: list[Poly], spacing: float,
               others: list[tuple[float, float, float, float]]) -> bool:
    """To'rtburchak (x0, y0, x1, y1) har detaldan kamida `spacing` uzoqda (Evklid), detal ichida yotmaydi va boshqa qoldiqlardan ≥ spacing."""
    x0, y0, x1, y1 = rect
    for o in others:
        if not (x1 + spacing <= o[0] or o[2] + spacing <= x0 or y1 + spacing <= o[1] or o[3] + spacing <= y0):
            return False
    corners = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], dtype=float)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for p in polys:
        bx0, by0, bx1, by1 = p.bb
        if bx0 > x1 + spacing or bx1 < x0 - spacing or by0 > y1 + spacing or by1 < y0 - spacing:
            continue
        S = p.segs
        if _seg_hits_open_rect(S, x0, y0, x1, y1):
            return False
        if in_material((cx, cy), p):
            return False
        if spacing > 0:
            d = min(float(_pt_rect_dist(S[:, 0, :], x0, y0, x1, y1).min()),
                    float(_pt_rect_dist(S[:, 1, :], x0, y0, x1, y1).min()),
                    float(_pt_seg_dist(corners, S).min()))
            if d < spacing - 1e-6:
                return False
    return True


def _grow(rect, bounds, polys, spacing, others, tol: float = 0.25):
    """To'rtburchakni har tomonga aniq predikat bo'yicha kengaytirish (ikkilik qidiruv; ikki aylanish)."""
    x0, y0, x1, y1 = rect
    bx0, by0, bx1, by1 = bounds
    for _round in range(2):
        for side in ("r", "b", "l", "t"):
            cur = (x0, y0, x1, y1)
            room = {"r": bx1 - x1, "b": by1 - y1, "l": x0 - bx0, "t": y0 - by0}[side]
            if room <= tol:
                continue

            def mk(e: float):
                return {"r": (x0, y0, x1 + e, y1), "b": (x0, y0, x1, y1 + e), "l": (x0 - e, y0, x1, y1),
                        "t": (x0, y0 - e, x1, y1)}[side]
            if rect_clear(mk(room), polys, spacing, others):
                e = room
            else:
                lo, hi = 0.0, room
                while hi - lo > tol:
                    mid = (lo + hi) / 2
                    if rect_clear(mk(mid), polys, spacing, others):
                        lo = mid
                    else:
                        hi = mid
                e = lo
            if e > 0:
                x0, y0, x1, y1 = mk(e)
            del cur
    return x0, y0, x1, y1


# ───────────────────────── Qoldiq to'rtburchaklar ─────────────────────────
def free_rectangles(polys: list[Poly], length: float, width: float, margin: float, spacing: float,
                    min_side1: float, min_side2: float, limit: int = MAX_FREE) -> list[FreeRect]:
    """Detallar orasidagi eng katta bo'sh to'rtburchaklar (kamayish tartibida). Foydali zona — list − margin. Har qoldiq: foydali
    zonadagi (x, y, w, h) va list chetigacha kengaytirilgan xom o'lcham. Qoldiq tomonlari ≥ (min_side1, min_side2)."""
    Lu, Wu = length - 2 * margin, width - 2 * margin
    if Lu <= 0 or Wu <= 0:
        return []
    rc = choose_cell(Lu, Wu, COARSE_CELLS, 100.0)
    nx, ny = int(Lu / rc + 1e-9), int(Wu / rc + 1e-9)
    if nx < 1 or ny < 1:
        return []
    occ = np.zeros((ny, nx), dtype=bool)
    rho = spacing / rc
    for p in polys:
        mask, i0, j0 = raster_rings([p.outer, *p.holes], rc, margin, margin)
        D, R = dilate(mask, rho)
        _paste(occ, D, j0 - R, i0 - R)
    s_lo, s_hi = sorted((min_side1, min_side2))
    ma, mb = max(1, int(math.ceil(s_hi / rc))), max(1, int(math.ceil(s_lo / rc)))
    bounds = (margin, margin, length - margin, width - margin)
    out: list[FreeRect] = []
    taken: list[tuple[float, float, float, float]] = []
    for _it in range(limit):
        got = largest_rect(~occ, ma, mb)
        if got is None:
            break
        _ar, r0, c0, r1, c1 = got
        rect = (margin + c0 * rc, margin + r0 * rc, margin + c1 * rc, margin + r1 * rc)
        rect = (rect[0], rect[1], min(rect[2], bounds[2]), min(rect[3], bounds[3]))
        if not rect_clear(rect, polys, spacing, taken):
            # qo'pol xarita yaxlitlash xatosi: kataklarni egallangan deb belgilab, keyingisini izlaymiz
            occ[r0:r1, c0:c1] = True
            continue
        rect = _grow(rect, bounds, polys, spacing, taken)
        w, h = rect[2] - rect[0], rect[3] - rect[1]
        a, b = max(w, h), min(w, h)
        if a >= s_hi - 1e-6 and b >= s_lo - 1e-6:
            fx0 = 0.0 if rect[0] <= margin + 1e-6 else rect[0]
            fy0 = 0.0 if rect[1] <= margin + 1e-6 else rect[1]
            fx1 = length if rect[2] >= length - margin - 1e-6 else rect[2]
            fy1 = width if rect[3] >= width - margin - 1e-6 else rect[3]
            cx, cy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
            host = 0
            for p in polys:
                if any(G.point_in_ring((cx, cy), h_) for h_ in p.holes) and G.point_in_ring((cx, cy), p.outer):
                    host = p.uid
                    break
            out.append(FreeRect(rect[0], rect[1], w, h, (fx0, fy0, fx1, fy1), host))
            taken.append(rect)
        # band qilish: qoldiq + atrofidagi spacing (keyingi qoldiq undan kesim masofasida)
        pad = int(math.ceil(spacing / rc)) + 1
        ra, rb = max(0, int((rect[1] - margin) / rc) - pad), min(ny, int(math.ceil((rect[3] - margin) / rc)) + pad)
        ca, cb = max(0, int((rect[0] - margin) / rc) - pad), min(nx, int(math.ceil((rect[2] - margin) / rc)) + pad)
        occ[ra:rb, ca:cb] = True
    out.sort(key=lambda f: -f.area)
    return out


def _paste(dst: np.ndarray, src: np.ndarray, j0: int, i0: int) -> None:
    """src ni dst ga (satr j0, ustun i0 dan) OR bilan qo'shish (chegaradan chiqqani kesiladi)."""
    h, w = src.shape
    ya, xa = max(0, j0), max(0, i0)
    yb, xb = min(dst.shape[0], j0 + h), min(dst.shape[1], i0 + w)
    if ya >= yb or xa >= xb:
        return
    dst[ya:yb, xa:xb] |= src[ya - j0:yb - j0, xa - i0:xb - i0]


# ───────────────────────── Etiketka o'rni ─────────────────────────
def find_label_spot(shape: G.Shape, label_w: float, label_h: float, clear: float = LABEL_CLEAR) -> dict:
    """Detal (o'z koordinatalarida) ichida ishlov belgisi va chetdan `clear` uzoq eng katta bo'sh to'rtburchak.
    Qaytaradi: {x, y, w, h (bo'sh to'rtburchak), label: [cx, cy, w, h, burchak(0|90)] yoki None, fits}. Etiketka sig'sa — to'rtburchak
    markaziga (w × h, sig'masa 90° ga burilgan); sig'masa — label None va `fits` False (eng katta bo'sh to'rtburchak qaytariladi)."""
    bw, bh = shape.bbox_size
    mk0 = shape.marks or {}
    lw, lh = max(label_w, 0.0), max(label_h, 0.0)
    if shape.is_rect and not (mk0.get("drills") or mk0.get("paths") or mk0.get("grooves")):
        # oddiy to'rtburchak, ishlovsiz: butun ichki zona bo'sh — etiketka markazga (raster kerak emas)
        iw, ih = bw - 2 * clear, bh - 2 * clear
        if iw <= 0 or ih <= 0:
            return dict(x=0.0, y=0.0, w=0.0, h=0.0, label=None, fits=False)
        cx, cy = bw / 2, bh / 2
        label = None
        if lw > 0 and lh > 0:
            if iw >= lw and ih >= lh:
                label = [cx, cy, lw, lh, 0.0]
            elif iw >= lh and ih >= lw:
                label = [cx, cy, lh, lw, 90.0]
        return dict(x=clear, y=clear, w=iw, h=ih, label=label, fits=label is not None)
    c = max(choose_cell(bw, bh, 60_000, 100.0), 1.0)
    inside, touch, i0, j0 = raster_rings([shape.outer, *shape.holes], c, 0.0, 0.0, split=True)
    h, w = inside.shape
    blocked = touch.copy()
    gx = (np.arange(w) + 0.5) * c + i0 * c
    gy = (np.arange(h) + 0.5) * c + j0 * c
    mk = shape.marks or {}
    for x, y, r in mk.get("drills", []):
        rr = r + clear
        ia, ib = max(0, int((x - rr) / c) - i0 - 1), min(w, int((x + rr) / c) - i0 + 2)
        ja, jb = max(0, int((y - rr) / c) - j0 - 1), min(h, int((y + rr) / c) - j0 + 2)
        if ia < ib and ja < jb:
            xx, yy = np.meshgrid(gx[ia:ib], gy[ja:jb])
            blocked[ja:jb, ia:ib] |= np.hypot(xx - x, yy - y) <= rr + c * 0.71
    segs: list[tuple[float, float, float, float, float]] = []
    for pts, hw in mk.get("paths", []):
        for a, b in zip(pts[:-1], pts[1:]):
            segs.append((a[0], a[1], b[0], b[1], hw + clear))
    for x1, y1, x2, y2, hw in mk.get("grooves", []):
        segs.append((x1, y1, x2, y2, hw + clear))
    for x1, y1, x2, y2, rr in segs:
        ia, ib = max(0, int((min(x1, x2) - rr) / c) - i0 - 1), min(w, int((max(x1, x2) + rr) / c) - i0 + 2)
        ja, jb = max(0, int((min(y1, y2) - rr) / c) - j0 - 1), min(h, int((max(y1, y2) + rr) / c) - j0 + 2)
        if ia >= ib or ja >= jb:
            continue
        xx, yy = np.meshgrid(gx[ia:ib], gy[ja:jb])
        dx, dy = x2 - x1, y2 - y1
        l2 = max(dx * dx + dy * dy, 1e-12)
        t = np.clip(((xx - x1) * dx + (yy - y1) * dy) / l2, 0.0, 1.0)
        blocked[ja:jb, ia:ib] |= np.hypot(xx - (x1 + t * dx), yy - (y1 + t * dy)) <= rr + c * 0.71
    D, R = dilate(blocked, clear / c)
    blocked_d = D[R:R + h, R:R + w]
    free = inside & ~blocked_d
    ma, mb = max(1, int(math.ceil(lw / c))), max(1, int(math.ceil(lh / c)))
    got = largest_rect(free, ma, mb) if lw > 0 and lh > 0 else None
    fits = got is not None
    if got is None:
        got = largest_rect(free, 1, 1)
        if got is None:
            return dict(x=0.0, y=0.0, w=0.0, h=0.0, label=None, fits=False)
    _ar, r0, c0, r1, c1 = got
    x0, y0 = (c0 + i0) * c, (r0 + j0) * c
    rw, rh = (c1 - c0) * c, (r1 - r0) * c
    label = None
    if fits:
        cx, cy = x0 + rw / 2, y0 + rh / 2
        label = [cx, cy, lw, lh, 0.0] if (rw >= lw - 1e-9 and rh >= lh - 1e-9) else [cx, cy, lh, lw, 90.0]
    return dict(x=x0, y=y0, w=rw, h=rh, label=label, fits=fits)
