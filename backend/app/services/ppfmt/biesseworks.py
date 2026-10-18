"""Biesse Works v3.x — `.bpp` (BPP matn formati, VER=130; docs/mebelix/postprocessors/biesse-works-v3.md).

Bitta XNC operatsiyasi = bitta `<XNC kodi>.bpp`. `[PROGRAM]` da ishlov makroslari XNC tartibida (`BG` teshik, `CUT_G` arra
pazi, `ROUT` + kontur elementlari), keyin kromka belgilari (`GEO` + `GEOTEXT`) va yuz/orqa tomon belgisi (`FACE MARK`).
Makros id = 10 × tartib + tur kodi. `"Pnnnnn"` — buyurtma bo'yicha uzluksiz hisoblagich: avval barcha yuz tomoni dasturlari
(loyiha tartibida), keyin orqa tomon dasturlari (batch). Koordinatalar XNC dagidek; orqa tomon — X ag'darilgan.
"""
from __future__ import annotations

from . import DrillJob, Files, register, set_batch
from . import _cnc as C

PANS = ['ORLST|"1"', "SIMMETRY|1", "TLCHK|0", 'TOOLING|""', 'CUSTSTR|""', "FCN|1.000000", "XCUT|0", "YCUT|0", "JIGTH|0",
        "CKOP|0", "UNIQUE|0", 'MATERIAL|"ashwhite"', 'PUTLST|""', "OPPWKRS|0", "UNICLAMP|0", "CHKCOLL|0", "WTPIANI|0",
        "COLLTOOL|0", "CALCEDTH|0", "ENABLELABEL|0", "RUNPAV|1"]
SIDE = {"F": 0, "L": 1, "B": 2, "R": 3, "T": 4}          # BG tomoni
TYPE = {"F": 1, "L": 2, "R": 2, "T": 3, "B": 3}          # id dagi tur kodi
CRC = {1: 2, 2: 1}                                        # XNC C → Biesse korreksiyasi
# kromka belgisi: teg, chiziq (boshi, oxiri), matn (X, Y, burchak)
EDGE = {"top": ("ET", ("0, -10", "LPX, -10"), ("LPX/2", "LPY+25", "0")),
        "bottom": ("EB", ("0, LPY+10", "LPX, LPY+10"), ("LPX/2", "-37", "0")),
        "left": ("EL", ("-10, 0", "-10, LPY"), ("-35", "LPY/2", "90")),
        "right": ("ER", ("LPX+10, 0", "LPX+10, LPY"), ("LPX+25", "LPY/2", "270"))}
GEO_TAIL = '0, 1, 0, 0, 0, 0.1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, "GEO", 0'


def n(v: float) -> str:
    """Eng qisqa ko'rinish, 4 kasrgacha (34, 11.7, 298.2989)."""
    v = round(float(v), 4) + 0.0
    return str(int(v)) if v == int(v) else repr(v)


class _Pid:
    def __init__(self, start: int = 1):
        self.v = start

    def __call__(self) -> str:
        s = f'"P{self.v:05d}"'
        self.v += 1
        return s


def program(job: DrillJob, pid: _Pid) -> str:
    dz = job.dz
    P: list[str] = []
    k = 0

    def mid(t: int) -> int:
        nonlocal k
        k += 1
        return 10 * k + t

    lst = C.machine_ops(job)
    i = 0
    while i < len(lst):
        o = lst[i]
        t = o["t"]
        if t == "drill":
            s = o["side"]
            if s == "F":
                x, y = o["x"], o["y"]
            elif s in ("L", "R"):
                x, y = o["y"], o["z"]
            else:
                x, y = o["x"], o["z"]
            crn = "4" if s in ("R", "T") else "1"
            thr = 1 if s == "F" and o["dp"] > dz else 0      # dp = qalinlik — 0 (onlayn natija, 2026-10-18)
            P.append(f'@ BG, "", "", {mid(TYPE[s])}, "", 0 : {SIDE[s]}, "{crn}", {n(x)}, {n(y)}, 0, {n(o["dp"])}, {n(o["d"])}, '
                     f'0, -1, 32, 32, 50, 0, 45, 0, "", 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, -1, {pid()}, 0, "", "", '
                     f'{thr}, 0, 0, 0, 0, "", 0, 0, 0, 0, 0, "", "", "BG"')
        elif t == "groove":
            P.append(f'@ CUT_G, "", "", {mid(4)}, "", 0 : 0, "1", {n(o["x1"])}, {n(o["y1"])}, 0, {n(o["dp"])}, 2, 0, 0, '
                     f'{n(o["x2"])}, {n(o["y2"])}, 0, 0, "", 1, {n(o["d"])}, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, '
                     f'{n(o["w"])}, 0, 0, 0, 1, {pid()}, "", 201, 2, 0, 0, 0, "", 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, "", "", "CUT_G", 0')
        elif t == "ms":
            j = i + 1
            while j < len(lst) and lst[j]["t"] in ("ml", "mac"):
                j += 1
            # TIN, AIN (kirish turi, burchagi): kontur to'g'ri chiziq bilan boshlansa `9, 0`, yoy bilan boshlansa `1, 88`
            # (ikkinchisi — bitta namunadan; boshqa yoylarda burchak o'zgarishi mumkin — SAVOLLAR.md)
            tin = "1, 88" if j > i + 1 and lst[i + 1]["t"] == "mac" else "9, 0"
            P.append(f'@ ROUT, "", "", {mid(5)}, "", 0 : {pid()}, 0, "1", 0, {n(o["dp"])}, "", 1, {n(o["d"])}, -1, 0, 0, 0, 0, '
                     '50, 0, 45, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0, 0,"", '
                     f'103, 1, {CRC.get(o["c"], 0)}, {tin}, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "", 0, 0, 0, 0, 0, '
                     '0, 0, 0, 0, "", 5, 0, 20, 80, 60, 0, "", "", "ROUT", 0, 0, 0, 0, 0, 0, 0, 0, 0')
            P.append(f'  @ START_POINT, "", "", {mid(6)}, "", 0 : {n(o["x"])}, {n(o["y"])}, 0')
            for s in lst[i + 1:j]:
                if s["t"] == "ml":
                    P.append(f'  @ LINE_EP, "", "", {mid(7)}, "", 0 : {n(s["x"])}, {n(s["y"])}, 0, 0, 0, 0, 0, 0, 0')
                else:
                    P.append(f'  @ ARC_EPCE, "", "", {mid(8)}, "", 0 : {n(s["x"])}, {n(s["y"])}, {n(s["cx"])}, {n(s["cy"])}, '
                             f'{1 if s["ccw"] else 2}, 0, 0, 0, 0, 0, 0')
            P.append(f'  @ ENDPATH, "", "", {mid(9)}, "", 0 :')
            i = j
            continue
        i += 1
    for side, e in C.edges(job):
        pos = side if job.face else {"left": "right", "right": "left"}.get(side, side)
        tag, (a, b), (tx, ty, ang) = EDGE[pos]
        P += [f'@ GEO, "", "{tag}", 0, "", 0 : {pid()}, 0, "1", {GEO_TAIL}',
              f'@ START_POINT, "", "", 0, "", 0 : {a}, 0',
              f'@ LINE_EP, "", "", 0, "", 0 : {b}, 0, 0, 0, 0, 0, 0, 0',
              '@ ENDPATH, "", "", 0, "", 0 :',
              f'@ GEOTEXT, "", "{tag}", 0, "", 0 : {pid()}, 0, "2", "({e["symbol"]}) {n(e["thickness"])}mm", {tx}, {ty}, 0, '
              f'{ang}, 0, 0, 0, 0, 0, 0, "Arial", 32, 0, 0, 0, 0, 1, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, "GEOTEXT"']
    if C.has_pair(job):
        P += [f'@ GEO, "", "FACE MARK", 0, "", 0 : {pid()}, 0, "{1 if job.face else 4}", {GEO_TAIL}',
              '@ START_POINT, "", "", 0, "", 0 : -20, -20, 0']
        P += [f'@ LINE_EP, "", "", 0, "", 0 : {p}, 0, 0, 0, 0, 0, 0, 0' for p in ("0, -20", "0, 0", "-20, 0", "-20, -20")]
        P.append('@ ENDPATH, "", "", 0, "", 0 :')
    name = C.one_line(job.name)
    L = ["[HEADER]", "TYPE=BPP", "VER=130", "", "[DESCRIPTION]", f"|{name}", "|", "", "[VARIABLES]",
         f"PAN=LPX|{n(job.dx)}||0|", f"PAN=LPY|{n(job.dy)}||0|", f"PAN=LPZ|{n(dz)}||0|", *(f"PAN={p}||0|" for p in PANS), "",
         "[PROGRAM]", *P, "", "[VBSCRIPT]", "", "[MACRODATA]", "", "[TDCODES]", "", "[PCF]", "", "[TOOLING]", ""]
    return "\r\n".join(L) + "\r\n"


def _enc(s: str) -> bytes:
    return s.encode("cp1251", errors="replace")


@register("biesseworks", "Biesse Works v3.x (.bpp)", "cnc", "bpp",
          note="Asbob nomi yozilmaydi (faqat diametr). «Pnnnnn» identifikatori butun buyurtma bo'yicha uzluksiz (avval yuz, "
               "keyin orqa tomon dasturlari); bitta dastur eksportida P00001 dan. Qirra teshigi balandligi z (dz − z emas). "
               "Paz korreksiyasi (c≠0), freza kirish/chiqish, orqa tomondagi qirra teshigi va freza — namunada yo'q, faraz. "
               "Kromka matni ET/EB da chiziqqa qarama-qarshi tomonda (namunadagi kabi).")
def biesseworks(job: DrillJob) -> Files:
    return [(f"{job.code}.bpp", _enc(program(job, _Pid())))]


@set_batch("biesseworks")
def biesseworks_batch(jobs: list[DrillJob], project=None) -> Files:
    pid = _Pid()
    txt: dict[int, str] = {}
    for i in [i for i, j in enumerate(jobs) if j.face] + [i for i, j in enumerate(jobs) if not j.face]:
        txt[i] = program(jobs[i], pid)
    return [(f"{j.code}.bpp", _enc(txt[i])) for i, j in enumerate(jobs)]
