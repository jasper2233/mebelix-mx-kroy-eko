"""W16 (CN) — hisob: kroygacha taxmin (formula), kroydan keyin narx, operatsiya narxi asoslari, yaxlitlash, qoldiq maydoni (sarfdan ayiriladi),
natija ko'rsatkichlari (LT, CT, F, AP), qoldiq qoidalari (ichki kesimdagi qoldiq), hisoblangan miqdorlar."""
from __future__ import annotations

import math

import pytest

from app.models import OpCostBase, SheetRounding
from app.services import cn_calc
from cn_w16_proj import cmd, make_project, run


def test_estimate_before_cutting_follows_cs_formula():
    project, op = make_project([dict(length=500, width=400, qty=3), dict(length=300, width=200, qty=2)], [(2750, 1830)],
                               cn=dict(price=1000, est_fill_percent=80))
    info = cn_calc.cn_cost(project, op)
    area = (0.5 * 0.4 * 3 + 0.3 * 0.2 * 2)
    assert info["estimated"] is True
    assert info["material_qty_m2"] == pytest.approx(round(area * (2 - 0.8), 4), abs=1e-4)
    assert info["sheets"] == math.ceil(area * 1.2 / (2.75 * 1.83) - 1e-9)
    assert op.cost_material == pytest.approx(info["sheets"] * 1000)
    # m² bo'yicha
    op.cn.cost_by_sheets = False
    cn_calc.cn_cost(project, op)
    assert op.cost_material == pytest.approx(round(area * 1.2 * 1000, 2), abs=0.01)


def test_result_metrics_shape_area_perimeter_and_fill():
    prog = [cmd("MillRect", X=250, Y=200, L=500, W=400, R=0, DP=16, T="M"), cmd("MillRect", X=250, Y=200, L=200, W=100, R=0, DP=16, T="M")]
    project, op = make_project([dict(length=500, width=400, qty=1), dict(length=300, width=200, qty=1)], [(1200, 800)], xnc={0: prog})
    res = run(project, op, "fast")
    m = res.maps[0]
    net = 500 * 400 - 200 * 100 + 300 * 200
    assert m.parts_area_m2 == pytest.approx(net / 1e6, abs=2e-4)                    # teshik maydoni ayriladi
    per = 2 * (500 + 400) + 2 * (200 + 100) + 2 * (300 + 200)                       # tashqi + ichki konturlar
    assert m.cut_length_m == pytest.approx(per / 1000, abs=0.01) and m.cuts_count == 3
    assert m.fill_percent == pytest.approx(100 * net / 1e6 / (m.sheet_area_m2 - m.remnant_area_m2), abs=0.05)
    assert res.total_cut_length_m == m.cut_length_m and res.total_cuts == 3 and res.total_parts == 2
    assert res.material_qty_m2 == pytest.approx(res.material_area_m2 - res.remnant_area_m2, abs=1e-4)


@pytest.mark.parametrize("base", [OpCostBase.CUT_LENGTH, OpCostBase.PART_PERIMETER, OpCostBase.PART_AREA, OpCostBase.MATERIAL_AREA])
def test_operation_cost_bases(base):
    prog = [cmd("MillRect", X=100, Y=75, L=200, W=150, R=0, DP=16, T="M"), cmd("MillRect", X=100, Y=75, L=60, W=40, R=0, DP=16, T="M")]
    project, op = make_project([dict(length=200, width=150, qty=2)], [(1000, 700)], xnc={0: prog}, cn=dict(op_price=10.0, op_cost_base=base.value))
    res = run(project, op, "fast")
    info = cn_calc.cn_cost(project, op)
    expect = {OpCostBase.CUT_LENGTH: res.total_cut_length_m,
              OpCostBase.PART_PERIMETER: 2 * (200 + 150) * 2 / 1000,
              OpCostBase.PART_AREA: res.parts_area_m2,
              OpCostBase.MATERIAL_AREA: res.material_qty_m2}[base]
    assert info["op_base"] == pytest.approx(expect, abs=1e-3)
    assert op.cost_operation == pytest.approx(round(expect * 10.0, 2), abs=0.02)


def test_rounding_codes_for_last_sheet_fraction():
    # bitta karta, detallar listning chap-yuqori burchagida: kenglik bo'yicha band ulush
    project, op = make_project([dict(length=400, width=300, qty=1)], [(2000, 1000)], cn=dict(rot90=False, price=100.0))
    res = run(project, op, "fast")
    fl = (5 + 400) / 2000
    fw = (5 + 300) / 1000
    got = {}
    for code in ("11", "12", "13", "14", "22", "23", "24", "32", "33", "34"):
        op.cn.sheet_rounding = SheetRounding(code)
        got[code] = cn_calc.rounded_sheet_count(op)
    assert got["11"] == 1
    assert got["22"] == 0.5 and got["23"] == pytest.approx(1 / 3 * math.ceil(fw * 3 - 1e-9)) and got["24"] == 0.5
    assert got["32"] == 0.5 and got["33"] == pytest.approx(1 / 3) and got["34"] == pytest.approx(0.25)
    assert got["12"] == min(0.5, 0.5) and fl < fw
    # ko'p nusxali karta yaxlitlanmaydi
    res.maps[0].copies = 2
    assert cn_calc.rounded_sheet_count(op) == 2


def test_remnant_rules_business_min_sides_and_in_hole_flag():
    prog = [cmd("MillRect", X=300, Y=250, L=600, W=500, R=0, DP=16, T="M"), cmd("MillRect", X=300, Y=250, L=400, W=300, R=0, DP=16, T="M")]
    project, op = make_project([dict(length=600, width=500, qty=1)], [(800, 650)], xnc={0: prog},
                               cn=dict(remnant_min_side1=200, remnant_min_side2=150, remnant_min_area=0.1, margin=5))
    res = run(project, op, "fast")
    offs = res.maps[0].offcuts
    inner = [o for o in offs if o.in_part == 1]
    assert inner, "teshik ichidagi qoldiq (UPD-001) topilmadi"
    for o in inner:
        assert min(o.length, o.width) >= 150 and max(o.length, o.width) >= 200
        assert o.business == (o.length * o.width / 1e6 >= 0.1)
        assert max(o.length, o.width) <= 400 - 2 * 6.25 + 0.5 and min(o.length, o.width) <= 300 - 2 * 6.25 + 0.5      # teshikdan kichik (spacing)
        assert max(o.length, o.width) > 400 - 2 * 6.25 - 2 and min(o.length, o.width) > 300 - 2 * 6.25 - 2          # va unga deyarli teng (aniq kengaytirish)
    # qoldiqlar raqamlanadi va raw ≥ foydali
    assert [o.number for o in offs] == list(range(1, len(offs) + 1))
    assert all(o.raw_length >= o.length - 1e-6 and o.raw_width >= o.width - 1e-6 for o in offs)
    # chegara qiymatlari: yuqori min tomon — qoldiq bo'lmaydi
    op.cn.remnant_min_side1 = op.cn.remnant_min_side2 = 700
    res = run(project, op, "fast")
    assert res.maps[0].offcuts == []


def test_business_remnant_area_reduces_material_quantity():
    project, op = make_project([dict(length=500, width=400, qty=2)], [(2750, 1830)], cn=dict(remnant_min_side1=300, remnant_min_side2=200,
                                                                                            remnant_min_area=0.3, price=10.0, cost_by_sheets=False))
    res = run(project, op, "fast")
    m = res.maps[0]
    biz = sum(o.length * o.width for o in m.offcuts if o.business) / 1e6
    assert biz > 1.0 and m.remnant_area_m2 == pytest.approx(biz, abs=1e-3)
    assert res.material_qty_m2 == pytest.approx(m.sheet_area_m2 - biz, abs=1e-3)
    assert op.cost_material == pytest.approx(round(res.material_qty_m2 * 10, 2), abs=0.02)
    # F: деловой qoldiqsiz maydonga nisbatan
    assert m.fill_percent == pytest.approx(100 * m.parts_area_m2 / (m.sheet_area_m2 - biz), abs=0.05)



def test_label_spot_cache_distinguishes_rotated_rects():
    """Bir xil maydon / nuqtalar soni / koordinatalar yig'indisiga ega 300×200 va 200×300 detallar etiketkasi aralashib ketmasin."""
    project, op = make_project([dict(length=300, width=200), dict(length=200, width=300)], [(2000, 1000)])
    a = cn_calc.label_for(cn_calc.build_items(project, op).shapes[op.parts[0].id], op.cn)
    b = cn_calc.label_for(cn_calc.build_items(project, op).shapes[op.parts[1].id], op.cn)
    assert a["label"][:2] == [150.0, 100.0] and b["label"][:2] == [100.0, 150.0]
    res = run(project, op, "fast")
    for pl in res.maps[0].placements:                      # joylashgan etiketka o'rni detal o'rovchi to'rtburchagi ichida
        cx, cy = pl.label[0], pl.label[1]
        assert pl.x <= cx <= pl.x + pl.length and pl.y <= cy <= pl.y + pl.width


def test_label_spot_with_drills_in_result_avoids_machining():
    prog = [cmd("DrillFront", X=150, Y=100, DP=10, D=20, T="D20")]
    project, op = make_project([dict(length=300, width=200)], [(1000, 700)], xnc={0: prog})
    res = run(project, op, "fast")
    pl = res.maps[0].placements[0]
    cx, cy, w, h, ang = pl.label
    assert ang in (0.0, 90.0, 180.0, 270.0)
    # teshik (markazda, r = 10) etiketka to'rtburchagiga kirmaydi
    hx, hy = pl.x + 150, pl.y + 100 if pl.angle == 0 else None
    if pl.angle == 0:
        dx, dy = max(abs(cx - hx) - w / 2, 0), max(abs(cy - hy) - h / 2, 0)
        assert (dx * dx + dy * dy) ** 0.5 >= 10
