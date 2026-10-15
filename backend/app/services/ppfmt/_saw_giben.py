"""Giben (G57 / GVisionXP / GDrive) va KDT (XML / KS33X / yangi versiya) formatlari uchun umumiy: optimizator kesish
daraxtini (SawNode, list koordinatalarida) «darajali kesimlar» ko'rinishiga keltirish.

Bu formatlarning hammasida kesish rejasi bir xil modelda (docs/mebelix/postprocessors/giben-g57.md §3):
  * karta o'z koordinatasida `dimx × dimy`; 1-daraja kesimlar (polosalar) doim karta Y o'qi bo'ylab ketma-ket,
    keyingi darajalar navbat bilan X, Y, X …;
  * har kesim — «bo'lak o'lchami» + takror soni; o'rni yozilmaydi: `oldingi + o'lcham + propil`;
  * 1- va 2-daraja list chetidan `torsovka + propil` siljib boshlanadi, chuqurroqlari — siljishsiz;
  * farzandsiz bo'lak — tayyor detal (ko'ndalang o'lchami — otasining to'liq o'lchami); chiqindi yozilmaydi.
Shuning uchun: ota bo'lakni to'liq egallamagan detal oraliq bo'lakka o'raladi, o'rtadagi chiqindi tashlab yuboriladi
(keyingi bo'laklar oldinga suriladi — gilyotina kesimida bu joiz), delovoy qoldiq faqat 1-daraja oxirida qoladi.
Modul nomi «_» bilan boshlanadi — `load_all()` uni format sifatida yuklamaydi."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import SawJob, SawMap, SawNode

EPS = 0.01

_TR = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i", "й": "y",
       "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f",
       "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "y", "э": "e", "ю": "yu",
       "я": "ya", "ў": "o", "қ": "q", "ғ": "g", "ҳ": "h"}


def translit(s: str) -> str:
    """Kirill → lotin (namunadagi «Фронтальная» → «Frontalynaya» ga mos); qolgan ASCII bo'lmagan belgilar «?»."""
    out = []
    for ch in s or "":
        lo = ch.lower()
        if lo in _TR:
            t = _TR[lo]
            out.append((t[:1].upper() + t[1:]) if ch != lo else t)
        else:
            out.append(ch if ord(ch) < 128 else "?")
    return "".join(out)


def um(v: float) -> int:
    """mm → mm×1000 (butun)."""
    return int(round(float(v) * 1000))


@dataclass
class GN:
    """Bo'lak: `size` — ota o'qi bo'ylab o'lchami, `rep` — ketma-ket takror, `kids` — ichki kesimlar (bo'sh — detal)."""
    size: float
    rep: int = 1
    uid: int = 0
    kids: list["GN"] = field(default_factory=list)
    lead: float = 0.0            # birinchi ichki kesimdan oldingi siljish (faqat KDT XML `trim` da ifodalanadi)

    def sig(self):
        return (round(self.size, 3), self.uid, round(self.lead, 3), tuple((k.sig(), k.rep) for k in self.kids))


@dataclass
class GRest:
    number: int
    l: float                     # torsovkadan keyingi o'lcham, list uzunligi bo'ylab
    w: float


@dataclass
class GPat:
    map: SawMap
    axis: str                    # 1-daraja o'qi list koordinatasida (x — list uzunligi bo'ylab)
    dimx: float                  # karta ko'ndalang o'lchami (polosa uzunligi)
    dimy: float                  # 1-daraja kesimlar bo'ylab o'lcham
    copies: int
    off1: float                  # 1-daraja boshidagi siljish (torsovka + propil)
    off2: float                  # 2-daraja boshidagi siljish
    kids: list[GN]
    rest: Optional[GRest] = None
    dropped: int = 0             # surilgan joylar soni: o'rtadagi chiqindi yoki bo'lak boshidagi siljish (format
    #                              ularni ifodalamaydi — bo'laklar oldinga suriladi)

    def rest_raw(self, kerf: float) -> float:
        """1-daraja oxirida qolgan joy (list chetigacha, torsovkasiz)."""
        return self.dimy - self.off1 - sum((k.size + kerf) * k.rep for k in self.kids)


def _ext(n: SawNode, a: str) -> float:
    return n.l if a == "x" else n.w


def _start(n: SawNode, a: str) -> float:
    return n.x if a == "x" else n.y


def _oth(a: str) -> str:
    return "y" if a == "x" else "x"


def _has_part(n: SawNode) -> bool:
    return (n.kind == "P" and bool(n.uid)) or any(_has_part(c) for c in n.children)


def _rem(n: SawNode) -> Optional[SawNode]:
    if n.kind == "W" and n.rem:
        return n
    for c in n.children:
        r = _rem(c)
        if r is not None:
            return r
    return None


def merge(nodes: list[GN]) -> list[GN]:
    """Ketma-ket bir xil bo'laklar → bitta yozuv (rep)."""
    out: list[GN] = []
    for n in nodes:
        if out and out[-1].sig() == n.sig():
            out[-1].rep += n.rep
        else:
            out.append(n)
    return out


def pattern(job: SawJob, m: SawMap) -> Optional[GPat]:
    root = m.tree
    if root is None:
        return None
    if root.kind != "C" or not root.children:        # butun listni egallagan bitta bo'lak
        root = SawNode(x=root.x, y=root.y, l=root.l, w=root.w, kind="C", axis="x", children=[root])
    axis = root.axis if root.axis in ("x", "y") else "x"
    oth = _oth(axis)
    L, W = m.sheet_length, m.sheet_width
    pat = GPat(map=m, axis=axis, dimx=W if axis == "x" else L, dimy=L if axis == "x" else W, copies=max(1, m.copies),
               off1=_start(root, axis), off2=_start(root, oth), kids=[])
    rests: list[SawNode] = []

    def conv(n: SawNode, a: str, perp: float, level: int) -> list[GN]:
        o = _oth(a)
        out: list[GN] = []
        seen_waste = False
        for c in n.children:
            if c.kind == "C" and c.children and (c.axis or a) == a:       # bir xil o'qli ichki guruh — yoyiladi
                out += conv(c, a, perp, level)
                continue
            size = _ext(c, a)
            if c.kind == "P" and c.uid:
                pat.dropped += seen_waste
                if abs(_ext(c, o) - perp) > EPS:
                    out.append(GN(size, kids=[GN(_ext(c, o), uid=c.uid)]))
                else:
                    out.append(GN(size, uid=c.uid))
            elif c.kind == "C" and c.children and _has_part(c):
                pat.dropped += seen_waste
                lead = max(0.0, _start(c.children[0], o) - _start(c, o)) if level >= 2 else 0.0
                out.append(GN(size, kids=merge(conv(c, o, size, level + 1)), lead=lead))
            else:
                seen_waste = True
                r = _rem(c)
                if r is not None and level == 1:
                    rests.append(r)
        return out

    pat.kids = merge(conv(root, axis, pat.dimx, 1))
    if rests:
        r = max(rests, key=lambda x: x.l * x.w)
        pat.rest = GRest(number=r.rem, l=r.l, w=r.w)
    return pat


def patterns(job: SawJob) -> list[GPat]:
    return [p for p in (pattern(job, m) for m in job.maps) if p is not None and p.kids]


def depth(nodes: list[GN]) -> int:
    return 0 if not nodes else 1 + max(depth(n.kids) for n in nodes)


def layout(pat: GPat, kerf: float) -> list[tuple[int, float, float, float, float]]:
    """Barglar (detal uid, x0, y0, x1, y1) karta koordinatasida — format qoidasi bo'yicha (stanok shunday kesadi)."""
    out: list[tuple[int, float, float, float, float]] = []

    def walk(nodes: list[GN], lvl: int, x0: float, y0: float, w: float, h: float):
        along_y = lvl % 2 == 1
        pos = (y0 if along_y else x0) + (pat.off1 if lvl == 1 else pat.off2 if lvl == 2 else 0.0)
        for c in nodes:
            for _ in range(c.rep):
                if along_y:
                    cx, cy, cw, ch = x0, pos, w, c.size
                else:
                    cx, cy, cw, ch = pos, y0, c.size, h
                if c.kids:
                    walk(c.kids, lvl + 1, cx, cy, cw, ch)
                else:
                    out.append((c.uid, cx, cy, cx + cw, cy + ch))
                pos += c.size + kerf

    walk(pat.kids, 1, 0.0, 0.0, pat.dimx, pat.dimy)
    return out


def leaf_counts(nodes: list[GN], mult: int = 1, acc: Optional[dict] = None) -> dict[int, int]:
    """Bitta listdagi detallar soni: uid → dona."""
    acc = {} if acc is None else acc
    for n in nodes:
        if n.kids:
            leaf_counts(n.kids, mult * n.rep, acc)
        else:
            acc[n.uid] = acc.get(n.uid, 0) + mult * n.rep
    return acc


def business_area(job: SawJob) -> float:
    """Delovoy qoldiqlar maydoni, m² (karta nusxalari bilan)."""
    a = 0.0
    for m in job.maps:
        for o in m.offcuts:
            if o.get("business"):
                a += float(o.get("length", 0)) * float(o.get("width", 0)) * max(1, m.copies) / 1e6
    return a
