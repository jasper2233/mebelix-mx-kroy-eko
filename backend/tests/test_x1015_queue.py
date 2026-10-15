"""2026-10-15 — buyurtmalar navbati va material bazasi tekshiruvi (services/material_check.py, api_queue.py):
kerak / bazada / yetmaydi, katalogda yo'q material, navbatdagi birinchi «material to'liq bor» loyiha, ogohlantirishlar."""


def _project(client, name, material_id=None, code="", mname="", parts=None, folder_id=None):   # nomsiz → katalog tovar nomi
    pid = client.post("/api/projects", json={"name": name, "folder_id": folder_id}).json()["id"]
    body = {"type": "CS", "code": code, "name": mname}
    if material_id:
        body["material_id"] = material_id
    p = client.post(f"/api/projects/{pid}/operations", json=body).json()
    oid = p["operations"][-1]["id"]
    if parts:
        client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=parts)
    return pid, oid


def test_material_check_and_queue(client):
    client.post("/api/catalog/sync", json=[{"id": "m-ldspq", "kind": "sheet", "code": "LDSPQ", "name": "LDSP Q", "stock": 2,
                                            "thickness": 16, "length": 2750, "width": 1830}])
    full = [{"name": "p", "length": 2700, "width": 1800, "qty": 3}]        # 3 ta butun list kerak
    # alohida papka: navbat shu papka bo'yicha so'raladi — umumiy test bazasidagi yuzlab loyihalar (va `limit`) ta'sir qilmaydi
    fid = client.post("/api/folders", json={"name": "Navbat test"}).json()["id"]
    qs = f"statuses=0&limit=500&folder_id={fid}&all_folders=false"
    a, a_cs = _project(client, "Navbat A", material_id="m-ldspq", parts=full, folder_id=fid)
    b, b_cs = _project(client, "Navbat B", material_id="m-ldspq", parts=[{"name": "p", "length": 600, "width": 400, "qty": 2}], folder_id=fid)
    c, _ = _project(client, "Navbat C", code="NOCAT", mname="Nomalum", parts=[{"name": "p", "length": 600, "width": 400}], folder_id=fid)
    # kroygacha — taxmin (estimated), kroydan keyin — kartalardagi butun listlar
    chk = client.get(f"/api/projects/{a}/material-check").json()
    assert chk["items"][0]["estimated"] is True and chk["items"][0]["have"] == 2
    client.post(f"/api/projects/{a}/operations/{a_cs}/optimize?quality=fast")
    client.post(f"/api/projects/{b}/operations/{b_cs}/optimize?quality=fast")
    chk = client.get(f"/api/projects/{a}/material-check").json()
    it = chk["items"][0]
    assert it["need"] == 3 and it["have"] == 2 and it["short"] == 1 and it["status"] == "short" and it["estimated"] is False
    assert chk["ok"] is False and chk["warnings"] and "LDSP Q" in chk["warnings"][0]
    chk_b = client.get(f"/api/projects/{b}/material-check").json()
    assert chk_b["ok"] is True and chk_b["items"][0]["need"] == 1
    chk_c = client.get(f"/api/projects/{c}/material-check").json()
    assert chk_c["items"][0]["status"] == "unknown" and chk_c["known"] is False and chk_c["ok"] is False
    # navbat: raqam tartibida; birinchi «material to'liq bor» — B; A va C uchun ogohlantirish loyiha raqami bilan
    q = client.get(f"/api/queue?{qs}").json()
    ids = [r["project_id"] for r in q["rows"]]
    assert ids.index(a) < ids.index(b) < ids.index(c)
    assert q["next"]["project_id"] == b
    rows = {r["project_id"]: r for r in q["rows"]}
    assert rows[b]["next"] is True and rows[a]["next"] is False
    na = rows[a]["number"]
    assert any(w.startswith(f"№{na}:") for w in q["warnings"])
    assert str(rows[b]["number"]) in q["message"]
    # zaxira to'ldirildi — A ham to'liq, navbatda birinchi bo'ladi
    client.post("/api/catalog/sync", json=[{"id": "m-ldspq", "kind": "sheet", "name": "LDSP Q", "stock": 10}])
    q = client.get(f"/api/queue?{qs}").json()
    assert q["next"]["project_id"] == a
    # hech qaysi loyihada material yo'q — xabar «bazani to'ldiring»
    client.post("/api/catalog/sync", json=[{"id": "m-ldspq", "kind": "sheet", "name": "LDSP Q", "stock": 0}])
    q = client.get(f"/api/queue?{qs}").json()
    assert q["next"] is None and q["message"]
