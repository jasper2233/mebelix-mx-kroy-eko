"""2026-10-18 — «Операции» jadvali (joylashuv mosligi auditi D3 / D7): «Объединить» faqat belgilangan operatsiyalarni joriy
operatsiyaga qo'shadi (api_ops_x1018.merge_into), CS → «Нестинговый раскрой» (CN) konvertatsiyasi (yangi ustun profillari doiralari ops_columns / catalog_columns — test_grid_columns.py da parametr sifatida)."""


def _mk(client, name="X"):
    return client.post("/api/projects", json={"name": name}).json()["id"]


def _add(client, pid, ty, code="", name="", parts=None):
    p = client.post(f"/api/projects/{pid}/operations", json={"type": ty, "code": code, "name": name}).json()
    oid = p["operations"][-1]["id"]
    if parts:
        client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=parts)
    return oid


def _op(p, oid):
    return next((o for o in p["operations"] if o["id"] == oid), None)


def test_merge_only_selected_ops_into_current(client):
    pid = _mk(client, "Merge tanlov")
    a = _add(client, pid, "CS", "A", "LMDF", [{"name": "a", "length": 600, "width": 400, "qty": 2}])
    b = _add(client, pid, "CS", "B", "XDF", [{"name": "b", "length": 500, "width": 300}])
    c = _add(client, pid, "CS", "C", "XDF", [{"name": "c", "length": 400, "width": 300}])
    client.post(f"/api/projects/{pid}/operations/{a}/optimize?quality=fast")
    r = client.post(f"/api/projects/{pid}/operations/{a}/merge", json={"ids": [c]})
    assert r.status_code == 200, r.text
    p = r.json()
    assert _op(p, c) is None and _op(p, b) is not None          # faqat belgilangani qo'shildi
    assert [pt["name"] for pt in _op(p, a)["parts"]] == ["a", "c"]
    assert _op(p, a)["result"] is None                          # natija eskirdi
    assert [pt["name"] for pt in _op(p, b)["parts"]] == ["b"]
    # bitta Ctrl+Z — hammasi qaytadi
    p = client.post(f"/api/projects/{pid}/undo").json()
    assert _op(p, c) is not None and len(_op(p, a)["parts"]) == 1


def test_merge_empty_selection_changes_nothing(client):
    pid = _mk(client, "Merge bo'sh")
    a = _add(client, pid, "CS", "A", "A")
    _add(client, pid, "CS", "A", "A")
    p = client.post(f"/api/projects/{pid}/operations/{a}/merge", json={"ids": []}).json()
    assert len(p["operations"]) == 2


def test_merge_rejects_other_type_self_and_unknown(client):
    pid = _mk(client, "Merge xato")
    a = _add(client, pid, "CS", "A", "A")
    e = _add(client, pid, "EL", "K", "Kromka")
    x = _add(client, pid, "XNC")
    assert client.post(f"/api/projects/{pid}/operations/{a}/merge", json={"ids": [e]}).status_code == 400
    assert client.post(f"/api/projects/{pid}/operations/{a}/merge", json={"ids": [a]}).status_code == 400
    assert client.post(f"/api/projects/{pid}/operations/{a}/merge", json={"ids": ["nope"]}).status_code == 404
    assert client.post(f"/api/projects/{pid}/operations/{x}/merge", json={"ids": []}).status_code == 400
    assert len(client.get(f"/api/projects/{pid}").json()["operations"]) == 3


def test_merge_edges_remaps_part_references(client):
    pid = _mk(client, "Merge kromka")
    e1 = _add(client, pid, "EL", "K1", "PVC")
    e2 = _add(client, pid, "EL", "K2", "PVC 2")
    cs = _add(client, pid, "CS", "L", "LDSP", [{"name": "p", "length": 600, "width": 400, "edge_top": {"op_id": e2}}])
    p = client.post(f"/api/projects/{pid}/operations/{e1}/merge", json={"ids": [e2]}).json()
    assert _op(p, e2) is None
    assert _op(p, cs)["parts"][0]["edge_top"]["op_id"] == e1


def test_convert_cs_to_cn_keeps_parts_and_thickness(client):
    pid = _mk(client, "Konvert")
    a = _add(client, pid, "CS", "L", "LDSP", [{"name": "p", "length": 600, "width": 400, "qty": 3}])
    client.patch(f"/api/projects/{pid}/operations/{a}", json={"cs_material": {"thickness": 18, "price": 250}})
    client.post(f"/api/projects/{pid}/operations/{a}/optimize?quality=fast")
    r = client.post(f"/api/projects/{pid}/operations/{a}/convert", json={"to": "CN"})
    assert r.status_code == 200, r.text
    o = _op(r.json(), a)
    assert o["type"] == "CN" and o["cn"]["thickness"] == 18 and o["cn"]["price"] == 250
    assert o["cs_material"] is None and o["result"] is None
    assert [pt["name"] for pt in o["parts"]] == ["p"] and o["sheets"]
    # faqat CS konvertatsiya qilinadi
    assert client.post(f"/api/projects/{pid}/operations/{a}/convert", json={"to": "CN"}).status_code == 400
    p = client.post(f"/api/projects/{pid}/undo").json()
    assert _op(p, a)["type"] == "CS"

