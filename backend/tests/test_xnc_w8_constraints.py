"""W8 · XNC stanok cheklovlari («Настройки → XNC → Ограничения»): model va standartlar, har cheklov uchun tekshiruv,
rejimlar (off / warn / block), buyruq yo'li, burish hisobi (uzun tomon, kromka bilan burchak), kontekst va API."""
import json

import pytest
from pydantic import ValidationError

from app.models import EdgeRef, ELParams, Operation, OpType, Part, Project, XNCParams, XncCommand as C
from app.services import postprocessors as pp
from app.services import xnc as X
from app.services import xnc_constraints as XC
from app.services.xnc_constraints import XncConstraints, check_program, pick_turn

from test_qa_fix_calc import _set_prog, _xnc_for


def cmd(kind, /, **p):
    return C(cmd=kind, params=p)


def xop(prog, length=200, width=100, thickness=16, **kw):
    return Operation(type=OpType.XNC, code="K1", name="Bok",
                     xnc=XNCParams(length=length, width=width, thickness=thickness, by_part_size=False, program=prog, **kw))


def project_of(op, **edges):
    """Detal (op.xnc o'lchamida) va unga bog'langan XNC; edges: top=True … — kromkali tomonlar."""
    el = Operation(type=OpType.EL, code="E1", name="PVC", el=ELParams())
    part = Part(length=op.xnc.length, width=op.xnc.width, xnc_op_ids=[op.id],
                **{f"edge_{s}": EdgeRef(op_id=el.id) for s, on in edges.items() if on})
    cs = Operation(type=OpType.CS, code="CS1", name="LDSP", parts=[part])
    return Project(name="T", operations=[el, cs, op])


def cons(mode="warn", **kw) -> XncConstraints:
    """Cheklovlar: berilgan maydonlar yoqilgan (Limit: son → qiymat, Flag: (allowed, ) …)."""
    d: dict = {"mode": mode}
    for k, v in kw.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool) and k in XC.LIMIT_DEFAULTS:
            d[k] = {"enabled": True, "value": v}
        elif k in XC.FLAG_DEFAULTS:
            d[k] = {"enabled": True, "value": v}
        else:
            d[k] = v
    return XncConstraints.model_validate(d)


def issues(c, prog, project=None, **kw):
    op = xop(prog, **kw)
    return check_program(c, X.machine_program(op, project, "any", c))


def codes(lst):
    return [i["code"] for i in lst]


# ───────────────────────── Model va standartlar ─────────────────────────
def test_defaults_match_reference_values_all_disabled():
    c = XncConstraints()
    assert c.mode == "off" and c.active is False and c.rotate_long_side == "off"
    assert c.rotate_corner_on is False and c.rotate_corner == "LT"
    vals = {k: getattr(c, k).value for k in XC.LIMIT_DEFAULTS}
    assert vals == {"length_min": 200, "length_max": 3000, "width_min": 70, "width_max": 950, "thickness_min": 12,
                    "thickness_max": 60, "hole_center_top": 30, "hole_center_bottom": 30, "hole_center_left": 30,
                    "hole_center_right": 30, "hole_end_top": 30, "hole_end_bottom": 30, "hole_end_left": 30,
                    "hole_end_right": 30, "groove_margin_top": 30, "groove_margin_bottom": 30, "groove_margin_left": 30,
                    "groove_margin_right": 30, "mill_max_distance": 100, "blind_depth_margin": 2, "hole_gap_min": 5,
                    "hole_edge_front_min": 4, "hole_edge_horizontal_min": 3}
    assert not any(getattr(c, k).enabled for k in XC.LIMIT_DEFAULTS)
    assert (c.groove_horizontal.enabled, c.groove_horizontal.value) == (False, True)
    assert (c.groove_vertical.enabled, c.groove_vertical.value) == (False, False)
    assert (c.avoid_bottom_horizontal.enabled, c.avoid_bottom_horizontal.value) == (False, True)


def test_old_and_partial_json_is_accepted():
    assert XncConstraints.model_validate({}).mode == "off"
    c = XncConstraints.model_validate({"length_min": {"enabled": True}, "groove_vertical": {"enabled": True},
                                       "zzz": 1, "mode": "warn"})            # qiymat yo'q — shu maydonning standarti (0 emas)
    assert c.length_min.enabled and c.length_min.value == 200
    assert c.groove_vertical.enabled and c.groove_vertical.value is False
    assert c.mode == "warn" and c.thickness_max.value == 60
    # round-trip
    assert XncConstraints.model_validate(c.model_dump(mode="json")) == c


def test_validation_errors():
    with pytest.raises(ValidationError):
        XncConstraints.model_validate({"mode": "loud"})
    with pytest.raises(ValidationError):
        XncConstraints.model_validate({"hole_gap_min": {"enabled": True, "value": -1}})
    with pytest.raises(ValidationError):
        XncConstraints.model_validate({"rotate_corner": "XX"})
    with pytest.raises(ValidationError):                                      # min > max (ikkalasi yoqilgan)
        XncConstraints.model_validate({"width_min": {"enabled": True, "value": 500}, "width_max": {"enabled": True, "value": 400}})
    # yoqilmagan juftlik tekshirilmaydi
    XncConstraints.model_validate({"width_min": {"enabled": True, "value": 500}, "width_max": {"enabled": False, "value": 400}})


def test_off_mode_and_none_give_no_issues():
    c = cons("off", length_min=500)
    assert issues(c, [cmd("DrillFront", X=3, Y=3, D=8, DP=15)]) == []
    assert check_program(None, X.machine_program(xop([]))) == []


# ───────────────────────── Gabaritlar ─────────────────────────
def test_size_limits_all_six():
    prog = [cmd("DrillFront", X=50, Y=50, D=8, DP=8)]
    r = issues(cons(length_min=300, width_max=80, thickness_min=18), prog, length=200, width=100, thickness=16)
    assert codes(r) == ["len_min", "wid_max", "thk_min"]
    assert all(i["command_path"] == "" and i["level"] == "warn" for i in r)
    assert "200" in r[0]["text_ru"] and "300" in r[0]["text_ru"] and "200" in r[0]["text_uz"]
    r = issues(cons(length_max=150, width_min=120, thickness_max=15), prog, length=200, width=100, thickness=16)
    assert codes(r) == ["len_max", "wid_min", "thk_max"]
    # chegara qiymatining o'zi — xato emas
    assert issues(cons(length_min=200, length_max=200, width_min=100, width_max=100, thickness_min=16, thickness_max=16),
                  prog, length=200, width=100, thickness=16) == []


def test_size_uses_machine_orientation():
    prog = [cmd("DrillFront", X=5, Y=5, D=8, DP=8)]
    c = cons(length_max=150)
    assert codes(issues(c, prog, length=200, width=100)) == ["len_max"]
    assert issues(c, prog, length=200, width=100, rotation=90) == []         # burilgach X = 100


# ───────────────────────── Rejimlar ─────────────────────────
def test_modes_warn_and_block_levels():
    prog = [cmd("DrillFront", X=3, Y=50, D=8, DP=8)]
    w = issues(cons("warn", hole_edge_front_min=4), prog)
    b = issues(cons("block", hole_edge_front_min=4), prog)
    assert [i["level"] for i in w] == ["warn"] and [i["level"] for i in b] == ["error"]
    assert w[0]["code"] == b[0]["code"] == "hole_edge_front"
    assert set(w[0]) >= {"level", "code", "text", "text_ru", "text_uz", "command_path", "count"}


def test_text_follows_request_language():
    from app.i18n import LANG
    prog = [cmd("DrillFront", X=3, Y=50, D=8, DP=8)]
    tok = LANG.set("uz")
    try:
        i = issues(cons(hole_edge_front_min=4), prog)[0]
    finally:
        LANG.reset(tok)
    assert i["text"] == i["text_uz"] and i["text_ru"] != i["text_uz"]
    assert issues(cons(hole_edge_front_min=4), prog)[0]["text"] == i["text_ru"]


# ───────────────────────── Teshiklar ─────────────────────────
def test_horizontal_hole_center_distance_per_side():
    prog = [cmd("DrillLeft", Y=50, Z=40, D=8, DP=20), cmd("DrillTop", X=50, Z=40, D=8, DP=20),
            cmd("DrillRight", Y=50, Z=20, D=8, DP=20)]
    r = issues(cons(hole_center_top=30, hole_center_right=30), prog, thickness=60)
    assert codes(r) == ["hole_center_far"] and r[0]["command_path"] == "2"       # chap tekshirilmaydi, o'ng (Z=20) joyida
    r = issues(cons(hole_center_left=30, hole_center_top=30), prog, thickness=60)
    assert [i["command_path"] for i in r] == ["1", "2"]
    # M (qalinlik o'rtasi): Z = dz / 2
    mid = [cmd("DrillLeft", Y=50, Z=1, M="true", D=8, DP=20)]
    assert issues(cons(hole_center_left=30), mid, thickness=60) == []             # 30 ≤ 30
    assert codes(issues(cons(hole_center_left=29), mid, thickness=60)) == ["hole_center_far"]


def test_hole_center_side_is_machine_side_after_rotation():
    prog = [cmd("DrillLeft", Y=50, Z=40, D=8, DP=20)]
    c = cons(hole_center_left=30)
    assert codes(issues(c, prog, thickness=60)) == ["hole_center_far"]
    assert issues(c, prog, thickness=60, rotation=90) == []                      # chap → yuqori tomon
    assert codes(issues(cons(hole_center_top=30), prog, thickness=60, rotation=90)) == ["hole_center_far"]


def test_bottom_horizontal_is_preference_or_restriction():
    prog = [cmd("DrillBottom", X=50, Z=8, D=8, DP=20), cmd("DrillFront", X=3, Y=50, D=8, DP=8)]
    pref = issues(cons("block", avoid_bottom_horizontal=True, hole_edge_front_min=4), prog)
    assert {i["code"]: i["level"] for i in pref} == {"bottom_horizontal": "warn", "hole_edge_front": "error"}   # afzallik — warn
    hard = issues(cons("block", avoid_bottom_horizontal=False), prog)
    assert {i["code"]: i["level"] for i in hard} == {"bottom_horizontal": "error"}
    assert issues(cons("warn"), prog) == []                                       # yoqilmagan — yo'q
    assert issues(cons("warn", avoid_bottom_horizontal=True), [cmd("DrillTop", X=50, Z=8, D=8, DP=20)]) == []


def test_blind_vertical_depth_must_be_less_than_thickness():
    c = cons(blind_depth_margin=2)
    f = lambda dp: issues(c, [cmd("DrillFront", X=50, Y=50, D=8, DP=dp)])        # noqa: E731  (qalinlik 16)
    assert codes(f(15)) == ["blind_depth"] and codes(f(14.5)) == ["blind_depth"]
    assert f(14) == [] and f(5) == []
    assert f(16) == [] and f(20) == []                                            # o'tuvchi — ko'r emas
    assert issues(c, [cmd("DrillLeft", Y=50, Z=8, D=8, DP=15)]) == []             # faqat vertikal (frontal) teshik


def test_hole_gap_between_edges():
    c = cons(hole_gap_min=5)
    near = [cmd("DrillFront", X=30, Y=30, D=8, DP=8), cmd("DrillFront", X=36, Y=30, D=8, DP=8)]
    r = issues(c, near)
    assert codes(r) == ["hole_gap"] and r[0]["command_path"] == "2"               # dasturda keyingisiga yoziladi
    far = [cmd("DrillFront", X=30, Y=30, D=8, DP=8), cmd("DrillFront", X=50, Y=30, D=8, DP=8)]
    assert issues(c, far) == []
    exact = [cmd("DrillFront", X=30, Y=30, D=8, DP=8), cmd("DrillFront", X=43, Y=30, D=8, DP=8)]       # chetlar orasi 5 — mos
    assert issues(c, exact) == []
    arr = [cmd("DrillFront", X=30, Y=30, D=8, DP=8, AC=3, AS=10, AV="false")]       # massiv: 3 teshik, chetlar orasi 2 mm
    r = issues(c, arr)
    assert len(r) == 1 and r[0]["count"] == 2 and "×2" in r[0]["text_ru"]
    # yon teshiklar: bir tomon, chekka bo'ylab o'rin va qalinlik o'rni bo'yicha
    side = [cmd("DrillLeft", Y=30, Z=8, D=8, DP=20), cmd("DrillLeft", Y=36, Z=8, D=8, DP=20)]
    assert codes(issues(c, side)) == ["hole_gap"]
    assert issues(c, [cmd("DrillLeft", Y=30, Z=8, D=8, DP=20), cmd("DrillRight", Y=30, Z=8, D=8, DP=20)]) == []


def test_edge_distance_front_and_horizontal_holes():
    f = lambda x: issues(cons(hole_edge_front_min=4), [cmd("DrillFront", X=x, Y=50, D=8, DP=8)])   # noqa: E731
    assert codes(f(6)) == ["hole_edge_front"] and f(8) == [] and f(10) == []
    assert codes(issues(cons(hole_edge_front_min=4), [cmd("DrillFront", X=100, Y=3, D=8, DP=8)])) == ["hole_edge_front"]
    assert codes(issues(cons(hole_edge_front_min=4), [cmd("DrillFront", X=197, Y=50, D=8, DP=8)])) == ["hole_edge_front"]
    c = cons(hole_edge_horizontal_min=3)
    assert codes(issues(c, [cmd("DrillLeft", Y=50, Z=3, D=8, DP=20)])) == ["hole_edge_horizontal"]     # yuzadan 3 − 4 < 3
    assert issues(c, [cmd("DrillLeft", Y=50, Z=8, D=8, DP=20)]) == []                                  # 8 − 4 = 4 ≥ 3
    assert codes(issues(c, [cmd("DrillLeft", Y=3, Z=8, D=8, DP=20)])) == ["hole_edge_horizontal"]       # chekka bo'ylab yaqin
    assert codes(issues(c, [cmd("DrillTop", X=198, Z=8, D=8, DP=20)])) == ["hole_edge_horizontal"]


# ───────────────────────── Paz va freza ─────────────────────────
def test_groove_orientation_permission():
    h = cmd("Groove", X1=20, Y1=50, X2=180, Y2=50, W=4, DP=8)
    v = cmd("Groove", X1=100, Y1=10, X2=100, Y2=90, W=4, DP=8)
    c = cons(groove_horizontal=False, groove_vertical=True)
    r = issues(c, [h, v])
    assert codes(r) == ["groove_horizontal"] and r[0]["command_path"] == "1"      # gorizontal taqiqlangan, vertikal ruxsat
    r = issues(cons(groove_vertical=False), [h, v])
    assert codes(r) == ["groove_vertical"] and r[0]["command_path"] == "2"
    assert issues(cons(groove_horizontal=True, groove_vertical=True), [h, v]) == []
    assert issues(cons("warn"), [h, v]) == []                                     # yoqilmagan


def test_groove_margin_from_part_edge(monkeypatch):
    near_top = cmd("Groove", X1=40, Y1=16, X2=160, Y2=16, W=4, DP=8)           # yuqoridan 14 mm (16 − 2)
    r = issues(cons(groove_margin_top=30), [near_top])
    assert codes(r) == ["groove_margin"] and "14" in r[0]["text_ru"]
    assert issues(cons(groove_margin_top=14), [near_top]) == []
    assert issues(cons(groove_margin_bottom=30), [near_top]) == []                 # 100 − 18 = 82
    through = cmd("Groove", X1=0, Y1=50, X2=200, Y2=50, W=4, DP=8)
    assert codes(issues(cons(groove_margin_left=30), [through])) == ["groove_margin"]    # uchlari ham hisobga olinadi (taxmin)
    monkeypatch.setattr(XC, "GROOVE_MARGIN_ALL_SIDES", False)
    assert issues(cons(groove_margin_left=30), [through]) == []                    # faqat ko'ndalang tomonlar
    assert codes(issues(cons(groove_margin_top=30), [near_top])) == ["groove_margin"]


def test_mill_distance_from_part():
    c = cons(mill_max_distance=100)
    far = [cmd("MillStart", X=-150, Y=10, DP=8, T="M", D=6), cmd("MillLine", X=100, Y=10)]
    r = issues(c, far)
    assert codes(r) == ["mill_far"] and r[0]["command_path"] == "1"
    ok = [cmd("MillStart", X=-50, Y=10, DP=8, T="M", D=6), cmd("MillLine", X=100, Y=10)]
    assert issues(c, ok) == []
    line_far = [cmd("MillStart", X=10, Y=10, DP=8, T="M", D=6), cmd("MillLine", X=100, Y=300)]     # Y: 300 − 100 = 200
    r = issues(c, line_far)
    assert codes(r) == ["mill_far"] and r[0]["command_path"] == "2"
    rect = [cmd("MillRect", X=100, Y=50, L=500, W=40, T="M", D=6, DP=3)]                           # to'rtburchak detaldan chiqib ketgan
    assert codes(issues(c, rect)) == ["mill_far"]


# ───────────────────────── Buyruq yo'li (ichma-ich) ─────────────────────────
def test_command_path_nested_blocks():
    prog = [cmd("Var", name="v", value=1),
            C(cmd="If", params={"cond": 1}, children=[cmd("DrillFront", X=50, Y=50, D=8, DP=8),
                                                       cmd("DrillFront", X=3, Y=50, D=8, DP=8)])]
    r = issues(cons(hole_edge_front_min=4), prog)
    assert [i["command_path"] for i in r] == ["2.2"]
    assert XC._path_key("2.10") > XC._path_key("2.9") and XC._path_key("") < XC._path_key("1")


def test_machine_program_ops_carry_cmd_path():
    prog = [cmd("DrillFront", X=50, Y=50, D=8, DP=8), cmd("MillStart", X=0, Y=0, DP=3, T="M", D=6), cmd("MillLine", X=30, Y=0)]
    assert [o["cmd_path"] for o in X.machine_program(xop(prog))["ops"]] == ["1", "2", "3"]
    assert [o["cmd_path"] for o in X.evaluate(prog, 200, 100, 16)] == ["1", "2", "3"]


def test_issue_list_is_capped():
    prog = [cmd("DrillFront", X=3, Y=50, D=8, DP=8) for _ in range(XC.MAX_ISSUES + 15)]
    # bir xil (kod, yo'l) qayta kelmaydi: har buyruq o'z yo'liga ega
    r = issues(cons(hole_edge_front_min=4), prog)
    assert len(r) == XC.MAX_ISSUES + 1 and r[-1]["code"] == "more" and r[-1]["count"] == 15


# ───────────────────────── Burish hisobi ─────────────────────────
@pytest.mark.parametrize("rotation,long_turn,edged,corner,rule,expected", [
    (0, None, ["top"], "LT", "first", 0), (0, None, ["bottom"], "LT", "first", 90), (0, None, ["right"], "LT", "first", 180),
    (0, None, ["top"], "RB", "first", 90), (0, None, ["left"], "RB", "first", 180), (0, None, ["left"], "LT", "first", 0),
    (0, 0, ["bottom"], "LT", "first", 180), (0, 90, ["top"], "LT", "first", 270), (0, 90, ["bottom"], "LT", "first", 90),
    (90, None, ["top"], "LT", "first", 180),                                     # burilgan detal: yuqori tomon 90° da o'ngda, 270° da chapda
    (0, None, [], "LT", "first", 0),
    (0, None, ["top", "left"], "RB", "first", 90), (0, None, ["top", "left"], "RB", "max", 180),
])
def test_pick_turn(rotation, long_turn, edged, corner, rule, expected):
    t, info = pick_turn(rotation, long_turn, edged, corner, rule)
    assert t == expected and info["turn"] == expected and info["corner"] == corner


def test_pick_turn_keeps_long_side_parity():
    for rot in (0, 90, 180, 270):
        for lt in (0, 90):
            for edged in (["top"], ["bottom"], ["left"], ["right"], ["top", "left", "bottom", "right"]):
                for corner in XC.CORNERS:
                    t, _i = pick_turn(rot, lt, edged, corner)
                    assert t % 180 == lt


def test_first_edged_side_follows_documented_order():
    # birinchi kromkali tomon: yuqori, past, chap, o'ng (XC.EDGE_ORDER); qoida konstanta orqasida
    assert XC.EDGE_ORDER == ("top", "bottom", "left", "right") and XC.CORNER_EDGE_RULE == "first"
    t, info = pick_turn(0, None, ["right", "bottom"], "LT")
    assert info["target"] == "bottom" and t == 90


def test_machine_program_rotates_edge_into_corner():
    prog = [cmd("DrillFront", X=30, Y=20, D=8, DP=8)]
    op = xop(prog, length=200, width=100)
    prj = project_of(op, top=True)
    c = cons("warn", rotate_corner_on=True, rotate_corner="RB")
    p = X.machine_program(op, prj, "any", c)
    assert p["extra_turn"] == 90 and p["size"] == {"length": 100, "width": 200}
    assert p["rotation"]["corner"] == "RB" and p["rotation"]["target"] == "top" and p["rotation"]["turn"] == 90
    assert (p["ops"][0]["x"], p["ops"][0]["y"]) == (80, 30)                       # (dy − y, x)
    ctx = pp.context_xnc(prj, op, "any", None, c)["xnc"]
    assert ctx["turn"] == 90 and set(ctx["edges"]) == {"top"} and set(ctx["edges_final"]) == {"right"}
    # rejim off — burish yo'q
    assert X.machine_program(op, prj, "any", cons("off", rotate_corner_on=True))["extra_turn"] == 0
    # bog'lanmagan operatsiya (kromka ma'lum emas) — burish yo'q
    assert X.machine_program(op, None, "any", c)["extra_turn"] == 0
    assert X.machine_program(op, project_of(op), "any", c)["extra_turn"] == 0       # kromkasiz detal


def test_long_side_from_constraints_and_explicit_override():
    op = xop([cmd("DrillFront", X=30, Y=20, D=8, DP=8)], length=100, width=200)     # uzun tomon vertikal
    c = cons("warn", rotate_long_side="horizontal")
    p = X.machine_program(op, None, "any", c)
    assert p["extra_turn"] == 90 and p["size"] == {"length": 200, "width": 100}
    assert p["rotation"]["long_side"] == "horizontal"
    # aniq long_side parametri cheklovdan ustun
    assert X.machine_program(op, None, "vertical", c)["extra_turn"] == 0
    assert X.machine_program(op, None, "any", cons("off", rotate_long_side="horizontal"))["extra_turn"] == 0
    assert X.machine_program(op, None)["rotation"] is None and X.machine_program(op, None)["extra_turn"] == 0
    # ikkalasi birga: uzun tomon gorizontal + chap-yuqori burchakda pastki kromka
    prj = project_of(op, bottom=True)
    c2 = cons("warn", rotate_long_side="horizontal", rotate_corner_on=True, rotate_corner="LT")
    p2 = X.machine_program(op, prj, "any", c2)
    assert p2["extra_turn"] == 90 and p2["size"] == {"length": 200, "width": 100}  # bottom → left (90°)
    assert p2["rotation"]["long_side"] == "horizontal"


def test_context_xnc_has_constraints_and_issues():
    op = xop([cmd("DrillFront", X=3, Y=50, D=8, DP=8)])
    plain = pp.context_xnc(project_of(op), op)["xnc"]
    assert plain["constraints"] == {"mode": "off"} and plain["constraint_issues"] == [] and plain["extra_turn"] == 0
    c = cons("block", hole_edge_front_min=4, length_max=150)
    x = pp.context_xnc(project_of(op), op, "any", None, c)["xnc"]
    assert x["constraints"]["mode"] == "block" and x["constraints"]["length_max"] == {"enabled": True, "value": 150}
    assert [(i["code"], i["level"]) for i in x["constraint_issues"]] == [("len_max", "error"), ("hole_edge_front", "error")]
    json.dumps(x)                                                                  # JSON-ga mos


def test_check_program_accepts_operation_directly():
    op = xop([cmd("DrillFront", X=3, Y=50, D=8, DP=8)], length=100, width=200)
    c = cons("warn", hole_edge_front_min=4, rotate_long_side="horizontal", length_max=150)
    r = check_program(c, op)                                   # operatsiya: cheklovlar burishi bilan hisoblanadi (X = 200)
    assert codes(r) == ["len_max", "hole_edge_front"]
    assert check_program(cons("off", length_max=1), op) == []


def test_analyze_helper_and_stats_fields():
    op = xop([cmd("DrillFront", X=3, Y=50, D=8, DP=8)])
    r = XC.analyze(op, project_of(op), cons("warn", hole_edge_front_min=4))
    assert r["mode"] == "warn" and codes(r["issues"]) == ["hole_edge_front"] and r["extra_turn"] == 0
    r = XC.analyze(op, project_of(op), cons("off", hole_edge_front_min=4))
    assert r == dict(mode="off", issues=[], extra_turn=0, rotation=None)


# ───────────────────────── API ─────────────────────────
@pytest.fixture()
def reset_constraints(client):
    yield
    client.put("/api/settings/xnc_constraints/default", json={})


def test_settings_scope_defaults_and_roundtrip(client, reset_constraints):
    d = client.get("/api/settings/xnc_constraints/default").json()
    assert d["mode"] == "off" and d["length_max"] == {"enabled": False, "value": 3000}
    assert "xnc_constraints" in client.get("/api/settings").json()
    body = dict(d, mode="warn", rotate_long_side="vertical", hole_gap_min={"enabled": True, "value": 6.5})
    assert client.put("/api/settings/xnc_constraints/default", json=body).status_code == 200
    d2 = client.get("/api/settings/xnc_constraints/default").json()
    assert d2["mode"] == "warn" and d2["rotate_long_side"] == "vertical" and d2["hole_gap_min"] == {"enabled": True, "value": 6.5}
    # noto'g'ri qiymat — 4xx, avvalgisi saqlanadi
    bad = client.put("/api/settings/xnc_constraints/default", json=dict(d, mode="loud"))
    assert 400 <= bad.status_code < 500
    bad = client.put("/api/settings/xnc_constraints/default",
                     json=dict(d, width_min={"enabled": True, "value": 9}, width_max={"enabled": True, "value": 5}))
    assert 400 <= bad.status_code < 500
    assert client.get("/api/settings/xnc_constraints/default").json()["mode"] == "warn"
    # standartga qaytarish
    client.put("/api/settings/xnc_constraints/default", json={})
    assert client.get("/api/settings/xnc_constraints/default").json()["mode"] == "off"


def test_xnc_stats_has_constraint_issues_and_keeps_old_fields(client, kravat, reset_constraints):
    pid, cs, ptid, xid = _xnc_for(client, kravat)                   # detal 480×800
    _set_prog(client, pid, xid, [dict(cmd="DrillFront", params=dict(X=3, Y=20, D=8, DP=8), comment="", children=[])])
    st = client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()
    assert {"drills", "mill_m", "saw_m", "unit_cost", "qty", "cost", "errors", "warnings", "params"} <= set(st)
    assert st["constraint_issues"] == [] and st["constraint_mode"] == "off"          # standart — o'chiq
    client.put("/api/settings/xnc_constraints/default",
               json={"mode": "warn", "hole_edge_front_min": {"enabled": True, "value": 4},
                     "length_max": {"enabled": True, "value": 400}})
    st = client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()
    assert st["drills"] == 1 and st["constraint_mode"] == "warn"
    assert [(i["code"], i["level"], i["command_path"]) for i in st["constraint_issues"]] == [
        ("len_max", "warn", ""), ("hole_edge_front", "warn", "1")]
    client.put("/api/settings/xnc_constraints/default",
               json={"mode": "block", "hole_edge_front_min": {"enabled": True, "value": 4}})
    st = client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()
    assert [i["level"] for i in st["constraint_issues"]] == ["error"]
    # alohida endpoint
    r = client.get(f"/api/projects/{pid}/operations/{xid}/xnc-constraints").json()
    assert r["mode"] == "block" and codes(r["issues"]) == ["hole_edge_front"] and r["extra_turn"] == 0
    assert client.get(f"/api/projects/{pid}/operations/{xid}/xnc-constraints", params={"long_side": "zz"}).status_code == 400
    # CS operatsiyasi — XNC emas
    assert client.get(f"/api/projects/{pid}/operations/{cs}/xnc-constraints").status_code == 400


def test_postprocess_applies_constraint_rotation(client, kravat, reset_constraints):
    pid, cs, ptid, xid = _xnc_for(client, kravat)                   # 480×800, kromka: yuqori / past
    _set_prog(client, pid, xid, [dict(cmd="DrillFront", params=dict(X=30, Y=20, D=8, DP=8), comment="", children=[])])
    get = lambda **q: json.loads(client.get(f"/api/projects/{pid}/operations/{xid}/postprocess",     # noqa: E731
                                             params={"key": "json", **q}).content)["xnc"]
    assert get()["extra_turn"] == 0 and get()["turn"] == 0
    client.put("/api/settings/xnc_constraints/default", json={"mode": "warn", "rotate_long_side": "horizontal"})
    x = get()                                                       # 480×800: uzun tomon vertikal → gorizontal bo'lsin
    assert x["extra_turn"] == 90 and x["size"] == {"length": 800, "width": 480} and x["rotation"]["long_side"] == "horizontal"
    assert get(long_side="vertical")["extra_turn"] == 0             # aniq parametr ustun
    client.put("/api/settings/xnc_constraints/default", json={"mode": "off", "rotate_long_side": "horizontal"})
    assert get()["extra_turn"] == 0                                 # rejim off — burish yo'q
    client.put("/api/settings/xnc_constraints/default",
               json={"mode": "warn", "rotate_corner_on": True, "rotate_corner": "RB"})
    x = get()                                                       # birinchi kromkali tomon — yuqori → o'ngga (90°)
    assert x["extra_turn"] == 90 and set(x["edges_final"]) == {"right", "left"} and x["rotation"]["target"] == "top"
    assert x["constraints"]["rotate_corner"] == "RB" and x["constraint_issues"] == []


def test_horizontal_hole_min_distance_to_part_edge():
    """«Минимальное расстояние между центром горизонтального отверстия и краем детали» (onlayn oynada, 2026-10-23):
    chap/o'ng teshik — Y chetlardan, yuqori/past — X chetlardan; faqat yoqilgan tomon tekshiriladi."""
    c = cons(hole_end_left=30)
    assert codes(issues(c, [cmd("DrillLeft", Y=20, Z=8, D=8, DP=20)])) == ["hole_end_near"]
    assert codes(issues(c, [cmd("DrillLeft", Y=85, Z=8, D=8, DP=20)])) == ["hole_end_near"]       # eni 100: 100 − 85 = 15
    assert issues(c, [cmd("DrillLeft", Y=50, Z=8, D=8, DP=20)]) == []
    assert issues(c, [cmd("DrillRight", Y=20, Z=8, D=8, DP=20)]) == []                            # o'ng tomon o'chiq
    r = issues(cons(hole_end_top=30), [cmd("DrillTop", X=180, Z=8, D=8, DP=20)])                  # uzunligi 200: 20 mm
    assert codes(r) == ["hole_end_near"] and "20" in r[0]["text_ru"] and "30" in r[0]["text_ru"]
    assert issues(cons(hole_end_top=30), [cmd("DrillTop", X=100, Z=8, D=8, DP=20)]) == []


def test_strict_mode_blocks_machine_file(client, kravat, reset_constraints):
    """«Строго» (block): buzilgan XNC stanok fayliga chiqmaydi (400, sababi bilan); «Не строго» (warn) — chiqadi (2026-10-23)."""
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    _set_prog(client, pid, xid, [dict(cmd="DrillFront", params=dict(X=3, Y=40, D=8, DP=8), comment="", children=[])])
    pp = lambda: client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "json"})   # noqa: E731
    client.put("/api/settings/xnc_constraints/default", json={"mode": "block", "hole_edge_front_min": {"enabled": True, "value": 4}})
    r = pp()
    assert r.status_code == 400 and "Строго" in r.json()["detail"]
    client.put("/api/settings/xnc_constraints/default", json={"mode": "warn", "hole_edge_front_min": {"enabled": True, "value": 4}})
    assert pp().status_code == 200
    client.put("/api/settings/xnc_constraints/default", json={"mode": "block", "hole_edge_front_min": {"enabled": True, "value": 4}})
    _set_prog(client, pid, xid, [dict(cmd="DrillFront", params=dict(X=60, Y=40, D=8, DP=8), comment="", children=[])])
    assert pp().status_code == 200                                     # qoidaga mos dastur — chiqadi
