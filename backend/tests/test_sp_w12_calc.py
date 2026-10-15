"""W12 · (SP) Обработка поверхности: model, hisob formulalari, ombor talabnomasi, mahsulot narxi, API, hisobot, eski JSON,
etiketka o'zgaruvchilari (`surfFront` / `surfBack`)."""
import pytest

from app.models import Operation, OpType, Part, Project, SPParams
from app.services import calc, label_vars, sp_ops


def _api(client, method, url, **kw):
    r = getattr(client, method)(url, **kw)
    assert r.status_code == 200, (url, r.status_code, r.text[:300])
    return r.json()


def _op(p, oid):
    return next(o for o in p["operations"] if o["id"] == oid)


def _project(client, qty=3):
    """Loyiha: mahsulot (soni qty) + CS operatsiyasi; qaytaradi (pid, prid, cs_id)."""
    p = _api(client, "post", "/api/projects", json={"name": "SP test"})
    pid, prid = p["id"], p["products"][0]["id"]
    _api(client, "patch", f"/api/projects/{pid}/products/{prid}", json={"qty": qty})
    p = _api(client, "post", f"/api/projects/{pid}/operations", json={"type": "CS", "code": "LDSP16", "name": "LDSP"})
    return pid, prid, p["operations"][-1]["id"]


def _sp(client, pid, **params):
    p = _api(client, "post", f"/api/projects/{pid}/operations", json={"type": "SP", "name": "Lak"})
    oid = p["operations"][-1]["id"]
    if params:
        p = _api(client, "patch", f"/api/projects/{pid}/operations/{oid}", json={"sp": params})
    return oid, p


def _parts(client, pid, cs, parts):
    p = _api(client, "post", f"/api/projects/{pid}/operations/{cs}/parts", json=parts)
    return [x["id"] for x in _op(p, cs)["parts"]], p


# ───────────────────────── 1. model va yaratish ─────────────────────────
def test_new_sp_operation_defaults_and_catalog_price(client):
    pid, _prid, _cs = _project(client)
    oid, p = _sp(client, pid)
    sp = _op(p, oid)["sp"]
    assert _op(p, oid)["type"] == "SP"
    assert sp == dict(count_material=True, waste_percent=0.0, rest_side=0.0, size_mode=-1, op_price=0.0, price=0.0,
                      length=2200.0, width=800.0, thickness=1.0,           # v2.5: material o'lchami (GibLab kabi)
                      area_m2=0.0, material_m2=0.0)
    assert _op(p, oid)["cost_material"] == 0 and _op(p, oid)["cost_operation"] == 0


def test_sp_defaults_setting(client):
    """«Сохранить параметры по умолчанию»: yangi SP shu standartdan; hisoblangan maydonlar saqlanmaydi."""
    r = client.put("/api/settings/sp_defaults/default", json=dict(waste_percent=7, op_price=1234, area_m2=99, material_m2=88))
    assert r.status_code == 200
    try:
        d = client.get("/api/settings/sp_defaults/default").json()
        assert d["waste_percent"] == 7 and d["op_price"] == 1234 and d["area_m2"] == 0 and d["material_m2"] == 0
        pid, _prid, _cs = _project(client)
        oid, p = _sp(client, pid)
        sp = _op(p, oid)["sp"]
        assert sp["waste_percent"] == 7 and sp["op_price"] == 1234 and sp["area_m2"] == 0
    finally:
        client.put("/api/settings/sp_defaults/default", json={})


def test_sp_param_limits_422(client):
    pid, _prid, _cs = _project(client)
    oid, _p = _sp(client, pid)
    for bad in (dict(waste_percent=101), dict(waste_percent=-1), dict(size_mode=1), dict(size_mode=-2),
                dict(rest_side=-5), dict(op_price=-1)):
        r = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"sp": bad})
        assert r.status_code == 422, bad


# ───────────────────────── 2. hisob formulalari ─────────────────────────
def test_area_material_and_costs(client):
    """1000×500 detal ×2, mahsulot ×3 → ОК = 6; ikki tomon; chiqit 10 %, chetda 20 mm; zagotovka rejimi (0)."""
    pid, _prid, cs = _project(client, qty=3)
    ids, _ = _parts(client, pid, cs, [dict(name="Eshik", length=1000, width=500, qty=2)])
    oid, _p = _sp(client, pid, size_mode=0, waste_percent=10, rest_side=20, price=100, op_price=50)
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}",
             json=dict(surface_face_op=oid, surface_back_op=oid))
    sp, op = _op(p, oid)["sp"], _op(p, oid)
    assert sp["area_m2"] == pytest.approx(0.5 * 2 * 6, abs=1e-4)                                   # 6.0
    mat = (1.040 * 0.540) * 2 * 6 * 1.10                                                           # 7.41312
    assert sp["material_m2"] == pytest.approx(mat, abs=1e-4)
    assert op["cost_operation"] == pytest.approx(6.0 * 50, abs=0.01)                               # 300
    assert op["cost_material"] == pytest.approx(round(round(mat, 4) * 100, 2), abs=0.01)           # ~741.31


def test_front_only_and_back_only_count_one_side(client):
    pid, _prid, cs = _project(client, qty=1)
    ids, _ = _parts(client, pid, cs, [dict(name="A", length=1000, width=1000, qty=1),
                                      dict(name="B", length=1000, width=1000, qty=1)])
    oid, _p = _sp(client, pid, size_mode=0)
    _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}", json=dict(surface_face_op=oid))
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[1]}", json=dict(surface_back_op=oid))
    assert _op(p, oid)["sp"]["area_m2"] == pytest.approx(2.0)
    rows = client.get(f"/api/projects/{pid}/operations/{oid}/surface-usage").json()["rows"]
    assert [(r["front"], r["back"], r["sides"], r["area_m2"]) for r in rows] == [(True, False, 1, 1.0), (False, True, 1, 1.0)]


def test_size_mode_saw_vs_blank_with_allowance(client):
    """-1 — pilniy o'lcham (zagotovka + pripusk + «Припуск на обработку»), 0 — zagotovka."""
    pid, _prid, cs = _project(client, qty=1)
    _api(client, "patch", f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": {"machining_allowance": 5}})
    ids, _ = _parts(client, pid, cs, [dict(name="A", length=1000, width=500, qty=1, allow_top=10, allow_left=20)])
    oid, _p = _sp(client, pid, size_mode=-1)
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}", json=dict(surface_face_op=oid))
    # pilniy: (1000 + 20 + 2·5) × (500 + 10 + 2·5) = 1030 × 520
    assert _op(p, oid)["sp"]["area_m2"] == pytest.approx(1.030 * 0.520, abs=1e-4)
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{oid}", json={"sp": {"size_mode": 0}})
    assert _op(p, oid)["sp"]["area_m2"] == pytest.approx(0.5, abs=1e-4)


def test_edge_thickness_changes_blank_size(client):
    """Kiritish rejimi «detal» (standart): zagotovka = detal − kromka qalinligi (kromkali tomonlarda) — maydon shunga mos."""
    pid, _prid, cs = _project(client, qty=1)
    p = _api(client, "post", f"/api/projects/{pid}/operations", json={"type": "EL", "name": "PVC"})
    el = p["operations"][-1]["id"]
    _api(client, "patch", f"/api/projects/{pid}/operations/{el}", json={"el": {"thickness": 2}})
    ids, _ = _parts(client, pid, cs, [dict(name="A", length=1000, width=500, qty=1, edge_left={"op_id": el},
                                           edge_top={"op_id": el})])
    oid, _p = _sp(client, pid, size_mode=0)
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}", json=dict(surface_face_op=oid))
    assert _op(p, oid)["sp"]["area_m2"] == pytest.approx(998 * 498 / 1e6, abs=1e-4)


def test_count_material_off_and_minus_qty(client):
    pid, _prid, cs = _project(client, qty=2)
    ids, _ = _parts(client, pid, cs, [dict(name="A", length=1000, width=1000, qty=3, minus_qty=2)])
    oid, _p = _sp(client, pid, size_mode=0, price=1000, op_price=10)
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}", json=dict(surface_face_op=oid))
    # ОК = 3 × 2 = 6, МК = 2 → 4
    assert _op(p, oid)["sp"]["area_m2"] == 4.0 and _op(p, oid)["sp"]["material_m2"] == 4.0
    assert _op(p, oid)["cost_material"] == 4000 and _op(p, oid)["cost_operation"] == 40
    wh = [r for r in client.get(f"/api/projects/{pid}/warehouse").json() if r["type"] == "SP"]
    assert len(wh) == 1 and wh[0]["qty"] == 4.0 and wh[0]["unit"] in ("м²", "m²") and wh[0]["sum"] == 4000
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{oid}", json={"sp": {"count_material": False}})
    assert _op(p, oid)["sp"]["material_m2"] == 0 and _op(p, oid)["cost_material"] == 0
    assert _op(p, oid)["cost_operation"] == 40                       # ish narxi material hisobiga bog'liq emas
    assert [r for r in client.get(f"/api/projects/{pid}/warehouse").json() if r["type"] == "SP"] == []


def test_degenerate_sizes_do_not_break(client):
    """O'lchami 0 / bo'sh detal — maydon 0, xato yo'q."""
    pid, _prid, cs = _project(client, qty=1)
    ids, _ = _parts(client, pid, cs, [dict(name="Bo'sh", length=0, width=0, qty=1)])
    oid, _p = _sp(client, pid, size_mode=0, rest_side=50, price=10)
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}", json=dict(surface_face_op=oid))
    assert _op(p, oid)["sp"]["area_m2"] == 0 and _op(p, oid)["cost_material"] == 0


def test_rest_side_switch(client, monkeypatch):
    """REST_BOTH_EDGES=False — qoldiq faqat bir chetda (L + r)."""
    pid, _prid, cs = _project(client, qty=1)
    ids, _ = _parts(client, pid, cs, [dict(name="A", length=1000, width=500, qty=1)])
    oid, _p = _sp(client, pid, size_mode=0, rest_side=20)
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}", json=dict(surface_face_op=oid))
    assert _op(p, oid)["sp"]["material_m2"] == pytest.approx(1.04 * 0.54, abs=1e-4)
    monkeypatch.setattr(sp_ops, "REST_BOTH_EDGES", False)
    p = _api(client, "post", f"/api/projects/{pid}/save")
    assert _op(p, oid)["sp"]["material_m2"] == pytest.approx(1.02 * 0.52, abs=1e-4)


# ───────────────────────── 3. mahsulot narxi va bog'lanishlar ─────────────────────────
def test_product_cost_spread_by_area_share(client):
    pid, prid, cs = _project(client, qty=1)
    p2 = _api(client, "post", f"/api/projects/{pid}/products", json={"name": "Stol", "qty": 1})
    prid2 = p2["products"][1]["id"]
    ids, _ = _parts(client, pid, cs, [dict(name="A", length=1000, width=1000, qty=1, product_id=prid),
                                      dict(name="B", length=1000, width=3000, qty=1, product_id=prid2)])
    oid, _p = _sp(client, pid, size_mode=0, op_price=100)
    for i in ids:
        p = _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{i}", json=dict(surface_face_op=oid))
    assert _op(p, oid)["cost_operation"] == 400                       # 4 m² × 100
    cost = {x["name"]: x["cost_operation"] for x in p["products"]}
    assert cost[p["products"][0]["name"]] == 100 and cost["Stol"] == 300


def test_delete_sp_clears_part_references(client):
    pid, _prid, cs = _project(client)
    ids, _ = _parts(client, pid, cs, [dict(name="A", length=500, width=500, qty=1)])
    oid, _p = _sp(client, pid)
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}",
             json=dict(surface_face_op=oid, surface_back_op=oid))
    assert _op(p, cs)["parts"][0]["surface_face_op"] == oid
    p = _api(client, "delete", f"/api/projects/{pid}/operations/{oid}")
    pt = _op(p, cs)["parts"][0]
    assert pt["surface_face_op"] is None and pt["surface_back_op"] is None


def test_dangling_reference_is_pruned_on_save():
    """Yo'q (yoki SP bo'lmagan) operatsiyaga havola recalc_project da tozalanadi."""
    cs = Operation(type=OpType.CS, name="LDSP", parts=[Part(length=100, width=100, surface_face_op="yo'q",
                                                          surface_back_op="x")])
    el = Operation(type=OpType.EL, name="PVC", id="x")
    p = calc.recalc_project(Project(name="t", operations=[cs, el]))
    assert p.operations[0].parts[0].surface_face_op is None and p.operations[0].parts[0].surface_back_op is None


def test_clone_cs_keeps_surface_refs_and_doubles_area(client):
    pid, _prid, cs = _project(client, qty=1)
    ids, _ = _parts(client, pid, cs, [dict(name="A", length=1000, width=1000, qty=1)])
    oid, _p = _sp(client, pid, size_mode=0)
    _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}", json=dict(surface_face_op=oid))
    p = _api(client, "post", f"/api/projects/{pid}/operations/{cs}/clone")
    assert _op(p, oid)["sp"]["area_m2"] == 2.0


# ───────────────────────── 4. API ─────────────────────────
def test_surface_usage_endpoint_and_type_check(client):
    pid, _prid, cs = _project(client, qty=2)
    ids, _ = _parts(client, pid, cs, [dict(name="Panel", length=800, width=400, qty=1)])
    oid, _p = _sp(client, pid, size_mode=0, op_price=10)
    _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}", json=dict(surface_face_op=oid))
    u = _api(client, "get", f"/api/projects/{pid}/operations/{oid}/surface-usage")
    assert u["area_m2"] == pytest.approx(0.64) and u["cost_operation"] == pytest.approx(6.4)
    r0 = u["rows"][0]
    assert (r0["name"], r0["material"], r0["length"], r0["width"], r0["qty"], r0["sides"]) == ("Panel", "LDSP", 800, 400, 2, 1)
    assert client.get(f"/api/projects/{pid}/operations/{cs}/surface-usage").status_code == 400
    assert client.get(f"/api/projects/{pid}/operations/yoq/surface-usage").status_code == 404


def test_part_surface_patch_does_not_invalidate_cutting(client):
    """Sirt ishlovi bog'lanishi kroy natijasini eskirtirmaydi (kroyga ta'sir qilmaydi)."""
    pid, _prid, cs = _project(client, qty=1)
    ids, _ = _parts(client, pid, cs, [dict(name="A", length=500, width=400, qty=2)])
    _api(client, "post", f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    assert _op(_api(client, "get", f"/api/projects/{pid}"), cs)["result"] is not None
    oid, _p = _sp(client, pid)
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}", json=dict(surface_face_op=oid))
    assert _op(p, cs)["result"] is not None


# ───────────────────────── 5. eski JSON ─────────────────────────
def test_old_json_without_sp_fields_loads():
    raw = {"name": "eski", "operations": [{"type": "CS", "name": "L", "parts": [{"length": 100, "width": 100}]},
                                          {"type": "SP", "name": "Bo'yoq"}],
           "products": [{"name": "m"}]}
    p = Project.model_validate(raw)
    assert p.operations[1].sp is None and p.operations[0].parts[0].surface_face_op is None
    p = calc.recalc_project(p)                                     # sp bo'lmasa — standart parametrlar yaratiladi
    assert p.operations[1].sp == SPParams()
    assert p.products[0].program == [] and p.products[0].par_values == {}


def test_legacy_out_of_range_sp_values_are_clamped():
    raw = {"name": "e", "operations": [{"type": "SP", "sp": {"waste_percent": 500, "rest_side": -9, "size_mode": 7}}]}
    sp = Project.model_validate(raw).operations[0].sp
    assert (sp.waste_percent, sp.rest_side, sp.size_mode) == (100, 0, -1)


# ───────────────────────── 6. hisobot ─────────────────────────
def test_report_sections_and_print_switches(client):
    pid, _prid, cs = _project(client, qty=1)
    ids, _ = _parts(client, pid, cs, [dict(name="Fasad-1", length=900, width=500, qty=2)])
    oid, _p = _sp(client, pid, size_mode=0, price=300, op_price=200, waste_percent=5)
    _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}", json=dict(surface_face_op=oid))
    html = client.post(f"/api/projects/{pid}/report", json={}).text
    assert "(SP) Обработка поверхности" in html and "Fasad-1" in html and "Площадь обработки" in html
    assert "Требование на склад" in html and "SP" in html
    uz = client.post(f"/api/projects/{pid}/report?lang=uz", json={}).text
    assert "Sirt ishlovi" in uz and "Ishlov maydoni" in uz
    ps = client.get("/api/settings/print/default").json()
    assert ps["sp_params"] is True and ps["sp_parts"] is True
    no_params = client.post(f"/api/projects/{pid}/report", json={**ps, "sp_params": False}).text
    assert "Площадь обработки" not in no_params and "Fasad-1" in no_params
    no_parts = client.post(f"/api/projects/{pid}/report", json={**ps, "sp_parts": False}).text
    assert "Площадь обработки" in no_parts and "Fasad-1" not in no_parts.split("(SP)")[1]
    none = client.post(f"/api/projects/{pid}/report", json={**ps, "sp_params": False, "sp_parts": False}).text
    assert "(SP) Обработка поверхности" not in none


def test_report_escapes_names(client):
    pid, _prid, cs = _project(client, qty=1)
    ids, _ = _parts(client, pid, cs, [dict(name="<b>x</b>", length=100, width=100, qty=1)])
    oid, _p = _sp(client, pid)
    _api(client, "patch", f"/api/projects/{pid}/operations/{oid}", json={"name": "<script>1</script>"})
    _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}", json=dict(surface_face_op=oid))
    html = client.post(f"/api/projects/{pid}/report", json={}).text
    assert "<script>1</script>" not in html and "&lt;script&gt;" in html and "<b>x</b>" not in html


def test_mes_export_has_sp_numbers(client):
    pid, _prid, cs = _project(client, qty=1)
    ids, _ = _parts(client, pid, cs, [dict(name="A", length=1000, width=1000, qty=1)])
    oid, _p = _sp(client, pid, size_mode=0)
    _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{ids[0]}", json=dict(surface_face_op=oid))
    ex = _api(client, "get", f"/api/projects/{pid}/mes-export")
    sp = next(o for o in ex["operations"] if o["type"] == "SP")
    assert sp["area_m2"] == 1.0 and sp["material_m2"] == 1.0


# ───────────────────────── 7. etiketka o'zgaruvchilari ─────────────────────────
def test_label_vars_surf_front_back():
    sp1 = Operation(type=OpType.SP, name="Lak", code="L-1", sp=SPParams())
    sp2 = Operation(type=OpType.SP, name="Plyonka", code="P-9", sp=SPParams())
    pt = Part(uid=1, length=500, width=300, surface_face_op=sp1.id, surface_back_op=sp2.id)
    pt2 = Part(uid=2, length=500, width=300)
    cs = Operation(type=OpType.CS, name="LDSP", parts=[pt, pt2])
    project = Project(name="t", operations=[sp1, sp2, cs])
    eb = label_vars.EnvBuilder(project, label_vars.LBParams(), total=1)
    e = eb.env(label_vars.Item("part", op=cs, part=pt, part_index=1, copy=1, copies=1))
    assert e["surfFront"] == "Lak" and e["surfBack"] == "Plyonka"
    assert (e["surface.front.code"], e["surface.back.code"], e["surface.front.has"]) == ("L-1", "P-9", True)
    e2 = eb.env(label_vars.Item("part", op=cs, part=pt2, part_index=2, copy=1, copies=1))
    assert e2["surfFront"] == "" and e2["surfBack"] == "" and e2["surface.front.has"] is False
    from app.services import expr
    assert expr.evaluate("surfFront + '/' + surfBack", e) == "Lak/Plyonka"
    assert "surfFront" in label_vars.VAR_NAMES and "surface.back.name" in label_vars.VAR_NAMES


# ───────────────────────── 8. .project importi (sintetik; real korpusda SP yo'q) ─────────────────────────
def _project_xml(sp_attrs='spCalcMat="true" spWastePRC="10" spRestSide="15" spSizeMode="0" spCost="2500"',
                 sp_parts='<part id="11"/><part id="12"/>', extra_ops=""):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project name="SP import" currency="сум" version="1">
 <good id="1" typeId="product" name="Shkaf" count="2">
  <part id="11" dl="1000" dw="500" l="1000" w="500" count="2" name="Eshik"/>
  <part id="12" dl="800" dw="400" l="800" w="400" count="1" name="Yon"/>
 </good>
 <good id="2" typeId="sheet" code="LDSP16" name="LDSP 16" l="2750" w="1830" t="16" count="10"><part id="21" l="2750" w="1830" count="10000"/></good>
 <good id="3" typeId="tool.cutting" name="Arra" swSawthick="3"/>
 <good id="4" typeId="simple" code="LAK-1" name="Lak mat" unit="m2" cost="12000"/>
 <operation id="1" typeId="CS" tool1="3" cSizeMode="0"><material id="2" used="base"/><part id="11"/><part id="12"/></operation>
 <operation id="2" typeId="SP" typeName="Bo'yash" {sp_attrs} printable="true" startNewPage="false"><material id="4"/>{sp_parts}</operation>
 {extra_ops}
</project>""".encode("utf-8")


def test_import_sp_operation_and_part_links():
    from app.plugins.legacy_project import import_project
    p, warnings = import_project(_project_xml(), "sp.project")
    sp = next(o for o in p.operations if o.type == OpType.SP)
    assert (sp.name, sp.code) == ("Lak mat", "LAK-1")
    assert sp.sp.count_material is True and sp.sp.waste_percent == 10 and sp.sp.rest_side == 15
    assert sp.sp.size_mode == 0 and sp.sp.op_price == 2500 and sp.sp.price == 12000
    assert sp.new_page is False and sp.print is True
    cs = next(o for o in p.operations if o.type == OpType.CS)
    assert [pt.surface_face_op for pt in cs.parts] == [sp.id, sp.id]
    assert all(pt.surface_back_op is None for pt in cs.parts)
    assert any("SP" in w and "Lak mat" in w for w in warnings)              # tomon taxmin qilingani aytiladi
    calc.recalc_project(p)
    # ОК = 2 (mahsulot) × (2 + 1) ... : eshik 2×2=4 dona 0.5 m² + yon 1×2=2 dona 0.32 m²
    assert sp.sp.area_m2 == pytest.approx(4 * 0.5 + 2 * 0.32, abs=1e-4)


def test_import_second_sp_goes_to_back_side_and_missing_part_warns():
    from app.plugins.legacy_project import import_project
    extra = '<operation id="3" typeId="SP" typeName="Plyonka"><part id="11"/><part id="999"/></operation>'
    p, warnings = import_project(_project_xml(extra_ops=extra), "sp2.project")
    sps = [o for o in p.operations if o.type == OpType.SP]
    assert len(sps) == 2
    cs = next(o for o in p.operations if o.type == OpType.CS)
    eshik = next(pt for pt in cs.parts if pt.name == "Eshik")
    assert eshik.surface_face_op == sps[0].id and eshik.surface_back_op == sps[1].id
    assert any("999" in w for w in warnings)
    assert sps[1].name == "Plyonka" and sps[1].sp.size_mode == -1            # atribut yo'q — standart


def test_import_sp_missing_attributes_and_no_skip_warning():
    from app.plugins.legacy_project import import_project
    p, warnings = import_project(_project_xml(sp_attrs="", sp_parts=""), "sp3.project")
    sp = next(o for o in p.operations if o.type == OpType.SP)
    assert sp.sp.count_material is True and sp.sp.size_mode == -1 and sp.sp.op_price == 0
    assert not any("Пропущена операция SP" in w or "SP operatsiyasi o'tkazib" in w for w in warnings)


def test_import_via_api_roundtrip(client):
    r = client.post("/api/projects/import-file", files={"file": ("sp.project", _project_xml(), "application/xml")})
    assert r.status_code == 200, r.text
    p = r.json()["project"]
    sp = next(o for o in p["operations"] if o["type"] == "SP")
    assert sp["sp"]["area_m2"] == pytest.approx(2.0 + 0.64, abs=1e-4) and sp["cost_operation"] == pytest.approx(2.64 * 2500, abs=0.01)


# ───────────────────────── 9. Excel importi (W3) uchun bog'lanish nuqtasi ─────────────────────────
def test_find_or_create_and_attach_helpers():
    cs = Operation(type=OpType.CS, name="LDSP", parts=[Part(length=100, width=100)])
    project = Project(name="t", operations=[cs])
    a = sp_ops.find_or_create(project, "Lak mat")
    assert a.type == OpType.SP and a.sp is not None and a in project.operations
    assert sp_ops.find_or_create(project, "  lak MAT ") is a                 # katta-kichik harf va bo'sh joyga sezgirsiz
    assert len([o for o in project.operations if o.type == OpType.SP]) == 1
    pt = cs.parts[0]
    sp_ops.attach(pt, "front", a)
    sp_ops.attach(pt, "back", a)
    assert pt.surface_face_op == a.id and pt.surface_back_op == a.id
    sp_ops.attach(pt, "back", None)
    assert pt.surface_back_op is None
