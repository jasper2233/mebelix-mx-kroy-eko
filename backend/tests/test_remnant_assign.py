# Detallarni aniq qoldiqqa bog'lash (2026-10-25, foydalanuvchi talabi): «Остатки: расход» → «Детали на остаток» — avto
# (eng ko'p tejaydigan) yoki qo'lda tanlov, soni bilan; tanlangan detallar qoldiqqa sig'masa — «sig'maydi» va kroy to'xtaydi.
import uuid


def _setup(client, parts, rem=(2500, 650)):
    name = f"LDSP BIND {uuid.uuid4().hex[:6]}"
    pid = client.post("/api/projects", json={"name": "Bind"}).json()["id"]
    oid = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "name": name}).json()["operations"][-1]["id"]
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cs_material": {"thickness": 16}, "cs_cut": {"use_grain": False}})
    client.put(f"/api/projects/{pid}/operations/{oid}/sheets", json=[{"id": "full", "length": 2750, "width": 1830, "qty": 10000}])
    client.post(f"/api/projects/{pid}/operations/{oid}/parts",
                json=[dict(name=n, length=l, width=w, qty=q, grain=False) for n, l, w, q in parts])
    rid = client.post("/api/remnants", json={"material_code": name, "length": rem[0], "width": rem[1], "thickness": 16, "qty": 1}).json()["id"]
    op = next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)
    ids = {p["name"]: p["id"] for p in op["parts"]}
    return pid, oid, rid, ids


PARTS = [("Yon", 2385, 449, 1), ("Planka", 1400, 100, 2), ("Polka", 1400, 330, 2), ("Eshik", 459, 520, 3), ("Tom", 2385, 427, 1)]


def test_manual_assign_places_exactly_on_that_remnant(client):
    pid, oid, rid, ids = _setup(client, PARTS)
    view = client.get(f"/api/projects/{pid}/operations/{oid}/remnant-assign/{rid}").json()
    assert {r["name"] for r in view["parts"]} >= {"Yon", "Planka"}            # o'lchami bo'yicha sig'adiganlar
    r = client.post(f"/api/projects/{pid}/operations/{oid}/remnant-assign",
                    json={"remnant_id": rid, "parts": [{"id": ids["Yon"], "count": 1}, {"id": ids["Planka"], "count": 1}]})
    assert r.status_code == 200, r.text
    got = {x["name"]: x["count"] for x in r.json()["parts"]}
    assert got["Yon"] == 1 and got["Planka"] == 1
    op = next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)
    assert any(s["source_remnant_id"] == rid for s in op["sheets"])                    # qoldiq listlarga qo'shildi
    res = client.post(f"/api/projects/{pid}/operations/{oid}/optimize?quality=fast")
    assert res.status_code == 200, res.text
    res = res.json()
    rem_sheet = next(s["id"] for s in op["sheets"] if s["source_remnant_id"] == rid)
    on_rem = [pl["part_id"] for m in res["maps"] if m["sheet_id"] == rem_sheet for pl in m["placements"]]
    assert ids["Yon"] in on_rem and on_rem.count(ids["Planka"]) >= 1 and not res["unplaced"]


def test_assign_not_fitting_is_rejected_and_nothing_saved(client):
    pid, oid, rid, ids = _setup(client, PARTS)
    r = client.post(f"/api/projects/{pid}/operations/{oid}/remnant-assign",
                    json={"remnant_id": rid, "parts": [{"id": ids["Yon"], "count": 1}, {"id": ids["Tom"], "count": 1}]})
    assert r.status_code == 400 and ("не помещаются" in r.json()["detail"] or "sig'maydi" in r.json()["detail"])
    op = next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)
    assert all(p["remnant_id"] is None for p in op["parts"])
    assert not any(s["source_remnant_id"] == rid for s in op["sheets"])


def test_cut_stops_when_bound_parts_no_longer_fit(client):
    pid, oid, rid, ids = _setup(client, PARTS)
    client.post(f"/api/projects/{pid}/operations/{oid}/remnant-assign",
                json={"remnant_id": rid, "parts": [{"id": ids["Polka"], "count": 1}]})
    ok = client.post(f"/api/projects/{pid}/operations/{oid}/optimize?quality=fast")
    assert ok.status_code == 200
    # detal o'lchami kattalashdi — endi qoldiqqa sig'maydi: kroy to'xtaydi, natija o'zgarmaydi
    client.post(f"/api/projects/{pid}/operations/{oid}/parts/batch-update", json=[{"id": ids["Polka"], "fields": {"width": 700}}])
    before = next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)["result"]
    bad = client.post(f"/api/projects/{pid}/operations/{oid}/optimize?quality=fast")
    assert bad.status_code == 400 and str(rid) in bad.json()["detail"]
    after = next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)["result"]
    assert after == before


P4421 = [(f"D{u}", l, w, n) for u, l, w, n in [(1, 459, 520, 3), (2, 2385, 427, 1), (3, 2385, 449, 1), (4, 1400, 100, 2),
                                                (5, 1400, 70, 2), (6, 1377, 330, 2), (7, 1400, 330, 2), (8, 459, 485, 3)]]


def test_auto_selects_most_saving_set(client):
    # «4421»: qoldiqsiz 2 butun list; qoldiq 2500×650 + 1 list yetadi — avto tanlash shu to'plamni beradi
    pid, oid, rid, ids = _setup(client, P4421)
    a = client.post(f"/api/projects/{pid}/operations/{oid}/remnant-auto/{rid}").json()
    assert a["parts"] and a["saving"] is True
    r = client.post(f"/api/projects/{pid}/operations/{oid}/remnant-assign", json={"remnant_id": rid, "parts": a["parts"]})
    assert r.status_code == 200, r.text
    res = client.post(f"/api/projects/{pid}/operations/{oid}/optimize?quality=fast").json()
    assert not res["unplaced"] and len(res["maps"]) == 2                    # 1 butun list + qoldiq


def test_clear_assignment(client):
    pid, oid, rid, ids = _setup(client, PARTS)
    client.post(f"/api/projects/{pid}/operations/{oid}/remnant-assign", json={"remnant_id": rid, "parts": [{"id": ids["Yon"], "count": 1}]})
    client.post(f"/api/projects/{pid}/operations/{oid}/remnant-assign", json={"remnant_id": rid, "parts": []})
    op = next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)
    assert all(p["remnant_id"] is None and not p["from_remnant"] for p in op["parts"])


def test_auto_fallback_fills_remnant_when_no_saving(client):
    # qoldiqsiz ham 1 listga sig'adi — qoldiq tejamaydi; avto tanlash qoldiqni zich to'ldiradigan detallarni beradi
    pid, oid, rid, ids = _setup(client, PARTS)
    a = client.post(f"/api/projects/{pid}/operations/{oid}/remnant-auto/{rid}").json()
    assert a["saving"] is False and a["parts"]
