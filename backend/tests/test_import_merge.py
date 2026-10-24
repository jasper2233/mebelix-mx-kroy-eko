"""«Проект → Импортировать»: bir nechta loyiha fayli ochiq loyihaga qo'shiladi (`POST /projects/{pid}/import-merge`)."""
import json


def _project_json(client, kravat) -> bytes:
    pid, _cs, _el = kravat
    return json.dumps(client.get(f"/api/projects/{pid}").json()).encode()


def test_merge_two_files_into_open_project(client, kravat):
    src = _project_json(client, kravat)
    tgt = client.post("/api/projects", json={"name": "Yangi"}).json()["id"]
    files = [("files", ("a.mxk.json", src, "application/json")), ("files", ("b.mxk.json", src, "application/json"))]
    r = client.post(f"/api/projects/{tgt}/import-merge", files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert [f["ok"] for f in body["files"]] == [True, True]
    p = body["project"]
    assert p["name"] == "Yangi"                                    # sarlavha o'zgarmaydi
    src_p = json.loads(src)
    assert len(p["operations"]) == 2 * len(src_p["operations"])
    assert len(p["products"]) == len([x for x in p["products"]]) >= 2 * len(src_p["products"]) - 1
    ids = [o["id"] for o in p["operations"]] + [x["id"] for x in p["products"]] + \
          [pt["id"] for o in p["operations"] for pt in o["parts"]]
    assert len(ids) == len(set(ids))                               # to'qnashgan id lar yangilangan
    uids = [pt["uid"] for o in p["operations"] for pt in o["parts"]]
    assert len(uids) == len(set(uids)) and min(uids) == 1         # detal raqamlari davom etadi
    src_uids = [pt["uid"] for o in src_p["operations"] for pt in o["parts"]]
    assert uids[:len(src_uids)] == src_uids                        # birinchi fayl ID lari saqlanadi (onlayn kabi)
    assert min(uids[len(src_uids):]) > max(src_uids)                # ikkinchisi — band, keyingi raqamlardan
    op_ids = {o["id"] for o in p["operations"]}
    prod_ids = {x["id"] for x in p["products"]}
    for o in p["operations"]:
        for pt in o["parts"]:
            if pt.get("product_id"):
                assert pt["product_id"] in prod_ids
            for side in ("edge_top", "edge_bottom", "edge_left", "edge_right"):
                e = pt.get(side)
                if e and e.get("op_id"):
                    assert e["op_id"] in op_ids                    # kromka havolasi o'z nusxasiga
    # ikkinchi nusxaning kromkasi ikkinchi EL operatsiyasiga bog'langan
    els = [o["id"] for o in p["operations"] if o["type"] == "EL"]
    css = [o for o in p["operations"] if o["type"] == "CS"]
    used = {pt["edge_top"]["op_id"] for o in css for pt in o["parts"] if pt.get("edge_top") and pt["edge_top"].get("op_id")}
    assert used == set(els)
    # bitta Ctrl+Z bilan hammasi qaytadi
    assert client.post(f"/api/projects/{tgt}/undo").status_code == 200
    assert client.get(f"/api/projects/{tgt}").json()["operations"] == []


def test_merge_reports_bad_file_and_keeps_good(client, kravat):
    src = _project_json(client, kravat)
    tgt = client.post("/api/projects", json={"name": "T"}).json()["id"]
    files = [("files", ("bad.mxk.json", b"{not json", "application/json")), ("files", ("ok.mxk.json", src, "application/json"))]
    r = client.post(f"/api/projects/{tgt}/import-merge", files=files)
    assert r.status_code == 200
    rep = {f["file"]: f for f in r.json()["files"]}
    assert rep["bad.mxk.json"]["ok"] is False and rep["ok.mxk.json"]["ok"] is True
    assert len(r.json()["project"]["operations"]) == len(json.loads(src)["operations"])
