"""Jadval «Настройки» → foydalanuvchi ustunlari: «Настроенный Параметры» (qator `user_params`, matn) va «Выражение»
(`/expr/eval-rows`). Saqlash / qayta yuklash, `.mxk.json` va `.project` aylanmasi, profil tekshiruvi."""
import xml.etree.ElementTree as ET

import pytest

from app.models import OMaterial, Part, Project
from app.services.project_schema import validate_project_xml


def _api(client, method, url, **kw):
    r = getattr(client, method)(url, **kw)
    assert r.status_code == 200, (url, r.status_code, r.text[:300])
    return r.json()


def _op(p, oid):
    return next(o for o in p["operations"] if o["id"] == oid)


def _cs_with_parts(client):
    p = _api(client, "post", "/api/projects", json={"name": "UC test"})
    pid = p["id"]
    p = _api(client, "post", f"/api/projects/{pid}/operations", json={"type": "CS", "name": "LDSP"})
    cs = p["operations"][-1]["id"]
    p = _api(client, "post", f"/api/projects/{pid}/operations/{cs}/parts",
             json=[{"name": "Yon", "length": 700, "width": 500, "qty": 2}, {"name": "Tom", "length": 800, "width": 400, "qty": 1}])
    return pid, cs, _op(p, cs)["parts"]


# ───────────────────────── model ─────────────────────────
def test_model_coerces_values_to_strings_and_drops_null():
    pt = Part(length=1, width=1, user_params={"part.a": 5, "part.b": 2.5, "part.c": True, "part.d": None, "part.e": 3.0})
    assert pt.user_params == {"part.a": "5", "part.b": "2.5", "part.c": "true", "part.e": "3"}
    assert OMaterial(user_params={"material.name1": "qizil"}).user_params == {"material.name1": "qizil"}


@pytest.mark.parametrize("bad", [{"1abc": "x"}, {"part.": "x"}, {"a b": "x"}, {"x" * 41: "1"}, {"part.a": "v" * 1001},
                                 {"part.a": [1]}, {f"p{i}": "1" for i in range(101)}, "abc"])
def test_model_rejects_bad_params(bad):
    with pytest.raises(ValueError):
        Part(length=1, width=1, user_params=bad)


def test_legacy_json_drops_bad_params_instead_of_failing():
    p = Project.model_validate({"operations": [{"type": "CS", "parts": [
        {"length": 1, "width": 1, "user_params": {"part.ok": "1", "bad name": "2", "part.long": "v" * 2000}}]}]},
        context={"legacy": True})
    up = p.operations[0].parts[0].user_params
    assert up["part.ok"] == "1" and "bad name" not in up and len(up["part.long"]) == 1000


# ───────────────────────── detallar: saqlash / kroy natijasi ─────────────────────────
def test_part_params_saved_via_batch_update_and_do_not_invalidate(client):
    pid, cs, parts = _cs_with_parts(client)
    _api(client, "post", f"/api/projects/{pid}/operations/{cs}/optimize", json={"quality": "fast"})
    assert _op(_api(client, "get", f"/api/projects/{pid}"), cs)["result"] is not None
    p = _api(client, "post", f"/api/projects/{pid}/operations/{cs}/parts/batch-update",
             json=[{"id": parts[0]["id"], "fields": {"user_params": {"part.name1": 12, "part.ok": True}}}])
    op = _op(p, cs)
    assert op["parts"][0]["user_params"] == {"part.name1": "12", "part.ok": "true"}
    assert op["result"] is not None                                     # kroyga ta'sirsiz — natija saqlanadi
    # qayta yuklash
    assert _op(_api(client, "get", f"/api/projects/{pid}"), cs)["parts"][0]["user_params"]["part.name1"] == "12"
    r = client.post(f"/api/projects/{pid}/operations/{cs}/parts/batch-update",
                    json=[{"id": parts[0]["id"], "fields": {"user_params": {"bad name": "1"}}}])
    assert r.status_code in (400, 422)


def test_mxk_json_and_project_roundtrip_keep_params(client):
    pid, cs, parts = _cs_with_parts(client)
    _api(client, "post", f"/api/projects/{pid}/operations/{cs}/parts/batch-update",
         json=[{"id": parts[0]["id"], "fields": {"user_params": {"part.name1": "A-1", "part.rang": "oq", "free": "x"}}}])
    p = _api(client, "post", f"/api/projects/{pid}/operations", json={"type": "O", "name": "Furnitura"})
    oid = p["operations"][-1]["id"]
    _api(client, "put", f"/api/projects/{pid}/operations/{oid}/o/materials",
         json=[{"name": "Ruchka", "qty": 4, "price": 10, "user_params": {"material.name1": "7", "other": "y"}}])
    # .mxk.json — hammasi saqlanadi
    blob = client.get(f"/api/projects/{pid}/export").content
    q = _api(client, "post", "/api/projects/import-file", files={"file": ("x.mxk.json", blob)})["project"]
    q_cs = next(o for o in q["operations"] if o["type"] == "CS")
    q_o = next(o for o in q["operations"] if o["type"] == "O")
    assert q_cs["parts"][0]["user_params"] == {"part.name1": "A-1", "part.rang": "oq", "free": "x"}
    assert q_o["o"]["materials"][0]["user_params"] == {"material.name1": "7", "other": "y"}
    # .project — format nomlash qoidasiga mos («part.*» / «material.*») parametrlar atribut sifatida
    xml = client.get(f"/api/projects/{pid}/export/project").content
    assert validate_project_xml(xml) == []
    root = ET.fromstring(xml)
    pe = next(e for e in root.findall("good[@typeId='product']/part") if e.get("name") == "Yon")
    assert pe.get("part.name1") == "A-1" and pe.get("part.rang") == "oq" and pe.get("free") is None
    ge = root.find("good[@typeId='simple']")
    assert ge.get("material.name1") == "7" and ge.get("other") is None
    r = _api(client, "post", "/api/projects/import-file", files={"file": ("x.project", xml)})["project"]
    r_cs = next(o for o in r["operations"] if o["type"] == "CS")
    r_o = next(o for o in r["operations"] if o["type"] == "O")
    yon = next(x for x in r_cs["parts"] if x["name"] == "Yon")
    assert yon["user_params"] == {"part.name1": "A-1", "part.rang": "oq"}
    assert next(x for x in r_cs["parts"] if x["name"] == "Tom")["user_params"] == {}
    assert r_o["o"]["materials"][0]["user_params"] == {"material.name1": "7"}
    # prefiksisiz parametrlar `.project` ga yozilmaydi — hisobotda ogohlantirish
    rep = client.get(f"/api/projects/{pid}/export/project/report", headers={"Accept-Language": "ru"}).json()
    assert any("part. / material." in w["text"] for w in rep["warnings"])


# ───────────────────────── profil: foydalanuvchi ustunlari ─────────────────────────
def test_profile_with_user_columns(client):
    cols = [{"key": "qty", "visible": True},
            {"key": "material.name1", "visible": True, "title": "Rang", "width": 10,
             "user": {"kind": "param", "vtype": "int", "desc": "Tavsif"}},
            {"key": "material.name2", "visible": True, "user": {"kind": "expr", "vtype": "double", "expr": "qty*2"}}]
    pr = _api(client, "post", "/api/settings/o_columns", json={"name": "U", "data": {"columns": cols}})
    got = pr["data"]["columns"]
    assert got[1]["user"] == {"kind": "param", "vtype": "int", "desc": "Tavsif", "expr": ""}
    assert got[2]["user"]["expr"] == "qty*2" and got[0].get("user") is None
    r = client.put("/api/settings/o_columns/default", json={"columns": cols})
    assert r.status_code == 200
    assert client.get("/api/settings/o_columns/default").json()["columns"][2]["user"]["kind"] == "expr"
    client.put("/api/settings/o_columns/default", json={"columns": []})        # boshqa testlar uchun standart bo'sh qolsin


@pytest.mark.parametrize("col", [
    {"key": "bad name", "user": {"kind": "param"}},                     # nom — ifoda o'zgaruvchisi emas
    {"key": "part.x", "user": {"kind": "expr", "expr": "1 +"}},          # ifoda sintaksisi
    {"key": "part.x", "user": {"kind": "other"}},
    {"key": "part.x", "user": {"kind": "param", "vtype": "date"}},
    {"key": "part.x", "user": {"kind": "param", "desc": "d" * 301}},
])
def test_profile_user_column_validation(client, col):
    assert client.post("/api/settings/cl_columns", json={"name": "X", "data": {"columns": [col]}}).status_code == 400


def test_profile_duplicate_keys_rejected(client):
    cols = [{"key": "part.a", "user": {"kind": "param"}}, {"key": "part.a", "user": {"kind": "param"}}]
    assert client.post("/api/settings/cn_columns", json={"name": "X", "data": {"columns": cols}}).status_code == 400


# ───────────────────────── /expr/eval-rows ─────────────────────────
def test_eval_rows_values_and_errors(client):
    rows = [{"qty": 2, "material.name1": "5"}, {"qty": 3.5, "material.name1": "x"}, {"qty": 1}]
    r = _api(client, "post", "/api/expr/eval-rows",
             json={"exprs": ["qty*2", "integer(material.name1)+1", "", "1 +"], "rows": rows})["results"]
    assert r[0] == {"error": None, "values": [4, 7, 2], "errors": [None, None, None]}
    assert r[1]["values"][0] == 6 and r[1]["values"][1] is None and r[1]["errors"][1]       # «x» — son emas
    assert r[1]["values"][2] is None and r[1]["errors"][2]                                   # o'zgaruvchi yo'q
    assert r[2] == {"error": None, "values": [None] * 3, "errors": [None] * 3}
    assert r[3]["error"] and r[3]["values"] == [None] * 3


def test_eval_rows_limits(client):
    assert client.post("/api/expr/eval-rows", json={"exprs": ["1"] * 21, "rows": []}).status_code == 422
    assert client.post("/api/expr/eval-rows", json={"exprs": ["1"] * 11, "rows": [{}] * 5000}).status_code == 400
    assert client.post("/api/expr/eval-rows", json={"exprs": ["a"], "rows": [{"a": [1]}]}).status_code == 422
