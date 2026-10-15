"""Homag woodWOP v6.x — `.mpr` (woodWOP 4.0 matn formati; docs/mebelix/postprocessors/homag-woodwop-v6.md).

Bitta XNC operatsiyasi = bitta `<XNC kodi>.mpr`. Sarlavha `[H`, o'zgaruvchilar `[001`, zagotovka `<100`, keyin amallar XNC
tartibida (`<102` yuz teshigi, `<103` qirra teshigi, `<109` paz, `]n`+`$E…`+`<105` freza konturi), oxirida `<152` grafik
izohlar (kromka chiziqlari, yuz/orqa tomon belgisi) va `!`. Koordinatalar XNC dagidek; orqa tomon — X ag'darilgan.
"""
from __future__ import annotations

from . import DrillJob, Files, register
from . import _cnc as C

PICTURE = ["STARTLOCAL", "SIZE X100.0000 Y100.0000", "SPINDLE X0.0000 Y0.0000", "U", "X0.0000 Y0.0000", "D",
           "X100.0000 Y0.0000", "X100.0000 Y100.0000", "X0.000 Y100.0000", "X0.000 Y0.0000", "ENDLOCAL"]
RK = {1: "WRKL", 2: "WRKR"}
BM = {"L": "XP", "R": "XM", "T": "YP", "B": "YM"}


from . import tooling as TL          # freza / paz arrasi raqami — «Инструменты» jadvalidan (bo'sh bo'lsa -1)

def f(v: float) -> str:
    """2 xonagacha yaxlitlab, eng qisqa ko'rinish (34.0 → 34, 590.9996 → 591, 313.4998 → 313.5)."""
    v = round(float(v) + 0.0, 2)
    s = ("%.2f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def fd(v: float) -> str:
    """Qarama-qarshi qirra koordinatasi (dx / dy) — kasr bilan («368.0»), namunadagi kabi."""
    return repr(float(v))


def qty(job: DrillJob) -> int:
    p = C.part_of(job)
    if p is not None:
        return int(p.qty)
    return int(getattr(job.op.xnc, "qty", 1) or 1)


def program(job: DrillJob) -> str:
    dx, dy, dz = job.dx, job.dy, job.dz
    L = ["[H", 'VERSION="4.0 Alpha"', 'MAT="HOMAG"', 'FM="1"', 'INCH="0"', 'VIEW="NOMIRROR"', f'ANZ="{qty(job)}"',
         'BES="0"', 'ENT="0"', f"_BSX={f(dx)}", f"_BSY={f(dy)}", f"_BSZ={f(dz)}", "_FNX=0.000000", "_FNY=0.000000",
         "_RNX=0.000000", "_RNY=0.000000", "_RNZ=0.000000", f"_RX={f(dx)}", f"_RY={f(dy)}", "",
         "[001", f'l="{f(dx)}"', 'KM="length"', f'w="{f(dy)}"', 'KM="width"', f't="{f(dz)}"', 'KM="thickness"', "",
         "<100 \\WerkStck\\", 'LA="l"', 'BR="w"', 'DI="t"', 'FNX="0"', 'FNY="0"', 'AX="0"', 'AY="0"']
    lst = C.machine_ops(job)
    kno = 0
    i = 0
    while i < len(lst):
        o = lst[i]
        t = o["t"]
        if t == "drill" and o["side"] == "F":
            L += ["", "<102 \\BohrVert\\", f'XA="{f(o["x"])}"', f'YA="{f(o["y"])}"']
            if o["dp"] >= dz:
                L += ['BM="LSL"']
            else:
                L += ['BM="LS"', f'TI="{f(o["dp"])}"']
            L += [f'DU="{f(o["d"])}"']
        elif t == "drill":
            s = o["side"]
            xa = "0" if s == "L" else fd(dx) if s == "R" else f(o["x"])
            ya = "0" if s == "T" else fd(dy) if s == "B" else f(o["y"])
            za = dz / 2 if o["mid"] else dz - o["z"]
            L += ["", "<103 \\BohrHoriz\\", f'XA="{xa}"', f'YA="{ya}"', f'ZA="{f(za)}"', f'TI="{f(o["dp"])}"',
                  f'BM="{BM[s]}"', f'DU="{f(o["d"])}"']
        elif t == "groove":
            L += ["", "<109 \\Nuten\\", f'XA="{f(o["x1"])}"', f'YA="{f(o["y1"])}"', f'XE="{f(o["x2"])}"',
                  f'YE="{f(o["y2"])}"', f'TI="{f(o["dp"])}"', f'NB="{f(o["w"])}"', f'RK="{RK.get(o["c"], "NoWRK")}"',
                  f'TNO="{TL.tool_ref(job, "saw", "front", o["w"], "-1")}"', 'EM="MOD1"']
        elif t == "ms":
            kno += 1
            j = i + 1
            while j < len(lst) and lst[j]["t"] in ("ml", "mac"):
                j += 1
            seg = lst[i:j]
            L += ["", f"]{kno}", "$E0", "KP ", f"X={f(o['x'])}", f"Y={f(o['y'])}", "Z=0", "KO=00"]
            cur = (o["x"], o["y"])
            for e, s in enumerate(seg[1:], 1):
                if s["t"] == "ml":
                    L += ["", f"$E{e}", "KL ", f"X={f(s['x'])}", f"Y={f(s['y'])}"]
                else:
                    r = ((cur[0] - s["cx"]) ** 2 + (cur[1] - s["cy"]) ** 2) ** 0.5
                    L += ["", f"$E{e}", "KA", f"X={f(s['x'])}", f"Y={f(s['y'])}", f"DS={1 if s['ccw'] else 0}", f"R={f(r)}"]
                cur = (s["x"], s["y"])
            L += ["", "<105 \\Konturfraesen\\", f'EA="{kno}:0"', f'EE="{kno}:{len(seg) - 1}"',
                  f'RK="{RK.get(o["c"], "NoWRK")}"', 'MDA="SEN"', 'MDE="SEN_AB"', 'EM="0"', f'TNO="{TL.tool_ref(job, "mill", "front", o["d"], "-1")}"',
                  f'ZA="{f(max(0.0, dz - o["dp"]))}"', 'F_="STANDARD"']
            i = j
            continue
        i += 1
    # kromka chiziqlari (faqat ekran uchun): tartib top, bottom, left, right; orqa tomonda chap ↔ o'ng joy almashadi
    for side, e in C.edges(job):
        pos = side
        if not job.face:
            pos = {"left": "right", "right": "left"}.get(side, side)
        xa, ya, br, he = {"top": (dx / 2, 0, dx, 5), "bottom": (dx / 2, dy, dx, 5),
                          "left": (0, dy / 2, 5, dy), "right": (dx, dy / 2, 5, dy)}[pos]
        rgb = e["color"]                 # kromka operatsiyasining rangi («Цвет»)
        L += ["<152 \\Grafischer Kommentar\\", 'LOCAL="1"', f'XA="{f(xa)}"', f'YA="{f(ya)}"', f'BR="{f(br)}"',
              f'HE="{f(he)}"', 'WI="0"', f'ROT="{rgb[0]}"', f'GRUEN="{rgb[1]}"', f'BLAU="{rgb[2]}"', 'WIDTH="3"',
              f'KAT="{e["name"]}"', f'MNM="{e["name"]}"', *PICTURE]
    if C.has_pair(job):                 # yuz / orqa tomon belgisi (detalda ikkala tomon dasturi bo'lsa)
        xa, rgb = (dx - 30, (10, 200, 150)) if job.face else (30, (200, 10, 150))
        L += ["<152 \\Grafischer Kommentar\\", 'LOCAL="2"', f'XA="{f(xa)}"', 'YA="30"', f'ROT="{rgb[0]}"',
              f'GRUEN="{rgb[1]}"', f'BLAU="{rgb[2]}"', 'BR="20"', 'HE="20"', 'WI="0"', 'WIDTH="3"', *PICTURE]
    L.append("!")
    return "\r\n".join(L) + "\r\n"


@register("woodwop", "Homag woodWOP v6.x (.mpr)", "cnc", "mpr",
          note="woodWOP 4.0 matn formati. Asbob raqami yozilmaydi (TNO=-1, stanok diametr bo'yicha tanlaydi). Freza: kirish "
               "SEN / chiqish SEN_AB (namunada yagona), ZA = qalinlik − chuqurlik (namunada faqat o'tuvchi → 0, faraz). "
               "Qirra teshigi ZA = dz − z. Orqa tomondagi qirra teshigi (XP↔XM) va freza (DS, WRKL↔WRKR) — namunada yo'q, "
               "faraz. Kromka chizig'i rangi — kromka operatsiyasining rangi.")
def woodwop(job: DrillJob) -> Files:
    return [(f"{job.code}.mpr", program(job).encode("cp1251", errors="replace"))]
