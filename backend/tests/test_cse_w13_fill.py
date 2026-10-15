"""W13 / CSE-022, CSE-023, CSE-021: ko'p qo'yish (Shift+A), blok bilan kengaytirish (Shift+W), detalni burish va
almashtirish. Sheet 2750×1830, torsovka 0, propil 3 (daraxt qo'lda quriladi — optimizator tebranishiga bog'liq emas)."""
from cse_w13_util import (C, P, W, bad, blank, card, check, deep, edit, leaves_p, make_project, nodes, ok, uid_count)


# ───────────────────────── Shift+A — ko'p qo'yish ─────────────────────────
def test_place_multi_fills_rows_and_columns_up_to_remaining(client):
    pid, cs, sh = make_project(client, [(400, 300, 20)])
    res = blank(client, pid, cs, sh)
    r = ok(client, pid, cs, res, type="place_multi", map=1, path=[0], uid=1)
    assert uid_count(r, 1) == 20 and not r["unplaced"]
    pls = r["maps"][0]["placements"]
    rows = sorted({pl["y"] for pl in pls})
    assert len(rows) == 4                                              # 6 + 6 + 6 + 2
    assert [sum(1 for pl in pls if pl["y"] == y) for y in rows] == [6, 6, 6, 2]
    # propil: qo'shni detallar orasida 3 mm
    row0 = sorted(pl["x"] for pl in pls if pl["y"] == rows[0])
    assert all(abs(b - a - 403) < 0.01 for a, b in zip(row0, row0[1:]))


def test_place_multi_limited_by_space_and_exact_count(client):
    pid, cs, sh = make_project(client, [(400, 300, 50)])
    res = blank(client, pid, cs, sh)
    r = ok(client, pid, cs, res, type="place_multi", map=1, path=[0], uid=1)
    assert uid_count(r, 1) == 36 and len(r["unplaced"]) == 14           # 6 ustun × 6 qator — joy tugadi
    r = ok(client, pid, cs, res, type="place_multi", map=1, path=[0], uid=1, count=5)
    assert uid_count(r, 1) == 5
    d = bad(client, pid, cs, res, type="place_multi", map=1, path=[0], uid=1, count=37)    # sig'maydi
    assert d
    d = bad(client, pid, cs, res, type="place_multi", map=1, path=[0], uid=1, count=51)    # detal yetmaydi
    assert d
    for cnt in (0, -3, 5001, "x", [1], {"a": 1}, "NaN"):
        r = edit(client, pid, cs, res, type="place_multi", map=1, path=[0], uid=1, count=cnt)
        assert 400 <= r.status_code < 500, (cnt, r.status_code)


def test_place_multi_rotation_grain_and_copies(client):
    # tekstura: burib qo'yib bo'lmaydi
    pid, cs, sh = make_project(client, [(400, 300, 10, True)])
    res = blank(client, pid, cs, sh)
    d = bad(client, pid, cs, res, type="place_multi", map=1, path=[0], uid=1, rotated=True)
    assert d
    # burilgan holatda ham ishlaydi
    pid, cs, sh = make_project(client, [(400, 300, 10)])
    res = blank(client, pid, cs, sh)
    r = ok(client, pid, cs, res, type="place_multi", map=1, path=[0], uid=1, rotated=True, count=4)
    assert all(pl["rotated"] and pl["length"] == 300 and pl["width"] == 400 for pl in r["maps"][0]["placements"])
    # karta 2 nusxada: har bir qo'yish 2 detal sarflaydi — 10 dan 5 tagacha
    res2 = ok(client, pid, cs, res, type="copies", map=1, copies=2)
    r = ok(client, pid, cs, res2, type="place_multi", map=1, path=[0], uid=1)
    assert uid_count(r, 1) == 10 and len(r["maps"][0]["placements"]) == 5
    d = bad(client, pid, cs, res2, type="place_multi", map=1, path=[0], uid=1, count=6)
    assert d


def test_place_multi_errors(client):
    pid, cs, sh = make_project(client, [(400, 300, 3), (5000, 100, 1)])
    res = blank(client, pid, cs, sh)
    bad(client, pid, cs, res, type="place_multi", map=1, path=[], uid=1)             # ildiz — bo'sh joy emas
    bad(client, pid, cs, res, type="place_multi", map=1, path=[5], uid=1)            # yo'q manzil
    bad(client, pid, cs, res, type="place_multi", map=1, path=[0], uid=99)           # yo'q detal
    bad(client, pid, cs, res, type="place_multi", map=1, path=[0], uid=2)            # list uzunligidan katta
    full = ok(client, pid, cs, res, type="place_multi", map=1, path=[0], uid=1)      # hammasi qo'yildi
    bad(client, pid, cs, full, type="place_multi", map=1, path=[0], uid=1)           # endi hech narsa qolmagan


def test_place_multi_respects_max_rotations(client):
    # burilishlar = 2: ichma-ich (3-daraja) kerak bo'lgan joyga qo'yilmaydi — natija baribir to'g'ri
    pid, cs, sh = make_project(client, [(400, 300, 30)], cut={"max_rotations": 2})
    res = blank(client, pid, cs, sh)
    r = edit(client, pid, cs, res, type="place_multi", map=1, path=[0], uid=1)
    if r.status_code == 200:
        out = check(pid, cs, r.json())
        assert max(len(p) for p, _n in nodes(out.maps[0].strips[0], lambda n: True)) <= 2
    else:
        assert r.status_code == 422


# ───────────────────────── Shift+W — blok bilan kengaytirish ─────────────────────────
GROUP_TREE = lambda extra=(): C(0, 0, 2750, 1830, "y", [                      # noqa: E731
    C(0, 0, 2750, 915, "x", [
        C(0, 0, 500, 915, "y", [
            C(0, 0, 500, 910, "y", [P(0, 0, 500, 300, 1, 1), P(0, 305, 500, 300, 1, 1), P(0, 610, 500, 300, 1, 1)], g=5),
            W(0, 913, 500, 2)]),
        W(503, 0, 2247, 915)]),
    W(0, 918, 2750, 912)])


def _group_project(client, qty=5, gmax=4):
    return make_project(client, [(300, 500, qty), (600, 912, 1)], cut={"kerf_group": 5},
                        group={1: dict(group_by="length", group_max=gmax)})


def test_expand_block_grows_strip_to_group_maximum(client):
    pid, cs, sh = _group_project(client, qty=5, gmax=4)
    res = edit(client, pid, cs, card(sh, GROUP_TREE()), type="copies", map=1, copies=1)
    assert res.status_code == 200, res.text
    res = res.json()
    assert uid_count(res, 1) == 3 and len(res["unplaced"]) == 3
    # blokdagi detalni tanlab: 4 ga (maksimum) yetguncha — qolgan detal bitta
    r = ok(client, pid, cs, res, type="expand_block", map=1, path=[0, 0, 0, 0])
    assert uid_count(r, 1) == 4 and len(r["unplaced"]) == 2
    strip = r["maps"][0]["strips"][0]["c"][0]
    assert strip["w"] == 1220                                          # polosa 305 ga (detal + guruh propili) kengaydi
    g = strip["c"][0]["c"][0]
    assert g["g"] == 5 and len(g["c"]) == 4 and g["w"] == 1215
    # guruh tugunining o'zini tanlash ham ishlaydi
    r2 = ok(client, pid, cs, res, type="expand_block", map=1, path=[0, 0, 0])
    assert uid_count(r2, 1) == 4
    # maksimumga yetgan blok — xato
    d = bad(client, pid, cs, r, type="expand_block", map=1, path=[0, 0, 0, 0])
    assert d


def test_expand_block_pushes_following_strips_down(client):
    """Blok polosasi kengayganda undan keyingi polosa siljiydi, joy esa eng oxiridagi bo'sh joydan olinadi."""
    pid, cs, sh = make_project(client, [(300, 500, 5), (600, 603, 1)], cut={"kerf_group": 5},
                               group={1: dict(group_by="length", group_max=4)})
    g = C(0, 0, 500, 910, "y", [P(0, 0, 500, 300, 1, 1), P(0, 305, 500, 300, 1, 1), P(0, 610, 500, 300, 1, 1)], g=5)
    tree = C(0, 0, 2750, 1830, "y", [
        C(0, 0, 2750, 915, "x", [C(0, 0, 500, 915, "y", [g, W(0, 913, 500, 2)]), W(503, 0, 2247, 915)]),
        C(0, 918, 2750, 603, "x", [P(0, 918, 600, 603, 2), W(603, 918, 2147, 603)]),
        W(0, 1524, 2750, 306)])
    res = edit(client, pid, cs, card(sh, tree), type="copies", map=1, copies=1)
    assert res.status_code == 200, res.text
    r = ok(client, pid, cs, res.json(), type="expand_block", map=1, path=[0, 0, 0, 0])
    assert uid_count(r, 1) == 4
    pl = {p["part_uid"]: p for p in r["maps"][0]["placements"] if p["part_uid"] == 2}
    assert pl[2]["y"] == 918 + 305                                       # 2-polosa 305 mm pastga siljidi
    top = r["maps"][0]["strips"][0]["c"]
    assert top[0]["w"] == 1220 and top[1]["y"] == 1223 and top[-1]["k"] == "W" and top[-1]["w"] == 1
    # oxirgi bo'sh joy (209 mm) 305 mm ga yetmaydi — rad etiladi
    pid, cs, sh = make_project(client, [(300, 500, 5), (600, 700, 1)], cut={"kerf_group": 5},
                               group={1: dict(group_by="length", group_max=4)})
    tree2 = C(0, 0, 2750, 1830, "y", [
        C(0, 0, 2750, 915, "x", [C(0, 0, 500, 915, "y", [deep(g), W(0, 913, 500, 2)]), W(503, 0, 2247, 915)]),
        C(0, 918, 2750, 700, "x", [P(0, 918, 600, 700, 2), W(603, 918, 2147, 700)]),
        W(0, 1621, 2750, 209)])
    res2 = edit(client, pid, cs, card(sh, tree2), type="copies", map=1, copies=1)
    assert res2.status_code == 200, res2.text
    assert bad(client, pid, cs, res2.json(), type="expand_block", map=1, path=[0, 0, 0, 0])


def test_expand_block_unlimited_max_uses_remaining_parts_and_room(client):
    pid, cs, sh = _group_project(client, qty=5, gmax=0)
    res = edit(client, pid, cs, card(sh, GROUP_TREE()), type="copies", map=1, copies=1).json()
    r = ok(client, pid, cs, res, type="expand_block", map=1, path=[0, 0, 0, 1])
    assert uid_count(r, 1) == 5 and len(r["unplaced"]) == 1            # qolgan 2 detalning ikkalasi blokka qo'shildi


def test_expand_block_errors(client):
    # guruhlash yo'q detal
    pid, cs, sh = make_project(client, [(300, 500, 5)])
    tree = GROUP_TREE()
    tree["c"][0]["c"][0]["c"][0]["g"] = None
    del tree["c"][0]["c"][0]["c"][0]["g"]
    res = edit(client, pid, cs, card(sh, tree), type="copies", map=1, copies=1)
    # guruhsiz detalning daraxtida `g` bo'lmasa ham qatorni kengaytirish rad etiladi
    if res.status_code == 200:
        d = bad(client, pid, cs, res.json(), type="expand_block", map=1, path=[0, 0, 0, 0])
        assert d
    # soxta guruh tuguni (guruhlanmaydigan detalda `g` bor) — daraxtning o'zi rad etiladi
    pid, cs, sh = make_project(client, [(300, 500, 5)])
    r = edit(client, pid, cs, card(sh, GROUP_TREE()), type="copies", map=1, copies=1)
    assert r.status_code == 422
    # joy yo'q: blokdan keyin chiqindi kichik, polosadan keyin ham bo'sh joy yo'q
    pid, cs, sh = _group_project(client, qty=5, gmax=4)
    tight = C(0, 0, 2750, 1830, "y", [
        C(0, 0, 2750, 1830, "x", [
            C(0, 0, 500, 1830, "y", [
                C(0, 0, 500, 910, "y", [P(0, 0, 500, 300, 1, 1), P(0, 305, 500, 300, 1, 1), P(0, 610, 500, 300, 1, 1)], g=5),
                W(0, 913, 500, 917)]),
            W(503, 0, 2247, 1830)])])
    res = edit(client, pid, cs, card(sh, tight), type="copies", map=1, copies=1).json()
    # bu holatda joy YETARLI (917 mm chiqindi) — blokka qo'shiladi; chiqindi bo'lmasa — xato
    r = ok(client, pid, cs, res, type="expand_block", map=1, path=_path_of(res, 1))
    assert uid_count(r, 1) >= 4
    nospace = C(0, 0, 2750, 1830, "y", [
        C(0, 0, 2750, 915, "x", [
            C(0, 0, 500, 915, "y", [
                C(0, 0, 500, 910, "y", [P(0, 0, 500, 300, 1, 1), P(0, 305, 500, 300, 1, 1), P(0, 610, 500, 300, 1, 1)], g=5),
                W(0, 913, 500, 2)]),
            W(503, 0, 2247, 915)]),
        C(0, 918, 2750, 912, "x", [P(0, 918, 600, 912, 2), W(603, 918, 2147, 912)])])
    # 2-polosa bor — 1-polosadan keyin chiqindi yo'q; 2-detal esa joylashgan
    res = edit(client, pid, cs, card(sh, nospace), type="copies", map=1, copies=1)
    assert res.status_code == 200, res.text
    d = bad(client, pid, cs, res.json(), type="expand_block", map=1, path=[0, 0, 0, 0])
    assert d
    # chiqindi / yo'q manzil
    bad(client, pid, cs, res.json(), type="expand_block", map=1, path=[0, 1])
    bad(client, pid, cs, res.json(), type="expand_block", map=1, path=[9])
    bad(client, pid, cs, res.json(), type="expand_block", map=1, path=[])


def _path_of(res, uid, which=0):
    """Qayta qurilgan daraxtda detalning manzili (normallashtirish manzillarni o'zgartirishi mumkin)."""
    return [p for p, n in leaves_p(res["maps"][0]["strips"][0]) if n["u"] == uid][which]


# ───────────────────────── burish va almashtirish ─────────────────────────
def _strip_project(client, parts, cut=None):
    pid, cs, sh = make_project(client, parts, cut=cut)
    tree = C(0, 0, 2750, 1830, "y", [
        C(0, 0, 2750, 500, "x", [P(0, 0, 300, 500, 1), W(303, 0, 2447, 500)]),
        W(0, 503, 2750, 1327)])
    res = edit(client, pid, cs, card(sh, tree), type="copies", map=1, copies=1)
    assert res.status_code == 200, res.text
    return pid, cs, sh, res.json()


def test_flip_rotates_part_in_place_when_it_fits(client):
    pid, cs, sh, res = _strip_project(client, [(300, 500, 1), (200, 500, 2)])
    r = ok(client, pid, cs, res, type="flip", map=1, path=[0, 0])
    pl = r["maps"][0]["placements"][0]
    assert pl["rotated"] and (pl["length"], pl["width"]) == (500, 300) and (pl["x"], pl["y"]) == (0, 0)
    # qayta burish — asl holatga qaytadi
    back = ok(client, pid, cs, r, type="flip", map=1, path=_path_of(r, 1))
    assert not back["maps"][0]["placements"][0]["rotated"]
    # qoldiq yangilandi
    assert r["maps"][0]["strips"][0]["c"][0]["c"][0]["k"] == "C"


def test_flip_errors_grain_square_group_and_depth(client):
    pid, cs, sh, res = _strip_project(client, [(300, 500, 1, True)])
    d = bad(client, pid, cs, res, type="flip", map=1, path=[0, 0])         # tekstura
    assert d
    pid, cs, sh, res = _strip_project(client, [(300, 500, 1)], cut={"max_rotations": 2})
    d = bad(client, pid, cs, res, type="flip", map=1, path=[0, 0])         # ichma-ich daraja chegaradan oshadi
    assert d
    pid, cs, sh, res = _strip_project(client, [(300, 500, 1)])
    bad(client, pid, cs, res, type="flip", map=1, path=[0, 1])             # chiqindi
    bad(client, pid, cs, res, type="flip", map=1, path=[0])                # polosa
    bad(client, pid, cs, res, type="flip", map=1, path=[])
    pid, cs, sh = make_project(client, [(400, 400, 1)])                    # kvadrat
    tree = C(0, 0, 2750, 1830, "y", [C(0, 0, 2750, 400, "x", [P(0, 0, 400, 400, 1), W(403, 0, 2347, 400)]),
                                     W(0, 403, 2750, 1427)])
    sq = edit(client, pid, cs, card(sh, tree), type="copies", map=1, copies=1).json()
    bad(client, pid, cs, sq, type="flip", map=1, path=[0, 0])


def test_flip_with_tight_neighbour_does_not_fit(client):
    pid, cs, sh = make_project(client, [(300, 500, 1), (200, 500, 1)])
    tree = C(0, 0, 2750, 1830, "y", [
        C(0, 0, 2750, 500, "x", [P(0, 0, 300, 500, 1), P(303, 0, 200, 500, 2), W(506, 0, 2244, 500)]),
        W(0, 503, 2750, 1327)])
    res = edit(client, pid, cs, card(sh, tree), type="copies", map=1, copies=1).json()
    d = bad(client, pid, cs, res, type="flip", map=1, path=[0, 0])         # 500 uzunlik 300+3 oraliqqa sig'maydi
    assert d
    # ikkinchi detal o'ngda bo'sh joy bilan chegaralangan emas — buriladi
    r = ok(client, pid, cs, res, type="flip", map=1, path=[0, 1])
    assert any(pl["part_uid"] == 2 and pl["rotated"] for pl in r["maps"][0]["placements"])


def test_replace_swaps_part_in_place(client):
    pid, cs, sh, res = _strip_project(client, [(300, 500, 1), (200, 500, 1), (600, 500, 1), (3000, 100, 1)])
    r = ok(client, pid, cs, res, type="replace", map=1, path=[0, 0], uid=2)
    assert uid_count(r, 1) == 0 and uid_count(r, 2) == 1
    pl = r["maps"][0]["placements"][0]
    assert (pl["part_uid"], pl["x"], pl["y"]) == (2, 0, 0)
    assert len(r["unplaced"]) == 3                                      # 1, 3, 4 — joylashmagan
    # kattaroq detal: bo'sh joy hisobiga
    r = ok(client, pid, cs, res, type="replace", map=1, path=[0, 0], uid=3)
    assert uid_count(r, 3) == 1
    # sig'masa / xuddi shu / yo'q / joylashgan detal yo'q
    assert bad(client, pid, cs, res, type="replace", map=1, path=[0, 0], uid=4)
    assert bad(client, pid, cs, res, type="replace", map=1, path=[0, 0], uid=1)
    bad(client, pid, cs, res, type="replace", map=1, path=[0, 0], uid=77)
    bad(client, pid, cs, res, type="replace", map=1, path=[0, 1], uid=2)
    bad(client, pid, cs, res, type="replace", map=1, path=[0], uid=2)
    # bitta nusxali detal boshqa kartada band bo'lsa — qolmagan
    two = ok(client, pid, cs, res, type="add_map", sheet_id=sh["id"])
    two = ok(client, pid, cs, two, type="place", map=2, path=[0], uid=2)
    bad(client, pid, cs, two, type="replace", map=1, path=[0, 0], uid=2)
