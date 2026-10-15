"""W12 · Mahsulot «Программа» (parametrik mahsulot): «quruq» hisob (Par/Var/Set/If/Else/While/DoWhile/Sub/Call/Ret/Msg/Err),
tsikl chegaralari, `product.<nom>` konteksti (XNC va etiketka), API, `.project` importi, «Пересчитать параметричность»,
eski JSON."""
import json

import pytest

from app.models import PROG_MAX_NODES, Operation, OpType, Part, Product, Project, XncCommand as C
from app.services import calc, label_vars, product_program as pp, xnc


def Par(**p):
    return C(cmd="Par", params=p)


def Var(name, value, **kw):
    return C(cmd="Var", params={"name": name, "value": value, **kw})


def Set(name, value):
    return C(cmd="Set", params={"name": name, "value": value})


def If(cond, *kids):
    return C(cmd="If", params={"cond": cond}, children=list(kids))


def Else(*kids, cond=None):
    return C(cmd="Else", params={"cond": cond} if cond else {}, children=list(kids))


def While(cond, *kids):
    return C(cmd="While", params={"cond": cond}, children=list(kids))


def DoWhile(cond, *kids):
    return C(cmd="DoWhile", params={"cond": cond}, children=list(kids))


def Msg(text):
    return C(cmd="Msg", params={"text": text})


def Err(text):
    return C(cmd="Err", params={"text": text})


def run(prog, pars=None, qty=1, idx=1):
    return pp.run(Product(name="M", qty=qty, program=prog, par_values=pars or {}), idx)


def _api(client, method, url, **kw):
    r = getattr(client, method)(url, **kw)
    assert r.status_code == 200, (url, r.status_code, r.text[:300])
    return r.json()


def _prog_json(prog):
    return [json.loads(c.model_dump_json()) for c in prog]


# ───────────────────────── 1. hisob ─────────────────────────
def test_par_default_override_and_var_expressions():
    prog = [Par(name="eni", value=800, label="Eni"), Par(name="bal", value=2000), Var("yarim", "eni/2"),
            Var("hajm", "eni*bal/1000000")]
    r = run(prog)
    assert r.vars == {"eni": 800, "bal": 2000, "yarim": 400, "hajm": 1.6}
    r = run(prog, {"eni": 1000})
    assert r.vars["eni"] == 1000 and r.vars["yarim"] == 500 and r.vars["hajm"] == 2.0
    assert [(p["name"], p["label"], p["value"], p["default"]) for p in r.params][0] == ("eni", "Eni", 1000.0, 800.0)
    assert run(prog, {"eni": "2000/4"}).vars["eni"] == 500                   # kiritilgan qiymat — ifoda ham bo'lishi mumkin
    r = run(prog, {"eni": "bal/4"})                                          # `bal` hali e'lon qilinmagan — standart + ogohlantirish
    assert r.vars["eni"] == 800 and r.problems == 1
    assert run(prog, {"eni": ""}).vars["eni"] == 800                          # bo'sh — standart


def test_par_types_and_visible_readonly():
    prog = [Par(name="n", value=3.7, type="integer"), Par(name="b", value=5, type="boolean"),
            Par(name="k", value="n*2", readonly="true")]
    r = run(prog, {"n": 9.9, "k": 77})
    assert r.vars["n"] == 9 and r.vars["b"] == 1 and r.vars["k"] == 18       # kasr tashlanadi; faqat o'qish — kiritilgan e'tiborsiz
    p = {x["name"]: x for x in r.params}
    assert p["k"]["readonly"] is True and p["b"]["type"] == "boolean"


def test_if_else_while_dowhile_break_continue():
    prog = [Par(name="n", value=5), Var("s", 0), Var("i", 0),
            While("i<n", Set("i", "i+1"), If("i=3", C(cmd="Continue")), Set("s", "s+i")),          # 1+2+4+5 = 12
            Var("t", 0),
            DoWhile("t<100", Set("t", "t+7"), If("t>20", C(cmd="Break"))),                          # 7, 14, 21 → Break
            If("s>100", Set("big", 1)), Else(Set("big", 0)),
            Var("w", 0), If("n=5", Set("w", 1)), Else(Set("w", 2), cond="n=6"), Else(Set("w", 3))]
    r = run(prog)
    assert (r.vars["s"], r.vars["t"], r.vars["big"], r.vars["w"]) == (12, 21, 0, 1)
    r6 = run(prog, {"n": 6})
    assert r6.vars["w"] == 2                                                                # else-if
    r7 = run(prog, {"n": 7})
    assert r7.vars["w"] == 3                                                                # oxirgi Else


def test_sub_call_ret_and_nested_calls():
    prog = [Par(name="x", value=10), Var("y", 0),
            C(cmd="Sub", params={"name": "ikki"}, children=[Set("y", "y+x"), If("y>15", C(cmd="Ret")), Set("y", "y+1000")]),
            C(cmd="Call", params={"name": "ikki"}), C(cmd="Call", params={"name": "ikki"}),
            C(cmd="Call", params={"name": "yoq"})]
    r = run(prog)
    assert r.vars["y"] == 1010 + 10                                    # birinchi: 10 → 1010; ikkinchi: 1020>15 → Ret
    assert any("«yoq»" in m["text"] for m in r.messages if m["level"] == "warning")


def test_msg_err_levels_paths_and_interpolation():
    prog = [Par(name="eni", value=1500), Par(name="tavsiya", value="eni/3"),
            Msg("Tavsiya: {tavsiya} mm, eni {eni}"),
            If("eni>1200", Err("Eni {eni} mm — 1200 dan oshmasin")),
            Err("Doimiy xato"),
            Msg("{yoq}")]
    r = run(prog)
    by = [(m["level"], m["text"], m["path"]) for m in r.messages]
    assert ("info", "Tavsiya: 500 mm, eni 1500", "3") in by
    assert ("error", "Eni 1500 mm — 1200 dan oshmasin", "4.1") in by
    assert ("error", "Doimiy xato", "5") in by
    assert r.errors == 2
    assert ("info", "{yoq}", "6") in by                                        # xato ifoda o'z holicha qoladi...
    assert any(m["level"] == "warning" and "yoq" in m["text"] for m in r.messages)    # ...va ogohlantirish
    ok = run(prog, {"eni": 1000})
    assert ok.errors == 1 and not any(m["text"].startswith("Eni") for m in ok.messages)


def test_msg_interpolation_switch(monkeypatch):
    monkeypatch.setattr(xnc, "PROG_MSG_INTERPOLATE", False)
    r = run([Par(name="a", value=2), Msg("a={a}")])
    assert r.messages[0]["text"] == "a={a}"


def test_geometry_commands_are_not_executed_and_dx_is_unknown():
    prog = [Var("a", 5), C(cmd="DrillFront", params={"X": 10, "Y": 10}), C(cmd="Tool", params={"N": "B8", "D": 8}),
            Var("b", "dx+1"), Var("c", "a+1")]
    r = run(prog)
    assert r.vars == {"a": 5, "c": 6}                                           # dx yo'q → b e'lon qilinmaydi
    txt = [m["text"] for m in r.messages if m["level"] == "warning"]
    assert any("DrillFront" in t for t in txt) and any("Tool" in t for t in txt) and any("dx" in t for t in txt)
    assert all(not t.startswith("XNC") for t in txt)                            # «Программа 2 (…)», «XNC» emas
    assert r.problems == len(txt) == 3
    assert xnc.evaluate_control(prog).problems == 3                              # xuddi shu natija to'g'ridan-to'g'ri


def test_disabled_command_and_comments_are_skipped():
    r = run([C(cmd="Com", comment="izoh"), C(cmd="Var", params={"name": "a", "value": 1}, enabled=False), Var("b", 2),
             C(cmd="If", params={"cond": "1"}, enabled=False, children=[Err("ko'rinmasin")])])
    assert r.vars == {"b": 2} and r.errors == 0


def test_product_qty_and_index_are_visible_but_not_exported():
    r = run([Var("jami", "product.qty*10+product.index")], qty=4, idx=2)
    assert r.vars == {"jami": 42}                                              # product.qty / product.index chiqmaydi


def test_infinite_loop_and_step_limits():
    r = run([Var("i", 0), While("1", Set("i", "i+1"))])
    assert r.vars["i"] == xnc.MAX_LOOP_ITER                                    # 10 000 iteratsiyada to'xtaydi
    assert any(str(xnc.MAX_LOOP_ITER) in m["text"] for m in r.messages if m["level"] == "warning")
    r = run([Var("i", 0), DoWhile("1", Set("i", "i+1"))])
    assert r.vars["i"] == xnc.MAX_LOOP_ITER
    # ichma-ich tsikllar: jami qadam chegarasi (100 000)
    r = run([Var("i", 0), While("i<100", Set("i", "i+1"), Var("j", 0), While("j<1000", Set("j", "j+1")))])
    assert any("100000" in m["text"] for m in r.messages if m["level"] == "warning")
    # qism dastur rekursiyasi: chaqiruv chuqurligi chegarasi
    r = run([Var("n", 0), C(cmd="Sub", params={"name": "r"}, children=[Set("n", "n+1"), C(cmd="Call", params={"name": "r"})]),
             C(cmd="Call", params={"name": "r"})])
    assert r.vars["n"] == xnc.MAX_CALL_DEPTH
    assert any(str(xnc.MAX_CALL_DEPTH) in m["text"] for m in r.messages if m["level"] == "warning")


def test_deep_recursion_messages_are_capped_and_project_saves(client):
    """Chuqur rekursiyada buyruq yo'li uzun bo'ladi: xabar yo'li 60 belgigacha qisqartiriladi, saqlash 500 bermaydi."""
    prog = [Var("n", 0), C(cmd="Sub", params={"name": "r"}, children=[Set("n", "n+1"), Err("x{n}"),
                                                                        C(cmd="Call", params={"name": "r"})]),
            C(cmd="Call", params={"name": "r"})]
    r = run(prog)
    assert r.errors == xnc.MAX_CALL_DEPTH and all(len(m["path"]) <= 60 for m in r.messages)
    assert max(len(n["n"]) for n in xnc.evaluate_control(prog).notes) > 60          # asl yo'l haqiqatan uzun edi
    p = _api(client, "post", "/api/projects", json={"name": "Rek"})
    pid, prid = p["id"], p["products"][0]["id"]
    p = _api(client, "patch", f"/api/projects/{pid}/products/{prid}", json={"program": _prog_json(prog)})
    pr = p["products"][0]
    assert len(pr["prog_messages"]) == xnc.MAX_CALL_DEPTH + 1 and all(len(m["path"]) <= 60 for m in pr["prog_messages"])


def test_division_by_zero_and_bad_expression_become_warnings():
    r = run([Var("a", "1/0"), Var("b", "2+"), Var("c", 3), If("zzz>1", Var("d", 1))])
    assert r.vars == {"c": 3} and r.problems == 3 and r.errors == 0
    assert [m["level"] for m in r.messages] == ["warning"] * 3


def test_variable_name_rules_reserved_and_invalid():
    r = run([Var("name", 1), Var("qty", 2), Var("my var", 3), Var("ok_1", 4), Var("Eni", 5), Var("2x", 6)])
    assert r.vars == {"ok_1": 4, "Eni": 5}
    assert sum(1 for m in r.messages if m["level"] == "warning") == 4          # name, qty (zahira) + 2 ta yaroqsiz nom


def test_no_program_means_empty_result_and_legacy_warns():
    assert pp.run(Product(name="x")).vars == {} and pp.run(Product(name="x")).messages == []
    r = pp.run(Product(name="x", legacy_program="<program><zz/></program>"))
    assert r.vars == {} and [m["level"] for m in r.messages] == ["warning"]


# ───────────────────────── 2. model, API, eski JSON ─────────────────────────
def test_old_json_product_without_program_loads():
    p = Project.model_validate({"name": "eski", "products": [{"name": "m", "qty": 2, "extra": {"a": "b"}}]})
    pr = p.products[0]
    assert (pr.program, pr.par_values, pr.prog_vars, pr.prog_messages, pr.legacy_program) == ([], {}, {}, [], "")
    calc.recalc_project(p)                                                      # dasturi yo'q mahsulotga tegilmaydi
    assert pr.prog_vars == {} and pr.prog_messages == []


def test_api_program_patch_computes_vars_and_messages(client):
    p = _api(client, "post", "/api/projects", json={"name": "PP"})
    pid, prid = p["id"], p["products"][0]["id"]
    prog = _prog_json([Par(name="eni", value=900, label="Eni", suffix="mm"), Var("yarim", "eni/2"),
                       If("eni>1000", Err("Eni {eni} > 1000")), Msg("yarim={yarim}")])
    p = _api(client, "patch", f"/api/projects/{pid}/products/{prid}", json={"program": prog})
    pr = p["products"][0]
    assert pr["prog_vars"] == {"eni": 900, "yarim": 450}
    assert [(m["level"], m["text"]) for m in pr["prog_messages"]] == [("info", "yarim=450")]
    p = _api(client, "patch", f"/api/projects/{pid}/products/{prid}", json={"par_values": {"eni": 1200}})
    pr = p["products"][0]
    assert pr["par_values"] == {"eni": 1200} and pr["prog_vars"]["yarim"] == 600
    assert [(m["level"], m["text"], m["path"]) for m in pr["prog_messages"]] == [("error", "Eni 1200 > 1000", "3.1"),
                                                                                 ("info", "yarim=600", "4")]
    st = _api(client, "get", f"/api/projects/{pid}/products/{prid}/program-state")
    assert st["errors"] == 1 and st["vars"]["eni"] == 1200
    assert st["params"][0]["name"] == "eni" and st["params"][0]["suffix"] == "mm" and st["params"][0]["default"] == 900
    assert client.get(f"/api/projects/{pid}/products/yoq/program-state").status_code == 404
    # saqlangan va qayta yuklangan loyihada ham bor
    again = _api(client, "get", f"/api/projects/{pid}")["products"][0]
    assert again["prog_vars"] == pr["prog_vars"] and len(again["prog_messages"]) == 2
    # dastur olib tashlansa — natija ham tozalanadi
    p = _api(client, "patch", f"/api/projects/{pid}/products/{prid}", json={"program": []})
    assert p["products"][0]["prog_vars"] == {} and p["products"][0]["prog_messages"] == []


def test_api_limits_422(client):
    p = _api(client, "post", "/api/projects", json={"name": "PP2"})
    pid, prid = p["id"], p["products"][0]["id"]
    big = [{"cmd": "Com", "params": {}, "comment": "", "enabled": True, "children": []}] * (PROG_MAX_NODES + 1)
    assert client.patch(f"/api/projects/{pid}/products/{prid}", json={"program": big}).status_code == 422
    assert client.patch(f"/api/projects/{pid}/products/{prid}", json={"par_values": {"a" * 101: 1}}).status_code == 422
    assert client.patch(f"/api/projects/{pid}/products/{prid}", json={"par_values": {"a": [1]}}).status_code == 422
    r = client.patch(f"/api/projects/{pid}/products/{prid}", json={"program": [{"cmd": "Com", "params": {}}] * 5})
    assert r.status_code == 200
    assert client.patch(f"/api/projects/{pid}/products/{prid}", json={"program": [{"cmd": "DrillFront", "params": {"X": 1}}]}).status_code == 200


def test_clone_product_keeps_program(client):
    p = _api(client, "post", "/api/projects", json={"name": "PP3"})
    pid, prid = p["id"], p["products"][0]["id"]
    _api(client, "patch", f"/api/projects/{pid}/products/{prid}",
         json={"program": _prog_json([Par(name="a", value=3)]), "par_values": {"a": 7}})
    p = _api(client, "post", f"/api/projects/{pid}/products/{prid}/clone")
    a, b = p["products"][0], p["products"][1]
    assert b["id"] != a["id"] and b["program"] == a["program"] and b["par_values"] == {"a": 7} and b["prog_vars"] == {"a": 7}


def test_header_severity_summary():
    pr = Product(name="m", program=[Err("x"), Var("a", "1/0"), Msg("i")])
    project = Project(name="t", products=[pr, Product(name="n")])
    calc.recalc_project(project)
    assert pp.severity(project) == dict(errors=1, warnings=1, products=1)


# ───────────────────────── 3. product.<nom> konteksti ─────────────────────────
def _xnc_project(client, prog, par_values=None, xnc_prog=None):
    """Loyiha: mahsulot (dasturli) + CS + detal + shu detalga bog'langan XNC. Qaytaradi (pid, prid, xnc_id)."""
    p = _api(client, "post", "/api/projects", json={"name": "Ctx"})
    pid, prid = p["id"], p["products"][0]["id"]
    _api(client, "patch", f"/api/projects/{pid}/products/{prid}",
         json={"program": _prog_json(prog), "par_values": par_values or {}})
    p = _api(client, "post", f"/api/projects/{pid}/operations", json={"type": "CS", "name": "LDSP"})
    cs = p["operations"][-1]["id"]
    p = _api(client, "post", f"/api/projects/{pid}/operations/{cs}/parts",
             json=[dict(name="Yon", length=700, width=500, qty=1, product_id=prid)])
    ptid = next(o for o in p["operations"] if o["id"] == cs)["parts"][0]["id"]
    p = _api(client, "post", f"/api/projects/{pid}/operations/{cs}/parts/{ptid}/xnc")
    xid = p["operations"][-1]["id"]
    if xnc_prog is not None:
        _api(client, "patch", f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"program": _prog_json(xnc_prog)}})
    return pid, prid, xid


def test_product_vars_in_xnc_part_vars_and_expressions(client):
    drill = C(cmd="DrillFront", params={"X": "product.teshik_x", "Y": "product.teshik_x/2", "DP": 12, "D": 8})
    pid, prid, xid = _xnc_project(client, [Par(name="teshik_x", value=100), Var("bosh", "teshik_x*2")], xnc_prog=[drill])
    p = _api(client, "get", f"/api/projects/{pid}")
    x = next(o for o in p["operations"] if o["id"] == xid)["xnc"]
    assert x["part_vars"]["product.teshik_x"] == 100 and x["part_vars"]["product.bosh"] == 200
    st = _api(client, "get", f"/api/projects/{pid}/operations/{xid}/xnc-stats")
    assert st["drills"] == 1 and st["errors"] in (0, None)
    # mahsulot parametri o'zgarsa — XNC konteksti va hisob yangilanadi
    p = _api(client, "patch", f"/api/projects/{pid}/products/{prid}", json={"par_values": {"teshik_x": 9999}})
    x = next(o for o in p["operations"] if o["id"] == xid)["xnc"]
    assert x["part_vars"]["product.teshik_x"] == 9999
    st = _api(client, "get", f"/api/projects/{pid}/operations/{xid}/xnc-stats")
    assert st["drills"] == 0 and (st["errors"] or 0) == 0                     # X=9999 detaldan tashqarida — teshik bajarilmaydi
    # mahsulot dasturi o'chirilsa — o'zgaruvchi yo'q: «noma'lum o'zgaruvchi» xatosi (jim 0 emas)
    p = _api(client, "patch", f"/api/projects/{pid}/products/{prid}", json={"program": []})
    x = next(o for o in p["operations"] if o["id"] == xid)["xnc"]
    assert "product.teshik_x" not in x["part_vars"]
    st = _api(client, "get", f"/api/projects/{pid}/operations/{xid}/xnc-stats")
    assert st["errors"] >= 1


def test_xnc_without_product_program_unchanged(client):
    pid, prid, xid = _xnc_project(client, [])
    x = next(o for o in _api(client, "get", f"/api/projects/{pid}")["operations"] if o["id"] == xid)["xnc"]
    assert not any(k.startswith("product.") for k in x["part_vars"])


def test_label_env_has_product_vars_and_existing_names_win():
    prod = Product(name="Shkaf", code="SH-1", qty=2,
                   program=[Par(name="h", value=2100), Var("name", 5), Var("kod", "h/100")])
    other = Product(name="Stol", program=[Var("h", 750)])
    plain = Product(name="Tumba")
    pt = Part(uid=1, length=500, width=300, product_id=prod.id)
    pt2 = Part(uid=2, length=500, width=300, product_id=plain.id)
    cs = Operation(type=OpType.CS, name="LDSP", parts=[pt, pt2])
    project = calc.recalc_project(Project(name="t", operations=[cs], products=[prod, other, plain]))
    eb = label_vars.EnvBuilder(project, label_vars.LBParams(), total=1)
    e = eb.env(label_vars.Item("part", op=cs, part=pt, part_index=1, copy=1, copies=1))
    assert e["product.h"] == 2100 and e["product.kod"] == 21
    assert e["product.name"] == "Shkaf"                                        # mavjud ustun: dastur o'zgaruvchisi bosmaydi
    from app.services import expr
    assert expr.evaluate("product.h/100", e) == 21
    e2 = eb.env(label_vars.Item("part", op=cs, part=pt2, part_index=2, copy=1, copies=1))
    assert e2["product.h"] == 0 and e2["product.kod"] == 0                     # dasturi yo'q mahsulot — standart 0 (xato emas)
    e3 = eb.env(label_vars.Item("product", product=other, product_index=2, copy=1, copies=1))
    assert e3["product.h"] == 750
    assert {"index", "name", "code", "qty", "count", "description", "phone1", "phone2", "date", "order"} \
        == pp.RESERVED_NAMES == {n.split(".", 1)[1] for n in label_vars.VAR_NAMES
                                 if n.startswith("product.") and n.split(".", 1)[1] in pp.RESERVED_NAMES}


# ───────────────────────── 4. .project importi ─────────────────────────
def _xml(program, extra=""):
    esc = program.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project name="PP import" version="1">
 <good id="1" typeId="product" name="Shkaf" count="2" program="{esc}"><part id="11" dl="1000" dw="500" l="1000" w="500" count="1" name="Yon"/></good>
 <good id="2" typeId="sheet" code="L16" name="LDSP" l="2750" w="1830" t="16" count="10"/>
 <good id="3" typeId="tool.cutting" name="Arra"/>
 <operation id="1" typeId="CS" tool1="3" cSizeMode="1"><material id="2"/><part id="11"/></operation>
</project>""".encode("utf-8")


def test_import_product_program_xml():
    from app.plugins.legacy_project import import_project
    prog = ('<program>'
            '<par name="eni" value="800" label="Eni" type="double" suffix="mm"/>'
            '<var name="yarim" expr="eni/2" comment="yarmi"/>'
            '<if cond="eni&gt;1000"><err text="Eni oshdi"/></if><else><msg text="ok"/></else>'
            '<while expr="yarim&lt;10"><set name="yarim" value="yarim+1"/><brk/></while>'
            '<sub name="s"><ret/></sub><call name="s"/>'
            '</program>')
    p, warnings = import_project(_xml(prog), "pp.project")
    pr = p.products[0]
    assert pr.legacy_program == "" and not [w for w in warnings if "program" in w.lower() or "программ" in w.lower()]
    cmds = [c.cmd for c in pr.program]
    assert cmds == ["Par", "Var", "If", "Else", "While", "Sub", "Call"]
    par = pr.program[0].params
    assert par == {"name": "eni", "value": 800.0, "label": "Eni", "type": "double", "suffix": "mm"}
    assert pr.program[1].params == {"name": "yarim", "value": "eni/2"} and pr.program[1].comment == "yarmi"
    assert pr.program[2].params == {"cond": "eni>1000"} and pr.program[2].children[0].cmd == "Err"
    assert pr.program[4].params == {"cond": "yarim<10"} and [c.cmd for c in pr.program[4].children] == ["Set", "Break"]
    calc.recalc_project(p)
    assert pr.prog_vars["eni"] == 800 and pr.prog_vars["yarim"] == 400
    assert [m.level for m in pr.prog_messages] == ["info"] and pr.prog_messages[0].text == "ok"


def test_import_unknown_tag_warns_and_keeps_source():
    from app.plugins.legacy_project import import_project
    prog = '<program><par name="a" value="1"/><geom x="1"/><bf x="10" y="10"/></program>'
    p, warnings = import_project(_xml(prog), "pp2.project")
    pr = p.products[0]
    assert [c.cmd for c in pr.program] == ["Par"]                              # tushunilgani olinadi
    assert pr.legacy_program == prog                                           # asl matn yo'qolmaydi
    tags = [w for w in warnings if "<geom>" in w or "<bf>" in w]
    assert len(tags) == 2
    calc.recalc_project(p)
    assert pr.prog_vars == {"a": 1} and [m.level for m in pr.prog_messages] == ["warning"]    # «qisman tanildi» ogohlantirishi


def test_import_broken_xml_is_reported_not_dropped():
    from app.plugins.legacy_project import import_project
    p, warnings = import_project(_xml("<program><par name='a'"), "pp3.project")
    pr = p.products[0]
    assert pr.program == [] and pr.legacy_program.startswith("<program><par")
    assert any("Shkaf" in w for w in warnings)


def test_import_without_program_attribute_is_unchanged():
    from app.plugins.legacy_project import import_project
    data = _xml("").replace(b' program=""', b"")
    p, warnings = import_project(data, "pp4.project")
    assert p.products[0].program == [] and p.products[0].legacy_program == ""


def test_from_xml_limits_and_depth():
    warnings: list[str] = []
    big = "<program>" + '<com/>' * (PROG_MAX_NODES + 5) + "</program>"
    cmds, legacy = pp.from_xml(big, "X", warnings)
    assert cmds == [] and legacy.startswith("<program>") and warnings
    nested = "<program>" + "<if cond='1'>" * 40 + "<com/>" + "</if>" * 40 + "</program>"
    warnings = []
    cmds, legacy = pp.from_xml(nested, "X", warnings)
    assert legacy and warnings                                                # chuqurlik chegarasi (32) dan oshdi — tanilmagan sifatida
    assert pp.from_xml("", "X", []) == ([], "")


# ───────────────────────── 5. «Пересчитать параметричность» ─────────────────────────
def test_recalc_parametric_action(client):
    drill = C(cmd="DrillFront", params={"X": "product.px", "Y": 50, "DP": 12, "D": 8})
    pid, prid, xid = _xnc_project(client, [Par(name="px", value=120), If("px>100", Err("px katta"))], xnc_prog=[drill])
    hist0 = _api(client, "get", f"/api/projects/{pid}/history")
    r = _api(client, "post", f"/api/projects/{pid}/actions/recalc-parametric")
    rep = r["report"]
    assert rep["totals"]["programs"] == 1 and rep["totals"]["xnc"] == 1 and rep["totals"]["errors"] == 1
    assert rep["products"][0]["vars"] == 1 and rep["products"][0]["messages"][0]["text"] == "px katta"
    assert rep["xnc"][0]["id"] == xid and rep["xnc"][0]["errors"] == 0
    assert r["project"]["id"] == pid
    # hech narsa o'zgarmagan — tarixga bo'sh versiya yozilmadi
    assert _api(client, "get", f"/api/projects/{pid}/history")["version"] == hist0["version"]
    # eskirgan holat tuzatiladi: bazadagi part_vars qo'lda buzilgan bo'lsa ham action qayta hisoblaydi
    from app import store
    proj = store.load(pid)
    next(o for o in proj.operations if o.id == xid).xnc.part_vars = {"product.px": 1.0}
    proj.products[0].prog_vars = {"px": 1.0}
    proj.products[0].prog_messages = []
    store.save(proj, history=False)
    with store.editing(pid) as p2:                                              # editing → recalc: allaqachon to'g'ri
        pass
    r = _api(client, "post", f"/api/projects/{pid}/actions/recalc-parametric")
    x = next(o for o in r["project"]["operations"] if o["id"] == xid)["xnc"]
    assert x["part_vars"]["product.px"] == 120 and r["project"]["products"][0]["prog_vars"]["px"] == 120


def test_recalc_parametric_xnc_error_is_reported(client):
    bad = C(cmd="DrillFront", params={"X": "yoq_nom", "Y": 10, "DP": 5, "D": 8})
    pid, prid, xid = _xnc_project(client, [], xnc_prog=[bad])
    rep = _api(client, "post", f"/api/projects/{pid}/actions/recalc-parametric")["report"]
    assert rep["totals"]["programs"] == 0 and rep["totals"]["xnc_errors"] >= 1
    assert rep["xnc"][0]["messages"] and "yoq_nom" in rep["xnc"][0]["messages"][0]
    assert client.post("/api/projects/yoq/actions/recalc-parametric").status_code == 404


def test_xnc_evaluator_unchanged_for_normal_runs():
    """Quruq rejim XNC hisobiga ta'sir qilmaydi: dx/dy/dz va DEFAULT_VARS bor, Err — ogohlantirish, Msg — e'tiborsiz."""
    ops = xnc.evaluate([Var("a", "dx/2"), C(cmd="DrillFront", params={"X": "a", "Y": "allowanceT", "DP": 5, "D": 8}),
                        Msg("salom"), Err("xato")], 800, 600, 16)
    assert [(o["X"], o["Y"]) for o in ops if o["kind"] == "DrillFront"] == [(400, 0)]
    assert ops.problems == 1 and len(ops.messages) == 1 and ops.messages[0].startswith("XNC")
    assert ops.violations == 1 and [n["level"] for n in ops.notes] == ["info", "error"]
