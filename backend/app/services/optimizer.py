"""MebeliX Kroy — gilyotinali (guillotine) listli kroy optimizatori.

Mustaqil yozilgan algoritm (GibLab kodidan foydalanilmagan):
  * 3 bosqichli gilyotina: list → polosalar (C1) → ustunlar (C2) → detallar (P3)
  * propil (arra qalinligi), torsovka, tekstura (aylantirmaslik)
  * bir nechta start strategiyasi (saralash × birinchi kesish yo'nalishi),
    eng yaxshi natija tanlanadi
  * qoldiq (деловой остаток) va chiqindini ajratish
  * bir xil kartalarni birlashtirish (C: n)
  * kesish buyruqlari jadvali (T/C/P/W)

Koordinatalar: X — list uzunligi bo'ylab, Y — list eni bo'ylab, (0,0) chap-yuqori.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ..models import (CSCutParams, CSMaterialParams, CutCommand, CutMap,
                      CuttingResult, FirstCutDir, Offcut, Placement, StockSheet,
                      StripSort)


# ───────────────────────── Ichki tuzilmalar ─────────────────────────
@dataclass
class Item:
    part_id: str
    uid: int
    l: float            # X bo'yicha (aylantirilmagan)
    w: float            # Y bo'yicha
    can_rotate: bool

    def orientations(self) -> list[tuple[float, float, bool]]:
        o = [(self.l, self.w, False)]
        if self.can_rotate and self.l != self.w:
            o.append((self.w, self.l, True))
        return o

    @property
    def area(self) -> float:
        return self.l * self.w


@dataclass
class _Piece:
    item: Item
    x: float; y: float; l: float; w: float; rotated: bool


@dataclass
class _Column:
    x: float; width: float
    pieces: list[_Piece] = field(default_factory=list)


@dataclass
class _Strip:
    y: float; height: float
    columns: list[_Column] = field(default_factory=list)


@dataclass
class _SheetLayout:
    stock: StockSheet
    L: float; W: float              # to'liq list (transpozitsiyadan keyin)
    ox: float; oy: float            # foydali zona boshlanishi
    UL: float; UW: float            # foydali zona o'lchami
    transposed: bool
    strips: list[_Strip] = field(default_factory=list)

    @property
    def pieces(self) -> list[_Piece]:
        return [p for s in self.strips for c in s.columns for p in c.pieces]


# ───────────────────────── Polosa to'ldirish ─────────────────────────
def _fill_strip(h: float, UL: float, pool: list[Item], kerf: float,
                complex_strips: bool, types_left: int | None,
                used_types: set[str], max_strip_len: float) -> tuple[list[_Column], float]:
    """Balandligi h bo'lgan polosani to'ldiradi. (ustunlar, detal maydoni) qaytaradi.
    pool dan ishlatilgan elementlar o'chiriladi (chaqiruvchi nusxa beradi)."""
    limit = min(UL, max_strip_len) if max_strip_len else UL
    cols: list[_Column] = []
    x = 0.0
    area = 0.0
    types = set(used_types)

    def type_ok(it: Item) -> bool:
        return types_left is None or it.part_id in types or len(types) < types_left

    while True:
        rem = limit - x
        best = None
        for idx, it in enumerate(pool):
            if not type_ok(it):
                continue
            for (dl, dw, rot) in it.orientations():
                if dw <= h + 1e-9 and dl <= rem + 1e-9:
                    # h ga eng yaqin (eng baland) yo'nalishni tanlaymiz
                    key = (dw, dl * dw)
                    if best is None or key > best[0]:
                        best = (key, idx, dl, dw, rot)
            if best and best[0][0] >= h - 1e-9:
                break  # to'liq balandlikdagi birinchi mos detal — FFD
        if best is None:
            break
        _, idx, dl, dw, rot = best
        it = pool.pop(idx)
        types.add(it.part_id)
        col = _Column(x=x, width=dl)
        col.pieces.append(_Piece(it, x, 0.0, dl, dw, rot))
        area += dl * dw
        used_h = dw
        # 3-bosqich: ustunga detallarni ustma-ust qo'yish
        if complex_strips:
            while True:
                free = h - used_h - kerf
                if free <= 0:
                    break
                cand = None
                for j, it2 in enumerate(pool):
                    if not type_ok(it2):
                        continue
                    for (dl2, dw2, rot2) in it2.orientations():
                        if dl2 <= dl + 1e-9 and dw2 <= free + 1e-9:
                            key = (dl2 == dl, dl2 * dw2)
                            if cand is None or key > cand[0]:
                                cand = (key, j, dl2, dw2, rot2)
                if cand is None:
                    break
                _, j, dl2, dw2, rot2 = cand
                it2 = pool.pop(j)
                types.add(it2.part_id)
                col.pieces.append(_Piece(it2, x, used_h + kerf, dl2, dw2, rot2))
                area += dl2 * dw2
                used_h += kerf + dw2
        cols.append(col)
        x += dl + kerf
    used_types |= types
    return cols, area


def _pack_sheet(layout: _SheetLayout, pool: list[Item], p: CSCutParams,
                mode: str = "fill") -> None:
    """Bitta listga imkon qadar ko'p detal joylaydi (pool o'zgaradi).
    mode: "fill" — polosa to'lishi % bo'yicha, "area" — polosadagi maydon bo'yicha,
          "ffd" — har doim eng katta qolgan detal balandligi bo'yicha polosa."""
    y = 0.0
    used_types: set[str] = set()
    types_left = p.max_part_types_per_map or None
    while pool:
        rem_w = layout.UW - y
        # Nomzod polosa balandliklari: birinchi bir nechta detal o'lchamlari
        cands: list[float] = []
        for it in pool[:12]:
            for (_, dw, _) in it.orientations():
                if dw <= rem_w + 1e-9 and dw not in cands:
                    if p.max_strip_width and dw > p.max_strip_width:
                        continue
                    cands.append(dw)
        if not cands:
            break
        if mode == "ffd":
            cands = cands[:2]
        best = None
        for h in cands[:6]:
            trial_pool = list(pool)
            trial_types = set(used_types)
            cols, area = _fill_strip(h, layout.UL, trial_pool, p.kerf, p.complex_strips,
                                     types_left, trial_types, p.max_strip_length)
            if not cols:
                continue
            h_eff = max(h, p.min_strip_width or 0)
            score = area / (layout.UL * h_eff)
            key = (area, score) if mode == "area" else (round(score, 4), area)
            if best is None or key > best[0]:
                best = (key, h_eff, cols, trial_pool, trial_types)
        if best is None:
            break
        _, h, cols, new_pool, used_types = best
        # ustunlar y koordinatasini polosa y siga ko'chirish
        for c in cols:
            for pc in c.pieces:
                pc.y += y
        layout.strips.append(_Strip(y=y, height=h, columns=cols))
        pool[:] = new_pool
        y += h + p.kerf


SORT_KEYS = ("area", "maxside", "width", "length", "perimeter")


def _sort_items(items: list[Item], key: str) -> list[Item]:
    keys = {
        "area": lambda i: (i.area, max(i.l, i.w)),
        "maxside": lambda i: (max(i.l, i.w), i.area),
        "width": lambda i: (min(i.l, i.w), i.area),
        "length": lambda i: (i.l, i.w),
        "perimeter": lambda i: (i.l + i.w, i.area),
    }
    return sorted(items, key=keys[key], reverse=True)


# ───────────────────────── Asosiy funksiya ─────────────────────────
def _usable(stock: StockSheet, p: CSCutParams, transposed: bool):
    L, W = (stock.width, stock.length) if transposed else (stock.length, stock.width)
    tl = stock.trim_length if stock.trim_length is not None else p.trim_length
    tw = stock.trim_width if stock.trim_width is not None else p.trim_width
    if transposed:
        tl, tw = tw, tl
    add = 0 if p.trim_includes_kerf else p.kerf
    offL = (tl + add) if tl > 0 else 0
    offW = (tw + add) if tw > 0 else 0
    sides = 2 if p.trim_both_sides else 1
    return L, W, offL, offW, L - sides * offL - p.min_end_offset, W - sides * offW


def _run(items: list[Item], stock: list[StockSheet], p: CSCutParams,
         transposed: bool) -> tuple[list[_SheetLayout], list[Item]]:
    pool = list(items)
    if transposed:  # aylantirib bo'lmaydigan detallar ham transpozitsiya qilinadi
        pool = [Item(i.part_id, i.uid, i.w, i.l, i.can_rotate) for i in pool]
    layouts: list[_SheetLayout] = []
    remaining = {s.id: s.qty for s in stock}
    for s in stock:
        while remaining[s.id] > 0 and pool:
            L, W, ox, oy, UL, UW = _usable(s, p, transposed)
            # Har bir list uchun bir nechta variant: eng ko'p maydon joylaganini olamiz
            best = None
            for mode in ("fill", "area", "ffd"):
                for key in SORT_KEYS:
                    trial = _sort_items(pool, key)
                    lay = _SheetLayout(s, L, W, ox, oy, UL, UW, transposed)
                    _pack_sheet(lay, trial, p, mode)
                    placed = sum(pc.l * pc.w for pc in lay.pieces)
                    if best is None or placed > best[0] + 1e-6:
                        best = (placed, lay, trial)
            _, lay, pool = best
            if not lay.strips:
                break  # bu list turiga hech narsa sig'madi
            layouts.append(lay)
            remaining[s.id] -= 1
    return layouts, pool


def _score(layouts: list[_SheetLayout], left: list[Item]):
    used_area = sum(l.stock.length * l.stock.width for l in layouts)
    # oxirgi listda qolgan bo'sh joy qancha katta bo'lsa — shuncha yaxshi (qoldiq)
    last_used = sum(pc.l * pc.w for pc in layouts[-1].pieces) if layouts else 0
    return (len(left), len(layouts), used_area, last_used)


def optimize(items: list[Item], stock: list[StockSheet], cut: CSCutParams,
             mat: CSMaterialParams) -> CuttingResult:
    if not items or not stock:
        return CuttingResult(unplaced=[i.part_id for i in items])

    # Ombordagi qoldiqlar birinchi (kichigidan), keyin to'liq listlar
    stock_sorted = sorted(stock, key=lambda s: (not s.is_remnant,
                                                s.length * s.width if s.is_remnant else 0))
    dirs = {
        FirstCutDir.ANY: [False, True],
        FirstCutDir.LENGTH: [False],
        FirstCutDir.WIDTH: [True],
        FirstCutDir.LENGTH_PREF: [False, True],
        FirstCutDir.WIDTH_PREF: [True, False],
    }[cut.first_cut]

    best = None
    for tr in dirs:
        layouts, left = _run(items, stock_sorted, cut, tr)
        sc = _score(layouts, left)
        if best is None or sc < best[0]:
            best = (sc, layouts, left)
    _, layouts, left = best
    return _build_result(layouts, left, cut, mat)


# ───────────────────────── Natijani yig'ish ─────────────────────────
def _classify(l: float, w: float, mat: CSMaterialParams) -> str:
    a, b = max(l, w), min(l, w)
    if a >= mat.remnant_min_side1 and b >= mat.remnant_min_side2 and \
            (a * b) / 1e6 >= mat.remnant_min_area:
        return "remnant"
    return "waste"


def _to_sheet_xy(lay: _SheetLayout, x: float, y: float, l: float, w: float):
    """Foydali zona koordinatasini haqiqiy list koordinatasiga o'tkazish."""
    X, Y = x + lay.ox, y + lay.oy
    if lay.transposed:
        return Y, X, w, l
    return X, Y, l, w


def _build_map(lay: _SheetLayout, idx: int, p: CSCutParams,
               mat: CSMaterialParams, remnant_counter: list[int]) -> CutMap:
    m = CutMap(index=idx, sheet_id=lay.stock.id,
               sheet_length=lay.stock.length, sheet_width=lay.stock.width)
    cmds: list[CutCommand] = []
    cut_len = 0.0
    cuts = 0
    kerf = p.kerf

    # Torsovka
    if lay.oy > 0:
        cmds.append(CutCommand(code="T", level=1, size=lay.oy - (0 if p.trim_includes_kerf else kerf)))
        cut_len += lay.L; cuts += 1
    if lay.ox > 0:
        cmds.append(CutCommand(code="T", level=2, size=lay.ox - (0 if p.trim_includes_kerf else kerf)))
        cut_len += lay.W; cuts += 1

    y_end = 0.0
    for s in lay.strips:
        cmds.append(CutCommand(code="C", level=1, size=s.height))
        cut_len += lay.UL; cuts += 1
        x_end = 0.0
        for c in s.columns:
            single = len(c.pieces) == 1 and abs(c.pieces[0].w - s.height) < 1e-6
            if single:
                pc = c.pieces[0]
                cmds.append(CutCommand(code="P", level=2, size=c.width, ref=str(pc.item.uid)))
                cut_len += s.height; cuts += 1
            else:
                cmds.append(CutCommand(code="C", level=2, size=c.width))
                cut_len += s.height; cuts += 1
                used = 0.0
                for pc in c.pieces:
                    cmds.append(CutCommand(code="P", level=3, size=pc.w, ref=str(pc.item.uid)))
                    cut_len += c.width; cuts += 1
                    used = pc.y - s.y + pc.w
                    if pc.l < c.width - 1e-6:  # 4-bosqich: detal ustundan tor
                        cut_len += pc.w; cuts += 1
                        _add_off(m, lay, pc.x + pc.l + kerf, pc.y,
                                 c.width - pc.l - kerf, pc.w, mat, remnant_counter)
                    used += kerf
                if s.height - used > 0:
                    cmds.append(CutCommand(code="W", level=3, size=s.height - used))
                    _add_off(m, lay, c.x, s.y + used, c.width, s.height - used, mat, remnant_counter)
            x_end = c.x + c.width + kerf
        if lay.UL - x_end > 0:
            cmds.append(CutCommand(code="W", level=2, size=lay.UL - x_end))
            _add_off(m, lay, x_end, s.y, lay.UL - x_end, s.height, mat, remnant_counter)
        y_end = s.y + s.height + kerf
    if lay.UW - y_end > 0:
        off = _add_off(m, lay, 0, y_end, lay.UL, lay.UW - y_end, mat, remnant_counter)
        cmds.append(CutCommand(code="W", level=1, size=lay.UW - y_end,
                               ref=f"Д{off.number}" if off and off.kind == "remnant" else ""))

    for pc in lay.pieces:
        X, Y, l, w = _to_sheet_xy(lay, pc.x, pc.y, pc.l, pc.w)
        m.placements.append(Placement(part_id=pc.item.part_id, part_uid=pc.item.uid,
                                      x=X, y=Y, length=l, width=w, rotated=pc.rotated))
    if lay.transposed:
        cmds.insert(0, CutCommand(code="R", level=0, size=90))
    m.commands = _collapse(cmds)
    m.parts_count = len(m.placements)
    m.cut_length_m = round(cut_len / 1000, 3)
    m.cuts_count = cuts
    m.parts_area_m2 = round(sum(pl.length * pl.width for pl in m.placements) / 1e6, 4)
    m.sheet_area_m2 = round(lay.stock.length * lay.stock.width / 1e6, 4)
    m.fill_percent = round(100 * m.parts_area_m2 / m.sheet_area_m2, 2) if m.sheet_area_m2 else 0
    return m


def _add_off(m: CutMap, lay: _SheetLayout, x, y, l, w, mat, counter) -> Offcut | None:
    if l <= 0 or w <= 0:
        return None
    X, Y, L2, W2 = _to_sheet_xy(lay, x, y, l, w)
    kind = _classify(L2, W2, mat)
    num = 0
    if kind == "remnant":
        counter[0] += 1; num = counter[0]
    off = Offcut(x=X, y=Y, length=L2, width=W2, kind=kind, number=num)
    m.offcuts.append(off)
    return off


def _collapse(cmds: Iterable[CutCommand]) -> list[CutCommand]:
    out: list[CutCommand] = []
    for c in cmds:
        if out and (out[-1].code, out[-1].level, out[-1].size, out[-1].ref) == \
                (c.code, c.level, c.size, c.ref) and c.code in ("P", "C"):
            out[-1].count += 1
        else:
            out.append(c.model_copy())
    return out


def _signature(m: CutMap):
    return (m.sheet_id, tuple(sorted((p.part_id, p.x, p.y, p.length, p.width) for p in m.placements)))


def _build_result(layouts: list[_SheetLayout], left: list[Item],
                  p: CSCutParams, mat: CSMaterialParams) -> CuttingResult:
    maps: list[CutMap] = []
    counter = [0]
    for lay in layouts:
        m = _build_map(lay, len(maps) + 1, p, mat, counter)
        if maps and _signature(maps[-1]) == _signature(m):
            maps[-1].copies += 1
            # takroriy kartaning qoldiqlari ham hisobga olinadi
            continue
        maps.append(m)
    for i, m in enumerate(maps, 1):
        m.index = i
    res = CuttingResult(maps=maps)
    res.total_sheets = sum(m.copies for m in maps)
    res.total_parts = sum(m.parts_count * m.copies for m in maps)
    res.unplaced = [i.part_id for i in left]
    res.total_cut_length_m = round(sum(m.cut_length_m * m.copies for m in maps), 3)
    res.parts_area_m2 = round(sum(m.parts_area_m2 * m.copies for m in maps), 4)
    res.material_area_m2 = round(sum(m.sheet_area_m2 * m.copies for m in maps), 4)
    res.total_fill_percent = round(100 * res.parts_area_m2 / res.material_area_m2, 2) \
        if res.material_area_m2 else 0
    res.remnants = [o for m in maps for o in m.offcuts if o.kind == "remnant" for _ in range(m.copies)]
    return res
