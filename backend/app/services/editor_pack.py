"""Kroy tahriri: kartani burchakka zichlash va «Развернуть резы» (detallar joyini saqlab kesish tartibini almashtirish).

Onlayn tizimda tekshirilgan xatti-harakat (2026-10-21, «test uchun» papkasidagi sinov loyihasi):
  • detal / polosa o'chirilganda butun karta zichlanadi: qolgan detallar chap-yuqori burchakka suriladi, polosa eng katta
    qolgan detalgacha qisqaradi, bo'shagan polosa yo'qoladi va keyingilari ko'tariladi; «Расширить полосу» bilan
    kengaytirilgan polosa ham qaytadi;
  • «Развернуть резы»: hech narsa tanlanmasa — butun list, polosa tanlansa — o'sha polosa; detallar joyida qoladi,
    birinchi kesish o'qi almashadi (gorizontal polosalar ↔ vertikal ustunlar), qayta bosilsa — qaytadi.
MX qo'shimchasi (foydalanuvchi talabi): zichlash burchagi — umumiy sozlama («app».edit_pack_corner) yoki kartaning
o'zi (`CutMap.pack_corner`): LT — chap-yuqori (standart, onlayn tizimdagidek), RT, LB, RB. Tanlangan burchak bo'sh joyga
detal qo'yishda ham ishlatiladi (`editor._place_at`, `editor._relayout`).
"""
from __future__ import annotations

import copy
from contextvars import ContextVar
from typing import Optional

from .optimizer import EPS, _depth, _extent, _N, _normalize, _other

TOL = 0.01
CORNERS = ("LT", "RT", "LB", "RB")
# joriy amal uchun zichlash yo'nalishi: (x bo'yicha oxiriga, y bo'yicha oxiriga) — editor.apply o'rnatadi
REV: ContextVar[tuple[bool, bool]] = ContextVar("mx_pack_rev", default=(False, False))
# joriy amal uchun «Минимальная обрезка»: toraytirish / zichlashda ichki qirindi 0 yoki shundan keng bo'lishi shart
MIN_TRIM: ContextVar[float] = ContextVar("mx_pack_min_trim", default=0.0)


def corner_rev(corner: Optional[str]) -> tuple[bool, bool]:
    c = corner if corner in CORNERS else "LT"
    return c in ("RT", "RB"), c in ("LB", "RB")


def rev(ax: str) -> bool:
    rx, ry = REV.get()
    return rx if ax == "x" else ry


def _kf(n: _N, kerf: float) -> float:
    return n.gk if n.gk is not None else kerf


def has_parts(n: _N) -> bool:
    return n.kind == "P" or (n.kind == "C" and any(has_parts(c) for c in n.children))


def need(n: _N, ax: str, kerf: float) -> float:
    """Tugunning `ax` o'qi bo'yicha eng kichik o'lchami (bo'sh joylarsiz, detallar zich turganda)."""
    if n.kind == "P":
        return _extent(n, ax)
    if n.kind != "C":
        return 0.0
    body = [c for c in n.children if has_parts(c)]
    if not body:
        return 0.0
    if n.axis == ax:
        return sum(need(c, ax, kerf) for c in body) + _kf(n, kerf) * (len(body) - 1)
    sizes = [need(c, ax, kerf) for c in body]
    m = max(sizes)
    mt = MIN_TRIM.get()
    if mt <= EPS:
        return m
    # ko'ndalang: eng uzun bolagacha qisqarganda boshqa bolalar ortida 0 < qirindi < «Минимальная обрезка» qolmasin
    # (xodim loyihasi «1275»: blok 2304 gacha qisqarib, soklar ortida 1 mm qolardi) — eng kichik mos o'lcham, joriydan oshmaydi
    cur = _extent(n, ax)
    for cand in sorted({m, *(c + mt for c in sizes if c + mt > m)}):
        if cand > cur + EPS:
            break
        if all(cand - c <= EPS or cand - c >= mt - EPS for c in sizes):
            return cand
    return max(m, cur)


def _w(ax: str, a0: float, a_len: float, b0: float, b_len: float) -> _N:
    x, y, l, w = (a0, b0, a_len, b_len) if ax == "x" else (b0, a0, b_len, a_len)
    return _N(x, y, l, w, 0, "W")


def lay(n: _N, x: float, y: float, l: float, w: float, kerf: float) -> _N:
    """Tugunni (x, y, l, w) hududiga zich joylaydi: bolalar o'z o'qi bo'yicha burchak tomoniga suriladi, har biri
    eng kichik o'lchamigacha qisqaradi, qolgani bitta bo'sh joy. Detal hududdan kichik bo'lsa — kesish tuguniga o'raladi."""
    if n.kind == "P":
        if abs(n.l - l) <= TOL and abs(n.w - w) <= TOL:
            n.x, n.y = x, y
            return n
        wrap = _N(x, y, l, w, n.level, "C", axis="x" if abs(n.l - l) > TOL else "y", children=[n])
        return lay(wrap, x, y, l, w, kerf)
    n.x, n.y, n.l, n.w = x, y, l, w
    if n.kind != "C":
        return n
    ax = n.axis
    k = _kf(n, kerf)
    body = [c for c in n.children if has_parts(c)]
    sizes = [need(c, ax, kerf) for c in body]
    total = sum(sizes) + k * (len(body) - 1) if body else 0.0
    a0, ext = (x, l) if ax == "x" else (y, w)
    b0, bext = (y, w) if ax == "x" else (x, l)
    kids: list[_N] = []
    pos = a0
    if body and rev(ax):
        pos = a0 + ext - total
        lead = pos - k - a0
        if lead > EPS:
            kids.append(_w(ax, a0, lead, b0, bext))
        else:
            pos = a0 + max(0.0, ext - total)
    for c, s in zip(body, sizes):
        cx, cy, cl, cw = (pos, b0, s, bext) if ax == "x" else (b0, pos, bext, s)
        kids.append(lay(c, cx, cy, cl, cw, kerf))
        pos += s + k
    if not body:
        kids.append(_w(ax, a0, ext, b0, bext))
    elif not rev(ax):
        rest = a0 + ext - pos
        if rest > EPS:
            kids.append(_w(ax, pos, rest, b0, bext))
    n.children = kids
    return n


def compact(root: _N, kerf: float) -> _N:
    """Butun kartani burchakka zichlash (o'chirishdan keyin, onlayn tizimdagidek)."""
    return lay(root, root.x, root.y, root.l, root.w, kerf)


# ───────────────────────── «Развернуть резы» ─────────────────────────
class NoRecut(Exception):
    """Detallar joyini saqlab boshqa o'qda kesib bo'lmaydi (eski usul — qayta joylash — ishlatiladi)."""


def _span(p: _N, ax: str) -> tuple[float, float]:
    s = p.x if ax == "x" else p.y
    return s, s + _extent(p, ax)


def _split(parts: list[_N], ax: str, kerf: float) -> list[list[_N]]:
    """`ax` o'qi bo'ylab kesib ajratiladigan guruhlar: oralig'ida kamida propil kengligi bo'sh joy bor."""
    out: list[list[_N]] = []
    end = None
    for p in sorted(parts, key=lambda q: _span(q, ax)[0]):
        s, e = _span(p, ax)
        if end is None or s - end < kerf - TOL:
            if end is None:
                out.append([])
            out[-1].append(p)
            end = e if end is None else max(end, e)
        else:
            out.append([p])
            end = e
    return out


def _span_of(parts: list[_N], ax: str) -> tuple[float, float]:
    return min(_span(p, ax)[0] for p in parts), max(_span(p, ax)[1] for p in parts)


def _build(parts: list[_N], x: float, y: float, l: float, w: float, ax: str, kerf: float, depth: int = 0,
           switched: bool = False) -> _N:
    """Detallarning ANIQ joylaridan kesish daraxti: `ax` o'qi bo'ylab kesib ajraladigan guruhlar — bolalar (orasidagi bo'sh
    joylar — chiqindi), har guruh ichida — ko'ndalang o'q. Detallar siljimaydi (onlayn tizimdagidek)."""
    if depth > 60:
        raise NoRecut
    if len(parts) == 1:
        p = parts[0]
        if abs(p.l - l) <= TOL and abs(p.w - w) <= TOL:
            p.x, p.y = x, y
            return p
    a0, ext = (x, l) if ax == "x" else (y, w)
    a1 = a0 + ext
    groups = _split(parts, ax, kerf)
    if len(groups) == 1:
        lo, hi = _span_of(parts, ax)
        if lo <= a0 + TOL and hi >= a1 - TOL:                # bu o'qda kesib bo'lmaydi — ko'ndalang o'qqa
            if switched:
                raise NoRecut
            return _build(parts, x, y, l, w, _other(ax), kerf, depth + 1, True)
    kids: list[_N] = []
    cur = a0

    def strip(s0: float, s1: float) -> tuple[float, float, float, float]:
        return (s0, y, s1 - s0, w) if ax == "x" else (x, s0, l, s1 - s0)
    for g in groups:
        lo, hi = _span_of(g, ax)
        if lo - kerf - cur > EPS:                            # oldingi kesim va guruh orasida chiqindi
            kids.append(_N(*strip(cur, lo - kerf), 0, "W"))
            s0 = lo
        else:
            s0 = cur if lo - cur < kerf - TOL else lo        # propildan tor oraliq — bo'lak boshi kesim chizig'ida
            s0 = min(s0, lo)
        kids.append(_build(g, *strip(s0, hi), _other(ax), kerf, depth + 1))
        cur = hi + kerf
    if a1 - cur > EPS:
        kids.append(_N(*strip(cur, a1), 0, "W"))
    return _N(x, y, l, w, 0, "C", axis=ax, children=kids)


def recut(node: _N, kerf: float) -> _N:
    """Tugun (polosa yoki butun list) ichidagi detallar joyini saqlab, birinchi kesish o'qini almashtiradi."""
    if node.kind != "C":
        raise NoRecut
    parts = [lf for lf in node.leaves() if lf.kind == "P"]
    if not parts:
        raise NoRecut

    def grouped(n: _N) -> bool:
        return n.kind == "C" and (n.gk is not None or any(grouped(c) for c in n.children))
    if grouped(node):                       # blok (guruh propili) — eski usul
        raise NoRecut
    ax = _other(node.axis)
    lo, hi = _span_of(parts, ax)
    a0, ext = (node.x, node.l) if ax == "x" else (node.y, node.w)
    if len(_split(parts, ax, kerf)) == 1 and lo <= a0 + TOL and hi >= a0 + ext - TOL:
        raise NoRecut                       # ko'ndalang kesib bo'lmaydi — tuzilma o'zgarmaydi
    pos = {id(p): (p.x, p.y) for p in parts}
    new = _build(parts, node.x, node.y, node.l, node.w, ax, kerf, switched=True)
    if new.kind != "C" or new.axis != ax or any(abs(p.x - pos[id(p)][0]) > TOL or abs(p.y - pos[id(p)][1]) > TOL for p in parts):
        raise NoRecut
    new.level = node.level
    return new


def rotate_cuts(root: _N, path: list[int], kerf: float, max_depth: int) -> Optional[_N]:
    """`path` dagi tugunni (bo'sh — butun list) joylarni saqlab qayta kesadi. Imkonsiz yoki daraxt chuqurligi chegaradan
    oshsa — None (chaqiruvchi eski usulga o'tadi)."""
    work = copy.deepcopy(root)
    parent, node = None, work
    for i in path:
        if node.kind != "C" or not (0 <= i < len(node.children)):
            return None
        parent, node = node, node.children[i]
    try:
        new = recut(node, kerf)
    except NoRecut:
        return None
    if parent is None:
        work = new
    else:
        parent.children[parent.children.index(node)] = new
    probe = _normalize(copy.deepcopy(work))
    if probe is None or _depth(probe) > max_depth:
        return None
    return work
