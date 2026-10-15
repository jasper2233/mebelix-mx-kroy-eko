"""W6: GR (пазование) standart qiymatlari/panel API'si va EL (kromka) hisobining shartnomasi."""
import pytest

from app.models import GR_DEFAULTS, ELParams, GRParams
from app.services.calc import groove_passes

BUILTIN_GR = dict(width=4, depth=8, offset=10, offset_inclusive=True, saw_thickness=4, price=0)


def _op(p, oid):
    return next(o for o in p["operations"] if o["id"] == oid)


def _project(client, name):
    pid = client.post("/api/projects", json={"name": name}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "W6CS", "name": "W6CS"}).json()
    return pid, p["operations"][-1]["id"]


def _add(client, pid, typ, **kw):
    p = client.post(f"/api/projects/{pid}/operations", json={"type": typ, "code": typ + "1", "name": typ + " test", **kw}).json()
    return p["operations"][-1]["id"]


def _parts(client, pid, cs, parts):
    r = client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=parts)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture()
def clean_gr_defaults(client):
    """Umumiy standartni sinovdan keyin o'rnatilgan holatga qaytaradi (sessiya bazasi umumiy)."""
    yield
    client.put("/api/settings/gr_defaults/default", json=BUILTIN_GR)


# ───────────────────────── GR: standart qiymatlar — bitta konstanta ─────────────────────────
def test_gr_defaults_single_constant_matches_project_format():
    # `.project` formati: grWidth 4, grDepth 8, grOffset 10, grOffsetIncl true, grSawthick 4
    assert GR_DEFAULTS == dict(width=4.0, depth=8.0, offset=10.0, offset_inclusive=True, saw_thickness=4.0)
    g = GRParams()
    assert (g.width, g.depth, g.offset, g.offset_inclusive, g.saw_thickness, g.price) == (4, 8, 10, True, 4, 0)
    assert g.usage == 0 and g.cut_length == 0 and g.passes == 1


def test_gr_old_saved_json_keeps_its_values():
    g = GRParams.model_validate({"width": 4, "depth": 10, "offset": 16, "price": 100})       # eski loyiha (avvalgi standart 10/16)
    assert (g.depth, g.offset, g.price) == (10, 16, 100) and g.saw_thickness == 4 and g.offset_inclusive is True


def test_new_gr_operation_uses_builtin_defaults(client):
    pid, _cs = _project(client, "W6 GR defaults")
    gid = _add(client, pid, "GR")
    gr = _op(client.get(f"/api/projects/{pid}").json(), gid)
    for k, v in BUILTIN_GR.items():
        assert gr["gr"][k] == v, k
    assert client.get("/api/settings/gr_defaults/default").json()["depth"] == 8


def test_gr_defaults_scope_saves_params_but_not_computed_values(client, clean_gr_defaults):
    r = client.put("/api/settings/gr_defaults/default", json=dict(width=6, depth=12, offset=20, offset_inclusive=False,
                                                                  saw_thickness=3, price=1500, usage=99, cut_length=77, passes=9))
    assert r.status_code == 200, r.text
    saved = client.get("/api/settings/gr_defaults/default").json()
    assert (saved["width"], saved["depth"], saved["offset"], saved["offset_inclusive"], saved["saw_thickness"],
            saved["price"]) == (6, 12, 20, False, 3, 1500)
    assert saved["usage"] == 0 and saved["cut_length"] == 0 and saved["passes"] == 1          # hisoblanganlar saqlanmaydi
    pid, _cs = _project(client, "W6 GR defaults 2")
    gid = _add(client, pid, "GR")
    gr = _op(client.get(f"/api/projects/{pid}").json(), gid)
    assert (gr["gr"]["width"], gr["gr"]["offset_inclusive"], gr["gr"]["saw_thickness"], gr["gr"]["price"]) == (6, False, 3, 1500)
    assert gr["gr"]["usage"] == 0
    assert client.put("/api/settings/gr_defaults/default", json=dict(width=0)).status_code == 400      # chegara tekshiruvi


def test_gr_defaults_do_not_touch_existing_operations(client, clean_gr_defaults):
    pid, _cs = _project(client, "W6 GR defaults 3")
    gid = _add(client, pid, "GR")
    client.put("/api/settings/gr_defaults/default", json=dict(width=9, depth=9, offset=9, saw_thickness=9))
    assert _op(client.get(f"/api/projects/{pid}").json(), gid)["gr"]["width"] == 4


# ───────────────────────── GR: import `.project` ─────────────────────────
def _xml(attrs: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project name="Paz import">
  <good typeId="product" id="1" code="P1" name="Shkaf" count="1">
    <part id="11" code="A1" name="Bok" count="1" dl="720" dw="560" grt="@operation#5"/>
  </good>
  <good typeId="sheet" id="4" code="LDSP" name="LDSP 16" t="16" l="2750" w="1830" count="2"><part id="20" l="2750" w="1830" count="10000"/></good>
  <operation typeId="GR" id="5" typeName="Paz" {attrs}/>
  <operation typeId="CS" id="2" t="16" l="2750" w="1830"><material id="4" count="2"/><part id="11"/></operation>
</project>""".encode("utf-8")


def test_import_gr_attributes_and_format_defaults():
    from app.plugins.legacy_project import import_project
    p, _w = import_project(_xml('grWidth="6" grDepth="9" grOffset="12" grOffsetIncl="false" grSawthick="3" grCost="1500"'), "a.project")
    g = next(o for o in p.operations if o.type.value == "GR").gr
    assert (g.width, g.depth, g.offset, g.offset_inclusive, g.saw_thickness, g.price) == (6, 9, 12, False, 3, 1500)
    p, _w = import_project(_xml(""), "b.project")                                     # atributlar yo'q — formatdagi standartlar
    g = next(o for o in p.operations if o.type.value == "GR").gr
    assert (g.width, g.depth, g.offset, g.offset_inclusive, g.saw_thickness, g.price) == (4, 8, 10, True, 4, 0)
    p, _w = import_project(_xml('grWidth="0" grSawthick="0"'), "c.project")            # 0 eni/arra qalinligi — xatosiz, standartga
    g = next(o for o in p.operations if o.type.value == "GR").gr
    assert g.width == 4 and g.saw_thickness == 4


# ───────────────────────── GR: panel API (groove-usage) ─────────────────────────
def _gr_project(client, name, price=2000, **gr):
    pid, cs = _project(client, name)
    gid = _add(client, pid, "GR")
    client.patch(f"/api/projects/{pid}/operations/{gid}", json={"gr": {"price": price, **gr}})
    _parts(client, pid, cs, [
        {"name": "A", "length": 800, "width": 500, "qty": 3, "groove_top": {"op_id": gid}, "groove_bottom": {"op_id": gid, "back_side": True}},
        {"name": "B", "length": 600, "width": 300, "qty": 2, "groove_right": {"op_id": gid, "back_side": True}},
        {"name": "C", "length": 400, "width": 400, "qty": 1}])
    return pid, cs, gid


def test_groove_usage_endpoint_rows_and_totals(client):
    pid, _cs, gid = _gr_project(client, "W6 GR usage")
    r = client.get(f"/api/projects/{pid}/operations/{gid}/groove-usage")
    assert r.status_code == 200
    u = r.json()
    assert len(u["rows"]) == 2 and u["passes"] == 1
    a, b = u["rows"]
    # A: yuqori + past (uzunlik 800) × 3 = 4800 mm ; B: o'ng (en 300) × 2 = 600 mm
    assert (a["name"], a["length"], a["width"], a["qty"], a["top"], a["bottom"], a["left"], a["right"]) == ("A", 800, 500, 3, 1, 2, 0, 0)
    assert a["groove_len_m"] == 4.8 and a["material"] == "W6CS"
    assert (b["name"], b["top"], b["right"], b["groove_len_m"]) == ("B", 0, 2, 0.6)
    assert u["usage"] == 5.4 and u["cut_length"] == 5.4 and u["cost"] == 10800            # 5.4 m × 2000
    assert {"part_id", "uid", "material", "length", "width", "qty", "top", "bottom", "left", "right", "groove_len_m", "name"} <= set(a)


def test_groove_usage_passes_saw_thickness_and_inclusive_flag(client):
    pid, _cs, gid = _gr_project(client, "W6 GR passes")
    base = client.get(f"/api/projects/{pid}/operations/{gid}/groove-usage").json()
    client.patch(f"/api/projects/{pid}/operations/{gid}", json={"gr": {"width": 10, "saw_thickness": 4}})
    u = client.get(f"/api/projects/{pid}/operations/{gid}/groove-usage").json()
    assert u["passes"] == 3 and u["cut_length"] == round(u["usage"] * 3, 3) and u["cost"] == base["cost"]     # narx — paz uzunligi bo'yicha
    client.patch(f"/api/projects/{pid}/operations/{gid}", json={"gr": {"offset_inclusive": False, "depth": 15, "offset": 25}})
    u2 = client.get(f"/api/projects/{pid}/operations/{gid}/groove-usage").json()
    assert u2["usage"] == u["usage"] and u2["passes"] == 3                                 # chuqurlik/otstup/belgi uzunlikka ta'sir qilmaydi
    p = client.get(f"/api/projects/{pid}").json()
    g = _op(p, gid)["gr"]
    assert (g["usage"], g["passes"], g["cut_length"], g["offset_inclusive"]) == (u["usage"], 3, u["cut_length"], False)
    assert [groove_passes(w, 4) for w in (3, 4, 6, 10, 10.5, 11, 26)] == [1, 1, 2, 3, 3, 3, 7]
    assert groove_passes(5, 0) == 1 and groove_passes(0, 4) == 1


def test_groove_usage_follows_qty_minus_qty_and_product_qty(client):
    pid, cs, gid = _gr_project(client, "W6 GR qty")
    parts = _op(client.get(f"/api/projects/{pid}").json(), cs)["parts"]
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{parts[0]['id']}", json={"minus_qty": 1})
    u = client.get(f"/api/projects/{pid}/operations/{gid}/groove-usage").json()
    assert u["rows"][0]["qty"] == 2 and u["usage"] == 3.8                                  # A: 2 × 1600 + B: 600
    prid = client.get(f"/api/projects/{pid}").json()["products"][0]["id"]
    client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": 2})
    u = client.get(f"/api/projects/{pid}/operations/{gid}/groove-usage").json()
    assert u["rows"][0]["qty"] == 5 and u["rows"][1]["qty"] == 4 and u["usage"] == 9.2      # (6−1)·1600 + 4·300


def test_groove_usage_rejects_non_gr_and_unknown(client):
    pid, cs, gid = _gr_project(client, "W6 GR errors")
    assert client.get(f"/api/projects/{pid}/operations/{cs}/groove-usage").status_code == 400
    assert client.get(f"/api/projects/{pid}/operations/nope/groove-usage").status_code == 404
    assert client.get("/api/projects/nope/operations/x/groove-usage").status_code == 404
    assert "(GR)" in client.get(f"/api/projects/{pid}/operations/{cs}/groove-usage", headers={"Accept-Language": "uz"}).json()["detail"]


def test_groove_usage_empty_when_no_parts(client):
    pid, _cs = _project(client, "W6 GR empty")
    gid = _add(client, pid, "GR")
    u = client.get(f"/api/projects/{pid}/operations/{gid}/groove-usage").json()
    assert u == dict(rows=[], usage=0.0, cut_length=0.0, passes=1, cost=0.0)


# ───────────────────────── GR: chop sozlamalari (gr_params / gr_parts) ─────────────────────────
def test_print_settings_gr_flags_control_report(client):
    pid, _cs, _gid = _gr_project(client, "W6 GR print")
    ps = client.get("/api/settings/print/default").json()
    assert ps["gr_params"] is True and ps["gr_parts"] is True
    both = client.post(f"/api/projects/{pid}/report", json=ps).text
    assert "Длина пазования" in both and "Д-на паза" in both
    no_params = client.post(f"/api/projects/{pid}/report", json={**ps, "gr_params": False}).text
    assert "Длина пазования" not in no_params and "Д-на паза" in no_params
    no_parts = client.post(f"/api/projects/{pid}/report", json={**ps, "gr_parts": False}).text
    assert "Длина пазования" in no_parts and "Д-на паза" not in no_parts
    none = client.post(f"/api/projects/{pid}/report", json={**ps, "gr_params": False, "gr_parts": False}).text
    assert "Длина пазования" not in none and "Д-на паза" not in none
    uz = client.post(f"/api/projects/{pid}/report?lang=uz", json=ps).text
    assert "Pazlash uzunligi" in uz


# ───────────────────────── EL: kromka hisobi shartnomasi ─────────────────────────
def _el_project(client, name, **el):
    pid, cs = _project(client, name)
    eid = _add(client, pid, "EL")
    client.patch(f"/api/projects/{pid}/operations/{eid}", json={"el": el})
    return pid, cs, eid


def test_edge_usage_formula_waste_overhang_min_glue_and_rounding(client):
    pid, cs, eid = _el_project(client, "W6 EL formula", overhang=20, min_glue_length=100, waste_percent=5,
                               price=1000, op_price=500, material_round=20, work_round=20)
    _parts(client, pid, cs, [
        {"name": "P1", "length": 800, "width": 500, "qty": 2, "edge_top": {"op_id": eid}, "edge_left": {"op_id": eid}},
        {"name": "Short", "length": 60, "width": 300, "qty": 1, "edge_top": {"op_id": eid}}])
    u = client.get(f"/api/projects/{pid}/operations/{eid}/edge-usage").json()
    # ish = Σ tomonlar × soni = (800 + 500) × 2 + 60 = 2660 mm → 2.66 m
    # material = [(800+40) + (500+40)] × 2 + (max(60,100)+40) = 2760 + 140 = 2900 mm × 1.05 = 3045 mm → 3.045 m
    assert u["work_m"] == 2.66 and u["material_m"] == 3.05 and u["narrow"] == 0
    rows = {r["name"]: r for r in u["rows"]}
    assert rows["P1"]["edges_len"] == 1 and rows["P1"]["edges_wid"] == 1 and rows["P1"]["qty"] == 2
    assert rows["P1"]["edge_m"] == 2.898 and rows["Short"]["edge_m"] == 0.147             # 2760·1.05 ; 140·1.05
    el_op = _op(client.get(f"/api/projects/{pid}").json(), eid)
    assert el_op["cost_material"] == 3050 and el_op["cost_operation"] == 1330             # 3.05 × 1000 ; 2.66 × 500


def test_edge_usage_rounding_codes_up_and_down(client):
    pid, cs, eid = _el_project(client, "W6 EL round", overhang=0, min_glue_length=0, material_round=21, work_round=22)
    _parts(client, pid, cs, [{"name": "P", "length": 1234, "width": 400, "qty": 1, "edge_top": {"op_id": eid}}])
    u = client.get(f"/api/projects/{pid}/operations/{eid}/edge-usage").json()
    assert u["material_m"] == 1.24 and u["work_m"] == 1.23                                # ⌈0.00⌉ yuqoriga, ⌊0.00⌋ pastga
    client.patch(f"/api/projects/{pid}/operations/{eid}", json={"el": {"material_round": 0, "work_round": 1}})
    u = client.get(f"/api/projects/{pid}/operations/{eid}/edge-usage").json()
    assert u["material_m"] == 1 and u["work_m"] == 2                                      # [0] yaqiniga ; ⌈0⌉ yuqoriga


def test_edge_usage_narrow_side_warning_and_count_material_flag(client):
    pid, cs, eid = _el_project(client, "W6 EL narrow", min_perp_side=40, price=2000)
    _parts(client, pid, cs, [{"name": "Tor", "length": 500, "width": 30, "qty": 1, "edge_top": {"op_id": eid}}])
    u = client.get(f"/api/projects/{pid}/operations/{eid}/edge-usage").json()
    assert u["narrow"] == 1 and u["rows"][0]["narrow"] is True                             # eni 30 < 40: stanok ushlay olmaydi
    assert _op(client.get(f"/api/projects/{pid}").json(), eid)["cost_material"] > 0
    client.patch(f"/api/projects/{pid}/operations/{eid}", json={"el": {"count_material": False}})
    assert _op(client.get(f"/api/projects/{pid}").json(), eid)["cost_material"] == 0       # «Учитывать материал» ☐ — narx yo'q


def test_edge_defaults_do_not_store_symbol_or_color(client):
    d = client.get("/api/settings/el_defaults/default").json()
    r = client.put("/api/settings/el_defaults/default", json={**d, "symbol": "Z", "color": "#123456"})
    assert r.status_code == 200
    cur = client.get("/api/settings/el_defaults/default").json()
    assert cur["symbol"] == ELParams().symbol and cur["color"] == ELParams().color

