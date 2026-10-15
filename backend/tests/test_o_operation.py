"""(O) Комплектация и другие действия: model, hisob (390 000 / 130 000 namunasi), ombor talabnomasi, mahsulot narxi,
buferdan qo'yish, chegaralar, eski JSON, hisobot, MES, `.project` importi (inventar 03 §3.8)."""
import json

import pytest

from app.models import O_MAX_ROWS, Operation, Project
from app.plugins.legacy_project import import_project
from app.services import o_ops

MATS = [
    dict(code="R-1", name="Ruchka", unit="шт", qty=4, price=15000),
    dict(code="P-2", name="Plyonka", unit="м", qty=2.5, price=8000),
]


def _api(client, method, url, **kw):
    r = getattr(client, method)(url, **kw)
    assert r.status_code == 200, (url, r.status_code, r.text[:300])
    return r.json()


def _project(client, qty=3, name="Shkaf"):
    p = _api(client, "post", "/api/projects", json={"name": "O test"})
    pid, prid = p["id"], p["products"][0]["id"]
    _api(client, "patch", f"/api/projects/{pid}/products/{prid}", json={"name": name, "qty": qty})
    return pid, prid


def _o_op(client, pid, owner=None, work=50000, mats=MATS, name="Furnitura"):
    p = _api(client, "post", f"/api/projects/{pid}/operations", json={"type": "O", "name": name})
    oid = p["operations"][-1]["id"]
    _api(client, "put", f"/api/projects/{pid}/operations/{oid}/o/materials", json=mats)
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{oid}",
             json={"o": {"owner_product_id": owner, "work_cost": work}})
    return oid, p


def _op(p, oid):
    return next(o for o in p["operations"] if o["id"] == oid)


def _wh(client, pid):
    return {r["name"].split(" — ")[-1]: r for r in client.get(f"/api/projects/{pid}/warehouse").json() if r["type"] == "O"}


# ───────────────────────── 1. spetsifikatsiya namunasi ─────────────────────────
def test_sample_product_owner_390000(client):
    pid, prid = _project(client, qty=3)
    oid, p = _o_op(client, pid, owner=prid)
    op = _op(p, oid)
    assert op["type"] == "O" and op["o"]["multiplier"] == 3
    assert op["cost_material"] == 240000 and op["cost_operation"] == 150000
    assert op["cost_material"] + op["cost_operation"] == 390000
    wh = _wh(client, pid)
    assert wh["Ruchka"]["qty"] == 12 and wh["Plyonka"]["qty"] == 7.5
    assert wh["Ruchka"]["unit"] == "шт" and wh["Plyonka"]["unit"] == "м"
    assert wh["Ruchka"]["code"] == "R-1" and wh["Ruchka"]["name"] == "Furnitura — Ruchka"
    assert wh["Ruchka"]["price"] == 15000 and wh["Ruchka"]["sum"] == 12 * 15000
    # mahsulot narxi: 1 dona uchun (butun narx shu mahsulotga; Всего = × soni)
    pr = p["products"][0]
    assert pr["cost_material"] == 80000 and pr["cost_operation"] == 50000


def test_sample_project_owner_130000(client):
    pid, prid = _project(client, qty=3)
    oid, p = _o_op(client, pid, owner=None)
    op = _op(p, oid)
    assert op["o"]["multiplier"] == 1
    assert op["cost_material"] == 80000 and op["cost_operation"] == 50000
    assert op["cost_material"] + op["cost_operation"] == 130000
    wh = _wh(client, pid)
    assert wh["Ruchka"]["qty"] == 4 and wh["Plyonka"]["qty"] == 2.5
    # standart: loyiha egasi bo'lgan O narxi mahsulotlarga taqsimlanmaydi (savol 3)
    assert p["products"][0]["cost_material"] == 0 and p["products"][0]["cost_operation"] == 0


def test_project_owner_spread_switch(client, monkeypatch):
    """SPREAD_PROJECT_OWNED=True: loyiha narxi mahsulotlarga ularning soniga proporsional taqsimlanadi."""
    monkeypatch.setattr(o_ops, "SPREAD_PROJECT_OWNED", True)
    pid, prid = _project(client, qty=4)
    p2 = _api(client, "post", f"/api/projects/{pid}/products", json={"name": "Stol", "qty": 4})
    oid, p = _o_op(client, pid, owner=None, work=80000, mats=[dict(name="x", qty=1, price=40000)])
    a, b = p["products"]
    assert a["cost_material"] == b["cost_material"] == 5000          # 40 000 × (4/8) / 4
    assert a["cost_operation"] == b["cost_operation"] == 10000       # 80 000 × (4/8) / 4
    assert p2["products"][1]["name"] == "Stol"


def test_mult_zero_and_qty_change(client):
    pid, prid = _project(client, qty=3)
    oid, p = _o_op(client, pid, owner=prid)
    # soni 3 → 5: narx va talabnoma qayta hisoblanadi
    p = _api(client, "patch", f"/api/projects/{pid}/products/{prid}", json={"qty": 5})
    op = _op(p, oid)
    assert op["cost_material"] == 400000 and op["cost_operation"] == 250000 and op["o"]["multiplier"] == 5
    wh = _wh(client, pid)
    assert wh["Ruchka"]["qty"] == 20 and wh["Plyonka"]["qty"] == 12.5
    # soni 0 → narx 0, talabnomada qator yo'q
    p = _api(client, "patch", f"/api/projects/{pid}/products/{prid}", json={"qty": 0})
    op = _op(p, oid)
    assert op["cost_material"] == 0 and op["cost_operation"] == 0
    assert _wh(client, pid) == {}


def test_product_deleted_owner_falls_back_to_project(client):
    pid, prid = _project(client, qty=3)
    oid, p = _o_op(client, pid, owner=prid)
    assert _op(p, oid)["cost_material"] == 240000
    p = _api(client, "delete", f"/api/projects/{pid}/products/{prid}")
    op = _op(p, oid)
    assert op["o"]["owner_product_id"] is None and "owner_lost" in op["o"]["messages"]
    assert op["cost_material"] == 80000 and op["cost_operation"] == 50000          # 130 000 — loyiha egasi
    wh = _wh(client, pid)
    assert wh["Ruchka"]["qty"] == 4 and wh["Plyonka"]["qty"] == 2.5
    # ogohlantirishni foydalanuvchi yopadi
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{oid}", json={"o": {"messages": []}})
    assert _op(p, oid)["o"]["messages"] == []


def test_owner_validation_422(client):
    pid, prid = _project(client)
    oid, _p = _o_op(client, pid)
    r = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"o": {"owner_product_id": "yoq-mahsulot"}})
    assert r.status_code == 422
    op = _op(client.get(f"/api/projects/{pid}").json(), oid)
    full = {**op, "o": {**op["o"], "owner_product_id": "yoq-mahsulot"}}
    assert client.put(f"/api/projects/{pid}/operations/{oid}", json=full).status_code == 422
    ok = {**op, "o": {**op["o"], "owner_product_id": prid}}
    assert client.put(f"/api/projects/{pid}/operations/{oid}", json=ok).status_code == 200


# ───────────────────────── 2. Buferdan qo'yish ─────────────────────────
def _paste(client, pid, oid, text, mode="append"):
    return _api(client, "post", f"/api/projects/{pid}/operations/{oid}/o/materials/paste",
                json={"text": text, "mode": mode})


def test_paste_numbers_blank_rows_and_skipped(client):
    pid, _prid = _project(client)
    oid, _p = _o_op(client, pid, mats=[])
    text = ("K1\tРучка\tшт\t4\t15 000,50\n"
            "\n"                                    # butunlay bo'sh qator — jim o'tkaziladi
            "K2\tПлёнка\t\t2 шт\t1 200,5\n"          # birlik — «2 шт» qo'shimchasidan
            "\t\t\n"                                # faqat ajratgichlar — «bo'sh qator» (skipped)
            "K3\tВинт\tшт\tabc\t5\n"                # Кол — son emas
            "\t\tшт\t1\t1\n"                        # na kod, na nom
            "K4\tСаморез\tшт\t-3\t1\n"              # manfiy
            "K5\tУпаковка\n")                       # faqat kod va nom: Кол=1, Цена=0, Ед.И=standart
    r = _paste(client, pid, oid, text)
    assert r["added"] == 3
    assert [s["row"] for s in r["skipped"]] == [4, 5, 6, 7]
    assert all(s["reason"] for s in r["skipped"]) and r["warnings"]
    mats = _op(r, oid)["o"]["materials"]
    assert [(m["code"], m["unit"], m["qty"], m["price"]) for m in mats] == [
        ("K1", "шт", 4, 15000.5), ("K2", "шт", 2, 1200.5), ("K5", "шт", 1, 0)]
    # ikkinchi qo'yish — oxiriga qo'shiladi; mode=replace — almashtiradi
    r = _paste(client, pid, oid, "K9\tMix\tm\t1,5\t10")
    assert len(_op(r, oid)["o"]["materials"]) == 4 and _op(r, oid)["o"]["materials"][-1]["qty"] == 1.5
    r = _paste(client, pid, oid, "K7\tOnly\tшт\t1\t1", mode="replace")
    assert [m["code"] for m in _op(r, oid)["o"]["materials"]] == ["K7"]


def test_paste_header_row_skipped_and_nothing_added_no_history(client):
    pid, _prid = _project(client)
    oid, _p = _o_op(client, pid, mats=[])
    r = _paste(client, pid, oid, "Код\tНаименование\tЕд.И\tКол\tЦена\nA\tB\tшт\t1\t2")
    assert r["added"] == 1 and not r["skipped"] and len(r["warnings"]) == 1
    v = client.get(f"/api/projects/{pid}/history").json()["version"]
    r = _paste(client, pid, oid, "   \n\n")                 # hech narsa qo'shilmadi
    assert r["added"] == 0 and client.get(f"/api/projects/{pid}/history").json()["version"] == v


def test_paste_row_limit_5001(client):
    pid, _prid = _project(client)
    oid, _p = _o_op(client, pid, mats=[])
    text = "\n".join(f"C{i}\tN{i}\tшт\t1\t1" for i in range(1, O_MAX_ROWS + 2))        # 5001 qator
    r = _paste(client, pid, oid, text)
    assert r["added"] == O_MAX_ROWS
    assert [s["row"] for s in r["skipped"]] == [O_MAX_ROWS + 1] and len(_op(r, oid)["o"]["materials"]) == O_MAX_ROWS
    r = _paste(client, pid, oid, "X\tY\tшт\t1\t1")      # to'lgan jadvalga qo'shib bo'lmaydi
    assert r["added"] == 0 and len(r["skipped"]) == 1
    # PUT ham 5001 qatorni rad etadi
    rows = [dict(name=f"n{i}") for i in range(O_MAX_ROWS + 1)]
    assert client.put(f"/api/projects/{pid}/operations/{oid}/o/materials", json=rows).status_code == 422


def test_paste_long_text_skipped_not_truncated(client):
    pid, _prid = _project(client)
    oid, _p = _o_op(client, pid, mats=[])
    r = _paste(client, pid, oid, f"C1\t{'x' * 301}\tшт\t1\t1\nC2\tok\t{'u' * 21}\t1\t1\nC3\tok\tшт\t1\t1")
    assert r["added"] == 1 and [s["row"] for s in r["skipped"]] == [1, 2]
    assert client.post(f"/api/projects/{pid}/operations/{oid}/o/materials/paste",
                       json={"text": "x" * 2_000_001}).status_code == 422


def test_paste_unit_from_defaults(client):
    try:
        _api(client, "put", "/api/settings/o_defaults/default", json={"work_cost": 12000, "unit": "компл."})
        pid, _prid = _project(client)
        p = _api(client, "post", f"/api/projects/{pid}/operations", json={"type": "O"})
        o = p["operations"][-1]
        assert o["o"]["work_cost"] == 12000 and o["cost_operation"] == 12000        # o_defaults: yangi operatsiya ish narxi
        r = _paste(client, pid, o["id"], "A\tNomi\t\t3\t100")
        assert _op(r, o["id"])["o"]["materials"][0]["unit"] == "компл."
    finally:
        client.put("/api/settings/o_defaults/default", json={"work_cost": 0, "unit": "шт"})


# ───────────────────────── 3. Chegaralar ─────────────────────────
def test_limits_422(client):
    pid, _prid = _project(client)
    oid, _p = _o_op(client, pid)
    url = f"/api/projects/{pid}/operations/{oid}/o/materials"
    for bad in (dict(qty=-1), dict(price=-5), dict(qty=1e10), dict(price=1e10), dict(name="x" * 301),
                dict(code="x" * 101), dict(unit="x" * 21)):
        r = client.put(url, json=[{"name": "n", **bad}])
        assert r.status_code == 422, bad
    assert client.patch(f"/api/projects/{pid}/operations/{oid}", json={"o": {"work_cost": -1}}).status_code == 422
    assert client.patch(f"/api/projects/{pid}/operations/{oid}", json={"o": {"work_cost": 1e12}}).status_code == 422
    # jadval o'zgarmadi
    assert len(_op(client.get(f"/api/projects/{pid}").json(), oid)["o"]["materials"]) == 2
    # boshqa tur operatsiyasiga — 400
    cs = _api(client, "post", f"/api/projects/{pid}/operations", json={"type": "CS", "name": "LDSP"})["operations"][-1]["id"]
    assert client.put(f"/api/projects/{pid}/operations/{cs}/o/materials", json=[]).status_code == 400
    assert client.post(f"/api/projects/{pid}/operations/{cs}/o/materials/paste", json={"text": "a\tb"}).status_code == 400


# ───────────────────────── 4. Eski JSON ─────────────────────────
def test_old_json_without_o_opens(client):
    doc = {"name": "eski", "products": [{"name": "P", "qty": 2}],
           "operations": [{"type": "O", "name": "Komplekt"}, {"type": "CS", "name": "LDSP"}]}
    assert Operation.model_validate({"type": "O"}).o is None                          # migratsiyasiz
    r = client.post("/api/projects/import-file", files={"file": ("eski.mxk.json", json.dumps(doc).encode())})
    assert r.status_code == 200, r.text
    p = r.json()["project"]
    o = next(x for x in p["operations"] if x["type"] == "O")
    assert o["o"]["materials"] == [] and o["cost_material"] == 0 and o["cost_operation"] == 0
    assert client.get(f"/api/projects/{p['id']}/report").status_code == 200
    assert client.get(f"/api/projects/{p['id']}/warehouse").status_code == 200


def test_legacy_context_clamps_out_of_range():
    big = [dict(name="x" * 500, qty=-5, price=1e12, code="c" * 200, unit="u" * 50) for _ in range(O_MAX_ROWS + 10)]
    p = Project.model_validate({"operations": [{"type": "O", "o": {"materials": big, "work_cost": -3}}]})
    o = p.operations[0].o
    assert len(o.materials) == O_MAX_ROWS and o.work_cost == 0
    m = o.materials[0]
    assert m.qty == 0 and m.price == 1e9 and len(m.name) == 300 and len(m.code) == 100 and len(m.unit) == 20


def test_export_import_roundtrip(client):
    pid, prid = _project(client, qty=3)
    oid, _p = _o_op(client, pid, owner=prid)
    data = client.get(f"/api/projects/{pid}/export").content
    r = client.post("/api/projects/import-file", files={"file": ("x.mxk.json", data)})
    assert r.status_code == 200, r.text
    q = r.json()["project"]
    o = next(x for x in q["operations"] if x["type"] == "O")
    assert [m["name"] for m in o["o"]["materials"]] == ["Ruchka", "Plyonka"] and o["o"]["work_cost"] == 50000
    # egasi mahsulot id — importda yangi id olmaydi (mahsulot ham shu id bilan keladi)
    assert o["o"]["owner_product_id"] == q["products"][0]["id"] and o["cost_material"] + o["cost_operation"] == 390000


def test_clone_and_undo(client):
    pid, prid = _project(client)
    oid, _p = _o_op(client, pid)
    p = _api(client, "post", f"/api/projects/{pid}/operations/{oid}/clone")
    ops = [o for o in p["operations"] if o["type"] == "O"]
    assert len(ops) == 2 and len(ops[1]["o"]["materials"]) == 2
    # butun jadvalni almashtirish — bitta undo qadami
    _api(client, "put", f"/api/projects/{pid}/operations/{oid}/o/materials", json=[dict(name="yangi", qty=1, price=1)])
    p = _api(client, "post", f"/api/projects/{pid}/undo")
    assert [m["name"] for m in _op(p, oid)["o"]["materials"]] == ["Ruchka", "Plyonka"]


# ───────────────────────── 5. Hisobot, MES ─────────────────────────
def test_report_sections_and_product_table(client):
    pid, prid = _project(client, qty=3)
    oid, _p = _o_op(client, pid, owner=prid)
    _api(client, "patch", f"/api/projects/{pid}/operations/{oid}", json={"description": "Qadoqlash <b>x</b>"})
    html = client.post(f"/api/projects/{pid}/report?lang=ru", json={"products_list": True, "materials_list": True}).text
    assert "(O) Комплектация" in html and "Ruchka" in html and "Plyonka" in html
    assert "Требование на склад" in html and "Furnitura — Ruchka" in html
    assert "Qadoqlash &lt;b&gt;x&lt;/b&gt;" in html and "<b>x</b>" not in html          # izoh escape qilinadi
    assert "390000 UZS" in html                                                        # loyiha jami (sarlavha) O ni ham yig'adi
    assert "240000 UZS (80000 × 3)" in html and "150000 UZS (50000 × 3)" in html       # O bo'limi: ko'paytirgich bilan
    assert ">80000<" in html and ">50000<" in html                                     # mahsulot narxi 1 dona uchun
    uz = client.post(f"/api/projects/{pid}/report?lang=uz", json={}).text
    assert "(O) Komplektatsiya" in uz
    only = client.post(f"/api/projects/{pid}/report", json={"o_params": False, "o_materials": False}).text
    assert "(O) " not in only
    no_tbl = client.post(f"/api/projects/{pid}/report", json={"o_materials": False}).text
    assert "(O) Комплектация" in no_tbl and "Plyonka" not in no_tbl.split("(O) Комплектация")[1]      # jadvalsiz bo'lim
    assert "Plyonka" in html.split("(O) Комплектация")[1]                                              # jadvalli bo'lim
    # chop etilmaydigan operatsiya — bo'lim yo'q
    _api(client, "patch", f"/api/projects/{pid}/operations/{oid}", json={"print": False})
    assert "(O) Комплектация" not in client.post(f"/api/projects/{pid}/report", json={}).text


def test_mes_export_has_o_rows(client):
    pid, prid = _project(client, qty=3)
    oid, _p = _o_op(client, pid, owner=prid)
    ex = client.get(f"/api/projects/{pid}/mes-export").json()
    rows = [r for r in ex["warehouse"] if r["type"] == "O"]
    assert sorted(r["qty"] for r in rows) == [7.5, 12]
    op = next(o for o in ex["operations"] if o["id"] == oid)
    assert op["type"] == "O" and op["owner_product_id"] == prid and op["multiplier"] == 3 and op["work_cost"] == 50000
    assert {m["name"]: m["qty_total"] for m in op["materials"]} == {"Ruchka": 12, "Plyonka": 7.5}
    assert ex["cost_material"] == 240000 and ex["cost_operation"] == 150000


# ───────────────────────── 6. `.project` importi ─────────────────────────
def _xml(owner="1", cost_m="", cost_o="50000", extra="", count_a="4", with_c=True):
    c = '<material id="12" count="2.5"/>' if with_c else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project version="1" currency="сум" date="1775278504994">
  <good id="1" typeId="product" name="Shkaf" count="3"/>
  <good id="10" typeId="simple" code="R-1" name="Ruchka" unit="шт" count="1" cost="15000"/>
  <good id="12" typeId="simple" code="P-2" name="Plyonka" unit="м" count="1" cost="8000"/>
  <operation id="5" typeId="O" typeName="Komplektatsiya" description="Qadoqlash" owner="{owner}"
             costOperation="{cost_o}" {cost_m} printable="false" startNewPage="false">
    <material id="10" count="{count_a}"/>
    {c}
  </operation>
  {extra}
</project>""".encode("utf-8")


def test_bazis_import_o_operation():
    p, warns = import_project(_xml(), "t.project")
    o = next(x for x in p.operations if x.type.value == "O")
    prod = p.products[0]
    assert o.name == "Komplektatsiya" and o.description == "Qadoqlash"
    assert o.print is False and o.new_page is False
    assert o.o.owner_product_id == prod.id and o.o.work_cost == 50000
    assert [(m.code, m.name, m.unit, m.qty, m.price) for m in o.o.materials] == [
        ("R-1", "Ruchka", "шт", 4, 15000), ("P-2", "Plyonka", "м", 2.5, 8000)]
    assert not any("O" == w for w in warns)
    from app.services import calc
    calc.recalc_project(p)
    assert o.cost_material == 240000 and o.cost_operation == 150000                 # 390 000 (mahsulot soni 3)


def test_bazis_import_project_owner_and_warnings():
    # egasi — loyiha (0): ko'paytirgich yo'q; yo'q material havolasi — ogohlantirish bilan o'tkaziladi
    xml = _xml(owner="0").replace(b'<material id="12" count="2.5"/>', b'<material id="99" count="1"/>')
    p, warns = import_project(xml, "t.project")
    o = next(x for x in p.operations if x.type.value == "O")
    assert o.o.owner_product_id is None and [m.name for m in o.o.materials] == ["Ruchka"]
    assert any("99" in w for w in warns)
    # egasi — mavjud bo'lmagan id: loyiha egasi + ogohlantirish
    p, warns = import_project(_xml(owner="777"), "t.project")
    assert next(x for x in p.operations if x.type.value == "O").o.owner_product_id is None
    assert any("777" in w for w in warns)
    # qolgan turlar (CN — nesting) hamon o'tkazib yuboriladi va aytiladi; O — endi yo'q (CL W11 da import qilinadi)
    p, warns = import_project(_xml(extra='<operation id="6" typeId="CN" typeName="Pogonaj"/>'), "t.project")
    assert any("CN" in w and "Pogonaj" in w for w in warns) and not any("typeId" in w for w in warns)


def test_bazis_import_scaled_costs_heuristic():
    # fayldagi narxlar barcha mahsulotlar uchun (× 3) yozilgan: costMaterial = 80 000 × 3 → ish narxi 3 ga bo'linadi
    p, warns = import_project(_xml(cost_m='costMaterial="240000"', cost_o="150000"), "t.project")
    o = next(x for x in p.operations if x.type.value == "O")
    assert o.o.work_cost == 50000 and any("÷ 3" in w for w in warns)
    # costMaterial 1 dona narxiga teng — ish narxi o'zgarmaydi
    p, warns = import_project(_xml(cost_m='costMaterial="80000"', cost_o="50000"), "t.project")
    assert next(x for x in p.operations if x.type.value == "O").o.work_cost == 50000 and not any("÷" in w for w in warns)


def test_bazis_import_via_api_total_390000(client):
    r = client.post("/api/projects/import-file", files={"file": ("k.project", _xml())})
    assert r.status_code == 200, r.text
    p = r.json()["project"]
    o = next(x for x in p["operations"] if x["type"] == "O")
    assert o["cost_material"] + o["cost_operation"] == 390000
    wh = [x for x in client.get(f"/api/projects/{p['id']}/warehouse").json() if x["type"] == "O"]
    assert sorted(x["qty"] for x in wh) == [7.5, 12]


# ───────────────────────── 7. Parser (birlik testlari) ─────────────────────────
@pytest.mark.parametrize("cell,expected", [("1 200,5", 1200.5), ("1.200,5", 1200.5), ("2 шт", 2.0), ("3", 3.0), ("0,5", 0.5)])
def test_parse_paste_number_formats(cell, expected):
    res = o_ops.parse_paste(f"A\tB\tшт\t{cell}\t{cell}")
    assert res.rows and res.rows[0].qty == expected and res.rows[0].price == expected


def test_parse_rows_for_excel_import_tabs():
    """Excel importi (W3: «Простые операции» / «Материалы» tabi) katak qatorlarini shu funksiyaga beradi."""
    res = o_ops.parse_rows([(2, ["K1", "Ручка", "шт", 4.0, 15000.5]), (3, [None, None, None, None, None]),
                            (4, ["K2", None, "м", "2,5", None]), (5, ["", "", "", "-1", "1"])])
    assert [(m.code, m.name, m.unit, m.qty, m.price) for m in res.rows] == [
        ("K1", "Ручка", "шт", 4.0, 15000.5), ("K2", "", "м", 2.5, 0.0)]
    assert [s["row"] for s in res.skipped] == [3, 5]


def test_parse_paste_quoted_excel_cells():
    res = o_ops.parse_paste('"A-1"\t"Ручка ""мини"""\tшт\t1\t5')
    assert res.rows[0].code == "A-1" and res.rows[0].name == 'Ручка "мини"'
