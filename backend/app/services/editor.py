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
  rotate     {map, path}                «Развернуть резы» (Ctrl+R): detallar joyida, 1-kesish o'qi almashadi (path=[] — butun list;
                                        imkonsiz bo'lsa — hududni boshqa yo'nalishda qayta joylash)
  pack_corner {map, corner}             karta zichlash burchagi (LT/RT/LB/RB, null — umumiy sozlama); karta darhol zichlanadi
O'chirishdan keyin karta tanlangan burchakka zichlanadi (services/editor_pack.py, onlayn tizimdagidek).
  add_map    {sheet_id, axis?}          yangi bo'sh karta
  delete_map {map}
  copies     {map, copies}              karta bo'yicha listlar soni (C)
W13 (services/editor_w13.py) — CSE rejimlari:
  remove / move / clone / rotate   `paths: [[…], …]` (ko'p tanlash) ham qabul qiladi (`path` — bitta)
  place_multi  {map, path, uid, rotated?, count?}  Shift+A: bo'sh joyga ketma-ket ko'p nusxa
  expand_block {map, path}                         Shift+W: blokni «Группировка» maksimal soniga kengaytirish
  flip         {map, path}                         joylashgan detalni (tekstura ruxsat bersa) burish
  replace      {map, path, uid, rotated?}          joylashgan detalni boshqasiga almashtirish
  swap         {map, paths:[a, b]}                 bitta polosadagi ikki elementning o'rnini almashtirish
  move_map     {map, to}                           kartani ko'chirish: up | down | first | last (Ctrl+↑/↓)
  map_trim     {map, trim_length?, trim_width?, end_offset_bottom?, end_offset_right?}   «Торцовка листа»
  comment      {map, comment}                      karta izohi (F2)
"""
from __future__ import annotations

import copy
import math
import time
from collections import Counter, deque
from dataclasses import dataclass
from typing import Optional

from ..models import CuttingResult, CutMap, Operation, Project
from .calc import _items_for, edge_map, effective_qty
from .optimizer import (EPS, Item, _axes_for, _best_sheet, _trim_violations, _build_map, _depth, _extent, _finish, _N, _normalize, _other,
                        _Pool, _ser, _Sheet, _zone, _Zone, group_kerf)
from .sizes import compute_sizes
from .validate import TRIM_KEYS, map_stock, validate
from . import editor_pack
from ..i18n import _

TOL = 0.01
RELAYOUT_S = 3.0          # «detal sig'masa — list qayta joylanadi» qidiruvi (soniya)
MAX_PATH_DEPTH = 40                       # daraxt chuqurligi / manzil uzunligi chegarasi (xavfsizlik)
COMMENT_MAX = 2000                        # karta izohi uzunligi chegarasi


class EditError(ValueError):
    def __init__(self, message: str, details: Optional[list[str]] = None, code: str = ""):
        super().__init__(message)
        self.details = details or []
        self.code = code              # mashina uchun belgi (frontend maxsus oyna ko'rsatadi), masalan «rotate_keep»


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
                              effective_qty(project, p), p.name)
    return out


# ───────────────────────── daraxt ↔ JSON ─────────────────────────
Groups = Optional[tuple[set, float]]      # (guruhlanadigan detallar uid lari, guruh propili)


def op_groups(op: Operation) -> Groups:
    return ({p.uid for p in op.parts if p.group_by in ("length", "width")}, group_kerf(op.cs_cut))


def _num(v) -> float:
    f = float(v)
    if not math.isfinite(f) or abs(f) > 1e6:
        raise ValueError(v)
    return f


def _from_dict(d: dict, z: _Zone, info: dict[int, PartInfo], level: int = 0, grp: Groups = None) -> _N:
    """JSON daraxt → tugunlar. Buzuq ma'lumot (kalit yo'q, son emas, cheksiz) — EditError (4xx), 500 emas."""
    try:
        return _from_dict_raw(d, z, info, level, grp)
    except EditError:
        raise
    except (KeyError, TypeError, ValueError, AttributeError, RecursionError):
        raise EditError(_("ed.bad_tree")) from None


def _from_dict_raw(d: dict, z: _Zone, info: dict[int, PartInfo], level: int, grp: Groups) -> _N:
    if not isinstance(d, dict) or level > 40:
        raise ValueError("node")
    kind = d.get("k")
    n = _N(_num(d["x"]) - z.ox, _num(d["y"]) - z.oy, _num(d["l"]), _num(d["w"]), level, kind, axis=d.get("a"))
    if n.l < 0 or n.w < 0:
        raise ValueError("size")
    if kind == "C":
        if n.axis not in ("x", "y"):
            raise EditError(_("ed.bad_axis"))
        kids = d.get("c", [])
        if not isinstance(kids, list):
            raise ValueError("children")
        n.children = [_from_dict_raw(c, z, info, level + 1, grp) for c in kids]
        if d.get("g") is not None:
            # guruh (blok) tuguni: faqat bitta guruhlanadigan detal nusxalari, propil — «для групповых деталей»
            g = _num(d["g"])
            uids = {c.pid[1] for c in n.children if c.kind == "P"}
            if grp is None or level == 0 or abs(g - grp[1]) > TOL or len(uids) != 1 or not uids <= grp[0] \
                    or any(c.kind == "C" for c in n.children):
                raise EditError(_("ed.bad_group"))
            n.gk = g
    elif kind == "P":
        uid = d.get("u")
        pi = info.get(uid) if isinstance(uid, int) else None
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


def _kf(node: Optional[_N], kerf: float) -> float:
    """Tugun bolalari orasidagi propil: guruh (blok) tugunida — guruh propili."""
    return node.gk if node is not None and node.gk is not None else kerf


def _relayout(node: _N, body: list[_N], kerf: float) -> None:
    """Tugun bolalarini o'q bo'yicha zich joylash: body ketma-ket propil bilan, oxirida bitta chiqindi."""
    ax = node.axis
    start = _start(node, ax)
    end = start + _extent(node, ax)
    total = sum(_extent(c, ax) for c in body) + kerf * max(0, len(body) - 1)
    lead = end - total - kerf - start if editor_pack.rev(ax) and body else 0.0
    pos = start + (end - total - start if lead > EPS else 0.0)
    for c in body:
        _move_to(c, ax, pos)
        pos += _extent(c, ax) + kerf
    kids = list(body)
    if lead > EPS:                              # burchak o'ng / past — bo'sh joy boshida
        kids.insert(0, _waste(start, node.y, lead, node.w) if ax == "x" else _waste(node.x, start, node.l, lead))
    rest = end - pos
    if rest > EPS and lead <= EPS:
        w = _waste(pos, node.y, rest, node.w) if ax == "x" else _waste(node.x, pos, node.l, rest)
        kids.append(w)
    node.children = kids


# ───────────────────────── amallar ─────────────────────────
def _fits_in(ax: str, leaf: _N, pi: PartInfo, rot: bool) -> bool:
    """Detal (rot — burilgan) `leaf` bo'sh joyiga sig'adimi (ax — ota tugun o'qi)."""
    ext_a, ext_b = (leaf.l, leaf.w) if ax == "x" else (leaf.w, leaf.l)
    l, w = (pi.w, pi.l) if rot else (pi.l, pi.w)
    a, b = (l, w) if ax == "x" else (w, l)
    return a <= ext_a + TOL and b <= ext_b + TOL


def _place_at(parent: _N, idx: int, pi: PartInfo, rotated: bool, kerf: float) -> tuple[list[_N], _N]:
    """`parent.children[idx]` (chiqindi) o'rniga detal qo'yadi. Qaytaradi: (yangi bolalar [slot, qoldiq?], detal tuguni).
    So'ralgan holatda sig'masa, lekin aylantirilganda sig'sa (tekstura ruxsat bersa) — avtomatik aylantiriladi."""
    leaf = parent.children[idx]
    if leaf.kind != "W":
        raise EditError(_("ed.place_on_waste"))
    if rotated and not pi.can_rotate:
        raise EditError(_("ed.grain_no_rotate", uid=pi.uid))
    ax = parent.axis
    ext_a, ext_b = (leaf.l, leaf.w) if ax == "x" else (leaf.w, leaf.l)
    if not _fits_in(ax, leaf, pi, rotated):
        if pi.can_rotate and _fits_in(ax, leaf, pi, not rotated):
            rotated = not rotated
        else:
            pl0, pw0 = (pi.w, pi.l) if rotated else (pi.l, pi.w)
            raise EditError(_("ed.no_fit", uid=pi.uid, size=f"{pl0:g}×{pw0:g}", free=f"{leaf.l:g}×{leaf.w:g}"))
    pl, pw = (pi.w, pi.l) if rotated else (pi.l, pi.w)
    pa, pb = (pl, pw) if ax == "x" else (pw, pl)
    lvl = leaf.level
    ox = _other(ax)
    ka = _kf(parent, kerf)                 # ota o'qi bo'ylab (guruh tugunida — guruh propili)
    rest_a = ext_a - pa - ka
    rest_b = ext_b - pb - kerf
    # zichlash burchagi (editor_pack): o'ng / past burchakda detal bo'sh joyning oxiriga, bo'sh joy — oldiga
    rev_a, rev_b = editor_pack.rev(ax), editor_pack.rev(ox)
    a0, b0 = _start(leaf, ax), _start(leaf, ox)
    sa = a0 + (rest_a + ka if rev_a and rest_a > EPS else 0.0)            # slot boshi (ota o'qi bo'ylab)
    sb = b0 + (rest_b + kerf if rev_b and rest_b > EPS else 0.0)          # detal boshi (ko'ndalang)

    def xy(a: float, b: float) -> tuple[float, float]:
        return (a, b) if ax == "x" else (b, a)
    px, py = xy(sa, sb)
    part = _N(px, py, pl, pw, lvl, "P", rot=rotated)
    part.pid = (pi.part_id, pi.uid)
    if abs(pb - ext_b) <= TOL:
        slot = part
    else:
        part.level = lvl + 1
        kids = [part]
        if rest_b > EPS:
            wx, wy = xy(sa, b0 if rev_b else b0 + pb + kerf)
            wb = _waste(wx, wy, pl if ax == "x" else rest_b, rest_b if ax == "x" else pw)
            wb.level = lvl + 1
            if rev_b:
                kids.insert(0, wb)
            else:
                kids.append(wb)
        sx, sy = xy(sa, b0)
        slot = _N(sx, sy, pl if ax == "x" else leaf.l, leaf.w if ax == "x" else pw, lvl, "C",
                  axis=ox, children=kids)
    new = [slot]
    if rest_a > EPS:
        wx, wy = xy(a0 if rev_a else a0 + pa + ka, b0)
        wa = _waste(wx, wy, rest_a if ax == "x" else leaf.l, leaf.w if ax == "x" else rest_a)
        wa.level = lvl
        if rev_a:
            new.insert(0, wa)
        else:
            new.append(wa)
    parent.children[idx:idx + 1] = new
    return new, part


def split_for(leaf: _N, l: float, w: float, px: float, py: float) -> str:
    """Kursor bo'yicha birinchi kesim (onlayn tahrirdagidek, Shift bosib turilganda kursor bilan tanlanadi):
    detal bo'sh joy burchagiga qo'yiladi; kursor detalning o'ng chetidan ko'proq o'tgan bo'lsa — «H» (arra pastki chet bo'ylab
    to'liq enda — kursor tomonga yuradi), pastki chetidan ko'proq — «V» (o'ng chet bo'ylab to'liq balandlikda). Foydalanuvchi
    qarori (2026-10-21): kesish tarafi shunday — avvalgi teskari tanlov o'zgartirildi."""
    rx, ry = editor_pack.rev("x"), editor_pack.rev("y")
    dx = (leaf.x + leaf.l - l - px) if rx else (px - (leaf.x + l))
    dy = (leaf.y + leaf.w - w - py) if ry else (py - (leaf.y + w))
    return "H" if dx > dy else "V"


def _place(root: _N, path: list[int], pi: PartInfo, rotated: bool, kerf: float,
           point: Optional[tuple[float, float]] = None) -> None:
    parent, leaf, idx = _node_at(root, path)
    if parent is None or leaf.kind != "W":
        raise EditError(_("ed.place_on_waste"))
    if point is not None:
        l, w = (pi.w, pi.l) if rotated else (pi.l, pi.w)
        natural = "V" if parent.axis == "x" else "H"
        # ikkala tomonda ham bo'sh joy qoladigan bo'lsagina yo'nalish farq qiladi
        if leaf.l - l > kerf + EPS and leaf.w - w > kerf + EPS and split_for(leaf, l, w, *point) != natural:
            wrap = _N(leaf.x, leaf.y, leaf.l, leaf.w, leaf.level, "C", axis=_other(parent.axis), children=[leaf])
            leaf.level += 1
            parent.children[idx] = wrap
            parent, idx = wrap, 0
    _place_at(parent, idx, pi, rotated, kerf)


def free_anchors(leaf: _N, root: _N, l: float, w: float, point: Optional[tuple[float, float]]) -> list[tuple[float, float]]:
    """Bir nechta bo'sh katakdan iborat joyga qo'yishda sinaladigan burchaklar: bosilgan katak burchagi, katak qatori
    bo'ylab list chetlariga tekislangan holatlar va kursor markazi (list ichiga siqilgan)."""
    xs = [leaf.x, leaf.x + leaf.l - l, root.x, root.x + root.l - l]
    ys = [leaf.y, leaf.y + leaf.w - w, root.y, root.y + root.w - w]
    if point is not None:
        xs.append(min(max(point[0] - l / 2, root.x), root.x + root.l - l))
        ys.append(min(max(point[1] - w / 2, root.y), root.y + root.w - w))
    out: list[tuple[float, float]] = []
    for x in xs:
        for y in ys:
            # detal bosilgan katakni qoplashi shart (operator ko'rsatgan joy)
            if x > leaf.x + leaf.l - TOL or x + l < leaf.x + TOL or y > leaf.y + leaf.w - TOL or y + w < leaf.y + TOL:
                continue
            if (x, y) not in out:
                out.append((x, y))
    return out


def _place_free(root: _N, leaf: _N, pi: PartInfo, rotated: bool, kerf: float, max_depth: int,
                point: Optional[tuple[float, float]] = None, zone: Optional[_Zone] = None,
                min_trim: float = 0.0) -> Optional[_N]:
    """Detal bitta bo'sh katakka sig'masa — qo'shni bo'sh kataklar birlashgan joyga (bir nechta polosa oxiridagi umumiy
    bo'sh ustun va h.k.). Boshqa detallar o'z joyida qoladi; kesish daraxti detallarning aniq joylaridan qayta quriladi
    (onlayn tizim muharriridagidek; 2026-10-30, «1275» AKRIL: 3-sokl o'ngdagi umumiy bo'sh ustunga tik). Imkonsiz — None."""
    def grouped(n: _N) -> bool:
        return n.kind == "C" and (n.gk is not None or any(grouped(c) for c in n.children))
    if grouped(root):
        return None               # blok (guruh propili) tuzilmasi koordinatadan tiklanmaydi
    parts = [lf for lf in root.leaves() if lf.kind == "P"]
    opts = [rotated] + ([not rotated] if pi.can_rotate else [])
    for rot in opts:
        l, w = (pi.w, pi.l) if rot else (pi.l, pi.w)
        if l > root.l + TOL or w > root.w + TOL:
            continue
        for x, y in free_anchors(leaf, root, l, w, point):
            if x < root.x - TOL or y < root.y - TOL or x + l > root.x + root.l + TOL or y + w > root.y + root.w + TOL:
                continue
            if any(x < p.x + p.l + kerf - TOL and p.x < x + l + kerf - TOL and
                   y < p.y + p.w + kerf - TOL and p.y < y + w + kerf - TOL for p in parts):
                continue          # boshqa detal bilan ustma-ust yoki orasida propilga joy yo'q
            work = copy.deepcopy(root)
            mine = [lf for lf in work.leaves() if lf.kind == "P"]
            new = _N(x, y, l, w, 0, "P", rot=rot)
            new.pid = (pi.part_id, pi.uid)
            for ax in (root.axis or "x", _other(root.axis or "x")):
                cand = [copy.copy(p) for p in mine] + [copy.copy(new)]
                pos = [(p.x, p.y) for p in cand]
                try:
                    built = editor_pack._build(cand, root.x, root.y, root.l, root.w, ax, kerf)
                except editor_pack.NoRecut:
                    continue
                if any(abs(p.x - q[0]) > TOL or abs(p.y - q[1]) > TOL for p, q in zip(cand, pos)):
                    continue
                probe = _normalize(copy.deepcopy(built))
                if probe is None or _depth(probe) > max_depth:
                    continue
                if zone is not None and _trim_violations(built, zone, min_trim):
                    continue          # ichki qirindi «Минимальная обрезка» dan tor (masalan 1 mm) — kesib bo'lmaydi
                return built
    return None


def _no_new_sliver(before: _N, after: _N, zone: _Zone, min_trim: float) -> None:
    """Detal bo'sh katakka o'lchami bo'yicha sig'sa ham, ortida «Минимальная обрезка» dan tor qirindi qolsa (masalan 1151 mm
    joyga 1150 mm sokl — 1 mm) — kesib bo'lmaydi: EditError, chaqiruvchi keyingi usulga o'tadi (birlashgan joy / list qayta
    joylanadi). Xodim loyihasi «1275», 2026-10-30: shu holatda saqlashda «обрезок 1.0 мм» xatosi chiqardi."""
    if _trim_violations(after, zone, min_trim) > _trim_violations(before, zone, min_trim):
        raise EditError(_("ed.sliver", mt=f"{min_trim:g}"))


def _place_relayout(root: _N, z: _Zone, op: Operation, info: dict[int, PartInfo], pi: PartInfo) -> Optional[_N]:
    """Oxirgi imkoniyat: detal bo'sh joylarga (birlashtirilgan holda ham) sig'masa — shu kartadagi barcha detallar + yangi
    detal SHU listga qayta joylanadi (kesish chiziqlari va detallar o'rni o'zgaradi, hech biri listdan chiqmaydi). Foydalanuvchi
    qoidasi (2026-10-30): kesish chiziqlarini o'zgartirib detal sig'sa — sig'dirilsin. Imkonsiz — None."""
    def grouped(n: _N) -> bool:
        return n.kind == "C" and (n.gk is not None or any(grouped(c) for c in n.children))
    if grouped(root):
        return None
    items = []
    for lf in root.leaves():
        if lf.kind == "P":
            q = info[lf.pid[1]]
            items.append(Item(q.part_id, q.uid, q.l, q.w, q.can_rotate))
    items.append(Item(pi.part_id, pi.uid, pi.l, pi.w, pi.can_rotate))
    need = sum(it.l * it.w for it in items)
    if need > root.l * root.w + EPS:
        return None
    pool = _Pool(items)
    pool.gk = group_kerf(op.cs_cut)
    best = _best_sheet(pool, pool.counts0[:], z, op.cs_cut, _axes_for(op.cs_cut), time.monotonic() + RELAYOUT_S,
                       intensive=True, target_all=True)
    if best is None or sum(best.counts_after) > 0:
        return None
    queues = {s.idx: deque(s.pids) for s in pool.shapes}
    for lf in best.root.leaves():
        if lf.kind == "P":
            lf.pid = queues[lf.s].popleft()
    return best.root


def _leaf_at(root: _N, x: float, y: float) -> Optional[list[int]]:
    """Nuqtani o'z ichiga olgan bo'sh (W) barg manzili; bo'lmasa None."""
    path: list[int] = []
    n = root
    while True:
        hit = next(((i, c) for i, c in enumerate(n.children)
                    if c.x - TOL <= x <= c.x + c.l + TOL and c.y - TOL <= y <= c.y + c.w + TOL), None)
        if hit is None:
            return None
        path.append(hit[0])
        n = hit[1]
        if n.kind == "W":
            return path
        if n.kind != "C":
            return None


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
    _relayout(parent, body, _kf(parent, kerf))


def _index_of(parent: _N, node: _N) -> int:
    """Tugunning ota ichidagi o'rni (obyekt bo'yicha; topilmasa -1)."""
    try:
        return parent.children.index(node)          # _N da __eq__ yo'q — obyekt tengligi
    except ValueError:
        return -1


def _clone(root: _N, path: list[int], kerf: float) -> list[tuple[str, int]]:
    parent, node, idx = _node_at(root, path)
    if parent is None or node.kind == "W":
        raise EditError(_("ed.clone_select"))
    return _clone_in(parent, node, kerf)


def _clone_in(parent: _N, node: _N, kerf: float) -> list[tuple[str, int]]:
    """Tugun nusxasini ota ichidagi (undan keyingi, bo'lmasa — istalgan) yetarli bo'sh joyga qo'yadi."""
    idx = _index_of(parent, node)
    if idx < 0 or node.kind == "W":
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
    kerf = _kf(parent, kerf)
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
            kn = _kf(n, kerf)
            rest = d - kn
            if rest > EPS:
                w = _waste(n.x, n.y, n.l, n.w)
                _move_to(w, ax, end + kn)
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
    d = _extent(w, ax) + _kf(parent, kerf)
    parent.children[idx] = _grow(node, ax, d, kerf)
    parent.children.pop(idx + 1)


def can_narrow(root: _N, path: list[int], kerf: float) -> bool:
    try:
        parent, node, _i = _node_at(root, path)
    except EditError:
        return False
    if parent is None or node.kind != "C" or not editor_pack.has_parts(node):
        return False
    ax = parent.axis
    return _extent(node, ax) - editor_pack.need(node, ax, kerf) > kerf + EPS


def _narrow(root: _N, path: list[int], kerf: float) -> None:
    """«Сузить полосу» (lokal yordamdagi Ctrl+Q): polosa ichidagi detallar o'lchamigacha toraytiriladi, ortgan joy — undan keyin
    alohida bo'sh polosa (keyingi bo'sh joy bilan birlashadi). Detallar polosa ichida burchakka zichlanadi."""
    parent, node, idx = _node_at(root, path)
    if parent is None or node.kind != "C":
        raise EditError(_("ed.narrow_select"))
    ax = parent.axis
    need = editor_pack.need(node, ax, kerf)
    cur = _extent(node, ax)
    if cur - need <= kerf + EPS:
        raise EditError(_("ed.narrow_none"), code="narrow_none")
    a0 = _start(node, ax)
    x, y, l, w = (a0, node.y, need, node.w) if ax == "x" else (node.x, a0, node.l, need)
    new = editor_pack.lay(node, x, y, l, w, _kf(parent, kerf))
    rest = cur - need - _kf(parent, kerf)
    kids = [new]
    if rest > EPS:
        ws = a0 + need + _kf(parent, kerf)
        kids.append(_waste(ws, node.y, rest, node.w) if ax == "x" else _waste(node.x, ws, node.l, rest))
    parent.children[idx:idx + 1] = kids


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
    cut = op.cs_cut.model_copy(update={"max_rotations": max(1, op.cs_cut.max_rotations - depth_used)})
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
    max_depth = max(1, cut.max_rotations)       # detal darajasi = burilish raqami ≤ «Макс. количество вращений»
    grp = op_groups(op)
    for m in res.maps:
        st = stock.get(m.sheet_id)
        if st is None:
            raise EditError(_("ed.sheet_missing", map=m.index))
        if not m.strips:
            raise EditError(_("ed.no_tree", map=m.index))
        z = _zone(map_stock(st, m), cut)           # karta torsovkasi (W13) list qatoridagisidan ustun
        root = _from_dict(m.strips[0], z, info, grp=grp)
        _check_root(root, z, m.index)
        root = _normalize(root)
        if root is None:
            raise EditError(_("ed.tree_empty", map=m.index))
        if _depth(root) > max_depth:
            raise EditError(_("ed.too_deep", map=m.index, d=_depth(root), m=max(1, cut.max_rotations)))
        nm = _build_map(_Sheet(z, root, 0.0, []), len(maps) + 1, cut, mat, counter, {})
        nm.copies = max(1, int(m.copies))
        nm.comment = m.comment[:COMMENT_MAX]
        nm.pack_corner = m.pack_corner
        nm.done_count = min(m.done_count, nm.copies)
        for k in TRIM_KEYS:                          # karta torsovkasi saqlanadi
            setattr(nm, k, getattr(m, k))
        maps.append(nm)
    out = CuttingResult(maps=maps, variant=res.variant, manual=True, elapsed_s=res.elapsed_s,
                        warnings=list(res.warnings))
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
    _carry_taken(out, res)
    errs = validate(out, _items_for(project, op, cut), op.sheets, cut)
    if errs:
        raise EditError(errs[0], errs)
    return out


def _carry_taken(out: CuttingResult, src: CuttingResult) -> None:
    """«Исп. кол-во» (mijoz olib ketgan qoldiqlar) tahrirdan keyin ham saqlanadi: faqat hali mavjud qoldiq guruhlari
    uchun va ularning sonidan oshmaydigan miqdorda (qoldiq o'lchami o'zgargan bo'lsa — eskirgan kalit tashlanadi)."""
    if not src.taken_remnants:
        return
    from .warehouse import rem_key
    qty: Counter = Counter()
    for m in out.maps:
        for o in m.offcuts:
            if o.kind == "remnant":
                qty[rem_key(o.business, o.length, o.width)] += m.copies
    keep = {}
    for k, v in src.taken_remnants.items():
        try:
            n = min(qty.get(k, 0), max(0, int(v)))
        except (TypeError, ValueError, OverflowError):
            continue
        if n > 0:
            keep[k] = n
    out.taken_remnants = keep


def _check_root(root: _N, z: _Zone, map_no: int) -> None:
    """Daraxt ildizi listning foydali zonasidan chiqmasin (soxta/eskirgan daraxt detalni torsovka joyiga qo'ya olmaydi)."""
    if root.x < -TOL or root.y < -TOL or root.x + root.l > z.UL + TOL or root.y + root.w > z.UW + TOL:
        raise EditError(_("ed.root_out", map=map_no))


def apply(project: Project, op: Operation, res: CuttingResult, action: dict) -> CuttingResult:
    """Bitta tahrir amali. Xato bo'lsa EditError (qoralama o'zgarmaydi). Noto'g'ri parametrlar — EditError."""
    if not isinstance(action, dict):
        raise EditError(_("ed.bad_action", a=type(action).__name__))
    tok = editor_pack.REV.set(editor_pack.corner_rev(_map_corner(res, action)))
    tok2 = editor_pack.MIN_TRIM.set(float(op.cs_cut.min_trim_cut or 0.0) if op.cs_cut else 0.0)
    try:
        return _apply(project, op, res, action)
    except EditError:
        raise
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError):
        raise EditError(_("ed.bad_action", a=str(action.get("type"))[:40])) from None
    finally:
        editor_pack.MIN_TRIM.reset(tok2)
        editor_pack.REV.reset(tok)


def default_corner() -> str:
    """Umumiy sozlama «Угол уплотнения раскроя» (app.edit_pack_corner); o'qib bo'lmasa — LT (onlayn tizimdagidek)."""
    try:
        from . import settings
        c = settings.get_default("app").get("edit_pack_corner")
    except Exception:          # noqa: BLE001 — sozlamalar bazasi yo'q (test / migratsiya) — standart
        c = None
    return c if c in editor_pack.CORNERS else "LT"


def _map_corner(res: CuttingResult, action: dict) -> str:
    """Amal uchun burchak: `pack_corner` amalida — yangi qiymat; aks holda kartaning o'zi yoki umumiy sozlama."""
    try:
        if action.get("type") == "pack_corner":
            c = action.get("corner")
            return c if c in editor_pack.CORNERS else default_corner()
        i = int(action.get("map", 0))
        m = res.maps[i - 1] if i >= 1 else None
    except (TypeError, ValueError, IndexError, AttributeError, OverflowError):
        m = None
    c = getattr(m, "pack_corner", None)
    return c if c in editor_pack.CORNERS else default_corner()


def _apply(project: Project, op: Operation, res: CuttingResult, action: dict) -> CuttingResult:
    res = res.model_copy(deep=True)
    kind = action.get("type")
    cut = op.cs_cut
    kerf = cut.kerf
    info = part_info(project, op)
    stock = {s.id: s for s in op.sheets}

    if kind == "add_map":
        sid = action.get("sheet_id")
        st = (stock.get(sid) if isinstance(sid, str) else None) or (op.sheets[0] if op.sheets else None)
        if st is None:
            raise EditError(_("ed.no_sheet"))
        z = _zone(st, cut)
        if z.UL <= 0 or z.UW <= 0:
            raise EditError(_("ed.sheet_small"))
        axis = action.get("axis") if action.get("axis") in ("x", "y") else "y"
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
        m.copies = max(1, min(100_000, int(action.get("copies", 1))))
        return rebuild(project, op, res)
    if kind in W13_MAP_KINDS:                       # karta darajasidagi amallar (daraxtga tegmaydi)
        from . import editor_w13
        return editor_w13.apply_map_kind(project, op, res, mi, kind, action)

    st = stock.get(m.sheet_id)
    if st is None:
        raise EditError(_("ed.no_sheet"))
    z = _zone(map_stock(st, m), cut)
    if not m.strips:
        raise EditError(_("ed.no_tree", map=mi + 1))
    root = _from_dict(m.strips[0], z, info, grp=op_groups(op))
    _check_root(root, z, mi + 1)
    multi = action.get("paths")
    paths = clean_paths(multi) if multi is not None else [clean_path(action.get("path", []))]
    path = paths[0] if paths else []

    def remaining(uid: int) -> int:
        pi = info[uid]
        used = sum(mm.copies for mm in res.maps for pl in mm.placements if pl.part_id == pi.part_id)
        return pi.need - used

    if kind in W13_TREE_KINDS or (kind in W13_MULTI_KINDS and len(paths) != 1):
        from . import editor_w13
        return editor_w13.apply_tree(editor_w13.Ctx(project, op, res, mi, m, root, z, info, kerf, remaining),
                                     kind, action, paths)
    if kind in ("place", "place_auto"):
        uid = int(action.get("uid", 0))
        pi = info.get(uid)
        if pi is None:
            raise EditError(_("part_uid_not_found", uid=uid))
        if remaining(uid) < m.copies:
            raise EditError(_("ed.none_left", uid=uid, c=m.copies))
        if kind == "place":
            pt = (float(action["x"]) - z.ox, float(action["y"]) - z.oy) if "x" in action and "y" in action else None
            rot = bool(action.get("rotated", False))
            try:
                work = copy.deepcopy(root)          # _place xato bersa ham daraxtni o'zgartirib ulgurishi mumkin
                _place(work, path, pi, rot, kerf, pt)
                _no_new_sliver(root, work, z, cut.min_trim_cut)
                root = work
            except EditError:
                # bitta katakka sig'madi — qo'shni bo'sh kataklar birlashgan joy (polosalar oxiridagi umumiy ustun)
                _parent, leaf, _idx = _node_at(root, path)
                if leaf.kind != "W":
                    raise
                new_root = _place_free(root, leaf, pi, rot, kerf, max(1, cut.max_rotations), pt, z, cut.min_trim_cut)
                if new_root is None:
                    new_root = _place_relayout(root, z, op, info, pi)
                if new_root is None:
                    raise
                root = new_root
        else:
            rot = action.get("rotated")
            try:
                work = copy.deepcopy(root)
                _place_auto(work, pi, None if rot is None else bool(rot), kerf)
                _no_new_sliver(root, work, z, cut.min_trim_cut)
                root = work
            except EditError:
                new_root = _place_relayout(root, z, op, info, pi)       # bo'sh joylarga sig'masa — list qayta joylanadi
                if new_root is None:
                    raise
                root = new_root
    elif kind == "remove":
        _remove(root, path)
        out = try_compacted(project, op, res, mi, root, z, kerf)
        if out is not None:
            return out
    elif kind == "pack_corner":
        c = action.get("corner")
        if c is not None and c not in editor_pack.CORNERS:
            raise EditError(_("ed.bad_action", a="pack_corner"))
        m.pack_corner = c
        root = editor_pack.compact(root, kerf)
    elif kind == "relocate":
        # Shift + sudrash: kartadagi detalni bo'sh joyga ko'chirish — tushirilgan nuqtadagi chiqindining burchagiga
        # (kesish chizig'iga tekislanadi); `rotated` — yangi joydagi holati (Ctrl bilan almashtiriladi)
        _parent, node, _idx = _node_at(root, path)
        if node.kind != "P" or node.pid is None:
            raise EditError(_("ed.relocate_part"))
        pi = info[node.pid[1]]
        rot = bool(action.get("rotated", node.rot))
        _remove(root, path)
        qx, qy = float(action["x"]) - z.ox, float(action["y"]) - z.oy       # list → zona koordinatalari
        tpath = _leaf_at(root, qx, qy)
        if tpath is None:
            raise EditError(_("ed.place_on_waste"))
        try:
            work = copy.deepcopy(root)
            _place(work, tpath, pi, rot, kerf, (qx, qy))
            _no_new_sliver(root, work, z, cut.min_trim_cut)
            root = work
        except EditError:
            _parent, leaf, _idx = _node_at(root, tpath)
            new_root = _place_free(root, leaf, pi, rot, kerf, max(1, cut.max_rotations), (qx, qy), z, cut.min_trim_cut)
            if new_root is None:
                raise
            root = new_root
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
    elif kind == "narrow":
        _narrow(root, path, kerf)
    elif kind == "rotate":
        # onlayn tizimdagidek: detallar joyida, faqat kesish tartibi almashadi; bo'lmasa — operator roziligi bilan
        # (`mode: "relayout"`) hudud boshqa yo'nalishda qayta kesiladi (detallar o'rni o'zgaradi)
        new_root = editor_pack.rotate_cuts(root, path, kerf, max(1, cut.max_rotations))
        if new_root is None:
            if action.get("mode") != "relayout":
                raise EditError(_("ed.rotate_keep"), code="rotate_keep")
            new_root = _rotate(root, path, z, op, info, _depth_of(path))
        root = new_root
    else:
        raise EditError(_("ed.bad_action", a=kind))
    return commit_tree(project, op, res, m, root, z)


def try_compacted(project: Project, op: Operation, res: CuttingResult, mi: int, root: _N, z: _Zone,
                  kerf: float) -> Optional[CuttingResult]:
    """O'chirishdan keyin karta burchakka zichlanadi (onlayn tizimdagidek). Zichlangan holat tekshiruvdan o'tmasa (masalan,
    minimal obrezkadan yupqa qirindi) — None: chaqiruvchi zichlamasdan saqlaydi (o'chirish hech qachon rad etilmasin)."""
    trial = res.model_copy(deep=True)
    try:
        return commit_tree(project, op, trial, trial.maps[mi], editor_pack.compact(copy.deepcopy(root), kerf), z)
    except EditError:
        return None


def commit_tree(project: Project, op: Operation, res: CuttingResult, m: CutMap, root: _N, z: _Zone) -> CuttingResult:
    """Daraxtni karta ichiga yozadi va butun natijani qayta quradi + tekshiradi (`rebuild`)."""
    root = _normalize(root)
    if root is None:
        raise EditError(_("ed.map_empty"))
    m.strips = [_ser(root, z)]
    return rebuild(project, op, res)


# W13: yangi amal turlari (services/editor_w13.py)
W13_MAP_KINDS = ("move_map", "comment")
W13_TREE_KINDS = ("place_multi", "expand_block", "flip", "replace", "swap", "map_trim")
W13_MULTI_KINDS = ("remove", "move", "clone", "rotate")          # `paths` (ko'p tanlash) bilan


def clean_path(raw) -> list[int]:
    """Manzil: butun sonlar ro'yxati (bool emas), uzunligi chegaralangan; aks holda EditError (500 emas)."""
    if not isinstance(raw, list) or len(raw) > MAX_PATH_DEPTH + 1 \
            or not all(isinstance(i, int) and not isinstance(i, bool) for i in raw):
        raise EditError(_("ed.node_missing"))
    return list(raw)


def clean_paths(raw, limit: int = 50_000) -> list[list[int]]:
    """Ko'p tanlash: manzillar ro'yxati — takrorsiz; tanlangan tugunning avlodi alohida hisoblanmaydi."""
    if not isinstance(raw, list) or len(raw) > limit:
        raise EditError(_("ed.sel_too_many", n=limit))
    seen = set()
    for p in raw:
        seen.add(tuple(clean_path(p)))
    keep = [t for t in seen if not any(t[:k] in seen for k in range(len(t)))]      # ota-tugun ham tanlangan bo'lsa — tashlanadi
    return [list(t) for t in sorted(keep)]                                          # hujjat tartibida
