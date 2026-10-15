"""W11 — (CL) Погонажный раскрой: REST API (operatsiya, detallar, polosalar, kroy, CLE, qoldiqlar, hisobot, MES)."""
import pytest

from app.models import PrintSettings


def _new_project(client, name="CL API"):
    return client.post("/api/projects", json={"name": name}).json()["id"]


def _add_cl(client, pid, name="Profil 40x20", **cl):
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CL", "name": name, "code": "PR-40"}).json()
    oid = p["operations"][-1]["id"]
    if cl:
        p = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cl": cl}).json()
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
    _parts(client, pid, oid, [(1000, 4), (750, 3), (1200, 2)])
    return pid, oid


def test_new_cl_operation_defaults(client):
    pid = _new_project(client)
    oid = _add_cl(client, pid)
    op, _p = _op(client, pid, oid)
    assert op["type"] == "CL" and op["cl"]["kerf"] == 3 and op["cl"]["trim"] == 10 and op["cl"]["width"] == 100
    assert op["cl"]["waste_min"] == 100 and op["cl"]["business_min"] == 1000 and op["cl"]["waste_incl_trim"] is True
    assert len(op["sheets"]) == 1 and op["sheets"][0]["length"] == 6000 and op["sheets"][0]["qty"] == 10000
    assert op["sheets"][0]["width"] == op["cl"]["width"]
    assert op["cs_cut"] is None and op["cs_material"] is None


def test_cl_defaults_scope_and_catalog_linear_item(client):
    """`cl_defaults` («Сохранить параметры по умолчанию») va katalogdagi погонажный tovar → yangi CL operatsiya."""
    r = client.put("/api/settings/cl_defaults/default", json={"kerf": 4, "trim": 12, "waste_min": 150, "usage_m": 99})
    assert r.status_code == 200, r.text
    d = client.get("/api/settings/cl_defaults/default").json()
    assert d["kerf"] == 4 and d["trim"] == 12 and d["usage_m"] == 0           # hisoblangan qiymat saqlanmaydi
    from app.db import CatalogItemRow, SessionLocal
    with SessionLocal() as s:
        s.merge(CatalogItemRow(id="cl-lin-1", kind="linear", code="PL-77", name="Plintus 77", price=2500, thickness=18,
                               length=3000, width=77, params={}))
        s.commit()
    pid = _new_project(client)
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CL", "material_id": "cl-lin-1"}).json()
    op = p["operations"][-1]
    assert op["code"] == "PL-77" and op["name"] == "Plintus 77"
    assert op["cl"]["kerf"] == 4 and op["cl"]["trim"] == 12 and op["cl"]["price"] == 2500
    assert op["cl"]["width"] == 77 and op["cl"]["thickness"] == 18
    assert op["sheets"][0]["length"] == 3000 and op["sheets"][0]["width"] == 77
    client.put("/api/settings/cl_defaults/default", json={})                    # boshqa testlarga ta'sir qilmasin


def test_cl_op_without_params_gets_defaults_and_old_json(client):
    from app.models import Operation, OpType, Project
    p = Project.model_validate({"name": "eski", "operations": [{"type": "CL", "name": "eski CL"}]})
    assert p.operations[0].type == OpType.CL and p.operations[0].cl is not None and p.operations[0].cl.kerf == 3
    op = Operation.model_validate({"type": "CS", "name": "x"})
    assert op.cl is None and op.result is None


def test_cl_kerf_must_be_positive_and_width_follows_sheets(client):
    pid = _new_project(client)
    oid = _add_cl(client, pid)
    r = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cl": {"kerf": 0}})
    assert r.status_code in (400, 422)
    p = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cl": {"width": 45}}).json()
    op = next(o for o in p["operations"] if o["id"] == oid)
    assert op["sheets"][0]["width"] == 45                      # polosa eni = cl.width


def test_cl_add_parts_forces_zero_width_and_no_grain(client):
    pid = _new_project(client)
    oid = _add_cl(client, pid)
    p = client.post(f"/api/projects/{pid}/operations/{oid}/parts",
                    json=[dict(name="x", length=500, width=300, qty=2, grain=True)]).json()
    pt = next(o for o in p["operations"] if o["id"] == oid)["parts"][0]
    assert pt["width"] == 0 and pt["grain"] is False and pt["length"] == 500


def test_estimate_before_cut_then_optimize(client, cl_job):
    pid, oid = cl_job
    op, _p = _op(client, pid, oid)
    sigma = (1000 * 4 + 750 * 3 + 1200 * 2) / 1000                                # 8.65 m
    assert abs(op["cl"]["usage_m"] - sigma * 1.1) < 1e-3                          # kroygacha: Σ × (2 − 90 / 100)
    assert abs(op["cost_material"] - sigma * 1.1 * 1000) < 1.0
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["kind"] == "linear" and res["total_parts"] == 9 and not res["unplaced"]
    m = res["maps"][0]
    assert m["sheet_width"] == 100 and all(pl["y"] == 0 and pl["width"] == 100 and not pl["rotated"] for pl in m["placements"])
    op, _p = _op(client, pid, oid)
    assert all(pt["used_qty"] == pt["qty"] and pt["left_qty"] == 0 for pt in op["parts"])      # ИК + Ост
    assert op["sheets"][0]["used_qty"] == res["total_sheets"]
    qty = res["material_len_m"] - res["business_len_m"]
    assert abs(op["cl"]["usage_m"] - qty) < 1e-3 and abs(op["cost_material"] - qty * 1000) < 1.0
    assert res["total_fill_percent"] > 0 and res["material_len_m"] == res["total_sheets"] * 6.0


def test_optimize_requires_parts_and_cl_only_endpoints(client):
    pid = _new_project(client)
    oid = _add_cl(client, pid)
    assert client.post(f"/api/projects/{pid}/operations/{oid}/optimize").status_code == 400      # detallar yo'q
    assert client.post(f"/api/projects/{pid}/operations/{oid}/variants").status_code == 400       # detallar yo'q (W18: CL da variantlar bor — test_w18_cl.py)
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "name": "LDSP"}).json()
    cs = p["operations"][-1]["id"]
    assert client.get(f"/api/projects/{pid}/operations/{cs}/cl-quantities").status_code == 400
    q = client.get(f"/api/projects/{pid}/operations/{oid}/cl-quantities")
    assert q.status_code == 200 and q.json()["estimated"] is True


def test_cut_params_invalidate_result_price_does_not(client, cl_job):
    pid, oid = cl_job
    client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    p = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cl": {"price": 2000, "op_price": 5, "quality": "fast"}}).json()
    assert next(o for o in p["operations"] if o["id"] == oid)["result"] is not None
    p = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cl": {"kerf": 4}}).json()
    op = next(o for o in p["operations"] if o["id"] == oid)
    assert op["result"] is None and all(pt["used_qty"] == 0 for pt in op["parts"])


def test_parts_change_invalidates_and_ctrl_m_move_between_cs_cl(client, cl_job):
    pid, oid = cl_job
    client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    p = _parts(client, pid, oid, [(300, 1)])
    assert next(o for o in p["operations"] if o["id"] == oid)["result"] is None
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "name": "LDSP"}).json()
    cs = p["operations"][-1]["id"]
    cs_part = client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[dict(name="d", length=700, width=400, qty=1)]).json()
    part = next(o for o in cs_part["operations"] if o["id"] == cs)["parts"][0]
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/move-to/{oid}", json={"ids": [part["id"]]}).json()
    moved = next(pt for pt in next(o for o in p["operations"] if o["id"] == oid)["parts"] if pt["id"] == part["id"])
    assert moved["width"] == 0                                   # CS dan kelgan eni CL da saqlanmaydi


def test_cle_edit_actions_and_save(client, cl_job):
    pid, oid = cl_job
    res = client.post(f"/api/projects/{pid}/operations/{oid}/optimize").json()
    base = f"/api/projects/{pid}/operations/{oid}/edit"

    def act(draft, **a):
        r = client.post(base, json={"result": draft, "action": a})
        return r

    draft = res
    first = draft["maps"][0]
    n0 = len(first["placements"])
    # olib tashlash: detal «Остаток» ga qaytadi (unplaced ro'yxatiga)
    r = act(draft, type="remove", map=1, index=0)
    assert r.status_code == 200, r.text
    d1 = r.json()
    assert len(d1["maps"][0]["placements"]) == n0 - 1 and len(d1["unplaced"]) >= 1 and d1["manual"] is True
    # qaytarib qo'yish
    uid_removed = first["placements"][0]["part_uid"]
    d2 = act(d1, type="place", map=1, uid=uid_removed).json()
    assert len(d2["maps"][0]["placements"]) == n0 and not d2["unplaced"]
    # ko'chirish: boshiga / oxiriga
    d3 = act(d2, type="move", map=1, index=0, to="end").json()
    assert d3["maps"][0]["placements"][-1]["part_uid"] == d2["maps"][0]["placements"][0]["part_uid"]
    xs = [p["x"] for p in d3["maps"][0]["placements"]]
    assert xs == sorted(xs)                                      # koordinatalar serverda qayta hisoblanadi
    # bo'sh karta qo'shish, detalni o'sha yerga ko'chirish (nusxalar teng bo'lganda)
    d4 = act(d3, type="add_map").json()
    assert len(d4["maps"]) == len(d3["maps"]) + 1 and d4["maps"][-1]["placements"] == []
    # artiqcha detalni qo'yib bo'lmaydi
    r = act(d3, type="place", map=1, uid=uid_removed)
    assert r.status_code == 422
    r = act(d4, type="place", map=len(d4["maps"]), uid=uid_removed)
    assert r.status_code == 422                                  # barcha nusxalar allaqachon joylashgan
    # torsovka (Торцовка листа): shu polosaga alohida
    d5 = act(d3, type="trims", map=1, trim_start=0, trim_end=0).json()
    assert d5["maps"][0]["trim_length"] == 0 and d5["maps"][0]["end_offset_right"] == 0
    r = act(d3, type="trims", map=1, trim_start=999)
    assert r.status_code == 422
    # polosalar soni (C) va izoh
    d6 = act(d3, type="copies", map=1, copies=1).json()
    assert d6["maps"][0]["copies"] == 1
    d7 = act(d3, type="comment", map=1, comment="Shoshilinch").json()
    assert d7["maps"][0]["comment"] == "Shoshilinch"
    assert act(d3, type="copies", map=1, copies=0).status_code == 422
    # saqlash: PUT result → ИК/Ост, narx qayta hisoblanadi
    r = client.put(f"/api/projects/{pid}/operations/{oid}/result", json=d7)
    assert r.status_code == 200, r.text
    op, _p = _op(client, pid, oid)
    assert op["result"]["manual"] is True and op["result"]["maps"][0]["comment"] == "Shoshilinch"
    assert all(pt["left_qty"] == 0 for pt in op["parts"])
    # bo'sh karta bilan saqlab bo'lmaydi
    assert client.put(f"/api/projects/{pid}/operations/{oid}/result", json=d4).status_code == 422


def test_cle_edit_rev_conflict(client, cl_job):
    pid, oid = cl_job
    res = client.post(f"/api/projects/{pid}/operations/{oid}/optimize").json()
    rev = client.get(f"/api/projects/{pid}/operations/{oid}/cl-edit/rev").json()["rev"]
    d = client.post(f"/api/projects/{pid}/operations/{oid}/edit",
                    json={"result": res, "action": {"type": "comment", "map": 1, "comment": "a"}}).json()
    assert client.put(f"/api/projects/{pid}/operations/{oid}/result", params={"base": rev}, json=d).status_code == 200
    assert client.put(f"/api/projects/{pid}/operations/{oid}/result", params={"base": rev}, json=d).status_code == 409


def test_remnants_linear_commit_picker_rollback(client):
    pid = _new_project(client)
    oid = _add_cl(client, pid, width=60, kerf=3, trim=10, waste_min=100, business_min=500)
    _parts(client, pid, oid, [(1000, 3)])
    res = client.post(f"/api/projects/{pid}/operations/{oid}/optimize").json()
    assert res["business_len_m"] > 2.0
    info = client.get(f"/api/projects/{pid}/operations/{oid}/remnants").json()
    assert info["remnants"] and info["remnants"][0]["width"] == 60 and info["remnants"][0]["length"] > 2000   # xom o'lcham, almashtirilmagan
    out = client.post(f"/api/projects/{pid}/operations/{oid}/remnants/commit")
    assert out.status_code == 200, out.text
    rid = out.json()["added"][0]["id"]
    assert out.json()["added"][0]["linear"] is True
    lin = client.get("/api/remnants", params={"linear": True}).json()
    assert any(r["id"] == rid for r in lin)
    assert not any(r["id"] == rid for r in client.get("/api/remnants", params={"linear": False}).json())
    # boshqa CL operatsiyaga qo'shiladi va birinchi ishlatiladi; CS ga qo'shib bo'lmaydi
    pid2 = _new_project(client, "CL 2")
    oid2 = _add_cl(client, pid2, width=60, kerf=3, trim=10)
    _parts(client, pid2, oid2, [(900, 2)])
    r = client.post(f"/api/projects/{pid2}/operations/{oid2}/sheets/from-remnants", json={"ids": [rid]})
    assert r.status_code == 200, r.text
    op2, _p = _op(client, pid2, oid2)
    assert op2["sheets"][0]["source_remnant_id"] == rid and op2["sheets"][0]["is_remnant"] and op2["sheets"][0]["width"] == 60
    res2 = client.post(f"/api/projects/{pid2}/operations/{oid2}/optimize").json()
    assert res2["maps"][0]["is_remnant"] is True
    cs = client.post(f"/api/projects/{pid2}/operations", json={"type": "CS", "name": "LDSP"}).json()["operations"][-1]["id"]
    assert client.post(f"/api/projects/{pid2}/operations/{cs}/sheets/from-remnants", json={"ids": [rid]}).status_code == 400
    # bekor qilish
    rb = client.post(f"/api/projects/{pid}/operations/{oid}/remnants/rollback")
    assert rb.status_code == 200
    # ikkinchi loyiha ishlatgan qoldiqni qaytarish — qator o'chirilgan bo'lsa ham xato bo'lmaydi
    assert client.post(f"/api/projects/{pid}/operations/{oid}/remnants/commit").status_code == 200
    client.delete(f"/api/projects/{pid2}")
    client.delete(f"/api/projects/{pid}")


def test_remnants_linear_column_migration(tmp_path, monkeypatch):
    """Eski bazada `remnants.linear` yo'q: `_migrate` ustunni qo'shadi, eski qatorlar listli (linear = false) bo'lib qoladi."""
    from sqlalchemy import create_engine, text
    from app import db
    eng = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE remnants (id INTEGER PRIMARY KEY AUTOINCREMENT, material_code VARCHAR(100), length FLOAT, "
                       "width FLOAT, thickness FLOAT, qty INTEGER, source_project VARCHAR(32), note TEXT)"))
        c.execute(text("INSERT INTO remnants (material_code, length, width, thickness, qty) VALUES ('LDSP', 1000, 500, 16, 2)"))
    monkeypatch.setattr(db, "engine", eng)
    db._migrate()
    with eng.begin() as c:
        assert c.execute(text("SELECT linear FROM remnants")).scalar() in (0, False)


def test_remnant_groups_and_taken_for_cl(client):
    pid = _new_project(client)
    oid = _add_cl(client, pid, width=60, kerf=3, trim=10, waste_min=100, business_min=500)
    _parts(client, pid, oid, [(1000, 3)])
    client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    g = client.get(f"/api/projects/{pid}/operations/{oid}/remnant-groups").json()["groups"]
    assert g and g[0]["business"] and g[0]["qty"] == 1
    r = client.put(f"/api/projects/{pid}/operations/{oid}/result/taken", json={"key": g[0]["key"], "qty": 1})
    assert r.status_code == 200
    info = client.get(f"/api/projects/{pid}/operations/{oid}/remnants").json()
    assert info["remnants"] == []                                # mijoz olib ketadigan bo'lak omborga yozilmaydi


def test_report_svg_warehouse_postprocess_mes(client, cl_job):
    pid, oid = cl_job
    client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    html = client.get(f"/api/projects/{pid}/report", params={"lang": "ru"}).text
    assert "(CL) Погонажный раскрой" in html
    assert "Полосы" in html and "<svg" in html
    uz = client.get(f"/api/projects/{pid}/report", params={"lang": "uz"}).text
    assert "(CL) Pogonaj kroy" in uz
    # chop sozlamalari: bo'limlarni o'chirish
    ps = PrintSettings(cl_parts=False, cl_strips=False, cl_remnants=False, cl_maps=False, cl_header=False).model_dump(mode="json")
    short = client.post(f"/api/projects/{pid}/report", json=ps).text
    assert "<svg" not in short and "Параметры" not in short
    ps2 = PrintSettings(cl_commands=True).model_dump(mode="json")
    assert "Кд" in client.post(f"/api/projects/{pid}/report", json=ps2).text
    svg = client.get(f"/api/projects/{pid}/operations/{oid}/maps/1.svg")
    assert svg.status_code == 200 and svg.text.startswith("<svg") and "Д" in svg.text
    wh = [r for r in client.get(f"/api/projects/{pid}/warehouse").json() if r["type"] == "CL"]
    assert wh and wh[0]["unit_code"] == "m" and wh[0]["qty"] > 0
    for key in ("csv", "commands", "json", "dxf"):
        r = client.get(f"/api/projects/{pid}/operations/{oid}/postprocess", params={"key": key})
        assert r.status_code == 200, (key, r.text[:200])


def test_mes_export_includes_cl(client, cl_job):
    pid, oid = cl_job
    client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    from app import store
    from app.services import mes
    data = mes.export(store.load(pid))
    op = next(o for o in data["operations"] if o["id"] == oid)
    assert op["kind"] == "linear" and op["strips"] >= 1 and op["material_len_m"] > 0 and op["maps"] and op["parts"]
    assert any(r["type"] == "CL" for r in data["warehouse"])
