"""Gilyotina daraxtini stanok formatlari uchun «polosa» ko'rinishiga keltirish (Nanxing .CUT/.ncp, AES .ss, FastPanel .ocm).

Bu formatlarda daraxt qat'iy qoidaga bo'ysunadi (korxona namunalaridan, docs/mebelix/postprocessors/nanxing-nxcutsaw.md §2.5):
  * har tugun bolalari bitta o'q bo'ylab ketma-ket (propil bilan), har chuqurlashganda o'q almashadi;
  * bola ota-onaning perpendikulyar o'lchamini to'liq egallaydi — kichik detal alohida konteynerga o'raladi;
  * 1-daraja bo'laklar (polosalar) doim konteyner (ichida kamida bitta bo'lak);
  * chiqindi yozilmaydi, delovoy qoldiq — alohida barg (R).
Modul nomi «_» bilan boshlanadi — `load_all()` uni format sifatida yuklamaydi.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator, Optional

from . import SawJob, SawMap, SawNode

EPS = 0.01
PROGRAM = "MebeliX Kroy"          # yaratuvchi dastur maydonlari uchun


def now() -> datetime:
    """Fayl yaratilish vaqti (sinovlarda almashtiriladi)."""
    return datetime.now()


@dataclass
class Piece:
    """Polosa daraxti bo'lagi (list koordinatalarida, mm). kind: C — konteyner (bolalari `axis` bo'ylab), P — detal,
    R — delovoy qoldiq. `cr` — .CUT ko'rinishidagi to'rtburchak (1-daraja polosa perpendikulyar bo'yicha butun list)."""
    x: float
    y: float
    l: float
    w: float
    kind: str
    axis: str = ""
    uid: int = 0
    rotated: bool = False
    rem: int = 0
    level: int = 0
    children: list["Piece"] = field(default_factory=list)
    cr: tuple = (0.0, 0.0, 0.0, 0.0)
    k: int = 0                    # qoldiq raqami (material bo'yicha, 1 dan) — R uchun

    def pos(self, a: str) -> float:
        return self.x if a == "x" else self.y

    def size(self, a: str) -> float:
        return self.l if a == "x" else self.w

    def set_span(self, a: str, start: float, size: float) -> None:
        if a == "x":
            self.x, self.l = start, size
        else:
            self.y, self.w = start, size


def other(a: str) -> str:
    return "y" if a == "x" else "x"


# ───────────────────────── SawNode → Piece ─────────────────────────
def _build(n: SawNode) -> Optional[Piece]:
    if n.kind == "P":
        return Piece(n.x, n.y, n.l, n.w, "P", uid=n.uid, rotated=bool(n.rotated))
    if n.kind == "W" or not n.children and n.kind != "C":
        return Piece(n.x, n.y, n.l, n.w, "R", rem=n.rem) if n.rem else None
    ax = n.axis if n.axis in ("x", "y") else _guess_axis(n)
    p = Piece(n.x, n.y, n.l, n.w, "C", axis=ax)
    for c in n.children:
        b = _build(c)
        if b is None:
            continue
        if b.kind == "C" and (b.axis == ax or not b.children):
            p.children.extend(b.children)        # bir xil o'qli ichki konteyner — ota-onaga qo'shiladi
        else:
            p.children.append(b)
    return p


def _guess_axis(n: SawNode) -> str:
    """O'qi berilmagan konteyner: bolalar qaysi o'q bo'ylab tarqalgan bo'lsa shu."""
    xs = {round(c.x, 2) for c in n.children}
    ys = {round(c.y, 2) for c in n.children}
    return "x" if len(xs) >= len(ys) else "y"


def _fix(p: Piece, level: int, wrap_all: bool) -> None:
    """Bolalarni o'q bo'yicha tartiblash, perpendikulyar o'lchamni ota-onaga tenglash (kichik detal — konteynerga)."""
    p.level = level
    if p.kind != "C":
        return
    a, b = p.axis, other(p.axis)
    p.children.sort(key=lambda c: (c.pos(a), c.kind == "R"))
    out: list[Piece] = []
    for c in p.children:
        if c.kind == "P" and (wrap_all or c.size(b) < p.size(b) - EPS or abs(c.pos(b) - p.pos(b)) > EPS):
            w = Piece(c.x, c.y, c.l, c.w, "C", axis=b, children=[c])
            w.set_span(b, p.pos(b), p.size(b))
            c = w
        elif c.kind == "C":
            if c.axis == a:                          # (flatten'dan keyin bo'lmasligi kerak) — o'rab qo'yiladi
                w = Piece(c.x, c.y, c.l, c.w, "C", axis=b, children=[c])
                w.set_span(b, p.pos(b), p.size(b))
                c = w
            else:
                c.set_span(b, p.pos(b), p.size(b))   # bo'lak ota-onaning to'liq perpendikulyar o'lchamida kesiladi
        out.append(c)
    p.children = out
    for c in p.children:
        _fix(c, level + 1, False)


def strip_tree(root: Optional[SawNode]) -> Optional[Piece]:
    """SawMap.tree → Piece ildizi (ildiz = list zonasi torsovkadan keyin, level 0)."""
    if root is None:
        return None
    p = _build(root)
    if p is None:
        return None
    if p.kind != "C":                                  # butun zona bitta detal — polosa ichiga
        p = Piece(p.x, p.y, p.l, p.w, "C", axis="x", children=[p])
    if not p.children:
        return p
    _fix(p, 0, True)
    return p


def walk(p: Optional[Piece]) -> Iterator[Piece]:
    if p is None:
        return
    yield p
    for c in p.children:
        yield from walk(c)


def sig(p: Piece) -> tuple:
    """Bir xillik kaliti (ketma-ket bir xil bo'laklar: .CUT `Grouped`, .ncp yozuvlari, .ocm `Quantity`)."""
    return (p.kind, round(p.l, 2), round(p.w, 2), p.uid if p.kind == "P" else 0, p.rotated if p.kind == "P" else False,
            p.axis, tuple(sig(c) for c in p.children))


def runs(children: list[Piece]) -> list[list[Piece]]:
    """Ketma-ket bir xil (sig) bo'laklar guruhlari; R (qoldiq) hech qachon guruhlanmaydi."""
    out: list[list[Piece]] = []
    for c in children:
        if out and c.kind != "R" and out[-1][-1].kind != "R" and sig(out[-1][-1]) == sig(c):
            out[-1].append(c)
        else:
            out.append([c])
    return out


# ───────────────────────── karta ma'lumotlari ─────────────────────────
@dataclass
class MapInfo:
    m: SawMap
    root: Optional[Piece]
    L: float                     # list o'lchami
    W: float
    tx: float                    # torsovka (zona boshi) X va Y bo'yicha
    ty: float

    @property
    def axis(self) -> str:
        return self.root.axis if self.root is not None and self.root.axis else "x"


def default_trim(job: SawJob, m: Optional[SawMap] = None) -> tuple[float, float]:
    """Zona boshi: torsovka + propil (torsovka propilni o'z ichiga olmasa) — optimizator zonasi bilan bir xil."""
    cut = getattr(job.op, "cs_cut", None)
    incl = bool(getattr(cut, "trim_includes_kerf", False)) if cut is not None else False
    tl = m.trim_length if m is not None else job.trim_length
    tw = m.trim_width if m is not None else job.trim_width
    k = 0.0 if incl else job.kerf
    return (tl + k if tl > 0 else 0.0), (tw + k if tw > 0 else 0.0)


def map_infos(job: SawJob) -> list[MapInfo]:
    out = []
    for m in job.maps:
        r = strip_tree(m.tree)
        if r is not None:
            tx, ty = r.x, r.y
        else:
            tx, ty = default_trim(job, m)
        mi = MapInfo(m, r, m.sheet_length, m.sheet_width, tx, ty)
        if r is not None:
            _cut_rects(mi)
        out.append(mi)
    _number_spares(out)
    return out


def _cut_rects(mi: MapInfo) -> None:
    """.CUT ko'rinishidagi to'rtburchaklar: 1-daraja polosa perpendikulyar bo'yicha butun list (0…L/W);
    qoldiq — ota-onaning (.CUT) oxirigacha cho'ziladi."""
    root = mi.root
    root.cr = (0.0, 0.0, mi.L, mi.W)
    full = {"x": (0.0, mi.L), "y": (0.0, mi.W)}

    def rect(p: Piece, parent: Piece) -> None:
        a = parent.axis
        b = other(a)
        px, py, pl, pw = parent.cr
        pr = {"x": (px, pl), "y": (py, pw)}
        if p.kind == "R":
            end = pr[a][0] + pr[a][1]
            span = {a: (p.pos(a), end - p.pos(a)), b: pr[b]}
        elif parent is root:
            span = {a: (p.pos(a), p.size(a)), b: full[b]}
        else:
            span = {"x": (p.x, p.l), "y": (p.y, p.w)}
        p.cr = (span["x"][0], span["y"][0], span["x"][1], span["y"][1])
        for c in p.children:
            rect(c, p)

    for c in root.children:
        rect(c, root)


def _number_spares(infos: list[MapInfo]) -> None:
    """Delovoy qoldiqlar: .CUT xom o'lchami bo'yicha guruh, birinchi uchrash tartibida raqam (1 dan)."""
    keys: dict[tuple, int] = {}
    for mi in infos:
        for p in walk(mi.root):
            if p.kind == "R":
                key = (round(p.cr[2], 2), round(p.cr[3], 2))
                if key not in keys:
                    keys[key] = len(keys) + 1
                p.k = keys[key]


def spares(infos: list[MapInfo]) -> list[tuple[float, float, int]]:
    """[(X, Y, jami soni)] — `k` tartibida."""
    acc: dict[int, list] = {}
    for mi in infos:
        for p in walk(mi.root):
            if p.kind == "R":
                e = acc.setdefault(p.k, [p.cr[2], p.cr[3], 0])
                e[2] += mi.m.copies
    return [tuple(acc[k]) for k in sorted(acc)]


# ───────────────────────── umumiy matn yordamchilari ─────────────────────────
def file_stem(job: SawJob) -> str:
    """`<loyiha>_<material>`: bo'sh joy va qavslar ketma-ketligi → «_» (oxirgi «_» ham saqlanadi — namunalardagi kabi)."""
    order = (job.order or "").strip()
    pn = (job.project_name or "").strip()
    if order and order != "0" and not pn.startswith(order):
        pn = f"{order} {pn}" if pn else order
    s = f"{pn}_{job.material_name}" if pn else (job.material_name or "kroy")
    s = re.sub(r'[\\/:*?"<>|\r\n\t]+', "", s)
    s = re.sub(r"[\s()]+", "_", s)
    return s[:150] or "kroy"


def project_title(job: SawJob) -> str:
    order = (job.order or "").strip()
    pn = (job.project_name or "").strip()
    if order and order != "0" and not pn.startswith(order):
        pn = f"{order} {pn}" if pn else order
    return pn


def edge_text(e: Optional[dict]) -> str:
    """Kromka: `(A) 1-19 dub votan` (EL belgisi + kromka nomi); yo'q bo'lsa bo'sh."""
    if not e:
        return ""
    sym = (e.get("symbol") or "").strip()
    nm = (e.get("name") or "").strip()
    return f"({sym}) {nm}" if sym else nm


def can_turn(job: SawJob, part) -> bool:
    cut = getattr(job.op, "cs_cut", None)
    use_grain = bool(getattr(cut, "use_grain", True)) if cut is not None else True
    return not (use_grain and part.grain)


def part_groove(job: SawJob, uid: int) -> bool:
    """Detalning XNC dasturlarida paz (Groove) bormi."""
    from ...models import OpType
    op_part = next((p for p in job.op.parts if p.uid == uid), None)
    if op_part is None:
        return False
    xnc = {o.id: o for o in job.project.operations if o.type == OpType.XNC}
    for xid in op_part.xnc_op_ids:
        xo = xnc.get(xid)
        if not xo or not xo.xnc:
            continue
        stack = list(xo.xnc.program)
        while stack:
            c = stack.pop()
            if not c.enabled:
                continue
            if str(getattr(c.cmd, "value", c.cmd)).lower().startswith("groove"):
                return True
            stack.extend(c.children)
    return False
