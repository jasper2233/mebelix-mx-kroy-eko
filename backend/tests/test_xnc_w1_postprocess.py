"""W1 · Ishlov markazi (XNC operatsiyasi) postprotsessor konteksti: hisoblangan amallar, burish / ko'zgu / koordinata boshi
oldindan qo'llangan, detal o'lchamlari va kromkalar, asboblar; o'rnatilgan JSON, Jinja shablon, stanok guruhi, uzun tomon."""
import json
import math

import pytest

from app.models import Operation, OpType, PostprocessorProfile, Project, XNCParams, XncCommand as C
from app.services import postprocessors as pp
from app.services import xnc as X

from test_qa_fix_calc import _op, _ops, _set_prog, _xnc_for


def cmd(kind, /, **p):
    return C(cmd=kind, params=p)


def xop(prog, length=200, width=100, **kw):
    return Operation(type=OpType.XNC, code="K1", name="Bok", xnc=XNCParams(length=length, width=width, thickness=16,
                                                                          by_part_size=False, program=prog, **kw))


def project_with(op):
    return Project(name="Test", operations=[op])


def ops_of(prog, **kw):
    op = xop(prog, **kw)
    return X.machine_program(op)["ops"]


FRONT = [cmd("Tool", N="B8", D=8), cmd("DrillFront", X=30, Y=20, DP=12, T="B8")]


def test_context_basic_structure():
    op = xop(FRONT + [cmd("MillStart", X=10, Y=10, DP=8, T="M6", D=6), cmd("MillLine", X=100, Y=10)])
    ctx = pp.context_xnc(project_with(op), op)
    assert set(ctx) >= {"project", "op", "xnc", "f", "now"}
    x = ctx["xnc"]
    assert x["code"] == "K1" and x["face"] == "front" and x["turn"] == 0 and x["origin"] == "LT"
    assert x["size"] == {"length": 200, "width": 100} and x["blank"] == {"length": 200, "width": 100, "thickness": 16}
    assert [o["kind"] for o in x["ops"]] == ["drill", "mill_start", "mill_line"]
    assert [o["n"] for o in x["ops"]] == [1, 2, 3]
    d = x["ops"][0]
    assert (d["face"], d["x"], d["y"], d["d"], d["depth"], d["tool"], d["through"]) == ("front", 30, 20, 8, 12, "B8", False)
    assert x["tools"][0]["name"] == "B8" and x["tools"][0]["d"] == 8 and "drill" in x["tools"][0]["uses"]
    assert x["stats"]["drills"] == 1 and x["stats"]["mill_m"] == 0.09 and x["errors"] == 0
    json.dumps(ctx["xnc"])                                              # JSON-ga mos (NaN yo'q)


def test_rotation_mirror_origin_applied_to_coordinates():
    drill = [cmd("DrillFront", X=30, Y=20, DP=12, D=8)]
    f = lambda **kw: (lambda o: (o["x"], o["y"]))(ops_of(drill, **kw)[0])        # noqa: E731
    assert f() == (30, 20)
    assert f(rotation=90) == (80, 30)                                    # (dy − y, x)
    assert f(rotation=180) == (170, 80)
    assert f(rotation=270) == (20, 170)
    assert f(mirror_x=True) == (170, 20) and f(mirror_y=True) == (30, 80)
    assert f(origin="RT") == (170, 20) and f(origin="LB") == (30, 80) and f(origin="RB") == (170, 80)
    # koordinata boshi buyrug'i
    o = ops_of([cmd("Origin", X=10, Y=5)] + drill)[0]
    assert (o["x"], o["y"]) == (40, 25)
    # burilgan detal o'lchami
    assert X.machine_program(xop(drill, rotation=90))["size"] == {"length": 100, "width": 200}
    assert X.machine_program(xop(drill, rotation=90))["blank"]["length"] == 200


def test_edge_drills_side_and_position_after_transform():
    prog = [cmd("DrillLeft", Y=30, Z=8, DP=25, D=8), cmd("DrillTop", X=50, Z=8, DP=25, D=8)]
    o0 = ops_of(prog)
    assert [(o["face"], o["x"], o["y"]) for o in o0] == [("left", 0, 30), ("top", 50, 0)]
    o90 = ops_of(prog, rotation=90)                                      # chap → yuqori, yuqori → o'ng
    assert [(o["face"], o["x"], o["y"]) for o in o90] == [("top", 70, 0), ("right", 100, 50)]
    o180 = ops_of(prog, rotation=180)
    assert [(o["face"], o["x"], o["y"]) for o in o180] == [("right", 200, 70), ("bottom", 150, 100)]
    o270 = ops_of(prog, rotation=270)
    assert [(o["face"], o["x"], o["y"]) for o in o270] == [("bottom", 30, 200), ("left", 0, 150)]
    # ko'zgu: chap ↔ o'ng
    om = ops_of(prog, mirror_x=True)
    assert om[0]["face"] == "right" and (om[0]["x"], om[0]["y"]) == (200, 30)
    omy = ops_of(prog, mirror_y=True)                                    # yuqori ↔ pastki; Y koordinata aks etadi
    assert [(o["face"], o["x"], o["y"]) for o in omy] == [("left", 0, 70), ("bottom", 50, 100)]
    assert om[0]["middle"] is False and om[0]["z"] == 8


def test_arc_direction_flips_with_mirror():
    prog = [cmd("MillStart", X=0, Y=0, DP=8, T="M", D=6), cmd("MillArcCenter", X=20, Y=20, CX=0, CY=20, DIR="true")]
    a = ops_of(prog)[1]
    assert a["kind"] == "mill_arc" and a["radius"] == pytest.approx(20) and a["angle"] == pytest.approx(90)
    assert (a["cx"], a["cy"]) == (0, 20)
    flipped = ops_of(prog, mirror_x=True)[1]
    assert flipped["clockwise"] != a["clockwise"] and (flipped["cx"], flipped["cy"]) == (200, 20)
    both = ops_of(prog, mirror_x=True, mirror_y=True)[1]
    assert both["clockwise"] == a["clockwise"]                          # ikki akslantirish — yo'nalish saqlanadi
    rot = ops_of(prog, rotation=90)[1]
    assert rot["clockwise"] == a["clockwise"] and rot["radius"] == pytest.approx(20)


def test_fillet_pocket_rect_ellipse_groove_in_context():
    prog = [cmd("MillStart", X=0, Y=0, DP=8, T="M", D=6, C=3, SDP=4, SXY=3, IN=1, OUT=0), cmd("MillLine", X=50, Y=0),
            cmd("MillFillet", R=5), cmd("MillLine", X=50, Y=50),
            cmd("MillRect", X=100, Y=50, L=40, W=20, R=4, T="M", DP=3),
            cmd("MillEllipse", X=150, Y=50, RL=15, RW=8),
            cmd("Groove", X1=0, Y1=90, X2=200, Y2=90, DP=8, W=4)]
    ops = ops_of(prog)
    assert [o["kind"] for o in ops] == ["mill_start", "mill_line", "mill_arc", "mill_line", "rect", "ellipse", "groove"]
    s = ops[0]
    assert (s["pocket"], s["correction"], s["step_depth"], s["step_xy"], s["entry"], s["exit"]) == (True, 3, 4, 3, 1, 0)
    assert ops[2]["fillet"] is True and ops[2]["radius"] == pytest.approx(5, abs=1e-4)
    r = ops[4]
    assert (r["x"], r["y"], r["length"], r["width"], r["radius"], r["depth"]) == (100, 50, 40, 20, 4, 3)
    assert [p["type"] for p in r["path"]].count("arc") == 4 and r["path"][0]["type"] == "move"
    assert ops[5]["rl"] == 15 and ops[5]["path"][0] == ops[5]["path"][-1] and len(ops[5]["path"]) > 36
    g = ops[6]
    assert (g["x1"], g["y1"], g["x2"], g["y2"], g["width"], g["passes"]) == (0, 90, 200, 90, 4, 1)


def test_par_values_and_warnings_in_context():
    prog = [cmd("Par", name="a", value=10, label="A"), cmd("DrillFront", X="a", Y=5, DP=12, D=8), cmd("Err", text="diqqat")]
    op = xop(prog)
    op.xnc.par_values = {"a": 77}
    x = pp.context_xnc(project_with(op), op)["xnc"]
    assert x["ops"][0]["x"] == 77 and x["params"] == [{"name": "a", "label": "A", "type": "double", "value": 77.0}]
    assert x["errors"] == 1 and "diqqat" in x["warnings"][0]


def test_long_side_restriction():
    prog = [cmd("DrillFront", X=30, Y=20, DP=12, D=8)]
    op = xop(prog, length=200, width=100)
    ctx = pp.context_xnc(project_with(op), op, "vertical")["xnc"]          # uzun tomon vertikal bo'lsin: 90° qo'shimcha burish
    assert ctx["turn"] == 90 and ctx["size"] == {"length": 100, "width": 200} and ctx["extra_turn"] == 90
    assert (ctx["ops"][0]["x"], ctx["ops"][0]["y"]) == (80, 30)
    assert pp.context_xnc(project_with(op), op, "horizontal")["xnc"]["turn"] == 0           # allaqachon gorizontal
    assert pp.context_xnc(project_with(op), op, "any")["xnc"]["turn"] == 0
    # burilgan (90°) detal: uzun tomon allaqachon vertikal
    op90 = xop(prog, length=200, width=100, rotation=90)
    assert pp.context_xnc(project_with(op90), op90, "vertical")["xnc"]["turn"] == 90
    assert pp.context_xnc(project_with(op90), op90, "horizontal")["xnc"]["turn"] == 180
    # kvadrat — o'zgarmaydi
    sq = xop(prog, length=100, width=100)
    assert pp.context_xnc(project_with(sq), sq, "vertical")["xnc"]["turn"] == 0
    assert X.long_side_turn(200, 100, "vertical") == 90 and X.long_side_turn(200, 100, "zzz") == 0


# ───────────────────────── API ─────────────────────────
def _xnc_op(client, kravat, prog):
    pid, cs, ptid, xid = _xnc_for(client, kravat)               # detal 480×800, kromka: top/bottom
    _set_prog(client, pid, xid, prog)
    return pid, cs, ptid, xid


def test_postprocess_endpoint_json_for_xnc_operation(client, kravat):
    pid, cs, ptid, xid = _xnc_op(client, kravat, [dict(cmd="DrillFront", params=dict(X=30, Y=20, DP=12, D=8), comment="", children=[]),
                                                    dict(cmd="DrillLeft", params=dict(Y=100, DP=25, D=8), comment="", children=[])])
    r = client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "json"})
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"] and ".json" in r.headers["content-disposition"]
    d = json.loads(r.content)
    x = d["xnc"]
    assert x["size"] == {"length": 480, "width": 800} and x["part"]["name"] == "Panel6" and x["part"]["length"] == 480
    assert set(x["edges"]) == {"top", "bottom"} and x["edges"]["top"]["symbol"] and x["edges"]["top"]["name"] == "PVC 1-19"
    assert set(x["edges_final"]) == {"top", "bottom"}
    assert [o["kind"] for o in x["ops"]] == ["drill", "drill"] and x["ops"][1]["face"] == "left"
    # burish: kromkalar ham aylanadi (yuqori/past → o'ng/chap)
    client.patch(f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"rotation": 90}})
    x = json.loads(client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "json"}).content)["xnc"]
    assert set(x["edges_final"]) == {"right", "left"} and x["size"] == {"length": 800, "width": 480}
    assert x["ops"][0]["x"] == 780 and x["ops"][0]["y"] == 30
    # uzun tomon
    x = json.loads(client.get(f"/api/projects/{pid}/operations/{xid}/postprocess",
                              params={"key": "json", "long_side": "vertical"}).content)["xnc"]
    assert x["turn"] == 180 and x["extra_turn"] == 90          # 90° da uzun tomon gorizontal — vertikal talab: yana 90°
    assert client.get(f"/api/projects/{pid}/operations/{xid}/postprocess",
                      params={"key": "json", "long_side": "zz"}).status_code == 400
    # kerakli kalit yo'q / noto'g'ri
    assert client.get(f"/api/projects/{pid}/operations/{xid}/postprocess").status_code == 400
    assert client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "csv"}).status_code == 400
    # CS operatsiyasi uchun avvalgi xatti-harakat: kroy natijasi kerak
    assert client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"key": "json"}).status_code == 400


def test_postprocess_endpoint_template_and_machine(client, kravat):
    pid, cs, ptid, xid = _xnc_op(client, kravat, [dict(cmd="DrillFront", params=dict(X=30, Y=20, DP=12, D=8), comment="", children=[]),
                                                    dict(cmd="DrillFront", params=dict(X=60, Y=20, D=8), comment="", children=[])])
    tpl =("PROG {{ xnc.code }} {{ f(xnc.size.length) }}x{{ f(xnc.size.width) }}\n"
           "{% for o in xnc.ops %}{{ o.n }} {{ o.kind }} X{{ f(o.x) }} Y{{ f(o.y) }} D{{ f(o.d) }}\n{% endfor %}END\n")
    prof = client.post("/api/settings/postprocessor", json={"name": "W1 xnc", "data": PostprocessorProfile(
        name="W1 xnc", extension="nc", newline="lf", template=tpl).model_dump()}).json()
    r = client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"profile_id": prof["id"]})
    assert r.status_code == 200, r.text
    assert ".nc" in r.headers["content-disposition"]
    text = r.content.decode("utf-8")
    assert text.startswith("PROG ") and "480x800" in text and "1 drill X30 Y20 D8" in text and "2 drill X60 Y20 D8" in text
    # shablon xatosi — 400 (500 emas)
    bad = client.post("/api/settings/postprocessor", json={"name": "W1 xnc bad", "data": PostprocessorProfile(
        name="bad", extension="txt", template="{{ xnc.nope.deeper }}").model_dump()}).json()
    assert client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"profile_id": bad["id"]}).status_code == 400
    # stanok: o'rnatilgan formati yo'q ishlov markazi — faqat yoqilgan va shablon biriktirilgan bo'lsa (v2.5)
    assert client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "machine:mw310"}).status_code == 400
    # o'rnatilgan format (woodwop, namunalardan) — shablonsiz ham ishlaydi
    r0 = client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "machine:woodwop"})
    assert r0.status_code == 200 and ".mpr" in r0.headers["content-disposition"] and b"GibLab" not in r0.content
    client.put("/api/postprocessors/machines", json={"enabled": {"woodwop": True, "scm_wincut": True},
                                                      "profile": {"woodwop": prof["id"], "scm_wincut": prof["id"]}, "prefix": True})
    r = client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "machine:woodwop"})
    assert r.status_code == 200 and "WoodWop" in r.headers["content-disposition"]
    assert client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "machine:scm_wincut"}).status_code == 400   # pil markazi
    assert client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "machine:zzz"}).status_code == 400
    lst = client.get("/api/xnc/postprocessors").json()
    keys = {i["key"] for i in lst}
    assert "json" in keys and f"pp:{prof['id']}" in keys and "machine:woodwop" in keys and "machine:scm_wincut" not in keys
    assert next(i for i in lst if i["key"] == "machine:woodwop")["available"] is True
    # tozalash
    client.put("/api/postprocessors/machines", json={"enabled": {}, "profile": {}, "prefix": False})
    for pr in (prof, bad):
        client.delete(f"/api/settings/postprocessor/{pr['id']}")


def test_cs_postprocessor_list_unchanged_by_xnc(client):
    keys = {i["key"] for i in client.get("/api/postprocessors").json()}
    assert {"csv", "commands", "dxf", "json"} <= keys and "machine:woodwop" not in keys
