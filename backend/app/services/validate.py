"""Kroy natijasini tekshirish (sexga yuborishdan oldin): har karta jismonan kesib bo'ladimi?

Tekshiruvlar:
  * har detal listning foydali zonasi ichida;
  * detallar ustma-ust tushmaydi va orasida kamida propil (arra qalinligi) bor;
  * kesish daraxti izchil: bolalar ota tugun ichida, o'q bo'ylab propil bilan ketma-ket (gilyotina);
  * tekstura (aylantirish taqiqlangan) buzilmagan;
  * joylashgan + joylashmagan detallar soni kirish bilan teng.
"""
from __future__ import annotations

from collections import Counter

from ..i18n import _
from ..models import CSCutParams, CuttingResult, StockSheet

TOL = 0.01

# «Торцовка листа» (CSE-009): karta darajasidagi torsovka maydonlari (None — list qatori / operatsiya qiymati)
TRIM_KEYS = ("trim_length", "trim_width", "end_offset_bottom", "end_offset_right")


def map_stock(st: StockSheet, m) -> StockSheet:
    """Karta uchun amaldagi list: kartadagi torsovka (agar berilgan bo'lsa) list qatoridagisidan ustun."""
    upd = {k: getattr(m, k) for k in TRIM_KEYS if getattr(m, k, None) is not None}
    return st.model_copy(update=upd) if upd else st


def validate(res: CuttingResult, items, stock: list[StockSheet], cut: CSCutParams) -> list[str]:
    errs: list[str] = []
    sheets = {s.id: s for s in stock}
    item_dims = {}
    for it in items:
        item_dims.setdefault(it.part_id, set()).add((round(it.l, 2), round(it.w, 2), it.can_rotate))
    placed = Counter()
    for m in res.maps:
        st = sheets.get(m.sheet_id)
        if st is None:
            errs.append(_("v.unknown_sheet", map=m.index, id=m.sheet_id))
            continue
        for p in m.placements:
            placed[p.part_id] += m.copies
            if p.x < -TOL or p.y < -TOL or p.x + p.length > st.length + TOL or p.y + p.width > st.width + TOL:
                errs.append(_("v.outside", map=m.index, uid=p.part_uid))
            dims = item_dims.get(p.part_id, set())
            ok = False
            for (l, w, rot) in dims:
                if abs(p.length - l) <= TOL and abs(p.width - w) <= TOL and not p.rotated:
                    ok = True
                if abs(p.length - w) <= TOL and abs(p.width - l) <= TOL and p.rotated and rot:
                    ok = True
                if abs(l - w) <= TOL and abs(p.length - l) <= TOL and abs(p.width - w) <= TOL:
                    ok = True
            if not ok:
                errs.append(_("v.bad_size", map=m.index, uid=p.part_uid, l=p.length, w=p.width))
        # guruh (blok) tugunlari: ichidagi detallar orasida guruh propili (g) yetarli
        boxes: list[tuple] = []
        if m.strips:
            _group_boxes(m.strips[0], boxes)

        def grp(p):
            for gi, (gx, gy, gl, gw, gk) in enumerate(boxes):
                if p.x >= gx - TOL and p.y >= gy - TOL and p.x + p.length <= gx + gl + TOL and \
                        p.y + p.width <= gy + gw + TOL:
                    return gi, gk
            return None
        pl = sorted(m.placements, key=lambda p: (p.x, p.y))
        pg = [grp(p) for p in pl]
        brk = max([cut.kerf] + [bx[4] for bx in boxes])
        for i in range(len(pl)):
            a = pl[i]
            ga = pg[i]
            for j in range(i + 1, len(pl)):
                b = pl[j]
                if b.x >= a.x + a.length + brk - TOL:
                    break
                gb = pg[j]
                kf = ga[1] if ga is not None and gb is not None and ga[0] == gb[0] else cut.kerf
                sep_x = b.x >= a.x + a.length + kf - TOL or a.x >= b.x + b.length + kf - TOL
                sep_y = b.y >= a.y + a.width + kf - TOL or a.y >= b.y + b.width + kf - TOL
                if not (sep_x or sep_y):
                    errs.append(_("v.overlap", map=m.index, a=a.part_uid, b=b.part_uid))
        if m.strips:
            root = m.strips[0]
            from .optimizer import group_kerf
            gk = group_kerf(cut)
            for (_x, _y, _l, _w, g) in boxes:
                if abs(g - gk) > TOL:
                    errs.append(_("v.group_kerf", map=m.index, g=g, k=gk))
            errs += [_(e[0], map=m.index, **e[1]) for e in _check_tree(root, cut.kerf)]
            from .optimizer import _zone
            z = _zone(map_stock(st, m), cut)
            errs += [_(e[0], map=m.index, **e[1]) for e in _check_trim(root, z.ox + z.UL, z.oy + z.UW, cut.min_trim_cut)]
            depth = _max_depth(root)
            if depth > max(1, cut.max_rotations):
                errs.append(_("v.too_deep", map=m.index, d=depth, m=max(1, cut.max_rotations)))
            leaves = []
            _collect(root, leaves)
            if len(leaves) != len(m.placements):
                errs.append(_("v.tree_count", map=m.index, a=len(leaves), b=len(m.placements)))
    want = Counter(it.part_id for it in items)
    got = placed + Counter(res.unplaced)
    if want != got:
        diff = (want - got) + (got - want)
        errs.append(_("v.count", d=dict(list(diff.items())[:5])))
    return errs


def _check_trim(n: dict, xend: float, yend: float, mt: float) -> list[tuple[str, dict]]:
    """Ichki kesimda minimal obrezkadan kichik qirindi qolmasin (list chetlari bundan mustasno)."""
    errs = []
    if n["k"] != "C":
        return errs
    ax = n["a"]
    end = n["x"] + n["l"] if ax == "x" else n["y"] + n["w"]
    raw = end >= (xend if ax == "x" else yend) - TOL
    body = [c for c in n["c"] if c["k"] != "W"]
    if body and not raw:
        last = max((c["x"] + c["l"]) if ax == "x" else (c["y"] + c["w"]) for c in body)
        rest = end - last
        if TOL < rest < mt - TOL:
            errs.append(("v.trim", dict(x=n["x"], y=n["y"], r=f"{rest:.1f}", mt=mt)))
    for c in n["c"]:
        errs += _check_trim(c, xend, yend, mt)
    return errs


def _group_boxes(n: dict, out: list) -> None:
    """Guruh (blok) tugunlari: (x, y, l, w, guruh propili)."""
    if n.get("k") == "C" and n.get("g") is not None:
        out.append((float(n["x"]), float(n["y"]), float(n["l"]), float(n["w"]), float(n["g"])))
        return
    for c in n.get("c", []):
        _group_boxes(c, out)


def _max_depth(n: dict, d: int = 0) -> int:
    """Kesish darajasi (burilish raqami): ildiz — 0, polosalar — 1, … Chiqindi bo'lagi ham hisoblanadi —
    uni ajratadigan kesim shu darajada."""
    kids = n.get("c") or []
    if n.get("k") != "C" or not kids:
        return d
    return max(_max_depth(c, d + 1) for c in kids)


def _collect(n: dict, out: list) -> None:
    if n["k"] == "P":
        out.append(n)
    for c in n.get("c", []):
        _collect(c, out)


def _check_tree(n: dict, kerf: float) -> list[tuple[str, dict]]:
    errs = []
    if n["k"] != "C":
        return errs
    ax = n["a"]
    start = n["x"] if ax == "x" else n["y"]
    end = start + (n["l"] if ax == "x" else n["w"])
    pos = start
    gap = float(n["g"]) if n.get("g") is not None else kerf       # guruh tugunida — guruh propili
    for i, c in enumerate(n["c"]):
        cs = c["x"] if ax == "x" else c["y"]
        ce = cs + (c["l"] if ax == "x" else c["w"])
        # ko'ndalang o'lcham ota tugun bilan bir xil bo'lishi kerak (gilyotina)
        if ax == "x":
            if abs(c["y"] - n["y"]) > TOL or abs(c["w"] - n["w"]) > TOL:
                errs.append(("v.tree_cross", dict(x=n["x"], y=n["y"])))
        else:
            if abs(c["x"] - n["x"]) > TOL or abs(c["l"] - n["l"]) > TOL:
                errs.append(("v.tree_cross", dict(x=n["x"], y=n["y"])))
        if cs < pos - TOL:
            errs.append(("v.tree_overlap", dict(x=n["x"], y=n["y"])))
        if ce > end + TOL:
            errs.append(("v.tree_out", dict(x=n["x"], y=n["y"])))
        pos = ce + gap
        errs += _check_tree(c, kerf)
    return errs
