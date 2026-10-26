# «Минимальный размер детали» (2026-10-26, onlayn tizimda jonli tekshirildi): shundan kichik detal bo'lsa kroy BAJARILMAYDI —
# «Размер детали N8 меньше ограничения "Минимальный размер детали"=30.0!» (N — detal qatori raqami). Avval MX detalni jimgina
# chetga qoldirib qolganini kesardi. Sintetik detallar.


def test_small_part_blocks_cut(client):
    p = client.post("/api/projects", json={"name": "min detal"}).json()
    p = client.post(f"/api/projects/{p['id']}/operations", json={"type": "CS", "name": "LDSP"}).json()
    pid, oid = p["id"], p["operations"][-1]["id"]
    client.put(f"/api/projects/{pid}/operations/{oid}/sheets", json=[{"length": 2750, "width": 1830, "qty": 10000}])
    client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=[dict(name="Bok", length=700, width=500, qty=2),
                                                                     dict(name="Mayda", length=300, width=25, qty=4)])
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize", params={"quality": "fast"})
    assert r.status_code == 400 and "N2" in r.json()["detail"] and "30" in r.json()["detail"]
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cs_material": {"min_part_size": 20}})
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize", params={"quality": "fast"})
    assert r.status_code == 200 and not r.json()["unplaced"]
