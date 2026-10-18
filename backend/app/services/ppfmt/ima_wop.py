"""IMA ImaWop — `.FMC` (INI ko'rinishidagi bloklar, `…60` avlodi; docs/mebelix/postprocessors/ima-imawop.md).

Bitta XNC operatsiyasi = bitta `<XNC kodi>.FMC`. Koordinatalar XNC dagidek (X o'ngga, Y pastga, burishsiz); orqa tomon —
X ag'darilgan. Bloklar: `[PGKOPF60]` (detal), `[PRODUZ60]` (mahsulot, soni), `[BOHRPO60]`, amallar (dastur tartibida:
qirra teshigi `HBXPLU/HBXMIN/HBYPLU/HBYMIN`, yuz teshigi `VBDMES`, freza konturi `KDEFANFC … KDEFENDE` + `KTFRAE60`),
oxirida har kromka uchun `[PRODBLOCK]` (detal tashqarisidagi 5 mm li to'rtburchak belgi). Sonlar 2 xonagacha.
"""
from __future__ import annotations

from ...i18n import _
import math

from . import DrillJob, Files, num_hu, register
from . import _cnc as C
from . import tooling as T
from ._saw_giben import translit

ENC = "cp1251"
MILL_SWKZID = "IMA 601"              # freza asbob identifikatori — namunada doimiy (jadvaldagi nom faylga chiqmagan)
JON = "1"                            # buyurtma raqami maydoni — namunada 1 (manbasi noma'lum)
# Namunada yoy markazi `MPY` ga ham X qiymati yozilgan (MPY = MPX) — aniq xato; standart: to'g'ri markaz.
# True — namunadagi kabi (bayt-ma-bayt solishtirish uchun).
MPY_AS_SAMPLE = False
EDGE_GAP, EDGE_W = 20.0, 5.0         # kromka belgisi: detal chetidan masofa va eni
HOR = {"L": ("HBXPLU60", "Y1", "X"), "R": ("HBXMIN60", "Y1", "X"), "T": ("HBYPLU60", "X1", "Y"),
       "B": ("HBYMIN60", "X1", "Y")}
JUS = {"top": "21", "bottom": "1", "left": "12", "right": "10"}


def n(v: float) -> str:
    return num_hu(v, 2)


def squeeze(s) -> str:
    """Nom maydonlari: bo'sh joysiz («01_001 tr» → «01_001tr»)."""
    return "".join(C.one_line(s).split())


def product_name(job: DrillJob) -> str:
    p = C.part_of(job)
    if p is not None and p.product_id:
        for pr in job.project.products:
            if pr.id == p.product_id:
                return pr.name or ""
    return ""


def _seg(o: dict, lv: str, bezb: bool = True) -> list[str]:
    """Kontur elementi: G1 (chiziq) yoki G2 / G3 (yoy; XNC dir="true" → G3). `lv` — «[» yoki «[[»."""
    rv = "]" * len(lv)
    if o["t"] == "mac":
        r = math.hypot(o["x"] - o["cx"], o["y"] - o["cy"])
        out = [f"{lv}{'G3' if o['ccw'] else 'G2'}{rv}", "BEZB=Arc", "AFB=1", "EB=0", "PKTBEZUG_XY=0", f"MPX={n(o['cx'])}",
               f"MPY={n(o['cx'] if MPY_AS_SAMPLE else o['cy'])}", f"RAD={n(r)}"]
    else:
        out = [f"{lv}G1{rv}"] + (["BEZB=Line"] if bezb else []) + ["AFB=1", "EB=0", "PKTBEZUG_XY=0"]
    return out + [f"X={n(o['x'])}", f"Y={n(o['y'])}", f"Z={n(o.get('zz', 0.0))}"]


def _edge_block(side: str, name: str, L: float, W: float) -> list[str]:
    g, w = EDGE_GAP, EDGE_GAP + EDGE_W
    if side in ("top", "bottom"):
        s = -1 if side == "top" else 1
        y0 = 0.0 if side == "top" else W
        pts = [(L / 2, y0 + s * g), (L, y0 + s * g), (L, y0 + s * w), (0.0, y0 + s * w), (0.0, y0 + s * g), (L / 2, y0 + s * g)]
    else:
        s = -1 if side == "left" else 1
        x0 = 0.0 if side == "left" else L
        pts = [(x0 + s * g, W / 2), (x0 + s * g, W), (x0 + s * w, W), (x0 + s * w, 0.0), (x0 + s * g, 0.0), (x0 + s * g, W / 2)]
    out = ["[PRODBLOCK]", "PRODSTATUS=1", f"BEZ=EDGEBEND-{name}", "[[KDEFANFC]]", "BEZB=Start path", "PKTBEZUG_XY=0",
           f"X={n(pts[0][0])}", f"Y={n(pts[0][1])}", "HP_RADIUS=0", f"JUS={JUS[side]}", f"KNAME={name}", "SICHTBAR=1",
           "TH=-20", "TNAM=Courier New Bold"]
    for x, y in pts[1:]:
        out += _seg(dict(t="ml", x=x, y=y), "[[", bezb=False)
    return out + ["[[KDEFENDE]]", "BEZB=End path"]


def program(job: DrillJob) -> str:
    L, W, D = job.dx, job.dy, job.dz
    lst = C.machine_ops(job)
    if any(o["t"] == "groove" for o in lst):
        raise ValueError(_("pp_e_groove", fmt="ImaWop"))
    prod = translit(squeeze(product_name(job)))   # mahsulot nomi lotincha («Модель2» → «Modely2», onlayn natija 2026-10-18)
    qty = getattr(job.op.xnc, "qty", 1) if job.op.xnc else 1
    # BEZB — operatsiyaning o'z kodi: kodsiz dasturda bo'sh (fayl nomi esa «<loyiha> <nom>», onlayn natija 2026-10-18)
    code = job.code if job.op is None else (job.op.code or "")
    out = ["[PGKOPF60]", f"BEZB={code}", f"FTL={n(L)}", f"FTB={n(W)}", f"FTD={n(D)}", f"KOM1={squeeze(job.name)}",
           "KOM2=", "[PRODUZ60]", "AFB=1", f"BEZB={prod}", f"JON={JON}", "KAF= ", f"KOM={prod}", f"STZ={qty}", "WDA=1",
           "[BOHRPO60]", "BEZB=Hole group optimization", "GPN=1", "OPA=2", "AFB=1"]
    conts = {id(c[0]): c for c in C.contours(lst)}
    k = 0
    for o in lst:
        if o["t"] == "drill" and o["side"] == "F":
            out += ["[VBDMES60]", "BEZB=Vertical drilling", f"DM={n(o['d'])}", f"TI={n(o['dp'])}", f"X={n(o['x'])}",
                    f"Y={n(o['y'])}", "GRP=1", "AFB=1", "PKTBEZUG_XY=0"]
        elif o["t"] == "drill":
            blk, key, ax = HOR[o["side"]]
            pos = o["y"] if ax == "X" else o["x"]
            out += [f"[{blk}]", f"DM={n(o['d'])}", f"TI={n(o['dp'])}", f"{key}={n(pos)}", "GRP=1", f"Z={n(o['z'])}",
                    f"BEZB=Horizontal drilling {ax}", "AFB=1"]
        elif o["t"] == "ms" and len(conts.get(id(o), ())) > 1:
            cont = conts[id(o)]
            T.need_tool(job, "mill", "front", o["d"], "ImaWop")          # nomsiz freza — xato (faylga SWKZID yoziladi)
            k += 1
            kn = f"Kontur{k}"
            zz = max(0.0, D - o["dp"])                                  # Z: detal tagidan (o'tuvchi kesim → 0) — faraz
            segs = [dict(s, zz=zz) for s in cont[1:]]
            x0, y0, trk = n(o["x"]), n(o["y"]), str(o["c"])
            out += ["[KDEFANFC]", f"BEZB=Start path {kn}", "PKTBEZUG_XY=0", f"X={x0}", f"Y={y0}", "HP_RADIUS=0", "JUS=0",
                    f"KNAME={kn}", "SICHTBAR=1", "TH=-10", "TNAM=Courier New"]
            for s in segs:
                out += _seg(s, "[")
            out += ["[KDEFENDE]", "BEZB=End path",
                    "[KTFRAE60]", f"SWKZID={MILL_SWKZID}", f"KNAME={kn}", "KENNUNG=(NULL)", "DEFRICHTUNG=1", f"Z={n(zz)}",
                    "EBG=0", "KD=0", "ROFFSET=0", f"TRKOR={trk}", "KTDAT=0", "LGEAN=0", "LGEAB=0", "EVS=0", "BEZU=Milling",
                    "AFBU=1", "SINDEX=1", "SKENNUNG=KENNUNG$", "SOFFSET=0", "SOFFSETTYP=0", "EINDEX=-1",
                    "EKENNUNG=KENNUNG$", "EOFFSET=0", "EOFFSETTYP=0", "UPCALC=0",
                    "[[KAFRAE60]]", f"SWKZID={MILL_SWKZID}", "BEZB=Call mill", "AFB=1", f"X={x0}", f"Y={y0}", f"Z={n(zz)}",
                    "EBG=0", "KD=0", f"TRKOR={trk}", "PKTBEZUG_XY=0", "EVS=0", "LGEAB=0", "LGEAN=0"]
            for s in segs:
                out += _seg(s, "[[")
            out += ["[[KDEFENDE]]", "BEZB=End path"]
    swap = {"left": "right", "right": "left"} if not job.face else {}
    es = {swap.get(side, side): e for side, e in C.edges(job)}
    for side in ("top", "bottom", "left", "right"):
        if side in es:
            out += _edge_block(side, C.one_line(es[side]["name"]), L, W)
    return "\r\n".join(out) + "\r\n"


@register("ima_wop", "IMA ImaWop (.FMC)", "cnc", "FMC",
          note="Bloklar …60 avlodi (PGKOPF60, VBDMES60, HBX/HBY PLU/MIN 60, KTFRAE60). Teshiklar diametr bo'yicha (DM), freza — "
               "asboblar jadvalida nom bo'lishi shart, lekin faylga SWKZID=IMA 601 yoziladi (namunadagi kabi). Yoy markazi: "
               "namunada MPY = MPX (xato) — biz to'g'ri markaz yozamiz. Paz (Groove) — namuna yo'q, xato beradi. Qirra teshigi "
               "Z bazasi, o'tuvchi teshik, chuqurligi < qalinlik freza (Z), orqa tomondagi kromka chap ↔ o'ng, JON — faraz.")
def ima_wop(job: DrillJob) -> Files:
    return [(f"{job.code}.FMC", program(job).encode(ENC, errors="replace"))]
