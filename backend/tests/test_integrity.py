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
