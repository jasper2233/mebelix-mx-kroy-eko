# Polosa cheklovlari har qanday qidiruv yo'lida bajariladi (2026-10-26 audit): «Минимальная / Максимальная ширина полосы» va
# «Максимальная длина полосы» — kartadagi birinchi daraja bo'laklari (chiqindidan tashqari). Sintetik detallar.
import pytest

PARTS = [("Bok", 2000, 560, 2), ("Tom", 1168, 560, 2), ("Polka", 1136, 540, 4), ("Eshik", 1996, 397, 4), ("Planka", 1136, 100, 3),
         ("Yashik old", 500, 160, 6), ("Yashik yon", 450, 140, 12), ("Tor", 1900, 60, 2)]


def _cut(client, **cut):
    p = client.post("/api/projects", json={"name": "strip limits"}).json()
    p = client.post(f"/api/projects/{p['id']}/operations", json={"type": "CS", "name": "LDSP"}).json()
    pid, oid = p["id"], p["operations"][-1]["id"]
    client.put(f"/api/projects/{pid}/operations/{oid}/sheets", json=[{"length": 2750, "width": 1830, "qty": 10000}])
    client.post(f"/api/projects/{pid}/operations/{oid}/parts",
                json=[dict(name=n, length=l, width=w, qty=q, grain=False) for n, l, w, q in PARTS])
    assert client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cs_cut": cut}).status_code == 200
    for q in ("fast", "normal"):
        r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize", params={"quality": q})
        assert r.status_code == 200, r.text
        yield r.json()


def _strips(res):
    for m in res["maps"]:
        root = m["strips"][0]
        ax = root["a"]
        for c in root["c"]:
            if c["k"] != "W":
                yield m["index"], (c["l"] if ax == "x" else c["w"]), (root["w"] if ax == "x" else root["l"])


@pytest.mark.parametrize("mins,maxs", [(400, 0), (0, 600), (150, 700)])
def test_strip_width_limits(client, mins, maxs):
    for res in _cut(client, min_strip_width=mins, max_strip_width=maxs):
        assert res["maps"]
        for idx, a, _cross in _strips(res):
            assert not mins or a >= mins - 0.01, (idx, a)
            assert not maxs or a <= maxs + 0.01, (idx, a)


def test_max_strip_length(client):
    for res in _cut(client, max_strip_length=1900):
        for idx, _a, cross in _strips(res):
            assert cross <= 1900 + 0.01, (idx, cross)
