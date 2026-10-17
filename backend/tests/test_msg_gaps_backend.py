# -*- coding: utf-8 -*-
"""Xabarlar auditi (backend): kirish nuqtasisiz freza segmenti, detaldan tashqaridagi / noto'g'ri chuqurlikdagi teshik (maydon nomi va
chegarasi bilan ogohlantirish, chizmada qizil uzuq aylana), Err matni tirnoqlarsiz, kroy uchun detal / list (polosa) yo'q — 400 va
«Раскроить все» da sabab."""
from app.i18n import set_lang
from app.models import Operation, OpType, XncCommand as C, XNCParams
from app.services import xnc as X
from app.services.xnc_tools import ToolLib, XncTool


def _xop(prog, dx=1900, dy=500, dz=16):
    return Operation(type=OpType.XNC, name="op", xnc=XNCParams(length=dx, width=dy, thickness=dz, by_part_size=False, program=prog))


def _ru():
    set_lang("ru")


# ───────────────────────── XNC: MillLine / дуга без MillStart ─────────────────────────
def test_mill_segment_without_start_warns_on_its_row():
    _ru()
    prog = [C(cmd="DrillFront", params={"X": 10, "Y": 20, "D": 8, "DP": 12}),
            C(cmd="MillLine", params={"X": 100, "Y": 0}),
            C(cmd="MillArc", params={"X": 200, "Y": 50, "R": 80})]
    st = X.xnc_cost(_xop(prog))
    msgs = st["warnings"]
    assert len(msgs) == 2 and all("точку входа" in m and "MillStart" in m for m in msgs)
    assert "XNC 2 (MillLine)" in msgs[0] and "XNC 3 (MillArc)" in msgs[1]
    assert st["warning_src"] == [["1"], ["2"]]
    svg = X.xnc_drawing_svg(_xop(prog))
    assert 'class="xnc-error" data-err-cmd="1"' in svg and "точку входа" in svg


def test_mill_segment_after_start_is_silent():
    prog = [C(cmd="MillStart", params={"X": 10, "Y": 10, "DP": 5, "D": 8}),
            C(cmd="DrillFront", params={"X": 50, "Y": 50, "D": 8, "DP": 12}),     # oraliqdagi teshik konturni uzmaydi
            C(cmd="MillLine", params={"X": 100, "Y": 10})]
    assert X.xnc_cost(_xop(prog))["warnings"] == []


def test_mill_no_start_uz():
    set_lang("uz")
    try:
        msgs = X.xnc_cost(_xop([C(cmd="MillLine", params={"X": 1, "Y": 1})]))["warnings"]
        assert "kirish nuqtasi" in msgs[0]
    finally:
        _ru()


# ───────────────────────── XNC: teshik chegaralari ─────────────────────────
def test_hole_outside_part_warns_with_field_and_limit_and_is_drawn():
    _ru()
    op = _xop([C(cmd="DrillFront", params={"X": 2500, "Y": 20, "D": 8, "DP": 12}),
               C(cmd="DrillFront", params={"X": 50, "Y": -3, "D": 8, "DP": 12}),
               C(cmd="DrillFront", params={"X": 50, "Y": 50, "D": 8, "DP": 12})])
    st = X.xnc_cost(op)
    assert st["drills"] == 1                                           # tashqaridagilar stanokka chiqmaydi
    assert len(st["warnings"]) == 2 and st["warning_src"] == [["0"], ["1"]]
    assert "X (по длине) = 2500" in st["warnings"][0] and "не больше 1900 мм" in st["warnings"][0]
    assert "Y (по ширине) = -3" in st["warnings"][1] and "не меньше 0 мм" in st["warnings"][1]
    svg = X.xnc_drawing_svg(op)
    assert svg.count("xnc-hole-out") == 2 and 'data-cmd="0"' in svg     # jim tashlanmaydi — qizil uzuq aylana
    assert "X (по длине)" in svg                                       # birinchi xabar — chizmada
    mp = X.machine_program(op)
    assert sum(1 for o in mp["ops"] if o["kind"] == "drill") == 1


def test_hole_array_outside_one_message_per_field():
    op = _xop([C(cmd="DrillFront", params={"X": 1800, "Y": 20, "D": 5, "DP": 12, "AC": 5, "AS": 50})])
    st = X.xnc_cost(op)
    assert st["drills"] == 3 and len(st["warnings"]) == 1


def test_hole_origin_shift_reports_program_coordinates():
    _ru()
    op = _xop([C(cmd="Origin", params={"X": 100, "Y": 0}), C(cmd="DrillFront", params={"X": 1850, "Y": 20, "D": 8, "DP": 12})])
    w = X.xnc_cost(op)["warnings"][0]
    assert "X (по длине) = 1850" in w and "не больше 1800 мм" in w


def test_hole_depth_checks():
    _ru()
    op = _xop([C(cmd="DrillFront", params={"X": 50, "Y": 50, "D": 8, "DP": -5}),
               C(cmd="DrillFront", params={"X": 60, "Y": 50, "D": 8, "DP": 30}),          # o'tuvchi teshik — xabarsiz
               C(cmd="DrillLeft", params={"Y": 50, "Z": 8, "D": 8, "DP": 2500}),
               C(cmd="DrillTop", params={"X": 50, "Z": 40, "D": 8, "DP": 20})])
    st = X.xnc_cost(op)
    w = st["warnings"]
    assert len(w) == 3 and st["warning_src"] == [["0"], ["2"], ["3"]]
    assert "DP = -5" in w[0] and "больше 0" in w[0]
    assert "DP = 2500" in w[1] and "1900" in w[1]
    assert "Z (по толщине) = 40" in w[2] and "16" in w[2]
    assert st["drills"] == 4                                           # chuqurlik xatosi — teshik baribir bajariladi


def test_blind_tool_deeper_than_thickness():
    _ru()
    lib = ToolLib([XncTool(plane="front", d=35, name="Cup", depth=13, through=False)])
    ops = X.evaluate([C(cmd="DrillFront", params={"X": 50, "Y": 50, "T": "Cup", "DP": 20})], 600, 400, 16, tool_lib=lib)
    assert len(ops.messages) == 1 and "DP = 20" in ops.messages[0] and "Cup" in ops.messages[0]
    ok = X.evaluate([C(cmd="DrillFront", params={"X": 50, "Y": 50, "T": "Cup"})], 600, 400, 16, tool_lib=lib)
    assert ok.messages == []


# ───────────────────────── XNC: Err matni ─────────────────────────
def test_err_text_without_quotes():
    _ru()
    for raw in ("'Custom error: too wide'", '"Custom error: too wide"'):
        op = _xop([C(cmd="Err", params={"text": raw})])
        st = X.xnc_cost(op)
        assert st["warnings"] == ["XNC 1: Custom error: too wide"]
        svg = X.xnc_drawing_svg(op)
        assert "Custom error: too wide" in svg and "&#x27;Custom" not in svg and "'Custom" not in svg
    st = X.xnc_cost(_xop([C(cmd="Var", params={"name": "a", "value": 5}), C(cmd="Err", params={"text": "'a=' + a"})]))
    assert st["warnings"][0].startswith("XNC 2: a=5")                    # ifoda hisoblanadi (son — dvigatel matni)
    assert X.xnc_cost(_xop([C(cmd="Err", params={"text": "oddiy matn"})]))["warnings"] == ["XNC 1: oddiy matn"]
    assert X.xnc_cost(_xop([C(cmd="Err", params={"text": "'yopilmagan"})]))["warnings"] == ["XNC 1: 'yopilmagan"]


# ───────────────────────── Kroy: detal / list yo'q ─────────────────────────
def _cs(client, sheets, parts):
    pid = client.post("/api/projects", json={"name": "bo'sh kroy"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "name": "LDSP"}).json()
    oid = p["operations"][-1]["id"]
    client.put(f"/api/projects/{pid}/operations/{oid}/sheets", json=sheets)
    if parts:
        client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=parts)
    return pid, oid


def test_cs_no_sheets_or_zero_qty_rejected(client):
    part = [dict(name="A", length=500, width=300, qty=2)]
    pid, oid = _cs(client, [{"length": 2750, "width": 1830, "qty": 0}], part)
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize?lang=ru")
    assert r.status_code == 400 and "Нет листов для раскроя" in r.json()["detail"]
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize", headers={"Accept-Language": "uz"})
    assert r.status_code == 400 and "Kroy uchun listlar yo'q" in r.json()["detail"]
    pid, oid = _cs(client, [], part)
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize?lang=ru")
    assert r.status_code == 400 and r.json()["detail"] == "Нет листов для раскроя"
    pid, oid = _cs(client, [{"length": 2750, "width": 1830, "qty": 1}], [])
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize?lang=ru")
    assert r.status_code == 400 and r.json()["detail"] == "Нет деталей для раскроя"
    pid, oid = _cs(client, [{"length": 2750, "width": 1830, "qty": 1}], [dict(name="A", length=500, width=300, qty=0)])
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize?lang=ru")
    assert r.status_code == 400 and "Нет деталей для раскроя" in r.json()["detail"]
    pid, oid = _cs(client, [{"length": 2750, "width": 1830, "qty": 1}, {"length": 2000, "width": 1000, "qty": 0}], part)
    assert client.post(f"/api/projects/{pid}/operations/{oid}/optimize?quality=fast").status_code == 200


def test_cl_no_bars_rejected_and_cut_all_reports_reason(client):
    pid = client.post("/api/projects", json={"name": "CL bo'sh"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CL", "name": "Profil"}).json()
    cl = p["operations"][-1]["id"]
    r = client.post(f"/api/projects/{pid}/operations/{cl}/optimize?lang=ru")
    assert r.status_code == 400 and r.json()["detail"] == "Нет деталей для раскроя"
    client.post(f"/api/projects/{pid}/operations/{cl}/parts", json=[dict(name="P", length=1000, width=0, qty=2)])
    client.put(f"/api/projects/{pid}/operations/{cl}/sheets", json=[{"length": 6000, "width": 100, "qty": 0}])
    r = client.post(f"/api/projects/{pid}/operations/{cl}/optimize?lang=ru")
    assert r.status_code == 400 and "Нет полос" in r.json()["detail"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "name": "LDSP"}).json()
    cs = p["operations"][-1]["id"]
    client.put(f"/api/projects/{pid}/operations/{cs}/sheets", json=[{"length": 2750, "width": 1830, "qty": 0}])
    client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[dict(name="A", length=500, width=300, qty=1)])
    res = client.post(f"/api/projects/{pid}/actions/optimize-all?lang=ru").json()["results"]
    by = {r["op_id"]: r for r in res}
    assert by[cl]["skipped"] and "Нет полос" in by[cl]["reason"]
    assert by[cs]["skipped"] and "Нет листов для раскроя" in by[cs]["reason"]


def test_cn_zero_qty_sheets_rejected(client):
    pid = client.post("/api/projects", json={"name": "CN bo'sh"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CN"}).json()
    oid = p["operations"][-1]["id"]
    client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=[dict(name="A", length=300, width=200, qty=1)])
    client.put(f"/api/projects/{pid}/operations/{oid}/sheets", json=[{"length": 2750, "width": 1830, "qty": 0}])
    for url in ("optimize", "cn/jobs"):
        r = client.post(f"/api/projects/{pid}/operations/{oid}/{url}?lang=ru")
        assert r.status_code == 400 and "Нет листов для раскроя" in r.json()["detail"]


# ───────────────────────── XNC: yoyning majburiy parametri ─────────────────────────
def test_arc_without_radius_or_center_warns():
    _ru()
    start = C(cmd="MillStart", params={"X": 10, "Y": 10, "DP": 5, "D": 8})
    w = X.xnc_cost(_xop([start, C(cmd="MillArc", params={"X": 100, "Y": 10})]))["warnings"]
    assert len(w) == 1 and "XNC 2 (MillArc): параметр R — не задан" in w[0]
    w = X.xnc_cost(_xop([start, C(cmd="MillArcCenter", params={"X": 100, "Y": 10, "CX": 55})]))["warnings"]
    assert len(w) == 1 and "параметр CY" in w[0]
    w = X.xnc_cost(_xop([start, C(cmd="MillArc3P", params={"X": 100, "Y": 10})]))["warnings"]
    assert len(w) == 1 and "X2/Y2" in w[0]
    # R oldingi yoydan meros — xabarsiz
    ok = [start, C(cmd="MillArc", params={"X": 100, "Y": 10, "R": 60}), C(cmd="MillArc", params={"X": 150, "Y": 10})]
    assert X.xnc_cost(_xop(ok))["warnings"] == []
