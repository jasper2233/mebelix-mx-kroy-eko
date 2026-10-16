"""2026-10-15 — onlayn solishtiruv va ko'p-kroyli audit tuzatishlari (docs/mebelix/X_1015_ONLAYN_AUDIT_MCP.md):
«Раскроить все операции», «Объединить» kaliti (qalinlik, list o'lchami) va listlarni birlashtirish, «Разделить кромку» belgilari,
listlar ro'yxati tekshiruvlari (dublikat id, yo'q qoldiq, otstup eskirtiradi, izoh 500), ombordan qoldiq qalinligi (`force`),
katalog `sync` qisman yangilash va tekshiruv, listdan katta detal ogohlantirishi, «Порядок листов»."""


def _mk(client, name="X"):
    return client.post("/api/projects", json={"name": name}).json()["id"]


def _cs(client, pid, code="LDSP16", name="LDSP", parts=None, thickness=None):
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": code, "name": name}).json()
    oid = p["operations"][-1]["id"]
    if thickness is not None:
        client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cs_material": {"thickness": thickness}})
    if parts:
        client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=parts)
    return oid


def _op(p, oid):
    return next(o for o in p["operations"] if o["id"] == oid)


def test_optimize_all_cuts_every_cut_op_in_one_history_step(client):
    pid = _mk(client, "Hammasi")
    a = _cs(client, pid, "A", "A", [{"name": "p", "length": 600, "width": 400, "qty": 3}])
    b = _cs(client, pid, "B", "B", [{"name": "p", "length": 500, "width": 300, "qty": 2}])
    c = _cs(client, pid, "C", "C")                       # detalsiz — xabar, qolganlar to'xtamaydi
    r = client.post(f"/api/projects/{pid}/actions/optimize-all?quality=fast")
    assert r.status_code == 200, r.text
    d = r.json()
    res = {x["op_id"]: x for x in d["results"]}
    assert res[a]["sheets"] == 1 and res[b]["sheets"] == 1
    assert res[c]["skipped"] is True and res[c]["reason"] and "error" not in res[c]     # bo'sh — «пропущено», xato emas (QA #6)
    p = d["project"]
    assert _op(p, a)["result"]["total_sheets"] == 1 and _op(p, b)["result"]["total_sheets"] == 1
    assert "2" in d["message"]
    p = client.post(f"/api/projects/{pid}/undo").json()     # bitta Ctrl+Z — ikkala natija ham qaytadi
    assert _op(p, a)["result"] is None and _op(p, b)["result"] is None
    client.post(f"/api/projects/{pid}/operations/{a}/optimize?quality=fast")
    d = client.post(f"/api/projects/{pid}/actions/optimize-all?quality=fast&skip_done=true").json()
    res = {x["op_id"]: x for x in d["results"]}
    assert res[a].get("skipped") is True and res[b]["sheets"] == 1


def test_merge_same_respects_thickness_and_keeps_sheets(client):
    pid = _mk(client, "Merge")
    a = _cs(client, pid, "devor", "Devor", [{"name": "p", "length": 600, "width": 400}], thickness=100)
    b = _cs(client, pid, "devor", "Devor", [{"name": "q", "length": 600, "width": 400}], thickness=200)
    c = _cs(client, pid, "devor", "Devor", [{"name": "r", "length": 600, "width": 400}], thickness=100)
    client.put(f"/api/projects/{pid}/operations/{c}/sheets",
               json=[{"length": 2750, "width": 1830, "qty": 10000}, {"length": 1500, "width": 900, "qty": 2}])
    p = client.post(f"/api/projects/{pid}/actions/merge-same").json()
    cs = [o for o in p["operations"] if o["type"] == "CS"]
    assert len(cs) == 2                                   # 100 mm (a + c) va 200 mm (b) — qalinligi boshqa birlashmaydi
    merged = next(o for o in cs if o["cs_material"]["thickness"] == 100)
    assert merged["id"] == a and len(merged["parts"]) == 2
    dims = {(s["length"], s["width"], s["qty"]) for s in merged["sheets"]}
    assert (1500.0, 900.0, 2) in dims and (2750.0, 1830.0, 10000) in dims   # yutilgan operatsiyaning listlari yo'qolmadi
    assert _op(p, b)["cs_material"]["thickness"] == 200


def test_split_edges_assigns_new_symbol_and_colour(client):
    pid = _mk(client, "Split")
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "code": "K", "name": "PVC"}).json()
    el = p["operations"][-1]["id"]
    _cs(client, pid, "A", "A", [{"name": "p", "length": 600, "width": 400, "edge_top": {"op_id": el}}])
    _cs(client, pid, "B", "B", [{"name": "q", "length": 600, "width": 400, "edge_top": {"op_id": el}}])
    p = client.post(f"/api/projects/{pid}/actions/split-edges").json()
    els = [o for o in p["operations"] if o["type"] == "EL"]
    assert len(els) == 2
    assert els[0]["el"]["symbol"] != els[1]["el"]["symbol"]
    assert els[0]["el"]["color"] != els[1]["el"]["color"]


def test_set_sheets_validation_and_stale_on_end_offset(client):
    pid = _mk(client, "Sheets")
    a = _cs(client, pid, "A", "A", [{"name": "p", "length": 600, "width": 400, "qty": 2}])
    r = client.put(f"/api/projects/{pid}/operations/{a}/sheets",
                   json=[{"id": "x1", "length": 2750, "width": 1830, "qty": 10000}, {"id": "x1", "length": 2000, "width": 1000, "qty": 1}])
    assert r.status_code == 422
    r = client.put(f"/api/projects/{pid}/operations/{a}/sheets",
                   json=[{"length": 2750, "width": 1830, "qty": 10000, "source_remnant_id": 999999, "is_remnant": True}])
    assert r.status_code == 404
    p = client.put(f"/api/projects/{pid}/operations/{a}/sheets",
                   json=[{"id": "s1", "length": 2750, "width": 1830, "qty": 10000, "description": "x" * 2000}]).json()
    assert len(_op(p, a)["sheets"][0]["description"]) == 500
    client.post(f"/api/projects/{pid}/operations/{a}/optimize?quality=fast")
    p = client.put(f"/api/projects/{pid}/operations/{a}/sheets",
                   json=[{"id": "s1", "length": 2750, "width": 1830, "qty": 10000, "end_offset_bottom": 400}]).json()
    assert _op(p, a)["result"] is None                   # foydali zona o'zgardi — natija eskirdi


def test_from_remnants_rejects_other_thickness_unless_forced(client):
    r = client.post("/api/remnants", json={"material_code": "LDSP16", "material_name": "L", "length": 1200, "width": 800,
                                           "thickness": 18, "qty": 1}).json()
    pid = _mk(client, "Rem")
    a = _cs(client, pid, "LDSP16", "L", [{"name": "p", "length": 300, "width": 200}])     # standart qalinlik 16
    resp = client.post(f"/api/projects/{pid}/operations/{a}/sheets/from-remnants", json={"ids": [r["id"]]})
    assert resp.status_code == 400 and "18" in resp.text
    assert client.post(f"/api/projects/{pid}/operations/{a}/sheets/from-remnants", json={"ids": [999999]}).status_code == 404
    resp = client.post(f"/api/projects/{pid}/operations/{a}/sheets/from-remnants?force=true", json={"ids": [r["id"]]})
    assert resp.status_code == 200
    assert any(s["source_remnant_id"] == r["id"] for s in _op(resp.json(), a)["sheets"])
    client.post(f"/api/projects/{pid}/operations/{a}/optimize?quality=fast")
    out = client.post(f"/api/projects/{pid}/operations/{a}/remnants/commit")
    assert out.status_code == 200, out.text               # boshqa kodli/qalinlikli qoldiq chiqimi 409 bermaydi
    assert out.json()["consumed"] == {str(r["id"]): 1}


def test_copy_project_drops_warehouse_links(client):
    r = client.post("/api/remnants", json={"material_code": "LDSP16", "material_name": "L", "length": 1200, "width": 800,
                                           "thickness": 16, "qty": 1}).json()
    pid = _mk(client, "Copy")
    a = _cs(client, pid, "LDSP16", "L", [{"name": "p", "length": 300, "width": 200}])
    client.post(f"/api/projects/{pid}/operations/{a}/sheets/from-remnants", json={"ids": [r["id"]]})
    cp = client.post(f"/api/projects/{pid}/copy").json()
    assert all(s["source_remnant_id"] is None for o in cp["operations"] for s in o["sheets"])


def test_catalog_sync_partial_update_and_validation(client):
    r = client.post("/api/catalog/sync", json=[{"id": "t1", "kind": "sheet", "code": "C1", "name": "N1", "unit": "лист", "price": 100,
                                                "stock": 5, "thickness": 16, "params": {"kerf": 4}}])
    assert r.status_code == 200
    r = client.post("/api/catalog/sync", json=[{"id": "t1", "kind": "sheet", "name": "N1", "price": 120}])
    assert r.status_code == 200
    it = client.get("/api/catalog/t1").json()
    assert it["price"] == 120 and it["unit"] == "лист" and it["stock"] == 5 and it["params"] == {"kerf": 4} and it["thickness"] == 16
    assert client.post("/api/catalog/sync", json=[{"id": "t2", "kind": "banana", "name": "x"}]).status_code == 422
    assert client.post("/api/catalog/sync", json=[{"id": "t3", "kind": "sheet", "name": "x", "price": -5}]).status_code == 422


def test_add_operation_unknown_material_404(client):
    pid = _mk(client, "Mat")
    assert client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "material_id": "no-such"}).status_code == 404


def test_oversize_parts_warning(client):
    pid = _mk(client, "Big")
    a = _cs(client, pid, "A", "A", [{"name": "big", "length": 2845, "width": 600, "grain": True}, {"name": "ok", "length": 600, "width": 400}])
    res = client.post(f"/api/projects/{pid}/operations/{a}/optimize?quality=fast").json()
    assert len(res["unplaced"]) == 1
    assert any("больше" in w for w in res["warnings"])


def test_stock_order_list_uses_limited_sheets_first(client):
    pid = _mk(client, "Order")
    a = _cs(client, pid, "A", "A", [{"name": "p", "length": 900, "width": 500, "qty": 3}])
    client.put(f"/api/projects/{pid}/operations/{a}/sheets",
               json=[{"id": "off", "length": 1000, "width": 600, "qty": 2}, {"id": "full", "length": 2750, "width": 1830, "qty": 10000}])
    client.patch(f"/api/projects/{pid}/operations/{a}", json={"cs_cut": {"stock_order": "list"}})
    res = client.post(f"/api/projects/{pid}/operations/{a}/optimize?quality=fast").json()
    used = {}
    for m in res["maps"]:
        used[m["sheet_id"]] = used.get(m["sheet_id"], 0) + m["copies"]
    assert used.get("off") == 2 and used.get("full") == 1   # qat'iy: avval 2 qoldiq, keyin butun list
    client.patch(f"/api/projects/{pid}/operations/{a}", json={"cs_cut": {"stock_order": "economy"}})
    res = client.post(f"/api/projects/{pid}/operations/{a}/optimize?quality=fast").json()
    assert res["total_sheets"] == 1 and {m["sheet_id"] for m in res["maps"]} == {"full"}   # eng kam maydon — bitta butun list
