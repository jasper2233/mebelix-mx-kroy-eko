"""QA hisoboti C bo'yicha hisob-kitob tuzatishlari: XNC (sinxron, ifodalar, boshqaruv buyruqlari, chizma), GR (paz),
ombor «arvoh» qoldig'i, hisobot (ko'zgu, sahifalash, shtamp), EL umumiy standarti, kromka > detal, etiketka va
server tomonidagi chegaralar."""
import copy
import re

import pytest

from app.db import ProjectRow, SessionLocal
from app.models import ELParams, GRParams, Operation, OpType, Part, Project, XncCommand as C, XNCParams
from app.services import labels
from app.services.xnc import (MAX_LOOP_ITER, eval_expr, evaluate, program_stats, xnc_drawing_svg, xnc_holes_table,
                              xnc_stats)

ENV = {"dx": 480.0, "dy": 800.0, "dz": 16.0}


def _op(p, oid):
    return next(o for o in p["operations"] if o["id"] == oid)


def _ops(p, typ):
    return [o for o in p["operations"] if o["type"] == typ]


def _new_project(client, name, cs_code="QACS"):
    pid = client.post("/api/projects", json={"name": name}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": cs_code, "name": cs_code}).json()
    return pid, p["operations"][-1]["id"]


def _add_parts(client, pid, cs, parts):
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=parts)
    assert p.status_code == 200, p.text
    return p.json()


def _xnc_for(client, kravat, part_idx=5):
    pid, cs, _el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    part = _op(p, cs)["parts"][part_idx]
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/{part['id']}/xnc").json()
    return pid, cs, part["id"], _ops(p, "XNC")[-1]["id"]


def _set_prog(client, pid, xid, prog, **xnc):
    r = client.patch(f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"program": prog, **xnc}})
    assert r.status_code == 200, r.text
    return r.json()


def drill(x, y, **kw):
    return C(cmd="DrillFront", params={"X": x, "Y": y, "D": 8, "DP": 12, **kw})


# ───────────────────────── №1 · XNC o'lcham/soni detal bilan sinxron ─────────────────────────
def test_xnc_size_qty_follow_part(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)               # detal №6: 480×800, soni 1
    prog = [{"cmd": "DrillFront", "params": {"X": "dx/2", "Y": "dy/2", "D": 8, "DP": 12}}]
    _set_prog(client, pid, xid, prog, drill_price=1000)
    x = _op(client.get(f"/api/projects/{pid}").json(), xid)
    assert (x["xnc"]["length"], x["xnc"]["width"], x["xnc"]["qty"]) == (480, 800, 1)
    # detal o'lchami va soni o'zgardi → XNC DX/DY/qty, chizma, narx yangilanadi
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{ptid}", json={"length": 600, "width": 300, "qty": 5})
    p = client.get(f"/api/projects/{pid}").json()
    x = _op(p, xid)
    assert (x["xnc"]["length"], x["xnc"]["width"], x["xnc"]["qty"]) == (600, 300, 5)
    assert x["xnc"]["thickness"] == 16 and x["cost_operation"] == 5 * 1000
    svg = client.get(f"/api/projects/{pid}/operations/{xid}/xnc.svg").text
    assert 'cx="300"' in svg and 'cy="150"' in svg
    # mahsulot soni va МК: qty = ОК − МК
    prid = p["products"][0]["id"]
    client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": 3})
    assert _op(client.get(f"/api/projects/{pid}").json(), xid)["xnc"]["qty"] == 15
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{ptid}", json={"minus_qty": 2})
    x = _op(client.get(f"/api/projects/{pid}").json(), xid)
    assert x["xnc"]["qty"] == 13 and x["cost_operation"] == 13 * 1000
    # loyihaning o'lcham kiritish rejimi (kromka bilan) — detal o'lchami (sizes.py) bo'yicha
    client.patch(f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"by_part_size": True}})
    st = client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()
    assert st["drills"] == 1 and st["qty"] == 13


def test_xnc_manual_size_when_not_by_part_size(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    client.patch(f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"by_part_size": False, "length": 111, "width": 222,
                                                                          "qty": 7}})
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{ptid}", json={"length": 650, "qty": 9})
    x = _op(client.get(f"/api/projects/{pid}").json(), xid)["xnc"]
    assert (x["length"], x["width"], x["qty"]) == (111, 222, 7)          # «По размеру детали» ☐ — qo'lda


def test_xnc_part_variables_allowance_and_edges(client, kravat):
    """J3: allowanceT/B/L/R, etj/ett…, xncSide, bySizeDetail, xncIndex."""
    pid, cs, ptid, xid = _xnc_for(client, kravat)                # №6: edge_top/bottom = PVC (kromka)
    el = kravat[2]
    client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {"thickness": 2, "jointing_width": 1}})
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{ptid}", json={"allow_left": 5, "allow_top": 3})
    prog = [{"cmd": "DrillFront", "params": {"X": "allowanceL+10", "Y": "allowanceT+ett*10+etj", "D": 8, "DP": 12}},
            {"cmd": "DrillFront", "params": {"X": "100+elt", "Y": "xncSide*50+bySizeDetail+xncIndex", "D": 8, "DP": 12}}]
    _set_prog(client, pid, xid, prog)
    st = client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()
    assert st["drills"] == 2 and st["errors"] == 0 and st["warnings"] == []
    svg = client.get(f"/api/projects/{pid}/operations/{xid}/xnc.svg").text
    assert 'cx="15" cy="24"' in svg            # 5+10 ; 3 + 2·10 + 1
    assert 'cx="100" cy="52"' in svg           # elt (chap kromka yo'q) = 0 ; 50 + 1 + xncIndex(1)
    xv = _op(client.get(f"/api/projects/{pid}").json(), xid)["xnc"]["part_vars"]
    assert xv["allowanceL"] == 5 and xv["ett"] == 2 and xv["ebj"] == 1 and xv["xncIndex"] == 1


# ───────────────────────── №5 · XNC ifodalari ─────────────────────────
@pytest.mark.parametrize("expr,val", [
    ("min(dx,dy)", 480), ("max(dx,dy)", 800), ("round(2.567,2)", 2.57), ("round(2.5)", 3), ("floor(2.9)", 2),
    ("ceil(2.1)", 3), ("tan(pi/4)", 1), ("sqrt(16)+abs(-2)", 6), ("1 if dx>500 else 2", 2), ("dx>=480", 1),
    ("dx<480", 0), ("dx==480", 1), ("dx!=480", 0), ("dx>100 and dy<900", 1), ("dx<100 or dy<900", 1), ("not dx", 0),
    ("1,5*dx", 720), ("min(1,5)", 1), ("max(1,5,3)", 5), ("(dx>100)*10", 10), ("-dx+3", -477), ("dx % 7", 4),
])
def test_expr_ok(expr, val):
    assert eval_expr(expr, ENV) == pytest.approx(val, abs=1e-9)


@pytest.mark.parametrize("expr", ["1/0", "abc", "__import__('os')", "dx.real", "'a'", "min()", "sqrt(-1)", "9**9**9",
                                  "1e400+1", "dx +", "lambda: 1", "[1,2]", "round(1,2,3)", "dx" * 80])
def test_expr_bad_raises(expr):
    try:
        v = eval_expr(expr, ENV)
    except Exception:                                    # noqa: BLE001 — har qanday xato qabul qilinadi (jim 0 emas)
        return
    assert v != v or abs(v) == float("inf"), f"{expr} → {v}"        # yoki cheksiz (keyin num() rad etadi)


def test_expr_errors_not_silent_zero():
    prog = [drill("1/0", 10), drill("abc", 10), drill("dx/2", "dy/2"), drill("9**9**9", 10)]
    st = program_stats(prog, 480, 800, 16)
    assert st["drills"] == 1                              # noto'g'ri koordinatali teshiklar (0,0) da sanalmaydi
    assert st["errors"] == 3 and len(st["warnings"]) == 3
    assert "X" in st["warnings"][0] and "XNC 1" in st["warnings"][0]
    ops = evaluate(prog, 480, 800, 16)
    assert [(o["X"], o["Y"]) for o in ops] == [(240.0, 400.0)]
    # xato — API da ham ko'rinadi, chizmada (0,0) doira yo'q
    pr = [C(cmd="DrillFront", params={"X": "abc", "Y": 10})]
    assert program_stats(pr, 100, 100, 16)["drills"] == 0


def test_min_max_round_in_drill_coordinates(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)            # 480×800
    prog = [{"cmd": "DrillFront", "params": {"X": "min(dx,dy)", "Y": "max(dx,dy)/2", "D": 8, "DP": 12}},
            {"cmd": "DrillFront", "params": {"X": "round(dx/7,1)", "Y": "ceil(dy/7)", "D": 8, "DP": 12}}]
    _set_prog(client, pid, xid, prog)
    svg = client.get(f"/api/projects/{pid}/operations/{xid}/xnc.svg").text
    assert 'cx="480" cy="400"' in svg and 'cx="68.6" cy="115"' in svg
    assert client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()["drills"] == 2


# ───────────────────────── №4 · XNC boshqaruv buyruqlari ─────────────────────────
def test_if_else(client):
    prog = [C(cmd="If", params={"cond": "dx>500"}, children=[drill(10, 10)]),
            C(cmd="Else", children=[drill(10, 10), drill(20, 10)])]
    assert program_stats(prog, 480, 800, 16)["drills"] == 2        # shart yolg'on → Else
    assert program_stats(prog, 600, 800, 16)["drills"] == 1        # shart rost → If
    chain = [C(cmd="If", params={"cond": "dx>700"}, children=[drill(1, 1)]),
             C(cmd="Else", params={"cond": "dx>500"}, children=[drill(1, 1), drill(2, 1)]),
             C(cmd="Else", children=[drill(1, 1), drill(2, 1), drill(3, 1)])]
    assert [program_stats(chain, w, 800, 16)["drills"] for w in (800, 600, 400)] == [1, 2, 3]
    # Else yolg'iz — xato, hech narsa bajarilmaydi
    st = program_stats([C(cmd="Else", children=[drill(1, 1)])], 480, 800, 16)
    assert st["drills"] == 0 and st["errors"] == 1
    # shart berilmagan / noto'g'ri — bajarilmaydi, xabar bor
    st = program_stats([C(cmd="If", params={"cond": ""}, children=[drill(1, 1)])], 480, 800, 16)
    assert st["drills"] == 0 and st["errors"] == 1
    st = program_stats([C(cmd="If", params={"cond": "zzz>1"}, children=[drill(1, 1)])], 480, 800, 16)
    assert st["drills"] == 0 and st["errors"] == 1


def test_while_dowhile_break_continue():
    inc = C(cmd="Set", params={"name": "i", "value": "i+1"})
    w = [C(cmd="Var", params={"name": "i", "value": 0}),
         C(cmd="While", params={"cond": "i<3"}, children=[drill("10+i*10", 10), inc])]
    ops = evaluate(w, 480, 800, 16)
    assert [o["X"] for o in ops] == [10, 20, 30]
    # DoWhile: shart yolg'on bo'lsa ham bir marta
    dw = [C(cmd="Var", params={"name": "i", "value": 5}),
          C(cmd="DoWhile", params={"cond": "i<3"}, children=[drill(10, 10), inc])]
    assert program_stats(dw, 480, 800, 16)["drills"] == 1
    # Break / Continue
    br = [C(cmd="Var", params={"name": "i", "value": 0}),
          C(cmd="While", params={"cond": "i<10"}, children=[
              inc, C(cmd="If", params={"cond": "i==2"}, children=[C(cmd="Continue")]),
              C(cmd="If", params={"cond": "i>=4"}, children=[C(cmd="Break")]), drill("i*10", 10)])]
    assert [o["X"] for o in evaluate(br, 480, 800, 16)] == [10, 30]
    # sikldan tashqarida Break — xabar
    assert program_stats([C(cmd="Break")], 480, 800, 16)["errors"] == 1


def test_infinite_loops_are_bounded():
    forever = [C(cmd="While", params={"cond": "1"}, children=[drill(10, 10)])]
    st = program_stats(forever, 480, 800, 16)
    assert st["drills"] == MAX_LOOP_ITER and st["errors"] == 1
    nested = [C(cmd="While", params={"cond": "1"}, children=[C(cmd="While", params={"cond": "1"}, children=[drill(1, 1)])])]
    st = program_stats(nested, 480, 800, 16)             # ichma-ich — umumiy qadam chegarasi to'xtatadi
    assert st["drills"] < 200_000 and st["errors"] >= 1
    rec = [C(cmd="Sub", params={"name": "r"}, children=[drill(1, 1), C(cmd="Call", params={"name": "r"})]),
           C(cmd="Call", params={"name": "r"})]
    st = program_stats(rec, 480, 800, 16)                # cheksiz rekursiya
    assert 0 < st["drills"] <= 64 and st["errors"] >= 1


def test_sub_call_ret():
    sub = C(cmd="Sub", params={"name": "s1"}, children=[drill(10, 10)])
    # Sub ta'rifi joyida bajarilmaydi; har Call — bajaradi (ta'rifdan oldin ham chaqirish mumkin)
    assert program_stats([sub, C(cmd="Call", params={"name": "s1"}), C(cmd="Call", params={"name": "s1"})],
                         480, 800, 16)["drills"] == 2
    assert program_stats([C(cmd="Call", params={"name": "s1"}), sub], 480, 800, 16)["drills"] == 1
    st = program_stats([C(cmd="Call", params={"name": "yo'q"})], 480, 800, 16)
    assert st["drills"] == 0 and st["errors"] == 1
    # Ret: qism dasturdan chiqish; yuqori darajada — dasturni to'xtatish
    sub2 = C(cmd="Sub", params={"name": "s2"}, children=[drill(1, 1), C(cmd="Ret"), drill(2, 2)])
    assert program_stats([sub2, C(cmd="Call", params={"name": "s2"}), drill(3, 3)], 480, 800, 16)["drills"] == 2
    assert program_stats([drill(1, 1), C(cmd="Ret"), drill(2, 2)], 480, 800, 16)["drills"] == 1


def test_control_flow_via_api(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    prog = [{"cmd": "If", "params": {"cond": "dx>500"}, "children": [
                {"cmd": "DrillFront", "params": {"X": 10, "Y": 10, "D": 8, "DP": 12}}]},
            {"cmd": "Else", "params": {}, "children": [
                {"cmd": "DrillFront", "params": {"X": 10, "Y": 10, "D": 8, "DP": 12}},
                {"cmd": "DrillFront", "params": {"X": 20, "Y": 10, "D": 8, "DP": 12}}]}]
    _set_prog(client, pid, xid, prog)                              # dx = 480 (detal)
    assert client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()["drills"] == 2
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{ptid}", json={"length": 600})
    assert client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()["drills"] == 1


# ───────────────────────── №14 · XNC chizma: yoylar, Origin, burish/ko'zgu ─────────────────────────
def _xop(prog, length=300, width=300, **kw):
    return Operation(type=OpType.XNC, xnc=XNCParams(length=length, width=width, thickness=16, program=prog, **kw))


def _start(x, y):
    return C(cmd="MillStart", params={"X": x, "Y": y, "DP": 8, "T": "M8"})


def test_arcs_drawn_as_arcs_and_measured():
    semi = 3.14159265 * 50 / 1000                             # yarim aylana, R=50
    for arc in (C(cmd="MillArc", params={"X": 100, "Y": 0, "R": 50}),
                C(cmd="MillArc3P", params={"X": 100, "Y": 0, "X2": 50, "Y2": 50}),
                C(cmd="MillArcCenter", params={"X": 100, "Y": 0, "CX": 50, "CY": 0, "DIR": "true"})):
        prog = [_start(0, 0), arc]
        st = program_stats(prog, 300, 300, 16)
        assert st["mill_m"] == pytest.approx(semi, abs=0.0006), arc.cmd
        svg = xnc_drawing_svg(_xop(prog))
        assert re.search(r'<path d="M 0 0 A 50 50 0 [01] [01] 100 0"', svg), (arc.cmd, svg)
    # 3 nuqta: yoy uzunligi — vatar emas
    assert program_stats([_start(0, 0), C(cmd="MillArc3P", params={"X": 100, "Y": 0, "X2": 50, "Y2": 50})],
                         300, 300, 16)["mill_m"] == pytest.approx(0.157, abs=0.001)
    # bir to'g'ri chiziqdagi 3 nuqta — to'g'ri chiziq (vatar)
    line3 = [_start(0, 0), C(cmd="MillArc3P", params={"X": 100, "Y": 0, "X2": 50, "Y2": 0})]
    assert program_stats(line3, 300, 300, 16)["mill_m"] == pytest.approx(0.1, abs=1e-6)
    assert " L 100 0" in xnc_drawing_svg(_xop(line3))
    # R < 0 — teskari yo'nalish (yoyning boshqa tomoni), uzunlik bir xil
    a = xnc_drawing_svg(_xop([_start(0, 0), C(cmd="MillArc", params={"X": 60, "Y": 0, "R": 50})]))
    b = xnc_drawing_svg(_xop([_start(0, 0), C(cmd="MillArc", params={"X": 60, "Y": 0, "R": -50})]))
    assert a != b and "A 50 50" in a and "A 50 50" in b


def test_origin_command_shifts_coordinates():
    prog = [C(cmd="Origin", params={"X": 100, "Y": 100}), drill(10, 10),
            C(cmd="DrillLeft", params={"Y": 5, "Z": 8, "D": 5, "DP": 20}),
            C(cmd="Origin", params={"X": "origin.x+50", "Y": 0}), drill(10, 10)]
    ops = evaluate(prog, 400, 400, 16)
    assert [(o["X"], o["Y"]) for o in ops if o["kind"] == "DrillFront"] == [(110, 110), (160, 10)]
    assert [o["Y"] for o in ops if o["kind"] == "DrillLeft"] == [105]
    # shift tufayli detaldan chiqib ketgan teshik — bajarilmaydi
    assert program_stats([C(cmd="Origin", params={"X": 395, "Y": 0}), drill(10, 10)], 400, 400, 16)["drills"] == 0
    rows = xnc_holes_table(_xop([C(cmd="Origin", params={"X": 100, "Y": 100}), drill(10, 10)], 400, 400))
    assert rows[0][1:3] == ["110", "110"]
    pr = [_start(0, 0), C(cmd="Origin", params={"X": 10, "Y": 10}), C(cmd="MillLine", params={"X": 100, "Y": 0})]
    assert " L 110 10" in xnc_drawing_svg(_xop(pr))


def test_rotation_mirror_origin_params_affect_drawing():
    prog = [drill(10, 20)]
    base = xnc_drawing_svg(_xop(prog, 200, 100))
    assert 'cx="10" cy="20"' in base
    assert 'cx="80" cy="10"' in xnc_drawing_svg(_xop(prog, 200, 100, rotation=90))        # (dy − y, x)
    assert 'cx="190" cy="80"' in xnc_drawing_svg(_xop(prog, 200, 100, rotation=180))
    assert 'cx="20" cy="190"' in xnc_drawing_svg(_xop(prog, 200, 100, rotation=270))
    assert 'cx="190" cy="20"' in xnc_drawing_svg(_xop(prog, 200, 100, mirror_x=True))
    assert 'cx="10" cy="80"' in xnc_drawing_svg(_xop(prog, 200, 100, mirror_y=True))
    assert 'cx="190" cy="20"' in xnc_drawing_svg(_xop(prog, 200, 100, origin="RT"))
    assert 'cx="190" cy="80"' in xnc_drawing_svg(_xop(prog, 200, 100, origin="RB"))
    assert '>100</text>' in xnc_drawing_svg(_xop(prog, 200, 100, rotation=90), dims=True)  # yuqori o'lcham — burilgan eni (dims=True)
    # statistika (uzunlik, teshiklar soni) burish / ko'zgu / koordinata boshidan o'zgarmaydi
    mill = [_start(0, 0), C(cmd="MillLine", params={"X": 100, "Y": 0}), drill(10, 20)]
    st0 = xnc_stats(_xop(mill, 200, 100).xnc)
    for kw in (dict(rotation=90), dict(rotation=270, mirror_x=True), dict(origin="RB", mirror_y=True)):
        assert xnc_stats(_xop(mill, 200, 100, **kw).xnc) == st0


# ───────────────────────── №2 · GR (paz) ─────────────────────────
def _gr_project(client, name="GR proyekt"):
    pid, cs = _new_project(client, name, "GRCS")
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "GR", "code": "G4", "name": "Paz 4"}).json()
    gr = p["operations"][-1]["id"]
    client.patch(f"/api/projects/{pid}/operations/{gr}", json={"gr": {"price": 2000}})
    _add_parts(client, pid, cs, [
        {"name": "A", "length": 800, "width": 500, "qty": 3, "groove_top": {"op_id": gr}},
        {"name": "B", "length": 600, "width": 300, "qty": 2, "groove_right": {"op_id": gr, "back_side": True}},
        {"name": "C", "length": 400, "width": 400, "qty": 1}])
    return pid, cs, gr


def test_gr_usage_cost_and_report(client):
    pid, cs, gr = _gr_project(client)
    p = client.get(f"/api/projects/{pid}").json()
    g = _op(p, gr)
    # 800 × 3 + 300 × 2 = 3000 mm → 3.0 m; narx 2000 → 6000
    assert g["gr"]["usage"] == 3.0 and g["gr"]["passes"] == 1 and g["gr"]["cut_length"] == 3.0
    assert g["cost_operation"] == 6000 and g["cost_material"] == 0
    row = next(r for r in client.get("/api/projects", params={"q": "GR proyekt"}).json() if r["id"] == pid)
    assert row["cost"] == 6000                                          # loyiha summasiga qo'shilgan
    html = client.get(f"/api/projects/{pid}/report").text
    assert "(GR)" in html and "Длина пазования" in html and "3 м" in html and "6000" in html
    assert "ПВ" in html and "+ обр." in html and "Д-на паза" in html
    assert "Pazlash uzunligi" in client.get(f"/api/projects/{pid}/report?lang=uz").text
    # arra o'tishlari = ⌈en / arra⌉, kesish uzunligi = paz uzunligi × o'tishlar
    client.patch(f"/api/projects/{pid}/operations/{gr}", json={"gr": {"width": 10, "saw_thickness": 4}})
    g = _op(client.get(f"/api/projects/{pid}").json(), gr)
    assert g["gr"]["passes"] == 3 and g["gr"]["cut_length"] == 9.0 and g["gr"]["usage"] == 3.0
    assert g["cost_operation"] == 6000                                  # narx — paz uzunligi bo'yicha
    # МК va mahsulot soni: (ОК − МК)
    parts = _op(client.get(f"/api/projects/{pid}").json(), cs)["parts"]
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{parts[0]['id']}", json={"minus_qty": 1})
    assert _op(client.get(f"/api/projects/{pid}").json(), gr)["gr"]["usage"] == 2.2     # (3−1)·800 + 2·300 = 2200 mm


def test_gr_usage_value_with_product_qty(client):
    pid, cs, gr = _gr_project(client, "GR proyekt 2")
    parts = _op(client.get(f"/api/projects/{pid}").json(), cs)["parts"]
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{parts[0]['id']}", json={"minus_qty": 1})
    prid = client.get(f"/api/projects/{pid}").json()["products"][0]["id"]
    client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": 2})
    g = _op(client.get(f"/api/projects/{pid}").json(), gr)
    # ОК = qty × mahsulot soni: A 6 − МК 1 = 5 → 5·800 = 4000 ; B 4 → 4·300 = 1200 ; jami 5200 mm
    assert g["gr"]["usage"] == 5.2 and g["cost_operation"] == 10400


def test_gr_product_cost_share_and_group_parts(client):
    pid, cs, gr = _gr_project(client, "GR proyekt 3")
    p = client.get(f"/api/projects/{pid}").json()
    assert p["products"][0]["cost_operation"] == 6000                  # yagona mahsulot — GR narxining hammasi


def test_gr_validation_and_legacy_params():
    assert GRParams.model_validate({"width": 4, "depth": 10, "offset": 16, "price": 0}).saw_thickness == 4   # eski JSON
    for bad in ({"width": 0}, {"width": -4}, {"saw_thickness": 0}, {"price": -1}, {"depth": -1}):
        with pytest.raises(ValueError):
            GRParams.model_validate(bad)


def test_gr_api_rejects_bad_width(client):
    pid, cs, gr = _gr_project(client, "GR proyekt 4")
    assert client.patch(f"/api/projects/{pid}/operations/{gr}", json={"gr": {"width": -4}}).status_code == 422
    assert client.patch(f"/api/projects/{pid}/operations/{gr}", json={"gr": {"price": -5}}).status_code == 422


# ───────────────────────── №22 · server tomonidagi chegaralar va eski JSON ─────────────────────────
def test_api_rejects_out_of_range_values(client, kravat):
    pid, cs, el = kravat
    for fld, val in (("waste_percent", -200), ("waste_percent", 150), ("price", -100), ("marker_lines", 9),
                     ("marker_lines", -1), ("thickness", -2)):
        r = client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {fld: val}})
        assert r.status_code == 422, (fld, val)
    assert client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {"marker_lines": 0}}).status_code == 200
    base = {"name": "x", "length": 100, "width": 50}
    for bad in ({"length": -5}, {"width": -1}, {"qty": -1}, {"qty": 10 ** 9}, {"qty": 100001}, {"minus_qty": -2}):
        r = client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[{**base, **bad}])
        assert r.status_code == 422, bad
    ok = client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[{**base, "qty": 100000}])
    assert ok.status_code == 200
    assert client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[{**base, "length": 0, "width": 0}]).status_code == 200
    prid = client.get(f"/api/projects/{pid}").json()["products"][0]["id"]
    assert client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": 10 ** 9}).status_code == 422


def test_old_json_with_bad_values_still_opens(client, kravat):
    pid, cs, el = kravat
    with SessionLocal() as s:
        row = s.get(ProjectRow, pid)
        d = copy.deepcopy(row.data)
        e = next(o for o in d["operations"] if o["id"] == el)
        e["el"].update(waste_percent=-200, price=-100, marker_lines=9, symbol="ABCDE")
        c = next(o for o in d["operations"] if o["id"] == cs)
        c["parts"][0].update(qty=10 ** 9, length=-5)
        c["parts"][1].update(qty=-3, minus_qty=-1)
        d["products"][0]["qty"] = 10 ** 9
        d["operations"].append({"id": "gr_old", "type": "GR", "name": "old", "gr": {"width": -4, "depth": 10, "offset": 16,
                                                                                    "price": -1}})
        row.data = d
        s.commit()
    r = client.get(f"/api/projects/{pid}")
    assert r.status_code == 200, r.text
    p = r.json()
    e = _op(p, el)["el"]
    assert (e["waste_percent"], e["price"], e["marker_lines"], e["symbol"]) == (0, 0, 3, "ABC")
    pt = _op(p, cs)["parts"]
    assert (pt[0]["qty"], pt[0]["length"], pt[1]["qty"], pt[1]["minus_qty"]) == (100000, 0, 0, 0)
    assert p["products"][0]["qty"] == 100000
    assert _op(p, "gr_old")["gr"]["width"] == 4 and _op(p, "gr_old")["gr"]["price"] == 0
    # .mxk.json import ham (eski eksport fayllari) ochiladi
    exp = client.get(f"/api/projects/{pid}/export")
    assert exp.status_code == 200
    bad = exp.text.replace('"marker_lines": 3', '"marker_lines": 9')
    imp = client.post("/api/projects/import", files={"file": ("bad.mxk.json", bad.encode("utf-8"))})
    assert imp.status_code == 200
    client.delete(f"/api/projects/{imp.json()['id']}")
    # to'g'ridan-to'g'ri (API) kiritish esa qat'iy: Part / ELParams
    with pytest.raises(ValueError):
        Part.model_validate({"length": -5, "width": 10})
    with pytest.raises(ValueError):
        ELParams.model_validate({"waste_percent": -200})
    assert Project.model_validate({"operations": [{"type": "EL", "el": {"waste_percent": -200}}]}).operations[0].el.waste_percent == 0


# ───────────────────────── №6 · ombor «arvoh» qoldiq ─────────────────────────
def _ghost_pair(client, tag):
    """A loyiha kroyi → omborga yozildi; B loyiha shu qoldiqdan foydalanib, kroy qildi va omborga yozdi."""
    from conftest import KRAVAT
    code = f"GHOST-{tag}"
    pa = client.post("/api/projects", json={"name": f"ghost A {tag}"}).json()
    ca = client.post(f"/api/projects/{pa['id']}/operations", json={"type": "CS", "code": code, "name": code}).json()
    csa = ca["operations"][-1]["id"]
    client.post(f"/api/projects/{pa['id']}/operations/{csa}/parts",
                json=[dict(name=f"P{u}", length=L, width=W, qty=q) for u, L, W, q in KRAVAT])
    client.post(f"/api/projects/{pa['id']}/operations/{csa}/optimize?quality=fast")
    out = client.post(f"/api/projects/{pa['id']}/operations/{csa}/remnants/commit").json()
    rid = out["added"][0]["id"]
    pb = client.post("/api/projects", json={"name": f"ghost B {tag}"}).json()
    cb = client.post(f"/api/projects/{pb['id']}/operations", json={"type": "CS", "code": code, "name": code}).json()
    csb = cb["operations"][-1]["id"]
    client.post(f"/api/projects/{pb['id']}/operations/{csb}/parts", json=[{"name": "k", "length": 300, "width": 200}])
    client.post(f"/api/projects/{pb['id']}/operations/{csb}/sheets/from-remnants", json={"ids": [rid]})
    client.post(f"/api/projects/{pb['id']}/operations/{csb}/optimize?quality=fast")
    assert client.post(f"/api/projects/{pb['id']}/operations/{csb}/remnants/commit").status_code == 200
    return pa["id"], csa, pb["id"], csb, rid, [a["id"] for a in out["added"]]


def _stock(client):
    return {r["id"]: r["qty"] for r in client.get("/api/remnants?include_empty=true").json()}


def test_warehouse_no_ghost_remnant_a_then_b(client):
    pa, csa, pb, csb, rid, added = _ghost_pair(client, "AB")
    client.post(f"/api/projects/{pa}/operations/{csa}/remnants/rollback")           # avval A
    assert _stock(client).get(rid, 0) == 0
    client.post(f"/api/projects/{pb}/operations/{csb}/remnants/rollback")           # keyin B
    st = _stock(client)
    assert st.get(rid, 0) == 0 and all(st.get(a, 0) == 0 for a in added)           # «arvoh» qoldiq yo'q


def test_warehouse_no_ghost_remnant_b_then_a(client):
    pa, csa, pb, csb, rid, added = _ghost_pair(client, "BA")
    client.post(f"/api/projects/{pb}/operations/{csb}/remnants/rollback")           # avval B
    assert _stock(client).get(rid, 0) >= 1                                          # qoldiq qaytdi
    client.post(f"/api/projects/{pa}/operations/{csa}/remnants/rollback")           # keyin A
    st = _stock(client)
    assert st.get(rid, 0) == 0 and all(st.get(a, 0) == 0 for a in added)


def test_warehouse_rollback_reports_orphaned(client):
    pa, csa, pb, csb, rid, _added = _ghost_pair(client, "ORPH")
    out = client.post(f"/api/projects/{pa}/operations/{csa}/remnants/rollback").json()
    assert rid in out["orphaned"] and rid in out["removed"]
    assert client.post(f"/api/projects/{pb}/operations/{csb}/remnants/rollback").json()["restored"] == {}


# ───────────────────────── №10, №17, №18 · hisobot ─────────────────────────
def _first_part_rect(html):
    m = re.search(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" fill="#F2A541"', html)
    return tuple(float(v) for v in m.groups())


def test_report_mirror_only_geometry(client, kravat):
    pid, cs, el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    res = _op(client.get(f"/api/projects/{pid}").json(), cs)["result"]
    ps = client.get("/api/settings/print/default").json()
    normal = client.post(f"/api/projects/{pid}/report", json={**ps, "map_mirror": False, "map_mono": False}).text
    mirror = client.post(f"/api/projects/{pid}/report", json={**ps, "map_mirror": True, "map_mono": False}).text
    assert "scale(-1" not in mirror and "scale(-1" not in normal
    x, y, w, h = _first_part_rect(normal)
    xm, ym, wm, hm = _first_part_rect(mirror)
    L = res["maps"][0]["sheet_length"]
    assert (ym, wm, hm) == (y, w, h) and xm == pytest.approx(L - x - w, abs=0.02)      # geometriya akslandi
    # matnlar — o'sha, o'qiladigan (transformsiz): son va tartib bir xil
    t_n = re.findall(r"<text[^>]*>([^<]*)</text>", normal)
    t_m = re.findall(r"<text[^>]*>([^<]*)</text>", mirror)
    assert t_n == t_m and t_n
    # maps/{i}.svg?mirror=true ham
    svg = client.get(f"/api/projects/{pid}/operations/{cs}/maps/1.svg?mirror=true").text
    assert "scale(-1" not in svg


def test_report_map_header_stays_with_card(client, kravat):
    pid, cs, el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    html = client.get(f"/api/projects/{pid}/report").text
    assert re.search(r"\.maphdr\s*\{[^}]*(page-break-after|break-after):\s*avoid", html)
    assert re.search(r"\.mapcard\s*\{[^}]*(page-break-inside|break-inside):\s*avoid", html)
    assert "<div class='mapcard'><div class='maphdr'>" in html            # sarlavha va karta bitta blokda


def test_report_xnc_stamp_has_product_and_sizes(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    prid = client.get(f"/api/projects/{pid}").json()["products"][0]["id"]
    client.patch(f"/api/projects/{pid}/products/{prid}", json={"name": "Shkaf-X", "qty": 3})
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{ptid}", json={"qty": 2, "minus_qty": 1})
    html = client.get(f"/api/projects/{pid}/report").text
    stamp = html[html.index("(XNC)"):]
    assert "<th>Изделие</th><td>Shkaf-X</td>" in stamp
    assert "<th>Рм. детали</th><td>480 × 800 × 16</td>" in stamp and "<th>Рм. заготовки</th>" in stamp
    assert "2 × 3 = 6 шт − 1 = 5 шт" in stamp
    assert "<th>По размеру детали</th><td>Да</td>" in stamp


# ───────────────────────── №11 · EL «умолч.»: belgi va rang yozilmaydi ─────────────────────────
def test_el_defaults_do_not_store_symbol_and_color(client):
    d = client.get("/api/settings/el_defaults/default").json()
    r = client.put("/api/settings/el_defaults/default", json={**d, "symbol": "C", "color": "#c0392b", "thickness": 1})
    assert r.status_code == 200 and "symbol" not in r.json()["data"] and "color" not in r.json()["data"]
    cur = client.get("/api/settings/el_defaults/default").json()
    assert cur["symbol"] == "A" and cur["color"] == "#000000" and cur["thickness"] == 1
    pid = client.post("/api/projects", json={"name": "EL avto"}).json()["id"]
    p = None
    for _i in range(4):
        p = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "name": f"K{_i}"}).json()
    els = [o["el"] for o in p["operations"] if o["type"] == "EL"]
    assert [e["symbol"] for e in els] == ["A", "B", "C", "D"]
    assert len({e["color"] for e in els}) == 4 and all(e["thickness"] == 1 for e in els)     # boshqa maydonlar saqlanadi
    # o'chirilgandan keyin ham takrorlanmaydi (band bo'lmagan birinchi harf)
    p = client.delete(f"/api/projects/{pid}/operations/{[o for o in p['operations'] if o['type'] == 'EL'][1]['id']}").json()
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "name": "K9"}).json()
    syms = [o["el"]["symbol"] for o in p["operations"] if o["type"] == "EL"]
    assert len(set(syms)) == len(syms) == 4
    client.put("/api/settings/el_defaults/default", json={**d, "thickness": 0})


# ───────────────────────── №21 · kromka detaldan katta ─────────────────────────
def test_edge_thicker_than_part_is_reported_not_dropped(client):
    pid, cs = _new_project(client, "Kromka katta")
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "name": "Qalin"}).json()
    el = p["operations"][-1]["id"]
    client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {"thickness": 500}})
    p = _add_parts(client, pid, cs, [
        {"name": "Yomon", "length": 800, "width": 400, "qty": 3, "edge_top": {"op_id": el}},
        {"name": "Yaxshi", "length": 500, "width": 300, "qty": 2},
        {"name": "Bo'sh", "length": 0, "width": 0, "qty": 1},
        {"name": "Yarim", "length": 500, "width": 0, "qty": 2}])
    client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": {"machining_allowance": 3}})
    parts = _op(client.get(f"/api/projects/{pid}").json(), cs)["parts"]
    res = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").json()
    # bo'sh qator (0×0, hali kiritilmagan qoralama) jim; bir tomoni 0 yoki kromka detaldan katta — ko'rsatiladi
    assert sorted(res["unplaced"]) == sorted([parts[0]["id"]] * 3 + [parts[3]["id"]] * 2)
    assert any(f"№{parts[0]['uid']}" in w for w in res["warnings"]) and any(f"№{parts[3]['uid']}" in w
                                                                             for w in res["warnings"])
    assert not any(f"№{parts[2]['uid']}" in w for w in res["warnings"])
    p = client.get(f"/api/projects/{pid}").json()
    q = _op(p, cs)["parts"]
    assert (q[0]["used_qty"], q[0]["left_qty"]) == (0, 3) and q[1]["used_qty"] == 2
    assert (q[3]["used_qty"], q[3]["left_qty"]) == (0, 2)
    assert res["total_parts"] == 2                                       # bo'sh qator «припуск» bilan ham kesilmaydi
    # §11: «Печать невместившихся деталей» standarti Нет — jadval aniq yoqilganda chiqadi
    html = client.post(f"/api/projects/{pid}/report", json={"cs_unplaced": True}).text
    assert "Невместившиеся" in html


# ───────────────────────── №23 · XNC yetim / ulashish ─────────────────────────
def test_deleting_part_removes_its_xnc(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    _set_prog(client, pid, xid, [{"cmd": "DrillFront", "params": {"X": 10, "Y": 10, "D": 8, "DP": 12}}], drill_price=200)
    p = client.get(f"/api/projects/{pid}").json()
    assert _op(p, xid)["cost_operation"] == 200
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/delete", json={"ids": [ptid]}).json()
    assert not _ops(p, "XNC")                                            # operatsiya olib tashlandi
    assert all(not pt["xnc_op_ids"] for o in p["operations"] for pt in o["parts"])
    assert "(XNC)" not in client.get(f"/api/projects/{pid}/report").text
    assert sum(o["cost_material"] + o["cost_operation"] for o in p["operations"]) == \
        next(r for r in client.get("/api/projects", params={"q": "Detskiy"}).json() if r["id"] == pid)["cost"]


def test_deleting_cs_operation_or_product_removes_linked_xnc(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    p = client.delete(f"/api/projects/{pid}/operations/{cs}").json()
    assert not _ops(p, "XNC")


def test_xnc_shared_by_two_parts_survives_one_deletion(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    parts = _op(client.get(f"/api/projects/{pid}").json(), cs)["parts"]
    other = next(x for x in parts if x["id"] != ptid)
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{other['id']}", json={"xnc_op_ids": [xid]})
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/delete", json={"ids": [ptid]}).json()
    x = _op(p, xid)
    assert x["xnc_part_id"] == other["id"]                               # bog'lanish qolgan detalga o'tdi


def test_clone_operation_does_not_share_xnc(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    p = client.post(f"/api/projects/{pid}/operations/{cs}/clone").json()
    css = _ops(p, "CS")
    assert len(css) == 2
    assert all(not pt["xnc_op_ids"] for pt in css[1]["parts"])           # nusxa asl XNC ga qaramaydi
    assert any(xid in pt["xnc_op_ids"] for pt in css[0]["parts"])
    assert len(_ops(p, "XNC")) == 1


# ───────────────────────── №24 / №25 · etiketka va EL belgi chiziqlari ─────────────────────────
def test_label_settings_validation(client, kravat):
    pid, cs, el = kravat
    for bad in ({"width_mm": -5}, {"width_mm": 0}, {"height_mm": -1}, {"columns": 1000000}, {"columns": -1},
                {"width_mm": 100000}):
        assert client.post(f"/api/projects/{pid}/labels", json=bad).status_code == 422, bad
        assert client.post("/api/settings/labels", json={"name": "bad", "data": bad}).status_code == 400, bad
    assert client.post(f"/api/projects/{pid}/labels", json={"columns": 0}).status_code == 200


def test_small_label_scales_and_keeps_footer(client, kravat):
    pid, cs, el = kravat
    big = client.post(f"/api/projects/{pid}/labels", json={"width_mm": 58, "height_mm": 40, "columns": 0}).text
    small = client.post(f"/api/projects/{pid}/labels", json={"width_mm": 40, "height_mm": 25, "columns": 0}).text
    assert re.search(r"size: 40(\.0)?mm 25(\.0)?mm", small)
    fs = lambda h: float(re.search(r"\.dim \{ font-size: ([\d.]+)mm", h).group(1))      # noqa: E731
    assert fs(small) < fs(big) and "white-space: nowrap" in small.split(".foot")[1].split("}")[0]


def test_qr_copy_number_range():
    assert labels.parse_qr("MXK:1000123:7:2/4") == dict(kind="part", number=1000123, uid=7, copy=2, total=4)
    for bad in ("MXK:1:7:3/2", "MXK:1:7:0/0", "MXK:1:7:-1/-1", "MXK:1:7:0/3", "MXK:1:7:1/0", "XXX:1:7:1/1"):
        assert labels.parse_qr(bad) is None, bad
    assert labels.parse_qr("MXK:1000123:abc:3")["kind"] == "map" and labels.parse_qr("MXK:1:abc:0") is None


def test_scan_rejects_copy_out_of_range(client, kravat):
    pid = kravat[0]
    num = client.get(f"/api/projects/{pid}").json()["number"]
    assert client.get(f"/api/mes/scan/MXK:{num}:6:1/1").status_code == 200
    for code in (f"MXK:{num}:6:3/2", f"MXK:{num}:6:0/0", f"MXK:{num}:6:-1/-1"):
        assert client.get(f"/api/mes/scan/{code}").status_code == 400, code


def test_marker_lines_zero_and_counts(client, kravat):
    pid, cs, el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    ps = {**client.get("/api/settings/print/default").json(), "map_qr": False, "map_edges": True}

    def lines(n):
        client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {"marker_lines": n}})
        t = client.post(f"/api/projects/{pid}/report", json=ps).text
        return t.count("<line ") - t.count('class="cut"')                    # arra kesish chiziqlari sanalmaydi
    assert [lines(n) for n in (0, 1, 2, 3)] == [0, 2, 4, 6]               # №6 detal: ikki kromkali tomon
    html = client.post(f"/api/projects/{pid}/report", json=ps).text
    assert "<td>Линии маркировки</td><td>3</td>" in html                   # EL parametrlar bloki
    assert "</span> A: PVC 1-19" in html                                   # legenda «A: <kromka>» (X_1015 §9; avval «A-3:»)
    client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {"marker_lines": 0}})
    assert "<td>Линии маркировки</td><td>0</td>" in client.post(f"/api/projects/{pid}/report", json=ps).text   # «0» 1 ga aylanmaydi
    lab = client.post(f"/api/projects/{pid}/labels", json={"columns": 0}).text
    assert 'stroke-width="3.5"' not in lab                                # chiziqsiz, faqat belgi


# ───────────────────────── №26 · bir xil nomli kromkalar (qalinligi boshqa) birlashtirilmaydi ─────────────────────────
def test_merge_same_keeps_edges_with_different_thickness(client, kravat):
    pid, cs, el = kravat
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "code": "KP-1/19", "name": "PVC 1-19"}).json()
    el2 = p["operations"][-1]["id"]
    client.patch(f"/api/projects/{pid}/operations/{el2}", json={"el": {"thickness": 2}})
    p = client.post(f"/api/projects/{pid}/actions/merge-same").json()
    assert len(_ops(p, "EL")) == 2
    client.patch(f"/api/projects/{pid}/operations/{el2}", json={"el": {"thickness": 0}})        # bir xil bo'ldi
    p = client.post(f"/api/projects/{pid}/actions/merge-same").json()
    assert len(_ops(p, "EL")) == 1


# ───────────────────────── QA B №5 · StockSheet (list) chegaralari ─────────────────────────
def _sheet(**kw):
    return {"length": 2750, "width": 1830, "qty": 10000, **kw}


def test_stock_sheet_validation(client, kravat):
    pid, cs, el = kravat
    url = f"/api/projects/{pid}/operations/{cs}/sheets"
    for bad in ({"length": 0}, {"length": -100}, {"width": 0}, {"length": 20001}, {"qty": -3}, {"qty": 10001},
                {"trim_length": -1}, {"trim_width": 501}, {"end_offset_bottom": -2}, {"end_offset_right": 9999}):
        assert client.put(url, json=[_sheet(**bad)]).status_code == 422, bad
    ok = client.put(url, json=[_sheet(trim_length=0, trim_width=5, end_offset_bottom=None, qty=0),
                               _sheet(length=20000, width=20000, qty=10000, end_offset_right=500)])
    assert ok.status_code == 200, ok.text
    for lim in ({"length": 190, "width": 80, "qty": 1}, {"length": 4200, "width": 2070}):      # real fayllardagi diapazon
        assert client.put(url, json=[_sheet(**lim)]).status_code == 200


def test_old_json_with_bad_sheet_and_cs_params_still_opens(client, kravat):
    pid, cs, el = kravat
    with SessionLocal() as s:
        row = s.get(ProjectRow, pid)
        d = copy.deepcopy(row.data)
        c = next(o for o in d["operations"] if o["id"] == cs)
        c["sheets"][0].update(length=-100, width=0, qty=-3, trim_length=5000, end_offset_right=-2)
        c["cs_material"].update(thickness=-5, price=-100, min_part_size=99999, est_fill_percent=500)
        c["cs_cut"].update(kerf=-3, max_rotations=99, pack_height=-40, trim_length=5000, min_trim_cut=3000, fill_packet=150)
        row.data = d
        s.commit()
    r = client.get(f"/api/projects/{pid}")
    assert r.status_code == 200, r.text
    c = _op(r.json(), cs)
    sh, m, cut = c["sheets"][0], c["cs_material"], c["cs_cut"]
    assert (sh["length"], sh["width"], sh["qty"], sh["trim_length"], sh["end_offset_right"]) == (1, 1, 0, 500, 0)
    assert (m["thickness"], m["price"], m["min_part_size"], m["est_fill_percent"]) == (0, 0, 10000, 100)
    assert (cut["kerf"], cut["max_rotations"], cut["pack_height"], cut["trim_length"], cut["min_trim_cut"],
            cut["fill_packet"]) == (0, 6, 0, 500, 500, 100)


# ───────────────────────── QA B №6 · CS parametrlari chegaralari ─────────────────────────
@pytest.mark.parametrize("sect,fld,val", [
    ("cs_material", "thickness", -5), ("cs_material", "thickness", 1000000000), ("cs_material", "price", -100),
    ("cs_material", "price", 1e12), ("cs_material", "min_part_size", -10), ("cs_material", "min_part_size", 99999),
    ("cs_material", "est_fill_percent", 150), ("cs_material", "op_price", -1), ("cs_material", "remnant_min_side1", -1),
    ("cs_material", "remnant_min_area", -0.5),
    ("cs_cut", "pack_height", -40), ("cs_cut", "kerf", 999), ("cs_cut", "kerf", -3), ("cs_cut", "trim_length", 5000),
    ("cs_cut", "trim_width", -1), ("cs_cut", "min_trim_cut", 3000), ("cs_cut", "max_rotations", 99),
    ("cs_cut", "max_rotations", 0), ("cs_cut", "fill_packet", 150), ("cs_cut", "kerf_group", -1),
    ("cs_cut", "end_offset_bottom", -3), ("cs_cut", "max_strip_width", -5),
])
def test_cs_param_out_of_range_rejected(client, kravat, sect, fld, val):
    pid, cs, el = kravat
    r = client.patch(f"/api/projects/{pid}/operations/{cs}", json={sect: {fld: val}})
    assert r.status_code == 422, (sect, fld, val)


def test_cs_param_real_and_edge_values_accepted(client, kravat):
    pid, cs, el = kravat
    good = {"cs_material": {"thickness": 0, "price": 420000, "min_part_size": 0, "est_fill_percent": 100,
                            "remnant_min_side1": 0, "remnant_min_area": 0},
            "cs_cut": {"kerf": 0, "kerf_group": 0, "trim_length": 0, "trim_width": 500, "min_trim_cut": 0,
                       "max_rotations": 2, "pack_height": 0, "fill_packet": 0, "end_offset_bottom": 0}}
    r = client.patch(f"/api/projects/{pid}/operations/{cs}", json=good)
    assert r.status_code == 200, r.text
    for v in ({"thickness": 350}, {"thickness": 1000}):                  # korxona loyihalarida 350 mm uchragan
        assert client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_material": v}).status_code == 200
    for v in ({"max_rotations": 6}, {"max_rotations": 1}, {"kerf": 4.4}, {"max_strip_length": 10000}):   # 1…6 (W10)
        assert client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": v}).status_code == 200
    # standart qiymatlar va v1 maydonlar (eski JSON) o'qiladi
    from app.models import CSCutParams, CSMaterialParams
    CSCutParams()
    CSMaterialParams()
    assert CSCutParams.model_validate({"trim_both_sides": False}).end_offset_bottom == 0.0


# ───────────────────────── XNC DZ: material qalinligiga ergashadi (faqat unga teng bo'lsa) ─────────────────────────
def test_xnc_dz_follows_material_thickness_only_when_equal(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    assert _op(client.get(f"/api/projects/{pid}").json(), xid)["xnc"]["thickness"] == 16
    client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_material": {"thickness": 18}})
    assert _op(client.get(f"/api/projects/{pid}").json(), xid)["xnc"]["thickness"] == 18
    client.patch(f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"thickness": 32}})        # boshqacha (ikki qatlam)
    client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_material": {"thickness": 16}})
    assert _op(client.get(f"/api/projects/{pid}").json(), xid)["xnc"]["thickness"] == 32
