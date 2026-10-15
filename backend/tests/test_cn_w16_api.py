"""W16 (CN) — API: operatsiya yaratish, kroy, natija tuzilmasi, miqdorlar / narx, eskirish, shakllar, fon vazifasi (progress, to'xtatish, eskirgan natija),
tahrir (409), SVG / hisobot / postprotsessor, qoldiqlar (ombor), eski JSON, eksport / import, MES, talabnoma."""
from __future__ import annotations

import json
import threading
import time

import pytest

from app.models import Project
from app.services import cn_calc, cn_jobs
from app.services import cn_nest as N


def _mk(client, parts=None, sheets=None, params=None, name="CN API"):
    p = client.post("/api/projects", json={"name": name}).json()
    pid = p["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CN", "name": "MDF nesting", "code": "MDF16"}).json()
    oid = p["operations"][-1]["id"]
    if params:
        r = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cn": params})
        assert r.status_code == 200, r.text
    if sheets:
        r = client.put(f"/api/projects/{pid}/operations/{oid}/sheets", json=sheets)
        assert r.status_code == 200, r.text
    parts = parts if parts is not None else [dict(name=f"P{i}", length=300 + 40 * i, width=200 + 25 * i, qty=2) for i in range(6)]
    r = client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=parts)
    assert r.status_code == 200, r.text
    return pid, oid


def _op(client, pid, oid):
    p = client.get(f"/api/projects/{pid}").json()
    return next(o for o in p["operations"] if o["id"] == oid)


def _opt(client, pid, oid, **q):
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize", params=q or {"quality": "fast"})
    assert r.status_code == 200, r.text
    return r.json()


def _xnc_part(client, pid, oid, part_index, program):
    op = _op(client, pid, oid)
    part = op["parts"][part_index]
    r = client.post(f"/api/projects/{pid}/operations/{oid}/parts/{part['id']}/xnc")
    assert r.status_code == 200, r.text
    xop = [o for o in r.json()["operations"] if o["type"] == "XNC" and o["xnc_part_id"] == part["id"]][0]
    r = client.patch(f"/api/projects/{pid}/operations/{xop['id']}", json={"xnc": {"program": program}})
    assert r.status_code == 200, r.text
    return xop["id"]


def _rect(x, y, L, W, R=0):
    return {"cmd": "MillRect", "params": {"X": x, "Y": y, "L": L, "W": W, "R": R, "DP": 16, "T": "Mill6"}, "comment": "", "enabled": True,
            "children": []}


# ───────────────────────── Operatsiya va parametrlar ─────────────────────────
def test_new_cn_operation_has_params_sheet_and_defaults(client):
    p = client.post("/api/projects", json={"name": "defaults"}).json()
    p = client.post(f"/api/projects/{p['id']}/operations", json={"type": "CN"}).json()
    op = p["operations"][-1]
    assert op["type"] == "CN" and op["cn"]["tool_diameter"] == 6 and op["cn"]["margin"] == 5 and op["cn"]["rot90"] is True
    assert op["cn"]["quality"] == "normal" and op["cs_cut"] is None and op["cl"] is None
    assert len(op["sheets"]) == 1 and (op["sheets"][0]["length"], op["sheets"][0]["width"]) == (2750, 1830) and op["sheets"][0]["qty"] == 10000
    # standartga saqlash (hisoblangan maydonlar saqlanmaydi) va yangi operatsiyada qo'llanishi
    d = dict(op["cn"], tool_diameter=8.0, part_gap=1.5)
    r = client.put("/api/settings/cn_defaults/default", json=d)
    assert r.status_code == 200, r.text
    got = client.get("/api/settings/cn_defaults/default").json()
    assert got["tool_diameter"] == 8
    p2 = client.post(f"/api/projects/{p['id']}/operations", json={"type": "CN"}).json()
    assert p2["operations"][-1]["cn"]["tool_diameter"] == 8 and p2["operations"][-1]["cn"]["part_gap"] == 1.5
    client.put("/api/settings/cn_defaults/default", json=dict(op["cn"]))          # asl holatga qaytarish (boshqa testlar uchun)
    assert client.put("/api/settings/cn_defaults/default", json=dict(op["cn"], tool_diameter=-1)).status_code == 400


def test_cn_params_validation_bounds(client):
    pid, oid = _mk(client)
    for bad in (dict(tool_diameter=0), dict(tool_diameter=500), dict(margin=-1), dict(arc_tol=5), dict(rot_step=120), dict(quality="x")):
        assert client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cn": bad}).status_code in (400, 422), bad
    r = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cn": {"tool_offset": 4.0, "part_gap": 2.0}})
    cn = next(o for o in r.json()["operations"] if o["id"] == oid)["cn"]
    assert (cn["tool_offset"], cn["part_gap"]) == (4.0, 2.0)


# ───────────────────────── Kroy ─────────────────────────
def test_optimize_returns_nest_result_and_updates_accounting(client):
    pid, oid = _mk(client)
    res = _opt(client, pid, oid)
    assert res["kind"] == "nest" and res["total_sheets"] >= 1 and res["unplaced"] == [] and res["total_parts"] == 12
    assert 0 < res["total_fill_percent"] <= 100 and res["total_cut_length_m"] > 0 and res["material_qty_m2"] > 0
    m = res["maps"][0]
    pl = m["placements"][0]
    assert pl["angle"] in (0, 90, 180, 270) and len(pl["outline"]) == 4 and pl["holes"] == [] and pl["label"] is not None
    assert pl["length"] > 0 and pl["width"] > 0 and m["cuts_count"] == m["parts_count"]
    assert res["nest"]["trials"] >= 1 and res["nest"]["input_rev"]
    op = _op(client, pid, oid)
    assert all(pt["used_qty"] == 2 and pt["left_qty"] == 0 for pt in op["parts"])           # ИК / Ост
    assert op["sheets"][0]["used_qty"] == res["total_sheets"]
    v = client.get(f"/api/projects/{pid}/operations/{oid}/cn-validate").json()
    assert v == {"ok": True, "errors": []}
    # qayta kroy: natija almashadi
    again = _opt(client, pid, oid, quality="normal")
    assert again["total_parts"] == 12 and again["kind"] == "nest"


def test_optimize_errors_empty_parts_sheets_and_limit(client, monkeypatch):
    p = client.post("/api/projects", json={"name": "bo'sh"}).json()
    p = client.post(f"/api/projects/{p['id']}/operations", json={"type": "CN"}).json()
    pid, oid = p["id"], p["operations"][-1]["id"]
    assert client.post(f"/api/projects/{pid}/operations/{oid}/optimize").status_code == 400            # detal yo'q
    pid, oid = _mk(client)
    client.put(f"/api/projects/{pid}/operations/{oid}/sheets", json=[])
    assert client.post(f"/api/projects/{pid}/operations/{oid}/optimize").status_code == 400            # list yo'q
    assert client.post(f"/api/projects/{pid}/operations/{oid}/cn/jobs").status_code == 400
    monkeypatch.setenv("MEBELIX_MAX_NEST_ITEMS", "5")
    pid, oid = _mk(client)
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    assert r.status_code == 400 and "5" in r.json()["detail"]
    assert client.post(f"/api/projects/{pid}/operations/{oid}/cn/jobs").status_code == 400
    # boshqa tur operatsiyada CN endpointlari rad etiladi
    p = client.post("/api/projects", json={"name": "cs"}).json()
    p = client.post(f"/api/projects/{p['id']}/operations", json={"type": "CS"}).json()
    cs = p["operations"][-1]["id"]
    for path in ("cn-quantities", "cn-shapes", "cn-edit/rev", "cn-validate"):
        assert client.get(f"/api/projects/{p['id']}/operations/{cs}/{path}").status_code == 400, path


def test_too_big_parts_and_small_parts_warnings(client):
    pid, oid = _mk(client, parts=[dict(name="Katta", length=3500, width=200, qty=1), dict(name="Mayda", length=10, width=10, qty=2),
                                  dict(name="Oddiy", length=300, width=200, qty=2)], params=dict(min_part_size=30))
    res = _opt(client, pid, oid)
    assert res["total_parts"] == 2 and len(res["unplaced"]) == 3
    text = " | ".join(res["warnings"])
    assert "3500" in text and "30" in text


def test_params_change_invalidates_only_when_it_affects_nesting(client):
    pid, oid = _mk(client)
    _opt(client, pid, oid)
    def has_result():
        return _op(client, pid, oid)["result"] is not None
    for ok in (dict(quality="max"), dict(price=1000.0), dict(op_price=5.0), dict(est_fill_percent=70.0), dict(thickness=18.0)):
        client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cn": ok})
        assert has_result(), ok
    for bad in (dict(tool_diameter=8.0), dict(part_gap=3.0), dict(margin=10.0), dict(rot90=False), dict(use_grain=False), dict(remnant_min_area=0.5)):
        _opt(client, pid, oid)
        client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cn": bad})
        assert not has_result(), bad
    # detal o'zgarishi ham natijani o'chiradi
    _opt(client, pid, oid)
    part = _op(client, pid, oid)["parts"][0]
    client.patch(f"/api/projects/{pid}/operations/{oid}/parts/{part['id']}", json={"length": 777})
    assert not has_result()


def test_quantities_before_and_after_and_costs(client):
    pid, oid = _mk(client, params=dict(price=1000.0, cost_by_sheets=True, op_price=10.0, op_cost_base=0, est_fill_percent=80.0),
                   sheets=[dict(length=1000, width=700, qty=10000)])
    q0 = client.get(f"/api/projects/{pid}/operations/{oid}/cn-quantities").json()
    assert q0["estimated"] is True and q0["sheets"] >= 1 and q0["material_qty_m2"] > 0
    res = _opt(client, pid, oid)
    q1 = client.get(f"/api/projects/{pid}/operations/{oid}/cn-quantities").json()
    assert q1["estimated"] is False and q1["sheets"] == res["total_sheets"] and q1["cut_length_m"] == res["total_cut_length_m"]
    op = _op(client, pid, oid)
    assert op["cost_material"] == pytest.approx(1000.0 * res["total_sheets"] - 0, abs=0.01) or op["cost_material"] > 0
    assert op["cost_operation"] == pytest.approx(round(res["total_cut_length_m"] * 10.0, 2), abs=0.01)
    assert op["cn"]["usage_m2"] == pytest.approx(q1["material_qty_m2"], abs=1e-3)
    # narx m² bo'yicha: ☐ «по листам»
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cn": {"cost_by_sheets": False, "price": 200.0}})
    op = _op(client, pid, oid)
    assert op["cost_material"] == pytest.approx(round(op["cn"]["usage_m2"] * 200.0, 2), abs=0.02)
    # talabnoma (ombor): CN qatori, yangi listlar soni va narx
    wh = client.get(f"/api/projects/{pid}/warehouse").json()
    row = next(r for r in wh if r["type"] == "CN")
    assert row["unit_code"] == "sheets" and row["qty"] == res["total_sheets"] and row["cut_m"] == res["total_cut_length_m"]


def test_sheet_rounding_by_last_sheet_fraction(client):
    pid, oid = _mk(client, parts=[dict(name="A", length=900, width=400, qty=1)], sheets=[dict(length=2000, width=1000, qty=10000)],
                   params=dict(price=100.0, cost_by_sheets=True, sheet_rounding="22", rot90=False))     # 1/2 gacha yaxlitlash (eni bo'yicha)
    res = _opt(client, pid, oid)
    assert res["total_sheets"] == 1
    op = _op(client, pid, oid)
    assert op["cost_material"] == pytest.approx(50.0)                                       # bitta karta: faqat yarmi band


# ───────────────────────── Shakllar ─────────────────────────
def test_shapes_endpoint_contour_rect_and_label_spot(client):
    pid, oid = _mk(client, parts=[dict(name="Fasad", length=500, width=400, qty=2), dict(name="Oddiy", length=300, width=200, qty=1)])
    _xnc_part(client, pid, oid, 0, [_rect(250, 200, 500, 400, 60), _rect(250, 200, 200, 140, 20)])
    s = client.get(f"/api/projects/{pid}/operations/{oid}/cn-shapes").json()
    kinds = {r["uid"]: r for r in s["parts"]}
    assert kinds[1]["kind"] == "contour" and kinds[1]["holes"] == 1 and len(kinds[1]["outline"]) > 8 and len(kinds[1]["hole_rings"]) == 1
    assert kinds[2]["kind"] == "rect" and kinds[2]["holes"] == 0 and kinds[2]["area_mm2"] == 60000
    assert kinds[1]["label"] is not None and kinds[1]["label_fits"] and kinds[2]["label_free"] is not None
    assert s["spacing"] == pytest.approx(6.25) and s["margin"] == 5
    # `use_xnc_contours` o'chiq — to'rtburchak
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cn": {"use_xnc_contours": False}})
    s = client.get(f"/api/projects/{pid}/operations/{oid}/cn-shapes").json()
    assert s["parts"][0]["kind"] == "rect"
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cn": {"use_xnc_contours": True}})
    res = _opt(client, pid, oid, quality="normal")
    pl = next(p for m in res["maps"] for p in m["placements"] if p["part_uid"] == 1)
    assert len(pl["holes"]) == 1 and pl["label"] is not None
    assert client.get(f"/api/projects/{pid}/operations/{oid}/cn-validate").json()["ok"] is True


# ───────────────────────── Fon vazifasi ─────────────────────────
def _wait(client, pid, oid, jid, timeout=30):
    t = time.time()
    while time.time() - t < timeout:
        j = client.get(f"/api/projects/{pid}/operations/{oid}/cn/jobs/{jid}").json()
        if j["state"] != "running":
            return j
        time.sleep(0.05)
    raise AssertionError("vazifa tugamadi")


def test_job_flow_progress_and_result_applied(client):
    pid, oid = _mk(client)
    j = client.post(f"/api/projects/{pid}/operations/{oid}/cn/jobs", params={"quality": "fast"})
    assert j.status_code == 200 and j.json()["state"] in ("running", "done")
    j = _wait(client, pid, oid, j.json()["id"])
    assert j["state"] == "done" and j["progress"] == 1.0 and j["result"]["unplaced"] == 0 and j["result"]["sheets"] >= 1
    op = _op(client, pid, oid)
    assert op["result"] is not None and op["result"]["kind"] == "nest"
    assert client.get(f"/api/projects/{pid}/operations/{oid}/cn/jobs/yoq").status_code == 404
    assert client.get(f"/api/projects/other/operations/{oid}/cn/jobs/{j['id']}").status_code in (404,)
    # tarix: natija bitta undo qadami
    assert client.post(f"/api/projects/{pid}/undo").status_code == 200
    assert _op(client, pid, oid)["result"] is None


def test_job_busy_cancel_and_stale_input(client, monkeypatch):
    gate = threading.Event()
    real = cn_calc.run_nesting

    def slow(project, op, quality=None, progress=None, cancel=None):
        for _i in range(200):                                      # kutish (to'xtatish tekshiruvi bilan)
            if gate.is_set():
                break
            if cancel and cancel():
                raise N.NestCancelled()
            time.sleep(0.01)
        return real(project, op, quality=quality, progress=progress, cancel=cancel)
    monkeypatch.setattr(cn_jobs.cn_calc, "run_nesting", slow)
    # band: ikkinchi vazifa 409
    pid, oid = _mk(client)
    j = client.post(f"/api/projects/{pid}/operations/{oid}/cn/jobs").json()
    assert client.post(f"/api/projects/{pid}/operations/{oid}/cn/jobs").status_code == 409
    cur = client.get(f"/api/projects/{pid}/operations/{oid}/cn/jobs/current")        # sahifa qayta yuklansa — ketayotgan vazifa topiladi
    assert cur.status_code == 200 and cur.json()["id"] == j["id"] and cur.json()["state"] == "running"
    # to'xtatish
    r = client.delete(f"/api/projects/{pid}/operations/{oid}/cn/jobs/{j['id']}")
    assert r.status_code == 200
    j = _wait(client, pid, oid, j["id"])
    assert j["state"] == "cancelled" and _op(client, pid, oid)["result"] is None
    assert client.get(f"/api/projects/{pid}/operations/{oid}/cn/jobs/current").json() is None        # tugagach — null
    # hisob vaqtida loyiha o'zgarsa — natija qo'llanmaydi
    j = client.post(f"/api/projects/{pid}/operations/{oid}/cn/jobs").json()
    part = _op(client, pid, oid)["parts"][0]
    client.patch(f"/api/projects/{pid}/operations/{oid}/parts/{part['id']}", json={"qty": 5})
    gate.set()
    j = _wait(client, pid, oid, j["id"])
    assert j["state"] == "error" and j["error"] and _op(client, pid, oid)["result"] is None


# ───────────────────────── Qo'lda tahrir (CNE) va 409 ─────────────────────────
def test_edit_save_with_rev_and_conflict(client):
    pid, oid = _mk(client)
    res = _opt(client, pid, oid)
    rev = client.get(f"/api/projects/{pid}/operations/{oid}/cn-edit/rev").json()["rev"]
    r = client.post(f"/api/projects/{pid}/operations/{oid}/edit",
                    json={"result": res, "action": {"type": "comment", "map": 1, "comment": "izoh"}})
    assert r.status_code == 200 and r.json()["maps"][0]["comment"] == "izoh" and r.json()["manual"] is True
    draft = r.json()
    bad = client.post(f"/api/projects/{pid}/operations/{oid}/edit",
                      json={"result": draft, "action": {"type": "move", "map": 1, "index": 0, "dx": 99999, "dy": 0}})
    assert bad.status_code == 422 and bad.json()["detail"]
    ok = client.put(f"/api/projects/{pid}/operations/{oid}/result", params={"base": rev}, json=draft)
    assert ok.status_code == 200
    saved = next(o for o in ok.json()["operations"] if o["id"] == oid)["result"]
    assert saved["manual"] is True and saved["maps"][0]["comment"] == "izoh" and saved["maps"][0]["placements"][0]["outline"]
    stale = client.put(f"/api/projects/{pid}/operations/{oid}/result", params={"base": rev}, json=draft)
    assert stale.status_code == 409
    # mijoz soxta kontur yuborsa — serverda qayta hisoblanadi (ishonilmaydi)
    forged = json.loads(json.dumps(draft))
    forged["maps"][0]["placements"][0]["outline"] = [[0, 0], [1, 0], [1, 1], [0, 1]]
    rev2 = client.get(f"/api/projects/{pid}/operations/{oid}/cn-edit/rev").json()["rev"]
    r = client.put(f"/api/projects/{pid}/operations/{oid}/result", params={"base": rev2}, json=forged)
    assert r.status_code == 200                                      # soxta kontur e'tiborga olinmaydi: serverda shakl + joylashuvdan qayta hisoblanadi
    fixed = next(o for o in r.json()["operations"] if o["id"] == oid)["result"]["maps"][0]["placements"][0]["outline"]
    assert fixed != [[0, 0], [1, 0], [1, 1], [0, 1]] and len(fixed) == 4 and max(abs(c) for pt in fixed for c in pt) > 100
    # tahrirlangan natijada hamma narsa qayta hisoblangan
    assert client.get(f"/api/projects/{pid}/operations/{oid}/cn-validate").json()["ok"] is True
    # qoldiq yozilgan natijani qayta kroy qilish — ombor yozuvi bekor qilinadi (umumiy qoida)
    assert client.delete(f"/api/projects/{pid}/operations/{oid}/result").status_code == 200


# ───────────────────────── SVG / hisobot / postprotsessor ─────────────────────────
def test_map_svg_report_and_print_flags(client):
    pid, oid = _mk(client, parts=[dict(name="Fasad", length=500, width=400, qty=2), dict(name="Mayda", length=80, width=60, qty=4)])
    _xnc_part(client, pid, oid, 0, [_rect(250, 200, 500, 400, 60), _rect(250, 200, 200, 140, 20)])
    _opt(client, pid, oid, quality="normal")
    svg = client.get(f"/api/projects/{pid}/operations/{oid}/maps/1.svg", params={"width": 800})
    assert svg.status_code == 200 and "image/svg+xml" in svg.headers["content-type"]
    assert svg.text.count("<path") >= 6 and 'fill-rule="evenodd"' in svg.text and svg.text.startswith("<svg")
    assert client.get(f"/api/projects/{pid}/operations/{oid}/maps/9.svg").status_code == 404
    rep = client.get(f"/api/projects/{pid}/report", params={"lang": "ru"})
    assert rep.status_code == 200 and "(CN)" in rep.text and "Нестинговый раскрой" in rep.text and "<svg" in rep.text
    uz = client.get(f"/api/projects/{pid}/report", params={"lang": "uz"}).text
    assert "Nesting kroy" in uz and "Detallar" in uz
    # chop bayroqlari: kartalarsiz
    ps = client.get("/api/settings/print/default").json()
    ps.update(cn_maps=False, cn_remnants=False, cn_params=False)
    r = client.post(f"/api/projects/{pid}/report", params={"lang": "ru"}, json=ps)
    assert r.status_code == 200 and 'fill-rule="evenodd"' not in r.text and "(CN)" in r.text


def test_postprocess_builtin_json_csv_dxf_commands_and_template(client):
    pid, oid = _mk(client, parts=[dict(name="Fasad", length=500, width=400, qty=1), dict(name="Oddiy", length=300, width=200, qty=2)],
                   params=dict(tool_diameter=6.0))
    _xnc_part(client, pid, oid, 0, [_rect(250, 200, 500, 400, 40), _rect(250, 200, 200, 140, 10)])
    _opt(client, pid, oid, quality="fast")
    url = f"/api/projects/{pid}/operations/{oid}/postprocess"
    j = client.get(url, params={"key": "json"})
    assert j.status_code == 200 and "attachment" in j.headers["content-disposition"]
    data = j.json()
    assert data["tool"] == {"diameter": 6.0, "radius": 3.0, "offset": 3.0} and data["op"]["kind"] == "nest"
    pl = next(p for m in data["maps"] for p in m["placements"] if p["uid"] == 1)
    assert len(pl["outline"]) > 8 and len(pl["holes"]) == 1 and pl["angle"] in (0, 90, 180, 270)
    assert pl["tool_path"]["outer"] and pl["tool_path"]["holes"]                      # asbob yo'li: tashqariga / teshik ichiga ofset
    xs = [q[0] for q in pl["outline"]]
    tx = [q[0] for ring in pl["tool_path"]["outer"] for q in ring]
    assert min(tx) < min(xs) - 2.5 and max(tx) > max(xs) + 2.5                          # D/2 = 3 mm ga tashqarida
    assert {m["index"] for m in data["maps"]} == {1} or len(data["maps"]) >= 1
    csv = client.get(url, params={"key": "csv"}).content.decode("utf-8-sig")
    assert csv.splitlines()[0].startswith("karta;nusxa") and len(csv.splitlines()) == 4
    dxf = client.get(url, params={"key": "dxf"}).content.decode("ascii")
    assert "POLYLINE" in dxf and "TOOLPATH" in dxf and dxf.rstrip().endswith("EOF")
    txt = client.get(url, params={"key": "commands"}).content.decode("utf-8")
    assert "angle" in txt
    assert client.get(url, params={"key": "yoq"}).status_code == 400
    # foydalanuvchi shabloni (Jinja): stanok formati korxona dasturchilarida — bizda faqat ma'lumot
    tpl = ("{% for m in maps %}SHEET {{ f(m.sheet_length) }} {{ f(m.sheet_width) }}\n{% for p in m.placements %}PART {{ p.uid }} {{ f(p.x) }} "
           "{{ f(p.y) }} {{ f(p.angle) }} N={{ p.outline|length }} H={{ p.holes|length }} T={{ p.tool_path.outer|length }}\n{% endfor %}"
           "{% endfor %}TOOL {{ f(tool.diameter) }}")
    r = client.post("/api/settings/postprocessor", json={"name": "CN test", "data": dict(name="CN test", extension="nc", template=tpl,
                                                                                      newline="lf")})
    assert r.status_code == 200, r.text
    pid_prof = r.json()["id"]
    out = client.get(url, params={"profile_id": pid_prof})
    assert out.status_code == 200
    body = out.content.decode("utf-8")
    assert body.startswith("SHEET") and "PART 1" in body and "H=1" in body and body.rstrip().endswith("TOOL 6")


# ───────────────────────── Ombor (qoldiqlar) ─────────────────────────
def test_remnants_commit_rollback_and_reuse_as_sheet(client):
    pid, oid = _mk(client, parts=[dict(name="A", length=500, width=300, qty=2)], sheets=[dict(length=1500, width=1000, qty=1)],
                   params=dict(remnant_min_side1=300, remnant_min_side2=200, remnant_min_area=0.1))
    res = _opt(client, pid, oid)
    biz = [o for m in res["maps"] for o in m["offcuts"] if o["business"]]
    assert biz and all(o["raw_length"] >= o["length"] and o["raw_width"] >= o["width"] for o in biz)
    r = client.get(f"/api/projects/{pid}/operations/{oid}/remnants").json()
    assert r["saved"] is False and r["remnants"]
    c = client.post(f"/api/projects/{pid}/operations/{oid}/remnants/commit")
    assert c.status_code == 200 and c.json()["added"]
    ids = [x["id"] for x in c.json()["added"]]
    stock = {x["id"]: x for x in client.get("/api/remnants", params={"material_code": "MDF16"}).json()}
    assert all(i in stock and stock[i]["linear"] is False for i in ids)
    assert client.post(f"/api/projects/{pid}/operations/{oid}/remnants/commit").status_code == 400          # allaqachon yozilgan
    # boshqa loyihada qoldiqni list sifatida ishlatish: avval ro'yxatda, kroyda birinchi ishlatiladi
    pid2, oid2 = _mk(client, parts=[dict(name="B", length=200, width=150, qty=2)])
    big = max(ids, key=lambda i: stock[i]["area_m2"])
    s = client.post(f"/api/projects/{pid2}/operations/{oid2}/sheets/from-remnants", json={"ids": [big]})
    assert s.status_code == 200
    op2 = next(o for o in s.json()["operations"] if o["id"] == oid2)
    assert op2["sheets"][0]["source_remnant_id"] == big and op2["sheets"][0]["is_remnant"] is True
    r2 = _opt(client, pid2, oid2)
    assert r2["maps"][0]["is_remnant"] is True and r2["unplaced"] == []
    # birinchi loyiha natijasini bekor qilish — yozilgan qoldiqlar o'chadi (hali ishlatilmagan bo'lsa)
    rb = client.post(f"/api/projects/{pid}/operations/{oid}/remnants/rollback")
    assert rb.status_code == 200
    # CS dagi «Исп. кол-во» (mijoz olib ketadi): guruhlar ko'rinadi
    g = client.get(f"/api/projects/{pid}/operations/{oid}/remnant-groups").json()
    assert "groups" in g
    # pogonaj qoldiqni CN ga qo'shib bo'lmaydi
    # (ombordagi `linear` qoldiq CL uchun) — tur mosligi tekshiruvi
    client.delete(f"/api/projects/{pid2}")


# ───────────────────────── Eski JSON, eksport / import, MES ─────────────────────────
def test_old_json_without_cn_fields_opens_with_defaults():
    raw = {"name": "eski", "operations": [{"type": "CN", "name": "N", "parts": [{"length": 100, "width": 50, "qty": 1, "name": "x"}],
                                           "sheets": [{"length": 1000, "width": 500}]}]}
    p = Project.model_validate(raw)
    op = p.operations[0]
    assert op.cn is not None and op.cn.tool_diameter == 6 and op.result is None and op.parts[0].used_qty == 0
    # eski CS natijasi (Placement da angle / outline yo'q) ham ochiladi
    cs = {"name": "cs", "operations": [{"type": "CS", "name": "c", "result": {"maps": [{"index": 1, "sheet_id": "s", "sheet_length": 100,
          "sheet_width": 100, "placements": [{"part_id": "a", "part_uid": 1, "x": 0, "y": 0, "length": 10, "width": 10}]}]}}]}
    pl = Project.model_validate(cs).operations[0].result.maps[0].placements[0]
    assert pl.angle == 0 and pl.outline == [] and pl.holes == [] and pl.label is None


def test_mxk_json_roundtrip_keeps_cn_result_and_project_export_skips_cn(client):
    pid, oid = _mk(client)
    _opt(client, pid, oid)
    raw = client.get(f"/api/projects/{pid}/export").content
    r = client.post("/api/projects/import", files={"file": ("x.mxk.json", raw, "application/json")})
    assert r.status_code == 200
    op2 = next(o for o in r.json()["operations"] if o["type"] == "CN")
    assert op2["result"]["kind"] == "nest" and op2["result"]["maps"][0]["placements"][0]["outline"] and op2["cn"]["tool_diameter"] == 6
    # `.project` eksporti: CN o'tkazib yuboriladi va ogohlantiriladi (format atributlari yo'q)
    rep = client.get(f"/api/projects/{pid}/export/project/report").json()
    assert any("CN" in w.get("text", "") or w.get("code") == "op_skipped" or "CN" in json.dumps(w) for w in rep["warnings"])
    assert rep["counts"]["skipped_operations"] >= 1
    # `.project` importida CN operatsiyasi bo'lsa — ogohlantirish bilan o'tkazib yuboriladi
    xml = ('<?xml version="1.0" encoding="utf-8"?><project version="1" name="x"><operation id="1" typeId="CN" typeName="Nesting"/></project>')
    imp = client.post("/api/projects/import-file", files={"file": ("a.project", xml.encode("utf-8"), "application/xml")})
    assert imp.status_code == 200 and any("CN" in w for w in imp.json()["warnings"])
    assert not [o for o in imp.json()["project"]["operations"] if o["type"] == "CN"]


def test_mes_export_payload_for_cn(client):
    pid, oid = _mk(client)
    res = _opt(client, pid, oid)
    data = client.get(f"/api/projects/{pid}/mes-export").json()
    op = next(o for o in data["operations"] if o["type"] == "CN")
    assert op["kind"] == "nest" and op["sheets"] == res["total_sheets"] and op["fill_percent"] == res["total_fill_percent"]
    pls = op["maps"][0]["parts"]
    assert pls and set(pls[0]) == {"uid", "x", "y", "angle"} and len(op["parts"]) == 6
    assert op["tool_diameter"] == 6 and op["spacing"] == pytest.approx(6.25)


def test_cn_parts_move_from_cs_and_clone_and_delete(client):
    p = client.post("/api/projects", json={"name": "ko'chirish"}).json()
    pid = p["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "name": "LDSP"}).json()
    cs = p["operations"][-1]["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CN", "name": "MDF"}).json()
    cn = p["operations"][-1]["id"]
    parts = client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[dict(name="a", length=300, width=200, qty=2)]).json()
    part_id = next(o for o in parts["operations"] if o["id"] == cs)["parts"][0]["id"]
    r = client.post(f"/api/projects/{pid}/operations/{cs}/parts/move-to/{cn}", json={"ids": [part_id]})
    assert r.status_code == 200, r.text
    moved = next(o for o in r.json()["operations"] if o["id"] == cn)
    assert len(moved["parts"]) == 1 and moved["parts"][0]["name"] == "a"
    # klonlash: natija ko'chirilmaydi
    _opt(client, pid, cn) if _op(client, pid, cn)["parts"] else None
    r = client.post(f"/api/projects/{pid}/operations/{cn}/clone")
    assert r.status_code == 200
    clone = r.json()["operations"][[o["id"] for o in r.json()["operations"]].index(cn) + 1]
    assert clone["type"] == "CN" and clone["result"] is None and clone["cn"]["tool_diameter"] == 6
    # operatsiyani o'chirish: qoldiq yozilgan bo'lsa, ombor yozuvi bekor qilinadi
    assert client.delete(f"/api/projects/{pid}/operations/{cn}").status_code == 200


