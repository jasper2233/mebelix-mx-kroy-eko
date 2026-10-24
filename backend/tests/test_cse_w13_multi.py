"""W13 / CSE-019: ko'p tanlash (`paths`) вЂ” o'chirish, ko'chirish, nusxalash, qayta kesish; swap. Daraxt qo'lda quriladi
(optimizator tebranishiga bog'liq emas): bitta polosada P1..P4, ostida katta bo'sh joy.

Sheet 2750Г—1830, torsovka 0, propil 3:
  root(y) в†’ S(x, h=500)[P1 300, P2 200, P3 100, P4 400, W] , W(1327)"""
from cse_w13_util import (C, P, W, bad, card, check, deep, edit, leaves_p, make_project, nodes, ok, uid_count)


def _setup(client, qty=1):
    pid, cs, sh = make_project(client, [(300, 500, qty), (200, 500, qty), (100, 500, qty), (400, 500, qty)])
    tree = C(0, 0, 2750, 1830, "y", [
        C(0, 0, 2750, 500, "x", [P(0, 0, 300, 500, 1), P(303, 0, 200, 500, 2), P(506, 0, 100, 500, 3),
                                 P(609, 0, 400, 500, 4), W(1012, 0, 1738, 500)]),
        W(0, 503, 2750, 1327)])
    res = edit(client, pid, cs, card(sh, tree), type="copies", map=1, copies=1)      # `rebuild` вЂ” to'liq qayta quriladi
    assert res.status_code == 200, res.text
    return pid, cs, sh, res.json()


def _xs(res):
    return {pl["part_uid"]: pl["x"] for pl in res["maps"][0]["placements"]}


def test_multi_remove_matches_single_and_dedupes_ancestors(client):
    pid, cs, sh, res = _setup(client)
    r = ok(client, pid, cs, res, type="remove", map=1, paths=[[0, 0], [0, 2]])
    assert sorted(_xs(r)) == [2, 4] and len(r["unplaced"]) == 2
    assert _xs(r)[2] == 0 and _xs(r)[4] == 203                     # qolganlar chapga zichlanadi (onlayn tizimdagidek)
    # ketma-ket bitta-bitta olib tashlash bilan bir xil natija
    s1 = ok(client, pid, cs, res, type="remove", map=1, path=[0, 0])
    s2 = ok(client, pid, cs, s1, type="remove", map=1, path=[0, 1])          # zichlashdan keyin 3-detal 2-o'rinda
    assert s2["maps"][0]["strips"] == r["maps"][0]["strips"]
    # tanlangan polosaning avlodlari alohida hisoblanmaydi
    r2 = ok(client, pid, cs, res, type="remove", map=1, paths=[[0, 0], [0, 1], [0]])
    assert r2["maps"][0]["placements"] == [] and len(r2["unplaced"]) == 4
    # `paths` bitta element bo'lsa вЂ” eski `path` kabi
    r3 = ok(client, pid, cs, res, type="remove", map=1, paths=[[0, 3]])
    assert sorted(_xs(r3)) == [1, 2, 3]


def test_multi_move_keeps_relative_order_and_packs(client):
    pid, cs, sh, res = _setup(client)
    r = ok(client, pid, cs, res, type="move", map=1, paths=[[0, 1], [0, 3]], to="start")
    x = _xs(r)
    assert (x[2], x[4], x[1], x[3]) == (0, 203, 606, 909)           # P2,P4 boshiga (nisbiy tartib saqlanadi), zich + propil
    r = ok(client, pid, cs, res, type="move", map=1, paths=[[0, 0], [0, 2]], to="end")
    x = _xs(r)
    assert x[2] < x[4] < x[1] < x[3]
    r = ok(client, pid, cs, res, type="move", map=1, paths=[[0, 2], [0, 3]], to="prev")      # P3,P4 blok bir qadam chapga
    x = _xs(r)
    assert x[1] < x[3] < x[4] < x[2]
    r = ok(client, pid, cs, res, type="move", map=1, paths=[[0, 0], [0, 1]], to="next")      # P1,P2 blok bir qadam o'ngga
    x = _xs(r)
    assert x[3] < x[1] < x[2] < x[4]
    # chiqindi va ildizni ko'chirib bo'lmaydi
    bad(client, pid, cs, res, type="move", map=1, paths=[[0, 4], [0, 0]], to="start")
    bad(client, pid, cs, res, type="move", map=1, paths=[[], [0, 0]], to="start")
    bad(client, pid, cs, res, type="move", map=1, paths=[[0, 0], [0, 1]], to="sideways")


def test_multi_clone_needs_parts_and_space(client):
    pid, cs, sh, res = _setup(client, qty=2)
    r = ok(client, pid, cs, res, type="clone", map=1, paths=[[0, 0], [0, 1]])        # P1, P2 nusxalari bo'sh joyga
    assert uid_count(r, 1) == 2 and uid_count(r, 2) == 2 and uid_count(r, 3) == 1
    assert len(r["unplaced"]) == 8 - 6
    # butun polosa nusxasi (barcha detallar 2 tadan) вЂ” pastdagi bo'sh joyga
    r = ok(client, pid, cs, res, type="clone", map=1, path=[0])
    assert all(uid_count(r, u) == 2 for u in (1, 2, 3, 4)) and not r["unplaced"]
    # detal yetmasa: qty=1 вЂ” nusxa rad etiladi
    pid1, cs1, sh1, res1 = _setup(client, qty=1)
    d = bad(client, pid1, cs1, res1, type="clone", map=1, paths=[[0, 0], [0, 1]])
    assert d
    # tanlanganda chiqindi bo'lsa
    bad(client, pid, cs, res, type="clone", map=1, paths=[[0, 0], [0, 4]])


def test_swap_exchanges_positions(client):
    pid, cs, sh, res = _setup(client)
    r = ok(client, pid, cs, res, type="swap", map=1, paths=[[0, 0], [0, 2]])
    x = _xs(r)
    assert (x[3], x[2], x[1], x[4]) == (0, 103, 306, 609)           # P3, P2, P1, P4 вЂ” zich + propil
    assert not r["unplaced"]
    for paths in ([[0, 0]], [[0, 0], [0, 1], [0, 2]], [[0, 0], [0, 4]], [[0, 0], [1]], [[], [0, 0]]):
        bad(client, pid, cs, res, type="swap", map=1, paths=paths)


def test_multi_rotate_regions_limits_and_safety(client):
    pid, cs, sh = make_project(client, [(300, 200, 4), (250, 200, 4)])
    s1 = C(0, 0, 2750, 200, "x", [P(0, 0, 300, 200, 1), P(303, 0, 300, 200, 1), W(606, 0, 2144, 200)])
    s2 = C(0, 203, 2750, 200, "x", [P(0, 203, 250, 200, 2), P(253, 203, 250, 200, 2), W(506, 203, 2244, 200)])
    tree = C(0, 0, 2750, 1830, "y", [s1, s2, W(0, 406, 2750, 1424)])
    res = edit(client, pid, cs, card(sh, tree), type="copies", map=1, copies=1).json()
    # qayta kesish: yo'nalish almashadi; mos kelmasa 422 вЂ” hech qachon 500 emas; muvaffaqiyatda tekshiruvdan o'tadi
    for paths in ([[0], [1]], [[0]], [[1]]):
        r = edit(client, pid, cs, res, type="rotate", map=1, paths=paths)
        assert r.status_code in (200, 422), r.text[:200]
        if r.status_code == 200:
            check(pid, cs, r.json())
            assert uid_count(r.json(), 1) == 2 and uid_count(r.json(), 2) == 2
    # chegaralar
    bad(client, pid, cs, res, type="rotate", map=1, paths=[])
    bad(client, pid, cs, res, type="rotate", map=1, paths=[[0, 0], [1, 0]])                  # detallar вЂ” hudud emas
    many = [[0]] + [[i] for i in range(1, 3)] + [[0, i] for i in range(0, 9)]
    bad(client, pid, cs, res, type="rotate", map=1, paths=many)                              # 10 dan ko'p hudud


def test_paths_validation_never_500_and_state_untouched(client):
    pid, cs, sh, res = _setup(client)
    before = deep(res)
    junk = ["abc", 5, {"a": 1}, [[0, "a"]], [[True]], [[-1]], [[99]], [[0, 99]], [["x"]], [None], [[1.5]],
            [[0] * 60], [[0, 0], "z"], [[[0]]]]
    for paths in junk:
        for kind in ("remove", "move", "clone", "rotate", "swap", "flip"):
            r = edit(client, pid, cs, res, type=kind, map=1, paths=paths, to="start")
            assert 400 <= r.status_code < 500, (kind, paths, r.status_code, r.text[:200])
    # soxta `path` (eski forma) ham 4xx
    for path in ("abc", None, [True], [-1], [0, 0, 0, 0, 0, 0, 0]):
        r = edit(client, pid, cs, res, type="remove", map=1, path=path)
        assert 400 <= r.status_code < 500, (path, r.status_code)
    # juda ko'p tanlov вЂ” 422
    r = edit(client, pid, cs, res, type="remove", map=1, paths=[[0]] * 50_001)
    assert r.status_code == 422
    # qoralama o'zgarmagan (amal toza funksiya): xuddi shu natija qayta qo'llansa вЂ” xuddi shu javob
    assert res == before
    r = ok(client, pid, cs, res, type="remove", map=1, paths=[[0, 0], [0, 1]])
    assert len(r["unplaced"]) == 2 and len(res["unplaced"]) == 0
    assert len(nodes(res["maps"][0]["strips"][0], lambda n: n["k"] == "P")) == 4 and len(leaves_p(r["maps"][0]["strips"][0])) == 2

