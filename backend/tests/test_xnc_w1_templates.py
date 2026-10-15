"""W1 · XNC shablonlar kutubxonasi: o'rnatilgan namunalar (parametrik, har xil o'lchamda xatosiz), saqlash / ochish /
o'chirish / eksport / import, operatsiyaga qo'llash (replace / append), zaxira."""
import json
import math

import pytest

from app.models import XNCParams, XncCommand as C
from app.services import xnc as X
from app.services import xnc_templates as T

from test_qa_fix_calc import _op, _ops, _xnc_for


def _prog(key, lang="ru"):
    return T.library_program(key, lang)


def _ev(key, dx, dy, dz=16, pars=None, lang="ru"):
    prog = _prog(key, lang)
    ops = X.evaluate(prog, dx, dy, dz, None, pars)
    st = X.program_stats(prog, dx, dy, dz, None, pars)
    return ops, st


SIZES = [(720, 560, 16), (800, 600, 18), (2000, 450, 16), (300, 300, 16), (1200, 400, 22)]


@pytest.mark.parametrize("key", list(T.LIBRARY))
@pytest.mark.parametrize("dx,dy,dz", SIZES)
def test_library_templates_run_clean_for_any_size(key, dx, dy, dz):
    """Har bir o'rnatilgan shablon har qanday detal o'lchamida xato / ogohlantirishsiz hisoblanadi."""
    for lang in ("ru", "uz"):
        ops, st = _ev(key, dx, dy, dz, lang=lang)
        assert st["errors"] == 0 and st["warnings"] == [], (key, st["warnings"])
        assert len(ops) > 0
    # barcha Par larning yorlig'i va turi bor
    pars = [c for c in _prog(key) if c.cmd == "Par"]
    assert pars and all(c.params.get("label") and c.params.get("type") in ("double", "integer", "boolean") for c in pars)


def test_library_catalog_has_required_samples():
    ids = {t["id"] for t in T.library_list("ru")}
    assert {"lib:pocket_rect", "lib:hole_circle", "lib:outline_rounded", "lib:facade_frame", "lib:row32",
            "lib:side_panel"} <= ids
    ru = {t["id"]: t["name"] for t in T.library_list("ru")}
    uz = {t["id"]: t["name"] for t in T.library_list("uz")}
    assert ru["lib:row32"] != uz["lib:row32"] and all(ru[k] and uz[k] for k in ru)


def test_pocket_rect_geometry_and_parameters():
    ops, st = _ev("pocket_rect", 720, 560)
    start = next(o for o in ops if o["kind"] == "MillStart")
    assert start["C"] == 3 and start["DP"] == 8 and (start["X"], start["Y"]) == (360, 230)      # markaz (dx/2, dy/2), -W/2
    assert st["mill_m"] == 0.0                                          # cho'ntak (C=3) uzunlikka kirmaydi
    arcs = [o for o in ops if o["kind"] == "MillArcCenter" and o.get("fillet")]
    assert len(arcs) == 4 and all(math.isclose(math.dist((a["X"], a["Y"]), (a["CX"], a["CY"])), 10, abs_tol=1e-4)
                                  for a in arcs)
    # parametrlar: L, W o'zgarsa — kontur chegarasi ham o'zgaradi; chuqurlik
    ops2, _ = _ev("pocket_rect", 720, 560, pars={"L": 300, "W": 120, "R": 0, "depth": 5, "cx": 100, "cy": 100})
    xs = [o["X"] for o in ops2 if o["kind"] in ("MillStart", "MillLine")]
    ys = [o["Y"] for o in ops2 if o["kind"] in ("MillStart", "MillLine")]
    assert (min(xs), max(xs), min(ys), max(ys)) == (-50, 250, 40, 160)
    assert next(o for o in ops2 if o["kind"] == "MillStart")["DP"] == 5
    assert not any(o["kind"] == "MillArcCenter" for o in ops2)           # R = 0 — yoy yo'q
    # radius tomon yarmidan katta bo'lsa — kesiladi (xatosiz)
    _, st3 = _ev("pocket_rect", 720, 560, pars={"L": 100, "W": 40, "R": 999})
    assert st3["errors"] == 0


def test_hole_circle_length_and_correction():
    ops, st = _ev("hole_circle", 720, 560, pars={"D": 40, "td": 8})
    assert st["mill_m"] == pytest.approx(math.pi * 40 / 1000, abs=1e-3)
    start = next(o for o in ops if o["kind"] == "MillStart")
    assert (start["X"], start["Y"]) == (340, 280) and start["C"] == 2 and start["DP"] == 16   # dz — o'tuvchi
    _, st = _ev("hole_circle", 720, 560, pars={"D": 100, "corr": 0})
    assert st["mill_m"] == pytest.approx(math.pi * 100 / 1000, abs=1e-3)


def test_outline_rounded_length():
    """Kontur: 4 to'g'ri chiziq + 4 yoy — perimetr 2(dx+dy) − 8r + 2πr."""
    for r in (0, 30, 100):
        _, st = _ev("outline_rounded", 720, 560, pars={"r": r})
        assert st["mill_m"] == pytest.approx((2 * (720 + 560) - 8 * r + 2 * math.pi * r) / 1000, abs=1e-3), r
    # radius kichik tomon yarmidan katta bo'lsa kesiladi: 300×300, r=999 -> doira (r = 150)
    _, st = _ev("outline_rounded", 300, 300, pars={"r": 999})
    assert st["mill_m"] == pytest.approx(2 * math.pi * 150 / 1000, abs=1e-3) and st["errors"] == 0


def test_facade_frame_single_and_double():
    ops, st = _ev("facade_frame", 600, 700)
    rects = [o for o in ops if o["kind"] == "MillRect"]
    assert len(rects) == 1 and (rects[0]["X"], rects[0]["Y"]) == (300, 350)
    assert (rects[0]["L"], rects[0]["W"], rects[0]["R"], rects[0]["DP"]) == (460, 560, 15, 4)
    ops, st = _ev("facade_frame", 600, 700, pars={"dbl": 1, "gap": 12, "m": 50})
    rects = [o for o in ops if o["kind"] == "MillRect"]
    assert len(rects) == 2 and (rects[1]["L"], rects[1]["W"], rects[1]["R"]) == (500 - 24, 600 - 24, 3)
    # ramka perimetri: 2(L+W) − 8R + 2πR, har ikki ramka yig'indisi
    exp = sum(2 * (r["L"] + r["W"]) - 8 * r["R"] + 2 * math.pi * r["R"] for r in rects) / 1000
    assert st["mill_m"] == pytest.approx(exp, abs=1e-3)


def test_row32_uses_array_and_is_centered():
    ops, st = _ev("row32", 720, 560)
    holes = [o for o in ops if o["kind"] == "DrillFront"]
    n = max(1, math.floor((720 - 2 * 64) / 32) + 1)            # 19
    assert len(holes) == 2 * n and st["drills"] == 2 * n
    row1 = sorted(o["X"] for o in holes if o["Y"] == 37)
    assert len(row1) == n and all(math.isclose(b - a, 32) for a, b in zip(row1, row1[1:]))
    assert math.isclose(row1[0] + row1[-1], 720)                # qator markazda (simmetrik)
    assert all(h["inside"] for h in holes)
    _, st1 = _ev("row32", 720, 560, pars={"both": 0, "pitch": 50})
    assert st1["drills"] == max(1, math.floor((720 - 128) / 50) + 1)
    # detal juda kichik — kamida 1 ta teshik, xatosiz
    _, st2 = _ev("row32", 100, 100)
    assert st2["drills"] >= 1 and st2["errors"] == 0


def test_side_panel_drilling_and_groove():
    ops, st = _ev("side_panel", 720, 560)
    conf = [o for o in ops if o["kind"] == "DrillFront" and o["DP"] == 16]
    pts = sorted((o["X"], o["Y"]) for o in conf)
    # dy >= 500 — o'rtadagi konfirmatlar ham: 4 chekka + 2 o'rta = 6
    assert pts == sorted([(8, 50), (8, 510), (712, 50), (712, 510), (8, 280), (712, 280)])
    pins = [o for o in ops if o["kind"] == "DrillFront" and o["DP"] == 13]
    n = math.floor((720 - 2 * (16 + 64)) / 32) + 1
    assert len(pins) == 2 * n
    gr = [o for o in ops if o["kind"] == "Groove"]
    assert len(gr) == 1 and gr[0]["Y1"] == 540 == gr[0]["Y2"] and gr[0]["DP"] == 8 and gr[0]["W"] == 4
    assert st["saw_m"] == pytest.approx(0.72, abs=1e-3)
    # parametrlarni o'chirish: qisqa panel (dy < 500), polka va paz o'chiq
    ops, st = _ev("side_panel", 720, 400, pars={"shelf": 0, "back": 0})
    assert st["drills"] == 4 and st["saw_m"] == 0


def test_back_groove_orientation():
    ops, _ = _ev("back_groove", 720, 560)
    g = next(o for o in ops if o["kind"] == "Groove")
    assert (g["X1"], g["Y1"], g["X2"], g["Y2"]) == (0, 540, 720, 540)
    ops, _ = _ev("back_groove", 720, 560, pars={"side": 1, "off": 10})
    g = next(o for o in ops if o["kind"] == "Groove")
    assert (g["X1"], g["Y1"], g["X2"], g["Y2"]) == (710, 0, 710, 560)


# ───────────────────────── API ─────────────────────────
def test_templates_api_roundtrip(client):
    lst = client.get("/api/xnc/templates?lang=uz").json()
    assert {t["id"] for t in lst if t["builtin"]} == {f"lib:{k}" for k in T.LIBRARY}
    one = client.get("/api/xnc/templates/lib:pocket_rect?lang=ru").json()
    assert one["builtin"] and one["program"][0]["cmd"] == "Par" and one["name"] == "Карман прямоугольный"
    assert client.get("/api/xnc/templates/lib:nope").status_code == 404
    assert client.get("/api/xnc/templates/u:999999").status_code == 404
    assert client.delete("/api/xnc/templates/lib:pocket_rect").status_code == 400      # o'rnatilgan — o'zgarmas
    # saqlash
    prog = [{"cmd": "DrillFront", "params": {"X": 50, "Y": 50, "DP": 12, "D": 8}, "comment": "", "children": []}]
    r = client.post("/api/xnc/templates", json={"name": "W1 test shablon", "program": prog, "description": "d"})
    assert r.status_code == 200, r.text
    tid = r.json()["id"]
    assert tid.startswith("u:") and r.json()["commands"] == 1 and not r.json()["builtin"]
    assert client.get(f"/api/xnc/templates/{tid}").json()["program"][0]["params"]["X"] == 50
    # upsert: bir xil nom — yangi qator yaratilmaydi
    r2 = client.post("/api/xnc/templates?upsert=true", json={"name": "W1 test shablon", "program": prog * 2})
    assert r2.json()["id"] == tid and r2.json()["commands"] == 2
    # eksport -> import (boshqa nom bilan)
    ex = client.get(f"/api/xnc/templates/{tid}/export")
    assert ex.status_code == 200 and "attachment" in ex.headers["content-disposition"]
    data = json.loads(ex.content)
    assert data["kind"] == "xnc_template" and data["app"] == "MebeliX Kroy" and len(data["program"]) == 2
    data["name"] = "W1 test import"
    imp = client.post("/api/xnc/templates/import", json=data)
    assert imp.status_code == 200 and imp.json()["commands"] == 2
    # buzuq fayllar — 400 (500 emas)
    for bad in ({}, {"kind": "xnc_template"}, {"kind": "xnc_template", "name": "x", "program": "abc"},
                {"kind": "xnc_template", "name": "x", "program": [{"cmd": "Nope"}]},
                {"kind": "xnc_template", "name": "x", "program": [1, 2]}, [1, 2], "text"):
        assert client.post("/api/xnc/templates/import", json=bad).status_code == 400, bad
    # juda chuqur / juda katta
    deep = {"cmd": "Com", "params": {}, "comment": "", "children": []}
    cur = deep
    for _i in range(40):
        cur["children"] = [{"cmd": "Com", "params": {}, "comment": "", "children": []}]
        cur = cur["children"][0]
    assert client.post("/api/xnc/templates/import", json={"kind": "xnc_template", "name": "deep", "program": [deep]}).status_code == 400
    # ro'yxatda ikkalasi ham bor; o'chirish
    names = {t["name"] for t in client.get("/api/xnc/templates").json() if not t["builtin"]}
    assert {"W1 test shablon", "W1 test import"} <= names
    for t in client.get("/api/xnc/templates").json():
        if t["name"].startswith("W1 test"):
            assert client.delete(f"/api/xnc/templates/{t['id']}").status_code == 200
    assert client.delete(f"/api/xnc/templates/{tid}").status_code == 404


def test_templates_included_in_settings_backup(client):
    prog = [{"cmd": "Com", "params": {}, "comment": "zaxira", "children": []}]
    tid = client.post("/api/xnc/templates", json={"name": "W1 backup", "program": prog}).json()["id"]
    b = client.get("/api/backup/settings").json()
    assert any(x["name"] == "W1 backup" for x in b["profiles"]["xnc_template"])
    client.delete(f"/api/xnc/templates/{tid}")


def test_apply_template_replace_and_append(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)               # detal 480×800
    # replace: o'rnatilgan shablon
    r = client.post(f"/api/projects/{pid}/operations/{xid}/xnc/apply-template",
                    json={"template": "lib:row32", "mode": "replace", "lang": "ru"})
    assert r.status_code == 200, r.text
    x = _op(r.json(), xid)["xnc"]
    assert x["program"][0]["cmd"] == "Par" and x["par_values"] == {}
    st = client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()
    assert st["drills"] == 2 * max(1, math.floor((480 - 128) / 32) + 1) and st["errors"] == 0
    n_before = len(x["program"])
    # append: yana shu shablon — Par lar qayta e'lon qilinmaydi, buyruqlar oxiriga qo'shiladi
    r = client.post(f"/api/projects/{pid}/operations/{xid}/xnc/apply-template", json={"template": "lib:row32", "mode": "append"})
    x = _op(r.json(), xid)["xnc"]
    n_par = sum(1 for c in x["program"] if c["cmd"] == "Par")
    assert n_par == 6 and len(x["program"]) == 2 * n_before - 6
    # boshqa shablon + Par qiymati bilan append
    client.patch(f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"par_values": {"pitch": 64}}})
    r = client.post(f"/api/projects/{pid}/operations/{xid}/xnc/apply-template", json={"template": "lib:back_groove", "mode": "append"})
    assert _op(r.json(), xid)["xnc"]["par_values"] == {"pitch": 64}                 # mavjud qiymatlar saqlanadi
    # xato holatlar
    assert client.post(f"/api/projects/{pid}/operations/{xid}/xnc/apply-template", json={"template": "lib:zzz"}).status_code == 404
    assert client.post(f"/api/projects/{pid}/operations/{cs}/xnc/apply-template", json={"template": "lib:row32"}).status_code == 400
    assert client.post(f"/api/projects/{pid}/operations/{xid}/xnc/apply-template",
                       json={"template": "lib:row32", "mode": "zz"}).status_code == 422
    # foydalanuvchi shabloni (saqlangan dastur) — operatsiyadan shablon, boshqa operatsiyaga qo'llash
    prog = _op(client.get(f"/api/projects/{pid}").json(), xid)["xnc"]["program"]
    tid = client.post("/api/xnc/templates", json={"name": "W1 apply", "program": prog,
                                                  "par_values": {"pitch": 50}}).json()["id"]
    r = client.post(f"/api/projects/{pid}/operations/{xid}/xnc/apply-template", json={"template": tid, "mode": "replace"})
    assert _op(r.json(), xid)["xnc"]["par_values"] == {"pitch": 50} and len(_op(r.json(), xid)["xnc"]["program"]) == len(prog)
    client.delete(f"/api/xnc/templates/{tid}")


def test_merge_program_unit():
    a = [C(cmd="Par", params={"name": "w", "value": 1}), C(cmd="Com")]
    b = [C(cmd="Par", params={"name": "w", "value": 9}), C(cmd="Par", params={"name": "h", "value": 2}), C(cmd="Com")]
    out, skipped = T.merge_program(a, b, "append")
    assert skipped == ["w"] and [c.cmd for c in out] == ["Par", "Com", "Par", "Com"]
    assert out[0].params["value"] == 1                                  # mavjud Par o'zgarmadi
    out, skipped = T.merge_program(a, b, "replace")
    assert skipped == [] and len(out) == 3 and out is not b             # chuqur nusxa


def test_template_validation_limits():
    big = [C(cmd="Com") for _ in range(T.MAX_NODES + 1)]
    with pytest.raises(ValueError):
        T.XncTemplate(program=big)
    with pytest.raises(T.TemplateError):
        T.precheck_raw([{"cmd": "Com", "children": [{"cmd": "Com"}] * 2}] * 2000)
