"""Редактирование раскроя: daraxt ustidagi amallar, qayta qurish va tekshiruv."""


def _cs(p, cs):
    return next(o for o in p["operations"] if o["id"] == cs)


def _find(node, pred, path=()):
    """Daraxtdan shartga mos birinchi tugun manzili."""
    if pred(node):
        return list(path), node
    for i, c in enumerate(node.get("c", [])):
        r = _find(c, pred, path + (i,))
        if r:
            return r
    return None


def _edit(client, pid, cs, result, **action):
    return client.post(f"/api/projects/{pid}/operations/{cs}/edit", json={"result": result, "action": action})


def _prepare(client, kravat):
    pid, cs, el = kravat
    res = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").json()
    assert res["total_sheets"] == 2 and not res["unplaced"]
    return pid, cs, res


def test_remove_and_place_back(client, kravat):
    pid, cs, res = _prepare(client, kravat)
    root = res["maps"][0]["strips"][0]
    path, leaf = _find(root, lambda n: n["k"] == "P")
    r = _edit(client, pid, cs, res, type="remove", map=1, path=path)
    assert r.status_code == 200, r.text
    d = r.json()
    assert len(d["unplaced"]) == 1 and d["manual"]
    assert d["maps"][0]["parts_count"] == res["maps"][0]["parts_count"] - 1
    # qaytarib qo'yish: o'chirilgandan keyin karta zichlanadi (onlayn tizimdagidek) — detal sig'adigan bo'sh joyga
    uid = leaf["u"]
    root2 = d["maps"][0]["strips"][0]
    wpath, w = _find(root2, lambda n: n["k"] == "W" and n["l"] >= leaf["l"] - 0.01 and n["w"] >= leaf["w"] - 0.01)
    r = _edit(client, pid, cs, d, type="place", map=1, path=wpath, uid=uid, rotated=bool(leaf.get("o")))
    assert r.status_code == 200, r.text
    d2 = r.json()
    assert not d2["unplaced"] and d2["maps"][0]["parts_count"] == res["maps"][0]["parts_count"]
    # saqlash
    p = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=d2).json()
    assert _cs(p, cs)["result"]["manual"] and not _cs(p, cs)["result"]["unplaced"]


def test_place_auto_and_errors(client, kravat):
    pid, cs, res = _prepare(client, kravat)
    # kamida 2 detalli karta (oxirgi list joylashuvi qoldiqni yig'ish uchun o'zgarishi mumkin)
    mi = max(i for i, m in enumerate(res["maps"]) if m["parts_count"] >= 2)
    other = 1 - mi if len(res["maps"]) == 2 else 0
    root = res["maps"][mi]["strips"][0]
    path, leaf = _find(root, lambda n: n["k"] == "P")
    d = _edit(client, pid, cs, res, type="remove", map=mi + 1, path=path).json()
    # detal yo'q joyga (P ga) qo'yish — xato
    ppath, _ = _find(d["maps"][mi]["strips"][0], lambda n: n["k"] == "P")
    r = _edit(client, pid, cs, d, type="place", map=mi + 1, path=ppath, uid=leaf["u"])
    assert r.status_code == 422
    # ortiqcha detal — xato (hammasi joylashgan detal)
    placed_uid = next(pl["part_uid"] for pl in d["maps"][other]["placements"] if pl["part_uid"] != leaf["u"])
    r = _edit(client, pid, cs, res, type="place_auto", map=mi + 1, uid=placed_uid)
    assert r.status_code == 422
    r = _edit(client, pid, cs, d, type="place_auto", map=mi + 1, uid=leaf["u"])
    assert r.status_code == 200, r.text
    assert not r.json()["unplaced"]


def test_move_clone_expand_copies_maps(client, kravat):
    pid, cs, res = _prepare(client, kravat)
    root = res["maps"][0]["strips"][0]
    body = [i for i, c in enumerate(root["c"]) if c["k"] != "W"]
    assert len(body) >= 2
    r = _edit(client, pid, cs, res, type="move", map=1, path=[body[0]], to="end")
    assert r.status_code == 200, r.text
    moved = r.json()["maps"][0]["strips"][0]["c"]
    assert moved[0]["l"] == root["c"][body[1]]["l"] and moved[0]["w"] == root["c"][body[1]]["w"]
    # nusxa: detallar yetmaydi
    r = _edit(client, pid, cs, res, type="clone", map=1, path=[body[0]])
    assert r.status_code == 422
    # yangi bo'sh karta, nusxalar soni, o'chirish
    d = _edit(client, pid, cs, res, type="add_map").json()
    assert len(d["maps"]) == 3 and d["maps"][2]["parts_count"] == 0
    r = _edit(client, pid, cs, d, type="copies", map=1, copies=2)
    assert r.status_code == 422                     # detallar ikki barobar kerak bo'lardi
    d = _edit(client, pid, cs, d, type="delete_map", map=3).json()
    assert len(d["maps"]) == 2
    # kengaytirish: keyingi bo'sh joyi bor polosa
    def strip_with_room(n):
        kids = n.get("c", [])
        return any(kids[i]["k"] == "C" and kids[i + 1]["k"] == "W" for i in range(len(kids) - 1))
    for mi, m in enumerate(res["maps"], 1):
        found = _find(m["strips"][0], lambda n: n["k"] == "C" and strip_with_room(n))
        if found:
            ppath, par = found
            i = next(i for i in range(len(par["c"]) - 1) if par["c"][i]["k"] == "C" and par["c"][i + 1]["k"] == "W")
            r = _edit(client, pid, cs, res, type="expand", map=mi, path=ppath + [i])
            assert r.status_code in (200, 422)          # min obrezka buzilsa — rad etiladi
            if r.status_code == 200:
                assert not r.json()["unplaced"]
            break


def test_rotate_region_keeps_parts(client, kravat):
    pid, cs, res = _prepare(client, kravat)
    mi, idx = next((mi, i) for mi in range(len(res["maps"]) - 1, -1, -1)
                   for i, c in enumerate(res["maps"][mi]["strips"][0]["c"]) if c["k"] == "C")
    r = _edit(client, pid, cs, res, type="rotate", map=mi + 1, path=[idx])
    assert r.status_code in (200, 422)
    if r.status_code == 200:
        d = r.json()
        assert not d["unplaced"] and d["maps"][mi]["parts_count"] == res["maps"][mi]["parts_count"]


def test_edit_does_not_change_saved_project(client, kravat):
    pid, cs, res = _prepare(client, kravat)
    path, _ = _find(res["maps"][0]["strips"][0], lambda n: n["k"] == "P")
    _edit(client, pid, cs, res, type="remove", map=1, path=path)
    p = client.get(f"/api/projects/{pid}").json()
    assert not _cs(p, cs)["result"]["unplaced"]          # qoralama saqlanmaydi


def test_place_auto_rotates_when_needed(client, kravat):
    pid, cs, res = _prepare(client, kravat)
    for mi, m in enumerate(res["maps"], 1):
        found = _find(m["strips"][0], lambda n: n["k"] == "P" and n.get("o") == 1 and abs(n["l"] - n["w"]) > 1)
        if found:
            path, leaf = found
            break
    else:
        return                     # bu kroyda aylantirilgan detal yo'q
    d = _edit(client, pid, cs, res, type="remove", map=mi, path=path).json()
    wpath, _w = _find(d["maps"][mi - 1]["strips"][0],
                      lambda n: n["k"] == "W" and abs(n["x"] - leaf["x"]) < 0.01 and abs(n["y"] - leaf["y"]) < 0.01)
    # aylantirish belgisisiz qo'yamiz — sig'masa o'zi aylantiradi
    r = _edit(client, pid, cs, d, type="place", map=mi, path=wpath, uid=leaf["u"], rotated=False)
    assert r.status_code == 200, r.text
    assert not r.json()["unplaced"]


def test_edit_error_language(client, kravat):
    pid, cs, res = _prepare(client, kravat)
    r = client.post(f"/api/projects/{pid}/operations/{cs}/edit", json={"result": res, "action": {"type": "bogus", "map": 1}},
                    headers={"Accept-Language": "uz"})
    assert r.status_code == 422 and "Noma'lum amal" in r.json()["detail"]
    r = client.post(f"/api/projects/{pid}/operations/{cs}/edit", json={"result": res, "action": {"type": "bogus", "map": 1}})
    assert "Неизвестное действие" in r.json()["detail"]
