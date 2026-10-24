"""Solishtiruv vositasi (faqat tools/bench): `.project` dagi tayyor CS kroy natijasini (`data` bloki) MX kroy natijasiga aylantirish.

Blok tuzilishi — `project_export_cut.py` (MX o'zi shu formatda yozadi): har karta uchun sarlavha va kesish jadvali yozuvlari
(chuqurlik, tur T/C/P/W, o'lcham, soni, detal id) preorder tartibida. Bu yerda teskari amal: yozuvlardan MX daraxti
(`strips`: k/a/x/y/l/w/c/u) quriladi va `editor.rebuild` bilan to'liq karta (joylashuv, qoldiq, buyruqlar) yasaladi.

Ishlatilishi: postprotsessor fayllarini onlayn tizim natijasi bilan AYNAN shu kroyda solishtirish (tools/bench/pp_online_*).
"""
from __future__ import annotations

import base64
import struct
from dataclasses import dataclass, field

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "backend"))
from app.models import CutMap, CuttingResult, Operation, Project  # noqa: E402

_TYPES = {1: "T", 2: "C", 3: "P", 4: "W"}


@dataclass
class RawMap:
    copies: int
    length: float
    width: float
    stock_id: int
    records: list[tuple[int, str, float, int, int]] = field(default_factory=list)   # (chuqurlik, tur, o'lcham, soni, id)


def decode(data: str) -> list[RawMap]:
    b = base64.b64decode(data)
    o = 0

    def take(fmt: str):
        nonlocal o
        v = struct.unpack_from(fmt, b, o)
        o += struct.calcsize(fmt)
        return v

    _a, _b, _t, n = take(">IIBI")
    out: list[RawMap] = []
    for _ in range(n):
        (mult,) = take(">I")
        length, width, stock, _z = take(">ddIB")
        take(">dddd")
        take(">IdIdIdIdId")
        (nr,) = take(">I")
        m = RawMap(mult, length, width, stock)
        for _ in range(nr):
            tag, size, _z, cnt, pid = take(">BdBBi")
            m.records.append((tag >> 3, _TYPES.get(tag & 7, "T"), size, cnt, pid))
        out.append(m)
    if o != len(b):
        raise ValueError(f"data bloki oxiri mos emas ({o} != {len(b)})")
    return out


def _shift(d: dict, dv: float, ax: str) -> dict:
    out = dict(d)
    out[ax] = round(d[ax] + dv, 3)
    if "c" in d:
        out["c"] = [_shift(c, dv, ax) for c in d["c"]]
    return out


def _tree(m: RawMap, z, kerf: float) -> dict:
    recs = m.records
    axis = "x"
    if recs and recs[0][0] == 0:                     # bo'sh slot — birinchi kesimlar Y bo'ylab
        axis = "y"
        recs = recs[1:]
    pos = 0

    def build(x: float, y: float, l: float, w: float, ax: str, depth: int) -> dict:
        nonlocal pos
        node = {"x": round(x, 3), "y": round(y, 3), "l": round(l, 3), "w": round(w, 3), "k": "C", "a": ax, "c": []}
        cur = x if ax == "x" else y
        end = (x + l) if ax == "x" else (y + w)
        while pos < len(recs) and recs[pos][0] == depth:
            _d, kind, size, cnt, pid = recs[pos]
            pos += 1
            if kind == "T":
                continue
            first = None
            for k in range(max(1, cnt)):
                cx, cy, cl, cw = (cur, y, size, w) if ax == "x" else (x, cur, l, size)
                if kind == "C":                       # ichki yozuvlar bir marta; takrorlar — siljitilgan nusxa
                    if first is None:
                        first = ch = build(cx, cy, cl, cw, "y" if ax == "x" else "x", depth + 1)
                    else:
                        ch = _shift(first, k * (size + kerf), ax)
                elif kind == "P":
                    ch = {"x": round(cx, 3), "y": round(cy, 3), "l": round(cl, 3), "w": round(cw, 3), "k": "P", "u": pid}
                else:
                    ch = {"x": round(cx, 3), "y": round(cy, 3), "l": round(cl, 3), "w": round(cw, 3), "k": "W", "r": 1}
                node["c"].append(ch)
                cur += size + kerf
        rest = end - cur
        if rest > 1e-6:
            wx, wy, wl, ww = (cur, y, rest, w) if ax == "x" else (x, cur, l, rest)
            node["c"].append({"x": round(wx, 3), "y": round(wy, 3), "l": round(wl, 3), "w": round(ww, 3), "k": "W"})
        return node

    root = build(z.ox, z.oy, z.UL, z.UW, axis, 1)
    if pos != len(recs):
        raise ValueError(f"kesish jadvali to'liq o'qilmadi ({pos} / {len(recs)})")
    return root


def to_result(project: Project, op: Operation, data: str) -> CuttingResult:
    """`data` blokidan MX kroy natijasi (list — operatsiyaning birinchi list qatori; o'lchami kartadagidek)."""
    from app.services import editor
    from app.services.optimizer import _zone

    cut = op.cs_cut
    maps: list[CutMap] = []
    for i, rm in enumerate(decode(data), 1):
        st = next((s for s in op.sheets if abs(s.length - rm.length) < 0.5 and abs(s.width - rm.width) < 0.5), None)
        if st is None:
            raise ValueError(f"karta {i}: {rm.length:g}×{rm.width:g} list operatsiyada yo'q")
        z = _zone(st, cut)
        maps.append(CutMap(index=i, sheet_id=st.id, sheet_length=rm.length, sheet_width=rm.width, copies=max(1, rm.copies),
                           strips=[_tree(rm, z, cut.kerf)]))
    return editor.rebuild(project, op, CuttingResult(maps=maps, manual=True))
