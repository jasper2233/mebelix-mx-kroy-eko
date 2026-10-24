"""Daron FoxCNC (MicroDraw) — `.ban` (MicroDrawBan_XML 3.0; docs/mebelix/postprocessors/daron-foxcnc-microdraw.md).

Bitta XNC operatsiyasi = bitta `<XNC kodi>.ban`. Koordinata: X = x − L (boshi o'ng qirrada, X manfiy), Y = y, Z = 0 —
yuqori yuza (pastga manfiy). Orqa tomon — avval X ag'dariladi (`machine_ops`). Tartib: yuz teshiklari (HoleV); paz va
freza (SlotL / SlotA, dastur tartibida); qirra teshiklari L, R, D (y=0), U (y=W).

Daron freza korreksiyasini olmaydi — asbob MARKAZI trayektoriyasi yoziladi: har segment d/2 ga korreksiya tomoniga
siljitiladi, qo'shni siljigan chiziqlar kesishish nuqtasida tutashadi, yoy radiusi r ∓ d/2; urinma bo'lmagan tashqi
burchakda cho'qqi atrofida r = d/2 li yoy qo'shiladi. SlotA da yo'nalish yo'q — Start→End doim soat miliga teskari.
"""
from __future__ import annotations

from datetime import datetime

from . import DrillJob, Files, register
from . import _cnc as C
from ._cnc2 import cs_material, edge_flags, num, offset_path, part_contours, xml_attr
from . import _cnc2 as C2

FACE = {"L": "L", "R": "R", "T": "D", "B": "U"}


def n(v: float) -> str:
    return num(v, 5)


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
