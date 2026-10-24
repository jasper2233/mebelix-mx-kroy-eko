"""QA tuzatishlari (server infratuzilmasi, import, MES): qidiruv, tarix, MES qayta yuborish, webhook, JWT rollari,
server tekshiruvlari, 422 xabarlari tili, Excel / .project import, profillar zaxirasi, kroy hajmi chegarasi."""
import copy
import io
import json
import sys
import time
from datetime import date
from uuid import uuid4

import jwt
import pytest
from openpyxl import Workbook

SECRET = "s3cret-for-tests-only-0123456789"
UZ = {"Accept-Language": "uz"}


def _op(p, t):
    return [o for o in p["operations"] if o["type"] == t]


def _ids(rows):
    return [r["id"] for r in rows]


# ───────────────────────── 1. Qidiruv ─────────────────────────
def test_search_cyrillic_case_insensitive_and_wildcards_escaped(client):
    mk = lambda n: client.post("/api/projects", json={"name": n}).json()["id"]          # noqa: E731
    kitchen, disc, under, plain = (mk("Кухня Большая Zq7"), mk("Скидка 50% Zq7"), mk("Шкаф_А Zq7"), mk("Шкаф B Zq7"))
    for q in ("Кухня", "кухня", "КУХНЯ", "большая", "бОлЬшАя zq7"):
        assert kitchen in _ids(client.get("/api/projects", params={"q": q}).json()), q
    # `%` va `_` — wildcard emas: aynan shu belgi bor nomlargina
    pct = client.get("/api/projects", params={"q": "%"}).json()
    assert disc in _ids(pct) and kitchen not in _ids(pct) and all("%" in r["name"] for r in pct)
    und = client.get("/api/projects", params={"q": "_"}).json()
    assert under in _ids(und) and plain not in _ids(und) and all("_" in r["name"] for r in und)
    assert client.get("/api/projects", params={"q": "50%"}).json()[0]["id"] == disc
    # tuzoqlar: unicode raqam / juda uzun raqam — 500 emas
    assert client.get("/api/projects", params={"q": "²"}).status_code == 200
    assert client.get("/api/projects", params={"q": "9" * 40}).status_code == 200
    # katalog va ombor
    client.post("/api/catalog/sync", json=[{"id": "zq7-mdf", "kind": "sheet", "code": "MDF-ZQ7", "name": "МДФ 18 мм Zq7"}])
    assert "zq7-mdf" in _ids(client.get("/api/catalog", params={"q": "мдф"}).json())
    assert "zq7-mdf" not in _ids(client.get("/api/catalog", params={"q": "%"}).json())
    r = client.post("/api/remnants", json={"material_code": "LDSP-ZQ7", "material_name": "ЛДСП Белый Zq7",
                                           "length": 1000, "width": 500, "qty": 1, "note": "хвост"}).json()
    assert r["id"] in _ids(client.get("/api/remnants", params={"q": "лдсп белый"}).json())
    assert r["id"] in _ids(client.get("/api/remnants", params={"q": "ХВОСТ"}).json())
    assert r["id"] not in _ids(client.get("/api/remnants", params={"q": "%"}).json())
    assert r["id"] not in _ids(client.get("/api/remnants", params={"q": "_"}).json())


# ───────────────────────── 2. Tarix ─────────────────────────
def _version(client, pid):
    return client.get(f"/api/projects/{pid}/history").json()["version"]


def test_optimize_ops_is_one_history_step_and_save_adds_no_empty_version(client):
    pid = client.post("/api/projects", json={"name": "Tarix"}).json()["id"]
    for t, code in (("CS", "M1"), ("CS", "M1"), ("EL", "E-unused"), ("XNC", "X1")):
        client.post(f"/api/projects/{pid}/operations", json={"type": t, "code": code, "name": code})
    before = client.get(f"/api/projects/{pid}").json()
    v0 = _version(client, pid)
    after = client.post(f"/api/projects/{pid}/actions/optimize-ops").json()
    assert len(after["operations"]) < len(before["operations"])
    assert _version(client, pid) == v0 + 1                                  # bitta qadam (avval 3 ta edi)
    undone = client.post(f"/api/projects/{pid}/undo").json()
    assert [o["id"] for o in undone["operations"]] == [o["id"] for o in before["operations"]]
    # «Сохранить»: o'zgarish yo'q — bo'sh versiya yozilmaydi; o'zgarishdan keyin — yoziladi
    v1 = _version(client, pid)
    client.post(f"/api/projects/{pid}/save")
    client.post(f"/api/projects/{pid}/save")
    assert _version(client, pid) == v1
    client.patch(f"/api/projects/{pid}", json={"note": "yangi izoh"})
    assert _version(client, pid) == v1 + 1
    client.post(f"/api/projects/{pid}/save")
    assert _version(client, pid) == v1 + 1
    assert client.post(f"/api/projects/{pid}/undo").json()["note"] == ""     # Save bo'sh qadam qo'shmagan


# ───────────────────────── 3. MES qayta yuborish ─────────────────────────
def _order(ref, **kw):
    o = {"mes_order_ref": ref, "name": "QA zakaz", "customer": "Karimov A.",
         "materials": [{"code": "LDSP-16-W", "name": "LDSP 16 Oq", "thickness": 16, "length": 2750, "width": 1830,
                        "price": 420000}],
         "edges": [{"code": "PVC-2-19", "name": "PVC 2/19 Oq", "thickness": 2, "price": 3000}],
         "products": [{"code": "K-01", "name": "Pastki shkaf 600", "qty": 2, "parts": [
             {"name": "Yon devor", "code": "YD", "material_code": "LDSP-16-W", "length": 720, "width": 560, "qty": 2,
              "grain": True, "edges": {"top": "PVC-2-19", "left": "PVC-2-19"}},
             {"name": "Tub", "code": "TB", "material_code": "LDSP-16-W", "length": 568, "width": 560, "qty": 1,
              "edges": {"top": "PVC-2-19"}}]}]}
    o.update(kw)
    return o


def test_mes_resend_keeps_local_work_and_updates_mes_fields(client):
    o = _order("QA-RESEND-1")
    p = client.post("/api/mes/orders", json=o).json()
    pid, cs = p["id"], _op(p, "CS")[0]
    ids0 = [pt["id"] for pt in cs["parts"]]
    assert all(i.startswith("mx") for i in ids0) and [pt["uid"] for pt in cs["parts"]] == [1, 2]
    # kroychining lokal ishi
    client.patch(f"/api/projects/{pid}", json={"status": 1, "size_mode": "blank", "note": "lokal izoh"})
    client.post(f"/api/projects/{pid}/operations", json={"type": "XNC", "code": "X-LOCAL", "name": "Lokal XNC"})
    client.post(f"/api/projects/{pid}/operations", json={"type": "GR", "code": "G-LOCAL", "name": "Lokal GR"})
    client.patch(f"/api/projects/{pid}/operations/{cs['id']}/parts/{ids0[0]}", json={"allow_top": 5})
    cur = client.get(f"/api/projects/{pid}").json()
    sizes0 = [(pt["length"], pt["width"]) for pt in _op(cur, "CS")[0]["parts"]]
    assert sizes0 != [(720, 560), (568, 560)]                       # blank rejimida (kromka qalinligi ayrildi)
    res = client.post(f"/api/projects/{pid}/operations/{cs['id']}/optimize?quality=fast").json()
    assert res["total_parts"] == 6
    v0 = _version(client, pid)
    # o'sha buyurtmani qayta yuborish
    p2 = client.post("/api/mes/orders", json=o).json()
    assert p2["id"] == pid and p2["number"] == p["number"]
    assert p2["status"] == 1 and p2["size_mode"] == "blank" and p2["note"] == "lokal izoh"
    assert p2["customer"] == "Karimov A." and p2["owner"] == "MES"
    assert {x["code"] for x in p2["operations"]} >= {"X-LOCAL", "G-LOCAL", "LDSP-16-W", "PVC-2-19"}
    cs2 = _op(p2, "CS")[0]
    assert cs2["id"] == cs["id"] and [pt["id"] for pt in cs2["parts"]] == ids0     # id lar turg'un
    assert cs2["parts"][0]["allow_top"] == 5                                         # MES bermagan lokal maydon
    assert [(pt["length"], pt["width"]) for pt in cs2["parts"]] == sizes0            # jismoniy o'lcham o'zgarmadi
    assert cs2["result"] is not None and cs2["result"]["total_parts"] == 6          # kroyga ta'sir yo'q — natija bor
    assert _version(client, pid) == v0 + 1                                           # bitta tarix qadami
    # MES o'zgartirdi: soni 3 ta, nom yangilandi — natija eskirdi, id lar o'sha
    o2 = copy.deepcopy(o)
    o2["products"][0]["parts"][1].update(qty=3, name="Tub (yangi)")
    p3 = client.post("/api/mes/orders", json=o2).json()
    cs3 = _op(p3, "CS")[0]
    assert [pt["id"] for pt in cs3["parts"]] == ids0 and cs3["parts"][1]["qty"] == 3
    assert cs3["parts"][1]["name"] == "Tub (yangi)" and cs3["result"] is None
    assert p3["status"] == 1 and {x["code"] for x in p3["operations"]} >= {"X-LOCAL", "G-LOCAL"}
    # tasdiqlangan — avvalgidek 409
    client.patch(f"/api/projects/{pid}", json={"status": 2})
    assert client.post("/api/mes/orders", json=o2).status_code == 409


def test_mes_resend_line_id_add_remove_and_legacy_ids(client):
    def parts_of(ps, extra=()):
        base = [dict(name=n, code=n[:2].upper(), material_code="LDSP-16-W", length=L, width=W, qty=1, line_id=lid)
                for n, L, W, lid in (("Alfa", 700, 500, "L1"), ("Beta", 600, 400, "L2"), *extra)]
        return [x for x in base if x["line_id"] in ps]
    o = _order("QA-RESEND-2", products=[{"code": "P", "name": "Prod", "qty": 1, "parts": parts_of({"L1", "L2"})}])
    p = client.post("/api/mes/orders", json=o).json()
    pid, cs = p["id"], _op(p, "CS")[0]
    alfa, beta = cs["parts"]
    client.post(f"/api/projects/{pid}/operations/{cs['id']}/parts/{beta['id']}/xnc")        # Beta ga bog'langan XNC
    local = client.post(f"/api/projects/{pid}/operations/{cs['id']}/parts",
                        json=[{"name": "Lokal detal", "length": 100, "width": 100}]).json()
    local_part = _op(local, "CS")[0]["parts"][-1]
    # Beta o'chirildi, Gamma qo'shildi — Alfa id/uid si turg'un, lokal qo'shilgan detal saqlanadi
    gamma = dict(name="Gamma", code="GA", material_code="LDSP-16-W", length=300, width=200, qty=2, line_id="L3")
    o2 = copy.deepcopy(o)
    o2["products"][0]["parts"] = parts_of({"L1"}) + [gamma]
    p2 = client.post("/api/mes/orders", json=o2).json()
    cs2 = _op(p2, "CS")[0]
    names = [pt["name"] for pt in cs2["parts"]]
    assert names == ["Alfa", "Lokal detal", "Gamma"], names
    assert cs2["parts"][0]["id"] == alfa["id"] and cs2["parts"][0]["uid"] == alfa["uid"]
    assert cs2["parts"][1]["id"] == local_part["id"]
    assert len({pt["uid"] for pt in cs2["parts"]}) == 3                                  # uid to'qnashmaydi
    assert not [x for x in p2["operations"] if x["type"] == "XNC"]                        # o'chirilgan detal XNC si ham
    # eski loyiha (tasodifiy id lar): qayta yuborish id larni MES id siga o'tkazadi, dublikat bermaydi
    from app import store
    with store.editing(pid, history=False) as pr:
        for op in pr.operations:
            for pt in op.parts:
                pt.id = uuid4().hex[:12]
    p3 = client.post("/api/mes/orders", json=o2).json()
    assert [pt["name"] for pt in _op(p3, "CS")[0]["parts"]] == ["Alfa", "Gamma"]        # lokal detal — eski rejimda MES siniqi
    assert all(pt["id"].startswith("mx") for pt in _op(p3, "CS")[0]["parts"])


def test_mes_validation_and_ref_with_slash(client):
    bad = _order("QA-BAD")
    bad["products"][0]["parts"][0]["length"] = -5
    assert client.post("/api/mes/orders", json=bad).status_code == 422
    assert client.post("/api/mes/orders", json=_order("   ")).status_code == 422
    big = _order("QA-BIG")
    big["products"][0]["parts"][0]["qty"] = 10**9
    assert client.post("/api/mes/orders", json=big).status_code == 422
    assert client.post("/api/mes/orders?folder_id=yoq-papka", json=_order("QA-NOFOLDER")).status_code == 400
    ref = "2026/001"
    p = client.post("/api/mes/orders", json=_order(ref)).json()
    assert p["mes_order_ref"] == ref
    assert client.get("/api/mes/orders/2026%2F001").json()["mes_order_ref"] == ref
    assert client.get("/api/mes/orders/2026/001").json()["project_id"] == p["id"]
    assert client.get("/api/mes/orders/yoq-buyurtma").status_code == 404


# ───────────────────────── 4. Webhook ─────────────────────────
class _Resp:
    def __init__(self, code):
        self.status_code = code


def test_webhook_test_reports_failures(client, monkeypatch):
    import httpx
    monkeypatch.setenv("MES_WEBHOOK_URL", "http://user:pass@mes.local/hook")
    monkeypatch.setattr(httpx, "post", lambda url, json=None, headers=None, timeout=None: _Resp(500))
    r = client.post("/api/mes/webhook-test").json()
    assert r["sent"] is False and r["status"] == 500 and "500" in r["reason"] and r["elapsed_ms"] >= 0
    assert "pass" not in r["url"]                                                    # parol yashirilgan

    def boom(url, json=None, headers=None, timeout=None):
        raise httpx.ConnectTimeout("")
    monkeypatch.setattr(httpx, "post", boom)
    r = client.post("/api/mes/webhook-test", headers=UZ).json()
    assert r["sent"] is False and r["status"] is None and "ConnectTimeout" in r["error"] and "Yuborib bo'lmadi" in r["reason"]
    monkeypatch.setattr(httpx, "post", lambda url, json=None, headers=None, timeout=None: _Resp(204))
    ok = client.post("/api/mes/webhook-test").json()
    assert ok["sent"] is True and ok["status"] == 204 and ok["error"] is None
    monkeypatch.delenv("MES_WEBHOOK_URL")
    assert client.post("/api/mes/webhook-test").json()["sent"] is False


def test_webhook_events_retry(client, monkeypatch):
    import httpx
    from app.services import mes
    monkeypatch.setenv("MES_WEBHOOK_URL", "http://mes.local/hook")
    monkeypatch.setenv("MES_WEBHOOK_RETRY_DELAY", "0")
    calls = []

    def seq(*codes):
        it = iter(codes)

        def post(url, json=None, headers=None, timeout=None):
            calls.append(json["event"])
            c = next(it)
            if isinstance(c, Exception):
                raise c
            return _Resp(c)
        return post
    monkeypatch.setattr(httpx, "post", seq(503, httpx.ReadTimeout("t"), 200))
    res = mes.send_webhook("x", {})
    assert res["sent"] and res["attempts"] == 3 and len(calls) == 3
    calls.clear()
    monkeypatch.setattr(httpx, "post", seq(500, 500, 500, 200))
    res = mes.send_webhook("x", {})
    assert not res["sent"] and res["attempts"] == 3 and res["status"] == 500
    calls.clear()
    monkeypatch.setattr(httpx, "post", seq(404, 200))                      # 4xx — qayta urinilmaydi
    assert mes.send_webhook("x", {}) ["attempts"] == 1 and len(calls) == 1
    # hodisa (fon vazifasi): birinchi urinish xato — qayta yuboriladi
    calls.clear()
    monkeypatch.setattr(httpx, "post", seq(502, 200))
    p = client.post("/api/projects", json={"name": "Hook retry"}).json()
    client.patch(f"/api/projects/{p['id']}", json={"status": 1})
    assert calls == ["project.status", "project.status"]


# ───────────────────────── 6. JWT rollari ─────────────────────────
def _tok(roles=None, exp=True, **extra):
    claims = {"sub": "u1", "name": "Tester", **extra}
    if roles is not None:
        claims["roles"] = roles
    if exp:
        claims["exp"] = int(time.time()) + 300
    return {"Authorization": "Bearer " + jwt.encode(claims, SECRET, algorithm="HS256")}


def test_jwt_roles_viewer_read_only_and_exp_required(client, monkeypatch):
    monkeypatch.setenv("MEBELIX_AUTH_REQUIRED", "1")
    monkeypatch.setenv("MEBELIX_JWT_SECRET", SECRET)
    editor = _tok(["kroychi"])
    pid = client.post("/api/projects", json={"name": "Rollar"}, headers=editor).json()["id"]
    for roles in (["viewer"], ["ko'ruvchi"], ["Viewer"], "viewer", ["offline_access", "viewer"]):
        hv = _tok(roles)
        assert client.get("/api/projects", headers=hv).status_code == 200, roles
        assert client.get(f"/api/projects/{pid}", headers=hv).status_code == 200
        assert client.post("/api/projects", json={"name": "x"}, headers=hv).status_code == 403
        assert client.patch(f"/api/projects/{pid}", json={"name": "x"}, headers=hv).status_code == 403
        assert client.delete(f"/api/projects/{pid}", headers=hv).status_code == 403
        assert client.put("/api/settings/app/default", json={"currency": "USD"}, headers=hv).status_code == 403
    hv = _tok(["viewer"])
    assert client.post(f"/api/projects/{pid}/report", json={}, headers=hv).status_code == 200   # oldindan ko'rish — o'qish
    assert client.get("/api/me", headers=hv).json()["read_only"] is True
    assert client.post("/api/projects", json={"name": "x"}, headers=_tok(["viewer"]))\
        .json()["detail"].startswith("Недостаточно прав")
    # yozish huquqi bor rollar / rolsiz (eski) token — avvalgidek
    for roles in (["kroychi"], ["texnolog"], ["admin"], ["viewer", "kroychi"], None, ["boshqa-rol"]):
        h = _tok(roles)
        assert client.post("/api/projects", json={"name": "ok"}, headers=h).status_code == 200, roles
    assert client.get("/api/me", headers=editor).json()["read_only"] is False
    # exp siz token rad etiladi
    assert client.get("/api/projects", headers=_tok(["kroychi"], exp=False)).status_code == 401
    assert client.get("/api/projects").status_code == 401


# ───────────────────────── 7, 8, 11. Server tekshiruvlari va xabarlar tili ─────────────────────────
def test_settings_app_validation(client):
    ok = client.put("/api/settings/app/default", json={"currency": "UZS", "default_sheet_length": 2800,
                                                       "default_sheet_width": 2070})
    assert ok.status_code == 200
    for bad in ({"default_sheet_length": 0}, {"default_sheet_width": -5}, {"default_sheet_length": 20001},
                {"currency": ""}, {"currency": "   "}):
        r = client.put("/api/settings/app/default", json=bad)
        assert r.status_code == 400, bad
        assert "Input should" not in r.json()["detail"]
    r = client.put("/api/settings/app/default", json={"currency": ""}, headers=UZ)
    assert r.status_code == 400 and "Valyuta" in r.json()["detail"] and "currency" in r.json()["detail"]
    assert client.get("/api/settings/app/default").json()["default_sheet_length"] == 2800
    assert client.put("/api/settings/app/default", json={}).status_code == 200          # standartga qaytarish
    assert client.get("/api/settings/app/default").json()["default_sheet_length"] == 2750


def test_project_header_folder_and_product_validation(client):
    p = client.post("/api/projects", json={"name": "Tekshiruv"}).json()
    pid = p["id"]
    patch = lambda **kw: client.patch(f"/api/projects/{pid}", json=kw)                # noqa: E731
    assert patch(name="  ").json()["name"] == "Без названия"
    assert patch(name="Y" * 301).status_code == 400
    r = patch(currency="")
    assert r.status_code == 400 and "Валюта" in r.json()["detail"]
    r = client.patch(f"/api/projects/{pid}", json={"currency": ""}, headers=UZ)
    assert r.status_code == 400 and "Valyuta" in r.json()["detail"]
    assert patch(order_date="0001-01-01").status_code == 400
    assert patch(ready_date="2200-01-01").status_code == 400
    assert patch(order_date="abc").status_code == 400
    assert patch(order_date="2026-13-45").status_code == 400
    assert patch(size_mode="zzz").status_code == 400
    r = patch(order_date="2026-10-10", ready_date="2026-10-01")                        # tayyorlik < buyurtma — qabul
    assert r.status_code == 200 and r.json()["ready_date"] == "2026-10-01"
    assert patch(currency="usd").json()["currency"] == "usd"
    # papka mavjud bo'lishi shart
    assert patch(folder_id="yoq-papka").status_code == 400
    assert client.post("/api/projects", json={"name": "A", "folder_id": "yoq"}).status_code == 400
    assert client.post("/api/folders", json={"name": "A", "parent_id": "yoq"}).status_code == 400
    f = client.post("/api/folders", json={"name": "Haqiqiy"}).json()
    q = client.post("/api/projects", json={"name": "B", "folder_id": f["id"]}).json()
    assert client.post("/api/projects/move", json={"ids": [q["id"]], "folder_id": "yoq"}).status_code == 400
    assert client.get(f"/api/projects/{q['id']}").json()["folder_id"] == f["id"]        # yo'qolib qolmadi
    assert client.post(f"/api/projects/{q['id']}/copy", params={"folder_id": "yoq"}).status_code == 400
    # mahsulot: soni chegarasi, takroriy kalitlar
    prid = p["products"][0]["id"]
    assert client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": 100000}).status_code == 200
    assert client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": 100001}).status_code in (400, 422)
    assert client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": -1}).status_code in (400, 422)
    r = client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": 10**11}, headers=UZ)
    assert r.status_code in (400, 422) and "100000" in json.dumps(r.json()) and "Input should" not in json.dumps(r.json())
    r = client.patch(f"/api/projects/{pid}/products/{prid}", json={"extra": {"product.import": "a", "product.import ": "b"}})
    assert r.status_code == 400 and "product.import" in r.json()["detail"]
    assert client.patch(f"/api/projects/{pid}/products/{prid}", json={"extra": {"": "x"}}).status_code == 400
    prod = client.get(f"/api/projects/{pid}").json()["products"][0]
    prod["extra"] = {"a": "1", " a": "2"}
    assert client.put(f"/api/projects/{pid}/products/{prid}", json=prod).status_code == 400
    assert client.post(f"/api/projects/{pid}/products", json={"name": "N", "qty": 200000}).status_code in (400, 422)
    assert client.patch(f"/api/projects/{pid}/products/{prid}", json={"extra": {"a": "1"}}).status_code == 200


def test_mxk_import_errors_are_readable_and_empty_json_rejected(client, kravat):
    pid, cs, _el = kravat
    n0 = len(client.get("/api/projects", params={"all_folders": True}).json())
    for body in (b'{"x": 1}', b"{}", b"[]", b'"matn"', b'{"operations": "x"}', b"{bad"):
        r = client.post("/api/projects/import", files={"file": ("a.mxk.json", io.BytesIO(body))})
        assert r.status_code == 400, body
        assert "validation error for" not in r.json()["detail"], r.json()
    r = client.post("/api/projects/import", files={"file": ("a.mxk.json", io.BytesIO(b'{"operations": [{"type": "ZZ"}]}'))})
    assert r.status_code == 400 and "Операции" in r.json()["detail"]
    assert len(client.get("/api/projects", params={"all_folders": True}).json()) == n0          # loyiha yaratilmadi
    doc = client.get(f"/api/projects/{pid}/export").json()
    doc["products"][0]["qty"] = 10**7                      # eski/katta qiymat: rad etilmaydi, chegaraga qisqartiriladi + ogohlantirish
    r = client.post("/api/projects/import-file", files={"file": ("a.mxk.json", io.BytesIO(json.dumps(doc).encode()))})
    assert r.status_code == 200 and r.json()["project"]["products"][0]["qty"] == 100000
    assert len(r.json()["warnings"]) == 1 and "100000" not in r.json()["warnings"][0]
    doc["products"][0]["qty"] = 1
    doc["order_date"] = "0001-01-01"
    imp = client.post("/api/projects/import", files={"file": ("a.mxk.json", io.BytesIO(json.dumps(doc).encode()))}).json()
    assert imp["order_date"] == date.today().isoformat()
    # export → import — avvalgidek
    ok = client.post("/api/projects/import-file", files={"file": ("a.mxk.json", client.get(f"/api/projects/{pid}/export").content)})
    assert ok.status_code == 200 and ok.json()["warnings"] == []


def test_validation_messages_are_localized_but_keep_structure(client):
    r = client.post("/api/remnants", json={"material_code": "Z", "length": 100, "width": 100, "qty": 1}).json()
    bad = client.patch(f"/api/remnants/{r['id']}", json={"length": -5})
    assert bad.status_code == 422
    d = bad.json()
    e = d["detail"][0]
    assert e["type"] == "greater_than_equal" and e["loc"][-1] == "length"                  # tuzilma avvalgidek
    assert "Input should" not in e["msg"] and "не меньше" in e["msg"] and d["message"].startswith("Длина: ")
    uz = client.patch(f"/api/remnants/{r['id']}", json={"length": -5}, headers=UZ).json()
    assert "kam bo'lmasligi" in uz["detail"][0]["msg"] and "kam bo'lmasligi" in uz["message"]
    p = client.post("/api/projects", json={"name": "L"}).json()
    prid = p["products"][0]["id"]
    bad = client.patch(f"/api/projects/{p['id']}/products/{prid}", json={"name": None})
    assert bad.status_code == 422 and "valid string" not in json.dumps(bad.json())
    bad = client.patch(f"/api/projects/{p['id']}/products/{prid}", json={"qty": "abc"}, headers=UZ)
    assert bad.status_code == 422 and "butun son" in bad.json()["detail"][0]["msg"]
    miss = client.post("/api/folders", json={})
    assert miss.status_code == 422 and miss.json()["detail"][0]["type"] == "missing" and "обязательное" in miss.json()["message"]


def test_settings_profile_name_upsert_and_backup_import(client):
    assert client.post("/api/settings/print", json={"name": "   ", "data": {}}).status_code == 400
    assert client.post("/api/settings/print", json={"name": "x" * 101, "data": {}}).status_code == 400
    a = client.post("/api/settings/print", json={"name": "QA Zaxira Zq7", "data": {"header": False}}).json()
    dup = client.post("/api/settings/print?upsert=true", json={"name": "qa zaxira zq7", "data": {"header": True}}).json()
    assert dup["id"] == a["id"] and dup["data"]["header"] is True
    assert client.put(f"/api/settings/print/{a['id']}", json={"name": ""}).status_code == 400
    count = lambda: sum(1 for x in client.get("/api/settings/print").json() if x["name"] == "QA Zaxira Zq7")   # noqa: E731
    assert count() == 1
    backup = {"app": "MebeliX Kroy", "version": 1, "profiles": {
        "print": [{"name": "QA Zaxira Zq7", "data": {"header": False}, "is_default": False},
                  {"name": "QA Yangi Zq7", "data": {"warehouse": False}, "is_default": False}],
        "labels": [{"name": "QA Etiketka Zq7", "data": {"width_mm": 40}}],
        "nomalum": [{"name": "x"}],
        "app": [{"name": "QA Yomon Zq7", "data": {"default_sheet_length": 0}}]}}
    r1 = client.post("/api/backup/settings/import", json=backup).json()
    assert (r1["created"], r1["updated"], r1["skipped"]) == (2, 1, 0) and len(r1["invalid"]) == 1
    assert r1["invalid"][0]["scope"] == "app" and "default_sheet_length" in r1["invalid"][0]["error"]
    r2 = client.post("/api/backup/settings/import", json=backup).json()                  # qayta import — dublikat yo'q
    assert (r2["created"], r2["updated"]) == (0, 3)
    r3 = client.post("/api/backup/settings/import?mode=skip", json=backup).json()
    assert (r3["created"], r3["updated"], r3["skipped"]) == (0, 0, 3)
    names = [x["name"] for x in client.get("/api/settings/print").json()]
    assert names.count("QA Zaxira Zq7") == 1 and names.count("QA Yangi Zq7") == 1
    assert [x["name"] for x in client.get("/api/settings/labels").json()].count("QA Etiketka Zq7") == 1
    for bad in ({"x": 1}, {"profiles": []}, {"profiles": {"nomalum": []}}, [1]):
        assert client.post("/api/backup/settings/import", json=bad).status_code == 400, bad
    assert set(client.get("/api/backup/settings").json()["profiles"]) >= {"print", "labels", "app"}


def test_pdf_without_weasyprint_is_501_with_instructions(client, kravat, monkeypatch):
    monkeypatch.setitem(sys.modules, "weasyprint", None)               # import weasyprint → ImportError
    from app.services import pdf_render
    monkeypatch.setattr(pdf_render, "chrome_path", lambda: None)       # Chrome / Edge ham yo'q
    r = client.get(f"/api/projects/{kravat[0]}/report.pdf")
    assert r.status_code == 501 and "weasyprint" in r.json()["detail"]
    r = client.get(f"/api/projects/{kravat[0]}/report.pdf", headers=UZ)
    assert r.status_code == 501 and "Chop etish" in r.json()["detail"]


# ───────────────────────── 13. Kroy hajmi chegarasi ─────────────────────────
def test_optimize_item_limit(client, kravat):
    pid, cs, _el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    part = _op(p, "CS")[0]["parts"][0]
    assert client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{part['id']}", json={"qty": 100_000}).status_code == 200
    t0 = time.time()
    r = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    assert r.status_code == 400 and "20000" in r.json()["detail"] and time.time() - t0 < 5
    assert client.post(f"/api/projects/{pid}/operations/{cs}/variants").status_code == 400
    r = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast", headers=UZ)
    assert "juda ko'p" in r.json()["detail"]
    # loyiha qulfi bo'sh: boshqa amallar o'tadi
    assert client.patch(f"/api/projects/{pid}", json={"note": "ok"}).status_code == 200


# ───────────────────────── 9. Excel / CSV import ─────────────────────────
def test_parse_number_and_qty():
    from app.services.importers import parse_number, parse_qty
    cases = {"1 200,5": 1200.5, "1 200": 1200, "1 200,5": 1200.5, "1.200,5": 1200.5, "1,200.5": 1200.5,
             "1200 мм": 1200, "300,5": 300.5, "  42 ": 42, "-100": -100, "1.200.500": 1200500, "1,2,3": 123,
             5: 5, 5.5: 5.5, "0": 0}
    for raw, want in cases.items():
        assert parse_number(raw) == want, raw
    for raw in ("abc", "12x45", "", None, "1e3", float("nan"), "--5", True):
        assert parse_number(raw) is None, raw
    assert parse_qty("2 шт") == 2 and parse_qty("x2") == 2 and parse_qty(3.0) == 3 and parse_qty("2 (шт)") == 2
    assert parse_qty("2,5") is None and parse_qty("-1") is None and parse_qty("abc") is None and parse_qty(10**7) is None


def _xlsx(rows):
    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_excel_import_reports_skipped_rows_and_creates_edges(client, kravat):
    pid, cs, el = kravat
    rows = [["Nomi", "Uzunlik", "En", "Soni", "Tekstura", "Kromka"],
            ["Полка", "1 200,5", "300", "2 шт", "", "A"],                # 2: matn son + birlik + kromka belgisi
            ["Нет ширины", 500, "", 1, "", ""],                               # 3
            ["abc", "abc", 300, 1, "", ""],                                   # 4
            ["Нулевая", 0, 300, 1, "", ""],                                   # 5
            ["Минус", -100, 300, 1, "", ""],                                  # 6
            ["Новая", 400, 200, 1, "", "Новая кромка"],                       # 7: noma'lum nom → yangi EL
            ["Две", 400, 200, 1, "", "новая кромка"],                         # 8: o'sha EL (harf farqi yo'q)
            ["Без кромки", 100, 100, 1, "", "-"],                             # 9
            [None] * 6,                                                       # 10: bo'sh qator — jim
            ["Дробное", 100, 100, 2.5, "", ""],                               # 11
            ["Гигант", 1e7, 100, 1, "", ""]]                                  # 12
    cmap = {"name": "A", "length": "B", "width": "C", "qty": "D", "grain": "E", "edge_top": "F"}
    r = client.post(f"/api/projects/{pid}/operations/{cs}/parts/import", files={"file": ("d.xlsx", _xlsx(rows))},
                    data={"col_map": json.dumps(cmap), "sheet": 0, "start_row": 2})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["id"] == pid and d["operations"] and d["products"]                  # eski maydonlar saqlangan
    assert d["imported"] == 4
    assert [s["row"] for s in d["skipped"]] == [3, 4, 5, 6, 11, 12]
    assert all(s["reason"] for s in d["skipped"])
    assert "Ширина" in d["skipped"][0]["reason"] and "abc" in d["skipped"][1]["reason"]
    assert any("Новая кромка" in w for w in d["warnings"]) and any("6" in w for w in d["warnings"])
    new_els = [o for o in _op(d, "EL") if o["name"] == "Новая кромка"]
    assert len(new_els) == 1 and len(d["created_edges"]) == 1 and d["created_edges"][0]["id"] == new_els[0]["id"]
    assert new_els[0]["el"]["symbol"] != "A" and new_els[0]["el"]["color"] != _op(d, "EL")[0]["el"]["color"]
    parts = {x["name"]: x for x in _op(d, "CS")[0]["parts"]}
    assert parts["Полка"]["length"] == 1200.5 and parts["Полка"]["qty"] == 2 and parts["Полка"]["edge_top"]["op_id"] == el
    assert parts["Новая"]["edge_top"]["op_id"] == new_els[0]["id"] == parts["Две"]["edge_top"]["op_id"]
    assert parts["Без кромки"]["edge_top"]["op_id"] is None
    # uz tilida sabab
    r = client.post(f"/api/projects/{pid}/operations/{cs}/parts/import", files={"file": ("d.xlsx", _xlsx(rows))},
                    data={"col_map": json.dumps(cmap), "start_row": 2}, headers=UZ)
    assert "bo'sh" in r.json()["skipped"][0]["reason"]
    # ustunlar ko'rsatilmagan — 400
    r = client.post(f"/api/projects/{pid}/operations/{cs}/parts/import", files={"file": ("d.xlsx", _xlsx(rows))},
                    data={"col_map": json.dumps({"name": "A"}), "start_row": 2})
    assert r.status_code == 400


def test_csv_cp1251_and_utf8(client, kravat):
    pid, cs, _el = kravat
    cmap = {"name": "A", "length": "B", "width": "C", "qty": "D"}
    text = "Наименование;Длина;Ширина;Кол\nПолка кириллица;764;300;2\nСтенка;1 200,5;500;1\n"
    for enc in ("cp1251", "utf-8-sig", "utf-8"):
        r = client.post(f"/api/projects/{pid}/operations/{cs}/parts/import",
                        files={"file": ("d.csv", text.encode(enc))}, data={"col_map": json.dumps(cmap)})
        assert r.status_code == 200, enc
        names = [x["name"] for x in _op(r.json(), "CS")[0]["parts"]]
        assert names[-2:] == ["Полка кириллица", "Стенка"], (enc, names)
        assert r.json()["imported"] == 2 and r.json()["skipped"] == []
    pv = client.post("/api/import/preview", files={"file": ("d.csv", text.encode("cp1251"))}).json()
    assert pv["rows"][1][0] == "Полка кириллица"


# ───────────────────────── 10. .project import ─────────────────────────
def _legacy_xml():
    from xml.sax.saxutils import quoteattr
    prog = ('<?xml version="1.0"?><program dx="720" dy="560" dz="16"><tool name="Bore8" d="8"/>'
            '<bf x="37" y="32" dp="12" ac="3" as="32" name="Bore8"/><ms x="0" y="100" dp="10" c="1" name="Mill8"/>'
            '<ma x="100" y="150" r="50" dir="true"/><xy x="10" y="20"/><zz q="1"/></program>')
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project name="Paz test" currency="сум" date="1775278504994">
  <good typeId="product" id="1" code="P1" name="Shkaf" count="1">
    <part id="11" code="A1" name="Bok" count="1" dl="720" dw="560" grt="@operation#5" grts="false" grl="@operation#5"/>
  </good>
  <good typeId="sheet" id="4" code="LDSP" name="LDSP 16" t="16" l="2750" w="1830" count="2">
    <part id="20" l="2750" w="1830" count="10000"/></good>
  <operation typeId="GR" id="5" typeName="Paz 4x8" grWidth="6" grDepth="9" grOffset="12" grCost="1500"/>
  <operation typeId="CN" id="6" typeName="Pokraska"/>
  <operation typeId="CS" id="2" t="16" l="2750" w="1830"><material id="4" count="2"/><part id="11"/></operation>
  <operation typeId="XNC" id="7" code="X1" typeName="Bok" count="1" program={quoteattr(prog)}><part id="11"/></operation>
</project>""".encode("utf-8")


def test_legacy_project_xnc_arc_origin_array_grooves_epoch_and_skip_warnings():
    from app.plugins.legacy_project import import_project
    p, warnings = import_project(_legacy_xml(), "paz.project")
    assert p.order_date == date(2026, 4, 4)                                   # epoch-ms sana o'qildi
    gr = next(o for o in p.operations if o.type.value == "GR")
    assert (gr.name, gr.gr.width, gr.gr.depth, gr.gr.offset, gr.gr.price) == ("Paz 4x8", 6, 9, 12, 1500)
    part = next(o for o in p.operations if o.type.value == "CS").parts[0]
    assert part.groove_top.op_id == gr.id and part.groove_top.back_side is True          # grts=false → orqa
    assert part.groove_left.op_id == gr.id and part.groove_left.back_side is False
    assert part.groove_bottom.op_id is None
    xnc = next(o for o in p.operations if o.type.value == "XNC").xnc
    assert [c.cmd for c in xnc.program] == ["Tool", "DrillFront", "MillStart", "MillArc", "Origin"]
    drill, arc, origin = xnc.program[1], xnc.program[3], xnc.program[4]
    assert drill.params["AC"] == 3 and drill.params["AS"] == 32
    assert arc.params["R"] == 50 and arc.params["DIR"] == "true" and arc.params["X"] == 100
    assert origin.params == {"X": 10, "Y": 20}
    assert any("CN" in w and "Pokraska" in w for w in warnings)               # qaysi operatsiya o'tkazib yuborildi (SP, CL — endi import qilinadi)
    assert any("<zz>" in w and "X1" in w for w in warnings)                  # tanilmagan XNC tegi
    assert not any("Paz 4x8" in w for w in warnings)                          # GR endi o'tkazib yuborilmaydi


def test_legacy_project_dates():
    from app.plugins.legacy_project import _date
    assert _date("1775278504994") == date(2026, 4, 4) and _date("1775278504") == date(2026, 4, 4)
    assert _date("2026-04-04") == date(2026, 4, 4) and _date("04.04.2026") == date(2026, 4, 4)
    assert _date("0") is None and _date("abc") is None and _date("1000000000000000") is None and _date(None) is None


def test_legacy_project_import_via_api_keeps_grooves(client):
    r = client.post("/api/projects/import-file", files={"file": ("paz.project", _legacy_xml())})
    assert r.status_code == 200
    d = r.json()
    assert d["project"]["order_date"] == "2026-04-04" and any("Pokraska" in w for w in d["warnings"])
    assert _op(d["project"], "GR") and _op(d["project"], "CS")[0]["parts"][0]["groove_top"]["op_id"]


# ───────────────────────── Tilga mos va auth o'chiq (standart) ─────────────────────────
def test_auth_off_default_unchanged(client):
    me = client.get("/api/me").json()
    assert me["name"] == "admin" and me["read_only"] is False
    assert client.post("/api/projects", json={"name": "ochiq"}).status_code == 200
