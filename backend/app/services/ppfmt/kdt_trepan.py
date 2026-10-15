"""KDT WDX (trepan) — `.xml` (`AndersonXMLdata`; docs/mebelix/postprocessors/kdt-wdx-trepan.md).

Bitta XNC operatsiyasi = bitta `<XNC kodi>.xml`. X o'ng qirradan (`L − x`), Y — XNC dagidek, qirra teshigi balandligi
yuqori yuzadan (`T − z`). Qirra teshigi «chorak» (Quadrant) bilan: 1 — o'ng qirra (x=L), 2 — chap (x=0), 3 — y=W,
4 — y=0. Tartib: yuz teshiklari; freza va paz (dastur tartibida); Quadrant 1, 2, 4, 3. Orqa tomon — X ag'darilgan.
"""
from __future__ import annotations

import math

from . import DrillJob, Files, register
from . import _cnc as C
from ._cnc2 import num, xml_text

TAIL = ["<HoleNo>1</HoleNo>", "<IntervalX>0</IntervalX>", "<IntervalY>0</IntervalY>", "<IntervalZ>0</IntervalZ>",
        "<Mirror>0</Mirror>", "</CAD>"]
CORR = {0: "0", 1: "2", 2: "1"}         # X teskari bo'lgani uchun korreksiya tomoni almashadi
QUAD = (("R", "1"), ("L", "2"), ("T", "4"), ("B", "3"))


def n(v: float) -> str:
    return num(v, 4)


def program(job: DrillJob) -> str:
    L, W, T = job.dx, job.dy, job.dz
    lst = C.machine_ops(job)

    def fx(x):
        return L - x
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<AndersonXMLdata>", "<PANEL>", f"<PanelLength>{n(L)}</PanelLength>",
           f"<PanelWidth>{n(W)}</PanelWidth>", f"<PanelThickness>{n(T)}</PanelThickness>",
           f"<PanelName>{xml_text(job.name)}</PanelName>", "</PANEL>"]
    for o in lst:
        if o["t"] == "drill" and o["side"] == "F":
            out += ["<CAD>", "<TypeNo>1</TypeNo>", "<TypeName>Vertical Hole</TypeName>", "<PlaneID>0</PlaneID>",
                    "<Quadrant>1</Quadrant>", f"<X1>{n(fx(o['x']))}</X1>", f"<Y1>{n(o['y'])}</Y1>",
                    f"<Depth>{n(o['dp'])}</Depth>", f"<Diameter>{n(o['d'])}</Diameter>", *TAIL]
    cur = None
    width = corr = dp = None
    for o in lst:
        t = o["t"]
        if t == "ms":
            cur = (o["x"], o["y"])
            width, corr, dp = o["d"], CORR.get(o["c"], "0"), o["dp"]
        elif t == "ml" and cur is not None:
            out += ["<CAD>", "<TypeNo>3</TypeNo>", "<TypeName>Line</TypeName>", f"<BeginX>{n(fx(cur[0]))}</BeginX>",
                    f"<BeginY>{n(cur[1])}</BeginY>", f"<EndX>{n(fx(o['x']))}</EndX>", f"<EndY>{n(o['y'])}</EndY>",
                    f"<Width>{n(width)}</Width>", f"<Correction>{corr}</Correction>", f"<Depth>{n(dp)}</Depth>", "</CAD>"]
            cur = (o["x"], o["y"])
        elif t == "mac" and cur is not None:
            r = math.hypot(o["x"] - o["cx"], o["y"] - o["cy"])
            out += ["<CAD>", "<TypeNo>4</TypeNo>", "<TypeName>Arc</TypeName>", f"<StartX>{n(fx(cur[0]))}</StartX>",
                    f"<StartY>{n(cur[1])}</StartY>", f"<EndX>{n(fx(o['x']))}</EndX>", f"<EndY>{n(o['y'])}</EndY>",
                    f"<Radius>{num(r, 5)}</Radius>", f"<Direction>{'0' if o['ccw'] else '1'}</Direction>",
                    f"<Correction>{corr}</Correction>", f"<Width>{n(width)}</Width>", f"<Depth>{n(dp)}</Depth>", "</CAD>"]
            cur = (o["x"], o["y"])
        elif t == "groove":
            cur = None
            out += ["<CAD>", "<TypeNo>3</TypeNo>", "<TypeName>Groove</TypeName>", f"<BeginX>{n(fx(o['x1']))}</BeginX>",
                    f"<BeginY>{n(o['y1'])}</BeginY>", f"<EndX>{n(fx(o['x2']))}</EndX>", f"<EndY>{n(o['y2'])}</EndY>",
                    f"<Width>{n(o['w'])}</Width>", f"<Correction>{o['c']}</Correction>", "<UseSaw>1</UseSaw>",
                    f"<Depth>{n(o['dp'])}</Depth>", "</CAD>"]
        else:
            cur = None
    for side, q in QUAD:
        for o in lst:
            if o["t"] != "drill" or o["side"] != side:
                continue
            out += ["<CAD>", "<TypeNo>2</TypeNo>", "<TypeName>Horizontal Hole</TypeName>", "<PlaneID>2</PlaneID>"]
            if side in ("R", "L"):
                out += [f"<X1>{n(0 if side == 'R' else L)}</X1>", f"<Quadrant>{q}</Quadrant>", f"<Y1>{n(o['y'])}</Y1>"]
            else:
                out += [f"<Quadrant>{q}</Quadrant>", f"<X1>{n(fx(o['x']))}</X1>", f"<Y1>{n(0 if side == 'T' else W)}</Y1>"]
            out += [f"<Z1>{n(T - o['z'])}</Z1>", f"<Depth>{n(o['dp'])}</Depth>", f"<Diameter>{n(o['d'])}</Diameter>", *TAIL]
    out.append("</AndersonXMLdata>")
    return "\r\n".join(out) + "\r\n"


@register("kdt_trepan", "KDT WDX trepan (.xml AndersonXMLdata)", "cnc", "xml",
          note="X1 o'ng qirradan (L − x), qirra teshigi Z1 = qalinlik − z, Quadrant: 1 — x=L, 2 — x=0, 3 — y=W, 4 — y=0. "
               "Freza: kontur chizig'i (korreksiyani stanok qiladi), Correction 1↔2 almashgan (X teskari), yoy — Radius + "
               "Direction (soat bo'yicha → 0); 180° dan katta yoy va to'liq aylana qanday yozilishi noma'lum. Massiv maydonlari "
               "(HoleNo, Interval*) ishlatilmaydi — har teshik alohida. Orqa tomondagi qirra teshigi va freza — namunada yo'q, faraz.")
def kdt_trepan(job: DrillJob) -> Files:
    return [(f"{job.code}.xml", program(job).encode("utf-8"))]
