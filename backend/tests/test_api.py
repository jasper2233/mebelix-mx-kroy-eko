"""API testlari: loyihalar, papkalar, tarix, mahsulotlar, operatsiyalar, detallar, kroy, variantlar,
qoldiqlar ombori, hisobot, etiketka, postprotsessor, sozlamalar, katalog, import."""
import io
import json

from openpyxl import Workbook


def _op(p, oid):
    return next(o for o in p["operations"] if o["id"] == oid)


# ───────────────────────── papkalar va loyihalar ─────────────────────────
def test_folders_projects_move_copy_delete(client):
    f1 = client.post("/api/folders", json={"name": "2026"}).json()
    f2 = client.post("/api/folders", json={"name": "Sentyabr", "parent_id": f1["id"]}).json()
    assert [x["id"] for x in client.get(f"/api/folders?parent_id={f1['id']}").json()] == [f2["id"]]
    assert [x["name"] for x in client.get(f"/api/folders/{f2['id']}/path").json()] == ["2026", "Sentyabr"]
    # o'z ichiga ko'chirish taqiqlangan
    assert client.patch(f"/api/folders/{f1['id']}", json={"parent_id": f2["id"]}).status_code == 400
    assert client.patch(f"/api/folders/{f2['id']}", json={"name": "Oktyabr"}).json()["parent_id"] == f1["id"]
    p = client.post("/api/projects", json={"name": "Shkaf", "folder_id": f2["id"], "customer": "Aziz"}).json()
    assert p["owner"] == "admin" and p["currency"] == "UZS" and p["number"] > 1000000
    lst = client.get(f"/api/projects?folder_id={f2['id']}").json()
    assert [x["name"] for x in lst] == ["Shkaf"] and lst[0]["customer"] == "Aziz"
    assert client.get("/api/projects?q=Aziz").json()[0]["id"] == p["id"]          # qidiruv — barcha papkalar
    assert client.get(f"/api/projects?q={p['number']}").json()[0]["id"] == p["id"]
    assert client.post("/api/projects/move", json={"ids": [p["id"]], "folder_id": None}).status_code == 200
    assert client.get(f"/api/projects/{p['id']}").json()["folder_id"] is None
    cp = client.post(f"/api/projects/{p['id']}/copy").json()
    assert cp["id"] != p["id"] and cp["number"] != p["number"] and cp["name"].startswith("Shkaf")
    assert client.delete(f"/api/folders/{f1['id']}").status_code == 409        # bo'sh emas
    assert client.delete(f"/api/folders/{f1['id']}?recursive=true").json()["ok"]
    assert client.delete(f"/api/projects/{cp['id']}").json()["ok"]
    assert client.get(f"/api/projects/{cp['id']}").status_code == 404


def test_header_status_history_undo_redo(client):
    p = client.post("/api/projects", json={"name": "A"}).json()
    pid = p["id"]
    client.patch(f"/api/projects/{pid}", json={"name": "B", "status": 1, "note": "izoh"})
    p = client.patch(f"/api/projects/{pid}", json={"name": "C"}).json()
    assert p["name"] == "C" and p["status"] == 1 and p["note"] == "izoh"
    h = client.get(f"/api/projects/{pid}/history").json()
    assert h["can_undo"] and not h["can_redo"]
    assert client.post(f"/api/projects/{pid}/undo").json()["name"] == "B"
    assert client.post(f"/api/projects/{pid}/undo").json()["name"] == "A"
    assert client.get(f"/api/projects/{pid}/history").json()["can_redo"]
    assert client.post(f"/api/projects/{pid}/redo").json()["name"] == "B"
    # yangi o'zgarish redo zanjirini kesadi
    client.patch(f"/api/projects/{pid}", json={"name": "D"})
    assert client.post(f"/api/projects/{pid}/redo").status_code == 400
    # folder_id ni null qilib yuborish mumkin
    assert client.patch(f"/api/projects/{pid}", json={"folder_id": None}).json()["folder_id"] is None


def test_export_import_roundtrip(client, kravat):
    pid, cs, el = kravat
    data = client.get(f"/api/projects/{pid}/export").content
    r = client.post("/api/projects/import-file", files={"file": ("x.mxk.json", data, "application/json")}).json()
    p2 = r["project"]
    assert p2["id"] != pid and len(_op(p2, cs)["parts"]) == 14 and r["warnings"] == []
    assert client.post("/api/projects/import", files={"file": ("x.json", b"{bad", "application/json")}).status_code == 400
    fm = client.get("/api/import/formats").json()
    assert any(f["ext"] == ".project" for f in fm)


# ───────────────────────── mahsulotlar ─────────────────────────
def test_products_qty_clone_move_sort(client, kravat):
    pid, cs, el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    prid = p["products"][0]["id"]
    p = client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": 2, "code": "K1"}).json()
    assert p["products"][0]["qty"] == 2
    p = client.post(f"/api/projects/{pid}/products/{prid}/clone").json()
    assert len(p["products"]) == 2
    clone_id = p["products"][1]["id"]
    assert sum(1 for pt in _op(p, cs)["parts"] if pt["product_id"] == clone_id) == 14
    p = client.post(f"/api/projects/{pid}/products/{clone_id}/move?direction=up").json()
    assert p["products"][0]["id"] == clone_id
    p = client.post(f"/api/projects/{pid}/products/sort?by=name").json()
    assert p["products"][0]["name"] == "Изделие 1"
    p = client.post(f"/api/projects/{pid}/products", json={"name": "Yangi"}, params={"position": 0}).json()
    assert p["products"][0]["name"] == "Yangi"
    p = client.post(f"/api/projects/{pid}/products/zero-qty").json()
    assert all(x["qty"] == 0 for x in p["products"])
    p = client.delete(f"/api/projects/{pid}/products/{clone_id}").json()
    assert all(pt["product_id"] != clone_id for pt in _op(p, cs)["parts"])


# ───────────────────────── operatsiyalar ─────────────────────────
def test_operations_patch_sort_merge_split(client, kravat):
    pid, cs, el = kravat
    p = client.patch(f"/api/projects/{pid}/operations/{cs}", json={"name": "LDSP OQ", "cs_cut": {"kerf": 4}}).json()
    o = _op(p, cs)
    assert o["name"] == "LDSP OQ" and o["cs_cut"]["kerf"] == 4 and o["cs_cut"]["trim_length"] == 2
    assert len(o["parts"]) == 14
    # narx o'zgarishi kroyni o'chirmaydi, kesish parametri esa o'chiradi
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    p = client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_material": {"price": 500000}}).json()
    assert _op(p, cs)["result"] is not None and _op(p, cs)["cost_material"] == 1000000
    p = client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": {"kerf": 3}}).json()
    assert _op(p, cs)["result"] is None
    # ikkinchi CS (boshqa material) va ikkinchi kromka
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "name": "MDF"}).json()
    cs2 = p["operations"][-1]["id"]
    p = client.post(f"/api/projects/{pid}/operations/{cs2}/parts",
                    json=[{"name": "Fasad", "length": 700, "width": 400, "edge_top": {"op_id": el}}]).json()
    assert p["operations"][-1]["parts"][0]["uid"] == 15
    # kromkani materiallar bo'yicha ajratish
    p = client.post(f"/api/projects/{pid}/actions/split-edges").json()
    els = [o for o in p["operations"] if o["type"] == "EL"]
    assert len(els) == 2 and els[1]["name"].endswith("(MDF)")
    assert _op(p, cs2)["parts"][0]["edge_top"]["op_id"] == els[1]["id"]
    # bir xil operatsiyalarni birlashtirish (kromka havolalari qayta bog'lanadi)
    client.patch(f"/api/projects/{pid}/operations/{els[1]['id']}", json={"name": els[0]["name"]})
    p = client.post(f"/api/projects/{pid}/actions/merge-same").json()
    els = [o for o in p["operations"] if o["type"] == "EL"]
    assert len(els) == 1 and _op(p, cs2)["parts"][0]["edge_top"]["op_id"] == els[0]["id"]
    p = client.post(f"/api/projects/{pid}/operations/sort?by=type").json()
    assert [o["type"] for o in p["operations"]] == ["CS", "CS", "EL"]
    p = client.post(f"/api/projects/{pid}/operations/{cs2}/clone").json()
    assert len([o for o in p["operations"] if o["type"] == "CS"]) == 3
    p = client.delete(f"/api/projects/{pid}/operations/{el}").json()
    assert all(pt["edge_top"]["op_id"] is None for o in p["operations"] for pt in o["parts"])


def test_new_operation_uses_saved_defaults_and_catalog(client):
    client.put("/api/settings/cs_defaults/default", json={"material": {"thickness": 18}, "cut": {"kerf": 4.4}})
    client.post("/api/catalog/sync", json=[{"id": "m1", "kind": "sheet", "code": "LDSP-18-W", "name": "LDSP 18 Oq",
                                             "price": 450000, "thickness": 18, "length": 2800, "width": 2070,
                                             "params": {"trim_length": 10}}])
    p = client.post("/api/projects", json={"name": "Defaults"}).json()
    p = client.post(f"/api/projects/{p['id']}/operations", json={"type": "CS", "material_id": "m1"}).json()
    o = p["operations"][-1]
    assert o["name"] == "LDSP 18 Oq" and o["code"] == "LDSP-18-W"
    assert o["cs_cut"]["kerf"] == 4.4 and o["cs_cut"]["trim_length"] == 10
    assert o["cs_material"]["price"] == 450000 and o["sheets"][0]["length"] == 2800
    client.put("/api/settings/cs_defaults/default", json={})          # standartga qaytarish
    assert client.get("/api/settings/cs_defaults/default").json()["cut"]["kerf"] == 3


# ───────────────────────── detallar ─────────────────────────
def test_parts_patch_clone_move_sort_bulk(client, kravat):
    pid, cs, el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    parts = _op(p, cs)["parts"]
    a, b = parts[0]["id"], parts[1]["id"]
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    # nom o'zgarishi kroyni saqlaydi, o'lcham o'zgarishi o'chiradi
    p = client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{a}", json={"name": "Yon devor"}).json()
    assert _op(p, cs)["result"] is not None and _op(p, cs)["parts"][0]["name"] == "Yon devor"
    p = client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{a}", json={"length": 750}).json()
    assert _op(p, cs)["result"] is None
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/clone", json={"ids": [a]}).json()
    ps = _op(p, cs)["parts"]
    assert len(ps) == 15 and ps[1]["name"] == "Yon devor" and ps[1]["uid"] == 15
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/move?direction=down", json={"ids": [a]}).json()
    assert _op(p, cs)["parts"][1]["id"] == a
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/sort?by=area&desc=true").json()
    ps = _op(p, cs)["parts"]
    assert ps[0]["length"] * ps[0]["width"] >= ps[-1]["length"] * ps[-1]["width"]
    ids = [x["id"] for x in ps][::-1]
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/reorder", json={"ids": ids}).json()
    assert [x["id"] for x in _op(p, cs)["parts"]] == ids
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/bulk/swap", json={"ids": [b]}).json()
    pb = next(x for x in _op(p, cs)["parts"] if x["id"] == b)
    assert (pb["length"], pb["width"]) == (1468, 200)
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/group-update",
                    json={"ids": [a, b], "fields": {"grain": True, "qty": 3}}).json()
    assert all(x["grain"] and x["qty"] == 3 for x in _op(p, cs)["parts"] if x["id"] in (a, b))
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts", params={"position": 0},
                    json=[{"name": "Birinchi", "length": 300, "width": 200}]).json()
    assert _op(p, cs)["parts"][0]["name"] == "Birinchi"
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/delete", json={"ids": [a]}).json()
    assert all(x["id"] != a for x in _op(p, cs)["parts"])


def test_parts_excel_import_and_preview(client, kravat):
    pid, cs, el = kravat
    wb = Workbook()
    ws = wb.active
    ws.append(["Nomi", "Uzunlik", "En", "Soni", "Tekstura", "Kromka"])
    ws.append(["Polka", 764, 300, 4, "да", "KP-1/19"])
    ws.append(["Stenka", "1200,5", 500, 2, "", ""])
    buf = io.BytesIO(); wb.save(buf)
    data = buf.getvalue()
    pv = client.post("/api/import/preview", files={"file": ("d.xlsx", data)}, data={"sheet": 0}).json()
    assert pv["columns"][:3] == ["A", "B", "C"] and pv["rows"][1][0] == "Polka"
    cmap = {"name": "A", "length": "B", "width": "C", "qty": "D", "grain": "E", "edge_top": "F"}
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/import", files={"file": ("d.xlsx", data)},
                    data={"col_map": json.dumps(cmap), "sheet": 0, "start_row": 2}).json()
    ps = _op(p, cs)["parts"]
    assert ps[-2]["name"] == "Polka" and ps[-2]["grain"] and ps[-2]["edge_top"]["op_id"] == el
    assert ps[-1]["length"] == 1200.5 and ps[-1]["qty"] == 2


# ───────────────────────── kroy ─────────────────────────
def test_optimize_quality_variants_and_result_put(client, kravat):
    pid, cs, el = kravat
    res = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").json()
    assert res["total_sheets"] == 2 and not res["unplaced"] and res["maps"][0]["strips"]
    vs = client.post(f"/api/projects/{pid}/operations/{cs}/variants").json()
    assert [v["variant"] for v in vs] == ["optimal", "length", "width"]
    assert all(v["unplaced"] == 0 for v in vs)
    pick = vs[2]["result"]
    p = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=pick).json()
    o = _op(p, cs)
    assert o["result"]["variant"] == "width" and all(pt["left_qty"] == 0 for pt in o["parts"])
    # buzilgan natija rad etiladi
    bad = json.loads(json.dumps(pick))
    pl = bad["maps"][0]["placements"]
    pl[1]["x"], pl[1]["y"] = pl[0]["x"], pl[0]["y"]
    bad["maps"][0]["strips"] = []
    r = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=bad)
    assert r.status_code == 422 and r.json()["details"]


def test_optimize_only_remaining(client, kravat):
    pid, cs, el = kravat
    client.put(f"/api/projects/{pid}/operations/{cs}/sheets", json=[{"length": 2750, "width": 1830, "qty": 1}])
    res = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").json()
    assert res["total_sheets"] == 1 and res["unplaced"]
    first_map = res["maps"][0]
    # yangi list qo'shish ishlatilgan listni o'zgartirmaydi — natija saqlanadi
    sheets = _op(client.get(f"/api/projects/{pid}").json(), cs)["sheets"]
    sheets.append({"length": 2800, "width": 2070, "qty": 5})
    p = client.put(f"/api/projects/{pid}/operations/{cs}/sheets", json=sheets).json()
    assert _op(p, cs)["result"] is not None and _op(p, cs)["sheets"][0]["used_qty"] == 1
    res = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?only_remaining=true").json()
    assert not res["unplaced"] and res["total_parts"] == 19 and res["total_sheets"] == 2
    assert res["maps"][0]["placements"] == first_map["placements"]      # birinchi karta o'zgarmadi
    assert res["maps"][1]["sheet_length"] == 2800
    # ishlatilgan list o'lchami o'zgarsa — natija eskiradi
    sheets = _op(client.get(f"/api/projects/{pid}").json(), cs)["sheets"]
    sheets[0]["width"] = 1800
    p = client.put(f"/api/projects/{pid}/operations/{cs}/sheets", json=sheets).json()
    assert _op(p, cs)["result"] is None


def test_map_comment_done_and_svg(client, kravat):
    pid, cs, el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    p = client.patch(f"/api/projects/{pid}/operations/{cs}/maps/1", json={"comment": "Ehtiyot bo'ling"}).json()
    assert _op(p, cs)["result"]["maps"][0]["comment"] == "Ehtiyot bo'ling"
    p = client.patch(f"/api/projects/{pid}/operations/{cs}/maps/1", json={"done_count": 5}).json()
    assert _op(p, cs)["result"]["maps"][0]["done_count"] == 1          # nusxalar sonidan oshmaydi
    svg = client.get(f"/api/projects/{pid}/operations/{cs}/maps/1.svg?width=600&label=number")
    assert svg.status_code == 200 and "<svg" in svg.text
    assert client.get(f"/api/projects/{pid}/operations/{cs}/maps/9.svg").status_code == 404


# ───────────────────────── qoldiqlar ombori ─────────────────────────
def test_remnants_commit_use_rollback(client, kravat):
    pid, cs, el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    info = client.get(f"/api/projects/{pid}/operations/{cs}/remnants").json()
    assert info["remnants"] and not info["saved"] and info["material_code"] == "LDSP16"
    out = client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").json()
    assert out["added"] and out["project"]["operations"][1]["result"]["remnants_saved"]
    assert client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").status_code == 400
    rid = out["added"][0]["id"]
    stock = client.get("/api/remnants?material_code=LDSP16").json()
    assert any(r["id"] == rid for r in stock)
    # boshqa loyihada shu qoldiqdan foydalanish
    p2 = client.post("/api/projects", json={"name": "Qoldiqdan"}).json()
    p2 = client.post(f"/api/projects/{p2['id']}/operations", json={"type": "CS", "code": "LDSP16", "name": "LDSP"}).json()
    cs2 = p2["operations"][-1]["id"]
    client.post(f"/api/projects/{p2['id']}/operations/{cs2}/parts", json=[{"name": "Kichik", "length": 400, "width": 300}])
    p2 = client.post(f"/api/projects/{p2['id']}/operations/{cs2}/sheets/from-remnants", json={"ids": [rid]}).json()
    sh = _op(p2, cs2)["sheets"][0]
    assert sh["is_remnant"] and sh["source_remnant_id"] == rid
    res = client.post(f"/api/projects/{p2['id']}/operations/{cs2}/optimize?quality=fast").json()
    assert res["maps"][0]["sheet_id"] == sh["id"] and res["maps"][0]["is_remnant"]
    qty0 = next(r for r in client.get("/api/remnants").json() if r["id"] == rid)["qty"]
    client.post(f"/api/projects/{p2['id']}/operations/{cs2}/remnants/commit")
    left = [r for r in client.get("/api/remnants?include_empty=true").json() if r["id"] == rid][0]["qty"]
    assert left == qty0 - 1
    # talabnoma: ombor qoldig'i yangi list sifatida emas, alohida qatorda (№ bilan)
    wr = [r for r in client.get(f"/api/projects/{p2['id']}/warehouse").json() if r["type"] == "CS"]
    assert wr[0]["qty"] == 0 and wr[1]["remnant"] and wr[1]["remnant_id"] == rid and wr[1]["qty"] == 1
    # birinchi loyiha kroyi o'chirilsa — ishlatilmagan qoldiqlari ombordan olib tashlanadi; boshqa loyiha ishlatgan
    # qoldiqning birinchi loyihaga tegishli qismi ham bekor bo'ladi (QA №6: egasiz «arvoh» qoldiq qolmasin),
    # keyin o'sha loyiha bekor qilsa — qoldiq qayta paydo bo'lmaydi (bekor qilish tartibi natijaga ta'sir qilmaydi)
    others = [a["id"] for a in out["added"] if a["id"] != rid]
    client.delete(f"/api/projects/{pid}/operations/{cs}/result")
    rows = {r["id"]: r for r in client.get("/api/remnants?include_empty=true").json()}
    assert all(o not in rows for o in others)
    assert rid not in rows and all(r["id"] != rid for r in client.get("/api/remnants").json())
    client.post(f"/api/projects/{p2['id']}/operations/{cs2}/remnants/rollback")
    assert all(r["id"] != rid for r in client.get("/api/remnants?include_empty=true").json())
    # omborda yo'q — commit 409 (qoldiqning egasi bekor qilgan)
    r409 = client.post(f"/api/projects/{p2['id']}/operations/{cs2}/remnants/commit")
    assert r409.status_code == 409 and f"№{rid}" in r409.json()["detail"]
    r = client.post("/api/remnants", json={"material_code": "MDF", "length": 1200, "width": 600, "qty": 2}).json()
    assert client.patch(f"/api/remnants/{r['id']}", json={"qty": 1}).json()["qty"] == 1
    assert client.patch(f"/api/remnants/{r['id']}", json={"length": -5}).status_code == 422
    assert client.patch(f"/api/remnants/{r['id']}", json={"length": 0}).status_code == 400
    for bad in ('{"qty": 1e30}', '{"qty": 1000000000000000000000000000000}', '{"length": Infinity}',
                '{"width": NaN}'):
        rr = client.patch(f"/api/remnants/{r['id']}", content=bad, headers={"Content-Type": "application/json"})
        assert rr.status_code == 422, (bad, rr.status_code)
    assert client.get("/api/remnants").status_code == 200
    assert client.patch(f"/api/remnants/{r['id']}", json={"qty": "ko'p"}).status_code == 422
    assert client.delete(f"/api/remnants/{r['id']}").json()["ok"]


# ───────────────────────── hisobot, etiketka, postprotsessor ─────────────────────────
def test_report_labels_postprocessors(client, kravat):
    pid, cs, el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    html = client.get(f"/api/projects/{pid}/report").text
    assert "Требование на склад" in html and "MebeliX Kroy" in html and "<svg" in html
    assert "GibLab" not in html
    prof = client.post("/api/settings/print", json={"name": "Faqat talabnoma",
                                                    "data": {"operations": False, "materials_list": True,
                                                             "products_list": True, "products_list_single": True}}).json()
    html = client.get(f"/api/projects/{pid}/report?profile_id={prof['id']}").text
    assert "Материалы" in html and "Изделия" in html and "(CS)" not in html
    html = client.post(f"/api/projects/{pid}/report?lang=uz", json={"cs_commands": True}).text
    assert "Omborga talabnoma" in html
    lb = client.get(f"/api/projects/{pid}/labels").text
    assert lb.count('class="lbl"') == 19 and "MXK:" not in lb       # QR rasm, matn emas
    lst = client.get("/api/postprocessors").json()
    assert {"csv", "commands", "dxf", "json"} <= {x["key"] for x in lst}
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=csv")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    assert r.content.decode("utf-8-sig").count("\n") == 20            # sarlavha + 19 detal
    assert client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=dxf").text.endswith("EOF\n")
    j = json.loads(client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=json").content)
    assert len(j["maps"]) >= 1 and j["maps"][0]["commands"]
    # foydalanuvchi shabloni (namuna profil — birinchi ishga tushishda yaratiladi)
    user_pp = [x for x in lst if not x["builtin"]]
    assert user_pp
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?profile_id={user_pp[0]['profile_id']}")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    tpl = {"name": "T", "template": "{% for m in maps %}S;{{ f(m.sheet_length) }};{{ m.copies }}\n{% endfor %}",
           "per_map": False, "extension": "txt"}
    pv = client.post("/api/postprocessors/preview", json={"project_id": pid, "op_id": cs, "profile": tpl}).json()
    assert pv["ok"] and pv["text"].startswith("S;2750;")
    bad = dict(tpl, template="{{ map.__class__.__mro__ }}")
    pv = client.post("/api/postprocessors/preview", json={"project_id": pid, "op_id": cs, "profile": bad}).json()
    assert not pv["ok"] or "class" not in pv.get("text", "")          # sandbox


# ───────────────────────── sozlamalar ─────────────────────────
def test_settings_profiles_crud(client):
    assert client.get("/api/settings/nope").status_code == 404
    pr = client.post("/api/settings/labels", json={"name": "Termo 58x40", "data": {"columns": 0}}).json()
    assert pr["data"]["columns"] == 0 and pr["data"]["width_mm"] == 58
    assert client.put(f"/api/settings/labels/{pr['id']}", json={"is_default": True}).json()["is_default"]
    assert client.get("/api/settings/labels/default").json()["columns"] == 0
    assert client.post("/api/settings/labels", json={"name": "X", "data": {"columns": "abc"}}).status_code == 400
    assert client.delete(f"/api/settings/labels/{pr['id']}").json()["ok"]
    assert client.get("/api/settings/labels/default").json()["columns"] == 3
    cols = client.post("/api/settings/part_columns", json={"name": "Uslugiya",
                                                           "data": {"columns": [{"key": "name", "visible": True}]}}).json()
    assert cols["data"]["columns"][0]["key"] == "name"
    assert client.get("/api/settings/app/default").json()["language"] == "ru"


# ───────────────────────── katalog ─────────────────────────
def test_catalog_sync_import_delete(client):
    client.post("/api/catalog/sync", json=[{"id": "e1", "kind": "edge", "code": "KR-2/19", "name": "Kromka 2/19",
                                             "price": 3500, "params": {"width": 19, "thickness": 2}}])
    assert client.get("/api/catalog?kind=edge&q=2/19").json()[0]["id"] == "e1"
    wb = Workbook(); ws = wb.active
    ws.append(["ID", "Kod", "Nomi", "Narx", "Qalinlik", "Uzunlik", "En"])
    ws.append(["x1", "MDF-16", "MDF 16 oq", "380 000", 16, 2800, 2070])
    buf = io.BytesIO(); wb.save(buf)
    r = client.post("/api/catalog/import", files={"file": ("c.xlsx", buf.getvalue())},
                    data={"col_map": json.dumps({"id": "A", "code": "B", "name": "C", "price": "D", "thickness": "E",
                                                 "length": "F", "width": "G"}), "kind": "sheet"}).json()
    assert r["count"] == 1
    it = client.get("/api/catalog?q=MDF-16").json()[0]
    assert it["price"] == 380000 and it["length"] == 2800 and it["kind"] == "sheet"
    p = client.post("/api/projects", json={"name": "Kat"}).json()
    p = client.post(f"/api/projects/{p['id']}/operations", json={"type": "EL", "material_id": "e1"}).json()
    el = p["operations"][-1]["el"]
    assert el["price"] == 3500 and el["thickness"] == 2 and el["width"] == 19
    assert client.delete("/api/catalog/x1").json()["ok"]
    assert client.delete("/api/catalog/x1").status_code == 404


# ───────────────────────── XNC ─────────────────────────
def test_xnc_for_part_stats_and_drawing(client, kravat):
    pid, cs, el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    part = _op(p, cs)["parts"][0]
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/{part['id']}/xnc").json()
    x = p["operations"][-1]
    assert x["type"] == "XNC" and x["xnc_part_id"] == part["id"] and x["xnc"]["length"] == 748
    x["xnc"]["program"] = [{"cmd": "Tool", "params": {"N": "Bore8", "D": 8}},
                           {"cmd": "DrillFront", "params": {"X": 50, "Y": 32, "DP": 12, "T": "Bore8"}},
                           {"cmd": "DrillFront", "params": {"X": "dx-50", "Y": 32, "DP": "dz", "T": "Bore8"}},
                           {"cmd": "DrillFront", "params": {"X": 5000, "Y": 32, "DP": 12}}]     # detal tashqarisida
    x["xnc"]["drill_price"] = 1000
    client.put(f"/api/projects/{pid}/operations/{x['id']}", json=x)
    st = client.get(f"/api/projects/{pid}/operations/{x['id']}/xnc-stats").json()
    assert st["drills"] == 2 and st["cost"] == 2000
    assert "<circle" in client.get(f"/api/projects/{pid}/operations/{x['id']}/xnc.svg").text
    p = client.get(f"/api/projects/{pid}").json()
    assert _op(p, cs)["parts"][0]["xnc_op_ids"] == [x["id"]]
    html = client.get(f"/api/projects/{pid}/report").text
    assert "(XNC)" in html


def test_batch_update_size_mode_and_label_preview(client, kravat):
    pid, cs, el = kravat
    client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {"thickness": 1, "jointing_width": 1}})
    p = client.get(f"/api/projects/{pid}").json()
    parts = _op(p, cs)["parts"]
    p6 = parts[5]                                       # 480×800, ОВ+ОН kromka
    r = client.post(f"/api/projects/{pid}/operations/{cs}/parts/batch-update",
                    json=[{"id": parts[0]["id"], "fields": {"name": "Yon"}}, {"id": parts[1]["id"], "fields": {"qty": 5}}]).json()
    ps = _op(r, cs)["parts"]
    assert ps[0]["name"] == "Yon" and ps[1]["qty"] == 5
    # rejim: detal → zagotovka; jismoniy o'lcham saqlanadi (en: 800 − 2×1 + 2×1 = 800; uzunlik o'zgarmaydi)
    p = client.patch(f"/api/projects/{pid}", json={"size_mode": "jointed"}).json()
    q6 = next(x for x in _op(p, cs)["parts"] if x["id"] == p6["id"])
    assert (q6["length"], q6["width"]) == (480, 798)
    p = client.patch(f"/api/projects/{pid}", json={"size_mode": "detail"}).json()
    q6 = next(x for x in _op(p, cs)["parts"] if x["id"] == p6["id"])
    assert (q6["length"], q6["width"]) == (480, 800)
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    html = client.post(f"/api/projects/{pid}/labels?lang=uz", json={"width_mm": 70, "height_mm": 50, "columns": 0,
                                                                   "qr": False, "show_edges": True, "show_product": True,
                                                                   "show_map": True}).text
    assert "size: 70" in html and "karta" in html and "<svg" in html
