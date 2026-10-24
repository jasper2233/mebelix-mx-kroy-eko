"""TAB bilan qo'shilgan qator brauzerda darhol ko'rinadi — id ni brauzer beradi; server uni saqlaydi, band bo'lsa yangisini beradi."""


def _cs(c):
    pid = c.post("/api/projects", json={"name": "CID"}).json()["id"]
    p = c.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "L16", "name": "L"}).json()
    return pid, p["operations"][0]["id"]


def test_client_id_kept_and_collision_replaced(client):
    pid, cs = _cs(client)
    r = client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[{"id": "a1b2c3d4e5f6", "name": "", "length": 0, "width": 0}])
    assert r.status_code == 200
    ids = [x["id"] for x in r.json()["operations"][0]["parts"]]
    assert ids == ["a1b2c3d4e5f6"]
    r = client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[{"id": "a1b2c3d4e5f6", "name": "", "length": 0, "width": 0}])
    ids = [x["id"] for x in r.json()["operations"][0]["parts"]]
    assert len(ids) == 2 and len(set(ids)) == 2
