"""HIRZT MAGI — `.pd4` (CID3 parametrik matn; docs/mebelix/postprocessors/hirzt-magi.md).

Bitta XNC operatsiyasi = bitta `<XNC kodi>.pd4`. Koordinatalar XNC dagidek (X o'ngga, Y pastga), qirra teshigi
balandligi yuqori yuzadan (`dz − z`); orqa tomon — X ag'darilgan. Amallar tartibi: yuz guruhi (yuz teshigi va paz —
dastur tartibida), keyin chap, o'ng, y=dy, y=0 qirralari. Frezalash bu formatga chiqmaydi.
"""
from __future__ import annotations

from . import DrillJob, Files, register
from . import _cnc as C
from ._cnc2 import num

LAB = {"F": "FRONTALE", "L": "SINISTRA", "R": "DESTRA", "B": "SOPRA", "T": "SOTTO"}
SEG = {"FRONTALE": "0.0,0.0,LPZ", "SINISTRA": "0.0,0.0,0.0", "DESTRA": "LPX,0.0,0.0", "SOPRA": "LPX,LPY,0.0",
       "SOTTO": "0.0,0.0,0.0"}
WS = {"FRONTALE": 0, "SINISTRA": 1, "SOPRA": 2, "DESTRA": 3, "SOTTO": 4}
SAW_TECH = ("#NUM_CAT=1,#AR=*,#STDROT_S=*,#STDWRK_S=*,#DWNSPEED=*,#ROTSENSE=*,#ID_DIRECTION=*,#I_X_MIN=*,#I_X_MAX=*,"
            "#I_Y_MIN=*,#I_Y_MAX=*,#I_Z_MIN=*,#I_Z_MAX=*,#I_DEPTH_MIN=*,#I_DEPTH_MAX=*,#PRIORITY=*,#ID_TOOLNAME=*,"
            "#WORKSIDE=*,#ID_PARDISTANCE=*,#BLOCK_PRIO=*,#MIRXY=*,#TOOLPROFILENAME=*,#BLADE_CRU=*,#TYPE=1,#AZ=0.0")
DRILL_TECH = "#NUM_CAT=1,#ID_TOOLNAME=*,#PRIORITY=*,#TYPEDRILL=*,#DWNSPEED=*,#RIFDRILL=*"


def n(v: float) -> str:
    return num(v, 4)


def f1(v: float) -> str:
    return f"{float(v):.1f}"


def items(job: DrillJob) -> list[tuple]:
    """(tekislik, QX, QY, amal, parma turi) — fayldagi tartibda."""
    L, T = job.dx, job.dz
    lst = C.machine_ops(job)
    res = []
    for o in lst:
        if o["t"] == "drill" and o["side"] == "F":
            # parma turi: 2 — o'tuvchi, 3 — katta diametr (≥ 15: petlya, eksentrik), 1 — qolganlari
            typ = 2 if o["dp"] >= T else (3 if o["d"] >= 15 else 1)
            res.append(("FRONTALE", o["x"], o["y"], o, typ))
        elif o["t"] == "groove":
            res.append(("SAW", None, None, o, 1))
    for side in ("L", "R", "B", "T"):
        for o in lst:
            if o["t"] == "drill" and o["side"] == side:
                qx = o["y"] if side in ("L", "R") else (L - o["x"] if side == "B" else o["x"])
                res.append((LAB[side], qx, T - o["z"], o, 1))
    return res


def program(job: DrillJob) -> str:
    L, W, T = job.dx, job.dy, job.dz
    its = items(job)
    out = ["BEGIN ID CID3", f" ''={C.one_line(job.name)}", " REL= 3.10", " AXIS= x+,y-,z-", "END ID", "BEGIN MAINDATA",
           f" LX= {n(L)}", f" LY= {n(W)}", f" LZ= {n(T)}", "END MAINDATA", "BEGIN PARAMETRIC SECTION",
           f"[ 0.0 ] PROGETTO  {job.code} (", f'LPX = {n(L)} NOP "Width"', f', LPY = {n(W)} NOP "Height"',
           f', LPZ = {n(T)} NOP "Thickness"', ") EOS"]
    for i, (lab, qx, qy, o, _typ) in enumerate(its, 1):
        if lab == "SAW":
            out.append(f'[ 0.{i} ] PATH    "" "Saw\\X1_LPX.pm4" QY = {n(o["y1"])} "Quota Y",'
                       f'LPX = {n(abs(o["x2"] - o["x1"]))} "Larghezza",PRF = {n(o["dp"])} "Profondita",'
                       f'SP = {n(o["w"])} "Spessore lama")')
        else:
            out.append(f'[ 0.{i} ] PATH    "" "Drill\\1_Single.pm4" (QX = {n(qx)} "Quota X",QY = {n(qy)} "Quota Y",'
                       f'DIA = {n(o["d"])} "Diametro",PRF = {n(o["dp"])} "Profondita")')
    out += ["----------   LAVORAZIONE BASE DEL PROGETTO   ------------------------------------------------",
            '[  1.0 ] LAYER ON START 1 "WRK" COLORE 3', "[  1.1 ] LAYER  EOS", '[  2.0 ] LAYER ON START 2 "DOC" COLORE 2',
            "[  2.1 ] LAYER  EOS", "[  0.0 ] PUNTO [ 0 , 0 , LPZ ]", "[  0.1 ] CREA_SPACE 1096 1096 16"]
    k = 0
    for j, (lab, _qx, _qy, _o, _typ) in enumerate(its, 1):
        mod = "SIMMETRICO ASSE_Y PIANO  " if lab == "SINISTRA" else ("" if lab in ("FRONTALE", "SAW") else " ")
        lab2 = "FRONTALE" if lab == "SAW" else lab
        out += [f"[ {k + 1}.0 ] CREA_LAB {lab2}",
                f"[ {k + 2}.0 ] SEGMENTO MATITA PER [{SEG[lab2]}] INCLINAZIONE ASSE_X ANGOLO 0 MISURA 1",
                f"[ {k + 3}.0 ] INSERISCI FORI {mod}#{j}"]
        k += 3
    out.append("[  999.  ] FINE_MACRO")
    for j, (lab, _qx, _qy, o, typ) in enumerate(its, 1):
        if lab == "SAW":
            out.append(f"&&& [{j},1] {SAW_TECH},#DIAM={n(o['w'])},#ID_PARDEPTH={n(o['dp'])},#ISBLOCK=0,#SAWINSERTMODE=0")
        else:
            out.append(f"&&& [{j},1] {DRILL_TECH},#TYPE={typ},#AZ=270.000000,#AR=0.000000,#WORKSIDE=0,"
                       f"#DIAM={n(o['d'])},#ID_DEPTH={n(o['dp'])}")
    out.append("END PARAMETRIC SECTION")
    if its:
        out += ["BEGIN BLOCK", "NAME=WRK", "SIDE=0", "COLOR=LIGHT_GREEN", "VISIBILITY=YES"]
        for lab, qx, qy, o, typ in its:
            if lab == "SAW":
                out += ["BEGIN PLINE", "BEGIN TECH", "    CAT=1", "    TYP=1", "    ANG=0.0,0.0", f"    DIAM={n(o['w'])}",
                        "    WORKSIDE=0", f"    PARALDEPTH={n(o['dp'])}", "     ISBLOCK=0", "     SAWINSERTMODE=0", "END TECH",
                        f"    LINE,XS={n(o['x1'])},YS={n(o['y1'])},ZS={n(o['dp'])},"
                        f"XE={n(o['x2'])},YE={n(o['y2'])},ZE={n(o['dp'])}", "END PLINE"]
                continue
            if lab == "FRONTALE":
                pt, ang = f"POINT,X={n(qx)},Y={n(o['y'])},Z=0", "270.0,0.0"
            elif lab in ("SINISTRA", "DESTRA"):
                pt, ang = f"POINT,X={f1(0 if lab == 'SINISTRA' else L)} ,Y={n(qx)},Z={n(qy)}", "0.0,0.0"
            else:
                pt, ang = f"POINT,X={n(qx)} ,Y={f1(W if lab == 'SOPRA' else 0)},Z={n(qy)}", "0.0,0.0"
            out += [" BEGIN CUSTOM", "  BEGIN TECH", "   CAT=1", f"   TYP={typ}", f"   ANG={ang}", f"   DIAM={n(o['d'])}",
                    f"   DEPTH={n(o['dp'])},{n(o['dp'])}", f"   WORKSIDE={WS[lab]}", "  END TECH", "  " + pt, " END CUSTOM"]
        out.append("END BLOCK")
    return "\r\n".join(out) + "\r\n"


@register("hirzt_magi", "HIRZT MAGI (.pd4)", "cnc", "pd4",
          note="CID3 parametrik matn. Frezalash (kontur) bu formatga CHIQMAYDI — namunalardagi kabi (stanokda freza "
               "makrosi noma'lum). Paz — «Saw\\X1_LPX» makrosi (vertikal pazda LPX = 0, haqiqiy chiziq BLOCK da). Parma turi: "
               "2 — o'tuvchi, 3 — d ≥ 15, 1 — qolganlari (chegara 10…15 mm oralig'ida noma'lum). CREA_SPACE 1096 1096 16 va "
               "REL 3.10 — doimiy. Orqa tomondagi qirra teshigi (SINISTRA↔DESTRA) — namunada yo'q, faraz. Kirill nomlar "
               "cp1251 (tekshirilmagan).")
def hirzt_magi(job: DrillJob) -> Files:
    return [(f"{job.code}.pd4", program(job).encode("cp1251", errors="replace"))]
