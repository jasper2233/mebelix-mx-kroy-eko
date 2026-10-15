"""W13 / CSE xavfsizlik va yaxlitlik: tahrir sonlari (NaN, manfiy, katta), 10 000 detalli karta, parallel tahrir
(bir vaqtda saqlash / iz / qulf), chuqur ichma-ich ma'lumot. `test_integrity.py` himoyalarining davomi."""
import json
import threading
import time

from cse_w13_util import (C, P, W, bad, blank, card, check, deep, edit, leaves_p, make_project, nodes, ok, op_of,
                          raw_post, uid_count)

SPECIAL = [float("nan"), float("inf"), float("-inf"), -1, 0, 1, 10 ** 30, -(10 ** 30), 1e308, 1e-308, 2 ** 70, 0.5,
           "1e999", "NaN", "-5", "abc", "", True, False, None, [], {}, [1], {"a": 1}]


def _strip(client, parts=((300, 500, 2), (200, 500, 2))):
    pid, cs, sh = make_project(client, list(parts))
    tree = C(0, 0, 2750, 1830, "y", [
        C(0, 0, 2750, 500, "x", [P(0, 0, 300, 500, 1), P(303, 0, 200, 500, 2), W(506, 0, 2244, 500)]),
        W(0, 503, 2750, 1327)])
    res = edit(client, pid, cs, card(sh, tree), type="copies", map=1, copies=1).json()
    return pid, cs, sh, res


def test_numeric_parameters_never_crash_and_never_corrupt(client):
    """Har amalning har bir son/matn parametriga NaN, ±∞, manfiy, juda katta, noto'g'ri tur: 4xx (yoki mantiqan to'g'ri
    200), hech qachon 500; 200 bo'lsa natija to'liq tekshiruvdan o'tgan."""
    pid, cs, sh, res = _strip(client)
    url = f"/api/projects/{pid}/operations/{cs}/edit"
    base_actions = [
        dict(type="copies", map=1, copies=1), dict(type="place", map=1, path=[1], uid=1),
        dict(type="place_auto", map=1, uid=1), dict(type="place_multi", map=1, path=[1], uid=1),
        dict(type="remove", map=1, path=[0, 0]), dict(type="move", map=1, path=[0, 0], to="end"),
        dict(type="clone", map=1, path=[0, 0]), dict(type="expand", map=1, path=[0]),
        dict(type="rotate", map=1, path=[0]), dict(type="flip", map=1, path=[0, 0]),
        dict(type="replace", map=1, path=[0, 0], uid=2), dict(type="swap", map=1, paths=[[0, 0], [0, 1]]),
        dict(type="move_map", map=1, to="down"), dict(type="map_trim", map=1, trim_length=1),
        dict(type="comment", map=1, comment="x"), dict(type="add_map", sheet_id=sh["id"]),
        dict(type="expand_block", map=1, path=[0, 0]), dict(type="delete_map", map=1),
    ]
    n_ok = 0
    for action in base_actions:
        for key in list(action):
            if key == "type":
                continue
            for bad_value in SPECIAL:
                a = dict(action)
                a[key] = bad_value
                r = raw_post(client, url, json.dumps({"result": res, "action": a}))
                assert r.status_code < 500, (a, r.status_code, r.text[:200])
                if r.status_code == 200:
                    n_ok += 1
                    check(pid, cs, r.json())
                else:
                    assert r.status_code in (400, 422), (a, r.status_code)
                    assert "detail" in r.json()
    assert n_ok > 20                                                     # tekshiruv bo'sh o'tmadi (mantiqan to'g'ri 200 lar bor)
    # `type` ning o'zi
    for t in SPECIAL + ["", "REMOVE", "place;drop", "__class__"]:
        r = raw_post(client, url, json.dumps({"result": res, "action": {"type": t, "map": 1}}))
        assert r.status_code in (400, 422), (t, r.status_code)
    # action dict emas / yo'q
    for a in ("x", 5, [1, 2], None):
        assert raw_post(client, url, json.dumps({"result": res, "action": a})).status_code in (400, 422)


def test_poisoned_result_numbers_are_rejected(client):
    pid, cs, sh, res = _strip(client)
    url = f"/api/projects/{pid}/operations/{cs}/edit"
    action = {"type": "comment", "map": 1, "comment": "x"}
    neg = deep(res)
    neg["maps"][0]["copies"] = -3                                        # manfiy nusxalar — 1 ga keltiriladi (qirqilmaydi)
    assert ok(client, pid, cs, neg, type="comment", map=1, comment="x")["maps"][0]["copies"] == 1
    for path_, val in ((("maps", 0, "copies"), float("nan")), (("maps", 0, "copies"), 10 ** 30),
                       (("maps", 0, "sheet_length"), float("inf")), (("maps", 0, "placements", 0, "x"), float("nan")),
                       (("maps", 0, "trim_length"), -5), (("maps", 0, "trim_length"), 1e9),
                       (("maps", 0, "trim_width"), float("nan")), (("maps", 0, "strips", 0, "x"), float("nan")),
                       (("maps", 0, "strips", 0, "l"), -10), (("maps", 0, "strips", 0, "c", 0, "w"), 1e300),
                       (("maps", 0, "strips", 0, "c", 0, "c", 0, "u"), 99999), (("maps", 0, "strips", 0, "a"), "z")):
        bad_res = deep(res)
        cur = bad_res
        for k in path_[:-1]:
            cur = cur[k]
        cur[path_[-1]] = val
        r = raw_post(client, url, json.dumps({"result": bad_res, "action": action}))
        assert r.status_code in (400, 422), (path_, val, r.status_code, r.text[:160])
        r = raw_post(client, f"/api/projects/{pid}/operations/{cs}/edit/check", json.dumps(bad_res))
        assert r.status_code in (200, 422), (path_, val, r.status_code)
        if r.status_code == 200:
            assert not r.json()["ok"]
        r = client.put(f"/api/projects/{pid}/operations/{cs}/result", content=json.dumps(bad_res),
                       headers={"Content-Type": "application/json"})
        assert r.status_code in (400, 422), (path_, val, r.status_code)
    assert op_of(client.get(f"/api/projects/{pid}").json(), cs)["result"] is None      # hech biri saqlanmadi


def test_deeply_nested_and_oversized_trees_are_rejected_cleanly(client):
    pid, cs, sh, res = _strip(client)
    url = f"/api/projects/{pid}/operations/{cs}/edit"
    node = {"x": 0, "y": 0, "l": 10, "w": 10, "k": "W"}
    for _i in range(60):                                                  # 60 daraja: daraxt chegarasidan chuqur
        node = {"x": 0, "y": 0, "l": 10, "w": 10, "k": "C", "a": "x", "c": [node]}
    deep_res = deep(res)
    deep_res["maps"][0]["strips"] = [node]
    r = raw_post(client, url, json.dumps({"result": deep_res, "action": {"type": "comment", "map": 1, "comment": "x"}}))
    assert r.status_code == 422
    # juda chuqur JSON (rekursiya) — 500 emas
    text = '{"result": {"maps": [{"index":1,"sheet_id":"x","sheet_length":1,"sheet_width":1,"strips":[' + \
        '{"k":"C","a":"x","x":0,"y":0,"l":1,"w":1,"c":[' * 3000 + "]}" * 3000 + ']}]}, "action": {"type":"comment","map":1}}'
    try:
        r = raw_post(client, url, text)
        assert r.status_code in (400, 413, 422)
    except RecursionError:                                                # TestClient serverdagi istisnoni qaytaradi
        raise AssertionError("juda chuqur JSON 500 / RecursionError berdi")
    # ko'p kartali natija: 300 bo'sh karta — o'chirish/tartib ishlaydi va chegarada
    many = {"maps": []}
    one = ok(client, pid, cs, many, type="add_map", sheet_id=sh["id"])
    one["maps"] = one["maps"] * 300
    for i, m in enumerate(one["maps"], 1):
        m["index"] = i
    r = edit(client, pid, cs, one, type="move_map", map=300, to="first")
    assert r.status_code in (200, 422)
    # katta izoh — qisqartiriladi
    r = ok(client, pid, cs, many, type="add_map", sheet_id=sh["id"])
    r = ok(client, pid, cs, r, type="comment", map=1, comment="я" * 10 ** 6)
    assert len(r["maps"][0]["comment"]) == 2000


def test_ten_thousand_part_card_edits_stay_valid_and_fast(client):
    """10 000 detalli karta: ko'p qo'yish (2 × 5000), saqlash, ko'p tanlash bilan o'chirish/ko'chirish/almashtirish,
    tekshirish — hammasi chegaralangan vaqtda va validate() 0 xato bilan."""
    pid, cs, sh = make_project(client, [(10, 10, 10000)])
    res = blank(client, pid, cs, sh)
    t0 = time.perf_counter()
    r = ok(client, pid, cs, res, type="place_multi", map=1, path=[0], uid=1, count=5000)
    assert uid_count(r, 1) == 5000
    path = [p for p, n in nodes(r["maps"][0]["strips"][0], lambda n: n["k"] == "W" and n["l"] > 100 and n["w"] > 100)][-1]
    r = ok(client, pid, cs, r, type="place_multi", map=1, path=path, uid=1, count=5000)
    assert uid_count(r, 1) == 10000 and not r["unplaced"] and r["maps"][0]["parts_count"] == 10000
    t_fill = time.perf_counter() - t0
    assert t_fill < 90, t_fill
    # saqlash va qayta o'qish
    t0 = time.perf_counter()
    p = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=r)
    assert p.status_code == 200, p.text[:300]
    op = op_of(p.json(), cs)
    assert op["result"]["maps"][0]["parts_count"] == 10000 and op["parts"][0]["used_qty"] == 10000
    assert op["parts"][0]["left_qty"] == 0
    t_save = time.perf_counter() - t0
    assert t_save < 60, t_save
    # tekshirish endpointi
    t0 = time.perf_counter()
    c = client.post(f"/api/projects/{pid}/operations/{cs}/edit/check", json=op["result"])
    assert c.status_code == 200 and c.json()["ok"] and c.json()["maps"][0]["parts"] == 10000
    assert time.perf_counter() - t0 < 60
    # ko'p tanlash: 4000 ta detalni bir amalda o'chirish; keyin boshqa 1000 tasini boshiga ko'chirish
    leaves = [p_ for p_, _n in leaves_p(op["result"]["maps"][0]["strips"][0])]
    t0 = time.perf_counter()
    r2 = ok(client, pid, cs, op["result"], type="remove", map=1, paths=leaves[:4000])
    assert len(r2["unplaced"]) == 4000 and r2["maps"][0]["parts_count"] == 6000
    keep = [p_ for p_, _n in leaves_p(r2["maps"][0]["strips"][0])]
    r3 = ok(client, pid, cs, r2, type="move", map=1, paths=keep[-1000:], to="start")
    assert r3["maps"][0]["parts_count"] == 6000
    r4 = ok(client, pid, cs, r3, type="place_multi", map=1, path=[p_ for p_, _n in nodes(
        r3["maps"][0]["strips"][0], lambda n: n["k"] == "W")][0], uid=1, count=1000)
    assert r4["maps"][0]["parts_count"] == 7000
    assert time.perf_counter() - t0 < 120
    # ildizni o'chirish — hammasi bo'sh joy
    r5 = ok(client, pid, cs, op["result"], type="remove", map=1, path=[])
    assert r5["maps"][0]["parts_count"] == 0 and len(r5["unplaced"]) == 10000
    # 10 000 detaldan keyin 10 001-chisini qo'yib bo'lmaydi
    bad(client, pid, cs, op["result"], type="place_multi", map=1, path=[0], uid=1)


def test_concurrent_saves_with_base_exactly_one_wins(client):
    """Bir xil `base` bilan bir vaqtda 12 ta saqlash: faqat bittasi o'tadi, qolganlari 409; natija butun (aralashmagan)."""
    pid, cs, sh = make_project(client, [(300, 500, 2)])
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    base_res = op_of(client.get(f"/api/projects/{pid}").json(), cs)["result"]
    rev = client.get(f"/api/projects/{pid}/operations/{cs}/edit/rev").json()["rev"]
    drafts = [ok(client, pid, cs, base_res, type="comment", map=1, comment=f"T{i}") for i in range(12)]
    codes: list[int] = [0] * 12
    barrier = threading.Barrier(12)

    def worker(i):
        barrier.wait()
        codes[i] = client.put(f"/api/projects/{pid}/operations/{cs}/result?base={rev}", json=drafts[i]).status_code

    ts = [threading.Thread(target=worker, args=(i,)) for i in range(12)]
    [t.start() for t in ts]
    [t.join(60) for t in ts]
    assert sorted(codes) == [200] + [409] * 11, codes
    winner = codes.index(200)
    final = op_of(client.get(f"/api/projects/{pid}").json(), cs)["result"]
    assert final["maps"][0]["comment"] == f"T{winner}"
    check(pid, cs, final)


def test_concurrent_saves_without_base_keep_a_whole_valid_result(client):
    pid, cs, sh = make_project(client, [(300, 500, 3), (200, 400, 3)])
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    base_res = op_of(client.get(f"/api/projects/{pid}").json(), cs)["result"]
    first = [p for p, _n in leaves_p(base_res["maps"][0]["strips"][0])]
    drafts = [ok(client, pid, cs, base_res, type="remove", map=1, path=first[i % len(first)]) for i in range(8)]
    for i, d in enumerate(drafts):
        d["maps"][0]["comment"] = f"S{i}"
    codes: list[int] = [0] * 8
    barrier = threading.Barrier(8)

    def worker(i):
        barrier.wait()
        codes[i] = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=drafts[i]).status_code

    ts = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    [t.start() for t in ts]
    [t.join(60) for t in ts]
    assert codes == [200] * 8
    final = op_of(client.get(f"/api/projects/{pid}").json(), cs)["result"]
    tag = final["maps"][0]["comment"]
    assert tag in {f"S{i}" for i in range(8)}
    expect = drafts[int(tag[1:])]
    assert final["maps"][0]["strips"] == expect["maps"][0]["strips"]            # izoh va daraxt BIR qoralamadan
    assert len(final["unplaced"]) == len(expect["unplaced"])
    check(pid, cs, final)
    # tarix: har saqlash alohida versiya; ketma-ket bekor qilish zanjiri butun
    u = client.post(f"/api/projects/{pid}/undo")
    assert u.status_code == 200
    # parallel `edit` (toza funksiya) — natijalar ketma-ket chaqiruvlar bilan bir xil
    ref = ok(client, pid, cs, base_res, type="swap", map=1, paths=[first[0][:-1] + [0], first[0][:-1] + [1]]) \
        if len(first) > 1 and len(first[0]) >= 1 else None
    outs: list = [None] * 6

    def reader(i):
        outs[i] = client.post(f"/api/projects/{pid}/operations/{cs}/edit",
                              json={"result": base_res, "action": {"type": "comment", "map": 1, "comment": "z"}}).json()

    ts = [threading.Thread(target=reader, args=(i,)) for i in range(6)]
    [t.start() for t in ts]
    [t.join(60) for t in ts]
    assert all(o == outs[0] for o in outs) and outs[0]["maps"][0]["comment"] == "z"
    assert ref is None or ref["maps"]


def test_stale_draft_after_parts_change_is_rejected(client):
    pid, cs, sh, res = _strip(client, parts=((300, 500, 2), (200, 500, 2)))
    p = client.get(f"/api/projects/{pid}").json()
    parts = op_of(p, cs)["parts"]
    # boshqa oynada detal soni kamaytirildi (kroy eskirdi) — eski qoralama (2 ta 1-detal) endi mos emas
    two = ok(client, pid, cs, res, type="clone", map=1, path=[0, 0])
    assert uid_count(two, 1) == 2
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{parts[0]['id']}", json={"qty": 1})
    r = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=two)
    assert r.status_code == 422
    # detal o'chirildi — qoralamada uning daraxt bargi bor
    client.post(f"/api/projects/{pid}/operations/{cs}/parts/delete", json={"ids": [parts[1]["id"]]})
    r = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=res)
    assert r.status_code == 422
    r = edit(client, pid, cs, res, type="comment", map=1, comment="x")
    assert r.status_code == 422
