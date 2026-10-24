# Ombordagi qoldiq taklifi va «Из остатка» detallari (2026-10-24, foydalanuvchi talabi va qoidasi): kesish doim butun
# listlardan boshlanadi; kroydan keyin oxirgi butun listdagi detallar omborda shu materialdan bor qoldiqqa sig'ishi mumkin bo'lsa —
# tizim taklif qiladi (`remnant-offer`), xodim qabul qilsa `from-remnants` bilan qo'shiladi va qayta kesiladi.
import uuid


def _mk(client, name=None, thickness=16):
    name = name or f"LDSP-OFFER-{uuid.uuid4().hex[:6]}"
    pid = client.post("/api/projects", json={"name": "Offer"}).json()["id"]
    op = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "name": name}).json()["operations"][-1]
    oid = op["id"]
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cs_material": {"thickness": thickness}})
    client.put(f"/api/projects/{pid}/operations/{oid}/sheets", json=[{"id": "full", "length": 2750, "width": 1830, "qty": 10000}])
    return pid, oid, name


def _rem(client, code, length, width, thickness=16, qty=1):
    r = client.post("/api/remnants", json={"material_code": code, "length": length, "width": width, "thickness": thickness, "qty": qty})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _cut(client, pid, oid):
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize?quality=fast")
    assert r.status_code == 200, r.text
    return r.json()


def test_offer_after_cut_for_last_sheet_parts_and_accept(client):
    pid, oid, name = _mk(client)
    client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=[{"name": "A", "length": 1000, "width": 600, "qty": 9}])
    assert client.get(f"/api/projects/{pid}/operations/{oid}/remnant-offer").json()["rows"] == []   # kroygacha — taklif yo'q
    small = _rem(client, name, 2100, 1300)             # oxirgi listdagi 3 detal (tekstura — aylantirilmaydi) sig'adi
    _rem(client, name, 1500, 1300)                     # maydon yetadi, lekin 3 detal joylanmaydi — taklif qilinmaydi
    _rem(client, name, 700, 500)                       # oxirgi list detali sig'maydi
    _rem(client, name, 2100, 1300, thickness=18)       # boshqa qalinlik
    _rem(client, "BOSHQA-" + name, 2100, 1300)         # boshqa material
    res = _cut(client, pid, oid)
    assert res["total_sheets"] == 2 and all(m["sheet_id"] == "full" for m in res["maps"])   # kesish butun listlardan
    d = client.get(f"/api/projects/{pid}/operations/{oid}/remnant-offer").json()
    assert [r["id"] for r in d["rows"]] == [small] and d["tail"]["map"] == 2 and d["tail"]["parts"] >= 1
    # qabul: qoldiq qo'shiladi va qayta kesiladi — 1 butun list + qoldiq (butun list avval, qoldiq oxirida)
    assert client.post(f"/api/projects/{pid}/operations/{oid}/sheets/from-remnants", json={"ids": [small]}).status_code == 200
    res = _cut(client, pid, oid)
    ids = [m["sheet_id"] for m in res["maps"]]
    assert ids[0] == "full" and ids.count("full") == 1 and len(ids) == 2 and ids[1] != "full" and not res["unplaced"]
    assert client.get(f"/api/projects/{pid}/operations/{oid}/remnant-offer").json()["rows"] == []      # butun list oxiri yo'q
    # boshqa loyiha band qilingan qoldiqni ko'rmaydi
    pid2, oid2, _n = _mk(client, name)
    client.post(f"/api/projects/{pid2}/operations/{oid2}/parts", json=[{"name": "B", "length": 1000, "width": 600, "qty": 9}])
    _cut(client, pid2, oid2)
    assert small not in [r["id"] for r in client.get(f"/api/projects/{pid2}/operations/{oid2}/remnant-offer").json()["rows"]]


def test_from_remnant_parts_go_to_remnant(client):
    pid, oid, name = _mk(client)
    parts = [{"name": "Q", "length": 600, "width": 300, "qty": 2, "from_remnant": True},
             {"name": "F", "length": 1000, "width": 600, "qty": 4}]
    client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=parts)
    sheets = [{"id": "rem", "length": 1300, "width": 700, "qty": 1, "is_remnant": True},
              {"id": "full", "length": 2750, "width": 1830, "qty": 10000}]
    assert client.put(f"/api/projects/{pid}/operations/{oid}/sheets", json=sheets).status_code == 200
    res = _cut(client, pid, oid)
    op = next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)
    q = next(p["id"] for p in op["parts"] if p["name"] == "Q")
    on_rem = [pl for m in res["maps"] if m["sheet_id"] == "rem" for pl in m["placements"]]
    assert sum(1 for pl in on_rem if pl["part_id"] == q) == 2 and not res["unplaced"]
    assert next(p for p in op["parts"] if p["name"] == "Q")["from_remnant"] is True
    assert res["maps"][0]["sheet_id"] == "full" and res["maps"][-1]["sheet_id"] == "rem"      # butun list avval
