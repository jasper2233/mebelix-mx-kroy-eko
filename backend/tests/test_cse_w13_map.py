"""W13 / CSE-009, CSE-016: kartaga alohida torsovka («Торцовка листа»), kartalar tartibi (Ctrl+↑/↓), karta izohi,
paket va parallel tahrir izi; qo'lda tahrirlangan natijaning hisob-kitob / ombor / hisobotga o'tishi; undo/redo.

Sheet 2750×1830, torsovka 0, propil 3, minimal obrezka 5."""
import json

from app.models import CutMap, CuttingResult
from cse_w13_util import (C, P, W, bad, blank, card, check, deep, edit, leaves_p, make_project, ok, op_of, raw_post,
                          uid_count)


def _strip(client, qty=1, parts=None, cut=None):
    pid, cs, sh = make_project(client, parts or [(300, 500, qty), (200, 500, qty), (100, 500, qty)], cut=cut)
    tree = C(0, 0, 2750, 1830, "y", [
        C(0, 0, 2750, 500, "x", [P(0, 0, 300, 500, 1), P(303, 0, 200, 500, 2), W(506, 0, 2244, 500)]),
        W(0, 503, 2750, 1327)])
    res = edit(client, pid, cs, card(sh, tree), type="copies", map=1, copies=1)
    assert res.status_code == 200, res.text
    return pid, cs, sh, res.json()


def _cmds(res, mi=0):
    return [(c["code"], c["level"], c["size"]) for c in res["maps"][mi]["commands"]]


# ───────────────────────── Торцовка листа ─────────────────────────
def test_map_trim_shifts_zone_and_updates_commands(client):
    pid, cs, sh, res = _strip(client)
    assert not any(c[0] == "T" for c in _cmds(res))
    r = ok(client, pid, cs, res, type="map_trim", map=1, trim_length=10)
    m = r["maps"][0]
    assert m["trim_length"] == 10 and m["trim_width"] is None
    assert ("T", 1, 10.0) in _cmds(r)                                  # yuqoridan torsovka 10
    assert min(pl["y"] for pl in m["placements"]) == 13                # 10 + propil 3 (zona boshi)
    assert m["strips"][0]["w"] == 1804                                 # 1830 − 2·(10 + 3): quyidagi otstup torsovkaga teng
    assert m["strips"][0]["c"][-1]["w"] == 1301                        # oxirgi chiqindi 26 mm qisqardi
    # ikki tomondan: ТШ va minimal otstup (o'ngda)
    r2 = ok(client, pid, cs, r, type="map_trim", map=1, trim_width=7, end_offset_right=0)
    m2 = r2["maps"][0]
    assert m2["trim_length"] == 10 and m2["trim_width"] == 7 and m2["end_offset_right"] == 0
    assert min(pl["x"] for pl in m2["placements"]) == 10               # 7 + 3
    assert m2["strips"][0]["l"] == 2750 - 10 - 0                       # o'ngda otstup 0 — kesim yo'q
    # null — list qatori / operatsiya qiymatiga qaytish: boshlang'ich holatga aynan
    r3 = ok(client, pid, cs, r2, type="map_trim", map=1, trim_length=None, trim_width=None, end_offset_right=None)
    assert r3["maps"][0]["strips"] == res["maps"][0]["strips"]
    assert all(r3["maps"][0][k] is None for k in ("trim_length", "trim_width", "end_offset_bottom", "end_offset_right"))
    # torsovka o'sha kartada saqlanib qoladi (boshqa amal torsovkani yo'qotmaydi)
    r4 = ok(client, pid, cs, r, type="remove", map=1, path=[0, 0])
    assert r4["maps"][0]["trim_length"] == 10 and min(pl["y"] for pl in r4["maps"][0]["placements"]) == 13


def test_map_trim_only_changes_target_map_and_survives_save(client):
    pid, cs, sh, res = _strip(client)
    two = ok(client, pid, cs, res, type="add_map", sheet_id=sh["id"])
    r = ok(client, pid, cs, two, type="map_trim", map=2, trim_length=12, trim_width=12)
    assert r["maps"][0]["trim_length"] is None and r["maps"][1]["trim_length"] == 12
    assert r["maps"][0]["strips"] == two["maps"][0]["strips"]
    # saqlash: loyihada karta torsovkasi qoladi; qayta tahrir (ochib yopish) uni buzmaydi
    p = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=r).json()
    saved = op_of(p, cs)["result"]
    assert saved["maps"][1]["trim_length"] == 12 and saved["maps"][1]["trim_width"] == 12
    again = ok(client, pid, cs, saved, type="copies", map=1, copies=1)
    assert again["maps"][1]["strips"] == saved["maps"][1]["strips"]
    check(pid, cs, saved)


def test_map_trim_rejects_bad_values_and_overflowing_parts(client):
    pid, cs, sh, res = _strip(client)
    for v in (-1, 501, "abc", True, [1], {"a": 1}, "inf", "1e999", 10 ** 30):
        r = edit(client, pid, cs, res, type="map_trim", map=1, trim_length=v)
        assert r.status_code == 422, (v, r.status_code, r.text[:120])
    r = raw_post(client, f"/api/projects/{pid}/operations/{cs}/edit",
                 '{"result": %s, "action": {"type": "map_trim", "map": 1, "trim_length": NaN}}' % json.dumps(res))
    assert r.status_code == 422
    r = raw_post(client, f"/api/projects/{pid}/operations/{cs}/edit",
                 '{"result": %s, "action": {"type": "map_trim", "map": 1, "trim_width": Infinity}}' % json.dumps(res))
    assert r.status_code == 422
    bad(client, pid, cs, res, type="map_trim", map=1)                    # hech narsa berilmagan
    bad(client, pid, cs, res, type="map_trim", map=9, trim_length=1)    # yo'q karta
    # foydali zona detallardan kichik bo'lib qolsa — rad etiladi (detal torsovkaga tushib ketmaydi)
    pid, cs, sh = make_project(client, [(300, 1800, 1)])
    tree = C(0, 0, 2750, 1830, "y", [C(0, 0, 2750, 1800, "x", [P(0, 0, 300, 1800, 1), W(303, 0, 2447, 1800)]),
                                     W(0, 1803, 2750, 27)])
    full = edit(client, pid, cs, card(sh, tree), type="copies", map=1, copies=1).json()
    ok(client, pid, cs, full, type="map_trim", map=1, trim_length=0, end_offset_bottom=0)     # sig'adi
    d = bad(client, pid, cs, full, type="map_trim", map=1, trim_length=20)
    assert d
    bad(client, pid, cs, full, type="map_trim", map=1, trim_length=500, trim_width=500, end_offset_bottom=500)


def test_validate_rejects_part_in_trim_area_of_forged_tree(client):
    """Soxta daraxt ildizi foydali zonadan chiqib, detalni torsovka joyiga qo'ya olmaydi."""
    pid, cs, sh = make_project(client, [(300, 500, 1)], cut={"trim_length": 5, "trim_width": 5})
    # zona: ox = oy = 5 + 3 = 8; ildiz torsovka ichiga chiqqan
    tree = C(0, 0, 2750, 1830, "y", [C(0, 0, 2750, 500, "x", [P(0, 0, 300, 500, 1), W(303, 0, 2447, 500)]),
                                     W(0, 503, 2750, 1327)])
    r = edit(client, pid, cs, card(sh, tree), type="copies", map=1, copies=1)
    assert r.status_code == 422
    r = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=card(sh, tree))
    assert r.status_code == 422


# ───────────────────────── kartalar tartibi, izoh ─────────────────────────
def _two_maps(client):
    pid, cs, sh = make_project(client, [(300, 500, 1), (200, 500, 3)])
    res = blank(client, pid, cs, sh)
    res = ok(client, pid, cs, res, type="place", map=1, path=[0], uid=1)
    res = ok(client, pid, cs, res, type="add_map", sheet_id=sh["id"])
    res = ok(client, pid, cs, res, type="place_multi", map=2, path=[0], uid=2)
    res = ok(client, pid, cs, res, type="comment", map=1, comment="bir")
    res = ok(client, pid, cs, res, type="comment", map=2, comment="ikki")
    return pid, cs, sh, res


def test_move_map_reorders_with_content_and_renumbers(client):
    pid, cs, sh, res = _two_maps(client)
    assert [m["parts_count"] for m in res["maps"]] == [1, 3]
    r = ok(client, pid, cs, res, type="move_map", map=2, to="up")
    assert [m["parts_count"] for m in r["maps"]] == [3, 1] and [m["comment"] for m in r["maps"]] == ["ikki", "bir"]
    assert [m["index"] for m in r["maps"]] == [1, 2]
    r = ok(client, pid, cs, res, type="move_map", map=1, to="down")
    assert [m["parts_count"] for m in r["maps"]] == [3, 1]
    r = ok(client, pid, cs, res, type="move_map", map=1, to="last")
    assert [m["parts_count"] for m in r["maps"]] == [3, 1]
    r = ok(client, pid, cs, r, type="move_map", map=2, to="first")
    assert [m["parts_count"] for m in r["maps"]] == [1, 3]
    for kw in (dict(map=1, to="up"), dict(map=2, to="down"), dict(map=1, to="first"), dict(map=2, to="last"),
               dict(map=1, to="sideways"), dict(map=1, to=5), dict(map=1, to=None), dict(map=1)):
        r = edit(client, pid, cs, res, type="move_map", **kw)
        assert r.status_code == 422, (kw, r.status_code)
    # qoldiq raqamlari (Д1, Д2…) tartibdan keyin qayta raqamlanadi
    r = ok(client, pid, cs, res, type="move_map", map=2, to="first")
    nums = [o["number"] for m in r["maps"] for o in m["offcuts"] if o["kind"] == "remnant"]
    assert nums == sorted(nums) and nums[:1] == [1]


def test_map_comment_edit_limit_and_type(client):
    pid, cs, sh, res = _two_maps(client)
    r = ok(client, pid, cs, res, type="comment", map=1, comment="x" * 5000)
    assert len(r["maps"][0]["comment"]) == 2000
    r = ok(client, pid, cs, r, type="comment", map=1, comment="")
    assert r["maps"][0]["comment"] == "" and r["maps"][1]["comment"] == "ikki"
    for v in (5, None, ["a"], {"a": 1}):
        r = edit(client, pid, cs, res, type="comment", map=1, comment=v)
        assert r.status_code == 422
    # izoh boshqa amallardan keyin ham saqlanadi
    r = ok(client, pid, cs, res, type="copies", map=2, copies=1)
    assert [m["comment"] for m in r["maps"]] == ["bir", "ikki"]
    # PATCH ham shu chegarada
    full = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=res).json()
    p = client.patch(f"/api/projects/{pid}/operations/{cs}/maps/1", json={"comment": "y" * 4000}).json()
    assert len(op_of(p, cs)["result"]["maps"][0]["comment"]) == 2000 and full


# ───────────────────────── paket, tekshirish, parallel tahrir izi ─────────────────────────
def test_batch_applies_in_order_and_is_atomic(client):
    pid, cs, sh = make_project(client, [(300, 500, 4)])
    res = blank(client, pid, cs, sh)
    acts = [dict(type="place_multi", map=1, path=[0], uid=1, count=3), dict(type="comment", map=1, comment="paket"),
            dict(type="add_map", sheet_id=sh["id"]), dict(type="place_multi", map=2, path=[0], uid=1)]
    r = client.post(f"/api/projects/{pid}/operations/{cs}/edit/batch", json={"result": res, "actions": acts})
    assert r.status_code == 200, r.text
    out = r.json()
    check(pid, cs, out)
    assert [m["parts_count"] for m in out["maps"]] == [3, 1] and out["maps"][0]["comment"] == "paket"
    # xuddi shu amallar bittalab — bir xil natija
    cur = res
    for a in acts:
        cur = ok(client, pid, cs, cur, **a)
    assert [m["strips"] for m in cur["maps"]] == [m["strips"] for m in out["maps"]]
    # biror amal xato — hammasi bekor, xabarda tartib raqami
    acts2 = [acts[0], dict(type="place_multi", map=1, path=[0], uid=1, count=99)]
    r = client.post(f"/api/projects/{pid}/operations/{cs}/edit/batch", json={"result": res, "actions": acts2})
    assert r.status_code == 422 and "2" in r.json()["detail"] and "place_multi" in r.json()["detail"]
    r = client.post(f"/api/projects/{pid}/operations/{cs}/edit/batch",
                    json={"result": res, "actions": [dict(type="comment", map=1, comment="a")] * 201})
    assert r.status_code == 422
    r = client.post(f"/api/projects/{pid}/operations/{cs}/edit/batch", json={"result": res, "actions": ["oops", 5]})
    assert r.status_code == 422
    assert client.post(f"/api/projects/{pid}/operations/{cs}/edit/batch", json={"result": res, "actions": []}).status_code == 200


def test_check_endpoint_reports_validity_without_saving(client):
    pid, cs, sh, res = _strip(client)
    r = client.post(f"/api/projects/{pid}/operations/{cs}/edit/check", json=res)
    assert r.status_code == 200 and r.json()["ok"] and r.json()["maps"][0]["parts"] == 2
    forged = deep(res)
    strip = forged["maps"][0]["strips"][0]["c"][0]
    strip["c"][1]["x"] = 100                                          # P2 P1 ustiga — propilsiz
    r = client.post(f"/api/projects/{pid}/operations/{cs}/edit/check", json=forged)
    assert r.status_code == 200 and not r.json()["ok"] and r.json()["errors"]
    assert op_of(client.get(f"/api/projects/{pid}").json(), cs)["result"] is None      # hech narsa saqlanmadi


def test_parallel_editor_detected_by_rev_and_409(client):
    pid, cs, sh = make_project(client, [(300, 500, 2)])
    assert client.get(f"/api/projects/{pid}/operations/{cs}/edit/rev").json()["rev"] == "none"
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    rev0 = client.get(f"/api/projects/{pid}/operations/{cs}/edit/rev").json()["rev"]
    assert rev0 != "none" and rev0 == client.get(f"/api/projects/{pid}/operations/{cs}/edit/rev").json()["rev"]
    base = client.get(f"/api/projects/{pid}").json()
    draft_a = ok(client, pid, cs, op_of(base, cs)["result"], type="comment", map=1, comment="A", )
    draft_b = ok(client, pid, cs, op_of(base, cs)["result"], type="comment", map=1, comment="B")
    # A birinchi saqlaydi (rev mos) — yangi iz
    r = client.put(f"/api/projects/{pid}/operations/{cs}/result?base={rev0}", json=draft_a)
    assert r.status_code == 200
    rev1 = client.get(f"/api/projects/{pid}/operations/{cs}/edit/rev").json()["rev"]
    assert rev1 != rev0
    # B eski iz bilan — 409, A ning izohi o'z joyida
    r = client.put(f"/api/projects/{pid}/operations/{cs}/result?base={rev0}", json=draft_b)
    assert r.status_code == 409 and "другом" in r.json()["detail"]
    assert op_of(client.get(f"/api/projects/{pid}").json(), cs)["result"]["maps"][0]["comment"] == "A"
    r = client.put(f"/api/projects/{pid}/operations/{cs}/result?base={rev0}", json=draft_b,
                   headers={"Accept-Language": "uz"})
    assert r.status_code == 409 and "boshqa" in r.json()["detail"]
    # yangi iz bilan — o'tadi; `base` berilmasa — eski xulq (tekshiruvsiz)
    assert client.put(f"/api/projects/{pid}/operations/{cs}/result?base={rev1}", json=draft_b).status_code == 200
    assert client.put(f"/api/projects/{pid}/operations/{cs}/result", json=draft_a).status_code == 200


# ───────────────────────── hisob-kitob, ombor, hisobot, undo ─────────────────────────
def _remnant_card(client, wide=2000):
    """Bitta katta detal + o'ngda bo'sh joy (qoldiq). Qaytaradi (pid, cs, sh, res)."""
    pid, cs, sh = make_project(client, [(wide, 1800, 1), (300, 200, 2)])
    tree = C(0, 0, 2750, 1830, "x", [C(0, 0, wide, 1830, "y", [P(0, 0, wide, 1800, 1), W(0, 1803, wide, 27)]),
                                     W(wide + 3, 0, 2750 - wide - 3, 1830)])
    res = edit(client, pid, cs, card(sh, tree), type="copies", map=1, copies=1)
    assert res.status_code == 200, res.text
    return pid, cs, sh, res.json()


def test_remnants_reclassified_after_every_edit(client):
    pid, cs, sh, res = _remnant_card(client, wide=2000)
    rem = res["remnants"]
    assert len(rem) == 1 and rem[0]["business"] and (rem[0]["length"], rem[0]["width"]) == (747, 1830)
    assert res["remnant_area_m2"] == round(747 * 1830 / 1e6, 4)
    assert abs(res["material_qty_m2"] - (2750 * 1830 / 1e6 - res["remnant_area_m2"])) < 1e-3
    # katta detal olib tashlansa — butun list деловой qoldiq
    r = ok(client, pid, cs, res, type="remove", map=1, path=[0, 0])
    assert len(r["remnants"]) == 1 and (r["remnants"][0]["length"], r["remnants"][0]["width"]) == (2750, 1830)
    assert r["maps"][0]["parts_count"] == 0 and r["remnants"][0]["business"]
    # kichik detallar qo'yilgach — qoldiq tushib ketadi (mayda qoldiq / chiqindi qayta tasniflanadi)
    r2 = ok(client, pid, cs, r, type="place_multi", map=1, path=[0], uid=2)
    assert uid_count(r2, 2) == 2
    assert r2["remnant_area_m2"] > 0 and all(o["kind"] in ("remnant", "waste") for o in r2["maps"][0]["offcuts"])
    # 2600 mm detal: qolgan 147 mm — chiqindi (ikkala tomoni ham chegaradan kichik)
    pid, cs, sh, res = _remnant_card(client, wide=2600)
    assert res["remnants"] == [] and res["remnant_area_m2"] == 0
    assert any(o["kind"] == "waste" and o["length"] == 147 for o in res["maps"][0]["offcuts"])
    assert res["material_qty_m2"] == round(2750 * 1830 / 1e6, 4)


def test_manual_result_flows_into_calc_report_and_warehouse(client):
    pid, cs, sh, res = _remnant_card(client, wide=2000)
    p = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=res).json()
    op = op_of(p, cs)
    # hisoblagichlar (ИК / Ост / list)
    big, small = op["parts"][0], op["parts"][1]
    assert (big["used_qty"], big["left_qty"], small["used_qty"], small["left_qty"]) == (1, 0, 0, 2)
    assert op["sheets"][0]["used_qty"] == 1 and op["result"]["manual"] and op["result"]["unplaced"] == [small["id"]] * 2
    assert op["result"]["total_sheets"] == 1 and op["result"]["sheets_per_pack"] >= 1
    q = client.get(f"/api/projects/{pid}/operations/{cs}/cs-quantities").json()
    assert q["estimated"] is False and abs(q["material_qty_m2"] - op["result"]["material_qty_m2"]) < 1e-3
    # hisobot: sig'magan (joylashmagan) detallar jadvali
    ps = client.get("/api/settings/print/default").json()
    ps.update(cs_unplaced=True, cs_maps=True)
    html = client.post(f"/api/projects/{pid}/report", json=ps).text
    assert "D2" in html and "D1" in html
    # ombor: деловой qoldiq taklifi va omborga yozish — qo'lda natijadan
    rem = client.get(f"/api/projects/{pid}/operations/{cs}/remnants").json()
    assert rem["saved"] is False and [{k: g[k] for k in ("length", "width", "qty")} for g in rem["remnants"]] == [{"length": 1830.0, "width": 747.0, "qty": 1}]
    out = client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").json()
    assert len(out["added"]) == 1 and out["added"][0]["length"] == 1830 and out["added"][0]["width"] == 747
    rid = out["added"][0]["id"]
    rows = {r["id"]: r for r in client.get("/api/remnants").json()}
    assert rid in rows
    # omborga yozilgan natijani qayta tahrirlab saqlash: yozuv avtomatik bekor qilinadi (kroyni qayta qilish kabi)
    res2 = ok(client, pid, cs, op["result"], type="remove", map=1, path=[0, 0])
    p2 = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=res2).json()
    assert op_of(p2, cs)["result"]["remnants_saved"] is False
    assert rid not in {r["id"] for r in client.get("/api/remnants").json()}
    rem2 = client.get(f"/api/projects/{pid}/operations/{cs}/remnants").json()
    assert [{k: g[k] for k in ("length", "width", "qty")} for g in rem2["remnants"]] == [{"length": 2750.0, "width": 1830.0, "qty": 1}]


def test_taken_remnants_survive_edits_until_remnant_changes(client):
    pid, cs, sh, res = _remnant_card(client, wide=2000)
    client.put(f"/api/projects/{pid}/operations/{cs}/result", json=res)
    g = client.get(f"/api/projects/{pid}/operations/{cs}/remnant-groups").json()["groups"][0]
    p = client.put(f"/api/projects/{pid}/operations/{cs}/result/taken", json={"key": g["key"], "qty": 1}).json()
    saved = op_of(p, cs)["result"]
    assert saved["taken_remnants"] == {g["key"]: 1}
    # qoldiqqa tegmaydigan amal — «Исп. кол-во» saqlanadi
    r = ok(client, pid, cs, saved, type="comment", map=1, comment="x")
    assert r["taken_remnants"] == {g["key"]: 1}
    p = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=r).json()
    assert op_of(p, cs)["result"]["taken_remnants"] == {g["key"]: 1}
    assert client.get(f"/api/projects/{pid}/operations/{cs}/remnants").json()["remnants"] == []   # olib ketilgan — yozilmaydi
    # qoldiq o'lchami o'zgardi — eskirgan kalit tashlanadi
    r2 = ok(client, pid, cs, r, type="remove", map=1, path=[0, 0])
    assert r2["taken_remnants"] == {}


def test_edit_is_one_undo_step_and_roundtrips(client):
    pid, cs, sh = make_project(client, [(300, 500, 2), (200, 400, 2)])
    r0 = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").json()
    assert not r0["manual"]
    first_part = [p for p, _n in leaves_p(r0["maps"][0]["strips"][0])][:1]
    edited = ok(client, pid, cs, r0, type="remove", map=1, paths=first_part)
    p = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=edited).json()
    assert op_of(p, cs)["result"]["manual"] and len(op_of(p, cs)["result"]["unplaced"]) == 1
    # loyiha darajasidagi bekor qilish: tahrirdan oldingi natija
    u = client.post(f"/api/projects/{pid}/undo").json()
    assert not op_of(u, cs)["result"]["manual"] and op_of(u, cs)["result"]["unplaced"] == []
    assert op_of(u, cs)["result"]["maps"][0]["strips"] == r0["maps"][0]["strips"]
    rd = client.post(f"/api/projects/{pid}/redo").json()
    assert op_of(rd, cs)["result"]["manual"] and len(op_of(rd, cs)["result"]["unplaced"]) == 1
    # eski JSON (karta torsovkasi maydonlarisiz) ochiladi — standart None
    legacy = deep(r0)
    for m in legacy["maps"]:
        for k in ("trim_length", "trim_width", "end_offset_bottom", "end_offset_right"):
            m.pop(k, None)
    m = CuttingResult.model_validate(legacy).maps[0]
    assert isinstance(m, CutMap) and m.trim_length is None and m.end_offset_right is None
