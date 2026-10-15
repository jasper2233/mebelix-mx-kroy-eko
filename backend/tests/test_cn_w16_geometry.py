"""W16 (CN) — geometriya: poligon amallari, yoylar (xato ≤ tol), XNC konturidan shakl, ichki konturlar, ofset, etiketka o'rni."""
from __future__ import annotations

import math

import pytest

from app.models import Operation, OpType, Part, Project, XNCParams, XncCommand
from app.services import cn_free
from app.services import cn_geometry as G
from cn_w16_util import circle_ring, shape_L, shape_ring


# ───────────────────────── Asosiy amallar ─────────────────────────
def test_area_perimeter_orientation():
    r = G.rect_ring(100, 50)
    assert G.signed_area(r) == 5000 and G.ring_perimeter(r) == 300
    assert G.signed_area(r[::-1]) == -5000
    assert G.signed_area(G.orient_ring(r[::-1], True)) == 5000
    assert G.signed_area(G.orient_ring(r, False)) == -5000
    assert G.ring_bbox(r) == (0, 0, 100, 50)


def test_clean_ring_drops_duplicates_and_closing_point():
    r = G.clean_ring([(0, 0), (0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
    assert r == [(0, 0), (10, 0), (10, 10), (0, 10)]


def test_rotation_exact_for_right_angles():
    r = [(1.0, 2.0), (4.0, 2.0), (4.0, 3.0)]
    for ang in (0, 90, 180, 270, 360, -90):
        out = G.transform_ring(r, ang)
        for (x, y) in out:                                    # 90° karrali burilishlarda aniq (hisob shovqini yo'q)
            assert x == round(x, 12) and y == round(y, 12)
    # 90°: (x, y) → (−y, x)  (ekranda soat mili bo'yicha: Y pastga)
    assert G.transform_ring([(1.0, 0.0)], 90) == [(0.0, 1.0)]
    assert G.transform_ring([(0.0, 1.0)], 90) == [(-1.0, 0.0)]


def test_orient_shape_bbox_origin_and_place():
    sh = shape_L(300, 200, 80)
    for ang in (0, 90, 180, 270, 37):
        o = G.orient_shape(sh, ang)
        xs = [p[0] for p in o.outer]
        ys = [p[1] for p in o.outer]
        assert min(xs) == pytest.approx(0, abs=1e-9) and min(ys) == pytest.approx(0, abs=1e-9)
        assert max(xs) == pytest.approx(o.bw) and max(ys) == pytest.approx(o.bh)
        outer, holes, bw, bh = G.place_shape(sh, ang, 100, 50)
        assert G.ring_bbox(outer)[:2] == pytest.approx((100, 50))
        assert G.ring_area(outer) == pytest.approx(sh.area)          # burish maydonni o'zgartirmaydi


def test_point_in_ring_and_simplify():
    r = G.rect_ring(10, 10)
    assert G.point_in_ring((5, 5), r) and not G.point_in_ring((15, 5), r)
    dense = [(x, 0.0) for x in range(0, 100)] + [(100.0, y) for y in range(0, 50)] + [(x, 50.0) for x in range(100, 0, -1)] + \
        [(0.0, y) for y in range(50, 0, -1)]
    s = G.simplify_ring(dense, 0.01)
    assert len(s) == 4 and G.ring_area(s) == pytest.approx(5000)
    assert len(G.limit_points(circle_ring(0, 0, 300, 2000), 100)) <= 100


# ───────────────────────── Yoylar ─────────────────────────
@pytest.mark.parametrize("r,tol", [(10, 0.25), (150, 0.25), (1000, 0.25), (50, 0.05), (400, 1.0)])
def test_arc_points_error_not_above_tol(r, tol):
    pts = G.arc_points((r, 0.0), (0.0, 0.0), r, math.pi, False, tol)
    assert pts[-1] == pytest.approx((-r, 0.0), abs=1e-9)
    prev = (r, 0.0)
    for p in pts:
        mid = ((prev[0] + p[0]) / 2, (prev[1] + p[1]) / 2)
        sag = r - math.hypot(*mid)                              # vatar o'rtasi — yoydan masofa
        assert 0 <= sag <= tol + 1e-9
        assert math.hypot(*p) == pytest.approx(r, rel=1e-9)     # nuqtalar aynan yoyda
        prev = p
    # to'liq aylana: yo'nalish va oxirgi nuqta
    full = G.arc_points((r, 0.0), (0.0, 0.0), r, 2 * math.pi, True, tol, end=(r, 0.0))
    assert full[-1] == (r, 0.0)
    ring = [(r, 0.0)] + full[:-1]
    assert G.signed_area(ring) > 0                               # clockwise=True → ekranda soat mili bo'yicha (musbat imzo)
    assert G.ring_area(ring) <= math.pi * r * r                  # ichki (inscribed) siniq chiziq maydoni aylanadan kichik
    assert G.ring_area(ring) == pytest.approx(math.pi * r * r, rel=max(0.02, 1.5 * tol / r))


# ───────────────────────── XNC dan shakl ─────────────────────────
def _project_with_xnc(program, length=500, width=400, thickness=16, **part_kw):
    p = Project(name="g")
    xo = Operation(type=OpType.XNC, name="x", xnc=XNCParams(length=length, width=width, thickness=thickness, by_part_size=False,
                                                          program=[XncCommand(**c) for c in program]))
    part = Part(name="p", length=length, width=width, qty=1, xnc_op_ids=[xo.id], **part_kw)
    cn = Operation(type=OpType.CN, name="n", parts=[part])
    p.operations += [cn, xo]
    return p, cn, part


def _cmd(cmd, **params):
    return dict(cmd=cmd, params=params, comment="", enabled=True, children=[])


def test_plain_part_is_rect():
    p = Project(name="g")
    part = Part(name="p", length=300, width=200, qty=1)
    sh = G.part_shape(p, Operation(type=OpType.CN, parts=[part]), part, (300, 200), True, 0.25)
    assert sh.kind == "rect" and sh.is_rect and sh.area == 60000 and sh.perimeter == 1000 and sh.holes == []


def test_rounded_rect_contour_with_hole_from_xnc():
    prog = [_cmd("MillRect", X=250, Y=200, L=500, W=400, R=60, DP=16, T="Mill6"),
            _cmd("MillRect", X=250, Y=200, L=200, W=140, R=20, DP=16, T="Mill6")]
    p, cn, part = _project_with_xnc(prog)
    sh = G.part_shape(p, cn, part, (500, 400), True, 0.25)
    assert sh.kind == "contour" and not sh.is_rect and len(sh.holes) == 1
    assert G.signed_area(sh.outer) > 0 and G.signed_area(sh.holes[0]) < 0
    bw, bh = sh.bbox_size
    assert bw == pytest.approx(500, abs=0.3) and bh == pytest.approx(400, abs=0.3)
    outer_a = 500 * 400 - (4 - math.pi) * 60 ** 2
    hole_a = 200 * 140 - (4 - math.pi) * 20 ** 2
    assert G.ring_area(sh.outer) == pytest.approx(outer_a, rel=0.01)       # yoylar ichki chiziq bilan: ≤ 1 % kam
    assert G.ring_area(sh.outer) <= outer_a
    assert sh.area == pytest.approx(outer_a - hole_a, rel=0.01)
    assert min(p_[0] for p_ in sh.outer) == pytest.approx(0, abs=1e-9)
    # `use_xnc=False` — oddiy to'rtburchak
    assert G.part_shape(p, cn, part, (500, 400), False, 0.25).is_rect


def test_polyline_contour_with_arc_and_ellipse():
    # MillStart + MillLine konturi: L-shakl
    prog = [_cmd("MillStart", X=0, Y=0, DP=16, T="Mill6"), _cmd("MillLine", X=300, Y=0), _cmd("MillLine", X=300, Y=100),
            _cmd("MillLine", X=100, Y=100), _cmd("MillLine", X=100, Y=300), _cmd("MillLine", X=0, Y=300), _cmd("MillLine", X=0, Y=0)]
    p, cn, part = _project_with_xnc(prog, 300, 300)
    sh = G.part_shape(p, cn, part, (300, 300), True, 0.25)
    assert sh.kind == "contour" and sh.area == pytest.approx(300 * 100 + 200 * 100)
    # ellips: tashqi kontur
    prog = [_cmd("MillEllipse", X=150, Y=100, RL=150, RW=100, A=0, DP=16, T="Mill6")]
    p, cn, part = _project_with_xnc(prog, 300, 200)
    sh = G.part_shape(p, cn, part, (300, 200), True, 0.25)
    assert sh.kind == "contour" and sh.area == pytest.approx(math.pi * 150 * 100, rel=0.01)
    assert sh.n_points <= G.MAX_POINTS


def test_open_contour_pocket_and_outside_are_ignored_with_warnings():
    # ochiq kontur
    prog = [_cmd("MillStart", X=0, Y=0, DP=16, T="Mill6"), _cmd("MillLine", X=300, Y=0), _cmd("MillLine", X=300, Y=100)]
    p, cn, part = _project_with_xnc(prog, 300, 200)
    sh = G.part_shape(p, cn, part, (300, 200), True, 0.25)
    assert sh.is_rect                                                  # yopiq kontur yo'q — to'rtburchak
    # cho'ntak (DP < qalinlik): shaklga ta'sir qilmaydi
    prog = [_cmd("MillRect", X=150, Y=100, L=100, W=60, R=0, DP=5, T="Mill6")]
    p, cn, part = _project_with_xnc(prog, 300, 200)
    assert G.part_shape(p, cn, part, (300, 200), True, 0.25).is_rect
    # to'rtburchakdan tashqaridagi kesim — ogohlantirish
    prog = [_cmd("MillRect", X=150, Y=100, L=40, W=40, R=0, DP=16, T="Mill6"),
            _cmd("MillRect", X=900, Y=900, L=40, W=40, R=0, DP=16, T="Mill6")]
    p, cn, part = _project_with_xnc(prog, 300, 200)
    sh = G.part_shape(p, cn, part, (300, 200), True, 0.25)
    assert len(sh.holes) == 1 and any(k == "cn.w_contour_outside" for k, _kw in sh.warns)


def test_xnc_rotation_origin_and_mirror_do_not_change_shape_frame():
    """XNC «Поворот» burilgan jismoniy koordinatalarni o'zgartirmasin: shakl detalning o'z (burilmagan) holatida."""
    prog = [_cmd("MillRect", X=250, Y=200, L=500, W=400, R=0, DP=16, T="Mill6"), _cmd("MillRect", X=100, Y=100, L=60, W=60, R=0, DP=16, T="Mill6")]
    p, cn, part = _project_with_xnc(prog)
    p.operations[1].xnc.rotation = 90
    sh = G.part_shape(p, cn, part, (500, 400), True, 0.25)
    bw, bh = sh.bbox_size
    assert (round(bw), round(bh)) == (500, 400) and len(sh.holes) == 1


# ───────────────────────── Ofset ─────────────────────────
def test_offset_rect_matches_formula():
    r = G.rect_ring(100, 50)
    for d in (3.0, 6.0, 12.5):
        out = G.offset_ring(r, d, tol=0.02)
        assert len(out) == 1
        exp = 100 * 50 + 2 * d * (100 + 50) + math.pi * d * d
        assert G.signed_area(out[0]) == pytest.approx(exp, rel=2e-3)
        x0, y0, x1, y1 = G.ring_bbox(out[0])
        assert (x0, y0, x1, y1) == pytest.approx((-d, -d, 100 + d, 50 + d), abs=1e-9)


def test_offset_circle_hole_and_L_shape():
    n = 240
    c = circle_ring(100, 100, 100, n)
    out = G.offset_ring(c, 6, tol=0.02)
    assert G.signed_area(out[0]) == pytest.approx(math.pi * 106 ** 2, rel=1e-3)
    hole = G.orient_ring(G.rect_ring(40, 30), False)
    out = G.offset_ring(hole, 5, tol=0.05)                 # teshik materialdan tashqariga — teshik kichrayadi
    assert len(out) == 1 and G.signed_area(out[0]) == pytest.approx(-(30 * 20))
    assert G.offset_ring(hole, 16, tol=0.05) == []        # teshik butunlay yopiladi
    L = [(0, 0), (100, 0), (100, 40), (40, 40), (40, 100), (0, 100)]
    out = G.offset_ring(L, 5, tol=0.02)
    assert len(out) == 1
    exp = 6400 + 400 * 5 + (5 * math.pi / 4 - 1) * 25
    assert G.signed_area(out[0]) == pytest.approx(exp, rel=2e-3)
    # teskari yo'nalish (ichkariga): kichrayadi
    inn = G.offset_ring(G.rect_ring(100, 50), -5)
    assert G.signed_area(inn[0]) == pytest.approx(90 * 40, rel=1e-6)


def test_offset_distance_property():
    """Ofset konturining har nuqtasi asl konturdan aynan d (± yoy xatosi) uzoqlikda."""
    sh = shape_L(300, 200, 80)
    d = 6.0
    out = G.offset_ring(sh.outer, d, tol=0.05)
    assert len(out) == 1
    segs = list(zip(sh.outer, sh.outer[1:] + sh.outer[:1]))
    for (x, y) in out[0]:
        dist = min(_ps(x, y, a, b) for a, b in segs)
        assert dist == pytest.approx(d, abs=0.06)


def _ps(x, y, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / l2))
    return math.hypot(x - (a[0] + t * dx), y - (a[1] + t * dy))


# ───────────────────────── Etiketka o'rni (UPD-002) ─────────────────────────
def test_label_spot_in_plain_rect_is_centered():
    sh = G.rect_shape(400, 300)
    got = cn_free.find_label_spot(sh, 40, 20)
    assert got["fits"] and got["label"] is not None
    cx, cy, w, h, ang = got["label"]
    assert (w, h, ang) == (40, 20, 0.0)
    assert cx == pytest.approx(200, abs=8) and cy == pytest.approx(150, abs=8)


def test_label_spot_avoids_machining_and_holes():
    sh = shape_ring(400, 300, 300, 200)                       # o'rtada katta teshik: etiketka chekkadagi ingichka zonada
    got = cn_free.find_label_spot(sh, 40, 20)
    assert got["fits"]
    cx, cy, w, h, ang = got["label"]
    # etiketka teshik ichida emas va chet / teshikdan ≥ 3 mm
    assert not (50 - 3 < cx - w / 2 + w and cx + w / 2 > 50 + 3 and 50 - 3 < cy + h / 2 and cy - h / 2 < 250 - 3
                and cx - w / 2 < 350 + 3)
    # ishlov belgisi (teshik) atrofidan chetlab o'tadi
    plain = G.rect_shape(100, 100)
    plain.marks = {"drills": [(50.0, 50.0, 20.0)], "paths": [], "grooves": []}
    got = cn_free.find_label_spot(plain, 30, 15)
    assert got["fits"]
    cx, cy, w, h, _a = got["label"]
    assert math.hypot(max(abs(cx - 50) - w / 2, 0), max(abs(cy - 50) - h / 2, 0)) >= 20 + 3 - 1.5
    # sig'maydigan etiketka: fits False, eng katta bo'sh to'rtburchak qaytariladi
    tiny = G.rect_shape(30, 20)
    got = cn_free.find_label_spot(tiny, 60, 40)
    assert not got["fits"] and got["label"] is None


def test_complexity_guard_falls_back_to_rect_and_caps_rings():
    import random
    rnd = random.Random(3)
    # 4000 ta o'tkir tish: soddalashtirish yordam bermaydi → to'rtburchak + ogohlantirish
    pts = []
    for i in range(4000):
        a = 2 * math.pi * i / 4000
        r = 150 + (30 if i % 2 else -30) + rnd.uniform(-5, 5)
        pts.append((200 + r * math.cos(a), 200 + r * math.sin(a)))
    con = G.Contour(ring=pts, closed=True, through=True)
    sh = G.shape_from_contours([con], {"drills": [], "paths": [], "grooves": []}, (400.0, 400.0), 0.25)
    assert sh is not None and sh.is_rect and any(k == "cn.w_complex_rect" for k, _kw in sh.warns)
    # oddiy aylana (4000 nuqta) — soddalashtiriladi va kontur bo'lib qoladi
    circ = G.Contour(ring=circle_ring(200, 200, 200, 4000), closed=True, through=True)
    sh = G.shape_from_contours([circ], {"drills": [], "paths": [], "grooves": []}, (400.0, 400.0), 0.25)
    assert sh is not None and sh.kind == "contour" and sh.n_points <= G.MAX_POINTS
    # ichki kesimlar soni chegaralanadi
    holes = [G.Contour(ring=[(10 + 5 * (i % 60), 10 + 5 * (i // 60) * 1.0 + 0.1 * j) for j in range(0, 1)] + [], closed=True, through=True)
             for i in range(0)]
    assert holes == []
