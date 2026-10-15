"""XNC dasturi (MebeliX buyruqlar daraxti) → `.project` dagi `program` XML matni (`operation typeId="XNC"` atributi).

`plugins/legacy_project.py::program_to_commands` ning TESKARISI: formatning ochiq tavsifidagi teglar —
`tool var bf bl br bt bb ms ml ma mac gr xy` (+ har tegda `comment`, `enable`; frontal teshik massivi `ac/as/av`;
`ms` uchun `sdp sxy c in out`; qirra teshigi `m`, `ver`).

Formatda teg nomi tavsiflanmagan buyruqlar (shartlar If/Else, sikllar, qism dasturlar, Set, Msg, Err, to'rtburchak /
ellips / 3 nuqtali yoy / fillet) uchun dastur «yoyilgan» yoziladi: `evaluate()` natijasi — tayyor koordinatali teglar
(parametrika yo'qoladi, geometriya va statistika saqlanadi). Bunday dastur haqida ogohlantirish beriladi. `Par` (kiritiladigan
parametr) — `var` ga aylanadi (kiritilgan yoki standart qiymat). `Com` (izoh) yozilmaydi.
"""
from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from typing import Callable

from ..models import XNCParams, XncCommand
from . import xnc as X

PROLOG = '<?xml version="1.0" encoding="UTF-8"?>'
_BAD_CHARS = "".join(chr(c) for c in list(range(0, 9)) + [11, 12] + list(range(14, 32))) + "￾￿"
_STRIP = {ord(ch): None for ch in _BAD_CHARS}


def clean(s) -> str:
    """XML 1.0 da ruxsat etilmagan boshqaruv belgilarini olib tashlaydi."""
    return str(s).translate(_STRIP)


def num(v) -> str:
    """Son → matn (butun bo'lsa nuqtasiz; aks holda eng qisqa aylanma-aniq yozuv)."""
    f = float(v)
    if not math.isfinite(f):
        return "0"
    if f == int(f) and abs(f) < 1e15:
        return str(int(f))
    return repr(f)


def boolean(v) -> str:
    return "true" if v else "false"


def _val(v) -> str | None:
    """Buyruq parametri (son yoki ifoda matni) → atribut qiymati; bo'sh — None."""
    if v is None:
        return None
    if isinstance(v, bool):
        return boolean(v)
    if isinstance(v, (int, float)):
        return num(v)
    s = clean(v).strip()
    return s or None


def _bool_val(v, default: str | None = None) -> str | None:
    """Mantiqiy parametr: `true/false/1/0` yoki son; ifoda bo'lsa — matn o'zi (formatda ifoda ruxsat etilgan joylar uchun)."""
    if v is None or v == "":
        return default
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return boolean(v != 0)
    s = clean(v).strip()
    low = s.lower()
    if low in ("true", "1", "ccw"):
        return "true"
    if low in ("false", "0"):
        return "false"
    return s


def _int_val(v, default: int = 0) -> str:
    try:
        return str(int(round(float(v))))
    except (TypeError, ValueError):
        return str(default)


# MebeliX buyrug'i → (teg, [(parametr, atribut, tur)]); tur: e — ifoda/son, b — mantiqiy, i — butun, s — matn
_PLAIN: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "DrillFront": ("bf", [("X", "x", "e"), ("Y", "y", "e"), ("DP", "dp", "e"), ("AC", "ac", "e"), ("AS", "as", "e"),
                          ("AV", "av", "b"), ("T", "name", "s")]),
    "DrillLeft": ("bl", [("Y", "y", "e"), ("Z", "z", "e"), ("M", "m", "b"), ("DP", "dp", "e"), ("AC", "ac", "e"),
                         ("AS", "as", "e"), ("VER", "ver", "e"), ("T", "name", "s")]),
    "DrillRight": ("br", [("Y", "y", "e"), ("Z", "z", "e"), ("M", "m", "b"), ("DP", "dp", "e"), ("AC", "ac", "e"),
                          ("AS", "as", "e"), ("VER", "ver", "e"), ("T", "name", "s")]),
    "DrillTop": ("bt", [("X", "x", "e"), ("Z", "z", "e"), ("M", "m", "b"), ("DP", "dp", "e"), ("AC", "ac", "e"),
                        ("AS", "as", "e"), ("VER", "ver", "e"), ("T", "name", "s")]),
    "DrillBottom": ("bb", [("X", "x", "e"), ("Z", "z", "e"), ("M", "m", "b"), ("DP", "dp", "e"), ("AC", "ac", "e"),
                           ("AS", "as", "e"), ("VER", "ver", "e"), ("T", "name", "s")]),
    "MillStart": ("ms", [("X", "x", "e"), ("Y", "y", "e"), ("DP", "dp", "e"), ("T", "name", "s"), ("C", "c", "i"),
                         ("SDP", "sdp", "e"), ("SXY", "sxy", "e"), ("IN", "in", "i"), ("OUT", "out", "i")]),
    "MillLine": ("ml", [("X", "x", "e"), ("Y", "y", "e"), ("DP", "dp", "e")]),
    "MillArc": ("ma", [("X", "x", "e"), ("Y", "y", "e"), ("DP", "dp", "e"), ("R", "r", "e"), ("DIR", "dir", "b")]),
    "MillArcCenter": ("mac", [("X", "x", "e"), ("Y", "y", "e"), ("CX", "cx", "e"), ("CY", "cy", "e"),
                              ("DP", "dp", "e"), ("DIR", "dir", "b")]),
    "Groove": ("gr", [("X1", "x1", "e"), ("Y1", "y1", "e"), ("X2", "x2", "e"), ("Y2", "y2", "e"), ("W", "t", "e"),
                      ("DP", "dp", "e"), ("T", "name", "s"), ("C", "c", "i"), ("P", "p", "e")]),
    "Origin": ("xy", [("X", "x", "e"), ("Y", "y", "e")]),
}
_DRILLS = ("DrillFront", "DrillLeft", "DrillRight", "DrillTop", "DrillBottom")
_TAGGED = set(_PLAIN) | {"Tool", "Var", "Par", "Com"}


def _walk(cmds: list[XncCommand]):
    for c in cmds:
        yield c
        yield from _walk(c.children)


def needs_flatten(cmds: list[XncCommand]) -> bool:
    """Dasturda formatda teg nomi tavsiflanmagan (yoki oddiy tegga o'tmaydigan) bajariladigan buyruq bormi."""
    for c in cmds:
        if not c.enabled:
            continue                                      # o'chirilgan buyruq (bolalari bilan) bajarilmaydi — tashlanadi
        if c.cmd not in _TAGGED or c.children:
            return True
        if c.cmd == "Groove" and (c.params.get("L") not in (None, "") or "X1" not in c.params and "X" in c.params):
            return True                                   # uzunlik bilan / X-Y yozuvi: x1,y1,x2,y2 ga o'tkazib bo'lmaydi
        if c.cmd == "MillArc3P":
            return True
    return False


def _el(tag: str, **attrs) -> ET.Element:
    e = ET.Element(tag)
    for k, v in attrs.items():
        if v is not None:
            e.set(k.rstrip("_"), v)
    return e


def _set_common(e: ET.Element, c: XncCommand) -> None:
    if c.comment:
        e.set("comment", clean(c.comment))
    if not c.enabled:
        e.set("enable", "false")


def _plain_children(x: XNCParams, code: str, notes: Callable[[str, dict], None]) -> list[ET.Element]:
    out: list[ET.Element] = []
    skipped_com = 0
    for c in x.program:
        p = c.params
        if c.cmd == "Com":
            skipped_com += 1
            continue
        if not c.enabled and c.cmd not in _PLAIN and c.cmd not in ("Tool", "Var", "Par"):
            continue
        if c.cmd == "Tool":
            name = _val(p.get("N", p.get("name", ""))) or ""
            e = _el("tool", name=name, d=_val(p.get("D")) or "0")       # `d` — ifoda (format ruxsat beradi)
            _set_common(e, c)
            out.append(e)
        elif c.cmd in ("Var", "Par"):
            name = _val(p.get("name"))
            if not name:
                continue
            if c.cmd == "Par":                           # kiritiladigan parametr → o'zgaruvchi (kiritilgan / standart qiymat)
                val = x.par_values.get(name, p.get("value", 0))
                if p.get("readonly") not in (None, "", 0, 0.0, "0", "false"):
                    val = p.get("value", 0)
                typ = X.par_type(p.get("type"))
                notes("par", dict(code=code))
                if typ == "string":                      # matn Par (W18): `var type="string"`, qiymat — satr literali ('…')
                    s = X.plain_text(val)
                    lit = "'" + s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r") + "'"
                    e = _el("var", name=name, type=typ, expr=clean(lit))
                else:
                    e = _el("var", name=name, type=typ, expr=_val(val) or "0")
                lab = _val(p.get("label"))
                if lab:
                    e.set("comment", lab)
                if not c.enabled:
                    e.set("enable", "false")
            else:
                e = _el("var", name=name, type=_val(p.get("type")) or "double", expr=_val(p.get("value")) or "0")
                _set_common(e, c)
            out.append(e)
        else:
            tag, spec = _PLAIN[c.cmd]
            e = ET.Element(tag)
            for key, attr, kind in spec:
                raw = p.get(key)
                if raw is None or raw == "":
                    continue
                if kind == "b":
                    v = _bool_val(raw)
                elif kind == "i":
                    v = _int_val(raw)
                else:
                    v = _val(raw)
                if v is not None:
                    e.set(attr, v)
            _set_common(e, c)
            out.append(e)
    if skipped_com:
        notes("com", dict(code=code, n=skipped_com))
    return out


# ───────────────────────── «Yoyilgan» dastur (evaluate natijasi) ─────────────────────────
def _fin(v) -> bool:
    return isinstance(v, (int, float)) and math.isfinite(v)


def _flat_children(x: XNCParams, code: str, notes: Callable[[str, dict], None]) -> list[ET.Element]:
    ops = X.evaluate(x.program, x.length, x.width, x.thickness, X.program_vars(x), x.par_values)
    out: list[ET.Element] = []
    tools: dict[str, float] = {}
    skipped = 0

    def tool(t: str, d) -> str:
        d = float(d) if _fin(d) and d > 0 else 0.0
        name = t or (f"D{num(d)}" if d else "T0")
        if tools.get(name) != d:
            out.append(_el("tool", name=name, d=num(d)))
            tools[name] = d
        return name

    pos: tuple[float, float] | None = None

    def start(o, X0, Y0, c=0, extra=None):
        nonlocal pos
        e = _el("ms", name=tool(o["T"], o.get("D")), x=num(X0), y=num(Y0), dp=num(o["DP"]), c=_int_val(c))
        for k, v in (extra or {}).items():
            e.set(k, v)
        out.append(e)
        pos = (X0, Y0)

    def line(o, X1, Y1):
        nonlocal pos
        out.append(_el("ml", x=num(X1), y=num(Y1), dp=num(o["DP"])))
        pos = (X1, Y1)

    def arc_c(o, X1, Y1, cx, cy, ccw):
        nonlocal pos
        out.append(_el("mac", x=num(X1), y=num(Y1), cx=num(cx), cy=num(cy), dp=num(o["DP"]), dir=boolean(ccw)))
        pos = (X1, Y1)

    for o in ops:
        k = o["kind"]
        if k in _DRILLS:
            if not o.get("inside", True):
                continue                                  # detaldan tashqaridagi teshik bajarilmaydi
            nm = tool(o["T"], o["D"])
            if k == "DrillFront":
                out.append(_el("bf", x=num(o["X"]), y=num(o["Y"]), dp=num(o["DP"]), name=nm))
            else:
                e = _el(_PLAIN[k][0], name=nm, dp=num(o["DP"]), m=boolean(o.get("M")))
                if k in ("DrillLeft", "DrillRight"):
                    e.set("y", num(o["Y"]))
                else:
                    e.set("x", num(o["X"]))
                e.set("z", num(o["Z"]))
                out.append(e)
        elif k == "Groove":
            if not o.get("ok", True):
                skipped += 1
                continue
            out.append(_el("gr", name=tool(o["T"], o.get("D")), x1=num(o["X1"]), y1=num(o["Y1"]), x2=num(o["X2"]),
                           y2=num(o["Y2"]), t=num(o["W"]), dp=num(o["DP"]), c=_int_val(o.get("C", 0))))
        elif k in ("MillStart", "MillLine", "MillArc", "MillArcCenter", "MillArc3P"):
            if not o.get("ok", True):
                skipped += 1
                continue
            if k == "MillStart":
                extra = {}
                if _fin(o.get("SDP")):
                    extra["sdp"] = num(o["SDP"])
                if _fin(o.get("SXY")):
                    extra["sxy"] = num(o["SXY"])
                extra["in"] = _int_val(o.get("IN", 0))
                extra["out"] = _int_val(o.get("OUT", 1))
                start(o, o["X"], o["Y"], o.get("C", 0), extra)
            elif k == "MillLine":
                line(o, o["X"], o["Y"])
            elif k == "MillArc":
                out.append(_el("ma", x=num(o["X"]), y=num(o["Y"]), dp=num(o["DP"]), r=num(o["R"]),
                               dir=_bool_val(o.get("DIR"), "false")))
                pos = (o["X"], o["Y"])
            elif k == "MillArcCenter":
                arc_c(o, o["X"], o["Y"], o["CX"], o["CY"], X._is_ccw(o.get("DIR", "")))
            else:                                         # MillArc3P → markazli yoy (yoki to'g'ri chiziq)
                g = X.arc_through(pos, (o["X2"], o["Y2"]), (o["X"], o["Y"])) if pos is not None else None
                if g is None:
                    line(o, o["X"], o["Y"])
                else:
                    arc_c(o, o["X"], o["Y"], g[3][0], g[3][1], g[2])
        elif k == "MillRect":
            if not o.get("ok", True):
                skipped += 1
                continue
            segs = X.rect_segments(o)
            for s in segs:
                if s[0] == "M":
                    start(o, s[1], s[2], o.get("C", 0), {"in": "0", "out": "1"})
                elif s[0] == "L":
                    line(o, s[1], s[2])
                else:
                    arc_c(o, s[1], s[2], s[3], s[4], s[5])
        elif k == "MillEllipse":
            if not o.get("ok", True):
                skipped += 1
                continue
            pts = X.ellipse_points(o)
            start(o, pts[0][0], pts[0][1], o.get("C", 0), {"in": "0", "out": "1"})
            for q in pts[1:]:
                line(o, q[0], q[1])
    if skipped:
        notes("bad", dict(code=code, n=skipped))
    return out


def program_xml(x: XNCParams, code: str, notes: Callable[[str, dict], None]) -> str:
    """`program` atributi matni. `notes(kod, parametrlar)` — eksport ogohlantirishlari uchun qayta chaqiruv."""
    flat = needs_flatten(x.program)
    if flat:
        notes("flat", dict(code=code))
        kids = _flat_children(x, code, notes)
    else:
        kids = _plain_children(x, code, notes)
    root = ET.Element("program", dx=num(x.length), dy=num(x.width), dz=num(x.thickness))
    root.extend(kids)
    return PROLOG + ET.tostring(root, encoding="unicode").replace(" />", "/>")
