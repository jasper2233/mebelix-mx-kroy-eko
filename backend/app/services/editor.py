"""Редактирование раскроя — kroy kartasini qo'lda tahrirlash (kesish daraxti ustida amallar).

Frontend qoralama natijani (CuttingResult) va bitta amalni yuboradi → backend yangi natijani qaytaradi.
Har amaldan keyin natija to'liq qayta quriladi (joylashuvlar, qoldiqlar, T/C/P/W buyruqlari, LT/CT/F)
va tekshiriladi: jismonan kesib bo'lmaydigan holat (ustma-ust, propilsiz, minimal obrezkadan kichik
qirindi, daraxt chuqurligi, detal/list soni) qaytarilmaydi — EditError.

Manzil (path) — kesish daraxtidagi bolalar indekslari ro'yxati (karta.strips[0] dan boshlab).
Amallar:
  place      {map, path, uid, rotated}  bo'sh (chiqindi) joyga detal qo'yish — joyning burchagiga
  place_auto {map, uid, rotated?}       kartadagi eng mos bo'sh joyga detal qo'yish
  remove     {map, path}                detal yoki polosani olib tashlash (joyi chiqindiga aylanadi)
  move       {map, path, to}            to: start | end | prev | next  (Ctrl+← / Ctrl+→)
  clone      {map, path}                polosa/detal nusxasi — shu tugundagi bo'sh joyga (Ctrl+C)
  expand     {map, path}                polosani keyingi bo'sh joy hisobiga kengaytirish (Ctrl+Q)
  rotate     {map, path}                hududni boshqa yo'nalishda qayta kesish (Ctrl+R)
  add_map    {sheet_id, axis?}          yangi bo'sh karta
  delete_map {map}
  copies     {map, copies}              karta bo'yicha listlar soni (C)
"""
from __future__ import annotations

import copy
import time
from collections import Counter, deque
from dataclasses import dataclass
from typing import Optional

from ..models import CuttingResult, CutMap, Operation, Project
from .calc import _items_for, edge_map, total_qty
from .optimizer import (EPS, Item, _best_sheet, _build_map, _depth, _extent, _finish, _N, _normalize, _other,
                        _Pool, _ser, _Sheet, _zone, _Zone)
from .sizes import compute_sizes
from .validate import validate
from ..i18n import _

TOL = 0.01


class EditError(ValueError):
    def __init__(self, message: str, details: Optional[list[str]] = None):
        super().__init__(message)
        self.details = details or []


@dataclass
class PartInfo:
    part_id: str
    uid: int
    l: float          # arra o'lchami (X, aylantirilmagan)
    w: float
    can_rotate: bool
    need: int         # jami kerak (ОК)
    name: str


def part_info(project: Project, op: Operation) -> dict[int, PartInfo]:
    cut = op.cs_cut
    edges = edge_map(project)
    out = {}
    for p in op.parts:
        s = compute_sizes(p, project.size_mode, edges, cut.machining_allowance)
        out[p.uid] = PartInfo(p.id, p.uid, s.saw[0], s.saw[1], not (cut.use_grain and p.grain),
                              total_qty(project, p), p.name)
    return out


# ───────────────────────── daraxt ↔ JSON ─────────────────────────
def _from_dict(d: dict, z: _Zone, info: dict[int, PartInfo], level: int = 0) -> _N:
    kind = d.get("k")
    n = _N(float(d["x"]) - z.ox, float(d["y"]) - z.oy, float(d["l"]), float(d["w"]), level, kind, axis=d.get("a"))
    if kind == "C":
        if n.axis not in ("x", "y"):
            raise EditError(_("ed.bad_axis"))
        n.children = [_from_dict(c, z, info, level + 1) for c in d.get("c", [])]
    elif kind == "P":
        uid = d.get("u")
        pi = info.get(uid)
        if pi is None:
            raise EditError(_("ed.part_missing", uid=uid))
        if "o" in d:
            n.rot = bool(d["o"])
        else:  # eski natija: aylanishni o'lchamdan aniqlash
            n.rot = not (abs(n.l - pi.l) <= TOL and abs(n.w - pi.w) <= TOL) and \
                abs(n.l - pi.w) <= TOL and abs(n.w - pi.l) <= TOL
        n.pid = (pi.part_id, uid)
    elif kind == "W":
        n.rem = int(d.get("r", 0) or 0)
    else:
        raise EditError(_("ed.bad_kind", k=kind))
    return n


def _node_at(root: _N, path: list[int]) -> tuple[Optional[_N], _N, int]:
    """(ota, tugun, indeks). path=[] — ildiz (ota yo'q)."""
    parent, node, idx = None, root, -1
    for i in path:
        if node.kind != "C" or not (0 <= i < len(node.children)):
            raise EditError(_("ed.node_missing"))
        parent, node, idx = node, node.children[i], i
    return parent, node, idx


def _start(n: _N, ax: str) -> float:
    return n.x if ax == "x" else n.y


def _set_extent(n: _N, ax: str, v: float) -> None:
    if ax == "x":
        n.l = v
    else:
        n.w = v


def _move_to(n: _N, ax: str, pos: float) -> None:
    d = pos - _start(n, ax)
    n.shift(d, 0) if ax == "x" else n.shift(0, d)


def _waste(x, y, l, w) -> _N:
    return _N(x, y, l, w, 0, "W")


def _leaves_p(n: _N) -> list[_N]:
    return [lf for lf in n.leaves() if lf.kind == "P"]


def _relayout(node: _N, body: list[_N], kerf: float) -> None:
    """Tugun bolalarini o'q bo'yicha zich joylash: body ketma-ket propil bilan, oxirida bitta chiqindi."""
    ax = node.axis
    start = _start(node, ax)
    end = start + _extent(node, ax)
    pos = start
    for c in body:
        _move_to(c, ax, pos)
        pos += _extent(c, ax) + kerf
    kids = list(body)
    rest = end - pos
    if rest > EPS:
        w = _waste(pos, node.y, rest, node.w) if ax == "x" else _waste(node.x, pos, node.l, rest)
        kids.append(w)
    node.children = kids


# ───────────────────────── amallar ─────────────────────────
def _place(root: _N, path: list[int], pi: PartInfo, rotated: bool, kerf: float) -> None:
    parent, leaf, idx = _node_at(root, path)
    if parent is None or leaf.kind != "W":
        raise EditError(_("ed.place_on_waste"))
    if rotated and not pi.can_rotate:
        raise EditError(_("ed.grain_no_rotate", uid=pi.uid))
    ax = parent.axis
    ext_a, ext_b = (leaf.l, leaf.w) if ax == "x" else (leaf.w, leaf.l)

    def fits(rot: bool) -> bool:
        l, w = (pi.w, pi.l) if rot else (pi.l, pi.w)
        a, b = (l, w) if ax == "x" else (w, l)
        return a <= ext_a + TOL and b <= ext_b + TOL
    if not fits(rotated):
        # so'ralgan holatda sig'masa, lekin aylantirilganda sig'sa (tekstura ruxsat bersa) — avtomatik aylantiriladi
        if pi.can_rotate and fits(not rotated):
            rotated = not rotated
        else:
            pl0, pw0 = (pi.w, pi.l) if rotated else (pi.l, pi.w)
            raise EditError(_("ed.no_fit", uid=pi.uid, size=f"{pl0:g}×{pw0:g}", free=f"{leaf.l:g}×{leaf.w:g}"))
    pl, pw = (pi.w, pi.l) if rotated else (pi.l, pi.w)
    pa, pb = (pl, pw) if ax == "x" else (pw, pl)
    part = _N(leaf.x, leaf.y, pl, pw, 0, "P", rot=rotated)
    part.pid = (pi.part_id, pi.uid)
    if abs(pb - ext_b) <= TOL:
        slot = part
    else:
        ox = _other(ax)
        rest_b = ext_b - pb - kerf
        kids = [part]
        if rest_b > EPS:
            kids.append(_waste(leaf.x + pl + kerf, leaf.y, rest_b, pw) if ox == "x"
                        else _waste(leaf.x, leaf.y + pw + kerf, pl, rest_b))
        slot = _N(leaf.x, leaf.y, pl if ax == "x" else leaf.l, leaf.w if ax == "x" else pw, 0, "C",
                  axis=ox, children=kids)
    new = [slot]
    rest_a = ext_a - pa - kerf
    if rest_a > EPS:
        new.append(_waste(leaf.x + pa + kerf, leaf.y, rest_a, leaf.w) if ax == "x"
                   else _waste(leaf.x, leaf.y + pa + kerf, leaf.l, rest_a))
    parent.children[idx:idx + 1] = new


def _free_leaves(n: _N, path: list[int], out: list) -> None:
    for i, c in enumerate(n.children):
        if c.kind == "W":
            out.append((path + [i], c))
        elif c.kind == "C":
            _free_leaves(c, path + [i], out)


def _place_auto(root: _N, pi: PartInfo, rotated: Optional[bool], kerf: float) -> None:
    """Eng mos bo'sh joy: detal sig'adigan eng kichik maydonli chiqindi (yo'nalishlar sinab ko'riladi)."""
    free: list = []
    _free_leaves(root, [], free)
    opts = [rotated] if rotated is not None else ([False, True] if pi.can_rotate else [False])
    best = None
    for path, lf in free:
        for rot in opts:
            pl, pw = (pi.w, pi.l) if rot else (pi.l, pi.w)
            if pl <= lf.l + TOL and pw <= lf.w + TOL:
                key = (lf.l * lf.w, path)
                if best is None or key < best[0]:
                    best = (key, path, rot)
    if best is None:
        raise EditError(_("ed.no_fit_any", uid=pi.uid))
    _place(root, best[1], pi, best[2], kerf)


def _remove(root: _N, path: list[int]) -> None:
    parent, node, idx = _node_at(root, path)
    if parent is None:
        root.children = [_waste(root.x, root.y, root.l, root.w)]
        return
    parent.children[idx] = _waste(node.x, node.y, node.l, node.w)


def _move(root: _N, path: list[int], to: str, kerf: float) -> None:
    parent, node, idx = _node_at(root, path)
    if parent is None:
        raise EditError(_("ed.root_move"))
    if node.kind == "W":
        raise EditError(_("ed.waste_move"))
    body = [c for c in parent.children if c.kind != "W"]
    i = body.index(node)
    body.pop(i)
    if to == "start":
        body.insert(0, node)
    elif to == "end":
        body.append(node)
    elif to == "prev":
        body.insert(max(0, i - 1), node)
    elif to == "next":
        body.insert(min(len(body), i + 1), node)
    else:
        raise EditError(_("ed.bad_dir", d=to))
    _relayout(parent, body, kerf)


def _clone(root: _N, path: list[int], kerf: float) -> list[tuple[str, int]]:
    parent, node, idx = _node_at(root, path)
    if parent is None or node.kind == "W":
        raise EditError(_("ed.clone_select"))
    ax = parent.axis
    ext = _extent(node, ax)
    cands = [(i, c) for i, c in enumerate(parent.children) if c.kind == "W" and _extent(c, ax) >= ext - TOL]
    if not cands:
        raise EditError(_("ed.clone_space"))
    after = [x for x in cands if x[0] > idx]
    i, w = (after or cands)[0]
    dup = copy.deepcopy(node)
    _move_to(dup, ax, _start(w, ax))
    rest = _extent(w, ax) - ext - kerf
    new = [dup]
    if rest > EPS:
        nw = _waste(w.x, w.y, w.l, w.w)
        _move_to(nw, ax, _start(w, ax) + ext + kerf)
        _set_extent(nw, ax, rest)
        new.append(nw)
    parent.children[i:i + 1] = new
    return [lf.pid for lf in _leaves_p(dup)]


def _grow(n: _N, ax: str, d: float, kerf: float) -> _N:
    """Tugunni ax o'qi bo'yicha d ga kengaytiradi (gilyotina saqlanadi). Yangi tugun qaytadi."""
    if n.kind == "W":
        _set_extent(n, ax, _extent(n, ax) + d)
        return n
    if n.kind == "P":
        end = _start(n, ax) + _extent(n, ax)
        kids = [n]
        rest = d - kerf
        if rest > EPS:
            w = _waste(n.x, n.y, n.l, n.w)
            _move_to(w, ax, end + kerf)
            _set_extent(w, ax, rest)
            kids.append(w)
        c = _N(n.x, n.y, n.l, n.w, 0, "C", axis=ax, children=kids)
        _set_extent(c, ax, _extent(n, ax) + d)
        return c
    if n.axis == ax:          # bolalar shu o'q bo'ylab — oxirgi chiqindi kattalashadi
        last = n.children[-1] if n.children else None
        if last is not None and last.kind == "W":
            _set_extent(last, ax, _extent(last, ax) + d)
        else:
            end = _start(n, ax) + _extent(n, ax)
            rest = d - kerf
            if rest > EPS:
                w = _waste(n.x, n.y, n.l, n.w)
                _move_to(w, ax, end + kerf)
                _set_extent(w, ax, rest)
                n.children.append(w)
        _set_extent(n, ax, _extent(n, ax) + d)
        return n
    n.children = [_grow(c, ax, d, kerf) for c in n.children]   # ko'ndalang: har bola kengayadi
    _set_extent(n, ax, _extent(n, ax) + d)
    return n


def _expand(root: _N, path: list[int], kerf: float) -> None:
    parent, node, idx = _node_at(root, path)
    if parent is None or node.kind != "C":
        raise EditError(_("ed.expand_select"))
    ax = parent.axis
    if idx + 1 >= len(parent.children) or parent.children[idx + 1].kind != "W":
        raise EditError(_("ed.expand_space"))
    w = parent.children[idx + 1]
    d = _extent(w, ax) + kerf
    parent.children[idx] = _grow(node, ax, d, kerf)
    parent.children.pop(idx + 1)


def _rotate(root: _N, path: list[int], zone: _Zone, op: Operation, info: dict[int, PartInfo],
            depth_used: int) -> _N:
    """Hududdagi detallarni boshqa yo'nalishda (1-kesish o'qi almashadi) qayta joylaydi."""
    parent, node, idx = _node_at(root, path)
    if node.kind != "C":
        raise EditError(_("ed.rotate_select"))
    leaves = _leaves_p(node)
    if not leaves:
        raise EditError(_("ed.rotate_empty"))
    items = []
    for lf in leaves:
        pi = info[lf.pid[1]]
        items.append(Item(pi.part_id, pi.uid, pi.l, pi.w, pi.can_rotate))
    pool = _Pool(items)
    cut = op.cs_cut.model_copy(update={"max_rotations": max(2, op.cs_cut.max_rotations - depth_used)})
    sub = _Zone(zone.stock, zone.L, zone.W, 0.0, 0.0, node.l, node.w, 0.0, 0.0)
    new_axis = _other(node.axis)
    best = _best_sheet(pool, pool.counts0[:], sub, cut, [new_axis], time.monotonic() + 1.5, target_all=True)
    if best is None or sum(best.counts_after) > 0:
        raise EditError(_("ed.rotate_fail"))
    queues = {s.idx: deque(s.pids) for s in pool.shapes}
    for lf in best.root.leaves():
        if lf.kind == "P":
            lf.pid = queues[lf.s].popleft()
    new = best.root
    new.shift(node.x, node.y)
    if parent is None:
        return new
    parent.children[idx] = new
    return root


def _depth_of(path: list[int]) -> int:
    return len(path)


# ───────────────────────── qayta qurish va tekshirish ─────────────────────────
def rebuild(project: Project, op: Operation, res: CuttingResult) -> CuttingResult:
    """Barcha kartalarni daraxtdan qayta quradi (raqamlash, buyruqlar, ko'rsatkichlar) va tekshiradi."""
    cut, mat = op.cs_cut, op.cs_material
    info = part_info(project, op)
    stock = {s.id: s for s in op.sheets}
    counter = [0]
    maps: list[CutMap] = []
    max_depth = max(2, cut.max_rotations) + 1
    for m in res.maps:
        st = stock.get(m.sheet_id)
        if st is None:
            raise EditError(_("ed.sheet_missing", map=m.index))
        if not m.strips:
            raise EditError(_("ed.no_tree", map=m.index))
        z = _zone(st, cut)
        root = _normalize(_from_dict(m.strips[0], z, info))
        if root is None:
            raise EditError(_("ed.tree_empty", map=m.index))
        if _depth(root) > max_depth:
            raise EditError(_("ed.too_deep", map=m.index, d=_depth(root) - 1, m=max(2, cut.max_rotations)))
        nm = _build_map(_Sheet(z, root, 0.0, []), len(maps) + 1, cut, mat, counter, {})
        nm.copies = max(1, int(m.copies))
        nm.comment = m.comment
        nm.done_count = min(m.done_count, nm.copies)
        maps.append(nm)
    out = CuttingResult(maps=maps, variant=res.variant, manual=True, elapsed_s=res.elapsed_s)
    placed: Counter = Counter()
    for m in maps:
        for pl in m.placements:
            placed[pl.part_id] += m.copies
    need = {pi.part_id: pi.need for pi in info.values()}
    names = {pi.part_id: pi.uid for pi in info.values()}
    for pid, n in placed.items():
        if n > need.get(pid, 0):
            raise EditError(_("ed.too_many", uid=names.get(pid, pid), n=n, need=need.get(pid, 0)))
    used_sheets: Counter = Counter()
    for m in maps:
        used_sheets[m.sheet_id] += m.copies
    for sid, n in used_sheets.items():
        st = stock[sid]
        if st.qty < 10000 and n > st.qty:
            raise EditError(_("ed.sheets_exceeded", size=f"{st.length:g}×{st.width:g}", n=n, q=st.qty))
    out.unplaced = [pid for pid, n in need.items() for _ in range(n - placed.get(pid, 0))]
    _finish(out, mat)
    errs = validate(out, _items_for(project, op, cut), op.sheets, cut)
    if errs:
        raise EditError(errs[0], errs)
    return out


def apply(project: Project, op: Operation, res: CuttingResult, action: dict) -> CuttingResult:
    """Bitta tahrir amali. Xato bo'lsa EditError (qoralama o'zgarmaydi)."""
    res = res.model_copy(deep=True)
    kind = action.get("type")
    cut = op.cs_cut
    kerf = cut.kerf
    info = part_info(project, op)
    stock = {s.id: s for s in op.sheets}

    if kind == "add_map":
        st = stock.get(action.get("sheet_id")) or (op.sheets[0] if op.sheets else None)
        if st is None:
            raise EditError(_("ed.no_sheet"))
        z = _zone(st, cut)
        if z.UL <= 0 or z.UW <= 0:
            raise EditError(_("ed.sheet_small"))
        axis = action.get("axis") or "y"
        root = _N(0, 0, z.UL, z.UW, 0, "C", axis=axis, children=[_waste(0, 0, z.UL, z.UW)])
        res.maps.append(CutMap(index=len(res.maps) + 1, sheet_id=st.id, sheet_length=st.length,
                               sheet_width=st.width, is_remnant=st.is_remnant, strips=[_ser(root, z)]))
        return rebuild(project, op, res)

    mi = int(action.get("map", 0)) - 1
    if not (0 <= mi < len(res.maps)):
        raise EditError(_("ed.no_map"))
    m = res.maps[mi]

    if kind == "delete_map":
        res.maps.pop(mi)
        return rebuild(project, op, res)
    if kind == "copies":
        m.copies = max(1, int(action.get("copies", 1)))
        return rebuild(project, op, res)

    st = stock.get(m.sheet_id)
    if st is None:
        raise EditError(_("ed.no_sheet"))
    z = _zone(st, cut)
    if not m.strips:
        raise EditError(_("ed.no_tree", map=mi + 1))
    root = _from_dict(m.strips[0], z, info)
    path = [int(i) for i in action.get("path", [])]

    def remaining(uid: int) -> int:
        pi = info[uid]
        used = sum(mm.copies for mm in res.maps for pl in mm.placements if pl.part_id == pi.part_id)
        return pi.need - used

    if kind in ("place", "place_auto"):
        uid = int(action.get("uid", 0))
        pi = info.get(uid)
        if pi is None:
            raise EditError(_("part_uid_not_found", uid=uid))
        if remaining(uid) < m.copies:
            raise EditError(_("ed.none_left", uid=uid, c=m.copies))
        if kind == "place":
            _place(root, path, pi, bool(action.get("rotated", False)), kerf)
        else:
            rot = action.get("rotated")
            _place_auto(root, pi, None if rot is None else bool(rot), kerf)
    elif kind == "remove":
        _remove(root, path)
    elif kind == "move":
        _move(root, path, str(action.get("to", "end")), kerf)
    elif kind == "clone":
        pids = _clone(root, path, kerf)
        cnt = Counter(uid for _pid, uid in pids)
        for uid, n in cnt.items():
            if remaining(uid) < n * m.copies:
                raise EditError(_("ed.clone_parts", uid=uid, n=remaining(uid)))
    elif kind == "expand":
        _expand(root, path, kerf)
    elif kind == "rotate":
        root = _rotate(root, path, z, op, info, _depth_of(path))
    else:
        raise EditError(_("ed.bad_action", a=kind))
    root = _normalize(root)
    if root is None:
        raise EditError(_("ed.map_empty"))
    m.strips = [_ser(root, z)]
    return rebuild(project, op, res)
