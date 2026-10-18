"""TPA Genesis Evolution 8.9 — EDICAD / Albatros `.CNC` (docs/mebelix/postprocessors/tpa-genesis-evolution-8-9.md).

Bitta XNC operatsiyasi = bitta fayl `<XNC kodi>.CNC`. XNC koordinatalari o'zgarishsiz (Y teskari emas); qirra teshigi
balandligi `dz − z`; orqa tomon — X bo'yicha ag'dariladi. Paz eni faylga yozilmaydi (namunadagi kabi bitta makro).
"""
from __future__ import annotations

from . import DrillJob, Files, register
from . import _cnc as C

HEAD = "TPA\\ALBATROS\\EDICAD\\01.00:86:r0w0h0"
MID = ["OFFS{", "#0=0|0", "#1=0|0", "#2=0|0", "#3=0.0|0", "#4=0.0|0", "#5=0.0|0", "#6=0.0|0", "#7=0.0|0", "}OFFS",
       "VARV{", "}VARV", "VAR{", "}VAR", "SPEC{", "}SPEC", "OPTI{", "}OPTI", "LINK{", "}LINK", "PREV{", "}PREV"]
SIDE_NO = {"F": 1, "T": 3, "R": 4, "B": 5, "L": 6}     # TPA tomonlari: 1 yuz, 3 y=0, 4 x=dx, 5 y=dy, 6 x=0


def n(v: float) -> str:
    """4 kasrgacha, ortiqcha nollarsiz (371, 785.99, -11.67)."""
    v = round(float(v), 4) + 0.0
    return str(int(v)) if v == int(v) else repr(v)


def dia(v: float) -> str:
    """Diametr — doim kasr bilan (5.0, 4.5)."""
    return repr(round(float(v), 4) + 0.0)


def program(job: DrillJob) -> str:
    dx, dz = job.dx, job.dz
    sides: dict[int, list[str]] = {k: [] for k in range(1, 7)}
    cur = (0.0, 0.0)
    for o in C.machine_ops(job):
        t = o["t"]
        if t == "drill":
            s = SIDE_NO[o["side"]]
            if s == 1:
                a, b = o["x"], o["y"]
            elif s in (3, 5):
                a, b = o["x"], dz - o["z"]
            else:
                a, b = o["y"], dz - o["z"]
            thr = 1 if s == 1 and o["dp"] >= dz else 0     # dp = qalinlik ham — o'tuvchi (onlayn natija, 2026-10-18)
            sides[s].append(f"W#81{{ ::WTp #1={n(a)} #2={n(b)} #3={n(-o['dp'])} #1002={dia(o['d'])} #1001={thr} }}W")
        elif t == "groove":
            tail = f"#8510={n(o['x1'])} #8511={n(o['y1'])} #8512={n(-o['dp'])} #8514=1 #8515=1 #8525=0 #8526=0 #8527=0 }}W"
            if abs(o["y1"] - o["y2"]) < 1e-9:
                sides[1].append(f"W#1050{{ ::WT2 #6=1 #8509=0 #8517={n(o['x2'])} " + tail)
            else:
                # Y o'qi bo'ylab (qiya paz namunada yo'q — Y bo'ylab yoziladi)
                sides[1].append(f"W#1051{{ ::WT2 #6=1 #8509=1  #8518={n(o['y2'])} " + tail)
        elif t == "ms":
            cur = (o["x"], o["y"])
            sides[1].append(f"W#89{{ ::WTs #1={n(o['x'])} #2={n(o['y'])} #3={n(-o['dp'])} #40={o['c']} #36={n(o['d'] / 2)} }}W")
        elif t == "ml":
            cur = (o["x"], o["y"])
            sides[1].append(f"W#2201{{ ::WTl  #1={n(o['x'])}  #2={n(o['y'])} }}W")
        elif t == "mac":
            sides[1].append(f"W#2101{{ ::WTa  #1={n(o['x'])}  #2={n(o['y'])} #34={1 if o['ccw'] else 0} "
                            f"#31={n(o['cx'] - cur[0])} #32={n(o['cy'] - cur[1])} }}W")
            cur = (o["x"], o["y"])
    lines = [HEAD, f"$={C.one_line(job.name)}", "::SIDE=1", f"::UNm DL={n(job.dx)} DH={n(job.dy)} DS={n(dz)}", *MID]
    for s in range(1, 7):
        lines += [f"SIDE#{s}{{", *sides[s], "}SIDE"]
    return "\r\n".join(lines) + "\r\n"


@register("tpa", "TPA Genesis Evolution 8.9 (EDICAD .CNC)", "cnc", "CNC",
          note="Paz eni (W) faylga yozilmaydi — namunadagi kabi bitta W#1050/W#1051 makrosi; qiya paz W#1051 bo'lib chiqadi. "
               "Qirra teshigi balandligi dz − z. Freza: #40 = korreksiya (C), #36 = freza radiusi (D/2). "
               "Orqa tomondagi qirra teshigi va freza (4↔6, yoy yo'nalishi) — namunada yo'q, faraz.")
def tpa(job: DrillJob) -> Files:
    return [(f"{job.code}.CNC", program(job).encode("cp1251", errors="replace"))]
