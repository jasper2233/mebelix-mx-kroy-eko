"""Postprotsessorlarga kirish (2026-10-18): admin ochadi/yopadi, yopiq — ro'yxatda xira (opened=false), server 403 bilan rad etadi."""
import time

import jwt
import pytest

from test_qa_fix_calc import _set_prog, _xnc_for

SECRET = "pp-access-secret-for-tests-0123456789"


def _tok(roles=None):
    claims = {"sub": "u1", "name": "Ali", "exp": int(time.time()) + 300}
    if roles is not None:
        claims["roles"] = roles
    return {"Authorization": "Bearer " + jwt.encode(claims, SECRET, algorithm="HS256")}


@pytest.fixture()
def reset_access(client):
    yield
    client.put("/api/postprocessors/access", json={"open": None})
    client.put("/api/postprocessors/machines", json={"enabled": {}, "profile": {}, "prefix": False})


def _row(lst, key):
    return next(x for x in lst if x["key"] == key)


def test_default_is_everything_that_works_today(client, reset_access):
    st = client.get("/api/postprocessors/access").json()
    assert st["explicit"] is False and st["can_edit"] is True            # lokal rejim — admin
    nat = {f["key"] for f in client.get("/api/postprocessors/native").json()}
    assert nat and nat <= set(st["open"])                                # o'rnatilgan formatlar standart ochiq
    assert "glass_gcode" not in st["open"]                               # generatorsiz, yoqilmagan — ochilmagan
    # yoqilgan stanok standart holatda avtomatik ochiladi (hech narsa buzilmasin)
    client.put("/api/postprocessors/machines", json={"enabled": {"glass_gcode": True}, "profile": {}, "prefix": False})
    assert "glass_gcode" in client.get("/api/postprocessors/access").json()["open"]


def test_closed_listed_greyed_and_refused(client, kravat, reset_access):
    pid, cs, _el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    assert client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=machine:scm_wincut").status_code == 200
    st = client.put("/api/postprocessors/access", json={"open": ["holzma_ptx", "woodwop"]}).json()
    assert st["explicit"] and st["open"] == ["holzma_ptx", "woodwop"] and st["updated_by"]
    lst = client.get("/api/postprocessors").json()
    saw = [x for x in lst if x.get("machine")]
    assert {x["key"] for x in saw} >= {"machine:scm_wincut", "machine:elmo3", "machine:holzma_ptx"}   # hammasi nomi bilan
    assert _row(lst, "machine:scm_wincut")["opened"] is False and _row(lst, "machine:scm_wincut")["available"] is False
    assert _row(lst, "machine:holzma_ptx")["opened"] is True and _row(lst, "machine:holzma_ptx")["available"] is True
    assert "machine:woodwop" not in {x["key"] for x in saw}              # ishlov markazi — XNC ro'yxatida
    # server rad etadi (ru va uz xabar)
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=machine:scm_wincut")
    assert r.status_code == 403 and "администратор" in r.json()["detail"]
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=machine:scm_wincut",
                   headers={"Accept-Language": "uz"})
    assert r.status_code == 403 and "administrator" in r.json()["detail"]
    # ochilgan — ishlaydi; o'z formatlarimiz (CSV …) doim ochiq
    assert client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=machine:holzma_ptx").status_code == 200
    assert client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=csv").status_code == 200
    # stanoklar sozlamasi oynasida ham belgi
    flat = {m["key"]: m for g in client.get("/api/postprocessors/machines").json()["groups"] for m in g["machines"]}
    assert flat["holzma_ptx"]["opened"] and not flat["scm_wincut"]["opened"]


def test_xnc_closed_refused_everywhere(client, kravat, reset_access):
    pid, cs, _pt, xid = _xnc_for(client, kravat)
    _set_prog(client, pid, xid, [dict(cmd="DrillFront", params=dict(X=30, Y=20, DP=12, D=8), comment="", children=[])])
    assert client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "machine:woodwop"}).status_code == 200
    client.put("/api/postprocessors/access", json={"open": ["tpa"]})
    lst = client.get("/api/xnc/postprocessors").json()
    assert _row(lst, "machine:woodwop")["opened"] is False and _row(lst, "machine:tpa")["available"] is True
    assert _row(lst, "machine:mw310")["opened"] is False                  # generatorsiz ham nomi bilan ro'yxatda
    assert client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "machine:woodwop"}).status_code == 403
    assert client.get(f"/api/projects/{pid}/postprocess-xnc", params={"key": "machine:woodwop"}).status_code == 403   # «Выделить все»
    assert client.get(f"/api/projects/{pid}/postprocess-xnc", params={"key": "machine:tpa"}).status_code == 200
    assert client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "json"}).status_code == 200


def test_only_admin_changes_access(client, monkeypatch, reset_access):
    monkeypatch.setenv("MEBELIX_AUTH_REQUIRED", "1")
    monkeypatch.setenv("MEBELIX_JWT_SECRET", SECRET)
    for h in (_tok(["technologist"]), _tok(["cutter"]), _tok(["viewer"]), _tok()):
        assert client.put("/api/postprocessors/access", json={"open": []}, headers=h).status_code == 403
        r = client.get("/api/postprocessors/access", headers=h)
        assert r.status_code == 200 and r.json()["can_edit"] is False     # o'qish — hammaga
    adm = _tok(["admin"])
    assert client.get("/api/postprocessors/access", headers=adm).json()["can_edit"] is True
    assert client.put("/api/postprocessors/access", json={"open": ["nope"]}, headers=adm).status_code == 400
    assert client.put("/api/postprocessors/access", json={"open": ["tpa"]}, headers=adm).status_code == 200
    assert client.put("/api/postprocessors/access", json={"open": None}, headers=adm).json()["explicit"] is False


def test_generic_settings_cannot_touch_access(client, reset_access):
    assert client.put("/api/settings/pp_access/default", json={"open": []}).status_code == 404
    assert client.post("/api/settings/pp_access", json={"name": "x", "data": {"open": []}}).status_code == 404
    client.put("/api/postprocessors/access", json={"open": ["tpa"]})
    assert "pp_access" not in client.get("/api/backup/settings").json()["profiles"]


# ───────── 2-qaror (2026-10-18): MebeliX'ning o'z formatlari va korxona shablonlari ham admin tomonidan yopiladi ─────────
SAW_TPL = dict(name="T saw", extension="txt", per_map=True, encoding="utf-8", newline="crlf", description="",
               template="SHEET;{{ f(map.sheet_length) }}\n")


def test_extras_default_open_and_listed(client, reset_access):
    st = client.get("/api/postprocessors/access").json()
    keys = {x["key"]: x for x in st["extras"]}
    for k in ("mx:csv", "mx:commands", "mx:dxf", "mx:json", "mx:xnc_json", "mx:mes_export", "mx:mes_package"):
        assert keys[k]["open"] is True and keys[k]["kind"] == "mx" and keys[k]["label"]
    assert st["closed_extra"] == []
    tid = client.post("/api/settings/postprocessor", json={"name": "T1", "data": SAW_TPL}).json()["id"]
    try:
        x = {e["key"]: e for e in client.get("/api/postprocessors/access").json()["extras"]}[f"pp:{tid}"]
        assert x["kind"] == "template" and x["open"] is True and x["group"] == "saw"      # yangi shablon ochiq tug'iladi
        assert all(r.get("opened") is True for r in client.get("/api/postprocessors").json() if not r.get("machine"))
    finally:
        client.delete(f"/api/settings/postprocessor/{tid}")


def test_close_csv_and_template_refused(client, kravat, reset_access):
    pid, cs, _el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    tid = client.post("/api/settings/postprocessor", json={"name": "T2", "data": SAW_TPL}).json()["id"]
    try:
        url = f"/api/projects/{pid}/operations/{cs}/postprocess"
        assert client.get(url, params={"profile_id": tid}).status_code == 200
        st = client.put("/api/postprocessors/access", json={"closed_extra": ["mx:csv", f"pp:{tid}"]}).json()
        assert st["closed_extra"] == sorted(["mx:csv", f"pp:{tid}"]) and st["explicit"] is False   # stanoklar standartda qoldi
        lst = client.get("/api/postprocessors").json()
        assert _row(lst, "csv")["opened"] is False and _row(lst, "dxf")["opened"] is True
        assert _row(lst, f"pp:{tid}")["opened"] is False
        r = client.get(url, params={"key": "csv"})
        assert r.status_code == 403 and "администратор" in r.json()["detail"] and "CSV" in r.json()["detail"]
        r = client.get(url, params={"key": "csv"}, headers={"Accept-Language": "uz"})
        assert r.status_code == 403 and "administrator" in r.json()["detail"]
        r = client.get(url, params={"key": "csv"}, headers={"Accept-Language": "uz-Cyrl"})
        assert r.status_code == 403 and "администратор" in r.json()["detail"].lower()
        assert client.get(url, params={"profile_id": tid}).status_code == 403
        assert client.get(url, params={"key": "dxf"}).status_code == 200                  # boshqalari ishlaydi
        assert client.get(url, params={"key": "machine:holzma_ptx"}).status_code == 200
        # shablon stanokka biriktirilgan bo'lsa — stanok kaliti tekshiriladi (shablon yopiqligi stanokni to'xtatmaydi)
        client.put("/api/postprocessors/machines", json={"enabled": {"elmo3": True}, "profile": {"elmo3": tid}, "prefix": False})
        assert client.get(url, params={"key": "machine:elmo3"}).status_code == 200
        # stanoklar ro'yxati saqlanganda yopilgan qo'shimchalar saqlanib qoladi
        st = client.put("/api/postprocessors/access", json={"open": ["holzma_ptx"]}).json()
        assert st["explicit"] and "mx:csv" in st["closed_extra"]
        # ochish
        st = client.put("/api/postprocessors/access", json={"closed_extra": []}).json()
        assert st["closed_extra"] == [] and st["open"] == ["holzma_ptx"]
        assert client.get(url, params={"key": "csv"}).status_code == 200
    finally:
        client.delete(f"/api/settings/postprocessor/{tid}")


def test_close_xnc_json_and_mes(client, kravat, reset_access):
    pid, cs, _pt, xid = _xnc_for(client, kravat)
    _set_prog(client, pid, xid, [dict(cmd="DrillFront", params=dict(X=30, Y=20, DP=12, D=8), comment="", children=[])])
    client.put("/api/postprocessors/access", json={"closed_extra": ["mx:xnc_json", "mx:mes_export", "mx:mes_package"]})
    assert _row(client.get("/api/xnc/postprocessors").json(), "json")["opened"] is False
    assert client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "json"}).status_code == 403
    assert client.get(f"/api/projects/{pid}/mes-export").status_code == 403
    assert client.get(f"/api/projects/{pid}/mes-package").status_code == 403
    assert client.get("/api/mes-package/schema").status_code == 200                       # sxema ochiq
    # kroy MES JSON (mx:json) alohida — ochiq
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    assert client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"key": "json"}).status_code == 200
    client.put("/api/postprocessors/access", json={"closed_extra": None})
    assert client.get(f"/api/projects/{pid}/mes-export").status_code == 200


def test_extras_validation_and_admin_only(client, monkeypatch, reset_access):
    assert client.put("/api/postprocessors/access", json={"closed_extra": ["mx:nope"]}).status_code == 400
    assert client.put("/api/postprocessors/access", json={"closed_extra": ["pp:999999"]}).status_code == 400
    monkeypatch.setenv("MEBELIX_AUTH_REQUIRED", "1")
    monkeypatch.setenv("MEBELIX_JWT_SECRET", SECRET)
    assert client.put("/api/postprocessors/access", json={"closed_extra": ["mx:csv"]},
                      headers=_tok(["technologist"])).status_code == 403
    assert client.put("/api/postprocessors/access", json={"closed_extra": ["mx:csv"]},
                      headers=_tok(["admin"])).status_code == 200
    # tozalash shu yerda (admin tokeni bilan): fixture teardown monkeypatch'dan oldin ishlaydi — tokensiz 401 bo'lardi
    assert client.put("/api/postprocessors/access", json={"open": None}, headers=_tok(["admin"])).json()["closed_extra"] == []
