"""«До кроить» onlayn tizimdagidek (2026-10-21): qolgan detallar avval mavjud kartalarning bo'sh joyiga, joylangan detallar
o'z joyida qoladi; sig'maganlari — yangi listlarga."""


def _leaves(n, out=None, path=()):
    out = [] if out is None else out
    for i, c in enumerate(n.get("c") or []):
        if c["k"] == "P":
            out.append((list(path) + [i], c))
        elif c["k"] == "C":
            _leaves(c, out, tuple(path) + (i,))
    return out


def _cs(p, cs):
    return next(o for o in p["operations"] if o["id"] == cs)


def test_rest_fills_free_space_of_existing_map(client, kravat):
    pid, cs, _el = kravat
    res = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").json()
    n_maps = len(res["maps"])
    m0 = res["maps"][0]
    parts = _leaves(m0["strips"][0])
    assert len(parts) >= 3
    # ikki detal olib tashlanadi (onlayndagidek: tahrir → «Ок»)
    paths = [parts[0][0], parts[1][0]]
    r = client.post(f"/api/projects/{pid}/operations/{cs}/edit",
                    json={"result": res, "action": {"type": "remove", "map": 1, "paths": paths}})
    assert r.status_code == 200, r.text
    d = r.json()
    assert len(d["unplaced"]) == 2
    p = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=d).json()
    kept = sorted((pl["part_id"], pl["x"], pl["y"]) for pl in _cs(p, cs)["result"]["maps"][0]["placements"])
    # «До кроить»
    r = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?only_remaining=true&quality=fast")
    assert r.status_code == 200, r.text
    out = _cs(client.get(f"/api/projects/{pid}").json(), cs)["result"]
    assert not out["unplaced"]
    assert len(out["maps"]) == n_maps                                  # yangi list qo'shilmadi
    now = sorted((pl["part_id"], pl["x"], pl["y"]) for pl in out["maps"][0]["placements"])
    assert set(kept) <= set(now)                                       # joylangan detallar o'z joyida
    before = sum(len(m["placements"]) for m in _cs(p, cs)["result"]["maps"])
    assert sum(len(m["placements"]) for m in out["maps"]) == before + 2   # qolgan ikkitasi tayyor kartalarga
