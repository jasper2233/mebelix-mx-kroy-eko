"""W16 (CN) — mustaqil tekshiruvchi `cn_validate`: to'g'ri joylashuv o'tadi, har bir buzilish aniqlanadi (kesishish, masofa, list chetidan
masofa, burilish qoidasi, soni, saqlangan kontur mosligi, ichki kesimdagi detal)."""
from __future__ import annotations

import pytest

from app.i18n import _
from app.models import CutMap, CuttingResult
from app.services import cn_calc
from app.services import cn_geometry as G
from app.services import cn_validate as V
from cn_w16_proj import cmd, make_project, run


def _spec(op, ci, uid, angle, x, y):
    part = next(p for p in op.parts if p.uid == uid)
    return cn_calc.Spec(part, ci.shapes[part.id], angle, x, y)


def _result(project, op, ci, specs, sheet_idx=0, copies=1):
    cn = op.cn
    st = op.sheets[sheet_idx]
    m = cn_calc.make_map(1, st, copies, specs, cn, {}, [])        # qoldiq: bo'sh (tekshiruvga ta'sir qilmaydi)
    res = CuttingResult(maps=[m], kind="nest")
    return cn_calc.finish_result(res)


def _errors(project, op, ci, res):
    return V.validate_cn(res, ci.shapes, ci.need, ci.grains, op.sheets, op.cn)


@pytest.fixture()
def setup():
    project, op = make_project([dict(length=300, width=200, qty=2), dict(length=100, width=80, qty=2, grain=True)], [(1000, 700)],
                               cn=dict(margin=5, tool_diameter=6, part_gap=2))      # spacing = 6 + 2 + arc_tol 0.25 = 8.25
    ci = cn_calc.build_items(project, op)
    return project, op, ci


def test_valid_layout_passes(setup):
    project, op, ci = setup
    specs = [_spec(op, ci, 1, 0.0, 5, 5), _spec(op, ci, 1, 0.0, 320, 5), _spec(op, ci, 2, 0.0, 5, 220), _spec(op, ci, 2, 180.0, 120, 220)]
    res = _result(project, op, ci, specs)
    assert _errors(project, op, ci, res) == []
    assert res.maps[0].placements[0].outline and res.maps[0].placements[0].angle == 0


def test_overlap_gap_outside_are_detected(setup):
    project, op, ci = setup
    # kesishish
    res = _result(project, op, ci, [_spec(op, ci, 1, 0.0, 5, 5), _spec(op, ci, 1, 0.0, 100, 50)])
    errs = _errors(project, op, ci, res)
    assert errs == [_("cn.v_overlap", map=1, a=1, b=1)]
    # masofa: 6 mm (spacing 8.25 dan kam, lekin kesishmaydi)
    res = _result(project, op, ci, [_spec(op, ci, 1, 0.0, 5, 5), _spec(op, ci, 1, 0.0, 311, 5)])
    errs = _errors(project, op, ci, res)
    assert len(errs) == 1 and "6" in errs[0]
    # masofa aynan spacing da — mumkin
    res = _result(project, op, ci, [_spec(op, ci, 1, 0.0, 5, 5), _spec(op, ci, 1, 0.0, 313.25, 5)])
    assert _errors(project, op, ci, res) == []
    # list chetidan masofa: margin 5 — x = 4 dan chiqish; list tashqarisi
    for x, y in ((4.0, 5.0), (5.0, 4.0), (701.0, 5.0), (5.0, 496.0)):
        res = _result(project, op, ci, [_spec(op, ci, 1, 0.0, x, y)])
        assert len(_errors(project, op, ci, res)) == 1, (x, y)


def test_part_inside_solid_material_or_hole(setup):
    project, op = make_project([dict(length=400, width=300), dict(length=60, width=40)], [(1000, 700)],
                               xnc={0: [cmd("MillRect", X=200, Y=150, L=400, W=300, R=0, DP=16, T="M"),
                                        cmd("MillRect", X=200, Y=150, L=200, W=140, R=0, DP=16, T="M")]})
    ci = cn_calc.build_items(project, op)
    host = _spec(op, ci, 1, 0.0, 100, 100)
    # kichik detal paneling qattiq qismida (teshikdan tashqarida, chetdan uzoqda): ichki chegara masofasi ≥ spacing bo'lsa ham — kesishish
    res = _result(project, op, ci, [host, _spec(op, ci, 2, 0.0, 120, 120)])
    assert any("1" in e and "2" in e for e in _errors(project, op, ci, res))
    # teshik ichida (hamma tomondan ≥ spacing): to'g'ri
    hole_x0, hole_y0 = 100 + 100, 100 + 80
    res = _result(project, op, ci, [host, _spec(op, ci, 2, 0.0, hole_x0 + 30, hole_y0 + 40)])
    assert _errors(project, op, ci, res) == []
    # teshik ichida, lekin chegaraga masofa kam
    res = _result(project, op, ci, [host, _spec(op, ci, 2, 0.0, hole_x0 + 3, hole_y0 + 40)])
    assert len(_errors(project, op, ci, res)) == 1


def test_angle_rules_count_and_stock(setup):
    project, op, ci = setup
    # Ткт ✓ detal 90° — taqiqlangan
    res = _result(project, op, ci, [_spec(op, ci, 2, 90.0, 5, 5)])
    assert len(_errors(project, op, ci, res)) == 1
    # rot90 o'chiq bo'lsa 90° ruxsat emas; erkin burchak qadam bo'lsa — ruxsat
    project2, op2 = make_project([dict(length=300, width=100)], [(1000, 700)], cn=dict(rot90=False))
    ci2 = cn_calc.build_items(project2, op2)
    assert not V.angle_ok(90.0, False, op2.cn) and V.angle_ok(0.0, False, op2.cn)
    op2.cn.rot_step = 30.0
    assert V.angle_ok(30.0, False, op2.cn) and V.angle_ok(60.0, False, op2.cn) and not V.angle_ok(45.0, False, op2.cn)
    del ci2
    # soni ОК − МК dan ko'p
    res = _result(project, op, ci, [_spec(op, ci, 1, 0.0, 5, 5), _spec(op, ci, 1, 0.0, 320, 5), _spec(op, ci, 1, 0.0, 5, 220)])
    assert any("3" in e and "2" in e for e in _errors(project, op, ci, res))
    # list nusxalari soni
    op.sheets[0].qty = 1
    res = _result(project, op, ci, [_spec(op, ci, 1, 0.0, 5, 5)], copies=2)
    assert len(_errors(project, op, ci, res)) == 1


def test_saved_outline_must_match_shape_and_transform(setup):
    project, op, ci = setup
    res = _result(project, op, ci, [_spec(op, ci, 1, 0.0, 5, 5)])
    assert _errors(project, op, ci, res) == []
    res.maps[0].placements[0].outline[2][0] += 5.0                 # soxta kontur
    assert len(_errors(project, op, ci, res)) == 1
    # joylashuvni o'zgartirib, konturni eskisicha qoldirish ham xato
    res = _result(project, op, ci, [_spec(op, ci, 1, 0.0, 5, 5)])
    res.maps[0].placements[0].x += 30
    assert len(_errors(project, op, ci, res)) == 1


def test_empty_map_and_unknown_part_and_sheet(setup):
    project, op, ci = setup
    res = _result(project, op, ci, [])
    assert len(_errors(project, op, ci, res)) == 1
    assert V.validate_cn(res, ci.shapes, ci.need, ci.grains, op.sheets, op.cn, allow_empty=True) == []
    res = _result(project, op, ci, [_spec(op, ci, 1, 0.0, 5, 5)])
    res.maps[0].sheet_id = "yoq"
    assert len(_errors(project, op, ci, res)) == 1


def test_low_level_check_polys_matches_expectations():
    a = V.Poly(1, G.rect_ring(100, 100), [])
    b = V.Poly(2, [(p[0] + 100, p[1]) for p in G.rect_ring(100, 100)], [])
    assert V.check_polys([a, b], 1000, 1000, 0, 0) == []                  # tegib turish (masofa 0) — ruxsat
    assert V.check_polys([a, b], 1000, 1000, 0, 0.5) != []                # 0.5 mm masofa talabi — buzilgan
    c = V.Poly(3, [(p[0] + 50, p[1] + 50) for p in G.rect_ring(100, 100)], [])
    assert V.check_polys([a, c], 1000, 1000, 0, 0)[0][0] == "cn.v_overlap"
    inner = V.Poly(4, [(p[0] + 30, p[1] + 30) for p in G.rect_ring(20, 20)], [])
    assert V.check_polys([a, inner], 1000, 1000, 0, 5)[0][0] == "cn.v_overlap"        # to'liq ichkarida — kesishish chegarasi yo'q, lekin ustma-ust
    ring = V.Poly(5, G.rect_ring(200, 200), [G.orient_ring([(50, 50), (150, 50), (150, 150), (50, 150)], False)])
    ok = V.Poly(6, [(p[0] + 80, p[1] + 80) for p in G.rect_ring(40, 40)], [])
    assert V.check_polys([ring, ok], 1000, 1000, 0, 10) == []                         # teshik ichida, 30 mm masofada
    tight = V.Poly(7, [(p[0] + 52, p[1] + 80) for p in G.rect_ring(40, 40)], [])
    assert V.check_polys([ring, tight], 1000, 1000, 0, 10)[0][0] == "cn.v_gap"
