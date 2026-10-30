"""Kroy tahriri: detal bitta bo'sh katakka sig'masa (xodim loyihasi «1275» AKRIL, 2026-10-30). Kartada 3 qator (fasadlar 717,
337 va 2 sokl), har qator oxirida bo'sh joy — birgalikda list balandligidagi ~123 mm bo'sh ustun. Operator 3-soklni Shift bilan
o'sha ustunga qo'yadi.
* sokl 1120: bo'sh kataklar birlashtiriladi — boshqa detallar joyida, kesish daraxti joylardan qayta quriladi;
* sokl 1150: pastki qatorda 1 mm qirindi qolardi (< «Минимальная обрезка») — list qayta joylanadi, hamma detal shu listda.
Onlayn tizim muharriri ikkala holatda ham rad etadi («test uchun», 2026-10-30 jonli sinov) — MX foydalanuvchi qoidasi bo'yicha
sig'diradi: kesish chiziqlarini o'zgartirib detal sig'sa va listdagi detallar chiqib ketmasa — sig'dirilsin."""
import pytest

from tests.test_editor_pack import _leaves


def _cs(p, cs):
    return next(o for o in p["operations"] if o["id"] == cs)


def _leaf_at(n, x, y, path=()):
    for i, c in enumerate(n.get("c") or []):
        if c["x"] - 0.01 <= x <= c["x"] + c["l"] + 0.01 and c["y"] - 0.01 <= y <= c["y"] + c["w"] + 0.01:
            if c["k"] == "C":
                return _leaf_at(c, x, y, tuple(path) + (i,))
            return list(path) + [i], c
    return None, None


@pytest.mark.parametrize("rot", [4, 6])
@pytest.mark.parametrize("sl, keep", [(1120, True), (1150, False)])
def test_place_into_merged_free_column(client, sl, keep, rot):
    ROT = rot
    pid = client.post("/api/projects", json={"name": "FREE"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "AK", "name": "AKRIL"}).json()
    cs = p["operations"][0]["id"]
    client.patch(f"/api/projects/{pid}/operations/{cs}",
                 json={"cs_cut": {"kerf": 3, "trim_length": 2, "trim_width": 2, "use_grain": False, "max_rotations": ROT,
                                  "min_trim_cut": 5}})
    sid = _cs(client.get(f"/api/projects/{pid}").json(), cs)["sheets"][0]["id"]
    client.put(f"/api/projects/{pid}/operations/{cs}/sheets", json=[{"id": sid, "length": 2440, "width": 1220, "qty": 10000}])
    parts = [("sokl", 100, sl, 3), ("fasad", 717, 337, 8), ("fasad2", 237, 604, 3)]
    client.post(f"/api/projects/{pid}/operations/{cs}/parts",
                json=[{"name": n, "length": l, "width": w, "qty": q, "grain": False} for n, l, w, q in parts])
    assert client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").status_code == 200
    op = _cs(client.get(f"/api/projects/{pid}").json(), cs)
    uid = {x["name"]: x["uid"] for x in op["parts"]}
    f, g, s = uid["fasad"], uid["fasad2"], uid["sokl"]

    def P(x, y, l, w, u, o=1):
        return {"x": x, "y": y, "l": l, "w": w, "k": "P", "u": u, **({"o": 1} if o else {})}

    def W(x, y, l, w):
        return {"x": x, "y": y, "l": l, "w": w, "k": "W"}
    # xodim kartasi (skrindagidek)
    band1 = {"x": 5, "y": 5, "l": 2430, "w": 717, "k": "C", "a": "x", "c": [
        *[P(5 + 340 * i, 5, 337, 717, f) for i in range(5)],
        {"x": 1705, "y": 5, "l": 604, "w": 717, "k": "C", "a": "y", "c": [P(1705, 5 + 240 * i, 604, 237, g) for i in range(3)]},
        W(2312, 5, 123, 717)]}
    band2 = {"x": 5, "y": 725, "l": 2430, "w": 337, "k": "C", "a": "x", "c": [
        *[P(5 + 720 * i, 725, 717, 337, f, 0) for i in range(3)], W(2165, 725, 270, 337)]}
    e3 = 5 + 2 * sl + 3
    band3 = {"x": 5, "y": 1065, "l": 2430, "w": 100, "k": "C", "a": "x", "c": [
        P(5, 1065, sl, 100, s), P(8 + sl, 1065, sl, 100, s), W(e3 + 3, 1065, 2435 - e3 - 3, 100)]}
    root = {"x": 5, "y": 5, "l": 2430, "w": 1210, "k": "C", "a": "y", "c": [band1, band2, band3, W(5, 1168, 2430, 47)]}
    res = {"maps": [{**op["result"]["maps"][0], "strips": [root], "placements": []}], "unplaced": []}
    before = sorted((round(n["x"]), round(n["y"])) for n in _leaves(root, "P"))
    x, y = 2370, 100                                               # yuqori qator oxiridagi bo'sh joy
    path, leaf = _leaf_at(root, x, y)
    assert leaf is not None and leaf["k"] == "W" and leaf["w"] < sl   # bitta katak soklga sig'maydi
    r = client.post(f"/api/projects/{pid}/operations/{cs}/edit",
                    json={"result": res, "action": {"type": "place", "map": 1, "path": path, "uid": s,
                                                    "rotated": False, "x": x, "y": y}})
    assert r.status_code == 200, ascii(r.json())
    out = r.json()
    assert len(out["maps"]) == 1
    root = out["maps"][0]["strips"][0]
    ps = _leaves(root, "P")
    assert len(ps) == 14                                           # hamma detal shu listda
    after = sorted((round(n["x"]), round(n["y"])) for n in ps)
    if keep:
        assert all(b in after for b in before)                     # boshqa detallar o'z joyida
        new = [n for n in ps if (round(n["x"]), round(n["y"])) not in before]
        assert len(new) == 1 and round(new[0]["l"]) == 100 and round(new[0]["w"]) == sl and new[0]["x"] > 2300
    # saqlash ham o'tadi (qayta qurish + tekshiruv)
    r = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=out)
    assert r.status_code == 200, ascii(r.json())


def test_sliver_slot_falls_back(client):
    """Xodim ketma-ketligi (2026-10-30, brauzerda takrorlandi): pastki 2-sokl o'ng ustunga sudraldi (relocate), pastki qatorda
    1151 mm bo'sh joy qoldi; ro'yxatdagi 3-sokl (1150) o'sha joyga qo'yilganda 1 mm qirindi qolardi va «обрезок 1.0 мм» xatosi
    chiqardi. Endi oddiy qo'yish rad etiladi va list qayta joylanadi — 14 detal bitta listda, saqlash o'tadi."""
    pid = client.post("/api/projects", json={"name": "SLIVER"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "AK", "name": "AKRIL"}).json()
    cs = p["operations"][0]["id"]
    client.patch(f"/api/projects/{pid}/operations/{cs}",
                 json={"cs_cut": {"kerf": 3, "trim_length": 2, "trim_width": 2, "use_grain": False, "max_rotations": 6,
                                  "min_trim_cut": 5}})
    sid = _cs(client.get(f"/api/projects/{pid}").json(), cs)["sheets"][0]["id"]
    client.put(f"/api/projects/{pid}/operations/{cs}/sheets", json=[{"id": sid, "length": 2440, "width": 1220, "qty": 10000}])
    client.post(f"/api/projects/{pid}/operations/{cs}/parts",
                json=[{"name": n, "length": l, "width": w, "qty": q, "grain": False}
                      for n, l, w, q in [("sokl", 100, 1150, 3), ("fasad", 717, 337, 8), ("fasad2", 237, 604, 3)]])
    assert client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").status_code == 200
    op = _cs(client.get(f"/api/projects/{pid}").json(), cs)
    uid = {x["name"]: x["uid"] for x in op["parts"]}
    f, g, s = uid["fasad"], uid["fasad2"], uid["sokl"]

    def P(x, y, l, w, u, o=1):
        return {"x": x, "y": y, "l": l, "w": w, "k": "P", "u": u, **({"o": 1} if o else {})}

    def W(x, y, l, w):
        return {"x": x, "y": y, "l": l, "w": w, "k": "W"}
    # sudrashdan keyingi karta (brauzerdagidek): chap blok 2304 (detallar 2309 gacha), pastki qatorda sokl + 1151 bo'sh,
    # o'ng ustunda tik sokl
    left = {"x": 5, "y": 5, "l": 2304, "w": 1210, "k": "C", "a": "y", "c": [
        {"x": 5, "y": 5, "l": 2304, "w": 717, "k": "C", "a": "x", "c": [*[P(5 + 340 * i, 5, 337, 717, f) for i in range(5)],
         {"x": 1705, "y": 5, "l": 604, "w": 717, "k": "C", "a": "y", "c": [P(1705, 5 + 240 * i, 604, 237, g) for i in range(3)]}]},
        {"x": 5, "y": 725, "l": 2304, "w": 337, "k": "C", "a": "x", "c": [*[P(5 + 720 * i, 725, 717, 337, f, 0) for i in range(3)],
                                                                         W(2165, 725, 144, 337)]},
        {"x": 5, "y": 1065, "l": 2304, "w": 100, "k": "C", "a": "x", "c": [P(5, 1065, 1150, 100, s), W(1158, 1065, 1151, 100)]},
        W(5, 1168, 2304, 47)]}
    col = {"x": 2312, "y": 5, "l": 100, "w": 1210, "k": "C", "a": "y", "c": [P(2312, 5, 100, 1150, s, 0), W(2312, 1158, 100, 57)]}
    root = {"x": 5, "y": 5, "l": 2430, "w": 1210, "k": "C", "a": "x", "c": [left, col, W(2415, 5, 20, 1210)]}
    res = {"maps": [{**op["result"]["maps"][0], "strips": [root], "placements": []}], "unplaced": []}
    path, leaf = _leaf_at(root, 1700, 1110)
    assert leaf["k"] == "W" and leaf["l"] == 1151
    r = client.post(f"/api/projects/{pid}/operations/{cs}/edit",
                    json={"result": res, "action": {"type": "place", "map": 1, "path": path, "uid": s, "rotated": True,
                                                    "x": 1700, "y": 1110}})
    assert r.status_code == 200, ascii(r.json())
    out = r.json()
    assert len(out["maps"]) == 1 and len(_leaves(out["maps"][0]["strips"][0], "P")) == 14
    assert client.put(f"/api/projects/{pid}/operations/{cs}/result", json=out).status_code == 200
