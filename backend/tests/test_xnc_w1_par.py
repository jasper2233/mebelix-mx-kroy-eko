"""W1 · Par kiritish oynasi: parametr sxemasi (tur, yorliq, ko'rinish sharti, faqat o'qish), operatsiyada saqlanadigan
qiymatlar (`XNCParams.par_values`), hisobda Par qiymatining o'zgaruvchiga aylanishi, eski JSON mosligi."""
import pytest

from app.models import Operation, OpType, XNCParams, XncCommand as C
from app.services.xnc import evaluate, program_stats, xnc_drawing_svg, xnc_holes_table, xnc_stats

from test_qa_fix_calc import _op, _set_prog, _xnc_for


def Par(**p):
    return C(cmd="Par", params=p)


def drill(x, y, **kw):
    return C(cmd="DrillFront", params={"X": x, "Y": y, "DP": 12, "D": 8, **kw})


def pos(prog, pars=None, dx=800, dy=600, dz=16):
    return [(o["X"], o["Y"]) for o in evaluate(prog, dx, dy, dz, None, pars) if o["kind"].startswith("Drill")]


def test_par_default_and_override():
    prog = [Par(name="a", value=100, label="A"), drill("a", "a/2")]
    assert pos(prog) == [(100, 50)]                                   # qiymat kiritilmagan — standart
    assert pos(prog, {"a": 240}) == [(240, 120)]                      # kiritilgan qiymat
    assert pos(prog, {"a": "dx/4"}) == [(200, 100)]                   # ifoda ham mumkin
    assert pos(prog, {"a": ""}) == [(100, 50)]                        # bo'sh — standart
    assert pos(prog, {"other": 5}) == [(100, 50)]                     # begona nom — e'tiborsiz
    # standart ifoda detal o'lchamiga bog'liq
    prog = [Par(name="cx", value="dx/2"), drill("cx", 10)]
    assert pos(prog, dx=600) == [(300, 10)] and pos(prog, {"cx": 111}, dx=600) == [(111, 10)]


def test_par_types_integer_boolean():
    ops = evaluate([Par(name="n", value=3.7, type="integer"), Par(name="b", value=5, type="boolean"),
                    Par(name="z", value=2.5, type="double")], 800, 600, 16, None, {"n": 9.9})
    pr = {p["name"]: p for p in ops.params}
    assert (pr["n"]["type"], pr["n"]["value"], pr["n"]["default"]) == ("integer", 9.0, 3.0)    # kasr tashlanadi
    assert (pr["b"]["type"], pr["b"]["value"]) == ("boolean", 1.0)                              # 0 dan boshqa — 1
    assert pr["z"]["type"] == "double" and pr["z"]["value"] == 2.5
    ops = evaluate([Par(name="b", value=1, type="boolean")], 800, 600, 16, None, {"b": 0})
    assert ops.params[0]["value"] == 0.0
    # noma'lum tur — double
    ops = evaluate([Par(name="q", value=1.5, type="zzz")], 800, 600, 16)
    assert ops.params[0]["type"] == "double" and ops.params[0]["value"] == 1.5
    # mantiqiy Par shartda
    prog = [Par(name="on", value=0, type="boolean"), C(cmd="If", params={"cond": "on"}, children=[drill(1, 1)])]
    assert pos(prog) == [] and pos(prog, {"on": 1}) == [(1, 1)]


def test_par_visible_and_readonly_expressions():
    prog = [Par(name="use", value=0, type="boolean", label="U"),
            Par(name="gap", value=10, label="G", visible="use"),
            Par(name="calc", value="gap*2", label="C", readonly="true"),
            Par(name="lock", value=7, readonly="use=0")]
    ops = evaluate(prog, 800, 600, 16, None, {"calc": 999, "lock": 123})
    pr = {p["name"]: p for p in ops.params}
    assert pr["gap"]["visible"] is False and pr["use"]["visible"] is True
    assert pr["calc"]["readonly"] is True and pr["calc"]["value"] == 20.0                  # faqat o'qish — kiritilgani e'tiborsiz
    assert pr["lock"]["readonly"] is True and pr["lock"]["value"] == 7.0
    ops = evaluate(prog, 800, 600, 16, None, {"use": 1, "gap": 30, "lock": 123})
    pr = {p["name"]: p for p in ops.params}
    assert pr["gap"]["visible"] is True and pr["gap"]["value"] == 30.0
    assert pr["lock"]["readonly"] is False and pr["lock"]["value"] == 123.0                # ifoda o'zgardi — endi tahrirlanadi
    assert pr["calc"]["value"] == 60.0


def test_par_label_suffix_and_order_and_disabled():
    prog = [Par(name="a", value=1, label="Birinchi", suffix="mm"), C(cmd="Par", params={"name": "off", "value": 5}, enabled=False),
            C(cmd="If", params={"cond": "0"}, children=[Par(name="hidden", value=1)]),
            C(cmd="If", params={"cond": "1"}, children=[Par(name="inner", value=2)]), Par(name="b", value=3)]
    ops = evaluate(prog, 800, 600, 16)
    assert [p["name"] for p in ops.params] == ["a", "inner", "b"]       # o'chirilgan va bajarilmagan blok Par lari yo'q
    assert ops.params[0]["label"] == "Birinchi" and ops.params[0]["suffix"] == "mm"
    # sikldagi takror Par — API da bitta yozuv
    from app.services.xnc import unique_params
    lp = [C(cmd="Var", params={"name": "i", "value": 0}),
          C(cmd="While", params={"cond": "i<3"}, children=[Par(name="p", value=1), C(cmd="Set", params={"name": "i", "value": "i+1"})])]
    ops = evaluate(lp, 800, 600, 16)
    assert len(ops.params) == 3 and len(unique_params(ops.params)) == 1


def test_par_invalid_expressions_do_not_break():
    ops = evaluate([Par(name="bad", value="1/0"), Par(name="ok", value=2), drill("ok", 5)], 800, 600, 16)
    assert ops.problems >= 1 and [o["X"] for o in ops if o["kind"] == "DrillFront"] == [2]
    prog = [Par(name="a", value=10), drill("a", 5)]
    ops = evaluate(prog, 800, 600, 16, None, {"a": "1/0"})              # noto'g'ri kiritilgan qiymat — standartga qaytadi + xabar
    assert ops.problems == 1 and [o["X"] for o in ops if o["kind"] == "DrillFront"] == [10]
    ops = evaluate(prog, 800, 600, 16, None, {"a": 1e12})
    assert [o["X"] for o in ops if o["kind"] == "DrillFront"] == [10]
    # visible / readonly noto'g'ri ifoda — xabar, standart (ko'rinadi, tahrirlanadi)
    ops = evaluate([Par(name="a", value=1, visible="nope+", readonly="zzz")], 800, 600, 16)
    assert ops.problems == 2 and ops.params[0]["visible"] is True and ops.params[0]["readonly"] is False
    # Par nomsiz — e'tiborsiz
    assert evaluate([Par(value=1)], 800, 600, 16).params == []
    # Par soni chegarasi
    from app.services.xnc import MAX_PARS
    many = [Par(name=f"p{i}", value=i) for i in range(MAX_PARS + 5)]
    assert len(evaluate(many, 800, 600, 16).params) == MAX_PARS


def test_par_values_used_by_stats_drawing_and_holes_table():
    prog = [Par(name="cx", value=100), drill("cx", 50), C(cmd="DrillFront", params={"AC": 3, "AS": 32, "X": "cx"})]
    x = XNCParams(length=800, width=600, thickness=16, program=prog, by_part_size=False, par_values={"cx": 250})
    assert xnc_stats(x)["drills"] == 4
    op = Operation(type=OpType.XNC, xnc=x)
    assert 'cx="250"' in xnc_drawing_svg(op)
    assert xnc_holes_table(op)[0][1] == "250"
    # par_values bo'sh (eski JSON) — standart
    x0 = XNCParams.model_validate({"length": 800, "width": 600, "program": [p.model_dump() for p in prog]})
    assert x0.par_values == {} and 'cx="100"' in xnc_drawing_svg(Operation(type=OpType.XNC, xnc=x0))
    # statistika Par holatini ham qaytaradi
    st = program_stats(prog, 800, 600, 16, None, {"cx": 7})
    assert st["params"][0]["value"] == 7.0 and st["params"][0]["default"] == 100.0


def test_par_values_validation_limits():
    with pytest.raises(ValueError):
        XNCParams(par_values={f"k{i}": 1 for i in range(201)})
    with pytest.raises(ValueError):
        XNCParams(par_values={"a": "x" * 201})
    assert XNCParams(par_values={"a": "dx/2", "b": 3}).par_values == {"a": "dx/2", "b": 3}


# ───────────────────────── API ─────────────────────────
def test_par_api_and_persistence(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)                      # detal 480×800
    prog = [{"cmd": "Par", "params": {"name": "cx", "value": "dx/2", "label": "Markaz X", "type": "double", "suffix": "mm"},
             "comment": "", "children": []},
            {"cmd": "Par", "params": {"name": "tw", "value": 0, "type": "boolean", "label": "Qo'shimcha"}, "comment": "", "children": []},
            {"cmd": "Par", "params": {"name": "gp", "value": 10, "visible": "tw", "label": "Oraliq"}, "comment": "", "children": []},
            {"cmd": "DrillFront", "params": {"X": "cx", "Y": "gp", "DP": 12, "D": 8}, "comment": "", "children": []}]
    _set_prog(client, pid, xid, prog)
    r = client.get(f"/api/projects/{pid}/operations/{xid}/xnc-params")
    assert r.status_code == 200
    pr = {p["name"]: p for p in r.json()["params"]}
    assert pr["cx"]["value"] == 240 and pr["cx"]["label"] == "Markaz X" and pr["cx"]["suffix"] == "mm"
    assert pr["gp"]["visible"] is False and pr["tw"]["type"] == "boolean"
    # qiymat kiritish -> saqlanadi, hisob, chizma va statistika yangilanadi
    r = client.patch(f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"par_values": {"cx": 100, "tw": 1}}})
    assert r.status_code == 200 and _op(r.json(), xid)["xnc"]["par_values"] == {"cx": 100, "tw": 1}
    pr = {p["name"]: p for p in client.get(f"/api/projects/{pid}/operations/{xid}/xnc-params").json()["params"]}
    assert pr["cx"]["value"] == 100 and pr["gp"]["visible"] is True
    assert 'cx="100" cy="10"' in client.get(f"/api/projects/{pid}/operations/{xid}/xnc.svg").text
    # qayta yuklash (bazadan) — qiymatlar saqlangan; undo — oldingi holat
    assert _op(client.get(f"/api/projects/{pid}").json(), xid)["xnc"]["par_values"] == {"cx": 100, "tw": 1}
    p = client.post(f"/api/projects/{pid}/undo").json()
    assert _op(p, xid)["xnc"]["par_values"] == {}
    # noto'g'ri turlar — 422; XNC bo'lmagan operatsiya — 400
    assert client.patch(f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"par_values": {"a": [1]}}}).status_code == 422
    assert client.get(f"/api/projects/{pid}/operations/{cs}/xnc-params").status_code == 400
    assert client.get(f"/api/projects/{pid}/operations/nope/xnc-params").status_code in (400, 404)


def test_old_json_without_par_values_opens(client, kravat):
    """Eski saqlangan loyiha (par_values yo'q) ochiladi va Par lar standart qiymat bilan ishlaydi."""
    from app.db import ProjectRow, SessionLocal
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    _set_prog(client, pid, xid, [{"cmd": "Par", "params": {"name": "a", "value": 33}, "comment": "", "children": []},
                                 {"cmd": "DrillFront", "params": {"X": "a", "Y": 5, "DP": 12, "D": 8}, "comment": "", "children": []}])
    with SessionLocal() as s:
        row = s.get(ProjectRow, pid)
        import copy
        data = copy.deepcopy(row.data)
        for o in data["operations"]:
            if o["id"] == xid:
                o["xnc"].pop("par_values", None)
        row.data = data
        s.commit()
    p = client.get(f"/api/projects/{pid}").json()
    assert _op(p, xid)["xnc"]["par_values"] == {}
    assert client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()["drills"] == 1
