"""Kroy tahriri: o'chirishdan keyin zichlash, «Развернуть резы» (joylar saqlanadi), zichlash burchagi.
Xatti-harakat onlayn tizimda «test uchun» sinov loyihasida tekshirilgan (2026-10-21)."""
import pytest


def _leaves(n, kind, out=None):
    out = [] if out is None else out
    for c in n.get("c") or []:
        if c["k"] == kind:
            out.append(c)
        elif c["k"] == "C":
            _leaves(c, kind, out)
    return out


def _path_of(n, uid, path=()):
    for i, c in enumerate(n.get("c") or []):
        if c["k"] == "P" and c.get("u") == uid:
            return list(path) + [i]
        if c["k"] == "C":
            r = _path_of(c, uid, tuple(path) + (i,))
            if r:
                return r
    return None


@pytest.fixture()
def ed(client):
    pid = client.post("/api/projects", json={"name": "PACK"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "L16", "name": "LDSP"}).json()
    op = p["operations"][0]
    cs = op["id"]
    parts = [{"name": n, "length": l, "width": w, "qty": 1, "grain": False}
             for n, l, w in [("a", 900, 434), ("b", 864, 376), ("c", 848, 320), ("d", 2006, 80), ("e", 2168, 434), ("f", 528, 402)]]
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=parts).json()
    op = next(o for o in p["operations"] if o["id"] == cs)
    uid = {x["name"]: x["uid"] for x in op["parts"]}
    sheet = op["sheets"][0]["id"]
    state = {"res": {"maps": [], "unplaced": []}}

    def act(a, ok=True):
        r = client.post(f"/api/projects/{pid}/operations/{cs}/edit", json={"result": state["res"], "action": a})
        if ok is not None:
            assert (r.status_code == 200) == ok, r.text
        state["last"] = r.json()
        if ok is None:
            assert r.status_code in (200, 422), r.text
            if r.status_code == 200:
                state["res"] = r.json()
            return state["res"]
        if ok:
            state["res"] = r.json()
        return state["res"]

    def root():
        return state["res"]["maps"][0]["strips"][0]

    def part(name):
        return next(n for n in _leaves(root(), "P") if n["u"] == uid[name])

    act({"type": "add_map", "sheet_id": sheet})
    return {"act": act, "root": root, "part": part, "uid": uid, "state": state}


def _free_path(n, target, path=()):
    for i, c in enumerate(n.get("c") or []):
        if c is target:
            return list(path) + [i]
        if c["k"] == "C":
            r = _free_path(c, target, tuple(path) + (i,))
            if r:
                return r
    return None


def test_remove_compacts_like_online(ed):
    # 1-qator: a (900×434), b (864×376), c (848×320) — chapdan o'ngga; 2-qator: d (2006×80)
    r0 = ed["root"]()
    X0, Y0 = r0["x"], r0["y"]
    for n in ("a", "b", "c"):
        free = [w for w in _leaves(ed["root"](), "W") if w["y"] < Y0 + 1 and w["l"] > 800]
        w = min(free, key=lambda q: q["x"])
        ed["act"]({"type": "place", "map": 1, "path": _free_path(ed["root"](), w), "uid": ed["uid"][n], "rotated": False})
    below = [w for w in _leaves(ed["root"](), "W") if w["y"] > Y0 + 400 and w["x"] < X0 + 1]
    ed["act"]({"type": "place", "map": 1, "path": _free_path(ed["root"](), max(below, key=lambda q: q["w"])),
               "uid": ed["uid"]["d"], "rotated": False})
    assert ed["part"]("c")["x"] > X0 + 1700 and ed["part"]("d")["y"] >= Y0 + 434
    # a va b olib tashlanadi → c chap chetga, qator c balandligigacha qisqaradi, d ko'tariladi
    r = ed["root"]()
    ed["act"]({"type": "remove", "map": 1, "paths": [_path_of(r, ed["uid"]["a"]), _path_of(r, ed["uid"]["b"])]})
    c, d = ed["part"]("c"), ed["part"]("d")
    assert c["x"] == pytest.approx(X0) and c["y"] == pytest.approx(Y0)
    assert d["x"] == pytest.approx(X0) and d["y"] < Y0 + 340        # 320 + propil
    # bitta detal o'chirilganda ham
    ed["act"]({"type": "remove", "map": 1, "path": _path_of(ed["root"](), ed["uid"]["c"])})
    assert ed["part"]("d")["y"] == pytest.approx(Y0)


def test_rotate_cuts_keeps_positions_and_toggles(ed):
    for n in ("e", "f"):
        free = [w for w in _leaves(ed["root"](), "W") if w["x"] < ed["root"]()["x"] + 1]
        w = min(free, key=lambda q: q["y"])
        ed["act"]({"type": "place", "map": 1, "path": _free_path(ed["root"](), w), "uid": ed["uid"][n], "rotated": False})
    before = {k: (ed["part"](k)["x"], ed["part"](k)["y"]) for k in ("e", "f")}
    assert ed["root"]()["a"] == "y"
    ed["act"]({"type": "rotate", "map": 1, "path": []})
    root = ed["root"]()
    assert root["a"] == "x"                                          # birinchi kesim endi vertikal
    col = root["c"][0]
    assert col["l"] == pytest.approx(2168) and root["c"][-1]["k"] == "W"
    assert {k: (ed["part"](k)["x"], ed["part"](k)["y"]) for k in ("e", "f")} == before
    ed["act"]({"type": "rotate", "map": 1, "path": []})
    assert ed["root"]()["a"] == "y"
    assert {k: (ed["part"](k)["x"], ed["part"](k)["y"]) for k in ("e", "f")} == before


def test_pack_corner_per_map(ed):
    w = _leaves(ed["root"](), "W")[0]
    ed["act"]({"type": "place", "map": 1, "path": _free_path(ed["root"](), w), "uid": ed["uid"]["f"], "rotated": False})
    res = ed["act"]({"type": "pack_corner", "map": 1, "corner": "RB"})
    m = res["maps"][0]
    f = ed["part"]("f")
    sx, sy = m["strips"][0]["x"] + m["strips"][0]["l"], m["strips"][0]["y"] + m["strips"][0]["w"]
    assert m["pack_corner"] == "RB"
    assert f["x"] + f["l"] == pytest.approx(sx) and f["y"] + f["w"] == pytest.approx(sy)
    # shu kartada yangi detal ham pastki-o'ng burchakka qo'yiladi (bo'sh joy oldinda)
    big = max(_leaves(ed["root"](), "W"), key=lambda q: q["l"] * q["w"])
    ed["act"]({"type": "place", "map": 1, "path": _free_path(ed["root"](), big), "uid": ed["uid"]["d"], "rotated": False})
    d = ed["part"]("d")
    assert d["x"] + d["l"] == pytest.approx(big["x"] + big["l"]) and d["y"] + d["w"] == pytest.approx(big["y"] + big["w"])
    ed["act"]({"type": "pack_corner", "map": 1, "corner": None})
    assert ed["state"]["res"]["maps"][0]["pack_corner"] is None
    x0 = ed["root"]()["x"]
    assert ed["part"]("f")["x"] == pytest.approx(x0) or ed["part"]("d")["x"] == pytest.approx(x0)
    ed["act"]({"type": "pack_corner", "map": 1, "corner": "XX"}, ok=False)


def test_rotate_strip_impossible_asks_then_relayout(ed, client):
    # ildizning yagona qatori: e (2168×434) qator balandligini to'liq egallaydi — joyida aylantirib bo'lmaydi
    w = _leaves(ed["root"](), "W")[0]
    ed["act"]({"type": "place", "map": 1, "path": _free_path(ed["root"](), w), "uid": ed["uid"]["e"], "rotated": False})
    strip = next(i for i, c in enumerate(ed["root"]()["c"]) if c["k"] == "C")
    st = ed["state"]["res"]
    r = ed["act"]({"type": "rotate", "map": 1, "path": [strip]}, ok=False)
    assert r is st and ed["state"]["last"]["code"] == "rotate_keep"          # qoralama o'zgarmadi, frontend so'raydi
    # operator roziligi bilan (`relayout`) hudud qayta kesiladi — natija yoki tushunarli rad (422), 500 emas
    ed["act"]({"type": "rotate", "map": 1, "path": [strip], "mode": "relayout"}, ok=None)


def test_narrow_strip_like_local_help(ed):
    """«Сузить полосы» (Ctrl+Q): polosa ichidagi detal o'lchamigacha toraytiriladi, qolgani — alohida bo'sh polosa."""
    for n in ("f", "e"):                                                  # 1-qator f (402), 2-qator e (434), pastda bo'sh joy
        free = [w for w in _leaves(ed["root"](), "W") if w["x"] < ed["root"]()["x"] + 1]
        w = max(free, key=lambda q: q["w"])
        ed["act"]({"type": "place", "map": 1, "path": _free_path(ed["root"](), w), "uid": ed["uid"][n], "rotated": False})
    r = ed["root"]()
    assert r["a"] == "y" and len([c for c in r["c"] if c["k"] != "W"]) == 2
    row2 = 1
    ed["act"]({"type": "expand", "map": 1, "path": [row2]})               # 2-qator pastdagi bo'sh joy hisobiga kengaydi
    assert ed["root"]()["c"][row2]["w"] > 434 + 1
    ed["act"]({"type": "narrow", "map": 1, "path": [row2]})
    r = ed["root"]()
    assert r["c"][row2]["w"] == pytest.approx(434) and r["c"][-1]["k"] == "W"
    # yana toraytirib bo'lmaydi — tushunarli rad (frontend Ctrl+Q da kengaytirishga o'tadi)
    ed["act"]({"type": "narrow", "map": 1, "path": [row2]}, ok=False)
    assert ed["state"]["last"]["code"] == "narrow_none"


@pytest.mark.parametrize("where, axis", [("right", "y"), ("below", "x")])
def test_place_split_follows_cursor(ed, where, axis):
    """Onlayn tahrirdagidek (foydalanuvchi videosi, 2026-10-21): Shift bilan qo'yishda kesim yo'nalishini kursor tanlaydi —
    detalning o'ng tomonida — gorizontal qator, pastida — vertikal ustun (foydalanuvchi qarori, teskari)."""
    r = ed["root"]()
    w = _leaves(r, "W")[0]
    x0, y0 = r["x"], r["y"]
    pt = (x0 + 1897 + 300, y0 + 200) if where == "right" else (x0 + 600, y0 + 434 + 300)
    ed["act"]({"type": "place", "map": 1, "path": _free_path(r, w), "uid": ed["uid"]["e"], "rotated": False, "x": pt[0], "y": pt[1]})
    root = ed["root"]()
    assert root["a"] == axis
    e = ed["part"]("e")
    assert e["x"] == pytest.approx(x0) and e["y"] == pytest.approx(y0)
    ws = _leaves(root, "W")
    if axis == "x":
        assert any(abs(q["w"] - root["w"]) < 0.01 for q in ws)             # o'ngda butun balandlikdagi ustun
    else:
        assert any(abs(q["l"] - root["l"]) < 0.01 for q in ws)             # pastda butun enlikdagi qator
