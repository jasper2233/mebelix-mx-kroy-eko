"""«До кроить»: kroyga kirmagan detallarni avval MAVJUD kartalarning bo'sh joylariga, keyin yangi listlarga joylash.

Onlayn tizimda tekshirilgan (2026-10-21, «test uchun»): tahrirda kartadan ikkita detal olib, «Ок» → «До кроить» — detallar
o'sha kartaning bo'sh joyiga qaytdi, joylangan detallar o'z joyida qoldi, kartalar soni o'zgarmadi. Foydalanuvchi talabi:
«terilgan detallar qoladi va yoniga qolgan kroyga kirishi kerak bo'lgan detallar avtomat qo'shilib, yaxlit kroy qilingandek».

Usul: har kartaning daraxtidagi bo'sh (W) barglar — kattasidan boshlab — alohida «kichik list» sifatida optimizatorga
(`_best_sheet`) beriladi; topilgan joylashuv shu bargning o'rniga qo'yiladi va butun natija `editor.rebuild` bilan qayta
quriladi va tekshiriladi (propil, minimal obrezka, kesim darajasi, detal soni). Tekshiruvdan o'tmagan joylashuv tashlanadi.
Karta bir nechta list (C > 1) bo'lsa — har detal C nusxada kerak. Guruhlanadigan (blok) detallar — yangi listlarga.
"""
from __future__ import annotations

import copy
import time
from collections import Counter, deque
from ..models import CSCutParams, CuttingResult, Operation, Project
from .calc import _items_for
from .optimizer import Item, _best_sheet, _largest_waste, _N, _other, _Pool, _zone, _Zone
from .validate import map_stock

TIME_PER_LEAF = 0.4          # bitta bo'sh joy qidiruvi, s
TOTAL_BUDGET = 20.0          # butun to'ldirish, s
MAX_LEAVES_PER_MAP = 40
FIRST_VARIANTS = 4           # nechta boshlanish varianti sinaladi (kartaga)


def _free(n: _N, path: list[int], out: list) -> None:
    for i, c in enumerate(n.children):
        if c.kind == "W":
            out.append((path + [i], n, c))
        elif c.kind == "C":
            _free(c, path + [i], out)


def _map_largest_free(res: CuttingResult, mi: int, info, grp, stock, cut) -> float:
    from . import editor as E
    m = res.maps[mi]
    try:
        root = E._from_dict(m.strips[0], _zone(map_stock(stock[m.sheet_id], m), cut), info, grp=grp)
    except E.EditError:
        return 0.0
    return _largest_waste(root)


def _fill_leaf(project, op, res, mi, root, z, path, parent, leaf, avail, proto, cut):
    """Bitta bo'sh bargni kichik list sifatida to'ldirish; topilsa (yangi natija, joylangan detallar soni)."""
    from . import editor as E
    items = [Item(p.part_id, p.uid, p.l, p.w, p.can_rotate) for pid, n in avail.items()
             for p in [proto[pid]] for _i in range(n)
             if any(a <= leaf.l + 1e-6 and b <= leaf.w + 1e-6 for a, b, _r in p.orientations())]
    if not items:
        return None
    # kichik daraxt bargning o'rniga turadi: ko'ndalang o'qda uning detallari (max − daraja) chuqurlikkacha; ota o'qi bilan
    # bir xil yo'nalishda esa birinchi kesimlar otaning o'ziga qo'shiladi — bir daraja ko'proq (aks holda chuqur bo'sh joylar
    # ishlatilmay, detallar yangi listga o'tib ketardi)
    rot_left = max(1, cut.max_rotations) - leaf.level
    pool = _Pool(items)
    sub = _Zone(z.stock, z.L, z.W, 0.0, 0.0, leaf.l, leaf.w, 0.0, 0.0, far_raw_x=False, far_raw_y=False)
    # ikkala yo'nalish sinaladi: ko'proq detal, teng bo'lsa — kattaroq butun bo'sh joy
    best = None
    for ax in (_other(parent.axis), parent.axis):
        k = rot_left + (1 if ax == parent.axis else 0)
        if k < 1:
            continue
        cp = cut.model_copy(update={"max_rotations": k})
        # intensive — kichik bo'sh joyda tor detallarni ham sinaydi («1268»: 1-list 90.49 → 91.73 %)
        sh = _best_sheet(pool, pool.counts0[:], sub, cp, [ax], time.monotonic() + TIME_PER_LEAF / 2, intensive=True)
        if sh is None or sum(sh.counts_after) >= sum(pool.counts0):
            continue
        key = (-sum(sh.counts_after), _largest_waste(sh.root))
        if best is None or key > best[0]:
            best = (key, sh)
    if best is None:
        return None
    sh = best[1]
    queues = {s.idx: deque(s.pids) for s in pool.shapes}
    for lf in sh.root.leaves():
        if lf.kind == "P":
            lf.pid = queues[lf.s].popleft()
    new = sh.root
    new.shift(leaf.x, leaf.y)
    new.level = leaf.level
    work_root = copy.deepcopy(root)
    wp, _wn, wi = E._node_at(work_root, path)
    wp.children[wi] = new
    trial = res.model_copy(deep=True)
    try:
        out = E.commit_tree(project, op, trial, trial.maps[mi], work_root, z)
    except E.EditError:
        return None
    return out, Counter(lf.pid[0] for lf in new.leaves() if lf.kind == "P")


def _fill_map(project, op, res, mi, left, proto, info, grp, stock, cut, min_area, t_end, first):
    """Bitta kartaning bo'sh joylarini ketma-ket to'ldirish; `first` — birinchi qadamda kattaligi bo'yicha nechanchi bo'sh joydan
    boshlanadi. Qaytaradi: (natija, qolgan detallar, birinchi qadamdagi bo'sh joylar soni)."""
    from . import editor as E
    tries = 0
    n_free0 = 0
    step = 0
    while time.monotonic() < t_end and tries < MAX_LEAVES_PER_MAP:
        m = res.maps[mi]
        c = max(1, int(m.copies))
        avail = {pid: n // c for pid, n in left.items() if pid in proto and n // c > 0}
        if not avail or not m.strips or m.sheet_id not in stock:
            break
        z = _zone(map_stock(stock[m.sheet_id], m), cut)
        try:
            root = E._from_dict(m.strips[0], z, info, grp=grp)
        except E.EditError:
            break
        free: list = []
        _free(root, [], free)
        free = [f for f in free if f[2].l * f[2].w >= min_area - 1e-6]
        free.sort(key=lambda f: -(f[2].l * f[2].w))
        if step == 0:
            n_free0 = len(free)
            if first:
                free = free[first:] + free[:first]
        step += 1
        placed = None
        for path, parent, leaf in free:
            tries += 1
            if tries > MAX_LEAVES_PER_MAP or time.monotonic() > t_end:
                break
            got = _fill_leaf(project, op, res, mi, root, z, path, parent, leaf, avail, proto, cut)
            if got is not None:
                placed = got
                break
        if placed is None:
            break
        res, got = placed
        for pid, n in got.items():
            left[pid] = left.get(pid, 0) - n * c
        left = {k: v for k, v in left.items() if v > 0}
        if not left:
            break
    return res, left, n_free0


def fill_existing(project: Project, op: Operation, res: CuttingResult, left: dict[str, int],
                  cut: CSCutParams) -> tuple[CuttingResult, dict[str, int]]:
    """Mavjud kartalarning bo'sh joylarini to'ldiradi. Qaytaradi: (yangi natija, hali joylanmagan detallar soni)."""
    from . import editor as E
    left = {k: v for k, v in left.items() if v > 0}
    grouped = {p.id for p in op.parts if p.group_by in ("length", "width")}
    if not left or not res.maps or res.remnants_saved:      # qoldiqlar omborga yozilgan — kartalarga tegilmaydi
        return res, left
    info = E.part_info(project, op)
    grp = E.op_groups(op)
    stock = {s.id: s for s in op.sheets}
    proto: dict[str, Item] = {}
    for it in _items_for(project, op, cut, {k: 1 for k in left if k not in grouped}):
        proto.setdefault(it.part_id, it)
    if not proto:
        return res, left
    min_area = min(it.area for it in proto.values())
    area = {pid: it.area for pid, it in proto.items()}
    t_end = time.monotonic() + TOTAL_BUDGET
    manual = res.manual
    for mi in range(len(res.maps)):
        if not left or time.monotonic() > t_end:
            break
        # onlayn tizim bitta yo'l bilan to'ldiradi; MX bir nechta variantni (qaysi bo'sh joydan boshlash) sinab, eng ko'p maydon
        # joylaganini oladi, teng bo'lsa — kattaroq butun bo'sh joy qolganini (foydalanuvchi: «undan ham yaxshi bo'lishi kerak»)
        best = None
        for first in range(FIRST_VARIANTS):
            if time.monotonic() > t_end:
                break
            r2, l2, n_free = _fill_map(project, op, res, mi, dict(left), proto, info, grp, stock, cut, min_area, t_end, first)
            key = (-sum(area[k] * v for k, v in l2.items() if k in area), _map_largest_free(r2, mi, info, grp, stock, cut))
            if best is None or key > best[0]:
                best = (key, r2, l2)
            if first + 1 >= n_free:
                break
        res, left = best[1], best[2]
    res.manual = manual
    return res, left

