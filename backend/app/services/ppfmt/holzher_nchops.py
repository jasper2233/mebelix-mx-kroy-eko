"""Holz-Her NC-HOPS — `.hop` (matn: `;KALIT=` sarlavha, `VARS`, `START`, buyruqlar; docs/mebelix/postprocessors/holz-her-nchops.md).

Bitta XNC operatsiyasi = bitta `<XNC kodi>.hop`. X — XNC dagidek, Y teskari (`DY − y`: koordinata boshi pastki-chap burchak),
chuqurlik manfiy. Amallar dastur tartibida: `HORD` (qirra teshigi; burilish 0 — x=0, 180 — x=DX, 90 / 270 — Y qirralari),
`DRILLING` (yuz teshigi), freza konturi `TOOLM` + `SP` / `G01` / `G02C` / `G03C` / `EP`. Asbob almashganda `TOOLD` / `TOOLM`.
Orqa tomon — X ag'darilgan.
"""
from __future__ import annotations

from ...i18n import _
from . import DrillJob, Files, register
from . import _cnc as C
from . import tooling as T
from ._cnc2 import num

ENC = "cp1251"
DRILL_HEAD = 501                 # parmalash kallagi (jadvalda parma raqami ko'rsatilmagan / −1 bo'lsa)
# Namunada y=0 qirrasidagi (DrillTop) teshik Y=0 / 90° yozilgan, holbuki boshqa hamma amalda Y teskari (DY − y) — ya'ni
# teshik qarama-qarshi qirraga tushadi (namunadagi detallar simmetrik, shuning uchun faqat qatorlar tartibi farq qiladi).
# Standart: geometriya bo'yicha to'g'ri (DrillTop → Y=DY, 270°). True — namunadagi kabi (bayt-ma-bayt solishtirish uchun).
TB_AS_SAMPLE = False
PLANE = {"F": "front", "L": "left", "R": "right", "T": "top", "B": "bottom"}


def n(v: float) -> str:
    return num(v, 4)


def _tool_no(v: str):
    i = T.ref_int(v)
    return i if i is not None and i >= 0 else None


def drill_tool(job: DrillJob, o: dict) -> int:
    kind = "through" if o["side"] == "F" and o["dp"] >= job.dz else "drill"
    v = _tool_no(T.tool_ref(job, kind, PLANE[o["side"]], o["d"]))
    if v is None and kind == "through":
        v = _tool_no(T.tool_ref(job, "drill", "front", o["d"]))
    return DRILL_HEAD if v is None else v


def mill_tool(job: DrillJob, d: float) -> int:
    v = _tool_no(T.need_tool(job, "mill", "front", d, "NC-HOPS"))
    if v is None:                                # «−1» yoki son emas — ko'rsatilmagan hisoblanadi
        raise ValueError(_("pp_e_tool_no", d=num(d, 3)))
    return v


def lines(job: DrillJob) -> list[str]:
    L, W = job.dx, job.dy
    lst = C.machine_ops(job)
    if any(o["t"] == "groove" for o in lst):
        raise ValueError(_("pp_e_groove", fmt="NC-HOPS"))
    conts = {id(c[0]): c for c in C.contours(lst)}
    out: list[str] = []
    cur = None                                   # joriy asbob: ("D" | "M", raqam)
    for o in lst:
        if o["t"] == "drill":
            tool = ("D", drill_tool(job, o))
            if tool != cur:
                out.append(f"TOOLD ({tool[1]},_VE,_V,_VA,_SD,_ANF,'')")
                cur = tool
            s = o["side"]
            if s == "F":
                out.append(f"DRILLING ({n(o['x'])},{n(W - o['y'])},{n(o['d'])},{n(-o['dp'])},10,0,0,1,0,0,0,0)")
                continue
            if s in ("L", "R"):
                x, y, ang = (0.0, W - o["y"], 0) if s == "L" else (L, W - o["y"], 180)
            elif (s == "T") == TB_AS_SAMPLE:
                x, y, ang = o["x"], 0.0, 90
            else:
                x, y, ang = o["x"], W, 270
            out.append(f"HORD ({n(x)},{n(y)},{n(o['z'])},{n(o['d'])},{n(-o['dp'])},10,0,{ang},0,2,0,0)")
        elif o["t"] == "ms" and len(conts.get(id(o), ())) > 1:
            cont = conts[id(o)]
            tool = ("M", mill_tool(job, o["d"]))
            if tool != cur:
                out.append(f"TOOLM ({tool[1]},_VE,_V,_VA,_SD,0,'')")
                cur = tool
            z = n(-o["dp"])
            out.append(f"SP ({n(o['x'])},{n(W - o['y'])},{z},{o['c']},0,_ANF," + ",".join(["0"] * 17) + ")")
            for g in cont[1:]:
                if g["t"] == "mac":
                    out.append(f"{'G03C' if g['ccw'] else 'G02C'} ({n(g['x'])},{n(W - g['y'])},{z},{n(g['cx'])},"
                               f"{n(W - g['cy'])},0,0,0,0)")
                else:
                    out.append(f"G01 ({n(g['x'])},{n(W - g['y'])},{z},0,0,0)")
            out.append("EP (0,_ANF,0)")
    return out


def program(job: DrillJob) -> str:
    out = [";KOMMENTAR=", ";DX=0.000", ";DY=0.000", ";DZ=0", ";DIALOGDLL=Dialoge.Dll", ";DIALOGPROC=StandardFormAnzeigen",
           ";AUTOSCRIPTSTART=1", ";BUTTONBILD=", ";DIMENSION_UNIT=0", "VARS",
           f"   DX := {n(job.dx)};*VAR*Dimension X", f"   DY := {n(job.dy)};*VAR*Dimension Y",
           f"   DZ := {n(job.dz)};*VAR*Dimension Z", "START", "FinishedPart (DX,DY,DZ,0,0,0,0,0,'',0,0,0)",
           "CALL HH_Park ( VAL PARK:=3,X:=0,Y:=0)"]
    return "\r\n".join(out + lines(job)) + "\r\n"


@register("holzher_nchops", "Holz-Her NC-HOPS (.hop)", "cnc", "hop",
          note="Y teskari (DY − y), chuqurlik manfiy. Parmalar: jadvalda raqam bo'lmasa TOOLD (501 — parmalash kallagi, diametr "
               "bo'yicha); freza raqami majburiy (TOOLM). DrillTop/DrillBottom: namunada Y teskari qilinmagan (xato) — biz "
               "geometriya bo'yicha to'g'ri yozamiz. Paz (Groove) — namuna yo'q, xato beradi. DRILLING sikl kodi doim 10 "
               "(o'tuvchi teshik ham), HORD Z bazasi, SP dagi korreksiya kodi (C=0/2), orqa tomon freza / qirra teshigi — faraz.")
def holzher_nchops(job: DrillJob) -> Files:
    return [(f"{job.code}.hop", program(job).encode(ENC, errors="replace"))]
