"""Detal soni oshirilsa / yangi detal qo'shilsa kroy saqlanadi (onlayn tizimdagidek, xodim loyihasi «1275», 2026-10-30):
ortgan detallar «kroyga kirmagan» (qizil) bo'ladi va «До кроить» bilan bo'sh joyga yoki yangi listga qo'shiladi.
O'lcham o'zgarsa yoki soni joylanganidan kam bo'lsa — kroy eskiradi (avvalgidek)."""


def _cs(p, cs):
    return next(o for o in p["operations"] if o["id"] == cs)


def _placed(op):
    return sorted((pl["part_id"], round(pl["x"]), round(pl["y"])) for m in op["result"]["maps"] for pl in m["placements"])


def test_qty_up_keeps_cut_and_rest_adds(client, kravat):
    pid, cs, _el = kravat
    op = _cs(client.get(f"/api/projects/{pid}").json(), cs)
    a, b = op["parts"][0], op["parts"][1]
    # 1) ikki detal soni 0 → kroy
    for pt in (a, b):
        client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{pt['id']}", json={"qty": 0})
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    op = _cs(client.get(f"/api/projects/{pid}").json(), cs)
    kept = _placed(op)
    # 2) soni qaytariladi — kroy o'chmaydi, detallar «kroyga kirmagan»
    p = client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{a['id']}", json={"qty": a["qty"]}).json()
    p = client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{b['id']}", json={"qty": b["qty"]}).json()
    op = _cs(p, cs)
    assert op["result"] is not None
    assert _placed(op) == kept
    left = {pt["id"]: pt["left_qty"] for pt in op["parts"]}
    assert left[a["id"]] == a["qty"] and left[b["id"]] == b["qty"]
    # 3) yangi detal qo'shilsa ham kroy saqlanadi
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[dict(name="sokl", length=1360, width=100, qty=1)]).json()
    op = _cs(p, cs)
    assert op["result"] is not None
    new = op["parts"][-1]
    assert new["left_qty"] == 1
    # 4) «До кроить» — avvalgilar o'z joyida, qolganlari qo'shiladi
    r = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?only_remaining=true&quality=fast")
    assert r.status_code == 200, r.text
    op = _cs(client.get(f"/api/projects/{pid}").json(), cs)
    assert set(kept) <= set(_placed(op))
    assert all(pt["left_qty"] == 0 for pt in op["parts"])


def test_size_change_or_qty_below_placed_invalidates(client, kravat):
    pid, cs, _el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    op = _cs(client.get(f"/api/projects/{pid}").json(), cs)
    a = op["parts"][0]
    p = client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{a['id']}", json={"name": "yangi nom"}).json()
    assert _cs(p, cs)["result"] is not None                      # nom — kroyga ta'sirsiz
    p = client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{a['id']}", json={"qty": 0}).json()
    assert _cs(p, cs)["result"] is None                          # joylanganidan kam
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{a['id']}", json={"qty": a["qty"]})
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    p = client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{a['id']}", json={"length": a["length"] - 10}).json()
    assert _cs(p, cs)["result"] is None                          # o'lcham o'zgardi
