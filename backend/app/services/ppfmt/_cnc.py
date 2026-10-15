"""Ishlov markazi (prisadka) formatlari uchun umumiy yordamchi: XNC xom amallari (`DrillJob.raw`, services.xnc.evaluate)
→ soddalashtirilgan amallar ro'yxati.

Koordinatalar — XNC dasturi koordinatalari (chap-yuqori burchak, X o'ngga, Y pastga), burish/ko'zgusiz; formatlar ularni
o'zgarishsiz yoki o'z qoidasi bilan yozadi (korxona namunalarida burish / ko'zgu uchramagan). Amallar:
  drill  — side: F (yuz) | L (x=0) | R (x=dx) | T (y=0) | B (y=dy); x, y (qirrada: qirra bo'ylab koordinata), z (qirra
           teshigi balandligi: M=true → dz/2), dp, d, mid
  groove — x1, y1, x2, y2, dp, w (en), d (arra), c
  ms     — kontur boshi: x, y, dp, d, c, ein (kirish), eout (chiqish), sdp
  ml     — chiziq: x, y
  mac    — markazli yoy: x, y, cx, cy, ccw (True — XNC dir="true")
MillArc (R bilan), MillArc3P, MillRect, MillEllipse — markazli yoy / chiziqlarga yoyiladi (namunada yo'q).
Orqa tomon (`face=False`): `mirror()` — X → dx − x, chap ↔ o'ng qirra, yoy yo'nalishi va korreksiya (1 ↔ 2) teskari.
"""
from __future__ import annotations

import math

from .. import xnc as X

SIDE = {"DrillFront": "F", "DrillLeft": "L", "DrillRight": "R", "DrillTop": "T", "DrillBottom": "B"}


def _fin(v, dflt=0.0) -> float:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return dflt
    return v if math.isfinite(v) else dflt


def ops(job, skip_outside: bool = True) -> list[dict]:
    """`job.raw` → soddalashtirilgan amallar (yuqoridagi tavsif). `skip_outside` — detal tashqarisidagi teshik chiqmaydi."""
    out: list[dict] = []
    pos = None
    for o in job.raw:
        k = o.get("kind", "")
        if k in SIDE:
            if skip_outside and not o.get("inside", True):
                continue
            s = SIDE[k]
            out.append(dict(t="drill", side=s, x=_fin(o.get("X")), y=_fin(o.get("Y")), z=_fin(o.get("Z"), job.dz / 2),
                            dp=_fin(o.get("DP")), d=_fin(o.get("D")), mid=bool(o.get("M"))))
        elif k == "Groove":
            if not o.get("ok", True):
                continue
            out.append(dict(t="groove", x1=o["X1"], y1=o["Y1"], x2=o["X2"], y2=o["Y2"], dp=_fin(o.get("DP")),
                            w=_fin(o.get("W"), 4.0), d=_fin(o.get("D"), 4.0), c=int(o.get("C", 0) or 0)))
        elif k == "MillStart":
            if not o.get("ok", True):
                pos = None
                continue
            pos = (o["X"], o["Y"])
            out.append(dict(t="ms", x=o["X"], y=o["Y"], dp=_fin(o.get("DP")), d=_fin(o.get("D")), c=int(o.get("C", 0) or 0),
                            ein=int(o.get("IN", 0) or 0), eout=int(o.get("OUT", 1) if o.get("OUT") is not None else 1),
                            sdp=_fin(o.get("SDP"), 0.0)))
        elif k in ("MillLine", "MillArc", "MillArcCenter", "MillArc3P"):
            if pos is None or not o.get("ok", True):
                continue
            end = (o["X"], o["Y"])
            if k == "MillArcCenter" and math.isfinite(_fin(o.get("CX"), math.nan)):
                out.append(dict(t="mac", x=end[0], y=end[1], cx=o["CX"], cy=o["CY"], ccw=X._is_ccw(o.get("DIR", ""))))
            elif k != "MillLine" and (g := X.mill_arc(k, pos, o)) is not None:
                _r, _sw, ccw, cen = g
                out.append(dict(t="mac", x=end[0], y=end[1], cx=cen[0], cy=cen[1], ccw=bool(ccw)))
            else:
                out.append(dict(t="ml", x=end[0], y=end[1]))
            pos = end
        elif k == "MillRect" and o.get("ok", True):
            pos = None
            for i, s in enumerate(X.rect_segments(o)):
                if i == 0:
                    out.append(dict(t="ms", x=s[1], y=s[2], dp=_fin(o.get("DP")), d=_fin(o.get("D")),
                                    c=int(o.get("C", 0) or 0), ein=0, eout=1, sdp=0.0))
                elif s[0] == "A":
                    out.append(dict(t="mac", x=s[1], y=s[2], cx=s[3], cy=s[4], ccw=bool(s[5])))
                else:
                    out.append(dict(t="ml", x=s[1], y=s[2]))
        elif k == "MillEllipse" and o.get("ok", True):
            pos = None
            for i, (px, py) in enumerate(X.ellipse_points(o)):
                if i == 0:
                    out.append(dict(t="ms", x=px, y=py, dp=_fin(o.get("DP")), d=_fin(o.get("D")),
                                    c=int(o.get("C", 0) or 0), ein=0, eout=1, sdp=0.0))
                else:
                    out.append(dict(t="ml", x=px, y=py))
    return out


_LR = {"L": "R", "R": "L"}


def mirror(lst: list[dict], dx: float) -> list[dict]:
    """Orqa tomon: detal X bo'yicha ag'dariladi (namunalar: yuz teshigi va paz tasdiqlangan; qirra teshigi va freza — faraz)."""
    res = []
    for o in lst:
        o = dict(o)
        t = o["t"]
        if t == "drill":
            if o["side"] in _LR:
                o["side"] = _LR[o["side"]]
            else:
                o["x"] = dx - o["x"]
        elif t == "groove":
            o["x1"], o["x2"] = dx - o["x1"], dx - o["x2"]
            if o["c"] in (1, 2):
                o["c"] = 3 - o["c"]
        elif t == "ms":
            o["x"] = dx - o["x"]
            if o["c"] in (1, 2):
                o["c"] = 3 - o["c"]
        elif t == "ml":
            o["x"] = dx - o["x"]
        elif t == "mac":
            o["x"], o["cx"] = dx - o["x"], dx - o["cx"]
            o["ccw"] = not o["ccw"]
        res.append(o)
    return res


def machine_ops(job, skip_outside: bool = True) -> list[dict]:
    """Stanok tomoni bo'yicha amallar: orqa tomon dasturi X bo'yicha ag'darilgan."""
    lst = ops(job, skip_outside)
    return lst if job.face else mirror(lst, job.dx)


def contours(lst: list[dict]) -> list[list[dict]]:
    """Ketma-ket ms + (ml|mac)* guruhlari (boshqa amallar orasida)."""
    res, cur = [], None
    for o in lst:
        if o["t"] == "ms":
            cur = [o]
            res.append(cur)
        elif o["t"] in ("ml", "mac") and cur is not None:
            cur.append(o)
        else:
            cur = None
    return res


def dup_names(names: list[str]) -> list[str]:
    """Bir xil nomlar: «kod», «kod (1)», «kod (2)» … (namunalardagi kabi; kengaytmasiz)."""
    seen: dict[str, int] = {}
    out = []
    for n in names:
        i = seen.get(n, 0)
        seen[n] = i + 1
        out.append(n if i == 0 else f"{n} ({i})")
    return out


def part_of(job):
    """Operatsiya bog'langan detal (Part) yoki None."""
    for o in job.project.operations:
        for p in o.parts:
            if job.op.id in p.xnc_op_ids:
                return p
    return None


def has_pair(job) -> bool:
    """Detalning ham yuz, ham orqa tomon XNC dasturi bormi (Homag / Biesse «tomon belgisi»)."""
    p = part_of(job)
    if p is None:
        return False
    sides = set()
    for o in job.project.operations:
        if o.id in p.xnc_op_ids and o.xnc is not None:
            sides.add(bool(o.xnc.face_side))
    return len(sides) == 2


def edge_ops_index(project) -> dict[str, int]:
    """EL operatsiyalari: id → tartib raqami (1 dan; loyihadagi tartibda)."""
    from ...models import OpType
    res = {}
    for o in project.operations:
        if o.type == OpType.EL:
            res[o.id] = len(res) + 1
    return res


def edges(job) -> list[tuple[str, dict]]:
    """Detal kromkalari tartibda top, bottom, left, right: (tomon, {symbol, name, thickness, color (r, g, b), index})."""
    p = part_of(job)
    if p is None:
        return []
    from ...models import OpType
    els = {o.id: o for o in job.project.operations if o.type == OpType.EL}
    idx = edge_ops_index(job.project)
    res = []
    for side in ("top", "bottom", "left", "right"):
        ref = getattr(p, f"edge_{side}", None)
        op = els.get(ref.op_id) if ref is not None and ref.op_id else None
        if op is None:
            continue
        el = op.el
        res.append((side, dict(symbol=(el.symbol if el else "") or "?", name=op.name or "",
                               thickness=float(el.thickness) if el else 0.0, color=rgb(el.color if el else ""),
                               index=idx.get(op.id, 0))))
    return res


def rgb(color: str) -> tuple[int, int, int]:
    """«#D2691E» → (210, 105, 30); noto'g'ri qiymat — qora."""
    c = (color or "").strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    try:
        return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    except (ValueError, IndexError):
        return 0, 0, 0


def one_line(s) -> str:
    """Matn maydoni uchun: qator ko'chirish belgilarisiz."""
    return " ".join(str(s or "").splitlines())
