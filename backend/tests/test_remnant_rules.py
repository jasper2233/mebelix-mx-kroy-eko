# «Правила остатков» (2026-10-24, foydalanuvchi talabi): kroydan keyingi qoldiq / butun list ≥ material foizi — korxona olib
# qoladi (omborga), kichigi — mijozga; foiz material turi (LDSP, AKRIL …) yoki aniq material bo'yicha; MES «list arradan chiqdi»
# signaligacha «kutilmoqda»; kirim-chiqim jurnali va MES ga yuborish navbati; ombor manbasi MES bo'lsa — hammasi MES bazasida.
import uuid

import pytest

from app.services import remnant_rules as R


def test_type_and_norm():
    assert R.material_type("", "LDSP KASHMIR SHAGREN") == "LDSP"
    assert R.material_type("", "ldsp kashmir") == "LDSP"
    assert R.material_type("", "AKRIL OQ GLYANETS") == "AKRIL"
    assert R.material_type("", "ЛДСП белый") == "LDSP"
    assert R.material_type("M-HD-001-01", "HDF 2800x2070 mm") == "HDF"
    assert R.material_type("M-LD-004-02", "Kashmir") == "LDSP"
    assert R.norm("LDSP  KASHMIR  Shagren ") == R.norm("ldsp kashmir shagren")
    rules = R.RemnantRules(types=[{"type": "ldsp", "keep_percent": 30}, {"type": "AKRIL", "keep_percent": 20}],
                           materials=[{"material": "LDSP KASHMIR SHAGREN", "keep_percent": 25}])
    assert R.rule_for("", "ldsp  kashmir shagren", rules) == (25, "material")          # material qoidasi tur qoidasidan ustun
    assert R.rule_for("", "LDSP OQ", rules) == (30, "type")
    assert R.rule_for("", "XDF 5.8", rules) is None


def _set(client, scope, data):
    assert client.put(f"/api/settings/{scope}/default", json=data).status_code == 200


@pytest.fixture()
def rules(client):
    app0 = client.get("/api/settings/app/default").json()
    yield lambda **kw: _set(client, "remnant_rules", kw)
    _set(client, "remnant_rules", {})
    _set(client, "app", app0)


def _project(client, name, parts, sheet=(2750, 1830)):
    pid = client.post("/api/projects", json={"name": "Rules"}).json()["id"]
    oid = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "name": name}).json()["operations"][-1]["id"]
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cs_material": {"thickness": 16}})
    client.put(f"/api/projects/{pid}/operations/{oid}/sheets", json=[{"id": "full", "length": sheet[0], "width": sheet[1], "qty": 10000}])
    client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=[dict(name=f"P{i}", length=l, width=w, qty=q)
                                                                     for i, (l, w, q) in enumerate(parts)])
    res = client.post(f"/api/projects/{pid}/operations/{oid}/optimize?quality=fast")
    assert res.status_code == 200, res.text
    return pid, oid, res.json()


def _moves(client, pid):
    return client.get("/api/remnants/moves", params={"project_id": pid}).json()


def test_percent_rule_keep_vs_client_and_ledger(client, rules):
    rules(types=[{"type": "LDSP", "keep_percent": 30}])
    name = f"LDSP RULE {uuid.uuid4().hex[:6]}"
    pid, oid, res = _project(client, name, [(1000, 600, 3), (700, 300, 1)])
    info = client.get(f"/api/projects/{pid}/operations/{oid}/remnants").json()
    assert info["keep_percent"] == 30 and info["rule_source"] == "type"
    assert info["remnants"] and all(g["percent"] >= 30 for g in info["remnants"])           # omborga — faqat ≥ 30 %
    assert all(c["percent"] < 30 for c in info["client"])                                    # mijozga — kichiklari
    r = client.post(f"/api/projects/{pid}/operations/{oid}/remnants/commit")
    assert r.status_code == 200, r.text
    rows = [x for x in client.get("/api/remnants", params={"material_code": name.lower()}).json()]   # nom katta-kichik harfsiz
    assert rows and all(x["percent"] >= 30 and x["status"] == "available" and x["mat_type"] == "LDSP" for x in rows)
    kinds = {m["kind"] for m in _moves(client, pid)}
    assert "kirim" in kinds and ("mijozga" in kinds or not info["client"])
    # bekor qilish: kirim olib tashlanadi, jurnalda «bekor»
    assert client.post(f"/api/projects/{pid}/operations/{oid}/remnants/rollback").status_code == 200
    assert not client.get("/api/remnants", params={"material_code": name}).json()
    assert "bekor" in {m["kind"] for m in _moves(client, pid)}


def test_pending_until_saw_signal(client, rules):
    app = client.get("/api/settings/app/default").json()
    _set(client, "app", {**app, "mes_enabled": True})
    rules(types=[{"type": "LDSP", "keep_percent": 20}], wait_mes=True)
    name = f"LDSP WAIT {uuid.uuid4().hex[:6]}"
    pid, oid, res = _project(client, name, [(1000, 600, 3)])
    assert client.post(f"/api/projects/{pid}/operations/{oid}/remnants/commit").status_code == 200
    rows = client.get("/api/remnants", params={"material_code": name}).json()
    assert rows and all(x["status"] == "pending" and x["qty"] == 0 and x["qty_pending"] > 0 for x in rows)
    # kroyga qo'shib bo'lmaydi (taklif ham qilinmaydi): mavjud emas
    assert not [x for x in rows if x["qty"] > 0]
    # MES: 1-karta arradan chiqdi → shu kartaning qoldiqlari «mavjud»
    m = rows[0]["source_map"]
    assert client.patch(f"/api/projects/{pid}/operations/{oid}/maps/{m}", json={"done_count": 1}).status_code == 200
    rows2 = {x["id"]: x for x in client.get("/api/remnants", params={"material_code": name}).json()}
    assert rows2[rows[0]["id"]]["status"] == "available" and rows2[rows[0]["id"]]["qty"] > 0
    assert {"kutish", "kirim"} <= {mv["kind"] for mv in _moves(client, pid)}
    # qaytarish (done 0) — yana «kutilmoqda»
    client.patch(f"/api/projects/{pid}/operations/{oid}/maps/{m}", json={"done_count": 0})
    assert next(x for x in client.get("/api/remnants", params={"material_code": name}).json() if x["id"] == rows[0]["id"])["status"] == "pending"


def test_auto_commit_after_cut_and_summary(client, rules):
    rules(types=[{"type": "AKRIL", "keep_percent": 25}], auto_commit=True)
    name = f"AKRIL AUTO {uuid.uuid4().hex[:6]}"
    pid, oid, res = _project(client, name, [(1000, 600, 2)])
    assert res["remnants_saved"] is True                      # kroydan keyin tasdiqsiz yozildi
    s = client.get("/api/remnants/summary").json()
    t = next(g for g in s["types"] if g["type"] == "AKRIL")
    assert t["keep_percent"] == 25 and t["count"] >= 1 and t["percent_total"] > 0
    assert any(m["material"] == name and m["keep_percent"] == 25 for m in s["materials"])


def test_manual_add_percent_and_moves(client):
    r = client.post("/api/remnants", json={"material_code": f"HDF M {uuid.uuid4().hex[:5]}", "length": 2000, "width": 1000,
                                          "thickness": 3, "qty": 1, "sheet_length": 2800, "sheet_width": 2070})
    assert r.status_code == 200
    d = r.json()
    assert d["percent"] == round(2.0 / (2.8 * 2.07) * 100, 1) and d["status"] == "available"
    rid = d["id"]
    client.patch(f"/api/remnants/{rid}", json={"qty": 2})
    client.delete(f"/api/remnants/{rid}")
    mv = client.get("/api/remnants/moves", params={"remnant_id": rid}).json()
    assert [m["kind"] for m in mv] == ["qolda", "qolda", "qolda"]


def test_offer_respects_normalized_name_and_price(client):
    name = f"LDSP Norm {uuid.uuid4().hex[:6]}"
    pid, oid, res = _project(client, name.upper(), [(1000, 600, 9)])
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cs_material": {"thickness": 16, "price": 503.25, "cost_by_sheets": True}})
    client.post(f"/api/projects/{pid}/operations/{oid}/optimize?quality=fast")
    client.post("/api/remnants", json={"material_code": "  " + name.lower() + " ", "length": 2100, "width": 1300, "thickness": 16, "qty": 1})
    d = client.get(f"/api/projects/{pid}/operations/{oid}/remnant-offer").json()
    assert len(d["rows"]) == 1
    row = d["rows"][0]
    assert row["percent"] == round(2.1 * 1.3 / (2.75 * 1.83) * 100, 1)
    assert abs(row["sale_price"] - 2.73 * 503.25 / (2.75 * 1.83)) < 0.05          # qoldiq m² / list m² × list narxi


def test_mes_source_delegates(client, rules, monkeypatch):
    """Ombor manbasi MES: qidirish, band qilish, kroydan keyin yuborish va bekor qilish MES API ga boradi."""
    from app.services import remnant_store
    calls = []
    name = f"LDSP MES {uuid.uuid4().hex[:6]}"
    item = dict(id=9001, material_code=name, material_name=name, length=2100, width=1300, thickness=16, qty=1, status="available")

    def fake(method, path, json=None, params=None):
        calls.append((method, path, json, params))
        if method == "GET":
            return {"items": [item]}
        if path == "/remnants/intake":
            return {"intake_id": "IN-1", "ids": [77, 78]}
        return {}
    monkeypatch.setattr(remnant_store, "_req", fake)
    rules(types=[{"type": "LDSP", "keep_percent": 30}], source="mes", mes_url="http://mes.local/api/v1/kroy")
    pid, oid, res = _project(client, name, [(1000, 600, 9)])
    d = client.get(f"/api/projects/{pid}/operations/{oid}/remnant-offer").json()
    assert [r["id"] for r in d["rows"]] == [9001]
    assert client.post(f"/api/projects/{pid}/operations/{oid}/sheets/from-remnants", json={"ids": [9001]}).status_code == 200
    assert any(c[1] == "/remnants/reservations" and c[2]["mode"] == "add" for c in calls)
    res = client.post(f"/api/projects/{pid}/operations/{oid}/optimize?quality=fast").json()
    assert any(m["sheet_id"] != "full" for m in res["maps"])
    r = client.post(f"/api/projects/{pid}/operations/{oid}/remnants/commit")
    assert r.status_code == 200, r.text
    body = next(c[2] for c in calls if c[1] == "/remnants/intake")
    assert body["order"]["project_id"] == pid and body["op"]["type"] == "LDSP" and body["keep_percent"] == 30
    assert body["consumed"] and body["consumed"][0]["id"] == 9001
    assert all(p["percent"] >= 30 for p in body["pieces"])
    op = next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)
    assert op["result"]["remnant_intake_id"] == "IN-1"
    assert client.post(f"/api/projects/{pid}/operations/{oid}/remnants/rollback").status_code == 200
    assert any(c[1] == "/remnants/intake/IN-1/cancel" for c in calls)
    # ro'yxat — MES dan
    assert [x["id"] for x in client.get("/api/remnants").json()] == [9001]


def test_mes_down_is_503(client, rules):
    rules(source="mes", mes_url="http://127.0.0.1:9/none")
    assert client.get("/api/remnants").status_code == 503


def test_outbox_sends_in_order(client, monkeypatch):
    from app.services import mes, remnant_outbox
    sent = []
    monkeypatch.setenv("MES_WEBHOOK_URL", "http://mes.local/hook")
    monkeypatch.setattr(mes, "send_webhook", lambda ev, payload, attempts=None: sent.append((ev, payload)) or {"sent": True})
    client.post("/api/remnants", json={"material_code": f"OUTBOX {uuid.uuid4().hex[:5]}", "length": 900, "width": 800, "qty": 1})
    out = remnant_outbox.flush()
    assert out["configured"] and out["queued"] == 0 and sent
    assert all(ev == "remnant.move" for ev, _p in sent)
    ids = [p["move"]["id"] for _e, p in sent]
    assert ids == sorted(ids)
    assert remnant_outbox.flush()["sent"] == 0                     # qayta yuborilmaydi


def test_report_keep_client_columns(client, rules):
    rules(types=[{"type": "LDSP", "keep_percent": 30}])
    pid, oid, res = _project(client, f"LDSP REP {uuid.uuid4().hex[:6]}", [(1000, 600, 3), (700, 300, 1)])
    from app import store
    from app.models import PrintSettings
    from app.services import render
    html = render.project_report_html(store.load(pid), PrintSettings(cs_remnants=True))
    assert "На склад" in html and "% листа" in html


def test_base_size_equals_cut_map_size_and_reuse_without_trim(client, rules):
    """Foydalanuvchi (2026-10-25): bazadagi qoldiq o'lchami = kroy kartasidagi haqiqiy (arra bilan tozalangan) o'lcham; bunday
    qoldiq qayta ishlatilganda torsovka / otstup 0 (chetlari toza)."""
    rules(types=[{"type": "LDSP", "keep_percent": 20}])
    name = f"LDSP CLEAN {uuid.uuid4().hex[:6]}"
    pid, oid, res = _project(client, name, [(1000, 600, 3)])
    offs = {(round(max(o["length"], o["width"]), 1), round(min(o["length"], o["width"]), 1))
            for m in res["maps"] for o in m["offcuts"]}
    assert client.post(f"/api/projects/{pid}/operations/{oid}/remnants/commit").status_code == 200
    rows = client.get("/api/remnants", params={"material_code": name}).json()
    assert rows and all((r["length"], r["width"]) in offs and r["clean_edges"] for r in rows)
    big = max(rows, key=lambda r: r["area_m2"])
    pid2, oid2, _r = _project(client, name, [(500, 400, 1)])
    assert client.post(f"/api/projects/{pid2}/operations/{oid2}/sheets/from-remnants", json={"ids": [big["id"]]}).status_code == 200
    op = next(o for o in client.get(f"/api/projects/{pid2}").json()["operations"] if o["id"] == oid2)
    sh = next(s for s in op["sheets"] if s["source_remnant_id"] == big["id"])
    assert (sh["length"], sh["width"]) == (big["length"], big["width"])
    assert sh["trim_length"] == 0 and sh["trim_width"] == 0 and sh["end_offset_bottom"] == 0 and sh["end_offset_right"] == 0


def test_only_exact_material_code(client):
    """Bazadan faqat aynan shu material kodi (kod bo'lmasa — nom) qoldiqlari; boshqa material aralashmaydi."""
    code = f"M-LD-{uuid.uuid4().hex[:4]}-01"
    client.post("/api/remnants", json={"material_code": code, "material_name": "LDSP OQ", "length": 2000, "width": 1000, "qty": 1})
    client.post("/api/remnants", json={"material_code": code + "X", "material_name": "LDSP OQ", "length": 2000, "width": 1000, "qty": 1})
    pid = client.post("/api/projects", json={"name": "Code"}).json()["id"]
    oid = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": code, "name": "LDSP OQ"}).json()["operations"][-1]["id"]
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cs_material": {"thickness": 16}})
    client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=[{"name": "A", "length": 500, "width": 400, "qty": 1}])
    m = client.get(f"/api/projects/{pid}/operations/{oid}/remnant-match").json()
    assert {r["material_code"] for r in m["fitting"]} == {code}
