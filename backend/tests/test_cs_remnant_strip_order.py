# Деловой qoldiq va polosalar tartibi (2026-10-23, xodim loyihasi): «Сортировка полос: по убыванию» qoldiqli eng keng
# polosani list TEPASIGA chiqarib qo'ydi (1405×100 ×2 + деловой 1332×653 — keyin 2375×414 ×2, 2005×330). To'g'risi:
# detallar list boshidan, qoldiq oxirida. Qidiruv ham kattaroq qoldiqni topmagan edi (qo'lda tuzatilgani 2375×653).
from app.models import CSCutParams, CSMaterialParams, StockSheet, StripSort
from app.services import optimizer as mod
from app.services.validate import validate

MAT = CSMaterialParams(remnant_min_side1=1000, remnant_min_side2=500, remnant_min_area=0.5)


def _zone():
    return mod._zone(StockSheet(id="s", length=2750, width=1830), CSCutParams(kerf=3, trim_length=2, trim_width=2))


def test_desc_sort_keeps_remnant_strip_last():
    z = _zone()
    rem_strip = mod._N(0, 0, z.UL, 653, 1, "C", axis="x", children=[
        mod._N(0, 0, 1405, 653, 2, "C", axis="y", children=[mod._N(0, 0, 1405, 100, 3, "P", s=0),
                                                           mod._N(0, 103, 1405, 100, 3, "P", s=0),
                                                           mod._N(0, 206, 1405, 447, 3, "W")]),
        mod._N(1408, 0, z.UL - 1408, 653, 2, "W")])
    s1 = mod._N(0, 656, z.UL, 414, 1, "P", s=1)
    s2 = mod._N(0, 1073, z.UL, 414, 1, "P", s=1)
    s3 = mod._N(0, 1490, z.UL, 330, 1, "P", s=2)
    root = mod._N(0, 0, z.UL, z.UW, 0, "C", axis="y", children=[rem_strip, s1, s2, s3])
    mod._safe_reorder(root, StripSort.DESC, CSCutParams(kerf=3), z, mat=MAT)
    assert [c.w for c in root.children] == [414, 414, 330, 653]          # qoldiqli polosa — oxirida
    assert root.children[-1].y == 414 + 3 + 414 + 3 + 330 + 3
    # qoldiq bo'lmasa (mat yo'q) — avvalgidek faqat eni bo'yicha
    root2 = mod._N(0, 0, z.UL, z.UW, 0, "C", axis="y", children=[s3, s1])
    mod._safe_reorder(root2, StripSort.ASC, CSCutParams(kerf=3), z, mat=MAT)
    assert [c.w for c in root2.children] == [330, 414]


def test_last_sheet_big_corner_remnant_after_parts():
    P = [(1, 2375, 510, 2), (2, 2375, 414, 7), (3, 335, 510, 1), (4, 2005, 330, 2), (5, 1450, 100, 2),
         (6, 1405, 100, 5), (7, 1405, 70, 4)]
    items = [mod.Item(f"p{u}", u, l, w, True) for u, l, w, n in P for _ in range(n)]
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, max_rotations=4, complex_strips=True, min_trim_cut=5)
    st = [StockSheet(id="s", length=2750, width=1830)]
    res = mod.optimize(items, st, cut, MAT)
    assert not validate(res, items, st, cut)
    assert res.total_sheets == 3 and not res.unplaced
    biz = [(m, o) for m in res.maps for o in m.offcuts if o.business]
    assert biz and sum(o.length * o.width for _m, o in biz) / 1e6 >= 1.55       # avval 0.87 (1332×653)
    for m, o in biz:                            # qoldiq — detallardan keyin (pastda / o'ngda), ular bilan ustma-ust emas
        for p in m.placements:
            assert p.y + p.width <= o.y + 1e-6 or p.x + p.length <= o.x + 1e-6


def test_no_sort_still_moves_remnant_column_last():
    # «Сортировка в полосе: не сортировать»: polosa ichida qoldiqli ustun detalli ustundan oldin — oxiriga o'tadi,
    # detalli bo'laklarning o'zaro tartibi saqlanadi
    z = _zone()
    col = mod._N(0, 0, 1470, 1050, 2, "C", axis="y", children=[mod._N(0, 0, 1470, 250, 3, "P", s=0),
                                                                mod._N(0, 253, 1470, 797, 3, "W")])
    p1 = mod._N(1473, 0, 500, 1050, 2, "P", s=1)
    p2 = mod._N(1976, 0, 300, 1050, 2, "P", s=2)
    strip = mod._N(0, 0, z.UL, 1050, 1, "C", axis="x", children=[col, p1, p2, mod._N(2279, 0, z.UL - 2279, 1050, 2, "W")])
    root = mod._N(0, 0, z.UL, z.UW, 0, "C", axis="y", children=[strip, mod._N(0, 1053, z.UL, z.UW - 1053, 1, "W")])
    mod._remnants_last(root, CSCutParams(kerf=3), z, MAT, root)
    assert [c.l for c in strip.children[:3]] == [500, 300, 1470]
    assert strip.children[2].x == 500 + 3 + 300 + 3 and strip.children[2].children[1].kind == "W"
