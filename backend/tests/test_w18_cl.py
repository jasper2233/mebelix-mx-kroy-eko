"""W18 — (CL) W11 bo'shliqlari: detal «Свойства» (batch-update, CL himoyasi), «Групповые действия» (SP / CL ga ko'chirish),
CL etiketka o'zgaruvchilari (`label_vars`, LB operatsiyasi), «Варианты» (kam material / kam sarf / kam kesim / maksimal sifat),
«До кроить» (mavjud kartalar saqlanadi, qolgan detallar yangi polosalarga)."""
import pytest

from app.services import cl_calc, cl_optimizer as co
from app.services import label_vars
from app.models import CLParams, OpType, StockSheet


def _new_project(client, name="W18 CL"):
    return client.post("/api/projects", json={"name": name}).json()["id"]


def _add_cl(client, pid, name="Profil 40x20", **cl):
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CL", "name": name, "code": "PR-40"}).json()
    oid = p["operations"][-1]["id"]
    if cl:
        client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cl": cl})
    return oid


def _op(client, pid, oid):
    p = client.get(f"/api/projects/{pid}").json()
    return next(o for o in p["operations"] if o["id"] == oid), p


def _parts(client, pid, oid, lengths):
    body = [dict(name=f"P{i}", length=L, width=0, qty=q) for i, (L, q) in enumerate(lengths, 1)]
    return client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=body).json()


@pytest.fixture()
def cl_job(client):
    pid = _new_project(client)
    oid = _add_cl(client, pid, width=100, kerf=3, trim=10, price=1000, waste_min=100, business_min=500)
    _parts(client, pid, oid, [(1000, 4), (750, 3), (1200, 2), (430, 5), (2150, 2)])
    return pid, oid


# ───────────────────────── detal «Свойства» (CL) ─────────────────────────
def test_cl_part_properties_batch_update_keeps_strip_width(client, cl_job):
    pid, oid = cl_job
    op, p = _op(client, pid, oid)
    part = op["parts"][0]
    el = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "name": "PVC 2/19"}).json()["operations"][-1]["id"]
    r = client.post(f"/api/projects/{pid}/operations/{oid}/parts/batch-update", json=[dict(id=part["id"], fields=dict(
        name="Plintus A", description="izoh", code="K-7", width=777, grain=True, edge_left=dict(op_id=el), qty=6))])
    assert r.status_code == 200, r.text
    got = next(x for x in next(o for o in r.json()["operations"] if o["id"] == oid)["parts"] if x["id"] == part["id"])
    assert got["name"] == "Plintus A" and got["description"] == "izoh" and got["code"] == "K-7" and got["qty"] == 6
    assert got["edge_left"]["op_id"] == el
    assert got["width"] == 0 and got["grain"] is False                   # CL: eni — polosa eni, tekstura ma'nosiz


def test_cl_part_name_change_keeps_result(client, cl_job):
    pid, oid = cl_job
    client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    op, _p = _op(client, pid, oid)
    part = op["parts"][0]
    client.post(f"/api/projects/{pid}/operations/{oid}/parts/batch-update", json=[dict(id=part["id"], fields=dict(name="Yangi"))])
    op, _p = _op(client, pid, oid)
    assert op["result"] is not None                                      # nom kroyni eskirtirmaydi
    client.post(f"/api/projects/{pid}/operations/{oid}/parts/batch-update", json=[dict(id=part["id"], fields=dict(length=999))])
    op, _p = _op(client, pid, oid)
    assert op["result"] is None                                          # uzunlik — eskirtiradi


# ───────────────────────── «Групповые действия»: SP va CL ─────────────────────────
def test_group_update_sp_binding_validates_and_keeps_result(client, cl_job):
    pid, oid = cl_job
    client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    sp = client.post(f"/api/projects/{pid}/operations", json={"type": "SP", "name": "Lak"}).json()["operations"][-1]["id"]
    op, _p = _op(client, pid, oid)
    ids = [x["id"] for x in op["parts"][:3]]
    r = client.post(f"/api/projects/{pid}/operations/{oid}/parts/group-update", json=dict(ids=ids, fields=dict(surface_face_op=sp)))
    assert r.status_code == 200, r.text
    op, _p = _op(client, pid, oid)
    assert [x["surface_face_op"] for x in op["parts"][:3]] == [sp] * 3 and op["parts"][3]["surface_face_op"] is None
    assert op["result"] is not None                                      # SP bog'lash kroyni eskirtirmaydi
    bad = client.post(f"/api/projects/{pid}/operations/{oid}/parts/group-update",
                      json=dict(ids=ids, fields=dict(surface_back_op="yo'q")))
    assert bad.status_code == 400
    # olib tashlash
    client.post(f"/api/projects/{pid}/operations/{oid}/parts/group-update", json=dict(ids=ids, fields=dict(surface_face_op=None)))
    op, _p = _op(client, pid, oid)
    assert all(x["surface_face_op"] is None for x in op["parts"])
    # kroyga ta'sir qiladigan maydon — eskirtiradi; CL da eni / tekstura e'tiborsiz
    client.post(f"/api/projects/{pid}/operations/{oid}/parts/group-update",
                json=dict(ids=ids, fields=dict(qty=9, width=500, grain=True)))
    op, _p = _op(client, pid, oid)
    assert op["result"] is None and all(x["qty"] == 9 and x["width"] == 0 and x["grain"] is False for x in op["parts"][:3])


def test_group_update_sp_on_cs_and_move_to_cl(client, kravat):
    pid, cs, _el = kravat
    sp = client.post(f"/api/projects/{pid}/operations", json={"type": "SP", "name": "Lak"}).json()["operations"][-1]["id"]
    cl = _add_cl(client, pid, width=80)
    op, _p = _op(client, pid, cs)
    ids = [op["parts"][0]["id"], op["parts"][1]["id"]]
    assert client.post(f"/api/projects/{pid}/operations/{cs}/parts/group-update",
                       json=dict(ids=ids, fields=dict(surface_face_op=sp, surface_back_op=sp))).status_code == 200
    r = client.post(f"/api/projects/{pid}/operations/{cs}/parts/move-to/{cl}", json=dict(ids=ids))
    assert r.status_code == 200
    moved, _p = _op(client, pid, cl)
    assert len(moved["parts"]) == 2 and all(x["width"] == 0 for x in moved["parts"])
    assert all(x["surface_face_op"] == sp and x["surface_back_op"] == sp for x in moved["parts"])    # SP bog'lanishi ko'chishda saqlanadi


# ───────────────────────── CL etiketka o'zgaruvchilari ─────────────────────────
def test_label_vars_catalog_has_strip_group():
    names = {n for n, *_ in label_vars.VARS}
    assert {"strip.index", "strip.length", "strip.width", "strip.parts", "strip.fill", "strip.offcut", "strip.business",
            "strip.total", "strip.copies"} <= names
    assert label_vars.DEFAULTS["strip.length"] == 0.0 and label_vars.DEFAULTS["strip.business"] is False
    groups = {g["key"] for g in label_vars.variable_catalog("ru")}
    assert "strip" in groups


def test_lb_labels_for_cl_parts_and_wastes(client, cl_job):
    pid, oid = cl_job
    client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    lb = client.post(f"/api/projects/{pid}/operations", json={"type": "LB"}).json()["operations"][-1]["id"]
    client.patch(f"/api/projects/{pid}/operations/{lb}", json={"lb": {"part_each": True, "print_wastes": False}})   # har donaga etiketka
    n = client.get(f"/api/projects/{pid}/operations/{lb}/lb/count").json()
    assert n["parts"] == 16                                              # 4 + 3 + 2 + 5 + 2 dona — har biriga bitta etiketka
    rows = client.get(f"/api/projects/{pid}/operations/{lb}/lb/rows").json()
    assert rows["total"] == 16 and all(r["kind"] == "part" and r["width"] == 100 and r["material"] == "Profil 40x20" for r in rows["rows"])
    assert {r["length"] for r in rows["rows"]} == {1000, 750, 1200, 430, 2150} and all(r["map"] >= 1 for r in rows["rows"])
    # faqat shu CL operatsiyasi; qoldiq (otxod) etiketkalari
    client.patch(f"/api/projects/{pid}/operations/{lb}", json={"lb": {"cs_op_id": oid, "print_wastes": True, "waste_business_only": False}})
    n2 = client.get(f"/api/projects/{pid}/operations/{lb}/lb/count").json()
    assert n2["parts"] == 16 and n2["wastes"] >= 1
    html = client.get(f"/api/projects/{pid}/operations/{lb}/lb/labels").text
    assert html.count("class='lbl'") == n2["total"]


def test_cl_label_qr_scans_in_mes_with_strip_width(client, cl_job):
    """CL etiketkasining QR kodi MES skanerida detalni topadi: eni = polosa eni, qalinlik = cl.thickness (W18)."""
    pid, oid = cl_job
    client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    lb = client.post(f"/api/projects/{pid}/operations", json={"type": "LB"}).json()["operations"][-1]["id"]
    row = client.get(f"/api/projects/{pid}/operations/{lb}/lb/rows").json()["rows"][0]
    r = client.get(f"/api/mes/scan/{row['code']}")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["kind"] == "part" and d["part"]["width"] == 100 and d["part"]["thickness"] == 16
    assert d["material"]["op_id"] == oid and d["maps"]


def test_cl_env_builder_strip_variables(client, cl_job):
    from app import store
    from app.models import LBParams
    pid, oid = cl_job
    client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    project = store.load(pid)
    op = next(o for o in project.operations if o.id == oid)
    lb = LBParams(cs_op_id=oid, print_wastes=True, waste_business_only=False)
    eb = label_vars.EnvBuilder(project, lb, 0, "ru")
    items = list(label_vars.iter_items(project, lb))
    parts = [eb.env(i) for i in items if i.kind == "part"]
    m1 = op.result.maps[0]
    first = parts[0]
    assert first["strip.index"] == 1 and first["strip.total"] == len(op.result.maps)
    assert first["strip.length"] == m1.sheet_length == 6000 and first["strip.width"] == 100
    assert first["strip.parts"] == m1.parts_count and first["strip.fill"] == m1.fill_percent
    assert first["part.width"] == 100.0 and first["part.saw_width"] == 100.0           # CL: detal eni = polosa eni
    assert first["part.dims"].endswith("× 100 × 16") and first["material.thickness"] == 16.0
    assert first["map.index"] == 1 and first["strip.offcut"] >= 0
    assert any(p["strip.offcut"] > 0 for p in parts)
    wastes = [eb.env(i) for i in items if i.kind == "waste"]
    assert wastes and all(w["waste.width"] == 100 and w["strip.index"] >= 1 for w in wastes)
    # CS operatsiyasida bu o'zgaruvchilar bo'sh
    cs = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "name": "LDSP"}).json()["operations"][-1]["id"]
    client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[dict(name="d", length=700, width=400, qty=1)])
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    project = store.load(pid)
    lb2 = LBParams(cs_op_id=cs)
    e2 = label_vars.EnvBuilder(project, lb2, 0, "ru")
    row = e2.env(next(label_vars.iter_items(project, lb2)))
    assert row["strip.index"] == 0 and row["strip.length"] == 0.0 and row["strip.business"] is False


def test_cl_label_template_expressions_work(client, cl_job):
    """Etiketka shablon ifodalari CL o'zgaruvchilari bilan (`strip.length`, `strip.index`) xatosiz hisoblanadi."""
    from app.services import expr
    from app import store
    from app.models import LBParams
    pid, oid = cl_job
    client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    project = store.load(pid)
    lb = LBParams(cs_op_id=oid)
    eb = label_vars.EnvBuilder(project, lb, 0, "ru")
    env = eb.env(next(label_vars.iter_items(project, lb)))
    assert expr.evaluate("strip.index * 1000 + strip.length", env) == 7000
    assert expr.evaluate("part.saw_length + strip.offcut >= 0", env) is True


# ───────────────────────── «Варианты» ─────────────────────────
def test_cl_variants_endpoint_and_apply(client, cl_job):
    pid, oid = cl_job
    r = client.post(f"/api/projects/{pid}/operations/{oid}/variants")
    assert r.status_code == 200, r.text
    vs = r.json()
    assert [v["variant"] for v in vs] == ["material", "consumption", "cuts", "max"]        # quality=normal → «max» ham bor
    for v in vs:
        assert v["result"]["kind"] == "linear" and v["result"]["variant"] == v["variant"] and v["unplaced"] == 0
        assert v["sheets"] == v["result"]["total_sheets"] and v["maps"] == len(v["result"]["maps"])
        assert v["material_len_m"] == v["result"]["material_len_m"] and v["cuts"] == v["result"]["total_cuts"]
    by = {v["variant"]: v for v in vs}
    assert by["material"]["material_len_m"] <= min(v["material_len_m"] for v in vs if v["variant"] != "max") + 1e-9
    assert by["cuts"]["cuts"] <= by["material"]["cuts"] and by["cuts"]["cuts"] <= by["consumption"]["cuts"]
    cons = lambda v: v["material_len_m"] - v["business_len_m"]       # noqa: E731
    assert cons(by["consumption"]) <= cons(by["material"]) + 1e-9
    # loyiha o'zgarmadi (variantlar faqat hisob)
    op, _p = _op(client, pid, oid)
    assert op["result"] is None
    # tanlangan variant PUT result bilan saqlanadi: ИК/Ост hisoblanadi, variant belgisi saqlanadi
    pick = by["cuts"]
    assert client.put(f"/api/projects/{pid}/operations/{oid}/result", json=pick["result"]).status_code == 200
    op, _p = _op(client, pid, oid)
    assert op["result"]["variant"] == "cuts" and op["result"]["total_cuts"] == pick["cuts"]
    assert all(pt["used_qty"] == pt["qty"] and pt["left_qty"] == 0 for pt in op["parts"])
    # har variant tekshiruvdan o'tadi (validate_cl: PUT 200)
    for v in vs:
        assert client.put(f"/api/projects/{pid}/operations/{oid}/result", json=v["result"]).status_code == 200, v["variant"]


def test_cl_variants_skip_max_when_quality_is_max_and_need_parts(client):
    pid = _new_project(client)
    oid = _add_cl(client, pid, width=100, quality="max")
    assert client.post(f"/api/projects/{pid}/operations/{oid}/variants").status_code == 400          # detal yo'q
    _parts(client, pid, oid, [(900, 3), (1100, 2)])
    vs = client.post(f"/api/projects/{pid}/operations/{oid}/variants").json()
    assert [v["variant"] for v in vs] == ["material", "consumption", "cuts"]
    # CS da eski xulq: 3 variant (optimal / length / width)
    cs = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "name": "LDSP"}).json()["operations"][-1]["id"]
    client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[dict(name="d", length=700, width=400, qty=2)])
    assert [v["variant"] for v in client.post(f"/api/projects/{pid}/operations/{cs}/variants").json()] == ["optimal", "length", "width"]
    # CL emas / CS emas operatsiya: variantlar yo'q
    el = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "name": "k"}).json()["operations"][-1]["id"]
    assert client.post(f"/api/projects/{pid}/operations/{el}/variants").status_code == 400


def test_cl_variants_same_as_marks_identical_results(client):
    pid = _new_project(client)
    oid = _add_cl(client, pid, width=100, quality="max")
    _parts(client, pid, oid, [(2000, 3)])                                # bitta sxema — hamma variant bir xil
    vs = client.post(f"/api/projects/{pid}/operations/{oid}/variants").json()
    assert vs[0]["same_as"] is None and all(v["same_as"] == "material" for v in vs[1:])


def test_optimizer_objective_param_default_unchanged():
    """`objective` berilmasa natija avvalgidek (OBJECTIVE); berilsa — faqat tanlov tartibi o'zgaradi, hamma detal joylanadi."""
    cl = CLParams(kerf=3, trim=10, waste_min=100, business_min=500)
    st = [StockSheet(length=6000, width=cl.width, qty=10000)]
    items = [co.LItem(f"p{i}", i, L) for i, L in enumerate([1000] * 4 + [750] * 3 + [1200] * 2 + [430] * 5 + [2150] * 2, 1)]
    base = co.optimize_linear(items, st, cl, quality="normal")
    again = co.optimize_linear(items, st, cl, quality="normal")
    assert [(m.copies, [p.part_uid for p in m.placements]) for m in base.maps] == [(m.copies, [p.part_uid for p in m.placements]) for m in again.maps]
    for obj in co.OBJECTIVES:
        r = co.optimize_linear(items, st, cl, quality="normal", objective=obj)
        assert not r.unplaced and r.total_parts == len(items)
        assert co.validate_cl(r, items, st, cl) == []
    mat = co.optimize_linear(items, st, cl, objective="material")
    cuts = co.optimize_linear(items, st, cl, objective="cuts")
    assert mat.material_len_m <= cuts.material_len_m + 1e-9 and cuts.total_cuts <= mat.total_cuts


# ───────────────────────── «До кроить» ─────────────────────────
def _stock_of(op):
    return [dict(id=s["id"], length=s["length"], width=s["width"], qty=s["qty"], is_remnant=s["is_remnant"],
                 trim_length=s.get("trim_length", 0), trim_width=s.get("trim_width", 0)) for s in op["sheets"]]


@pytest.fixture()
def partial_cut(client):
    """Cheklangan bitta 3000 mm polosa: hamma detal sig'maydi → «Остаток» bor; so'ng yana polosalar qo'shiladi."""
    pid = _new_project(client)
    oid = _add_cl(client, pid, width=100, kerf=3, trim=10, waste_min=100, business_min=500)
    op, _p = _op(client, pid, oid)
    sid = op["sheets"][0]["id"]
    r = client.put(f"/api/projects/{pid}/operations/{oid}/sheets", json=[dict(id=sid, length=3000, width=100, qty=1)])
    assert r.status_code == 200, r.text
    _parts(client, pid, oid, [(1000, 2), (700, 3), (450, 4)])
    res = client.post(f"/api/projects/{pid}/operations/{oid}/optimize").json()
    assert res["unplaced"] and len(res["maps"]) == 1
    return pid, oid, res


def test_cl_remaining_cut_adds_maps_and_keeps_old(client, partial_cut):
    pid, oid, res0 = partial_cut
    op, _p = _op(client, pid, oid)
    first_uids = [pl["part_uid"] for pl in res0["maps"][0]["placements"]]
    # eski karta izohi / torsovkasi saqlanishi uchun izoh yoziladi
    client.patch(f"/api/projects/{pid}/operations/{oid}/maps/1", json={"comment": "birinchi"})
    # yangi polosalar qo'shiladi (oldingi natija saqlanadi)
    sheets = [dict(id=s["id"], length=s["length"], width=s["width"], qty=s["qty"]) for s in op["sheets"]]
    sheets.append(dict(length=6000, width=100, qty=10000))
    r = client.put(f"/api/projects/{pid}/operations/{oid}/sheets", json=sheets)
    assert r.status_code == 200
    op, _p = _op(client, pid, oid)
    assert op["result"] is not None and any(pt["left_qty"] > 0 for pt in op["parts"])
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize", params={"only_remaining": True})
    assert r.status_code == 200, r.text
    res = r.json()
    assert len(res["maps"]) >= 2 and not res["unplaced"] and res["kind"] == "linear"
    assert [pl["part_uid"] for pl in res["maps"][0]["placements"]] == first_uids              # birinchi karta o'zgarmadi
    assert res["maps"][0]["comment"] == "birinchi" and res["manual"] is False
    assert [m["index"] for m in res["maps"]] == list(range(1, len(res["maps"]) + 1))
    assert res["total_parts"] == 9 and res["total_sheets"] == sum(m["copies"] for m in res["maps"])
    op, _p = _op(client, pid, oid)
    assert all(pt["used_qty"] == pt["qty"] and pt["left_qty"] == 0 for pt in op["parts"])           # ИК / Ост
    assert op["sheets"][0]["used_qty"] == 1                                                         # cheklangan polosa 1 marta ishlatilgan
    # qoldiq (Д№) raqamlari butun natijada takrorlanmaydi
    nums = [o["number"] for m in res["maps"] for o in m["offcuts"] if o["kind"] == "remnant"]
    assert len(nums) == len(set(nums))
    # butun natija validate_cl dan o'tadi (qaytadan saqlash)
    assert client.put(f"/api/projects/{pid}/operations/{oid}/result", json=res).status_code == 200


def test_cl_remaining_cut_noop_and_without_result(client, cl_job):
    pid, oid = cl_job
    # kroy yo'q: «До кроить» oddiy «Раскроить» kabi ishlaydi
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize", params={"only_remaining": True})
    assert r.status_code == 200 and not r.json()["unplaced"]
    before = [(m["copies"], [pl["part_uid"] for pl in m["placements"]]) for m in r.json()["maps"]]
    # hammasi joylashgan: hech narsa o'zgarmaydi
    r2 = client.post(f"/api/projects/{pid}/operations/{oid}/optimize", params={"only_remaining": True}).json()
    assert [(m["copies"], [pl["part_uid"] for pl in m["placements"]]) for m in r2["maps"]] == before


def test_cl_remaining_cut_still_unplaced_when_no_stock(client, partial_cut):
    """Polosa qo'shilmasa — «До кроить» hech narsa qo'shmaydi, sig'magan detallar «Остаток» da qoladi."""
    pid, oid, res0 = partial_cut
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize", params={"only_remaining": True}).json()
    assert len(r["maps"]) == len(res0["maps"]) and len(r["unplaced"]) == len(res0["unplaced"])
    assert r["warnings"]                                                 # «polosa yetmadi» ogohlantirishi


def test_cl_remaining_via_calc_unit(client, partial_cut):
    """Birlik darajasida: `cl_calc.run_linear(only_remaining=True)` — qolgan ro'yxat tartibi saqlanadi, kartalar qo'shiladi."""
    from app import store
    pid, oid, _res0 = partial_cut
    p = store.load(pid)
    op = next(o for o in p.operations if o.id == oid)
    op.sheets.append(StockSheet(length=2000, width=100, qty=2))
    n0 = len(op.result.maps)
    cl_calc.run_linear(p, op, only_remaining=True)
    assert len(op.result.maps) > n0 and op.result.maps[0].sheet_id == op.sheets[0].id
    assert op.sheets[1].used_qty >= 1 and not op.result.unplaced
