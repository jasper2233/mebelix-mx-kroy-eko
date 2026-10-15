"""Nanxing SyntecCad — `.scx` (XML `Root/Project/Panels/Panel`; docs/mebelix/postprocessors/nanxing-synteccad.md).

Bitta XNC operatsiyasi = bitta `<XNC kodi>.scx`, butun fayl bitta qatorda (qator oxirisiz), UTF-8. Koordinata: X = x,
Y = W − y (boshi pastki-chap burchakda), qirra teshigi Z — pastki yuzadan (XNC dagi z). Amallar — XNC dastur tartibida.
Atributlar alifbo tartibida. Freza — kontur chizig'i, korreksiya ToolOffset (中 / 左 / 右; Y akslangani uchun
c=1 → 左). Yoy — `Angle` (burilish burchagi, dir="true" → musbat). Orqa tomon — X ag'darilgan.

`<Outline>`: detal (to'rtburchak yoki o'tuvchi freza bilan kesilgan kontur) + 20 mm ramka va kromkali tomonda 30 mm
«bo'rtiq» (kromka belgisi).
"""
from __future__ import annotations

import math

from . import DrillJob, Files, num_hu, register
from . import _cnc as C
from . import _cnc2 as C2
from ._cnc2 import edge_flags, num, part_contours, sweep, xml_attr

CAD = "MebeliX Kroy"
FACE = {"L": "4", "R": "3", "T": "1", "B": "2"}
OFFSET = {0: "中", 1: "左", 2: "右"}


def n(v: float) -> str:
    return num_hu(v, 3)


def arc_angle(p0, o: dict) -> float:
    """Yoy burilish burchagi (gradus, ishora — yo'nalish). 180° dan kichik yoyda vatar va o'rtacha radius orqali
    (namunalardagi oxirgi raqamlargacha mos kelishi uchun), aks holda markaziy burchaklar ayirmasi."""
    sw = sweep(p0, o)
    if abs(sw) >= 179.0:
        return sw
    c = (o["cx"], o["cy"])
    q = (o["x"], o["y"])
    r0, r1 = math.dist(p0, c), math.dist(q, c)
    if abs(r0 - r1) > 1e-9:                 # markaz noaniq berilgan — markaziy burchaklar ayirmasi
        return sw
    r2 = (r0 * r0 + r1 * r1) / 2
    ch = math.dist(p0, q)
    a = math.degrees(2 * math.atan2(ch / 2, math.sqrt(max(0.0, r2 - ch * ch / 4))))
    return a if sw >= 0 else -a


def frame(L: float, W: float, bl: bool, bt: bool, br: bool, bb: bool) -> list[tuple[float, float]]:
    """Ramka va kromka «bo'rtiq»lari (Nanxing koordinatasi): kromkali tomonda 30, aks holda 20 mm."""
    def o(b):
        return 30 if b else 20
    P = [(0, -20), (L + 20, -20), (L + 20, W + 20), (-20, W + 20), (-20, 0)]
    P += [(-o(bl), 0), (-o(bl), W), (-20, W), (-20, W + 20)]
    P += [(-20, W + 20), (0, W + 20), (0, W + o(bt)), (L, W + o(bt)), (L, W + 20), (L + 20, W + 20)]
    P += [(L + 20, W), (L + o(br), W), (L + o(br), 0), (L + 20, 0), (L + 20, -20)]
    P += [(L, -20), (L, -o(bb)), (0, -o(bb)), (0, -20), (0, 0)]
    return P


def part_outline(job: DrillJob) -> list[tuple[float, float]]:
    """Detal konturi (Nanxing koordinatasida, soat miliga teskari): frezasiz — (0,0) (L,0) (L,W) (0,W) (0,W) (0,0).
    Ichki ro'yxat chokdan boshlanib yopiladi, so'ng koordinata boshiga eng yaqin nuqtadan boshlab yoziladi —
    shu sabab chok nuqtasi ikki marta chiqadi (namunalardagi kabi)."""
    L, W = job.dx, job.dy
    poly, _seam, rseam = C2.cut_outline(L, W, part_contours(job))
    rev = poly[::-1]
    k = next((i for i, p in enumerate(rev) if C2._same(p, rseam)), 0)
    lst = [(x, W - y) for x, y in rev[k:] + rev[:k]]
    if math.dist(lst[0], lst[-1]) > 1e-3:           # oxirgi nuqta chokka deyarli teng bo'lsa — yopuvchi nuqta qo'shilmaydi
        lst.append(lst[0])
    best = min(math.hypot(x, y) for x, y in lst)
    idx = max(i for i, (x, y) in enumerate(lst) if math.hypot(x, y) <= best + 1e-9)
    return lst[idx:] + lst[:idx + 1]


def program(job: DrillJob) -> str:
    L, W, T = job.dx, job.dy, job.dz
    e = edge_flags(job)
    pts = part_outline(job)
    pts = pts + frame(L, W, e["l"], e["t"], e["r"], e["b"])[:-1] + [pts[0]]     # ramka kontur boshiga qaytadi
    s = [f'<?xml version="1.0" encoding="UTF-8"?><Root Cad="{CAD}" version="2.0"><Project><Panels>',
         f'<Panel ID="{xml_attr(job.code)}" IsProduce="true" Length="{n(L)}" MachiningPoint="1" Name="{xml_attr(job.name)}" '
         f'Thickness="{n(T)}" Width="{n(W)}">',
         "<Outline>" + "".join(f'<Point X="{n(x)}" Y="{n(y)}"/>' for x, y in pts) + "</Outline><Machines>"]
    lst = C.machine_ops(job)
    conts = {id(c[0]): c for c in C.contours(lst)}
    for o in lst:
        t = o["t"]
        if t == "drill" and o["side"] == "F":
            s.append(f'<Machining Depth="{n(o["dp"])}" Diameter="{n(o["d"])}" Face="5" IsGenCode="2" Type="2" '
                     f'X="{n(o["x"])}" Y="{n(W - o["y"])}"/>')
        elif t == "drill":
            sd = o["side"]
            if sd in ("L", "R"):
                X, Y = (0.0 if sd == "L" else L), W - o["y"]
            else:
                X, Y = o["x"], (W if sd == "T" else 0.0)
            s.append(f'<Machining Depth="{n(o["dp"])}" Diameter="{n(o["d"])}" Face="{FACE[sd]}" IsGenCode="0" Type="1" '
                     f'X="{n(X)}" Y="{n(Y)}" Z="{n(o["z"])}"/>')
        elif t == "ms" and id(o) in conts and len(conts[id(o)]) > 1:
            p = (o["x"], o["y"])
            ls = []
            for i, sg in enumerate(conts[id(o)][1:]):
                ang = "0" if sg["t"] == "ml" else repr(arc_angle(p, sg))
                ls.append(f'<Line Angle="{ang}" EndX="{n(sg["x"])}" EndY="{n(W - sg["y"])}" LineID="{i}"/>')
                p = (sg["x"], sg["y"])
            s.append(f'<Machining Closed="0" Depth="{n(o["dp"])}" Diameter="{n(o["d"])}" Face="5" IsGenCode="0" Pocket="0" '
                     f'ToolOffset="{OFFSET.get(o["c"], "中")}" Type="3" X="{n(o["x"])}" Y="{n(W - o["y"])}"><Lines>'
                     + "".join(ls) + "</Lines></Machining>")
        elif t == "groove":
            s.append(f'<Machining Depth="{n(o["dp"])}" EndX="{n(o["x2"])}" EndY="{n(W - o["y2"])}" EndZ="{n(T)}" Face="5" '
                     f'IsGenCode="0" ToolOffset="{OFFSET.get(o["c"], "中")}" Type="4" Width="{n(o["w"])}" '
                     f'X="{n(o["x1"])}" Y="{n(W - o["y1"])}" Z="{n(T)}"/>')
    s.append("</Machines></Panel></Panels></Project></Root>")
    return "".join(s)


@register("nanxing_syntec", "Nanxing SyntecCad (.scx)", "cnc", "scx",
          note="XML bitta qatorda, UTF-8. ❓ Namunalarda Root@Cad atributida boshqa dastur nomi bor edi — biz Cad=\"MebeliX Kroy\" "
               "yozamiz; SyntecCad bu qiymatni tekshiradimi (fayl stanokda ochiladimi) — sinab ko'rish kerak. Y akslangan "
               "(boshi pastki-chap), qirra teshigi Z pastki yuzadan. Freza: kontur chizig'i, ToolOffset c=1 → 左, c=2 → 右; "
               "Closed/Pocket doim 0 (yopiq kontur, cho'ntak noma'lum). Outline: 20 mm ramka + kromkali tomonda 30 mm; "
               "o'tuvchi frezali detalda kesilgan kontur (yoylar vatarlarga bo'lingan). Orqa tomondagi qirra teshigi va "
               "freza — namunada yo'q, faraz.")
def nanxing_syntec(job: DrillJob) -> Files:
    return [(f"{job.code}.scx", program(job).encode("utf-8"))]
