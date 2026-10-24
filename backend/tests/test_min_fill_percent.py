"""«МЗап» — list qatorining minimal to'ldirish foizi: shu listdagi karta to'ldirishi chegaradan past bo'lsa, list ishlatilmaydi."""


def _setup(client, min_fill):
    pid = client.post("/api/projects", json={"name": "MZap"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "name": "LDSP"}).json()
    cs = p["operations"][0]["id"]
    client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[{"name": "A", "length": 500, "width": 400, "qty": 3}])   # hammasi qoldiqqa sig'adi (eng kam material qoidasi)
    sheets = [
        {"length": 1200, "width": 900, "qty": 1, "is_remnant": True, "min_fill_percent": min_fill},   # 3 detal ≈ 56 %
        {"length": 2750, "width": 1830, "qty": 10000},
    ]
    r = client.put(f"/api/projects/{pid}/operations/{cs}/sheets", json=sheets)
    assert r.status_code == 200, r.text
    return pid, cs


def _maps(client, pid, cs):
    r = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    assert r.status_code == 200, r.text
    op = next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == cs)
    small = next(s["id"] for s in op["sheets"] if s["length"] == 1200)
    return op, [m for m in op["result"]["maps"] if m["sheet_id"] == small]


def test_low_fill_remnant_is_skipped(client):
    pid, cs = _setup(client, 95)
    op, small = _maps(client, pid, cs)
    assert all(m["fill_percent"] >= 95 for m in small)
    assert not op["result"]["unplaced"]


def test_without_limit_remnant_is_used(client):
    pid, cs = _setup(client, None)
    _op, small = _maps(client, pid, cs)
    assert small, "cheklov bo'lmasa qoldiq listi ishlatiladi (ustuvor)"
