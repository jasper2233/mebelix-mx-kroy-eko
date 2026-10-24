# Loyiha saqlash versiyasi (`rev`, 2026-10-23): har o'zgarishda +1 — brauzer kechikib kelgan eski javobni keshga yozmaydi
# (tunnel orqali EL parametrlari ketma-ket saqlanganda oldingi PATCH javobi keyingisidan keyin kelib, ekranda yangi
# qiymat eskisiga qaytib qolardi; bazada esa to'g'ri saqlangan edi).
from app import store


def test_rev_increments_on_each_change_and_is_returned(client):
    pid = client.post("/api/projects", json={"name": "REV"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "name": "kromka"}).json()
    oid = p["operations"][0]["id"]
    r0 = p["rev"]
    r1 = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"el": {"overhang": 30}}).json()
    r2 = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"el": {"min_glue_length": 120}}).json()
    assert r0 < r1["rev"] < r2["rev"]
    got = client.get(f"/api/projects/{pid}").json()
    assert got["rev"] == r2["rev"]
    el = got["operations"][0]["el"]
    assert (el["overhang"], el["min_glue_length"]) == (30, 120)


def test_rev_not_taken_from_client_and_unchanged_save_keeps_it(client):
    pid = client.post("/api/projects", json={"name": "REV2"}).json()["id"]
    p = store.load(pid)
    rev = p.rev
    p.rev = 999                                     # mijoz / tarixdan kelgan qiymat — e'tiborsiz
    store.save(p, skip_unchanged=True)
    assert store.load(pid).rev == rev               # ma'lumot o'zgarmadi — versiya ham
    p = store.load(pid)
    p.name = "REV2b"
    store.save(p)
    assert store.load(pid).rev == rev + 1
