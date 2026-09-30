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

from ..models import CSCutParams, CuttingResult, StockSheet

TOL = 0.01


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
            errs.append(f"karta {m.index}: noma'lum list {m.sheet_id}")
            continue
        for p in m.placements:
            placed[p.part_id] += m.copies
            if p.x < -TOL or p.y < -TOL or p.x + p.length > st.length + TOL or p.y + p.width > st.width + TOL:
                errs.append(f"karta {m.index}: detal {p.part_uid} list tashqarisida")
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
                errs.append(f"karta {m.index}: detal {p.part_uid} o'lchami/aylanishi noto'g'ri ({p.length}x{p.width}, rot={p.rotated})")
        pl = sorted(m.placements, key=lambda p: (p.x, p.y))
        for i in range(len(pl)):
            a = pl[i]
            for j in range(i + 1, len(pl)):
                b = pl[j]
                if b.x >= a.x + a.length + cut.kerf - TOL:
                    break
                sep_x = b.x >= a.x + a.length + cut.kerf - TOL or a.x >= b.x + b.length + cut.kerf - TOL
                sep_y = b.y >= a.y + a.width + cut.kerf - TOL or a.y >= b.y + b.width + cut.kerf - TOL
                if not (sep_x or sep_y):
                    errs.append(f"karta {m.index}: detallar {a.part_uid} va {b.part_uid} ustma-ust yoki propilsiz")
        if m.strips:
            root = m.strips[0]
            errs += [f"karta {m.index}: {e}" for e in _check_tree(root, cut.kerf)]
            from .optimizer import _zone
            z = _zone(st, cut)
            errs += [f"karta {m.index}: {e}" for e in _check_trim(root, z.ox + z.UL, z.oy + z.UW, cut.min_trim_cut)]
            leaves = []
            _collect(root, leaves)
            if len(leaves) != len(m.placements):
                errs.append(f"karta {m.index}: daraxtdagi detallar soni {len(leaves)} ≠ joylashuvlar {len(m.placements)}")
    want = Counter(it.part_id for it in items)
    got = placed + Counter(res.unplaced)
    if want != got:
        diff = (want - got) + (got - want)
        errs.append(f"detallar soni mos emas: {dict(list(diff.items())[:5])}")
    return errs


def _check_trim(n: dict, xend: float, yend: float, mt: float) -> list[str]:
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
            errs.append(f"tugun ({n['x']},{n['y']}): {rest:.1f} mm qirindi < minimal obrezka {mt}")
    for c in n["c"]:
        errs += _check_trim(c, xend, yend, mt)
    return errs


def _collect(n: dict, out: list) -> None:
    if n["k"] == "P":
        out.append(n)
    for c in n.get("c", []):
        _collect(c, out)


def _check_tree(n: dict, kerf: float) -> list[str]:
    errs = []
    if n["k"] != "C":
        return errs
    ax = n["a"]
    start = n["x"] if ax == "x" else n["y"]
    end = start + (n["l"] if ax == "x" else n["w"])
    pos = start
    for i, c in enumerate(n["c"]):
        cs = c["x"] if ax == "x" else c["y"]
        ce = cs + (c["l"] if ax == "x" else c["w"])
        # ko'ndalang o'lcham ota tugun bilan bir xil bo'lishi kerak (gilyotina)
        if ax == "x":
            if abs(c["y"] - n["y"]) > TOL or abs(c["w"] - n["w"]) > TOL:
                errs.append(f"tugun ({n['x']},{n['y']}) bolasi ko'ndalang o'lchamda mos emas")
        else:
            if abs(c["x"] - n["x"]) > TOL or abs(c["l"] - n["l"]) > TOL:
                errs.append(f"tugun ({n['x']},{n['y']}) bolasi ko'ndalang o'lchamda mos emas")
        if cs < pos - TOL:
            errs.append(f"tugun ({n['x']},{n['y']}) bolalari ustma-ust (propilsiz)")
        if ce > end + TOL:
            errs.append(f"tugun ({n['x']},{n['y']}) bolasi chegaradan chiqqan")
        pos = ce + kerf
        errs += _check_tree(c, kerf)
    return errs
