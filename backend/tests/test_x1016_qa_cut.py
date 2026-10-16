"""2026-10-16 — QA tuzatishlari (kroy / EL / postprotsessor), docs/mebelix/X_1015_ONLAYN_AUDIT_MCP.md §15:
#1 EL «Толщина»/«Ширина прифуговки» → qaysi kroy natijalari o'chadi (`edge-affected`, o'zgartirmaydi);
#3 stanok formati burilishlarni cheklasa — `refit=check|copy|replace` (nusxadan eksport loyihani o'zgartirmaydi);
#6 «Раскроить все операции»: bo'sh operatsiya — `skipped` (xato emas);
#14 XNC ro'yxatida pil markazi shabloni yo'q, noto'g'ri shablon — tushunarli xabar;
#16 (backend tomoni yo'q — UI) ; #22 «Требование на склад» № = operatsiya jadvalidagi raqam (XNC lar ham sanaladi)."""
from app.models import PostprocessorProfile


def _op(client, pid, oid):
    return next(x for x in client.get(f"/api/projects/{pid}").json()["operations"] if x["id"] == oid)


# ── #1 ──
def test_edge_affected_lists_cut_ops_using_the_edge_without_changing_anything(client, kravat):
    pid, cs, el = kravat
    r = client.get(f"/api/projects/{pid}/operations/{el}/edge-affected")
    assert r.status_code == 200 and r.json()["ops"] == [] and r.json()["fields"] == ["thickness", "jointing_width"]
    assert client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").status_code == 200
    # ikkinchi kromka — hech qaysi detalda yo'q: ta'sir qilmaydi
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "code": "K2", "name": "PVC 2"}).json()
    el2 = p["operations"][-1]["id"]
    assert client.get(f"/api/projects/{pid}/operations/{el2}/edge-affected").json()["ops"] == []
    d = client.get(f"/api/projects/{pid}/operations/{el}/edge-affected").json()
    assert [o["id"] for o in d["ops"]] == [cs]
    assert d["ops"][0]["type"] == "CS" and d["ops"][0]["manual"] is False and d["ops"][0]["remnants_saved"] is False
    assert _op(client, pid, cs)["result"]["maps"]                       # so'rov natijani o'chirmadi
    # CS operatsiyasi uchun so'ralsa — bo'sh ro'yxat (faqat EL uchun ma'noli)
    assert client.get(f"/api/projects/{pid}/operations/{cs}/edge-affected").json()["ops"] == []
    # haqiqiy o'zgarish — avvalgidek natijani o'chiradi (UI tasdiqdan keyin yuboradi)
    client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {"thickness": 2}})
    assert _op(client, pid, cs)["result"] is None
    assert client.get(f"/api/projects/{pid}/operations/{el}/edge-affected").json()["ops"] == []


# ── #3 ──
def _cut_rot(client, kravat, rot):
    pid, cs, _el = kravat
    assert client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": {"max_rotations": rot}}).status_code == 200
    assert client.post(f"/api/projects/{pid}/operations/{cs}/optimize").status_code == 200
    return pid, cs


def test_pp_refit_check_reports_need_without_touching_result(client, kravat):
    pid, cs = _cut_rot(client, kravat, 5)
    before = _op(client, pid, cs)
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"key": "machine:fastpanel", "refit": "check"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["refit"] == {"limit": 3, "current": 5, "manual": False, "remnants_saved": False} and d["machine"]
    after = _op(client, pid, cs)
    assert after["result"] == before["result"] and after["cs_cut"]["max_rotations"] == 5   # hech narsa o'zgarmadi
    # chegara ichida — qayta kroy kerak emas
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"key": "machine:holzma_ptx", "refit": "check"})
    assert r.status_code == 200 and r.json()["refit"] is None


def test_pp_refit_copy_exports_without_replacing_stored_result(client, kravat):
    pid, cs = _cut_rot(client, kravat, 5)
    # qo'lda tahrirlangan natija (izoh) — nusxadan eksportda yo'qolmasligi kerak
    assert client.patch(f"/api/projects/{pid}/operations/{cs}/maps/1", json={"comment": "qo'lda"}).status_code == 200
    before = _op(client, pid, cs)
    hist = client.get(f"/api/projects/{pid}/history").json()
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"key": "machine:fastpanel", "refit": "copy"})
    assert r.status_code == 200, r.text
    assert r.headers.get("X-PP-Refit") == "3" and r.headers.get("X-PP-Refit-Mode") == "copy" and r.content
    after = _op(client, pid, cs)
    assert after["result"] == before["result"] and after["cs_cut"]["max_rotations"] == 5
    assert after["result"]["maps"][0]["comment"] == "qo'lda"
    assert client.get(f"/api/projects/{pid}/history").json() == hist         # tarix qadami ham qo'shilmadi


def test_pp_refit_replace_is_the_default_and_rewrites_result(client, kravat):
    pid, cs = _cut_rot(client, kravat, 5)
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"key": "machine:fastpanel", "refit": "replace"})
    assert r.status_code == 200 and r.headers.get("X-PP-Refit") == "3" and r.headers.get("X-PP-Refit-Mode") == "replace"
    assert _op(client, pid, cs)["cs_cut"]["max_rotations"] == 3
    assert client.get(f"/api/projects/{pid}/operations/{cs}/postprocess",
                      params={"key": "machine:fastpanel", "refit": "bogus"}).status_code == 422


# ── #6 ──
def test_optimize_all_reports_empty_ops_as_skipped_not_error(client):
    pid = client.post("/api/projects", json={"name": "Hammasi 2"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "A", "name": "A"}).json()
    a = p["operations"][-1]["id"]
    client.post(f"/api/projects/{pid}/operations/{a}/parts", json=[{"name": "p", "length": 600, "width": 400, "qty": 2}])
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "B", "name": "Bo'sh"}).json()
    b = p["operations"][-1]["id"]
    d = client.post(f"/api/projects/{pid}/actions/optimize-all?quality=fast").json()
    res = {x["op_id"]: x for x in d["results"]}
    assert res[a]["sheets"] == 1
    assert res[b]["skipped"] is True and "error" not in res[b] and res[b]["reason"]
    d = client.post(f"/api/projects/{pid}/actions/optimize-all?quality=fast&skip_done=true").json()
    res = {x["op_id"]: x for x in d["results"]}
    assert res[a]["skipped"] is True and res[a]["reason"] and res[b]["skipped"] is True


# ── #14 ──
def test_xnc_pp_list_hides_saw_templates_and_errors_are_clear(client, kravat):
    pid, cs, _el = kravat
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "XNC", "code": "X1", "name": "x1"}).json()
    xid = p["operations"][-1]["id"]
    saw = client.post("/api/settings/postprocessor", json={"name": "QA saw", "data": PostprocessorProfile(
        name="QA saw", extension="txt", template="{% for m in maps %}{{ m.index }}{% endfor %}").model_dump()}).json()
    xnc = client.post("/api/settings/postprocessor", json={"name": "QA xnc", "data": PostprocessorProfile(
        name="QA xnc", extension="nc", template="{{ xnc.code }}").model_dump()}).json()
    both = client.post("/api/settings/postprocessor", json={"name": "QA any", "data": PostprocessorProfile(
        name="QA any", extension="txt", template="{{ project.number }}").model_dump()}).json()
    try:
        lst = {i["key"]: i for i in client.get("/api/xnc/postprocessors").json()}
        assert f"pp:{saw['id']}" not in lst
        assert lst[f"pp:{xnc['id']}"]["kind"] == "xnc" and lst[f"pp:{both['id']}"]["kind"] == "any"
        # CS ro'yxatida hammasi bor (o'zgarmagan)
        keys = {i["key"] for i in client.get("/api/postprocessors").json()}
        assert f"pp:{saw['id']}" in keys and f"pp:{xnc['id']}" in keys
        r = client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"profile_id": saw["id"]})
        assert r.status_code == 400 and "map" in r.json()["detail"] and "Undefined" not in r.json()["detail"]
        client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
        r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"profile_id": xnc["id"]})
        assert r.status_code == 400 and "xnc" in r.json()["detail"] and "Undefined" not in r.json()["detail"]
        assert client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"profile_id": xnc["id"]}).status_code == 200
    finally:
        for pr in (saw, xnc, both):
            client.delete(f"/api/settings/postprocessor/{pr['id']}")


# ── #22 ──
def test_warehouse_request_numbers_are_operation_table_indexes(client, kravat):
    from app.services.render import _warehouse_rows
    from app.models import PrintSettings, Project
    pid, cs, el = kravat
    for nm in ("x1", "x2"):                                     # XNC qatorlari ham sanaladi
        client.post(f"/api/projects/{pid}/operations", json={"type": "XNC", "code": nm, "name": nm})
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "B", "name": "B"}).json()
    b = p["operations"][-1]["id"]
    client.post(f"/api/projects/{pid}/operations/{b}/parts", json=[{"name": "q", "length": 500, "width": 300}])
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    client.post(f"/api/projects/{pid}/operations/{b}/optimize?quality=fast")
    proj = Project.model_validate(client.get(f"/api/projects/{pid}").json())
    rows = _warehouse_rows(proj, PrintSettings(), {"sheets_n": "", "pcs": "", "cut_len": "", "m": "", "edge_work": "",
                                                   "cl_strips_n": "", "project": ""})
    nums = {r[2]: r[0] for r in rows if r[1] in ("CS", "EL")}   # kod → №
    idx = {o.code: i for i, o in enumerate(proj.operations, 1)}
    assert nums["LDSP16"] == idx["LDSP16"] == 2 and nums["B"] == idx["B"] == 5
