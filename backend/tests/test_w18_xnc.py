"""W18 · XNC bo'shliqlari: MillFillet chiziq–yoy / yoy–chiziq / yoy–yoy (geometriya), Par matn turi (`type=string`),
orqa yuzadan ishlov (`face_side=false`) uchun stanok cheklovlari, chizmada cheklov burishi (`xnc_drawing_svg(turn=…)`)."""
import copy
import json
import math
import random

import pytest

from app.models import Operation, OpType, XNCParams, XncCommand as C
from app.services import product_program as PP
from app.services import xnc as X
from app.services import xnc_constraints as XC
from app.services import xnc_fillet as F
from app.services.xnc import evaluate, program_stats, xnc_drawing_svg

from test_qa_fix_calc import _set_prog, _xnc_for
from test_xnc_w8_constraints import cmd, cons, codes, issues, project_of, xop

DIMS = (800, 600, 16)


def start(x=0.0, y=0.0):
    return cmd("MillStart", X=x, Y=y, DP=8, T="M6")


def line(x, y):
    return cmd("MillLine", X=x, Y=y)


def arcc(x, y, cx, cy, ccw):
    return cmd("MillArcCenter", X=x, Y=y, CX=cx, CY=cy, DIR="true" if ccw else "false")


def fillet(r):
    return cmd("MillFillet", R=r)


def kinds(ops):
    return [o["kind"] for o in ops]


# ───────────────────────── 1. MillFillet: chiziq–yoy, yoy–chiziq, yoy–yoy ─────────────────────────
def test_fillet_line_then_arc_known_geometry():
    """(0,0)→(100,0) chiziq, so'ng (100,0) dan markazi (150,0) radiusi 50 yoy (soat millariga teskari, 270° ga), R=10.
    Qo'lda hisob: fillet markazi y=−10, (x−150)² + 10² = 60² → x = 150 − √3500; T1 = (x, 0);
    T2 = c + 50·(C−c)/60."""
    prog = [start(0, 0), line(100, 0), arcc(150, -50, 150, 0, True)]
    full = program_stats(prog, *DIMS)["mill_m"]
    assert full == pytest.approx((100 + 50 * math.pi / 2) / 1000, abs=1e-3)
    prog = [start(0, 0), line(100, 0), fillet(10), arcc(150, -50, 150, 0, True)]
    ops = evaluate(prog, *DIMS)
    assert kinds(ops) == ["MillStart", "MillLine", "MillArcCenter", "MillArcCenter"]
    cx = 150 - math.sqrt(3500)
    t2 = (150 + 50 * (cx - 150) / 60, 50 * (-10) / 60)
    l1, fil, arc = ops[1], ops[2], ops[3]
    assert (l1["X"], l1["Y"]) == (pytest.approx(cx, abs=1e-5), 0)                      # chiziq T1 gacha qisqardi
    assert (fil["X"], fil["Y"]) == (pytest.approx(t2[0], abs=1e-5), pytest.approx(t2[1], abs=1e-5)) and fil["fillet"]
    assert (fil["CX"], fil["CY"]) == (pytest.approx(cx, abs=1e-5), pytest.approx(-10, abs=1e-5))
    assert fil["DIR"] == "false"                                                         # o'ngga burilish → soat bo'yicha
    assert (arc["X"], arc["Y"], arc["CX"], arc["CY"], arc["DIR"]) == (150, -50, 150, 0, "true")      # yoy: o'sha aylana, T2 dan
    # uzunlik: A→T1 + fillet yoyi + T2→oxiri (mustaqil formulalar)
    ang_t2 = math.atan2(t2[1], t2[0] - 150) % (2 * math.pi)                              # T2 burchagi (yoy markazidan, 0…2π)
    rest = 50 * (1.5 * math.pi - ang_t2)
    sweep = math.acos((t2[1] + 10) / 10)                                                 # (T1−C)=(0,10), (T2−C)·(0,10)/100
    exp = cx + 10 * sweep + rest
    assert program_stats(prog, *DIMS)["mill_m"] == pytest.approx(exp / 1000, abs=2e-3)
    assert program_stats(prog, *DIMS)["errors"] == 0


def test_fillet_arc_then_line_and_arc_arc_apply_and_keep_circles():
    # yoy → chiziq: (0,0)→(60,60) yoy (markaz (0,60), ccw emas), so'ng chiziq (160, 60)
    prog = [start(0, 0), arcc(60, 60, 0, 60, False), fillet(8), line(160, 60)]
    ops = evaluate(prog, *DIMS)
    assert kinds(ops) == ["MillStart", "MillArcCenter", "MillArcCenter", "MillLine"] and ops[2]["fillet"]
    assert (ops[1]["CX"], ops[1]["CY"], ops[1]["DIR"]) == (0, 60, "false")             # qisqargan yoy — o'sha aylana
    assert (ops[3]["X"], ops[3]["Y"]) == (160, 60)
    assert program_stats(prog, *DIMS)["errors"] == 0
    # yoy → yoy
    prog = [start(0, 0), arcc(60, 60, 0, 60, False), fillet(8), arcc(120, 0, 60, 0, False)]
    ops = evaluate(prog, *DIMS)
    assert kinds(ops).count("MillArcCenter") == 3 and ops[2]["fillet"]
    assert program_stats(prog, *DIMS)["errors"] == 0


def test_fillet_mill_arc_radius_and_three_point_neighbours_become_center_form():
    """MillArc R / MillArc3P qo'shni bo'lsa ham ishlaydi; qisqartirilgan yoy markazli shaklga o'tadi (aylana o'zgarmaydi)."""
    prog = [start(0, 0), cmd("MillArc", X=100, Y=0, R=60), fillet(5), line(100, 100)]
    ops = evaluate(prog, *DIMS)
    assert program_stats(prog, *DIMS)["errors"] == 0 and kinds(ops) == ["MillStart", "MillArcCenter", "MillArcCenter", "MillLine"]
    c1 = (ops[1]["CX"], ops[1]["CY"])
    assert math.dist((0, 0), c1) == pytest.approx(60, abs=1e-6) and math.dist((100, 0), c1) == pytest.approx(60, abs=1e-6)
    t1 = (ops[1]["X"], ops[1]["Y"])
    assert math.dist(t1, c1) == pytest.approx(60, abs=1e-4)                              # T1 — o'sha aylanada
    prog = [start(0, 0), cmd("MillArc3P", X=100, Y=0, X2=50, Y2=-30), fillet(5), line(100, 100)]
    ops = evaluate(prog, *DIMS)
    assert program_stats(prog, *DIMS)["errors"] == 0 and ops[2]["fillet"]


def _tangent(kind_op, p, ccw=None):
    """Segment yo'nalishi p nuqtada: chiziq — (u); yoy — aylana urinmasi."""
    if kind_op[0] == "L":
        a, b = kind_op[1], kind_op[2]
        ln = math.dist(a, b)
        return ((b[0] - a[0]) / ln, (b[1] - a[1]) / ln)
    c, ccw = kind_op[1], kind_op[2]
    rx, ry = p[0] - c[0], p[1] - c[1]
    r = math.hypot(rx, ry)
    return (-ry / r, rx / r) if ccw else (ry / r, -rx / r)


def _rand_prog(rng):
    """Tasodifiy ikki segment (chiziq yoki yoy) va fillet radiusi: (dastur, seg1, seg2, R); seg = ("L", a, b) | ("C", markaz, ccw, a, b)."""
    S = (0.0, 0.0)
    P = (rng.uniform(40, 160), rng.uniform(-80, 80))
    Q = (P[0] + rng.uniform(-150, 150), P[1] + rng.uniform(-150, 150))
    segs, prog = [], [start(*S)]
    for a, b in ((S, P), (P, Q)):
        if rng.random() < 0.5:
            prog.append(line(*b))
            segs.append(("L", a, b))
        else:
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            ch = math.dist(a, b)
            nx, ny = -(b[1] - a[1]) / ch, (b[0] - a[0]) / ch
            k = rng.choice((-1, 1)) * rng.uniform(0.3, 3.0) * ch / 2
            c = (mx + nx * k, my + ny * k)
            ccw = rng.random() < 0.5
            prog.append(arcc(b[0], b[1], c[0], c[1], ccw))
            segs.append(("C", c, ccw, a, b))
    R = rng.uniform(2, 25)
    prog.insert(2, fillet(R))
    return prog, segs, R


def _dist_to_line(p, a, b):
    ln = math.dist(a, b)
    return abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1])) / ln


def test_fillet_random_properties_all_four_combinations():
    """Tasodifiy 800 holat: fillet bo'lsa — (a) T1, T2 fillet markazidan R masofada, (b) ikkala segmentga urinadi (markaz–segment
    masofasi R), (c) T1 / T2 o'z segmentining ichida, (d) T1 va T2 da yo'nalish uzluksiz (G1). Bo'lmasa — burchak o'zgarishsiz + xabar."""
    rng = random.Random(20261002)
    ok = {("L", "L"): 0, ("L", "C"): 0, ("C", "L"): 0, ("C", "C"): 0}
    failed = 0
    for _i in range(800):
        prog, (s1, s2), R = _rand_prog(rng)
        ops = evaluate(prog, *DIMS)
        base = evaluate([c for c in prog if c.cmd != "MillFillet"], *DIMS)
        if not any(o.get("fillet") for o in ops):               # fillet qo'llanmadi: hech narsa o'zgarmagan, sababi xabarda
            failed += 1
            assert [(o["kind"], o["X"], o["Y"]) for o in ops] == [(o["kind"], o["X"], o["Y"]) for o in base]
            res = F.fillet(*(F.Seg(s[1], s[2]) if s[0] == "L" else F.Seg(s[3], s[4], s[1], s[2]) for s in (s1, s2)), R)
            assert isinstance(res, str)                          # to'g'ridan-to'g'ri geometriya ham rad etadi
            if res == "flat":
                assert not ops.messages
            else:
                assert len(ops.messages) == 1
                words = ("касательной", "urinuvchi") if res == "none" else ("велик", "katta")
                assert any(w in ops.messages[0] for w in words), (res, ops.messages)
            continue
        assert kinds(ops)[0] == "MillStart" and len(ops) == 4 and ops[2]["fillet"]
        o1, fo, o2 = ops[1], ops[2], ops[3]
        T1, T2, cen = (o1["X"], o1["Y"]), (fo["X"], fo["Y"]), (fo["CX"], fo["CY"])
        assert math.dist(T1, cen) == pytest.approx(R, abs=3e-5) and math.dist(T2, cen) == pytest.approx(R, abs=3e-5)
        ok[(s1[0], s2[0])] += 1
        P = s1[2] if s1[0] == "L" else s1[4]
        # (b) + (c): birinchi segment
        if s1[0] == "L":
            assert _dist_to_line(cen, s1[1], s1[2]) == pytest.approx(R, abs=3e-5)
            t = ((T1[0] - s1[1][0]) * (P[0] - s1[1][0]) + (T1[1] - s1[1][1]) * (P[1] - s1[1][1])) / math.dist(s1[1], P) ** 2
            assert -1e-6 <= t <= 1 + 1e-6 and _dist_to_line(T1, s1[1], P) < 3e-5
        else:
            c1, ccw1 = s1[1], s1[2]
            rho = math.dist(s1[3], c1)
            assert abs(math.dist(cen, c1) - rho) == pytest.approx(R, abs=3e-5)
            assert math.dist(T1, c1) == pytest.approx(rho, abs=3e-5)
            assert X.arc_sweep(s1[3], T1, c1, "true" if ccw1 else "false")[1] <= X.arc_sweep(s1[3], P, c1, "true" if ccw1 else "false")[1] + 1e-6
        # ikkinchi segment
        Q = s2[2] if s2[0] == "L" else s2[4]
        st2 = s2[1] if s2[0] == "L" else s2[3]
        if s2[0] == "L":
            assert _dist_to_line(cen, st2, Q) == pytest.approx(R, abs=3e-5) and _dist_to_line(T2, st2, Q) < 3e-5
            t = ((T2[0] - st2[0]) * (Q[0] - st2[0]) + (T2[1] - st2[1]) * (Q[1] - st2[1])) / math.dist(st2, Q) ** 2
            assert -1e-6 <= t <= 1 + 1e-6
        else:
            c2, ccw2 = s2[1], s2[2]
            rho = math.dist(st2, c2)
            assert abs(math.dist(cen, c2) - rho) == pytest.approx(R, abs=3e-5)
            assert math.dist(T2, c2) == pytest.approx(rho, abs=3e-5)
            d2 = "true" if ccw2 else "false"
            assert X.arc_sweep(st2, T2, c2, d2)[1] <= X.arc_sweep(st2, Q, c2, d2)[1] + 1e-6
            assert (o2["CX"], o2["CY"], o2["DIR"]) == (c2[0], c2[1], d2)               # aylana o'zgarmagan
        # (d) G1: T1 va T2 da yo'nalish uzluksiz
        fccw = fo["DIR"] == "true"
        ft1 = _tangent(("C", cen, fccw), T1)
        ft2 = _tangent(("C", cen, fccw), T2)
        g1 = _tangent(("L", s1[1], s1[2]) if s1[0] == "L" else ("C", s1[1], s1[2]), T1)
        g2 = _tangent(("L", st2, Q) if s2[0] == "L" else ("C", s2[1], s2[2]), T2)
        assert g1[0] * ft1[0] + g1[1] * ft1[1] == pytest.approx(1, abs=2e-4)
        assert g2[0] * ft2[0] + g2[1] * ft2[1] == pytest.approx(1, abs=2e-4)
    assert all(v >= 40 for v in ok.values()), ok            # to'rt birikma ham yetarlicha sinaldi
    assert failed > 0                                       # (R katta bo'lgan holatlar ham uchraydi)


def test_fillet_warnings_none_big_and_flat():
    # radius katta (qisqa chiziq + yoy): burchak o'zgarmaydi, xabar bor
    prog = [start(0, 0), line(100, 0), fillet(500), arcc(150, -50, 150, 0, True)]
    st = program_stats(prog, *DIMS)
    assert st["errors"] == 1 and "500" in st["warnings"][0]
    ops = evaluate(prog, *DIMS)
    assert kinds(ops) == ["MillStart", "MillLine", "MillArcCenter"] and (ops[1]["X"], ops[1]["Y"]) == (100, 0)
    # urinma aylana yo'q: chiziq (0,0)→(100,0) va undan (100,0) da deyarli qaytib kelayotgan yoy (markaz (60,−120), r≈126.5): chiziq
    # bilan yoy orasidagi «linza» eng qalin joyida 1.5 mm — radiusi 5 bo'lgan aylana sig'maydi, offsetlar kesishmaydi (R=1 sig'adi)
    r1 = math.hypot(40, 120)
    a1 = math.atan2(120, 40) + math.pi / 2
    end = (60 + r1 * math.cos(a1), -120 + r1 * math.sin(a1))
    seg1, seg2 = F.Seg((0, 0), (100, 0)), F.Seg((100, 0), end, (60, -120), True)
    assert F.fillet(seg1, seg2, 5) == "none" and isinstance(F.fillet(seg1, seg2, 1), F.Fillet)
    prog = [start(0, 0), line(100, 0), fillet(5), arcc(end[0], end[1], 60, -120, True)]
    st = program_stats(prog, *DIMS)
    assert st["errors"] == 1 and ("касательной" in st["warnings"][0] or "urinuvchi" in st["warnings"][0])
    assert program_stats([start(0, 0), line(100, 0), fillet(1), arcc(end[0], end[1], 60, -120, True)], *DIMS)["errors"] == 0
    # to'g'ri chiziq (burchaksiz) va qaytish
    assert F.fillet(F.Seg((0, 0), (10, 0)), F.Seg((10, 0), (20, 0)), 1) == "flat"
    assert F.fillet(F.Seg((0, 0), (10, 0)), F.Seg((10, 0), (0, 0)), 1) == "flat"
    assert F.fillet(F.Seg((0, 0), (10, 0)), F.Seg((10, 0), (10, 10)), 0) == "flat"
    # yoy bilan urinma davomi (chiziq + unga urinuvchi yoy): burchak yo'q — jim, o'zgarishsiz
    prog = [start(0, 0), line(100, 0), fillet(5), arcc(150, 50, 100, 50, False)]
    st = program_stats(prog, *DIMS)
    assert st["errors"] == 0 and kinds(evaluate(prog, *DIMS)) == ["MillStart", "MillLine", "MillArcCenter"]
    # kontur segmenti bo'lmagan qo'shni (MillRect) — avvalgidek xabar
    st = program_stats([cmd("MillRect", X=100, Y=80, L=60, W=40), fillet(5), line(100, 100)], *DIMS)
    assert st["errors"] == 2 and any("MillFillet" in w for w in st["warnings"])     # + MillStart siz MillLine xabari


def test_fillet_concentric_arcs_are_tangent_continuation_so_silent():
    """Bir markazli ikki yoy P da urinma davomi (burchak yo'q) — jim; markazlari bir xil bo'lgan yoy offsetlari kesishmaydi."""
    s1 = F.Seg((50, 0), (0, 50), (0, 0), True)
    s2 = F.Seg((0, 50), (-50, 0), (0, 0), True)
    assert F.fillet(s1, s2, 2) == "flat"
    # bir markazli, lekin yo'nalishi teskari (qaytish, kusp) — burchak emas
    assert F.fillet(s1, F.Seg((0, 50), (50, 0), (0, 0), False), 2) == "flat"
    # offset aylanalari kesishmaydi (bir markaz, farqli radius): to'g'ridan-to'g'ri `_inter`
    assert F._inter(("C", (0, 0), 10), ("C", (0, 0), 12)) == [] and F._inter(("C", (0, 0), 10), ("C", (50, 0), 12)) == []


def test_fillet_drawing_context_and_stats_agree():
    """Chizma (SVG), ishlov markazi konteksti va statistika bir xil yoylarni ko'radi."""
    prog = [start(10, 10), line(110, 10), fillet(10), arcc(160, -40, 160, 10, True)]
    op = Operation(type=OpType.XNC, xnc=XNCParams(length=300, width=200, thickness=16, by_part_size=False, program=prog))
    svg = xnc_drawing_svg(op)
    assert svg.count(" A ") + svg.count("A ") >= 2                                    # fillet yoyi + qisqargan yoy
    mp = X.machine_program(op)
    arcs = [o for o in mp["ops"] if o["kind"] == "mill_arc"]
    assert len(arcs) == 2 and arcs[0]["fillet"] is True and arcs[1]["fillet"] is False
    assert arcs[0]["radius"] == pytest.approx(10, abs=1e-4)
    # stanok konteksti uzunligi == statistika uzunligi (asosiy tekshiruv: bir xil evaluate())
    total = 0.0
    main = mp["ops"]
    pos = (main[0]["x"], main[0]["y"])
    for o in main[1:]:
        if o["kind"] == "mill_line":
            total += math.dist(pos, (o["x"], o["y"]))
        elif o["kind"] == "mill_arc":
            total += o["radius"] * math.radians(o["angle"])
        pos = (o["x"], o["y"])
    assert total / 1000 == pytest.approx(mp["stats"]["mill_m"], abs=2e-3)


# ───────────────────────── 2. Par matn turi ─────────────────────────
def par(name, value, typ="string", **kw):
    return cmd("Par", name=name, value=value, type=typ, **kw)


def drill(x, y="20"):
    return cmd("DrillFront", X=x, Y=y, D=8, DP=12)


def test_par_string_default_override_and_params_state():
    prog = [par("mode", "A", label="Rejim"), cmd("If", cond="mode = 'B'")]
    prog[1].children = [drill(10)]
    els = cmd("Else")
    els.children = [drill(20)]
    prog.append(els)
    ops = evaluate(prog, *DIMS)
    assert [o["X"] for o in ops if o["kind"] == "DrillFront"] == [20]                 # standart «A» — Else
    assert ops.params == [dict(name="mode", label="Rejim", type="string", suffix="", default="A", value="A",
                               visible=True, readonly=False, n="1")]
    ops = evaluate(prog, *DIMS, pars={"mode": "B"})
    assert [o["X"] for o in ops if o["kind"] == "DrillFront"] == [10] and ops.params[0]["value"] == "B"
    assert ops.params[0]["default"] == "A" and ops.problems == 0
    # bo'sh qiymat — kiritilmagan (standart); readonly — kiritilgan qiymat e'tiborsiz
    assert evaluate(prog, *DIMS, pars={"mode": ""}).params[0]["value"] == "A"
    ro = [par("mode", "A", readonly="true")] + prog[1:]
    assert evaluate(ro, *DIMS, pars={"mode": "B"}).params[0]["value"] == "A"
    # UI «123» ni songa aylantirgan bo'lsa ham matn «123» (5.0 emas), mantiqiy qiymat — true/false
    assert evaluate([par("code", 123)], *DIMS).params[0]["value"] == "123"
    assert evaluate([par("code", "x")], *DIMS, pars={"code": 7.0}).params[0]["value"] == "7"
    assert evaluate([par("code", "x")], *DIMS, pars={"code": 7.5}).params[0]["value"] == "7.5"
    assert evaluate([par("t", "")], *DIMS).params[0]["value"] == ""                    # bo'sh standart


def test_par_string_in_expressions_and_numeric_misuse_is_reported():
    prog = [par("name", "ABCD"), cmd("Var", name="n", value="len(name)*10"),
            drill("n"), cmd("Var", name="s", value="name + '-x'", type="string"),
            cmd("If", cond="s = 'ABCD-x'")]
    prog[-1].children = [drill(300)]
    ops = [o for o in evaluate(prog, *DIMS) if o["kind"] == "DrillFront"]
    assert [o["X"] for o in ops] == [40, 300]
    # Set matn o'zgaruvchisiga — matn bo'lib qoladi
    prog2 = [par("m", "A"), cmd("Set", name="m", value="m + '1'"), cmd("If", cond="m = 'A1'")]
    prog2[-1].children = [drill(5)]
    assert [o["X"] for o in evaluate(prog2, *DIMS) if o["kind"] == "DrillFront"] == [5]
    # son o'rnida matn: jim 0 emas — xabar va teshik bajarilmaydi
    bad = evaluate([par("name", "ABCD"), drill("name")], *DIMS)
    assert not [o for o in bad if o["kind"] == "DrillFront"] and bad.problems == 1
    assert "name" in bad.messages[0] or "X" in bad.messages[0]
    # ifoda xatosi (noma'lum o'zgaruvchi) ham xabar
    assert evaluate([cmd("Var", name="q", value="zzz + 'a'", type="string")], *DIMS).problems == 1


def test_par_string_literal_constant_and_length_limit(monkeypatch):
    # uzun standart qiymat — qisqartiriladi + xabar
    ops = evaluate([par("t", "x" * 250)], *DIMS)
    assert len(ops.params[0]["value"]) == X.MAX_PAR_STRING and ops.problems == 1
    # PAR_STRING_LITERAL = False — qiymat ifoda sifatida hisoblanadi
    monkeypatch.setattr(X, "PAR_STRING_LITERAL", False)
    ops = evaluate([par("t", "'ab' + 'cd'")], *DIMS)
    assert ops.params[0]["value"] == "abcd" and ops.problems == 0
    assert evaluate([par("t", "zzz")], *DIMS).problems >= 1                          # noma'lum o'zgaruvchi — xabar
    monkeypatch.undo()
    assert evaluate([par("t", "'ab' + 'cd'")], *DIMS).params[0]["value"] == "'ab' + 'cd'"       # standart: matn o'zi
    # par_type taxalluslari
    assert [X.par_type(t) for t in ("string", "STR", "text", "double", "int", "bool", "")] == [
        "string", "string", "string", "double", "integer", "boolean", "double"]


def test_par_string_api_roundtrip_and_old_json(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    prog = [dict(cmd="Par", params=dict(name="mode", value="A", type="string", label="Rejim"), comment="", children=[]),
            dict(cmd="Par", params=dict(name="k", value=5, type="integer"), comment="", children=[]),
            dict(cmd="If", params=dict(cond="mode = 'B'"), comment="",
                 children=[dict(cmd="DrillFront", params=dict(X="k", Y=20, D=8, DP=12), comment="", children=[])])]
    _set_prog(client, pid, xid, prog)
    st = client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()
    assert st["drills"] == 0 and {p["name"]: p["type"] for p in st["params"]} == {"mode": "string", "k": "integer"}
    r = client.patch(f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"par_values": {"mode": "B", "k": 7}}})
    assert r.status_code == 200
    pr = {p["name"]: p for p in client.get(f"/api/projects/{pid}/operations/{xid}/xnc-params").json()["params"]}
    assert pr["mode"]["value"] == "B" and pr["mode"]["default"] == "A" and pr["k"]["value"] == 7
    assert client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()["drills"] == 1
    assert 'cx="7" cy="20"' in client.get(f"/api/projects/{pid}/operations/{xid}/xnc.svg").text       # Par k=7 → teshik X=7
    # saqlangan matn — bazadan qaytganda ham matn (son emas)
    assert client.get(f"/api/projects/{pid}").json()["operations"][-1]["xnc"]["par_values"] == {"mode": "B", "k": 7}
    # 200 belgidan uzun matn — 422; massiv — 422
    assert client.patch(f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"par_values": {"mode": "x" * 201}}}).status_code == 422
    assert client.patch(f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"par_values": {"mode": ["x"]}}}).status_code == 422
    # ishlov markazi konteksti: Par qiymati matn
    ctx = json.loads(client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "json"}).content)["xnc"]
    assert {p["name"]: p["value"] for p in ctx["params"]} == {"mode": "B", "k": 7}


def test_par_string_in_product_program_is_text_only_and_not_exported_as_var():
    pr_prog = [par("tag", "ab"), cmd("Var", name="n", value="len(tag)")]
    from app.models import Product
    pr = Product(name="M", qty=1, program=pr_prog)
    res = PP.run(pr, 1)
    assert res.vars == {"n": 2.0}                                                     # matn o'zgaruvchisi mahsulot o'zgaruvchisiga kirmaydi
    assert [(p["name"], p["type"], p["value"]) for p in res.params] == [("tag", "string", "ab")]
    assert res.problems == 0


def test_par_string_exported_as_quoted_var_literal():
    from app.services import project_export_xnc as PX
    x = XNCParams(length=300, width=200, thickness=16, by_part_size=False, par_values={"nom": "O'q\\"},
                  program=[par("nom", "A"), drill(10)])
    xml = PX.program_xml(x, "K1", lambda *_a, **_k: None)
    assert 'type="string"' in xml and "expr=\"'O\\'q\\\\'\"" in xml


# ───────────────────────── 3. Orqa yuza (face_side=false): stanok tomonlari akslanadi ─────────────────────────
def _hole(cmd_name, z=20):
    return cmd(cmd_name, Y=50, Z=z, D=8, DP=20) if cmd_name in ("DrillLeft", "DrillRight") else cmd(cmd_name, X=100, Z=z, D=8, DP=20)


def test_back_face_hole_center_limits_use_mirrored_machine_side():
    c = cons("warn", hole_center_left=10, hole_center_right=40)
    left, right = [_hole("DrillLeft")], [_hole("DrillRight")]
    assert codes(issues(c, left)) == ["hole_center_far"] and issues(c, right) == []                  # lits yuza: chap 10, o'ng 40
    assert issues(c, left, face_side=False) == []                                                    # orqa: dastur «chap» — stanokda o'ng (40)
    r = issues(c, right, face_side=False)
    assert codes(r) == ["hole_center_far"] and "слева" in r[0]["text_ru"]                           # orqa: dastur «o'ng» — stanokda chap (10)
    # yuqori / past — o'zgarmaydi (BACK_FACE_MIRROR = "x")
    c2 = cons("warn", hole_center_top=10, hole_center_bottom=40)
    assert codes(issues(c2, [_hole("DrillTop")], face_side=False)) == ["hole_center_far"]
    assert issues(c2, [_hole("DrillBottom")], face_side=False) == []


def test_back_face_groove_margins_and_mirror_constant(monkeypatch):
    c = cons("warn", groove_margin_left=30, groove_margin_right=5)
    near_left = [cmd("Groove", X1=10, Y1=50, X2=150, Y2=50, W=4, DP=8)]          # chapdan 10, o'ngdan 50 (detal 200×100)
    near_right = [cmd("Groove", X1=50, Y1=50, X2=190, Y2=50, W=4, DP=8)]         # chapdan 50, o'ngdan 10
    assert codes(issues(c, near_left)) == ["groove_margin"] and issues(c, near_right) == []
    assert issues(c, near_left, face_side=False) == []                              # orqada: 10 mm — stanokdagi o'ng chegara (5) dan katta
    assert codes(issues(c, near_right, face_side=False)) == ["groove_margin"]       # 10 mm — stanokdagi chap chegara (30) dan kichik
    # gorizontal / vertikal paz ruxsati tomonga bog'liq emas
    cg = cons("warn", groove_vertical=False)
    assert codes(issues(cg, [cmd("Groove", X1=50, Y1=10, X2=50, Y2=80, W=4, DP=8)], face_side=False)) == ["groove_vertical"]
    # konstanta: "none" — akslanmaydi, "y" — yuqori ↔ past
    monkeypatch.setattr(XC, "BACK_FACE_MIRROR", "none")
    assert codes(issues(c, near_left, face_side=False)) == ["groove_margin"]
    assert XC.machine_side("left", True) == "left"
    monkeypatch.setattr(XC, "BACK_FACE_MIRROR", "y")
    assert XC.machine_side("top", True) == "bottom" and XC.machine_side("left", True) == "left" and XC.machine_side("top", False) == "top"
    flag = cons("warn", avoid_bottom_horizontal=True)
    assert issues(flag, [_hole("DrillBottom")], face_side=False) == []                # orqada «pastki» — stanokda yuqori
    assert codes(issues(flag, [_hole("DrillTop")], face_side=False)) == ["bottom_horizontal"]


def test_back_face_symmetric_checks_unchanged():
    c = cons("warn", length_max=150, hole_edge_front_min=4, hole_gap_min=20)
    prog = [cmd("DrillFront", X=3, Y=50, D=8, DP=8), cmd("DrillFront", X=10, Y=50, D=8, DP=8)]
    front = [(i["code"], i["command_path"]) for i in issues(c, prog)]
    back = [(i["code"], i["command_path"]) for i in issues(c, prog, face_side=False)]
    assert front == back and ("len_max", "") in front and ("hole_gap", "2") in front


def test_back_face_corner_rotation_mirrors_edge_sides():
    # kromka chap tomonda, burchak «o'ng-yuqori»: lits — 90° burish; orqa (akslangan) — chap kromka stanokda allaqachon o'ngda
    assert XC.pick_turn(0, None, ["left"], "RT")[0] == 90
    assert XC.pick_turn(0, None, ["left"], "RT", back=True)[0] == 0
    op = xop([cmd("DrillFront", X=30, Y=20, D=8, DP=8)], length=200, width=100, face_side=False)
    prj = project_of(op, left=True)
    c = cons("warn", rotate_corner_on=True, rotate_corner="RT")
    p = X.machine_program(op, prj, "any", c)
    assert p["face_back"] is True and p["extra_turn"] == 0
    op.xnc.face_side = True
    p = X.machine_program(op, prj, "any", c)
    assert p["face_back"] is False and p["extra_turn"] == 90


def test_back_face_does_not_change_default_off_results():
    """Cheklovsiz (rejim off) hisob orqa yuzada ham avvalgidek: faqat `face_back` bayrog'i qo'shilgan."""
    op = xop([cmd("DrillFront", X=30, Y=20, D=8, DP=8)], length=200, width=100, face_side=False)
    p = X.machine_program(op)
    assert p["extra_turn"] == 0 and p["rotation"] is None and p["face_back"] is True
    assert [o["x"] for o in p["ops"]] == [30]


# ───────────────────────── 4. Chizmada cheklov burishi ─────────────────────────
def test_drawing_shows_constraint_turn_badge_and_machine_view(monkeypatch):
    op = Operation(type=OpType.XNC, xnc=XNCParams(length=200, width=100, thickness=16, by_part_size=False,
                                                  program=[cmd("DrillFront", X=30, Y=20, D=8, DP=8)]))
    plain = xnc_drawing_svg(op)
    assert "xnc-turn" not in plain and "xnc-turn" not in xnc_drawing_svg(op, None, 560, 0, True)      # burish yo'q — yozuv yo'q
    badge = xnc_drawing_svg(op, None, 560, turn=90)
    assert 'class="xnc-turn" data-turn="90" data-turned="0"' in badge and "+90°" in badge
    assert badge.replace('<g class="xnc-turn"', "").count("<circle") == plain.count("<circle")        # chizma o'zi o'zgarmadi
    assert 'viewBox' in badge and 'width="560"' in badge
    mach = xnc_drawing_svg(op, None, 560, turn=90, turned=True, dims=True)                           # stanokdagi holat: 90° burilgan (o'lchamlar bilan)
    assert 'data-turned="1"' in mach and '<text x="50" y="-' in mach and ">200</text>" in mach         # yuqori o'lcham — burilgan eni emas, uzunligi
    assert 'cx="80" cy="30"' in mach                                                                  # (dy − y, x) = (80, 30)
    assert 'cx="30" cy="20"' in badge
    # konstanta orqasida o'chiriladi
    monkeypatch.setattr(X, "DRAW_TURN_BADGE", False)
    assert "xnc-turn" not in xnc_drawing_svg(op, None, 560, turn=90)


def test_drawing_turn_stacks_on_operation_rotation_and_does_not_mutate_op():
    op = Operation(type=OpType.XNC, xnc=XNCParams(length=200, width=100, thickness=16, by_part_size=False, rotation=90,
                                                  program=[cmd("DrillFront", X=30, Y=20, D=8, DP=8)]))
    svg = xnc_drawing_svg(op, None, 560, turn=90, turned=True)             # 90 + 90 = 180
    assert 'cx="170" cy="80"' in svg                                       # (dx − x, dy − y)
    assert op.xnc.rotation == 90                                           # operatsiya o'zgarmagan


def test_xnc_svg_endpoint_marks_constraint_turn(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)                          # 480×800 (uzun tomon vertikal)
    _set_prog(client, pid, xid, [dict(cmd="DrillFront", params=dict(X=30, Y=20, D=8, DP=8), comment="", children=[])])
    url = f"/api/projects/{pid}/operations/{xid}/xnc.svg"
    try:
        assert "xnc-turn" not in client.get(url).text                      # cheklov o'chiq (standart)
        client.put("/api/settings/xnc_constraints/default", json={"mode": "warn", "rotate_long_side": "horizontal"})
        s = client.get(url).text
        assert 'data-turn="90" data-turned="0"' in s
        s = client.get(url, params={"machine": "true"}).text
        assert 'data-turn="90" data-turned="1"' in s and 'viewBox="-' in s
        r = client.get(url, params={"machine": "true"}, headers={"Accept-Language": "uz"}).text
        assert "Stanokdagi ko'rinish" in r or "Stanokdagi" in r or "stanok" in r.lower()
    finally:
        client.put("/api/settings/xnc_constraints/default", json={})
    assert "xnc-turn" not in client.get(url).text
