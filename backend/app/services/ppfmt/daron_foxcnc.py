"""Daron FoxCNC (MicroDraw) — `.ban` (MicroDrawBan_XML 3.0; docs/mebelix/postprocessors/daron-foxcnc-microdraw.md).

Bitta XNC operatsiyasi = bitta `<XNC kodi>.ban`. Koordinata: X = x − L (boshi o'ng qirrada, X manfiy), Y = y, Z = 0 —
yuqori yuza (pastga manfiy). Orqa tomon — avval X ag'dariladi (`machine_ops`). Tartib: yuz teshiklari (HoleV); paz va
freza (SlotL / SlotA, dastur tartibida); qirra teshiklari L, R, D (y=0), U (y=W).

Daron freza korreksiyasini olmaydi — asbob MARKAZI trayektoriyasi yoziladi: har segment d/2 ga korreksiya tomoniga
siljitiladi, qo'shni siljigan chiziqlar kesishish nuqtasida tutashadi, yoy radiusi r ∓ d/2; urinma bo'lmagan tashqi
burchakda cho'qqi atrofida r = d/2 li yoy qo'shiladi. SlotA da yo'nalish yo'q — Start→End doim soat miliga teskari.
"""
from __future__ import annotations

import math
from datetime import datetime

from . import DrillJob, Files, register
from . import _cnc as C
from ._cnc2 import cs_material, edge_flags, num, part_contours, xml_attr
from . import _cnc2 as C2

FACE = {"L": "L", "R": "R", "T": "D", "B": "U"}
SNAP = 1e-3          # mm: shundan kichik uzilish — urinma tutashuv deb olinadi (namunalar: 0.0002 — ulangan, 0.004 — yoy)


def n(v: float) -> str:
    return num(v, 5)


def _unit(v):
    ln = math.hypot(v[0], v[1])
    return (v[0] / ln, v[1] / ln) if ln > 1e-12 else (0.0, 0.0)


def offset_path(cont: list[dict]) -> list[list]:
    """Kontur → asbob markazi segmentlari (XNC koordinatasi, Y pastga):
    ['L', p0, p1] yoki ['A', p0, p1, markaz, r, ccw] (ccw — XNC dir="true" ma'nosida, ya'ni kontur yo'nalishi)."""
    ms = cont[0]
    h = ms["d"] / 2.0
    side = {1: 1, 2: -1}.get(ms["c"], 0)          # 1 — harakat yo'nalishiga nisbatan o'ng (ekranda, Y pastga)
    segs: list[list] = []
    p = (ms["x"], ms["y"])
    for o in cont[1:]:
        q = (o["x"], o["y"])
        if o["t"] == "ml":
            ux, uy = _unit((q[0] - p[0], q[1] - p[1]))
            nx, ny = -uy * side * h, ux * side * h
            segs.append(["L", (p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), None, 0.0, False, (ux, uy), (ux, uy)])
        else:
            c = (o["cx"], o["cy"])
            r = math.hypot(q[0] - c[0], q[1] - c[1])
            r0 = math.hypot(p[0] - c[0], p[1] - c[1])
            inward = (side == 1) == o["ccw"]          # o'ng tomon markazga qaraydi (dir=true da)
            dr = 0.0 if side == 0 else (-h if inward else h)
            r2, r02 = r + dr, r0 + dr                 # boshi — boshlang'ich radius, oxiri — oxirgi radius bo'yicha
            u0 = ((p[0] - c[0]) / r0, (p[1] - c[1]) / r0) if r0 > 1e-12 else (0.0, 0.0)
            u1 = ((q[0] - c[0]) / r, (q[1] - c[1]) / r) if r > 1e-12 else (0.0, 0.0)
            # urinma yo'nalishlari (ekranda dir=true — soat bo'yicha; Y pastga koordinatada (−uy, ux) yo'nalish)
            s = 1 if o["ccw"] else -1
            t0, t1 = (-u0[1] * s, u0[0] * s), (-u1[1] * s, u1[0] * s)
            segs.append(["A", (c[0] + u0[0] * r02, c[1] + u0[1] * r02), (c[0] + u1[0] * r2, c[1] + u1[1] * r2), c, r2,
                         o["ccw"], t0, t1])
        p = q
    res: list[list] = []
    for i, sg in enumerate(segs):
        if res:
            a = res[-1]
            if a[0] == "L" and sg[0] == "L":
                x1, y1 = a[1]
                x2, y2 = a[2]
                x3, y3 = sg[1]
                x4, y4 = sg[2]
                den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
                if abs(den) > 1e-12:
                    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
                    ip = (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
                    a[2] = ip
                    sg[1] = ip
            elif math.dist(a[2], sg[1]) <= SNAP:
                sg[1] = a[2]                      # deyarli urinma tutashuv: keyingi segment oldingisining oxiridan boshlanadi
            elif side:
                # urinma bo'lmagan tutashuv: cho'qqi atrofida r = d/2 yoy (tashqi burchak)
                v = cont[i]                       # cho'qqi — oldingi segment oxiri
                vtx = (v["x"], v["y"])
                cross = a[7][0] * sg[6][1] - a[7][1] * sg[6][0]
                res.append(["A", a[2], sg[1], vtx, h, cross > 0, None, None])
        res.append(sg)
    return res


def program(job: DrillJob, when: str | None = None) -> str:
    L, W, T = job.dx, job.dy, job.dz
    lst = C.machine_ops(job)
    e = edge_flags(job)
    part = C.part_of(job)
    grain = "DIR_HOR" if part is not None and part.grain else "DIR_NONE"
    when = when or datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    def fx(x):
        return x - L
    out = [f'<MicroDrawBan_XML Version="3.0" Time="{when}" Source="" SourceType="BAN">',
           f'<Plane Name="{xml_attr(job.name)}" Code="{xml_attr(job.code)}" Material="{xml_attr(cs_material(job))}" '
           f'PlaneNo=" " Width="{n(L)}" Hight="{n(W)}" Thickness="{n(T)}" Grain="{grain}" '
           f'EdgeFBLR="{int(e["b"])} ,{int(e["t"])} ,{int(e["l"])} ,{int(e["r"])}" PlaneSize="1" MachineBase="-1">',
           "<Outline>"]
    out += [f'<Point Value="{n(x)} {n(y)} 0"/>' for x, y in outline(job)]
    out.append("</Outline>")
    for o in lst:
        if o["t"] == "drill" and o["side"] == "F":
            X, Y = n(fx(o["x"])), n(o["y"])
            out.append(f'<HoleV Name="" Face="A" Start="{X} {Y} 0.00" End="{X} {Y} {n(-o["dp"])}" '
                       f'Diameter="{n(o["d"])}" IsCuted="0"/>')
    conts = {id(c[0]): c for c in C.contours(lst)}
    for o in lst:
        if o["t"] == "groove":
            z = n(-o["dp"])
            out.append(f'<SlotL Start="{n(fx(o["x1"]))} {n(o["y1"])} {z}" End="{n(fx(o["x2"]))} {n(o["y2"])} {z}" '
                       f'Face="A" Width="{n(o["w"])}" IsCuted="0" />')
        elif o["t"] == "ms" and id(o) in conts and len(conts[id(o)]) > 1:
            z = n(-o["dp"])
            w = n(o["d"])
            for sg in offset_path(conts[id(o)]):
                s0, s1 = sg[1], sg[2]
                if sg[0] == "L":
                    out.append(f'<SlotL Start="{n(fx(s0[0]))} {n(s0[1])} {z}" End="{n(fx(s1[0]))} {n(s1[1])} {z}" '
                               f'Face="A" Width="{w}" IsCuted="0" />')
                else:
                    if not sg[5]:
                        s0, s1 = s1, s0
                    c = sg[3]
                    out.append(f'<SlotA Start="{n(fx(s0[0]))} {n(s0[1])} {z}" End="{n(fx(s1[0]))} {n(s1[1])} {z}" '
                               f'Center="{n(fx(c[0]))} {n(c[1])} {z}" Face="A" Width="{w}" IsCuted="0" />')
    for side in ("L", "R", "T", "B"):
        for o in lst:
            if o["t"] != "drill" or o["side"] != side:
                continue
            z = n(-(T - o["z"]))
            if side == "L":
                S, E = (-L, o["y"]), (-L + o["dp"], o["y"])
            elif side == "R":
                S, E = (0.0, o["y"]), (-o["dp"], o["y"])
            elif side == "T":
                S, E = (fx(o["x"]), 0.0), (fx(o["x"]), o["dp"])
            else:
                S, E = (fx(o["x"]), W), (fx(o["x"]), W - o["dp"])
            out.append(f'<HoleH Name="" Face="{FACE[side]}" Start="{n(S[0])} {n(S[1])} {z}" '
                       f'End="{n(E[0])} {n(E[1])} {z}" Diameter="{n(o["d"])}" IsCuted="0"/>')
    out += ["</Plane>", "</MicroDrawBan_XML>"]
    return "\r\n".join(out) + "\r\n"


def outline(job: DrillJob) -> list[tuple[float, float]]:
    """Detal konturi — Daron X, Y koordinatasida, yopiq (birinchi nuqta oxirida takrorlanadi). Frezasiz: to'rtburchak
    (−L,W) (−L,0) (0,0) (0,W); o'tuvchi freza bo'lsa — kesilgan kontur. Orqa tomon faylida kontur X bo'yicha
    ag'dariladi (X = −x)."""
    L, W = job.dx, job.dy
    poly, _seam, _r = C2.cut_outline(L, W, part_contours(job))
    pts = [((x - L) if job.face else -x, y) for x, y in C2.dedupe(poly, C2.TOL)]
    return pts + [pts[0]]


@register("daron_foxcnc", "Daron FoxCNC / MicroDraw (.ban)", "cnc", "ban",
          note="MicroDrawBan_XML 3.0 (XML deklaratsiyasisiz). Freza — ASBOB MARKAZI trayektoriyasi (kontur d/2 ga korreksiya "
               "tomoniga siljitilgan; korreksiyasiz C=0 — kontur o'zi), SlotA doim soat miliga teskari. Outline: frezasiz — "
               "to'rtburchak; o'tuvchi frezali detal — kesilgan kontur (yoylar vatarlarga bo'lingan; stanok uni ishlatadimi — "
               "noma'lum). Time — eksport vaqti. Grain: detal teksturasi (DIR_HOR / DIR_NONE). Orqa tomondagi qirra teshigi "
               "va freza — namunada yo'q, faraz. Massiv teshiklar alohida HoleV. Kirill matn cp1251 (tekshirilmagan).")
def daron_foxcnc(job: DrillJob) -> Files:
    return [(f"{job.code}.ban", program(job).encode("cp1251", errors="replace"))]
