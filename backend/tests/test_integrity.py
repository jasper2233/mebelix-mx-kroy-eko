"""Xavfsizlik va ma'lumotlar yaxlitligi: hisobotda XSS yo'q, kroy eskirishi, undo/redo va ombor,
shablon cheklovlari, mijozdan kelgan natija ombor bog'lanishini soxtalashtira olmaydi."""
import io
import json


def _op(p, oid):
    return next(o for o in p["operations"] if o["id"] == oid)


def _stock_ids(client):
    return {r["id"]: r["qty"] for r in client.get("/api/remnants?include_empty=true").json()}


XSS = '<img src=x onerror="alert(1)">'


def test_report_and_labels_escape_everything(client, kravat):
    pid, cs, el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    part = _op(p, cs)["parts"][0]
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{part['id']}", json={"name": XSS})
    client.patch(f"/api/projects/{pid}/products/{p['products'][0]['id']}", json={"name": "<script>alert(2)</script>",
                                                                               "code": "<b>K</b>"})
    client.patch(f"/api/projects/{pid}/operations/{cs}", json={"name": "<svg onload=alert(3)>"})
    client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {"color": "red' onmouseover='alert(4)",
                                                                     "symbol": "<i>"}})
    client.patch(f"/api/projects/{pid}", json={"customer": "</td><script>alert(5)</script>"})
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    ps = client.get("/api/settings/print/default").json()
    ps.update(materials_list=True, products_list=True, cs_commands=True, map_parts_list=True)
    r = client.post(f"/api/projects/{pid}/report", json=ps)
    html = r.text
    assert "default-src 'none'" in r.headers["content-security-policy"]
    assert '<meta http-equiv="Content-Security-Policy"' in html
    for bad in ("<img src=x", "<script>", "<svg onload", "onmouseover='alert", "<i>", "<b>K</b>"):
        assert bad not in html, bad
    assert "&lt;img src=x" in html and "&amp;lt;" not in html          # bir marta escape
    assert "&lt;br&gt;" not in html                                 # kromka nomlari <br> bilan ajraladi
    lab = client.get(f"/api/projects/{pid}/labels")
    assert "<img src=x" not in lab.text and "&lt;img" in lab.text
    assert "default-src 'none'" in lab.headers["content-security-policy"]


def test_forged_strips_in_result_are_not_injected(client, kravat):
    pid, cs, _ = kravat
    res = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").json()
    svg = client.get(f"/api/projects/{pid}/operations/{cs}/maps/1.svg").text
    assert svg.startswith("<svg") and "onload" not in svg
    # mijoz soxta ombor maydonlari bilan natija yuborsa — qabul qilinmaydi
    forged = dict(res, remnants_saved=True, saved_remnant_ids=[1, 2, 3], consumed_remnants={"1": 5})
    for m in forged["maps"]:
        m["strips"] = []                                           # daraxtsiz → tekshiruv yo'li
    p = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=forged).json()
    r = _op(p, cs)["result"]
    assert not r["remnants_saved"] and r["saved_remnant_ids"] == [] and r["consumed_remnants"] == {}
    # PUT operation ham natijani mijozdan olmaydi
    op = _op(p, cs)
    op["result"] = forged
    p = client.put(f"/api/projects/{pid}/operations/{cs}", json=op).json()
    assert not _op(p, cs)["result"]["remnants_saved"]


def test_product_qty_and_edge_params_invalidate_cut(client, kravat):
    pid, cs, el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    prid = p["products"][0]["id"]
    parts = _op(p, cs)["parts"]
    client.post(f"/api/projects/{pid}/operations/{cs}/parts/batch-update",
                json=[{"id": pt["id"], "fields": {"product_id": prid}} for pt in parts])
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    # nom o'zgarishi kroyni saqlaydi
    p = client.patch(f"/api/projects/{pid}/products/{prid}", json={"name": "Krovat"}).json()
    assert _op(p, cs)["result"] is not None
    # soni o'zgarsa — kroy eskiradi (detal soni = detal × mahsulot)
    p = client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": 2}).json()
    assert _op(p, cs)["result"] is None
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    pr = next(x for x in client.get(f"/api/projects/{pid}").json()["products"] if x["id"] == prid)
    p = client.put(f"/api/projects/{pid}/products/{prid}", json={**pr, "qty": 3}).json()
    assert _op(p, cs)["result"] is None
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    p = client.post(f"/api/projects/{pid}/products/zero-qty").json()
    assert _op(p, cs)["result"] is None
    client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": 1})
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    # kromka rangi — kroyga ta'sir qilmaydi; qalinligi — zagotovka o'lchami o'zgaradi → eskiradi
    p = client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {"color": "#123456"}}).json()
    assert _op(p, cs)["result"] is not None
    p = client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {"thickness": 2}}).json()
    assert _op(p, cs)["result"] is None
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    # keyingi kroy strategiyasi (sifat) — mavjud natija saqlanadi; propil — eskiradi
    p = client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": {"quality": "max"}}).json()
    assert _op(p, cs)["result"] is not None
    p = client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": {"kerf": 4}}).json()
    assert _op(p, cs)["result"] is None


def test_undo_redo_keeps_warehouse_consistent(client, kravat):
    pid, cs, _ = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    before = _stock_ids(client)
    out = client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").json()
    added = [a["id"] for a in out["added"]]
    assert added
    # undo: kroy o'sha — ombor yozuvi va bog'lanish saqlanadi (ikki marta yozilmaydi)
    p = client.post(f"/api/projects/{pid}/undo").json()
    assert _op(p, cs)["result"]["remnants_saved"] and _op(p, cs)["result"]["saved_remnant_ids"] == added
    assert client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").status_code == 400
    p = client.post(f"/api/projects/{pid}/redo").json()
    assert _op(p, cs)["result"]["remnants_saved"]
    # boshqa kroy (qayta Раскроить) — eski yozuv bekor; undo eski kroyni qaytaradi, lekin «yozilmagan» holda
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast&first_cut=1")
    stock = _stock_ids(client)
    assert all(a not in stock for a in added)
    p = client.post(f"/api/projects/{pid}/undo").json()
    r = _op(p, cs)["result"]
    assert r is not None and not r["remnants_saved"] and r["saved_remnant_ids"] == []
    assert _stock_ids(client) == stock
    # yana yozish mumkin; undo ga qaytib — keyin redo (boshqa kroy) → yozuv bekor qilinadi
    out2 = client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").json()
    assert out2["added"]
    client.post(f"/api/projects/{pid}/undo")                  # commit dan oldingi holat, kroy o'sha
    assert all(a["id"] in _stock_ids(client) for a in out2["added"])
    p = client.post(f"/api/projects/{pid}/redo").json()
    assert _op(p, cs)["result"]["remnants_saved"]
    # sex hisoblagichi undo bilan orqaga ketmaydi
    client.patch(f"/api/projects/{pid}/operations/{cs}/maps/1", json={"done_count": 1})
    p = client.post(f"/api/projects/{pid}/undo").json()
    assert _op(p, cs)["result"]["maps"][0]["done_count"] == 1
    assert set(_stock_ids(client)) >= set(before) - set(added)


def test_copy_import_merge_folder_delete_do_not_leak_warehouse(client, kravat):
    pid, cs, _ = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    out = client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").json()
    added = [a["id"] for a in out["added"]]
    # nusxa va import — ombor bog'lanishisiz
    cp = client.post(f"/api/projects/{pid}/copy").json()
    assert not next(o for o in cp["operations"] if o["type"] == "CS")["result"]["remnants_saved"]
    data = client.get(f"/api/projects/{pid}/export").content
    doc = json.loads(data)
    doc["operations"][1]["sheets"][0]["source_remnant_id"] = 999999
    imp = client.post("/api/projects/import", files={"file": ("x.mxk.json", io.BytesIO(json.dumps(doc).encode()))}).json()
    ics = next(o for o in imp["operations"] if o["type"] == "CS")
    assert not ics["result"]["remnants_saved"] and ics["sheets"][0]["source_remnant_id"] is None
    # nusxani o'chirish asl loyihaning qoldiqlariga tegmaydi
    client.delete(f"/api/projects/{cp['id']}")
    client.delete(f"/api/projects/{imp['id']}")
    assert all(a in _stock_ids(client) for a in added)
    # bir xil operatsiyalarni birlashtirish — olib tashlangan natijaning ombor yozuvi bekor qilinadi
    p = client.post(f"/api/projects/{pid}/operations/{cs}/clone").json()
    cs_ops = [o for o in p["operations"] if o["type"] == "CS"]
    assert len(cs_ops) == 2
    client.post(f"/api/projects/{pid}/actions/merge-same")
    assert all(a not in _stock_ids(client) for a in added)
    # papkani o'chirish — ichidagi loyihalar yozuvlari ham bekor
    f = client.post("/api/folders", json={"name": "Vaqtincha"}).json()
    p2 = client.post("/api/projects", json={"name": "Papkadagi"}).json()
    client.post("/api/projects/move", json={"ids": [p2["id"]], "folder_id": f["id"]})
    p2 = client.post(f"/api/projects/{p2['id']}/operations", json={"type": "CS", "code": "LDSP16", "name": "L"}).json()
    c2 = p2["operations"][-1]["id"]
    client.post(f"/api/projects/{p2['id']}/operations/{c2}/parts", json=[{"name": "A", "length": 900, "width": 600}])
    client.post(f"/api/projects/{p2['id']}/operations/{c2}/optimize?quality=fast")
    a2 = [a["id"] for a in client.post(f"/api/projects/{p2['id']}/operations/{c2}/remnants/commit").json()["added"]]
    assert a2
    assert client.delete(f"/api/folders/{f['id']}?recursive=true").json()["deleted_projects"] == 1
    assert all(a not in _stock_ids(client) for a in a2)


def test_template_limits(client, kravat):
    pid, cs, _ = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    base = {"name": "Test", "extension": "txt"}
    for tpl in ("{{ 'x' * 100000000 }}", "{% for i in range(100001) %}{% endfor %}",
                "{% for a in range(20) %}{{ range(100000)|length }}{% endfor %}",
                "{{ 9 ** 99999 }}", "{{ ''.__class__.__mro__ }}", "{% for x in maps %}{{ x.foo.bar() }}{% endfor %}"):
        r = client.post("/api/postprocessors/preview", json={"project_id": pid, "op_id": cs,
                                                             "profile": {**base, "template": tpl}}).json()
        assert r["ok"] is False, tpl
    r = client.post("/api/postprocessors/preview", json={"project_id": pid, "op_id": cs,
                                                         "profile": {**base, "template": "{{ maps|length }}"}}).json()
    assert r["ok"] and r["text"].strip().isdigit()


def test_xnc_bad_expressions_do_not_crash(client, kravat):
    pid, cs, _ = kravat
    p = client.get(f"/api/projects/{pid}").json()
    ptid = _op(p, cs)["parts"][0]["id"]
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/{ptid}/xnc").json()
    xop = next(o for o in p["operations"] if o["type"] == "XNC")
    prog = [{"cmd": "DrillFront", "params": {"X": "9**9**9", "Y": "1e308*10", "DP": "min()", "count": "1e400"},
             "comment": "", "children": []},
            {"cmd": "DrillFront", "params": {"X": "dx/2", "Y": "round(1,5)", "D": 8, "DP": 12}, "comment": "", "children": []}]
    r = client.patch(f"/api/projects/{pid}/operations/{xop['id']}", json={"xnc": {"program": prog}})
    assert r.status_code == 200
    assert client.get(f"/api/projects/{pid}/operations/{xop['id']}/xnc-stats").status_code == 200
    assert client.get(f"/api/projects/{pid}/operations/{xop['id']}/xnc.svg").status_code == 200


def test_template_runs_in_worker_with_time_and_memory_limits(client, kravat, monkeypatch):
    """Sandbox chetlab o'tadigan resurs hujumlari: xotira (center), cheksiz sikl — yordamchi jarayon o'ldiriladi."""
    pid, cs, _ = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    monkeypatch.setenv("MEBELIX_TEMPLATE_TIMEOUT", "3")
    base = {"name": "Test", "extension": "txt"}
    slow = ("{% for a in maps %}{% for b in range(100000) %}{% for c in range(9) %}{% endfor %}{% endfor %}"
            "{% endfor %}" * 3)
    for tpl in ("{{ 'x'.center(2000000000) }}", "{{ f(1, 999999999) }}{{ '%0999999999d' % 1 }}", slow):
        r = client.post("/api/postprocessors/preview", json={"project_id": pid, "op_id": cs,
                                                             "profile": {**base, "template": tpl}}).json()
        assert r["ok"] is False, tpl
    # keyin oddiy shablon yana ishlaydi (jarayon qayta ochiladi)
    r = client.post("/api/postprocessors/preview", json={"project_id": pid, "op_id": cs,
                                                         "profile": {**base, "template": "{{ f(12.345) }}"}}).json()
    assert r == {**r, "ok": True, "text": "12.3"}


def _gnodes(n, out):
    if n.get("g") is not None:
        out.append(n)
    for c in n.get("c", []):
        _gnodes(c, out)


def test_grouping_blocks_packets_and_limits(client, kravat):
    """Группировка в блок (группы с пропилом для групповых деталей), пакеты, простые полосы, узкие кромки."""
    pid, cs, el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    parts = {pt["uid"]: pt for pt in _op(p, cs)["parts"]}
    client.post(f"/api/projects/{pid}/operations/{cs}/parts/batch-update", json=[
        {"id": parts[5]["id"], "fields": {"group_by": "length"}},        # 50×1052 ×2 → blok 2×50 + propil
        {"id": parts[13]["id"], "fields": {"group_by": "width", "group_max": 2}},
    ])
    client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": {"kerf_group": 5, "quality": "fast"}})
    res = client.post(f"/api/projects/{pid}/operations/{cs}/optimize").json()
    assert not res["unplaced"] and res["total_sheets"] == 2
    for uid in (5, 13):
        pl = [x for m in res["maps"] for x in m["placements"] if x["part_uid"] == uid]
        assert len(pl) == 2
        a, b = sorted(pl, key=lambda q: (q["x"], q["y"]))
        gap_x = b["x"] - (a["x"] + a["length"])
        gap_y = b["y"] - (a["y"] + a["width"])
        assert abs(gap_x - 5) < 0.01 or abs(gap_y - 5) < 0.01, (uid, a, b)     # blok ichida guruh propili
    groups = []
    for m in res["maps"]:
        _gnodes(m["strips"][0], groups)
    assert len(groups) == 2 and all(g["g"] == 5 for g in groups)
    # daraxt → qayta qurish (tahrir saqlash) va tahrir amali guruh tugunlari bilan ishlaydi
    p = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=res).json()
    r2 = _op(p, cs)["result"]
    assert r2["total_sheets"] == 2 and not r2["unplaced"]
    # paketlar: 40 mm / 16 mm = 2 list (Кратность 2)
    assert r2["sheets_per_pack"] == 2 and r2["total_packs"] == sum((m["copies"] + 1) // 2 for m in r2["maps"])
    m1 = r2["maps"][0]
    path = None

    def find(n, pth):
        nonlocal path
        if n.get("k") == "P" and n.get("u") == 13 and path is None:
            path = pth
        for i, c in enumerate(n.get("c", [])):
            find(c, pth + [i])
    for mi, m in enumerate(r2["maps"], 1):
        find(m["strips"][0], [])
        if path is not None:
            ed = client.post(f"/api/projects/{pid}/operations/{cs}/edit",
                             json={"result": r2, "action": {"type": "remove", "map": mi, "path": path}})
            assert ed.status_code == 200, ed.text
            assert ed.json()["unplaced"] == [parts[13]["id"]]
            break
    assert path is not None and m1
    # simple strips only: still valid
    p = client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": {"complex_strips": False}}).json()
    res = client.post(f"/api/projects/{pid}/operations/{cs}/optimize").json()
    assert not res["unplaced"]
    # report header field PK
    ps = client.get("/api/settings/print/default").json()
    ps["map_header_fields"] = ["N", "PK"]
    assert "PK:" in client.post(f"/api/projects/{pid}/report", json=ps).text
    # EL: kromkaga perpendikulyar tomon cheklovi
    client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {"min_perp_side": 900}})
    u = client.get(f"/api/projects/{pid}/operations/{el}/edge-usage").json()
    assert u["narrow"] == 1 and u["rows"][0]["narrow"]


def test_non_finite_and_malformed_input_never_break_project(client, kravat):
    pid, cs, el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    ptid = _op(p, cs)["parts"][0]["id"]
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/{ptid}/xnc").json()
    xop = next(o for o in p["operations"] if o["type"] == "XNC")
    prog = [{"cmd": "MillRect", "params": {"X": 0, "Y": 0, "L": "1e308", "W": "1e308"}, "comment": "", "children": []}]
    assert client.patch(f"/api/projects/{pid}/operations/{xop['id']}", json={"xnc": {"program": prog}}).status_code == 200
    r = client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_material": {"price": 1e308}})
    assert r.status_code == 422                       # QA B №6: narx ≤ 1e9 (ma'nosiz katta qiymat rad etiladi)
    assert client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").status_code == 200
    assert client.get(f"/api/projects/{pid}").status_code == 200          # loyiha ochiladi
    assert client.post(f"/api/projects/{pid}/undo").status_code == 200
    # cheksiz son kirishda — 422 (500 emas), loyiha buzilmaydi
    bad = '{"length": Infinity}'
    r = client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{ptid}", content=bad,
                     headers={"Content-Type": "application/json"})
    assert r.status_code == 422
    assert client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{ptid}", json={"length": "abc"}).status_code == 422
    prid = client.get(f"/api/projects/{pid}").json()["products"][0]["id"]
    assert client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": "abc"}).status_code == 422
    assert client.get(f"/api/projects/{pid}").status_code == 200
    # bazadagi buzuq yozuv (son o'rnida null) ham ochiladi
    from app.db import ProjectRow, SessionLocal
    with SessionLocal() as s:
        row = s.get(ProjectRow, pid)
        data = json.loads(json.dumps(row.data))
        data["operations"][1]["cost_material"] = None
        data["operations"][1]["parts"][0]["length"] = None
        row.data = data
        s.commit()
    got = client.get(f"/api/projects/{pid}")
    assert got.status_code == 200 and _op(got.json(), cs)["parts"][0]["length"] == 0


def test_editor_rejects_forged_group_nodes_and_bad_actions(client, kravat):
    pid, cs, _ = kravat
    res = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").json()
    forged = json.loads(json.dumps(res))

    def first_c(n):
        for c in n.get("c", []):
            if c.get("k") == "C":
                return c
        return None
    node = first_c(forged["maps"][0]["strips"][0])
    node["g"] = 0                                            # soxta guruh propili (guruhlash yo'q)
    r = client.put(f"/api/projects/{pid}/operations/{cs}/result", json=forged)
    assert r.status_code == 422
    forged["maps"][0]["strips"][0]["g"] = 0                  # ildizda ham
    assert client.put(f"/api/projects/{pid}/operations/{cs}/result", json=forged).status_code == 422
    for action in ({"type": "remove", "map": "x", "path": [0]}, {"type": "remove", "map": 1, "path": ["a"]},
                   {"type": "remove", "map": 1, "path": None}, {"type": "add_map", "sheet_id": [1]},
                   {"type": "copies", "map": 1, "copies": "many"}, {"type": "place", "map": 1, "path": [0], "uid": [1]}):
        e = client.post(f"/api/projects/{pid}/operations/{cs}/edit", json={"result": res, "action": action})
        assert e.status_code < 500 and (action["type"] == "add_map" or e.status_code in (400, 422)), \
            (action, e.status_code, e.text[:200])
    broken = json.loads(json.dumps(res))
    del broken["maps"][0]["strips"][0]["x"]
    assert client.put(f"/api/projects/{pid}/operations/{cs}/result", json=broken).status_code == 422
    broken = json.loads(json.dumps(res))
    broken["maps"][0]["strips"][0]["c"][0] = "oops"
    assert client.put(f"/api/projects/{pid}/operations/{cs}/result", json=broken).status_code == 422


def test_remnant_identity_merge_el_and_type_change(client, kravat):
    pid, cs, el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    out = client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").json()
    rid = out["added"][0]["id"]
    p2 = client.post("/api/projects", json={"name": "B"}).json()
    p2 = client.post(f"/api/projects/{p2['id']}/operations", json={"type": "CS", "code": "LDSP16", "name": "L"}).json()
    c2 = p2["operations"][-1]["id"]
    client.post(f"/api/projects/{p2['id']}/operations/{c2}/parts", json=[{"name": "k", "length": 300, "width": 200}])
    client.post(f"/api/projects/{p2['id']}/operations/{c2}/sheets/from-remnants", json={"ids": [rid]})
    client.post(f"/api/projects/{p2['id']}/operations/{c2}/optimize?quality=fast")
    # ombordagi qator boshqa qoldiqqa aylandi (o'lchami o'zgardi) — commit 409
    client.patch(f"/api/remnants/{rid}", json={"length": 700, "width": 600, "material_code": "MDF8"})
    assert client.post(f"/api/projects/{p2['id']}/operations/{c2}/remnants/commit").status_code == 409
    # bir xil nomli kromkalar, lekin qalinligi boshqa — birlashtirilmaydi (QA №26: detal o'lchamlari jimgina o'zgarmasin)
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "code": "KP-1/19", "name": "PVC 1-19"}).json()
    el2 = p["operations"][-1]["id"]
    client.patch(f"/api/projects/{pid}/operations/{el2}", json={"el": {"thickness": 2}})
    parts = _op(p, cs)["parts"]
    client.post(f"/api/projects/{pid}/operations/{cs}/parts/batch-update",
                json=[{"id": parts[0]["id"], "fields": {"edge_left": {"op_id": el2}}}])
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    p = client.post(f"/api/projects/{pid}/actions/merge-same").json()
    assert _op(p, cs)["result"] is not None and len([o for o in p["operations"] if o["type"] == "EL"]) == 2
    # EL → GR (turi o'zgardi) — kromkali detallar o'lchami o'zgaradi
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    elop = next(o for o in p["operations"] if o["type"] == "EL")
    elop["type"] = "GR"
    p = client.put(f"/api/projects/{pid}/operations/{elop['id']}", json=elop).json()
    assert _op(p, cs)["result"] is None


def test_grouping_falls_back_when_blocks_do_not_fit_limited_sheets(client):
    p = client.post("/api/projects", json={"name": "Blok"}).json()
    pid = p["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "L", "name": "L"}).json()
    cs = p["operations"][-1]["id"]
    parts = [{"name": f"S{i}", "length": 100, "width": 600, "qty": 29, "grain": True, "group_by": "length"}
             for i in range(3)]
    client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=parts)
    client.put(f"/api/projects/{pid}/operations/{cs}/sheets", json=[
        {"length": 3050, "width": 1250, "qty": 1}, {"length": 2750, "width": 1830, "qty": 10000}])
    res = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").json()
    assert res["unplaced"] == []
    # paketlar qalinlik o'zgarsa yangilanadi (40 mm / 25 mm = 1 list)
    p = client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_material": {"thickness": 25}}).json()
    assert _op(p, cs)["result"]["sheets_per_pack"] == 1
    # import nomsiz — «Без названия»
    doc = client.get(f"/api/projects/{pid}/export").json()
    doc["name"] = ""
    imp = client.post("/api/projects/import", files={"file": ("x.mxk.json", io.BytesIO(json.dumps(doc).encode()))}).json()
    assert imp["name"] == "Без названия"


def test_postprocessor_zip_names_are_safe(client, kravat):
    pid, cs, _ = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    prof = client.post("/api/settings/postprocessor", json={"name": "../x", "data": {
        "name": "../../evil", "extension": "../../x", "per_map": True, "template": "{{ map.index }}"}}).json()
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?profile_id={prof['id']}")
    assert r.status_code == 200
    import zipfile
    names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
    assert names and all("/" not in n and ".." not in n for n in names), names
