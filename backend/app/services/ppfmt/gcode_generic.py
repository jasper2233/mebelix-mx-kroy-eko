"""Umumiy «G CODE» — kengaytmasiz matn fayl (docs/mebelix/postprocessors/gcode.md).

Bitta XNC operatsiyasi = bitta `<XNC kodi>` fayli; qatorlar `N10`, `N20`, … bilan raqamlanadi, CRLF, oxirgi qatordan keyin
qator ko'chirish yo'q. Faqat YUZ amallari chiqadi: teshik (`X Y Z-chuqurlik`) va freza konturi (`G0`/`G41`/`G1`/`G2`/`G3`);
qirra teshiklari bu formatga chiqmaydi. Ketma-ket bir xil asbobli amallar — bitta guruh: `(<d>MM <asbob nomi>)`, `M06`,
`S3000 M04`, …, `M05`. Asbob raqami yozilmaydi («Инструменты» jadvali ishlatilmaydi). Koordinatalar XNC dagidek (Y pastga),
orqa tomon — X ag'darilgan.

Paket holati (`State`): parmalash siklini bekor qilish (`G80`) keyingi guruh / keyingi fayl boshida yoziladi, frezada `Z`
so'zi faqat oxirgi yozilganidan farq qilsa chiqadi — ikkalasi ham bir paketdagi fayllar orasida saqlanadi (namunalardagi kabi).
"""
from __future__ import annotations

from . import DrillJob, Files, register, set_batch
from . import _cnc as C
from ._cnc2 import num

TITLE = "(generated code in MebeliX Kroy)"
SPEED = "S3000 M04"
SAFE_Z = 20
FEED = 100
CORR = {1: "G41", 2: "G42"}              # C=0 → G40 (namunada yo'q — faraz)


class State:
    """Paket bo'ylab saqlanadigan holat."""

    def __init__(self) -> None:
        self.cycle = False               # parmalash sikli ochiq (G80 hali yozilmagan)
        self.z: str | None = None        # freza qatorlarida oxirgi yozilgan Z


def n(v: float) -> str:
    return num(v, 4)


def tool_names(job: DrillJob) -> list[str]:
    """`C.ops` dagi drill / ms amallariga mos asbob nomlari (XNC `T`), o'sha tartib va o'sha filtr bilan."""
    res = []
    for o in job.raw:
        k = o.get("kind", "")
        if (k in C.SIDE and o.get("inside", True)) or (k in ("MillStart", "MillRect", "MillEllipse") and o.get("ok", True)):
            res.append(str(o.get("T") or ""))
    return res


def groups(job: DrillJob) -> list[tuple[str, float, list]]:
    """Yuz amallari guruhlari: (asbob nomi, diametr, [("d", teshik) | ("m", kontur)]) — ketma-ket bir xil asbob."""
    lst = C.machine_ops(job)
    names = tool_names(job)
    if len(names) != sum(1 for o in lst if o["t"] in ("drill", "ms")):
        names = []                                           # moslik buzilsa — nomsiz
    res: list[tuple[str, float, list]] = []
    k = i = 0
    while i < len(lst):
        o = lst[i]
        i += 1
        t = o["t"]
        if t == "groove":
            raise ValueError("паз (Groove) в формат G CODE не выводится — в образцах нет пиления")
        if t not in ("drill", "ms"):
            continue
        name = names[k] if k < len(names) else ""
        k += 1
        if t == "drill":
            if o["side"] != "F":
                continue                                     # qirra teshigi chiqmaydi
            item = ("d", o)
        else:
            cont = [o]
            while i < len(lst) and lst[i]["t"] in ("ml", "mac"):
                cont.append(lst[i])
                i += 1
            if len(cont) < 2:
                continue
            item = ("m", cont)
        if res and res[-1][0] == name and abs(res[-1][1] - o["d"]) < 1e-9:
            res[-1][2].append(item)
        else:
            res.append((name, o["d"], [item]))
    return res


def mill(cont: list[dict], st: State) -> list[str]:
    s = cont[0]
    x, y, z = n(s["x"]), n(s["y"]), n(-s["dp"])
    out = [f"G0 X{x} Y{y} Z{SAFE_Z}", f"G0 {CORR.get(s['c'], 'G40')} X{x} Y{y}", f"Z{z} F{FEED}"]
    px, py = s["x"], s["y"]
    for o in cont[1:]:
        w = ["G1" if o["t"] == "ml" else ("G3" if o["ccw"] else "G2")]
        if n(o["x"]) != x:
            x = n(o["x"])
            w.append(f"X{x}")
        if n(o["y"]) != y:
            y = n(o["y"])
            w.append(f"Y{y}")
        if o["t"] == "mac":
            w += [f"I{n(o['cx'] - px)}", f"J{n(o['cy'] - py)}"]
        if st.z != z:
            st.z = z
            w.append(f"Z{z}")
        out.append(" ".join(w))
        px, py = o["x"], o["y"]
    out.append(f"G0 Z{SAFE_Z}")
    return out


def program(job: DrillJob, st: State | None = None) -> str:
    st = st or State()
    out = [TITLE, "G90"]
    if st.cycle:
        out.append("G80")
        st.cycle = False
    grp = groups(job)
    for gi, (name, d, items) in enumerate(grp):
        out += [f"({n(d)}MM {name})".replace(" )", ")"), "M06", SPEED]
        for kind, o in items:
            if kind == "d":
                out.append(f"X{n(o['x'])} Y{n(o['y'])} Z{n(-o['dp'])}")
                st.cycle = True
            else:
                out += mill(o, st)
        if gi < len(grp) - 1 and st.cycle:
            out.append("G80")
            st.cycle = False
        out.append("M05")
    out.append("M30")
    return "\r\n".join(f"N{10 * (i + 1)} {s}" for i, s in enumerate(out))


def dup_names(codes: list[str]) -> list[str]:
    """Bir xil kodlar: «kod», «kod(1)», «kod(2)» (namunadagi kabi — probelsiz)."""
    seen: dict[str, int] = {}
    out = []
    for c in codes:
        i = seen.get(c, 0)
        seen[c] = i + 1
        out.append(c if i == 0 else f"{c}({i})")
    return out


@register("gcode", "G CODE (umumiy)", "cnc", "",
          note="Faqat yuz teshiklari va freza konturlari chiqadi — qirra teshiklari bu formatda yo'q. Asbob raqami yozilmaydi "
               "(`M06` raqamsiz, izohda diametr + XNC asbob nomi). `S3000`, `F100`, xavfsiz Z20 — namunadagi o'zgarmaslar. "
               "Paketda `G80` va freza `Z` so'zi oldingi faylga bog'liq (namunadagi kabi). C=0 konturda `G40`, C=2 da `G42` — "
               "faraz. Paz (Groove) chiqmaydi — xato beriladi.")
def gcode(job: DrillJob) -> Files:
    return [(job.code, program(job).encode("ascii", errors="replace"))]


@set_batch("gcode")
def gcode_batch(jobs: list[DrillJob], project=None) -> Files:
    st = State()
    names = dup_names([j.code for j in jobs])
    return [(nm, program(j, st).encode("ascii", errors="replace")) for nm, j in zip(names, jobs)]
