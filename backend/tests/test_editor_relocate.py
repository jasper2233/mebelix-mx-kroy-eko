"""Kroy tahriri: Shift + sudrash — kartadagi detalni bo'sh joyga ko'chirish (`relocate`), Ctrl — aylantirish."""


def _cut(client, kravat):
    pid, cs, _el = kravat
    assert client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").status_code == 200
    return pid, cs


def _leaves(n, path, kind, out):
    for i, c in enumerate(n.get("c") or []):
        if c["k"] == kind:
            out.append((path + [i], c))
        elif c["k"] == "C":
            _leaves(c, path + [i], kind, out)
    return out


def test_relocate_part_to_free_place(client, kravat):
    pid, cs = _cut(client, kravat)
    p = client.get(f"/api/projects/{pid}").json()
    res = next(o for o in p["operations"] if o["id"] == cs)["result"]
    # bo'sh joyga sig'adigan detal topiladi
    for mi, m in enumerate(res["maps"], 1):
        root = m["strips"][0]
        free = _leaves(root, [], "W", [])
        parts = _leaves(root, [], "P", [])
        for ppath, pn in parts:
            for _wpath, w in free:
                if pn["l"] <= w["l"] and pn["w"] <= w["w"]:
                    x, y = w["x"] + 1, w["y"] + 1
                    r = client.post(f"/api/projects/{pid}/operations/{cs}/edit",
                                    json={"result": res, "action": {"type": "relocate", "map": mi, "path": ppath,
                                                                    "x": x, "y": y, "rotated": bool(pn.get("o"))}})
                    assert r.status_code == 200, r.text
                    out = r.json()
                    out = out.get("result", out)
                    nroot = out["maps"][mi - 1]["strips"][0]
                    moved = [n for _p, n in _leaves(nroot, [], "P", []) if n["u"] == pn["u"]
                             and abs(n["x"] - w["x"]) < 0.01 and abs(n["y"] - w["y"]) < 0.01]
                    assert moved, "detal chiqindi burchagiga ko'chmadi"
                    return
    raise AssertionError("sinov uchun mos bo'sh joy topilmadi")


def test_relocate_rejects_non_part(client, kravat):
    pid, cs = _cut(client, kravat)
    p = client.get(f"/api/projects/{pid}").json()
    res = next(o for o in p["operations"] if o["id"] == cs)["result"]
    r = client.post(f"/api/projects/{pid}/operations/{cs}/edit",
                    json={"result": res, "action": {"type": "relocate", "map": 1, "path": [], "x": 1, "y": 1}})
    assert r.status_code in (400, 422)
