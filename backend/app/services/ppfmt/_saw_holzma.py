"""Holzma formatlari (.LC4, .SPL) uchun umumiy: optimizator kesish daraxtini (SawNode, list koordinatalarida)
«darajali» kesish rejasiga aylantirish.

Natija — `HPat`: karta burilgani (rot), 1-daraja bo'laklar ro'yxati va trimlar. Har bo'lak `HNode`:
  * strip — oraliq bo'lak (keyin yana kesiladi), `size` — ota o'qi bo'ylab o'lchami, `kids` — ichki bo'laklar;
  * part  — tayyor detal (uid, list bo'yicha burilgan-burilmagani), `size` — ota o'qi bo'ylab;
  * rest  — biznes-qoldiq (rem raqami), `size` — 1-darajada list chetigacha xom o'lcham;
  * waste — o'rtadagi chiqindi bo'lagi (keyingi bo'laklar joyi siljimasligi uchun; oxirgi chiqindi yozilmaydi).
Daraja yo'nalishlari navbatlashadi: 1-daraja — ildiz o'qi (rot=False → list uzunligi X, rot=True → eni Y).
Detal bargi doim «barg size × ota size» bo'lishi uchun ota bo'lakni to'liq egallamagan detal (masalan 1-darajadagi
detal) qo'shimcha oraliq bo'lak ichiga o'raladi."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import SawJob, SawMap, SawNode

EPS = 0.01


@dataclass
class HNode:
    kind: str                    # strip | part | rest | waste
    size: float
    uid: int = 0
    rot: bool = False            # detal list bo'yicha burilgan (uzunligi Y o'qi bo'ylab)
    rem: int = 0
    kids: list["HNode"] = field(default_factory=list)
    src: Optional[SawNode] = None

    def sig(self):
        """Ketma-ket bir xil bo'laklarni (takror, rep) birlashtirish uchun imzo."""
        return (self.kind, round(self.size, 3), self.uid, self.rot, self.rem, tuple(k.sig() for k in self.kids))


@dataclass
class HPat:
    rot: bool                    # True — 1-daraja list eni (Y) bo'ylab
    sheet_l: float
    sheet_w: float
    copies: int
    trim1: float                 # ildiz boshidagi trim (1-daraja o'qi bo'ylab)
    trim2: float                 # 1-daraja bo'laklar boshidagi trim (ikkinchi o'q bo'ylab)
    kids: list[HNode]
    map: SawMap


def _ext(n: SawNode, axis: str) -> float:
    return n.l if axis == "x" else n.w


def _start(n: SawNode, axis: str) -> float:
    return n.x if axis == "x" else n.y


def _other(axis: str) -> str:
    return "y" if axis == "x" else "x"


def _has_part(n: SawNode) -> bool:
    if n.kind == "P" and n.uid:
        return True
    return any(_has_part(c) for c in n.children)


def _first_rem(n: SawNode) -> int:
    if n.kind == "W" and n.rem:
        return n.rem
    for c in n.children:
        r = _first_rem(c)
        if r:
            return r
    return 0


def _seq(n: SawNode, axis: str) -> list[SawNode]:
    """`n` ning `axis` bo'ylab ketma-ket bolalari: bir xil o'qli ichki guruhlar va «to'liq egallagan bitta bola»
    o'ramlari ochib yuboriladi."""
    out: list[SawNode] = []
    for c in n.children:
        if c.kind == "C" and c.children and (c.axis or axis) == axis:
            out.extend(_seq(c, axis))
            continue
        if c.kind == "C" and c.children:
            real = [k for k in c.children if not (k.kind == "W" and not k.rem)]
            if len(real) == 1 and abs(_ext(real[0], c.axis) - _ext(c, c.axis)) < EPS:
                g = real[0]
                if g.kind == "C" and g.children and (g.axis or axis) == axis:
                    out.extend(_seq(g, axis))
                    continue
                if g.kind == "P":
                    out.append(g)
                    continue
        out.append(c)
    return out


def part_rot(job: SawJob, n: SawNode) -> bool:
    """Detal list bo'yicha burilganmi (uzunligi Y o'qi bo'ylab) — geometriyadan; kvadrat detalda daraxt belgisi."""
    p = job.part(n.uid)
    if p is None:
        return bool(n.rotated)
    a = abs(n.l - p.length) < 0.51 and abs(n.w - p.width) < 0.51
    b = abs(n.l - p.width) < 0.51 and abs(n.w - p.length) < 0.51
    if a and not b:
        return False
    if b and not a:
        return True
    return bool(n.rotated)


def _conv(job: SawJob, kids: list[SawNode], axis: str, perp: float, level: int, sheet_ext: float) -> list[HNode]:
    """`kids` (axis bo'ylab) → HNode ro'yxati. perp — ota bo'lakning ikkinchi o'q bo'yicha o'lchami (detal
    shu o'lchamga teng bo'lmasa o'raladi)."""
    out: list[HNode] = []
    oth = _other(axis)
    for c in kids:
        size = _ext(c, axis)
        if c.kind == "P" and c.uid:
            pn = HNode("part", size, uid=c.uid, rot=part_rot(job, c), src=c)
            if abs(_ext(c, oth) - perp) > EPS:
                out.append(HNode("strip", size, kids=[HNode("part", _ext(c, oth), uid=c.uid, rot=pn.rot, src=c)],
                                 src=c))
            else:
                out.append(pn)
        elif c.kind == "C" and c.children and _has_part(c):
            sub = _conv(job, _seq(c, oth), oth, size, level + 1, sheet_ext)
            out.append(HNode("strip", size, kids=sub, src=c))
        else:
            rem = _first_rem(c)
            if rem:
                raw = (sheet_ext - _start(c, axis)) if level == 1 else size
                out.append(HNode("rest", raw, rem=rem, src=c))
            else:
                out.append(HNode("waste", size, src=c))
    while out and out[-1].kind == "waste":          # oxirgi chiqindi yozilmaydi (qolgan joy)
        out.pop()
    return out


def pattern(job: SawJob, m: SawMap) -> Optional[HPat]:
    root = m.tree
    if root is None:
        return None
    if root.kind != "C":                            # butun listni egallagan bitta detal / bo'lak
        root = SawNode(x=root.x, y=root.y, l=root.l, w=root.w, kind="C", axis="x", children=[root])
    axis = root.axis or "x"
    rot = axis == "y"
    L, W = m.sheet_length, m.sheet_width
    ext1 = W if rot else L
    oth = _other(axis)
    kerf = job.kerf
    s1, s2 = _start(root, axis), _start(root, oth)
    trim1 = max(s1 - kerf, 0.0) if s1 > EPS else -1.0      # -1 — trim yo'q
    trim2 = max(s2 - kerf, 0.0) if s2 > EPS else -1.0
    kids = _conv(job, _seq(root, axis), axis, W if not rot else L, 1, ext1)
    return HPat(rot=rot, sheet_l=L, sheet_w=W, copies=max(1, m.copies), trim1=trim1, trim2=trim2, kids=kids, map=m)


def merge_reps(nodes: list[HNode]) -> list[tuple[HNode, int]]:
    """Ketma-ket bir xil bo'laklar → (bo'lak, takror soni)."""
    out: list[tuple[HNode, int]] = []
    for n in nodes:
        if out and out[-1][0].kind != "rest" and out[-1][0].sig() == n.sig():
            out[-1] = (out[-1][0], out[-1][1] + 1)
        else:
            out.append((n, 1))
    return out


def depth(nodes: list[HNode]) -> int:
    return 0 if not nodes else 1 + max(depth(n.kids) for n in nodes)


def part_area(job: SawJob, nodes: list[HNode], parent: float) -> float:
    """Bitta listdagi detallar maydoni (mm²) — barg size × ota size."""
    a = 0.0
    for n in nodes:
        if n.kind == "part":
            a += n.size * parent
        a += part_area(job, n.kids, n.size)
    return a
