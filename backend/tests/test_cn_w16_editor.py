"""W16 (CNE) — nesting kartasini qo'lda tahrirlash: ko'chirish, yopishtirish (chet / nuqta), burish, o'chirish, qo'yish, qayta joylash;
har amal `validate_cn` dan o'tadi; buzilsa rad etiladi; natija izi (409 himoyasi) o'zgaradi."""
from __future__ import annotations

import math

import pytest

from app.models import CuttingResult
from app.services import cn_calc, cn_editor
from app.services import cn_geometry as G
from app.services import cn_validate as V
from app.services.editor import EditError
from cn_w16_proj import cmd, make_project, run
from cn_w16_util import check_sheet


def _fresh(parts=None, sheets=None, **kw):
    project, op = make_project(parts or [dict(length=300, width=200, qty=3), dict(length=120, width=90, qty=3)], sheets or [(1000, 700)], **kw)
    run(project, op, "fast")
    return project, op


def _valid(project, op, res: CuttingResult):
    ci = cn_calc.build_items(project, op)
    return V.validate_cn(res, ci.shapes, ci.need, ci.grains, op.sheets, op.cn, allow_empty=True)


def _apply(project, op, res, **action):
    return cn_editor.apply(project, op, res, action)


def _polys(project, op, res, mi=0):
    return [(pl.outline, pl.holes) for pl in res.maps[mi].placements]


def _idx(res, uid, k=0, mi=0):
    return [i for i, pl in enumerate(res.maps[mi].placements) if pl.part_uid == uid][k]


def test_noop_rebuild_keeps_everything_and_is_valid():
    project, op = _fresh()
    res = op.result
    assert res.kind == "nest" and res.unplaced == [] and len(res.maps) == 1
    new = cn_editor.rebuild(project, op, res, final=True)
    assert new.manual and new.total_sheets == res.total_sheets and _valid(project, op, new) == []
    assert [(p.part_uid, p.x, p.y, p.angle) for p in new.maps[0].placements] == [(p.part_uid, p.x, p.y, p.angle) for p in res.maps[0].placements]
    assert new.maps[0].offcuts == res.maps[0].offcuts          # o'zgarmagan kartada qoldiqlar qayta hisoblanmaydi (yo'q bo'lmaydi)


def test_move_valid_and_invalid():
    project, op = _fresh()
    res = op.result
    i = _idx(res, 1)
    pl = res.maps[0].placements[i]
    out = _apply(project, op, res, type="move", map=1, index=i, dx=0.0, dy=0.0)
    assert _valid(project, op, out) == []
    # chekka: list tashqarisiga
    with pytest.raises(EditError) as e:
        _apply(project, op, res, type="move", map=1, index=i, dx=5000.0, dy=0.0)
    assert e.value.details                                         # xato matni ro'yxati bor
    # boshqa detal ustiga
    j = _idx(res, 2)
    other = res.maps[0].placements[j]
    with pytest.raises(EditError):
        _apply(project, op, res, type="move", map=1, index=i, dx=other.x - pl.x, dy=other.y - pl.y)
    # noto'g'ri indeks / tur
    with pytest.raises(EditError):
        _apply(project, op, res, type="move", map=1, index=99, dx=1.0, dy=0.0)
    with pytest.raises(EditError):
        _apply(project, op, res, type="yoq-amal", map=1)
    with pytest.raises(EditError):
        _apply(project, op, res, type="move", map=1, index=i, dx="x", dy=0)


def test_slide_in_every_direction_stops_at_exact_clearance():
    project, op = _fresh(parts=[dict(length=200, width=150, qty=2)], sheets=[(800, 500)], cn=dict(margin=5, tool_diameter=6, part_gap=0))
    spacing = op.cn.spacing + op.cn.arc_tol
    res = op.result
    # birinchi detalni o'ngga qadar, so'ng pastga, chapga, yuqoriga suramiz: har holda yaroqli va to'siq masofasi aniq
    cur = res
    for direction in ("right", "down", "left", "up"):
        for i in range(2):
            try:
                cur = _apply(project, op, cur, type="slide", map=1, index=i, dir=direction)
            except EditError:
                pass                                              # allaqachon yopishgan
        assert _valid(project, op, cur) == []
        polys = _polys(project, op, cur)
        assert check_sheet(polys, 800, 500, op.cn.margin, spacing) == []
    # chetga yopishgan: 'left' dan keyin x = margin
    cur = res
    for _k in range(2):
        for i in range(2):
            try:
                cur = _apply(project, op, cur, type="slide", map=1, index=i, dir="left")
            except EditError:
                pass
    xs = sorted(pl.x for pl in cur.maps[0].placements)
    assert xs[0] == pytest.approx(op.cn.margin, abs=0.02)
    # allaqachon yopishgan yo'nalishda — aniq xabar
    with pytest.raises(EditError) as e:
        _apply(project, op, cur, type="slide", map=1, index=_idx(cur, 1), dir="up")
        _apply(project, op, cur, type="slide", map=1, index=_idx(cur, 1), dir="up")
    assert e.value is not None


def test_slide_contact_distance_to_neighbor():
    project, op = make_project([dict(length=200, width=150, qty=2)], [(1000, 500)], cn=dict(margin=5, tool_diameter=6, part_gap=4))
    ci = cn_calc.build_items(project, op)
    st = op.sheets[0]
    a = cn_calc.Spec(op.parts[0], ci.shapes[op.parts[0].id], 0.0, 5.0, 5.0)
    b = cn_calc.Spec(op.parts[0], ci.shapes[op.parts[0].id], 0.0, 600.0, 5.0)
    res = cn_calc.finish_result(CuttingResult(maps=[cn_calc.make_map(1, st, 1, [a, b], op.cn, {}, [])], kind="nest"))
    out = _apply(project, op, res, type="slide", map=1, index=1, dir="left")
    gap = out.maps[0].placements[1].x - (out.maps[0].placements[0].x + out.maps[0].placements[0].length)
    spacing = op.cn.spacing + op.cn.arc_tol                      # 6 + 4 + 0.25
    assert gap >= spacing - 1e-6 and gap - spacing < 0.02
    # ikkala detal birga (guruh) o'ngga: o'zaro masofa saqlanadi
    out2 = _apply(project, op, out, type="slide", map=1, indices=[0, 1], dir="right")
    assert out2.maps[0].placements[1].x + out2.maps[0].placements[1].length == pytest.approx(1000 - 5, abs=0.02)
    assert (out2.maps[0].placements[1].x - out2.maps[0].placements[0].x) == pytest.approx(out.maps[0].placements[1].x - out.maps[0].placements[0].x, abs=1e-6)


def test_snap_by_point_moves_until_contact():
    project, op = make_project([dict(length=200, width=150, qty=2)], [(1000, 500)], cn=dict(margin=5, tool_diameter=6))
    ci = cn_calc.build_items(project, op)
    st = op.sheets[0]
    sh = ci.shapes[op.parts[0].id]
    a = cn_calc.Spec(op.parts[0], sh, 0.0, 5.0, 5.0)
    b = cn_calc.Spec(op.parts[0], sh, 0.0, 500.0, 5.0)
    res = cn_calc.finish_result(CuttingResult(maps=[cn_calc.make_map(1, st, 1, [a, b], op.cn, {}, [])], kind="nest"))
    # b ning chap-yuqori uchi (500, 5) → a ning o'ng-yuqori uchi (205, 5): masofa qoidasi to'siq qo'yadi
    out = _apply(project, op, res, type="snap", map=1, index=1, **{"from": [500.0, 5.0], "to": [205.0, 5.0]})
    p0, p1 = out.maps[0].placements
    spacing = op.cn.spacing + op.cn.arc_tol
    assert p1.x - (p0.x + p0.length) == pytest.approx(spacing, abs=0.02)
    assert _valid(project, op, out) == []
    # nishon bo'sh joyda (to'siqsiz) — to'liq yetib boradi
    out = _apply(project, op, res, type="snap", map=1, index=1, **{"from": [500.0, 5.0], "to": [700.0, 300.0]})
    assert out.maps[0].placements[1].x == pytest.approx(700.0) and out.maps[0].placements[1].y == pytest.approx(300.0)
    with pytest.raises(EditError):
        _apply(project, op, res, type="snap", map=1, index=1, **{"from": [1, 2, 3], "to": [4, 5]})


def _explicit(project, op, specs_def, copies=1, sheet=0):
    """Aniq joylashuv: [(uid, burchak, x, y)] — nesting natijasiga tayanmasdan."""
    ci = cn_calc.build_items(project, op)
    specs = []
    for uid, ang, x, y in specs_def:
        part = next(p for p in op.parts if p.uid == uid)
        specs.append(cn_calc.Spec(part, ci.shapes[part.id], ang, x, y))
    res = cn_calc.finish_result(CuttingResult(maps=[cn_calc.make_map(1, op.sheets[sheet], copies, specs, op.cn, {}, [])], kind="nest"))
    res.unplaced = [p.id for p in op.parts for _k in range(max(0, ci.need.get(p.id, 0) - sum(1 for s in specs if s.part.id == p.id) * copies))]
    return res


def test_rotate_rules_group_and_free_angle():
    project, op = make_project([dict(length=300, width=100, qty=1), dict(length=300, width=100, qty=1, grain=True)], [(1000, 700)],
                               cn=dict(margin=5, rot_step=15))
    res = _explicit(project, op, [(1, 0.0, 200, 200), (2, 0.0, 200, 450)])
    assert _valid(project, op, res) == []
    i1, i2 = _idx(res, 1), _idx(res, 2)
    # Ткт ✗ detalni 90° ga burish — mumkin; Ткт ✓ — taqiqlangan
    out = _apply(project, op, res, type="rotate", map=1, index=i1, delta=90)
    assert out.maps[0].placements[_idx(out, 1)].angle == 90.0 and _valid(project, op, out) == []
    with pytest.raises(EditError) as e:
        _apply(project, op, out, type="rotate", map=1, index=_idx(out, 2), delta=90)
    assert "90" in str(e.value)
    # erkin burchak (rot_step=15: 105° ruxsat, 100° — yo'q)
    out2 = _apply(project, op, out, type="rotate", map=1, index=_idx(out, 1), angle=105.0)
    assert out2.maps[0].placements[_idx(out2, 1)].angle == pytest.approx(105.0) and _valid(project, op, out2) == []
    with pytest.raises(EditError):
        _apply(project, op, out, type="rotate", map=1, index=_idx(out, 1), angle=100.0)
    # Ткт ✓ — 180° mumkin
    out3 = _apply(project, op, res, type="rotate", map=1, index=i2, delta=180)
    assert out3.maps[0].placements[_idx(out3, 2)].angle == 180.0 and _valid(project, op, out3) == []
    # qo'shni detalga tegib ketadigan burish — rad etiladi
    tight = _explicit(project, op, [(1, 0.0, 200, 200), (2, 0.0, 200, 316)])
    with pytest.raises(EditError):
        _apply(project, op, tight, type="rotate", map=1, index=_idx(tight, 1), delta=90)
    # guruh: ikkala detalni 180° — markaz atrofida aylanadi, o'zaro joylashuv aks etadi
    grp = _apply(project, op, res, type="rotate", map=1, indices=[i1, i2], delta=180)
    assert {p.part_uid: p.angle for p in grp.maps[0].placements} == {1: 180.0, 2: 180.0} and _valid(project, op, grp) == []
    assert grp.maps[0].placements[_idx(grp, 1)].y > grp.maps[0].placements[_idx(grp, 2)].y        # joylar almashdi

def test_remove_place_auto_place_and_remaining_counts():
    project, op = _fresh()
    res = op.result
    n0 = len(res.maps[0].placements)
    i = _idx(res, 2)
    uid_part = next(p for p in op.parts if p.uid == 2)
    out = _apply(project, op, res, type="remove", map=1, index=i)
    assert len(out.maps[0].placements) == n0 - 1 and uid_part.id in out.unplaced
    assert _valid(project, op, out) == []
    # qayta joylash: avtomatik
    back = _apply(project, op, out, type="auto_place", uid=2)
    assert len(back.maps[0].placements) == n0 and back.unplaced == []
    assert _valid(project, op, back) == []
    # keraksiz qo'yish: joylanmagan nusxa qolmagan
    with pytest.raises(EditError):
        _apply(project, op, back, type="auto_place", uid=2)
    with pytest.raises(EditError):
        _apply(project, op, back, type="place", map=1, uid=2, x=10, y=10)
    # aniq joyga qo'yish (bo'sh joy: o'ng-pastki burchak)
    out = _apply(project, op, res, type="remove", map=1, index=i)
    placed = _apply(project, op, out, type="place", map=1, uid=2, x=800.0, y=500.0, angle=0)
    assert placed.maps[0].placements[-1].x == 800.0 and _valid(project, op, placed) == []
    with pytest.raises(EditError):                                  # band joyga
        pl0 = out.maps[0].placements[0]
        _apply(project, op, out, type="place", map=1, uid=2, x=pl0.x + 5, y=pl0.y + 5)
    with pytest.raises(EditError):
        _apply(project, op, out, type="place", map=1, uid=999, x=1, y=1)


def test_maps_add_delete_copies_comment_move_and_final_rules():
    project, op = make_project([dict(length=300, width=200, qty=6)], [(1000, 700)])
    res = _explicit(project, op, [(1, 0.0, 10, 10), (1, 0.0, 400, 10)])
    out = _apply(project, op, res, type="add_map")
    assert len(out.maps) == 2 and out.maps[1].placements == []
    with pytest.raises(EditError):                                   # saqlashda bo'sh karta bo'lmasligi shart
        cn_editor.rebuild(project, op, out, final=True)
    out = _apply(project, op, out, type="comment", map=1, comment="F2 izoh")
    assert out.maps[0].comment == "F2 izoh"
    out = _apply(project, op, out, type="copies", map=1, copies=3)       # 3 nusxa × 2 detal = 6 = ОК
    assert out.maps[0].copies == 3 and out.total_sheets == 3 + 1 and out.unplaced == []
    with pytest.raises(EditError):                                   # ОК − МK dan ko'p bo'lmaydi
        _apply(project, op, out, type="copies", map=1, copies=4)
    out = _apply(project, op, out, type="copies", map=1, copies=1)
    out = _apply(project, op, out, type="move_map", map=1, to="down")
    assert out.maps[0].placements == [] and len(out.maps[1].placements) == 2
    out = _apply(project, op, out, type="delete_map", map=1)
    assert len(out.maps) == 1 and cn_editor.rebuild(project, op, out, final=True).maps
    with pytest.raises(EditError):
        _apply(project, op, res, type="copies", map=1, copies=0)

def test_renest_keeps_all_and_never_worsens():
    project, op = _fresh(parts=[dict(length=300, width=200, qty=3), dict(length=120, width=90, qty=3), dict(length=500, width=60, qty=2)],
                         sheets=[(1000, 700)])
    res = op.result
    # bir nechta detalni olib tashlab, qayta joylaymiz
    out = _apply(project, op, res, type="remove", map=1, indices=[0, 1, 2])
    n_before = len(out.maps[0].placements)
    re = _apply(project, op, out, type="renest", map=1)
    assert len(re.maps[0].placements) >= n_before + 1
    assert _valid(project, op, re) == []


def test_result_rev_changes_with_edits_and_ignores_polygons():
    project, op = _fresh()
    res = op.result
    r0 = cn_editor.result_rev(res)
    assert r0 == cn_editor.result_rev(CuttingResult.model_validate(res.model_dump()))
    out = _apply(project, op, res, type="comment", map=1, comment="x")
    assert cn_editor.result_rev(out) != r0
    out2 = _apply(project, op, res, type="move", map=1, index=0, dx=0.0, dy=0.0)
    assert cn_editor.result_rev(out2) == r0                          # o'zgarmagan joylashuv — iz ham o'zgarmaydi
    assert cn_editor.result_rev(None) == "none"


def test_edit_with_contour_parts_and_in_hole_remnants():
    prog = [cmd("MillRect", X=250, Y=200, L=500, W=400, R=40, DP=16, T="M"), cmd("MillRect", X=250, Y=200, L=300, W=200, R=10, DP=16, T="M")]
    project, op = make_project([dict(length=500, width=400, qty=1), dict(length=100, width=80, qty=2)], [(1200, 800)], xnc={0: prog},
                               cn=dict(remnant_min_side1=150, remnant_min_side2=100, remnant_min_area=0.02))
    run(project, op, "normal")
    res = op.result
    assert res.unplaced == []
    pls = res.maps[0].placements
    big = next(p for p in pls if p.part_uid == 1)
    assert len(big.holes) == 1 and len(big.outline) > 8
    assert _valid(project, op, res) == []
    # kontur detalni siljitish ham `validate_cn` dan o'tadi (qaysi tomonda joy bo'lsa o'sha tomonga)
    moved = None
    for d in ("right", "down", "left", "up"):
        try:
            moved = _apply(project, op, res, type="slide", map=1, index=_idx(res, 1), dir=d)
            break
        except EditError:
            continue
    assert moved is not None and _valid(project, op, moved) == []
    # qoldiqlar: ichki kesimdagi (in_part) yoki detalsiz — hammasi detallardan ≥ spacing da
    spacing = op.cn.spacing + op.cn.arc_tol
    for o in res.maps[0].offcuts:
        rect = [(o.x, o.y), (o.x + o.length, o.y), (o.x + o.length, o.y + o.width), (o.x, o.y + o.width)]
        rp = G.orient_ring(rect, True)
        for pl in pls:
            pv = V.Poly(pl.part_uid, [tuple(p) for p in pl.outline], [[tuple(p) for p in h] for h in pl.holes])
            rv = V.Poly(0, rp, [])
            if V.conflicts(rv, pv, spacing - 1e-3):
                pytest.fail(f"qoldiq {o.number} detal {pl.part_uid} ga yaqin")

