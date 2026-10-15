"""Masterwood MW310 — `.prg` (ISO dastur; docs/mebelix/postprocessors/masterwood-mw310.md).

Bitta XNC operatsiyasi = bitta `<XNC kodi>.prg`. Sarlavha: `%`, `|1` … `|14` (`|4` — uzunlik, `|5` — qalinlik, `|6` — en), `:1`;
amallar dastur tartibida; oxiri `%`. Yuz teshigi `G100 X Y Z<chuqurlik> T`; qirra teshigi `G182` (x=0) / `G183` (x=dx):
`X<chuqurlik> Y<dy − y> Z<z>`, `G184` (y=0) / `G185` (y=dy): `X<x> Y<chuqurlik> Z<z>`. Freza: `G172` (boshi, `S20 E10`),
`G42`/`G41`, `G101` (chiziq), `G102`/`G103` (yoy, markaz absolyut `I J`), `G40`. Har amalda asbob raqami (`T`) majburiy —
«Инструменты» jadvalidan (`tooling`). Orqa tomon — X ag'darilgan.
"""
from __future__ import annotations

from . import DrillJob, Files, register
from . import _cnc as C
from . import tooling as TL
from ._cnc2 import num

MILL_S, MILL_E = 20, 10                  # G172 dagi `S` / `E` (namunada o'zgarmas; ma'nosi — ochiq savol)
EDGE = {"L": ("G182", "left"), "R": ("G183", "right"), "T": ("G184", "top"), "B": ("G185", "bottom")}
CORR = {1: "G42", 2: "G41"}              # asbob konturdan o'ngda / chapda (C=0 — korreksiyasiz)
EDGE_X_FROM_RIGHT = False                # G184/G185: X = x (True — dx − x). Namunada x = dx/2 — aniqlab bo'lmaydi


def n(v: float) -> str:
    return num(v, 4)


def front_tool(job: DrillJob, o: dict) -> str:
    """Yuz teshigi asbobi: o'tuvchi (chuqurlik ≥ qalinlik) — «сквозное сверло» qatori, u bo'sh bo'lsa oddiy parma."""
    if o["dp"] >= job.dz - 1e-9:
        v = TL.tool_ref(job, "through", "front", o["d"]) or TL.tool_ref(job, "drill", "front", o["d"])
        return v or TL.need_tool(job, "through", "front", o["d"])
    return TL.need_tool(job, "drill", "front", o["d"])


def mill(job: DrillJob, cont: list[dict]) -> list[str]:
    s = cont[0]
    t = TL.need_tool(job, "mill", "front", s["d"])
    corr = CORR.get(s["c"])
    out = [f"G172 X{n(s['x'])} Y{n(s['y'])} Z{n(s['dp'])} S{MILL_S} E{MILL_E} T{t}"]
    if corr:
        out.append(corr)
    out.append(f"G101 X{n(s['x'])} Y{n(s['y'])} Z{n(s['dp'])}")
    for o in cont[1:]:
        if o["t"] == "mac":
            out.append(f"{'G102' if o['ccw'] else 'G103'} X{n(o['x'])}  Y{n(o['y'])} I{n(o['cx'])} J{n(o['cy'])}")
        else:
            out.append(f"G101 X{n(o['x'])}  Y{n(o['y'])}")
    if corr:
        out += ["G40", f"G101 X{n(cont[-1]['x'])} Y{n(cont[-1]['y'])}"]
    return out


def program(job: DrillJob) -> str:
    L, W = job.dx, job.dy
    out = ["%", "|1", "|2 0", "|3 1", f"|4 {n(L)}", f"|5 {n(job.dz)}", f"|6 {n(W)}", "|7 0 0 0 0", "|8 0",
           *[f"|{i}" for i in range(9, 15)], ":1"]
    lst = C.machine_ops(job)
    i = 0
    while i < len(lst):
        o = lst[i]
        i += 1
        t = o["t"]
        if t == "drill" and o["side"] == "F":
            out.append(f"G100 X{n(o['x'])} Y{n(o['y'])} Z{n(o['dp'])} T{front_tool(job, o)}")
        elif t == "drill":
            g, plane = EDGE[o["side"]]
            tool = TL.need_tool(job, "drill", plane, o["d"])
            if o["side"] in ("L", "R"):
                out.append(f"{g} X{n(o['dp'])} Y{n(W - o['y'])} Z{n(o['z'])} T{tool}")
            else:
                x = L - o["x"] if EDGE_X_FROM_RIGHT else o["x"]
                out.append(f"{g} X{n(x)} Y{n(o['dp'])} Z{n(o['z'])} T{tool}")
        elif t == "groove":
            raise ValueError("паз (Groove) в формат MW310 не выводится — в образцах нет пиления (G180/G181)")
        elif t == "ms":
            cont = [o]
            while i < len(lst) and lst[i]["t"] in ("ml", "mac"):
                cont.append(lst[i])
                i += 1
            if len(cont) > 1:
                out += mill(job, cont)
    out.append("%")
    return "\r\n".join(out) + "\r\n"


@register("mw310", "Masterwood MW310 (.prg)", "cnc", "prg",
          note="Har amalda asbob raqami majburiy («Инструменты» jadvali): parma — tekislik + diametr bo'yicha, o'tuvchi teshik "
               "(chuqurlik ≥ qalinlik) — «сквозное сверло» qatori (bo'sh bo'lsa oddiy parma), freza — «фреза». Qirra teshigi: "
               "G182/G183 da Y = en − y; G184/G185 da X = x va Z = z — namunada simmetrik, faraz. Freza `S20 E10` — namunadagi "
               "o'zgarmas; C=0 (korreksiyasiz) kontur va orqa tomondagi qirra teshigi / freza — namunada yo'q, faraz. "
               "Paz (Groove) chiqmaydi — xato beriladi.")
def mw310(job: DrillJob) -> Files:
    return [(f"{job.code}.prg", program(job).encode("ascii", errors="replace"))]
