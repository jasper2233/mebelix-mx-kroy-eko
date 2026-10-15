"""GibLab bilan solishtirishdan kelib chiqqan qo'shimchalar: mahsulot «Свойства», ko'p kalitli «Сортировка»,
.project importida mahsulot atributlari, optimizatorda ko'p-listli (qoldiq + butun list) kroy."""
from app.models import OpType, StockSheet, CSCutParams, CSMaterialParams
from app.plugins.legacy_project import import_project
from app.services import optimizer as O


def test_product_props_roundtrip(client):
    p = client.post("/api/projects", json={"name": "Xossalar"}).json()
    pid, prid = p["id"], p["products"][0]["id"]
    body = dict(name="Shkaf", code="123", order_info="1230 Jamshid", ready_date="2026-10-05", phone1="+998901112233",
                extra={"product.import": "bm.1.86"}, description="Fasad: oq")
    p = client.patch(f"/api/projects/{pid}/products/{prid}", json=body).json()
    pr = p["products"][0]
    assert (pr["name"], pr["order_info"], pr["phone1"], pr["extra"]) == ("Shkaf", "1230 Jamshid", "+998901112233", {"product.import": "bm.1.86"})
    assert pr["description"] == "Fasad: oq" and pr["messages"] == []
    # eski JSON (yangi maydonlarsiz) ham o'qiladi
    assert client.post(f"/api/projects/{pid}/products/{prid}/clone").json()["products"][1]["extra"] == {"product.import": "bm.1.86"}


def test_import_product_attributes():
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<project name="t">
  <good id="1" typeId="product" name="Shkaf" code="9" count="1" product.import="bm.1.86" product.order="1230 Jamshid" costMaterial="0">
    <part id="100" l="500" w="300" count="1" name="Yon"/>
  </good>
</project>"""
    p, _w = import_project(xml, "t.project")
    pr = p.products[0]
    assert pr.order_info == "1230 Jamshid" and pr.extra == {"product.import": "bm.1.86"}


def test_multikey_sort_products_ops_parts(client, kravat):
    pid, cs, el = kravat
    for n, q in (("B", 2), ("A", 2), ("C", 1)):
        client.post(f"/api/projects/{pid}/products", json={"name": n, "qty": q})
    names = lambda p: [x["name"] for x in p["products"]]               # noqa: E731
    p = client.post(f"/api/projects/{pid}/products/sort", json=[{"by": "qty", "desc": True}, {"by": "name"}]).json()
    got = [(x["qty"], x["name"]) for x in p["products"] if x["name"] in "ABC"]
    assert got == [(2, "A"), (2, "B"), (1, "C")]
    # eski so'rov shakli (query) ishlashda qoladi
    nm = names(client.post(f"/api/projects/{pid}/products/sort?by=name&desc=true").json())
    assert nm == sorted(nm, key=str.lower, reverse=True)
    assert client.post(f"/api/projects/{pid}/products/sort", json=[{"by": "nope"}]).status_code == 400
    # operatsiyalar: avval tur, keyin nom
    p = client.post(f"/api/projects/{pid}/operations/sort", json=[{"by": "type"}, {"by": "name", "desc": True}]).json()
    assert [o["type"] for o in p["operations"]] == ["CS", "EL"]
    # detallar: uzunlik kamayish, keyin nom
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/sort",
                    json=[{"by": "length", "desc": True}, {"by": "name"}]).json()
    parts = next(o for o in p["operations"] if o["id"] == cs)["parts"]
    lens = [x["length"] for x in parts]
    assert lens == sorted(lens, reverse=True)
    assert client.post(f"/api/projects/{pid}/operations/{cs}/parts/sort?by=area&desc=true").status_code == 200


def test_sort_endpoints_accept_empty_object_body(client, kravat):
    """Mijoz tanasiz so'rovga `{}` yuboradi (api/client.ts) — eski `?by=&desc=` shakli 422 bermasligi kerak."""
    pid, cs, el = kravat
    for url in (f"/api/projects/{pid}/products/sort?by=name", f"/api/projects/{pid}/operations/sort?by=type",
                f"/api/projects/{pid}/operations/{cs}/parts/sort?by=length&desc=true"):
        assert client.post(url, json={}).status_code == 200, url
    p = client.get(f"/api/projects/{pid}").json()
    lens = [x["length"] for x in next(o for o in p["operations"] if o["id"] == cs)["parts"]]
    assert lens == sorted(lens, reverse=True)
    assert client.post(f"/api/projects/{pid}/products/sort", json={"x": 1}).status_code == 400


def test_recode_xnc_and_optimize_ops(client):
    p = client.post("/api/projects", json={"name": "Xnc kodlar"}).json()
    pid = p["id"]
    for code in ("A_1", "A_1", "A_1", "A_1-2"):
        client.post(f"/api/projects/{pid}/operations", json={"type": "XNC", "code": code, "name": "x"})
    p = client.post(f"/api/projects/{pid}/actions/recode-xnc").json()
    codes = [o["code"] for o in p["operations"] if o["type"] == "XNC"]
    assert len(set(codes)) == 4 and codes[0] == "A_1" and codes[3] == "A_1-2"   # mavjud «A_1-2» ga to'qnashmaydi
    assert client.post(f"/api/projects/{pid}/actions/recode-xnc").json() == p      # takror chaqiruv hech narsani o'zgartirmaydi
    # «Оптимизировать операции» (sort_operations ni ichkaridan chaqiradi) buzilmagan
    assert client.post(f"/api/projects/{pid}/actions/optimize-ops").status_code == 200


def test_excel_import_profiles(client):
    data = {"map": {"name": "A", "length": "B", "width": "C", "qty": "D"}, "start": 3}
    pr = client.post("/api/settings/excel_import", json={"name": "Bazis", "data": data}).json()
    assert pr["scope"] == "excel_import" and pr["data"] == data
    assert [x["name"] for x in client.get("/api/settings/excel_import").json()] == ["Bazis"]
    assert client.put(f"/api/settings/excel_import/{pr['id']}", json={"name": "Bazis 2"}).json()["name"] == "Bazis 2"
    assert client.post("/api/settings/excel_import", json={"name": "x", "data": [1]}).status_code in (400, 422)
    assert client.delete(f"/api/settings/excel_import/{pr['id']}").status_code == 200
    assert client.get("/api/settings/excel_import").json() == []


def _items(parts):
    items = []
    for i, (l, w, q) in enumerate(parts):
        items += [O.Item(f"p{i}", i + 1, l, w, True) for _ in range(q)]
    return items


def test_optimizer_prefers_limited_sheets_and_less_material():
    """Qoldiq list (qty=1) birinchi ishlatiladi, ortiqcha butun list olinmaydi (GibLab kabi: 1230 Jamshid 04 shkaf)."""
    parts = [(1845, 299, 2), (150, 800, 1), (1945, 100, 2), (100, 600, 1)]       # 1.672 m²
    cut = CSCutParams(quality="fast", stock_order="economy")     # «Экономия материала»: tartib sinaladi (standart — qat'iy ro'yxat, 2026-10-15)
    stock = [StockSheet(id="a", length=2140, width=1140, qty=1), StockSheet(id="b", length=2750, width=1830, qty=10000)]
    res = O.optimize(_items(parts), stock, cut, CSMaterialParams())
    assert not res.unplaced and res.total_sheets == 1
    assert (res.maps[0].sheet_length, res.maps[0].sheet_width) == (2140, 1140)
    assert abs(res.total_fill_percent - 68.55) < 0.05            # GibLab: F 68.55 %
    # tartib teskari berilsa ham — cheklanganlar ro'yxat tartibida; natija to'g'ri va butun list tejaladi
    res2 = O.optimize(_items(parts), stock[::-1], cut, CSMaterialParams())
    assert not res2.unplaced and res2.material_area_m2 <= 2.45 + 1e-6


def test_optimizer_uses_leftover_to_save_whole_sheet():
    """Butun list o'rniga qoldiq listga joylash (material maydoni kamayadi)."""
    parts = [(2700, 1000, 1), (1200, 1000, 1), (1500, 800, 2)]
    cut = CSCutParams(quality="fast", stock_order="economy")     # «Экономия материала» rejimi xususiyati
    only_new = [StockSheet(id="b", length=2750, width=1830, qty=10000)]
    mixed = [StockSheet(id="r", length=2750, width=1000, qty=1), StockSheet(id="r2", length=1500, width=900, qty=2),
             StockSheet(id="b", length=2750, width=1830, qty=10000)]
    a = O.optimize(_items(parts), only_new, cut, CSMaterialParams())
    b = O.optimize(_items(parts), mixed, cut, CSMaterialParams())
    assert not b.unplaced and b.material_area_m2 <= a.material_area_m2 + 1e-6
