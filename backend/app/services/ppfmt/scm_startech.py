"""SCM Startech CN V — `.ISO` (docs/mebelix/postprocessors/scm-startech-cn-v.md).

Bir faylda ≤ 99 dastur (`o1` … `o99`, har faylda 1 dan), nomi `<birinchi>_<oxirgi>.ISO`; avval yuz tomoni dasturlari
(loyiha tartibida), keyin orqa tomon dasturlari. Koordinatalar: boshlanish chap-past, `Y = dy − y`; qirra teshigida
balandlik `z` o'zgarishsiz. Pazlar (`G300`) teshiklardan (`G81`) oldin, en arra qalinligidan katta bo'lsa — bir necha
o'tish (3 mm qadam). Frezalash bu formatga chiqmaydi.
"""
from __future__ import annotations

import math

from . import DrillJob, Files, register, set_batch
from . import _cnc as C

PER_FILE = 99
SAW_STEP = 3.0
K_OF = {"F": 1, "L": 2, "R": 3, "T": 4, "B": 5}


def f3(v: float) -> str:
    return f"{v:.3f}"


def groove_passes(x1: float, y1: float, x2: float, y2: float, w: float, saw: float, step: float = SAW_STEP):
    """Paz o'tishlari (stanok koordinatalarida): [(X, Y)], uzunlik. Birinchi o'tish — harakatning o'ng chekkasi (+w/2),
    keyingilari `step` mm chapga, oxirgisi −w/2 + arra (chap chekkaga tegadi)."""
    ln = math.hypot(x2 - x1, y2 - y1)
    a = math.atan2(y2 - y1, x2 - x1)
    # o'ng normal = −(chap normal); chap normal burchak orqali (a + 90°) — namunadagi «-0.000» ham shundan chiqadi
    lx, ly = math.cos(a + math.pi / 2), math.sin(a + math.pi / 2)
    offs = []
    s = w / 2
    while s > -w / 2 + saw + 1e-9:
        offs.append(s)
        s -= step
    offs.append(-w / 2 + saw)
    return [(x1 - lx * o, y1 - ly * o) for o in offs], ln


def block(n: int, job: DrillJob) -> str:
    dx, dy, dz = job.dx, job.dy, job.dz
    saws, holes = [], []
    for o in C.machine_ops(job):
        t = o["t"]
        if t == "drill":
            K = K_OF[o["side"]]
            if K == 1:
                X, Y = o["x"], dy - o["y"]
            elif K in (2, 3):
                X, Y = o["z"], dy - o["y"]
            else:
                X, Y = o["x"], o["z"]
            holes.append(f"G81 X{f3(X)} Y{f3(Y)} Z{f3(o['dp'])} K{K} J0 I0 Q{f3(o['d'])}")
        elif t == "groove":
            pts, ln = groove_passes(o["x1"], dy - o["y1"], o["x2"], dy - o["y2"], o["w"], o["d"] or 4.0)
            if ln <= 1e-9:
                continue
            saws += [f"G300 X{f3(px)} Y{f3(py)} Q{f3(ln)} Z{f3(o['dp'])} K0 J2 I0" for px, py in pts]
    lines = [f"o{n}", f";{job.code}", f"$1 X{f3(dx)} Y{f3(dy)} Z{f3(dz)}", "(1.000,1.000,0.000)G200", "(1.000)G101",
             *saws, *holes]
    if holes:
        lines.append("G80")
    lines.append("M30")
    return "\r\n".join(lines) + "\r\n"


def files_of(jobs: list[DrillJob]) -> Files:
    seq = [j for j in jobs if j.face] + [j for j in jobs if not j.face]
    out: Files = []
    for start in range(0, len(seq), PER_FILE):
        chunk = seq[start:start + PER_FILE]
        txt = "\r\n".join(block(i, j) for i, j in enumerate(chunk, 1))
        out.append((f"{start + 1}_{start + len(chunk)}.ISO", txt.encode("ascii", errors="replace")))
    return out


@register("scm_startech", "SCM Startech CN V (.ISO)", "cnc", "ISO",
          note="Bir faylda ≤ 99 dastur (1_99.ISO, 100_…); frezalash (kontur) bu formatga chiqmaydi. "
               "Paz eni arra qalinligidan katta bo'lsa — 3 mm qadamli bir necha G300 o'tishi. Qirra teshigi balandligi z "
               "(TPA/Homag dagi dz − z emas). Orqa tomondagi qirra teshigi (K2↔K3) — namunada yo'q, faraz.")
def startech(job: DrillJob) -> Files:
    return files_of([job])


@set_batch("scm_startech")
def startech_batch(jobs: list[DrillJob], project=None) -> Files:
    return files_of(jobs)
