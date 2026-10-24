"""W13 — CSE (Редактирование раскроя) rejimlari: ko'p tanlash, ko'p qo'yish (Shift+A), blok bilan kengaytirish
(Shift+W), kartaga alohida torsovka («Торцовка листа»), kartalar tartibi (Ctrl+↑/↓), detalni burish/almashtirish.

Hammasi `editor.py` daraxt primitivlari ustida toza funksiyalar: kirish — qoralama natija + amal, chiqish — YANGI
natija (`editor.rebuild` bilan to'liq qayta qurilgan va `validate()` dan o'tgan) yoki `EditError`. Qoralama o'zgarmaydi.
Har amalning tekshiruvi: kesish darajasi ≤ «Макс. количество вращений», propil, minimal obrezka, detallar soni,
tekstura — `rebuild` ichida; bu modul faqat daraxtni o'zgartiradi va eng ko'p mos soni topadi.

Eslatma: o'rin almashadigan amallar manzillar (path) o'rniga tugun OBYEKTLARI bilan ishlaydi — bir nechta tugun
tanlanganda birinchi o'zgarish keyingilarining manzilini buzmasin.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Optional

from ..i18n import _
from ..models import CuttingResult, CutMap, Operation, Project
from .editor import (COMMENT_MAX, EditError, PartInfo, TOL, _clone_in, _fits_in, _grow, _index_of, _kf, _move_to,
                     _node_at, _place_at, _relayout, _rotate, _set_extent, _start, _waste, commit_tree, rebuild)
from .optimizer import EPS, _extent, _N, _Zone, _zone
from .validate import TRIM_KEYS, map_stock
from . import editor_pack

MAX_FILL = 5000                 # bitta «ko'p qo'yish» / «blok kengaytirish» bosishida eng ko'p nusxa
MAX_ROTATE_REGIONS = 10         # bir vaqtda qayta kesiladigan hududlar soni (har biri qidiruv)
MAX_TRIM = 500.0                # torsovka chegarasi (modeldagi bilan bir xil)
ATTEMPTS = 8                    # qirindi qoidasi buzilsa — nusxalar sonini kamaytirib qayta urinishlar


@dataclass
class Ctx:
    """Bitta amalning ish konteksti (editor._apply tuzadi)."""
    project: Project
    op: Operation
    res: CuttingResult              # qoralamaning NUSXASI (amal uni o'zgartirishi mumkin)
    mi: int                         # karta indeksi (0 dan)
    m: CutMap
    root: _N                        # shu kartaning daraxti (zona koordinatalarida)
    z: _Zone
    info: dict[int, PartInfo]
    kerf: float
    remaining: Callable[[int], int]

    @property
    def max_depth(self) -> int:
        return max(1, self.op.cs_cut.max_rotations)

    @property
    def copies(self) -> int:
        return max(1, int(self.m.copies))


def result_rev(res: Optional[CuttingResult]) -> str:
    """Natijaning «izi» (parallel tahrirni aniqlash): kartalar tuzilmasi, nusxalar, izohlar, torsovka, omborga yozilganligi.
    Sexdagi `done_count` (MES kuzatuvi) kirmaydi — u tahrirni to'sib qo'ymasin."""
    if res is None:
        return "none"
    h = hashlib.sha1()
    for m in res.maps:
        h.update(json.dumps([m.sheet_id, m.copies, m.comment, m.strips, [getattr(m, k) for k in TRIM_KEYS]],
                            sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))
    h.update(f"|{len(res.maps)}|{len(res.unplaced)}|{int(bool(res.remnants_saved))}".encode())
    return h.hexdigest()[:16]


# ───────────────────────── karta darajasidagi amallar ─────────────────────────
def apply_map_kind(project: Project, op: Operation, res: CuttingResult, mi: int, kind: str, action: dict) -> CuttingResult:
    """move_map, comment — daraxtga tegmaydigan amallar."""
    maps = res.maps
    n = len(maps)
    if kind == "move_map":
        to = action.get("to")
        j = {"up": mi - 1, "down": mi + 1, "first": 0, "last": n - 1}.get(to) if isinstance(to, str) else None
        if j is None:
            raise EditError(_("ed.bad_dir", d=str(to)[:20]))
        if not (0 <= j < n) or j == mi:
            raise EditError(_("ed.map_edge"))
        maps.insert(j, maps.pop(mi))
    elif kind == "comment":
        c = action.get("comment", "")
        if not isinstance(c, str):
            raise EditError(_("ed.bad_action", a="comment"))
        maps[mi].comment = c[:COMMENT_MAX]
    else:
        raise EditError(_("ed.bad_action", a=str(kind)[:40]))
    return rebuild(project, op, res)


# ───────────────────────── daraxt darajasidagi amallar ─────────────────────────
def apply_tree(ctx: Ctx, kind: str, action: dict, paths: list[list[int]]) -> CuttingResult:
    if kind == "remove":
        remove_many(ctx, paths)
        from .editor import try_compacted
        out = try_compacted(ctx.project, ctx.op, ctx.res, ctx.mi, ctx.root, ctx.z, ctx.kerf)   # onlayn tizimdagidek: zichlash
        if out is not None:
            return out
    elif kind == "move":
        move_many(ctx, paths, str(action.get("to", "end")))
    elif kind == "clone":
        clone_many(ctx, paths)
    elif kind == "rotate":
        rotate_many(ctx, paths, str(action.get("mode", "keep")))
    elif kind == "swap":
        swap(ctx, paths)
    elif kind == "flip":
        flip(ctx, paths)
    elif kind == "replace":
        replace(ctx, _one(paths), action)
    elif kind == "place_multi":
        return place_multi(ctx, _one(paths), action)
    elif kind == "expand_block":
        return expand_block(ctx, _one(paths))
    elif kind == "map_trim":
        return map_trim(ctx, action)
    else:
        raise EditError(_("ed.bad_action", a=str(kind)[:40]))
    return commit_tree(ctx.project, ctx.op, ctx.res, ctx.m, ctx.root, ctx.z)


def _one(paths: list[list[int]]) -> list[int]:
    if len(paths) != 1:
        raise EditError(_("ed.node_missing"))
    return paths[0]


def _resolve(root: _N, paths: list[list[int]]) -> list[tuple[Optional[_N], _N]]:
    """Manzillar → (ota, tugun) obyektlari (o'zgarishdan OLDIN, shunda indekslar siljishi xalaqit bermaydi)."""
    if not paths:
        raise EditError(_("ed.multi_none"))
    out = []
    for p in paths:
        parent, node, _i = _node_at(root, p)
        out.append((parent, node))
    return out


# ── ko'p tanlash: o'chirish / ko'chirish / nusxalash / qayta kesish ──
def remove_many(ctx: Ctx, paths: list[list[int]]) -> None:
    for parent, node in _resolve(ctx.root, paths):
        w = _waste(node.x, node.y, node.l, node.w)
        if parent is None:
            ctx.root.children = [w]
        else:
            parent.children[_index_of(parent, node)] = w


def _bubble(body: list[_N], picked: set[int], step: int) -> None:
    if step < 0:
        for i in range(1, len(body)):
            if id(body[i]) in picked and id(body[i - 1]) not in picked:
                body[i - 1], body[i] = body[i], body[i - 1]
    else:
        for i in range(len(body) - 2, -1, -1):
            if id(body[i]) in picked and id(body[i + 1]) not in picked:
                body[i + 1], body[i] = body[i], body[i + 1]


def move_many(ctx: Ctx, paths: list[list[int]], to: str) -> None:
    """Tanlangan tugunlarni (har ota ichida bir blok sifatida, nisbiy tartibi saqlanib) boshiga/oxiriga/bir qadam."""
    if to not in ("start", "end", "prev", "next"):
        raise EditError(_("ed.bad_dir", d=to[:20]))
    groups: dict[int, tuple[_N, list[_N]]] = {}
    for parent, node in _resolve(ctx.root, paths):
        if parent is None:
            raise EditError(_("ed.root_move"))
        if node.kind == "W":
            raise EditError(_("ed.waste_move"))
        groups.setdefault(id(parent), (parent, []))[1].append(node)
    for parent, nodes in groups.values():
        picked = {id(n) for n in nodes}
        body = [c for c in parent.children if c.kind != "W"]
        sel = [c for c in body if id(c) in picked]
        rest = [c for c in body if id(c) not in picked]
        if to == "start":
            body = sel + rest
        elif to == "end":
            body = rest + sel
        else:
            _bubble(body, picked, -1 if to == "prev" else 1)
        _relayout(parent, body, _kf(parent, ctx.kerf))


def clone_many(ctx: Ctx, paths: list[list[int]]) -> None:
    cnt: Counter = Counter()
    for parent, node in _resolve(ctx.root, paths):
        if parent is None or node.kind == "W":
            raise EditError(_("ed.clone_select"))
        for _pid, uid in _clone_in(parent, node, ctx.kerf):
            cnt[uid] += 1
    for uid, n in cnt.items():
        if ctx.remaining(uid) < n * ctx.copies:
            raise EditError(_("ed.clone_parts", uid=uid, n=ctx.remaining(uid)))


def rotate_many(ctx: Ctx, paths: list[list[int]], mode: str = "keep") -> None:
    if not paths:
        raise EditError(_("ed.multi_none"))
    if len(paths) > MAX_ROTATE_REGIONS:
        raise EditError(_("ed.rotate_many", n=MAX_ROTATE_REGIONS))
    root = ctx.root
    for p in paths:               # almashtirish o'rnida (indeks saqlanadi) — qolgan manzillar yaroqli qoladi
        new_root = editor_pack.rotate_cuts(root, p, ctx.kerf, ctx.max_depth)
        if new_root is None:
            if mode != "relayout":
                raise EditError(_("ed.rotate_keep"), code="rotate_keep")
            new_root = _rotate(root, p, ctx.z, ctx.op, ctx.info, len(p))
        root = new_root
    ctx.root = root


def swap(ctx: Ctx, paths: list[list[int]]) -> None:
    """Bitta polosadagi ikki elementning o'rnini almashtirish (jami o'lcham o'zgarmaydi — doim sig'adi)."""
    if len(paths) != 2:
        raise EditError(_("ed.swap_two"))
    (pa, a), (pb, b) = _resolve(ctx.root, paths)
    if pa is None or pa is not pb or a.kind == "W" or b.kind == "W":
        raise EditError(_("ed.swap_two"))
    body = [c for c in pa.children if c.kind != "W"]
    i, j = _index_of_in(body, a), _index_of_in(body, b)
    body[i], body[j] = b, a
    _relayout(pa, body, _kf(pa, ctx.kerf))


def _index_of_in(lst: list[_N], node: _N) -> int:
    for i, c in enumerate(lst):
        if c is node:
            return i
    raise EditError(_("ed.node_missing"))


# ── detalni burish / almashtirish ──
def _reseat(ctx: Ctx, parent: _N, node: _N, pi: PartInfo, prefer: bool, only_pref: bool, err: str) -> None:
    """`node` (joylashgan detal) o'rniga `pi` detalini xuddi shu boshlanish nuqtasidan qo'yadi (undan keyingi bo'sh
    joy ham ishlatiladi). Faqat sig'sa va kesish darajasi chegarasidan oshmasa; aks holda EditError."""
    idx = _index_of(parent, node)
    if idx < 0:
        raise EditError(_("ed.node_missing"))
    ax = parent.axis
    w = _waste(node.x, node.y, node.l, node.w)
    w.level = node.level
    nxt = parent.children[idx + 1] if idx + 1 < len(parent.children) else None
    merged = nxt is not None and nxt.kind == "W"
    if merged:
        if ax == "x":
            w.l = nxt.x + nxt.l - w.x
        else:
            w.w = nxt.y + nxt.w - w.y
    old = parent.children[idx:idx + 2] if merged else parent.children[idx:idx + 1]
    parent.children[idx:idx + len(old)] = [w]
    cands = [prefer] if only_pref else ([prefer, not prefer] if pi.can_rotate else [False])
    for rot in cands:
        if rot and not pi.can_rotate:
            continue
        if not _fits_in(ax, w, pi, rot):
            continue
        l, ww = (pi.w, pi.l) if rot else (pi.l, pi.w)
        pb = ww if ax == "x" else l
        ext_b = w.w if ax == "x" else w.l
        if abs(pb - ext_b) > TOL and (w.level + 1 > ctx.max_depth or parent.gk is not None):
            continue
        _place_at(parent, idx, pi, rot, ctx.kerf)
        return
    pl, pw = (pi.w, pi.l) if prefer else (pi.l, pi.w)
    raise EditError(_(err, uid=pi.uid, size=f"{pl:g}×{pw:g}", free=f"{w.l:g}×{w.w:g}"))


def flip(ctx: Ctx, paths: list[list[int]]) -> None:
    """Joylashgan detalni 90° buradi (tekstura ruxsat bersa va yangi holatda joyiga sig'sa)."""
    for parent, node in _resolve(ctx.root, paths):
        if parent is None or node.kind != "P" or node.pid is None:
            raise EditError(_("ed.flip_select"))
        if parent.gk is not None:
            raise EditError(_("ed.flip_group"))
        pi = ctx.info[node.pid[1]]
        if not pi.can_rotate:
            raise EditError(_("ed.grain_no_rotate", uid=pi.uid))
        if abs(pi.l - pi.w) <= TOL:
            raise EditError(_("ed.flip_square"))
        _reseat(ctx, parent, node, pi, not node.rot, True, "ed.flip_nofit")


def replace(ctx: Ctx, path: list[int], action: dict) -> None:
    """Joylashgan detalni boshqa detal (uid) bilan almashtirish: yangi detal shu joyga sig'sa."""
    parent, node, _i = _node_at(ctx.root, path)
    if parent is None or node.kind != "P" or node.pid is None:
        raise EditError(_("ed.replace_select"))
    if parent.gk is not None:
        raise EditError(_("ed.flip_group"))
    uid = int(action.get("uid", 0))
    pi = ctx.info.get(uid)
    if pi is None:
        raise EditError(_("part_uid_not_found", uid=uid))
    if uid == node.pid[1]:
        raise EditError(_("ed.replace_same"))
    if ctx.remaining(uid) < ctx.copies:
        raise EditError(_("ed.none_left", uid=uid, c=ctx.copies))
    rot = action.get("rotated")
    prefer = bool(node.rot) if rot is None else bool(rot)
    if prefer and not pi.can_rotate:
        if rot is not None:
            raise EditError(_("ed.grain_no_rotate", uid=uid))
        prefer = False
    _reseat(ctx, parent, node, pi, prefer, rot is not None, "ed.replace_nofit")


# ── ko'p qo'yish (Shift+A) va blok kengaytirish (Shift+W) ──
def _descent(n: int) -> list[int]:
    ks = list(range(n, max(0, n - ATTEMPTS), -1))
    if ks and ks[-1] != 1:
        ks.append(1)
    return ks


def _search(ctx: Ctx, n_max: int, strict: bool, make_root: Callable[[int], _N]) -> CuttingResult:
    """`make_root(k)` — k nusxa qo'yilgan daraxt (yangi nusxada). Qirindi qoidasi (minimal obrezka) buzilsa —
    nusxalar soni 1 tadan kamaytirib qayta uriniladi (strict — aniq son so'ralgan: xato qaytariladi)."""
    last: Optional[EditError] = None
    for k in ([n_max] if strict else _descent(n_max)):
        res = ctx.res.model_copy(deep=True)
        try:
            return commit_tree(ctx.project, ctx.op, res, res.maps[ctx.mi], make_root(k), ctx.z)
        except EditError as e:
            last = e
    raise last if last is not None else EditError(_("ed.bad_action", a="search"))


def _fill_free(parent: _N, leaf: _N, pi: PartInfo, rotated: bool, kerf: float, limit: int, max_depth: int) -> int:
    """Bo'sh joyni detal nusxalari bilan to'ldiradi: avval ustun (ko'ndalang qoldiq), keyin o'q bo'ylab. Qaytaradi — soni."""
    placed = 0
    stack: list[tuple[_N, _N]] = [(parent, leaf)]
    orient = rotated
    geom_ok = False
    while stack and placed < limit:
        par, lf = stack.pop()
        idx = _index_of(par, lf)
        if idx < 0 or lf.kind != "W":
            continue
        ax = par.axis
        chosen = None
        for rot in [orient] + ([not orient] if pi.can_rotate else []):
            if not _fits_in(ax, lf, pi, rot):
                continue
            geom_ok = True
            l, w = (pi.w, pi.l) if rot else (pi.l, pi.w)
            pb = w if ax == "x" else l
            ext_b = lf.w if ax == "x" else lf.l
            if abs(pb - ext_b) > TOL and (lf.level + 1 > max_depth or par.gk is not None):
                continue                                  # ichma-ich daraja kerak, lekin chegaradan oshadi
            chosen = rot
            break
        if chosen is None:
            continue
        new, _part = _place_at(par, idx, pi, chosen, kerf)
        placed += 1
        orient = chosen
        if len(new) > 1:
            stack.append((par, new[1]))                   # o'q bo'ylab davomi
        slot = new[0]
        if slot.kind == "C" and len(slot.children) > 1:
            stack.append((slot, slot.children[1]))        # ustun ichidagi qoldiq — birinchi to'ldiriladi
    if placed == 0:
        pl, pw = (pi.w, pi.l) if rotated else (pi.l, pi.w)
        if geom_ok:
            raise EditError(_("ed.place_depth", uid=pi.uid))
        raise EditError(_("ed.no_fit", uid=pi.uid, size=f"{pl:g}×{pw:g}", free=f"{leaf.l:g}×{leaf.w:g}"))
    return placed


def place_multi(ctx: Ctx, path: list[int], action: dict) -> CuttingResult:
    """Shift+A: tanlangan bo'sh joyga detalning ketma-ket ko'p nusxasi (qolgan soni va joy yetguncha; `count` — aniq son)."""
    uid = int(action.get("uid", 0))
    pi = ctx.info.get(uid)
    if pi is None:
        raise EditError(_("part_uid_not_found", uid=uid))
    left = ctx.remaining(uid) // ctx.copies
    if left < 1:
        raise EditError(_("ed.none_left", uid=uid, c=ctx.copies))
    cnt = action.get("count")
    strict = cnt is not None
    want = left
    if strict:
        want = int(cnt)
        if not (1 <= want <= MAX_FILL):
            raise EditError(_("ed.count_range", n=MAX_FILL))
        if want > left:
            raise EditError(_("ed.none_left", uid=uid, c=ctx.copies))
    want = min(want, MAX_FILL)
    rotated = bool(action.get("rotated", False))
    if rotated and not pi.can_rotate:
        raise EditError(_("ed.grain_no_rotate", uid=uid))
    parent, leaf, _i = _node_at(ctx.root, path)
    if parent is None or leaf.kind != "W":
        raise EditError(_("ed.place_on_waste"))

    def make(k: int) -> _N:
        root = copy.deepcopy(ctx.root)
        par, lf, _j = _node_at(root, path)
        _fill_free(par, lf, pi, rotated, ctx.kerf, k, ctx.max_depth)
        return root

    root0 = copy.deepcopy(ctx.root)
    par0, lf0, _j = _node_at(root0, path)
    n_max = _fill_free(par0, lf0, pi, rotated, ctx.kerf, want, ctx.max_depth)
    if strict and n_max < want:
        raise EditError(_("ed.multi_fit", n=n_max, k=want))
    return _search(ctx, n_max, strict, make)


def _chain(root: _N, path: list[int]) -> list[_N]:
    """Ildizdan `path` dagi tugungacha bo'lgan tugunlar zanjiri."""
    out = [root]
    node = root
    for i in path:
        node = node.children[i]
        out.append(node)
    return out


def _room_levels(chain: list[_N], d: str) -> list[tuple[int, float]]:
    """Zanjirdagi har bir daraja uchun: (daraja, undan keyingi bo'sh joy uzunligi) — faqat ota o'qi `d` bo'lgan va tugundan
    keyin chiqindi turgan darajalar. Pastdan (blokka eng yaqin) yuqoriga."""
    out = []
    for lvl in range(len(chain) - 1, 0, -1):
        parent, node = chain[lvl - 1], chain[lvl]
        if parent.axis != d:
            continue
        j = _next_free(parent, node)
        if j is not None:
            out.append((lvl, _extent(parent.children[j], d)))
    return out


def _next_free(parent: _N, node: _N) -> Optional[int]:
    """`node` dan keyingi birinchi chiqindi (bo'sh joy) ning ota ichidagi indeksi; yo'q bo'lsa None."""
    i = _index_of(parent, node)
    if i < 0:
        return None
    return next((j for j in range(i + 1, len(parent.children)) if parent.children[j].kind == "W"), None)


def _grow_down(nodes: list[_N], d: str, delta: float, kerf: float) -> None:
    """`nodes` (ketma-ket ajdod → avlod) `d` o'qi bo'yicha delta ga kengayadi: o'q bo'ylab ketgan bolalarda keyingilar
    siljiydi, ko'ndalang bolalarda hammasi kengayadi (oxiridagi chiqindi kattalashadi)."""
    for k, n in enumerate(nodes):
        _set_extent(n, d, _extent(n, d) + delta)
        if k == len(nodes) - 1:
            break
        nxt = nodes[k + 1]
        if n.axis == d:
            i = _index_of(n, nxt)
            for c in n.children[i + 1:]:
                _move_to(c, d, _start(c, d) + delta)
        else:
            for i, c in enumerate(n.children):
                if c is not nxt:
                    n.children[i] = _grow(c, d, delta, kerf)


def _extend_chain(root: _N, tpath: list[int], d: str, delta: float, kerf: float) -> None:
    """`tpath` dagi tugun (blok konteyneri) va uning ajdodlarini `d` o'qi bo'yicha delta ga kengaytiradi: eng pastki
    (blokka yaqin) shunday ajdod A olinadiki, undan keyin yetarli chiqindi bor — o'sha chiqindi hisobiga."""
    chain = _chain(root, tpath)
    pick = next((lvl for lvl, room in _room_levels(chain, d) if room >= delta - TOL), None)
    if pick is None:
        raise EditError(_("ed.block_space"))
    parent, node = chain[pick - 1], chain[pick]
    i = _index_of(parent, node)
    j = _next_free(parent, node)
    for c in parent.children[i + 1:j]:                  # A bilan chiqindi orasidagi polosalar delta ga siljiydi
        _move_to(c, d, _start(c, d) + delta)
    w = parent.children[j]
    ext = _extent(w, d)
    _move_to(w, d, _start(w, d) + delta)
    _set_extent(w, d, ext - delta)
    if ext - delta <= EPS:
        parent.children.pop(j)
    _grow_down(chain[pick:], d, delta, kerf)


def expand_block(ctx: Ctx, path: list[int]) -> CuttingResult:
    """Shift+W: «Группировка в блок» detali uchun blokni (guruh tuguni yoki polosadagi bir xil detallar qatori)
    «Макс. количество в блоке» gacha kengaytiradi. Blok oxiridagi joy yetmasa — polosa (blok joylashgan hudud) blokning
    qo'yish o'qi bo'yicha kengayadi: undan keyingi polosalar siljiydi, joy esa keyingi bo'sh joy hisobiga olinadi
    (qo'shni ustunlarning oxirgi chiqindisi ham shuncha kattalashadi). Soni: qolgan detallar, maksimum va joy bilan
    chegaralanadi."""
    parent, node, idx = _node_at(ctx.root, path)
    if node.kind == "W":
        raise EditError(_("ed.block_select"))
    if node.kind == "P":
        if parent is None or node.pid is None:
            raise EditError(_("ed.block_select"))
        T, tpath, uid = parent, path[:-1], node.pid[1]
        lo = hi = idx
        kids = T.children

        def same(i: int) -> bool:
            c = kids[i]
            return c.kind == "P" and c.pid is not None and c.pid[1] == uid
        while lo - 1 >= 0 and same(lo - 1):
            lo -= 1
        while hi + 1 < len(kids) and same(hi + 1):
            hi += 1
    else:                                                   # C: guruh tuguni / polosa — faqat bir xil detallardan
        T, tpath = node, list(path)
        body = [i for i, c in enumerate(T.children) if c.kind != "W"]
        if not body or any(T.children[i].kind != "P" or T.children[i].pid is None for i in body) \
                or len({T.children[i].pid[1] for i in body}) != 1 or body[-1] - body[0] + 1 != len(body):
            raise EditError(_("ed.block_select"))
        uid = T.children[body[0]].pid[1]
        lo, hi = body[0], body[-1]
    kids = T.children
    if any(c.kind != "W" for c in kids[hi + 1:]):          # blokdan keyin boshqa detal/polosa bor — kengaytirib bo'lmaydi
        raise EditError(_("ed.block_space"))
    part = next((p for p in ctx.op.parts if p.uid == uid), None)
    if part is None or part.group_by not in ("length", "width"):
        raise EditError(_("ed.block_none", uid=uid))
    run_len = hi - lo + 1
    gmax = int(part.group_max or 0)
    if gmax > 0 and run_len >= gmax:
        raise EditError(_("ed.block_max", n=gmax))
    left = ctx.remaining(uid) // ctx.copies
    if left < 1:
        raise EditError(_("ed.none_left", uid=uid, c=ctx.copies))
    d = T.axis
    ue = _extent(kids[hi], d)
    gk = _kf(T, ctx.kerf)
    step = ue + gk
    avail = _start(T, d) + _extent(T, d) - (_start(kids[hi], d) + ue)      # blok oxiridan konteyner oxirigacha
    n_free = max(0, int((avail + TOL) // step))
    rooms = [room for _lvl, room in _room_levels(_chain(ctx.root, tpath), d)]
    n_grow = int((max(rooms, default=0.0) + TOL) // step)
    want = min(left, (gmax - run_len) if gmax > 0 else MAX_FILL, MAX_FILL)
    n_max = min(want, n_free + n_grow)
    if n_max < 1:
        raise EditError(_("ed.block_space"))

    def make(k: int) -> _N:
        root = copy.deepcopy(ctx.root)
        t2 = _node_at(root, tpath)[1]
        delta = k * step - avail
        if delta > TOL:
            _extend_chain(root, tpath, d, delta, ctx.kerf)
        proto = t2.children[hi]
        body2 = [c for c in t2.children if c.kind != "W"] + [copy.deepcopy(proto) for _i in range(k)]
        _relayout(t2, body2, gk)
        return root

    return _search(ctx, n_max, False, make)


# ───────────────────────── Торцовка листа (karta darajasida) ─────────────────────────
def _shrink(n: _N, ax: str, d: float) -> None:
    """`_grow` ning teskarisi: tugunni `ax` o'qi bo'yicha d ga qisqartiradi — faqat oxiridagi bo'sh joy hisobiga.
    Detal siqilishi kerak bo'lsa — EditError."""
    cur = _extent(n, ax)
    if n.kind == "W":
        if cur - d < -TOL:
            raise EditError(_("ed.trim_no_room"))
        _set_extent(n, ax, max(0.0, cur - d))
        return
    if n.kind == "P" or cur - d < EPS:
        raise EditError(_("ed.trim_no_room"))
    new_end = _start(n, ax) + cur - d
    if n.axis == ax:
        while n.children:
            last = n.children[-1]
            lend = _start(last, ax) + _extent(last, ax)
            if lend <= new_end + TOL:
                break
            if last.kind == "W":
                if _start(last, ax) < new_end - EPS:
                    _set_extent(last, ax, new_end - _start(last, ax))
                    break
                n.children.pop()                 # butunlay chegaradan tashqarida — olib tashlanadi
                continue
            if last.kind == "C":
                _shrink(last, ax, lend - new_end)
                break
            raise EditError(_("ed.trim_no_room"))
    else:
        for c in n.children:                     # ko'ndalang: har bola qisqaradi
            _shrink(c, ax, d)
    _set_extent(n, ax, cur - d)


def _trim_value(v) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float, str)):
        raise EditError(_("ed.trim_range", n=int(MAX_TRIM)))
    try:
        f = float(v)
    except ValueError:
        raise EditError(_("ed.trim_range", n=int(MAX_TRIM))) from None
    if not math.isfinite(f) or f < 0 or f > MAX_TRIM:
        raise EditError(_("ed.trim_range", n=int(MAX_TRIM)))
    return round(f, 3)


def map_trim(ctx: Ctx, action: dict) -> CuttingResult:
    """«Торцовка листа» (CSE-009): shu kartaga alohida ТД / ТШ / minimal otstup (pastda, o'ngda). Berilmagan kalit —
    o'zgarmaydi; `null` — list qatori / operatsiya qiymatiga qaytish. Foydali zona o'zgaradi: daraxt zona boshiga
    nisbatan o'z joyida qoladi, oxiridagi bo'sh joy kengayadi/qisqaradi; detal sig'masa — xato."""
    m = ctx.m
    st = next((s for s in ctx.op.sheets if s.id == m.sheet_id), None)
    if st is None:
        raise EditError(_("ed.no_sheet"))
    if not any(k in action for k in TRIM_KEYS):
        raise EditError(_("ed.bad_action", a="map_trim"))
    for k in TRIM_KEYS:
        if k in action:
            setattr(m, k, _trim_value(action[k]))
    z_new = _zone(map_stock(st, m), ctx.op.cs_cut)
    if z_new.UL <= 0 or z_new.UW <= 0:
        raise EditError(_("ed.sheet_small"))
    root = ctx.root
    for ax, target, cur in (("x", z_new.UL, root.l), ("y", z_new.UW, root.w)):
        d = target - cur
        if d > EPS:
            _grow(root, ax, d, ctx.kerf)
        elif d < -EPS:
            _shrink(root, ax, -d)
    return commit_tree(ctx.project, ctx.op, ctx.res, m, root, z_new)
