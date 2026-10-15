"""Ikkinchi guruh ishlov markazi formatlari (Daron, HIRZT, KDT, Nanxing SyntecCad, XDWoodCam) uchun umumiy yordamchilar.

Asosiy amallar ro'yxati — `_cnc.machine_ops` (orqa tomon X bo'yicha ag'darilgan). Bu yerda: son formati, yoy burchagi,
detal ma'lumoti (material, tekstura, buyurtma satri, kromka bayroqlari) va frezalangan detal konturi (`cut_outline`).
"""
from __future__ import annotations

import math
from typing import Optional

from . import _cnc as C


def num(v: float, nd: int = 4) -> str:
    """`nd` kasrgacha yaxlitlab, ortiqcha nollarsiz («-0» → «0»)."""
    v = round(float(v), nd)
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def sweep(p0, o: dict) -> float:
    """Yoy burilish burchagi (gradus) `p0` dan `o` (mac) oxirigacha: `ccw` (XNC dir="true") — musbat, aks holda manfiy."""
    a0 = math.atan2(p0[1] - o["cy"], p0[0] - o["cx"])
    a1 = math.atan2(o["y"] - o["cy"], o["x"] - o["cx"])
    sw = math.degrees(a1 - a0)
    if o["ccw"] and sw < 0:
        sw += 360
    if not o["ccw"] and sw > 0:
        sw -= 360
    return sw


def xml_attr(s) -> str:
    """XML atribut qiymati: `& < > "` ekranlanadi, qator ko'chirish olib tashlanadi."""
    s = C.one_line(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def xml_text(s) -> str:
    s = C.one_line(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def edge_flags(job) -> dict[str, bool]:
    """Kromka bayroqlari XNC tomonlari bo'yicha: t (y=0), b (y=dy), l (x=0), r (x=dx); orqa tomonda l ↔ r."""
    f = {k: False for k in "tblr"}
    for side, _e in C.edges(job):
        f[side[0]] = True
    if not job.face:
        f["l"], f["r"] = f["r"], f["l"]
    return f


def cs_material(job) -> str:
    """Detal joylashgan kroy (CS) operatsiyasining nomi (material)."""
    from ...models import OpType
    for o in job.project.operations:
        if o.type == OpType.CS and any(job.op.id in p.xnc_op_ids for p in o.parts):
            return o.name or o.code or ""
    return ""


def product_order(job) -> str:
    """Detal mahsulotining «Данные заказа» satri (`product.order`)."""
    from . import order_text
    p = C.part_of(job)
    if p is None or not p.product_id:
        return ""
    for pr in job.project.products:
        if pr.id == p.product_id:
            return order_text(job.project, pr.order_info or "")
    return ""


# ───────────────────────── frezalangan detal konturi ─────────────────────────
# Hammasi YUZ tomon XNC koordinatasida (X o'ngga, Y pastga). Ko'pburchak — yopilmagan siklik ro'yxat, yo'nalishi
# (0,W) → (0,0) → (L,0) → (L,W) (shoelace > 0); birinchi nuqta — «chok» (ro'yxat boshi).
EPS = 1e-7
TOL = 1e-4          # mm: burchak yaqinidagi kesishuv / nuqtalarni birlashtirish chegarasi


def part_contours(job) -> list[list[dict]]:
    """Detalning BARCHA XNC dasturlaridagi o'tuvchi (chuqurlik ≥ qalinlik) frezalash konturlari — yuz tomon
    koordinatasida (orqa tomon dasturi konturlari X bo'yicha ag'dariladi). Kontur detalning istalgan tomonidan
    frezalansa ham detal shakli o'zgaradi."""
    from . import drill_job
    p = C.part_of(job)
    jobs = [job]
    if p is not None:
        jobs = []
        for o in job.project.operations:
            if o.id in p.xnc_op_ids and o.xnc is not None:
                jobs.append(job if o.id == job.op.id else drill_job(job.project, o))
    res = []
    for j in jobs:
        for cont in C.contours(C.machine_ops(j)):
            if len(cont) > 1 and cont[0]["dp"] >= j.dz - 1e-6:
                res.append(cont)
    return res


def arc_segments(r: float, sw_deg: float) -> int:
    """Yoy vatarlari soni — namunalardan tanlangan empirik qoida (r=6/90° → 5, r=10/90° → 7, r=27/63° → 7,
    r=150/90° → 23)."""
    return max(1, int(math.ceil(abs(sw_deg) / 90.0 * 1.955 * max(r, 1e-9) ** 0.49 - 1e-9)))


def polyline(cont: list[dict]) -> list[tuple[float, float]]:
    """Kontur → siniq chiziq (yoylar teng burchakli vatarlarga bo'linadi)."""
    pts = [(cont[0]["x"], cont[0]["y"])]
    for o in cont[1:]:
        if o["t"] == "mac":
            p0 = pts[-1]
            cx, cy = o["cx"], o["cy"]
            r = math.hypot(o["x"] - cx, o["y"] - cy)      # oraliq nuqtalar — oxirgi nuqta radiusida (namunalardagi kabi)
            sw = math.radians(sweep(p0, o))
            a0 = math.atan2(p0[1] - cy, p0[0] - cx)
            n = arc_segments(r, math.degrees(sw))
            for k in range(1, n):
                pts.append((cx + r * math.cos(a0 + sw * k / n), cy + r * math.sin(a0 + sw * k / n)))
        pts.append((o["x"], o["y"]))
    return pts


def _arcs(cont: list[dict]) -> list[tuple[int, int, float, float, float, float, float]]:
    """Konturdagi yoylar: (siniq chiziqdagi bosh indeks, oxir indeks, cx, cy, r, bosh burchak, burilish (rad))."""
    out = []
    pts = [(cont[0]["x"], cont[0]["y"])]
    for o in cont[1:]:
        if o["t"] == "mac":
            p0 = pts[-1]
            cx, cy = o["cx"], o["cy"]
            r = math.hypot(o["x"] - cx, o["y"] - cy)
            sw = math.radians(sweep(p0, o))
            n = arc_segments(r, math.degrees(sw))
            out.append((len(pts) - 1, len(pts) - 1 + n, cx, cy, r, math.atan2(p0[1] - cy, p0[0] - cx), sw))
            pts.extend([p0] * (n - 1))
        pts.append((o["x"], o["y"]))
    return out


def _arc_edge_hit(arc, a, b, near) -> Optional[tuple[float, tuple[float, float]]]:
    """Yoyning (a→b) to'g'ri chiziq bilan aniq kesishuvi — `near` (vatar bo'yicha topilgan nuqta) ga eng yaqini.
    Qaytaradi: (yoy bo'ylab ulush 0…1, nuqta)."""
    _s, _e, cx, cy, r, a0, sw = arc
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy)
    if ln < 1e-12 or abs(sw) < 1e-12:
        return None
    ux, uy = dx / ln, dy / ln
    fx, fy = a[0] - cx, a[1] - cy
    bq = fx * ux + fy * uy
    disc = bq * bq - (fx * fx + fy * fy - r * r)
    if disc < 0:
        return None
    best = None
    for t in (-bq - math.sqrt(disc), -bq + math.sqrt(disc)):
        pt = (a[0] + t * ux, a[1] + t * uy)
        da = math.atan2(pt[1] - cy, pt[0] - cx) - a0
        while sw > 0 and da < -1e-9:
            da += 2 * math.pi
        while sw < 0 and da > 1e-9:
            da -= 2 * math.pi
        f = da / sw
        if -1e-9 <= f <= 1 + 1e-9:
            d = math.dist(pt, near)
            if best is None or d < best[0]:
                if abs(ux) < 1e-12:
                    pt = (a[0], pt[1])                     # o'qqa parallel qirra — koordinata aniq
                if abs(uy) < 1e-12:
                    pt = (pt[0], a[1])
                best = (d, min(1.0, max(0.0, f)), pt)
    return (best[1], best[2]) if best and best[0] < 5.0 else None


def _arc_part(arc, f0: float, f1: float) -> list[tuple[float, float]]:
    """Yoyning f0…f1 ulushi orasidagi oraliq nuqtalar (uchlarsiz) — shu bo'lak o'z burchagi bo'yicha qayta bo'linadi."""
    _s, _e, cx, cy, r, a0, sw = arc
    part = sw * (f1 - f0)
    n = arc_segments(r, math.degrees(part))
    return [(cx + r * math.cos(a0 + sw * f0 + part * k / n), cy + r * math.sin(a0 + sw * f0 + part * k / n))
            for k in range(1, n)]


def _area2(pts) -> float:
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))


def _same(a, b, eps=1e-6) -> bool:
    return abs(a[0] - b[0]) <= eps and abs(a[1] - b[1]) <= eps


def dedupe(pts, eps=1e-9):
    """Ketma-ket (siklik) takror nuqtalarni olib tashlash — oldingisi qoladi."""
    out = []
    for p in pts:
        if not out or not _same(out[-1], p, eps):
            out.append(p)
    while len(out) > 1 and _same(out[0], out[-1], eps):
        out.pop()
    return out


def _hits(path, poly):
    """Siniq chiziqning ko'pburchak chegarasi bilan kesishuvlari: (yo'l parametri, qirra raqami, qirradagi u, nuqta)."""
    res = []
    n = len(poly)
    for k in range(len(path) - 1):
        p, q = path[k], path[k + 1]
        d1 = (q[0] - p[0], q[1] - p[1])
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            d2 = (b[0] - a[0], b[1] - a[1])
            den = d1[0] * d2[1] - d1[1] * d2[0]
            if abs(den) < 1e-12:
                continue
            t = ((a[0] - p[0]) * d2[1] - (a[1] - p[1]) * d2[0]) / den
            u = ((a[0] - p[0]) * d1[1] - (a[1] - p[1]) * d1[0]) / den
            le = math.hypot(d2[0], d2[1])
            # qirra uchidan TOL mm gacha tashqaridagi kesishuv ham olinadi (burchakdan o'tuvchi qiya kesim — namunalardagi kabi)
            if -EPS <= t <= 1 + EPS and -TOL <= u * le <= le + TOL:
                pt = (p[0] + t * d1[0], p[1] + t * d1[1])
                # qirra o'qqa parallel bo'lsa — koordinatani aniq qo'yamiz
                if abs(d2[0]) < 1e-12:
                    pt = (a[0], pt[1])
                if abs(d2[1]) < 1e-12:
                    pt = (pt[0], a[1])
                res.append((k + min(1.0, max(0.0, t)), i, min(1.0, max(0.0, u)), pt))
    res.sort(key=lambda h: h[0])
    return res


def _edge_of(pt, poly) -> Optional[tuple[int, float]]:
    """Nuqta yotgan chegara qirrasi: (qirra raqami, qirradagi u) yoki None."""
    n = len(poly)
    best = None
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        d = (b[0] - a[0], b[1] - a[1])
        l2 = d[0] * d[0] + d[1] * d[1]
        if l2 < 1e-18:
            continue
        u = ((pt[0] - a[0]) * d[0] + (pt[1] - a[1]) * d[1]) / l2
        u = min(1.0, max(0.0, u))
        dist = math.hypot(pt[0] - (a[0] + u * d[0]), pt[1] - (a[1] + u * d[1]))
        if dist < 2 * TOL and (best is None or dist < best[2]):
            best = (i, u, dist)
    return (best[0], best[1]) if best else None


def _on_boundary(pt, poly) -> bool:
    return _edge_of(pt, poly) is not None


def cut_poly(poly: list[tuple[float, float]], cont: list[dict]) -> Optional[tuple[list[tuple[float, float]], tuple, tuple]]:
    """Ko'pburchakni kontur bilan kesish: asbob tomoni (c=1 — harakatga nisbatan o'ng, c=2 — chap) olib tashlanadi.
    Qaytaradi: (yangi ko'pburchak — o'sha yo'nalishda, yo'lga kirish tutashuvidan boshlab; kirish tutashuvi;
    ikkinchi tutashuv) yoki None (kontur detalni kesmaydi)."""
    c = cont[0]["c"]
    if c not in (1, 2):
        return None
    path = polyline(cont)
    hits = _hits(path, poly)
    if len(hits) < 2:
        return None
    h_in, h_out = hits[0], hits[-1]
    for h in hits[1:-1]:                       # kirish: bir joydagi (burchak) kesishuvlarning oxirgisi
        if math.dist(h[3], hits[0][3]) < 1e-3:
            h_in = h
    if h_out[0] - h_in[0] < 1e-9 or _same(h_in[3], h_out[3]):
        return None
    inner = [h_in[3]] + [path[k] for k in range(len(path)) if h_in[0] < k < h_out[0]] + [h_out[3]]
    # tutashuv yoy ustida bo'lsa: vatar emas, yoyning o'zi bilan aniq kesishuv; yoyning detal ichidagi bo'lagi qayta bo'linadi
    arcs = _arcs(cont)
    n_p = len(poly)
    a_in = next((x for x in arcs if x[0] <= h_in[0] < x[1]), None)
    a_out = next((x for x in arcs if x[0] < h_out[0] <= x[1]), None)
    if a_in is not None and a_in is not a_out:
        ex = _arc_edge_hit(a_in, poly[h_in[1]], poly[(h_in[1] + 1) % n_p], h_in[3])
        if ex is not None:
            mid = [path[k] for k in range(len(path)) if a_in[1] <= k < h_out[0]]
            inner = [ex[1]] + _arc_part(a_in, ex[0], 1.0) + mid + [inner[-1]]
    if a_out is not None and a_out is not a_in:
        ex = _arc_edge_hit(a_out, poly[h_out[1]], poly[(h_out[1] + 1) % n_p], h_out[3])
        if ex is not None:
            k0 = next((i for i, q in enumerate(inner) if _same(q, path[a_out[0]])), None)
            if k0 is not None:
                inner = inner[:k0 + 1] + _arc_part(a_out, 0.0, ex[0]) + [ex[1]]
    # yo'l chegara bo'ylab yursa (qirra ustida) — tutashuv yo'l chegaradan ajraladigan nuqtaga suriladi
    while len(inner) > 2 and _on_boundary(((inner[0][0] + inner[1][0]) / 2, (inner[0][1] + inner[1][1]) / 2), poly):
        inner.pop(0)
    while len(inner) > 2 and _on_boundary(((inner[-1][0] + inner[-2][0]) / 2, (inner[-1][1] + inner[-2][1]) / 2), poly):
        inner.pop()
    if len(inner) == 2 and _on_boundary(((inner[0][0] + inner[1][0]) / 2, (inner[0][1] + inner[1][1]) / 2), poly):
        return None
    e_in, e_out = _edge_of(inner[0], poly), _edge_of(inner[-1], poly)
    if e_in is None or e_out is None:
        return None
    h_in, h_out = (0, e_in[0], e_in[1], inner[0]), (1, e_out[0], e_out[1], inner[-1])
    n = len(poly)
    # chegara bo'ylab h_out dan h_in gacha: oldinga (ko'pburchak yo'nalishida) va orqaga
    fwd = []
    i = h_out[1]
    if not (h_out[1] == h_in[1] and h_in[2] >= h_out[2]):
        while True:
            i = (i + 1) % n
            fwd.append(poly[i])
            if i == h_in[1]:
                break
    bwd = []
    i = h_out[1]
    if not (h_out[1] == h_in[1] and h_in[2] <= h_out[2]):
        while True:
            bwd.append(poly[i])
            i = (i - 1) % n
            if i == h_in[1]:
                break
    want_pos = c == 2            # yo'l oldinga yurilganda: c=2 da qoladigan qism shoelace > 0 (ekranda o'ngda)
    cands = [dedupe(inner + fwd), dedupe(inner + bwd)]
    cands = [x for x in cands if len(x) >= 3 and abs(_area2(x)) > 1e-6]
    good = [x for x in cands if (_area2(x) > 0) == want_pos]
    if not good:
        return None
    res = max(good, key=lambda x: abs(_area2(x)))
    if abs(abs(_area2(res)) - abs(_area2(poly))) < 1e-6:
        return None                                    # hech narsa kesilmadi
    enter, other = h_in[3], h_out[3]
    if _area2(res) < 0:                                # yo'nalishni saqlash (shoelace > 0): yo'l orqaga yuriladi
        res = res[::-1]
        enter, other = h_out[3], h_in[3]
    k = next((i for i, p in enumerate(res) if _same(p, enter)), 0)
    return res[k:] + res[:k], enter, other


def cut_outline(L: float, W: float, conts: list[list[dict]]) -> tuple[list[tuple[float, float]], tuple, tuple]:
    """Detal konturi (yuz tomon XNC koordinatasi): (siklik ko'pburchak — (0,W) → (0,0) → (L,0) → (L,W) yo'nalishida,
    chokdan boshlab; chok; teskari yo'nalishdagi chok). Kesilmagan detal: choklar (0,W) va (0,0)."""
    poly = [(0.0, W), (0.0, 0.0), (L, 0.0), (L, W)]
    seam, rseam = poly[0], poly[1]
    first = True
    for cont in conts:
        r = cut_poly(poly, cont)
        if r is None:
            continue
        new, enter, other = r
        if first:
            seam, rseam = enter, other
            first = False
        k = next((i for i, p in enumerate(new) if _same(p, seam)), None)
        if k is None:
            seam = enter
            k = 0
        if not any(_same(p, rseam) for p in new):
            rseam = other
        poly = new[k:] + new[:k]
    return poly, seam, rseam
