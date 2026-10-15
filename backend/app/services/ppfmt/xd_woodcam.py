"""XDWoodCam — `.wxf` (WXF 2.0, INI uslubi; docs/mebelix/postprocessors/xdwoodcam.md).

Bitta XNC operatsiyasi = bitta `<XNC kodi>.wxf`. Yuz: Xs = x, Ys = W − y (Y akslangan). Qirra teshigi — har qirraning
o'z mahalliy koordinatasida (Panel 1 — x=0: Xs = chuqurlik, Ys = W − y; Panel 2 — x=L: Xs = chuqurlik, Ys = y;
Panel 3 — y=0: Xs = x, Ys = chuqurlik; Panel 4 — y=W: Xs = L − x, Ys = chuqurlik), balandlik Zs = T − z.
Tartib: yuz teshiklari, Panel 1…4, freza konturlari. Paz bu formatga chiqmaydi. Orqa tomon — X ag'darilgan.
"""
from __future__ import annotations

from . import DrillJob, Files, register
from . import _cnc as C
from ._cnc2 import edge_flags, num, product_order, sweep

TAIL = "Disable:0 ImageX:0 ImageY:0 ImageXY:0 Tool:0"
RK = {0: "0", 1: "2", 2: "1"}           # Y akslangani uchun korreksiya tomoni almashadi
PANEL = (("L", 1), ("R", 2), ("T", 3), ("B", 4))


def n(v: float) -> str:
    return num(v, 4)


def program(job: DrillJob) -> str:
    L, W, T = job.dx, job.dy, job.dz
    lst = C.machine_ops(job)
    e = edge_flags(job)
    desc = C.one_line(f"{product_order(job)} {job.code}").strip()
    head = ["[WXF]", "Version=2.0", f"Description={desc}", "Password=" + "0" * 32, f"X_Length={n(L)}", f"Y_Width={n(W)}",
            f"Z_Thickness={n(T)}",
            f"Edge=Type:61184 Left:{int(e['l'])} Front:{int(e['t'])} Right:{int(e['r'])} Back:{int(e['b'])}",
            "Contour=", "[DATA]"]
    rows = []
    for o in lst:
        if o["t"] == "drill" and o["side"] == "F":
            rows.append(f"Type:57856 Panel:0 Ref:0 Xs:{n(o['x'])} Ys:{n(W - o['y'])} Zs:{n(o['dp'])} Dia:{n(o['d'])} "
                        f"{TAIL} Num:1 Dx:0 Dy:0 Edge:0")
    for side, pn in PANEL:
        for o in lst:
            if o["t"] != "drill" or o["side"] != side:
                continue
            if side == "L":
                xs, ys = o["dp"], W - o["y"]
            elif side == "R":
                xs, ys = o["dp"], o["y"]
            elif side == "T":
                xs, ys = o["x"], o["dp"]
            else:
                xs, ys = L - o["x"], o["dp"]
            rows.append(f"Type:59904 Panel:{pn} Ref:0 Xs:{n(xs)} Ys:{n(ys)} Zs:{n(T - o['z'])} Dia:{n(o['d'])} "
                        f"{TAIL} Num:1 Dx:0 Dy:0 Edge:0")
    for cont in C.contours(lst):
        ms = cont[0]
        dp = ms["dp"]
        p = (ms["x"], ms["y"])
        segs = []
        for o in cont[1:]:
            if o["t"] == "ml":
                segs.append(f"LineTo:(Xe:{n(o['x'])}, Ye:{n(W - o['y'])}, Dep:{n(dp)})")
            else:
                segs.append(f"ArcTo:(Xc:{n(o['cx'])}, Yc:{n(W - o['cy'])}, Dep:{n(dp)}, Angle:{num(sweep(p, o), 5)})")
            p = (o["x"], o["y"])
        rows.append(f"Type:58368 Panel:0 Ref:0 Xs:{n(ms['x'])} Ys:{n(W - ms['y'])} Zs:{n(dp)} Dia:{n(ms['d'])} {TAIL} "
                    f"RK:{RK.get(ms['c'], '0')} Num:{len(segs)}" + "".join(" " + s for s in segs))
    lines = head + [f"Count={len(rows)}"] + [f"{i}={r}" for i, r in enumerate(rows, 1)]
    return "\r\n".join(lines) + "\r\n"


@register("xd_woodcam", "XDWoodCam (.wxf)", "cnc", "wxf",
          note="WXF 2.0. Paz (Groove) bu formatga CHIQMAYDI — namunalardagi kabi (XDWoodCam'da paz amali noma'lum; faqat "
               "pazdan iborat dastur Count=0). Description = mahsulot «Данные заказа» + XNC kodi. Freza: kontur chizig'i, "
               "RK 1↔2 almashgan (Y akslangan), ArcTo — markaz + burilish burchagi. Massiv (Num/Dx/Dy) ishlatilmaydi. "
               "Orqa tomondagi qirra teshigi va freza — namunada yo'q, faraz. Kirill matn cp1251 (tekshirilmagan).")
def xd_woodcam(job: DrillJob) -> Files:
    return [(f"{job.code}.wxf", program(job).encode("cp1251", errors="replace"))]
