"""W1 · Frezalash kengaytmalari: MillStart (sdp, sxy, in, out, c), cho'ntak (C=3) hisob qoidasi, MillFillet (burchak
yumaloqlash: geometriya, uzunlik, chizma), MillRect / MillEllipse (markaz, A, R, RL/RW), qirra teshigi «Середина по Z»
(M), paz C/P."""
import math

import pytest

from app.models import Operation, OpType, XNCParams, XncCommand as C
from app.services import xnc as X
from app.services.xnc import evaluate, program_stats, xnc_drawing_svg


def cmd(kind, /, **p):
    return C(cmd=kind, params=p)


def start(x=0, y=0, **kw):
    return cmd("MillStart", X=x, Y=y, DP=8, T="M6", **kw)


def line(x, y):
    return cmd("MillLine", X=x, Y=y)


def kinds(ops):
    return [o["kind"] for o in ops]


# ───────────────────────── MillStart parametrlari ─────────────────────────
def test_millstart_extra_attributes_evaluated():
    prog = [cmd("Tool", N="M6", D=6), cmd("MillStart", X=10, Y=20, DP=12, T="M6", C=2, SDP=4, SXY=2.5, IN=1, OUT=0),
            line(100, 20)]
    o = evaluate(prog, 800, 600, 16)[0]
    assert o["C"] == 2 and o["SDP"] == 4 and o["SXY"] == 2.5 and o["IN"] == 1 and o["OUT"] == 0 and o["DP"] == 12
    # standartlar: SDP — yo'q (nan), SXY — asbob diametri/2, IN=0, OUT=1
    prog = [cmd("Tool", N="M8", D=8), cmd("MillStart", X=0, Y=0, DP=8, T="M8")]
    o = evaluate(prog, 800, 600, 16)[0]
    assert math.isnan(o["SDP"]) and o["SXY"] == 4 and (o["IN"], o["OUT"]) == (0, 1) and o["C"] == 0
    # ifodali SDP / SXY: o'zgaruvchi orqali
    prog = [cmd("Var", name="st", value="dz/4"), cmd("MillStart", X=0, Y=0, DP="dz", T="M8", SDP="st", SXY="st+1")]
    o = evaluate(prog, 800, 600, 16)[0]
    assert o["SDP"] == 4 and o["SXY"] == 5
    # frezalash uzunligiga ta'sir qilmaydi (bir o'tish)
    a = program_stats([start(0, 0), line(100, 0)], 800, 600, 16)["mill_m"]
    b = program_stats([start(0, 0, SDP=2, SXY=3, IN=1, OUT=1), line(100, 0)], 800, 600, 16)["mill_m"]
    assert a == b == 0.1


def test_pocket_correction_excluded_from_length():
    """C=3 (cho'ntak): kontur «длина фрезерования» ga kirmaydi (korxona fayllarida saqlangan countMill = 0)."""
    contour = [line(100, 0), line(100, 50), line(0, 50), line(0, 0)]
    assert program_stats([start(0, 0, C=0)] + contour, 800, 600, 16)["mill_m"] == 0.3
    assert program_stats([start(0, 0, C=3)] + contour, 800, 600, 16)["mill_m"] == 0
    # keyingi oddiy kontur esa hisoblanadi
    prog = [start(0, 0, C=3)] + contour + [start(200, 0, C=1), line(300, 0)]
    assert program_stats(prog, 800, 600, 16)["mill_m"] == 0.1
    # konstanta orqali almashtiriladi
    old = X.POCKET_COUNTS_IN_LENGTH
    X.POCKET_COUNTS_IN_LENGTH = True
    try:
        assert program_stats([start(0, 0, C=3)] + contour, 800, 600, 16)["mill_m"] == 0.3
    finally:
        X.POCKET_COUNTS_IN_LENGTH = old


def test_pocket_drawn_with_fill():
    op = Operation(type=OpType.XNC, xnc=XNCParams(length=200, width=100, thickness=16, by_part_size=False,
                                                  program=[start(10, 10, C=3), line(90, 10), line(90, 60), line(10, 60)]))
    svg = xnc_drawing_svg(op)
    assert 'fill-opacity=".18"' in svg
    op.xnc.program[0].params["C"] = 0
    assert 'fill-opacity=".18"' not in xnc_drawing_svg(op)


# ───────────────────────── MillFillet ─────────────────────────
def test_fillet_right_angle_geometry_and_length():
    prog = [start(0, 0), line(100, 0), cmd("MillFillet", R=10), line(100, 100)]
    ops = evaluate(prog, 800, 600, 16)
    assert kinds(ops) == ["MillStart", "MillLine", "MillArcCenter", "MillLine"]
    l1, arc, l2 = ops[1], ops[2], ops[3]
    assert (l1["X"], l1["Y"]) == (90, 0)                                # oldingi chiziq qisqaradi
    assert (arc["X"], arc["Y"], arc["CX"], arc["CY"]) == (100, 10, 90, 10) and arc["fillet"]
    assert (l2["X"], l2["Y"]) == (100, 100)
    st = program_stats(prog, 800, 600, 16)
    assert st["mill_m"] == pytest.approx((90 + math.pi * 10 / 2 + 90) / 1000, abs=1e-3) and st["errors"] == 0


@pytest.mark.parametrize("pts,expect_t", [
    (((0, 0), (100, 0), (100, 100)), 10),                               # 90°
    (((0, 0), (100, 0), (150, 86.6025403784)), 10 / math.tan(math.radians(120) / 2)),         # P dagi ichki burchak 120° (to'mtoq)
    (((0, 0), (100, 0), (50, 86.6025403784)), 10 / math.tan(math.radians(60) / 2)),           # ichki burchak 60° (o'tkir)
])
def test_fillet_arc_is_tangent_to_both_lines(pts, expect_t):
    (ax, ay), (px, py), (bx, by) = pts
    prog = [start(ax, ay), line(px, py), cmd("MillFillet", R=10), line(bx, by)]
    ops = evaluate(prog, 800, 600, 16)
    t1 = (ops[1]["X"], ops[1]["Y"])
    arc = ops[2]
    t2 = (arc["X"], arc["Y"])
    cen = (arc["CX"], arc["CY"])
    assert math.dist(t1, (px, py)) == pytest.approx(expect_t, abs=1e-6)       # tangens uzunligi
    assert math.dist(t2, (px, py)) == pytest.approx(expect_t, abs=1e-6)
    assert math.dist(t1, cen) == pytest.approx(10, abs=1e-4) and math.dist(t2, cen) == pytest.approx(10, abs=1e-4)
    # radius chiziqqa tik: (cen - t1) · yo'nalish = 0
    d1 = (px - ax, py - ay)
    assert (cen[0] - t1[0]) * d1[0] + (cen[1] - t1[1]) * d1[1] == pytest.approx(0, abs=1e-3)
    d2 = (bx - px, by - py)
    assert (cen[0] - t2[0]) * d2[0] + (cen[1] - t2[1]) * d2[1] == pytest.approx(0, abs=1e-3)
    # uzunlik: A→T1 + yoy + T2→B
    r, sw = X.arc_sweep(t1, t2, cen, arc["DIR"])
    assert r == pytest.approx(10, abs=1e-4) and 0 < sw < math.pi
    exp = math.dist((ax, ay), t1) + r * sw + math.dist(t2, (bx, by))
    assert program_stats(prog, 800, 600, 16)["mill_m"] == pytest.approx(exp / 1000, abs=1e-3)


def test_fillet_both_turn_directions_and_chain():
    for sign in (1, -1):                                                # chapga / o'ngga burilish
        prog = [start(0, 0), line(100, 0), cmd("MillFillet", R=10), line(100, 100 * sign)]
        arc = evaluate(prog, 800, 600, 16)[2]
        assert (arc["CX"], arc["CY"]) == (90, 10 * sign) and arc["DIR"] == ("true" if sign > 0 else "false")
    # zanjir: to'rtburchak, to'rt burchakda yumaloqlash (kirish — tomon o'rtasida)
    prog = [start(50, 0), line(100, 0), cmd("MillFillet", R=10), line(100, 80), cmd("MillFillet", R=10), line(0, 80),
            cmd("MillFillet", R=10), line(0, 0), cmd("MillFillet", R=10), line(50, 0)]
    st = program_stats(prog, 800, 600, 16)
    assert st["mill_m"] == pytest.approx((2 * (100 + 80) - 8 * 10 + 2 * math.pi * 10) / 1000, abs=1e-3) and st["errors"] == 0
    ops = evaluate(prog, 800, 600, 16)
    assert kinds(ops).count("MillArcCenter") == 4 and "MillFillet" not in kinds(ops)


def test_fillet_edge_cases_leave_corner_and_warn():
    # R = 0 yoki yo'q — o'zgarmaydi, xabarsiz
    for r in (0, -5):
        prog = [start(0, 0), line(100, 0), cmd("MillFillet", R=r), line(100, 100)]
        st = program_stats(prog, 800, 600, 16)
        assert st["mill_m"] == 0.2 and st["errors"] == 0
    # radius juda katta
    st = program_stats([start(0, 0), line(100, 0), cmd("MillFillet", R=200), line(100, 100)], 800, 600, 16)
    assert st["mill_m"] == 0.2 and st["errors"] == 1 and "200" in st["warnings"][0]
    # qo'shni chiziq emas (yoy yoki yo'q) — xabar
    st = program_stats([start(0, 0), cmd("MillFillet", R=5), line(100, 0)], 800, 600, 16)
    assert st["errors"] == 1 and st["mill_m"] == 0.1
    st = program_stats([start(0, 0), line(100, 0), cmd("MillFillet", R=5)], 800, 600, 16)
    assert st["errors"] == 1
    # (W18: yoy qo'shni endi qo'llab-quvvatlanadi — test_w18_xnc.py; kontur segmenti bo'lmagan qo'shni (MillRect) — hamon xabar)
    st = program_stats([cmd("MillRect", X=100, Y=80, L=60, W=40), cmd("MillFillet", R=5), line(100, 100)], 800, 600, 16)
    assert st["errors"] == 2                                                   # + MillStart siz MillLine xabari
    # to'g'ri chiziq (burchaksiz) — o'zgarmaydi, xabarsiz
    st = program_stats([start(0, 0), line(100, 0), cmd("MillFillet", R=5), line(200, 0)], 800, 600, 16)
    assert st["mill_m"] == 0.2 and st["errors"] == 0
    # R ifoda / o'zgaruvchi
    st = program_stats([cmd("Var", name="r", value="dz/2"), start(0, 0), line(100, 0), cmd("MillFillet", R="r"), line(100, 100)],
                       800, 600, 16)
    assert st["mill_m"] == pytest.approx((2 * (100 - 8) + math.pi * 8 / 2) / 1000, abs=1e-3) and st["errors"] == 0


def test_fillet_drawn_as_arc_and_respects_origin_and_view():
    prog = [start(0, 0), line(100, 0), cmd("MillFillet", R=10), line(100, 100)]
    op = Operation(type=OpType.XNC, xnc=XNCParams(length=200, width=200, thickness=16, by_part_size=False, program=prog))
    svg = xnc_drawing_svg(op)
    assert "M 0 0 L 90 0 A 10 10 0 0 1 100 10 L 100 100" in svg
    # koordinata boshi siljishi
    op.xnc.program = [cmd("Origin", X=20, Y=30)] + prog
    assert "M 20 30 L 110 30 A 10 10 0 0 1 120 40 L 120 130" in xnc_drawing_svg(op)


# ───────────────────────── MillRect / MillEllipse ─────────────────────────
def test_rect_center_semantics_length_and_drawing():
    prog = [cmd("MillRect", X=100, Y=80, L=60, W=40)]
    o = evaluate(prog, 800, 600, 16)[0]
    assert (o["X"], o["Y"], o["L"], o["W"], o["A"], o["R"]) == (100, 80, 60, 40, 0, 0)
    assert program_stats(prog, 800, 600, 16)["mill_m"] == pytest.approx(0.2)
    seg = X.rect_segments(o)
    assert [s[0] for s in seg] == ["M", "L", "L", "L", "L"]
    xs = [s[1] for s in seg]
    ys = [s[2] for s in seg]
    assert (min(xs), max(xs), min(ys), max(ys)) == (70, 130, 60, 100)          # markaz atrofida
    op = Operation(type=OpType.XNC, xnc=XNCParams(length=400, width=300, thickness=16, by_part_size=False, program=prog))
    assert "M 70 60 L 130 60 L 130 100 L 70 100 L 70 60 Z" in xnc_drawing_svg(op)


def test_rect_corner_radius_and_rotation():
    prog = [cmd("MillRect", X=100, Y=80, L=60, W=40, R=8)]
    st = program_stats(prog, 800, 600, 16)
    assert st["mill_m"] == pytest.approx((2 * 60 + 2 * 40 - 8 * 8 + 2 * math.pi * 8) / 1000, abs=1e-3)
    seg = X.rect_segments(evaluate(prog, 800, 600, 16)[0])
    assert [s[0] for s in seg].count("A") == 4
    # radius tomon yarmidan katta — kesiladi (stadion)
    st = program_stats([cmd("MillRect", X=100, Y=80, L=60, W=40, R=999)], 800, 600, 16)
    assert st["mill_m"] == pytest.approx((2 * (60 - 40) + 2 * math.pi * 20) / 1000, abs=1e-3)
    # burilish (gradus): 90° — L va W almashadi
    o = evaluate([cmd("MillRect", X=100, Y=80, L=60, W=40, A=90)], 800, 600, 16)[0]
    xs = [s[1] for s in X.rect_segments(o)]
    ys = [s[2] for s in X.rect_segments(o)]
    assert (min(xs), max(xs), min(ys), max(ys)) == (pytest.approx(80), pytest.approx(120), pytest.approx(50), pytest.approx(110))
    # burilish perimetrni o'zgartirmaydi
    assert program_stats([cmd("MillRect", X=100, Y=80, L=60, W=40, A=33)], 800, 600, 16)["mill_m"] == pytest.approx(0.2)
    # yoylar yopiq kontur hosil qiladi: har yoy oxiri keyingi chiziq boshi
    o = evaluate([cmd("MillRect", X=100, Y=80, L=60, W=40, R=8, A=25)], 800, 600, 16)[0]
    seg = X.rect_segments(o)
    assert math.dist(seg[0][1:3], (seg[-1][1], seg[-1][2])) < 1e-9


def test_rect_corner_semantics_constant():
    old = X.RECT_XY_IS_CENTER
    X.RECT_XY_IS_CENTER = False
    try:
        o = evaluate([cmd("MillRect", X=10, Y=20, L=60, W=40)], 800, 600, 16)[0]
        assert (o["X"], o["Y"]) == (40, 40)                             # burchak → markazga o'tkaziladi
    finally:
        X.RECT_XY_IS_CENTER = old


def test_rect_invalid_params_not_counted():
    st = program_stats([cmd("MillRect", X="zzz", Y=0, L=10, W=10)], 800, 600, 16)
    assert st["mill_m"] == 0 and st["errors"] >= 1


def test_ellipse_semi_axes_length_and_drawing():
    o = evaluate([cmd("MillEllipse", X=100, Y=100, RL=30, RW=20)], 800, 600, 16)[0]
    assert (o["RL"], o["RW"], o["A"]) == (30, 20, 0)
    a, b = 30, 20
    exp = math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))
    assert program_stats([cmd("MillEllipse", X=100, Y=100, RL=30, RW=20)], 800, 600, 16)["mill_m"] == pytest.approx(exp / 1000, abs=1e-3)
    # doira: RL = RW
    assert program_stats([cmd("MillEllipse", X=100, Y=100, RL=25, RW=25)], 800, 600, 16)["mill_m"] == pytest.approx(
        2 * math.pi * 25 / 1000, abs=1e-4)
    pts = X.ellipse_points(o)
    assert pts[0] == pts[-1] and len(pts) > 36
    assert all(abs(((x - 100) / 30) ** 2 + ((y - 100) / 20) ** 2 - 1) < 1e-9 for x, y in pts)
    # burilish: nuqtalar burilgan ellipsda yotadi
    o = evaluate([cmd("MillEllipse", X=100, Y=100, RL=30, RW=20, A=90)], 800, 600, 16)[0]
    assert all(abs(((x - 100) / 20) ** 2 + ((y - 100) / 30) ** 2 - 1) < 1e-9 for x, y in X.ellipse_points(o))
    op = Operation(type=OpType.XNC, xnc=XNCParams(length=400, width=300, thickness=16, by_part_size=False,
                                                  program=[cmd("MillEllipse", X=100, Y=100, RL=30, RW=20)]))
    svg = xnc_drawing_svg(op)
    assert 'Z"' in svg and "M 130 100" in svg                           # chizmada ellips bor


def test_ellipse_legacy_full_axes_params():
    """Eski dastur: A, B — to'liq o'qlar (burilishsiz) → RL = A/2, RW = B/2."""
    o = evaluate([cmd("MillEllipse", X=100, Y=100, A=80, B=40)], 800, 600, 16)[0]
    assert (o["RL"], o["RW"], o["A"]) == (40, 20, 0)


def test_rect_ellipse_depth_tool_and_pocket_flag():
    prog = [cmd("Tool", N="F6", D=6), cmd("MillRect", X=100, Y=80, L=60, W=40, DP=5, T="F6", C=3),
            cmd("MillEllipse", X=300, Y=80, RL=20, RW=10, DP="dz/2", T="F6")]
    r, e = evaluate(prog, 800, 600, 16)
    assert (r["D"], r["DP"], r["C"], r["T"]) == (6, 5, 3, "F6") and (e["D"], e["DP"], e["C"]) == (6, 8, 0)
    # cho'ntak (C=3) to'rtburchak uzunlikka kirmaydi, ellips kiradi
    assert program_stats(prog, 800, 600, 16)["mill_m"] == pytest.approx(
        X.ellipse_length(e) / 1000, abs=1e-3)


# ───────────────────────── Qirra teshigi «Середина по Z» (M) ─────────────────────────
def test_edge_hole_middle_flag():
    dz = 18
    prog = [cmd("DrillLeft", Y=50, Z=5, DP=30, M="true"), cmd("DrillRight", Y=50, Z=5, DP=30, M="false"),
            cmd("DrillTop", X=50, Z=5, DP=30), cmd("DrillBottom", X=50, Z=7, DP=30, M="true")]
    ops = evaluate(prog, 800, 600, dz)
    assert [o["Z"] for o in ops] == [9, 5, 5, 9]                        # M=true — o'rtada (dz/2), false/yo'q — Z
    assert [o["M"] for o in ops] == [True, False, False, True]
    # Z ham, M ham yo'q — o'rtada (standart)
    assert evaluate([cmd("DrillLeft", Y=50, DP=30)], 800, 600, 18)[0]["Z"] == 9


def test_groove_correction_attribute():
    o = evaluate([cmd("Groove", X1=0, Y1=20, X2=100, Y2=20, DP=8, W=4, C=2)], 800, 600, 16)[0]
    assert o["C"] == 2
    assert evaluate([cmd("Groove", X1=0, Y1=20, X2=100, Y2=20, DP=8, W=4)], 800, 600, 16)[0]["C"] == 0
