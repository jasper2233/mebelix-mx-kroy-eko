"""W14 — «Общие действия»: onlayn GibLabdagi 3 amal (merge-same, split-edges, optimize-ops) bizda ishlashi va
taxminiy-xavfsiz «Очистить проект» (kroy natijalari va hisoblangan sanoqlar; detal/operatsiyalar saqlanadi; undo bor)."""
import pytest

from app.services import mes


@pytest.fixture(autouse=True)
def _quiet_hooks(monkeypatch):
    monkeypatch.setattr(mes, "send_webhook", lambda event, payload, attempts=None: dict(sent=True, attempts=1))


def mk(client, name="W14 amallar"):
    return client.post("/api/projects", json={"name": name}).json()["id"]


def add_op(client, pid, **body):
    p = client.post(f"/api/projects/{pid}/operations", json=body).json()
    return p["operations"][-1]["id"]


def parts(client, pid, oid, *items):
    return client.post(f"/api/projects/{pid}/operations/{oid}/parts",
                       json=[dict(name=n, length=L, width=W, qty=q, **kw) for n, L, W, q, kw in items]).json()


def proj(client, pid):
    return client.get(f"/api/projects/{pid}").json()


def op(p, oid):
    return next(o for o in p["operations"] if o["id"] == oid)


def version(client, pid):
    return client.get(f"/api/projects/{pid}/history").json()["version"]


def all_uids(p):
    return sorted(pt["uid"] for o in p["operations"] for pt in o["parts"])


# ───────────────────────── 1. Объединить операции с одинаковым кодом и наименованием ─────────────────────────
def test_merge_same_joins_parts_remaps_edges_and_is_one_undo_step(client):
    pid = mk(client)
    el1 = add_op(client, pid, type="EL", code="PVC", name="PVC 1/19")
    el2 = add_op(client, pid, type="EL", code="PVC", name="PVC 1/19")
    el3 = add_op(client, pid, type="EL", code="PVC2", name="PVC 2/19")
    c1 = add_op(client, pid, type="CS", code="L16", name="LDSP 16")
    c2 = add_op(client, pid, type="CS", code="L16", name="LDSP 16")
    c3 = add_op(client, pid, type="CS", code="L18", name="LDSP 18")
    parts(client, pid, c1, ("A", 500, 300, 2, {"edge_top": {"op_id": el1}}))
    parts(client, pid, c2, ("B", 600, 300, 1, {"edge_top": {"op_id": el2}, "edge_left": {"op_id": el3}}))
    parts(client, pid, c3, ("C", 700, 300, 3, {"edge_top": {"op_id": el2}}))
    client.post(f"/api/projects/{pid}/operations/{c1}/optimize?quality=fast")
    client.post(f"/api/projects/{pid}/operations/{c3}/optimize?quality=fast")
    before = proj(client, pid)
    v0 = version(client, pid)
    uids = all_uids(before)

    p = client.post(f"/api/projects/{pid}/actions/merge-same").json()
    types = [(o["type"], o["code"]) for o in p["operations"]]
    assert types == [("EL", "PVC"), ("EL", "PVC2"), ("CS", "L16"), ("CS", "L18")]      # tartib: birinchisi qoladi
    merged = op(p, c1)
    assert [pt["name"] for pt in merged["parts"]] == ["A", "B"] and all_uids(p) == uids   # detal yo'qolmagan, uid lar o'sha
    assert merged["result"] is None                                                    # birlashgan CS natijasi eskirdi
    assert op(p, c3)["result"] is not None                                             # tegilmagan CS natijasi saqlangan
    b = merged["parts"][1]
    assert b["edge_top"]["op_id"] == el1 and b["edge_left"]["op_id"] == el3            # olib tashlangan EL ga havola qayta bog'langan
    assert op(p, c3)["parts"][0]["edge_top"]["op_id"] == el1
    assert version(client, pid) == v0 + 1                                              # bitta qadam
    back = client.post(f"/api/projects/{pid}/undo").json()
    assert [o["id"] for o in back["operations"]] == [o["id"] for o in before["operations"]]
    assert op(before, c1)["result"] is not None and op(back, c1)["result"] is not None


def test_merge_same_keeps_el_with_other_thickness_and_ignores_xnc_gr(client):
    pid = mk(client)
    e1 = add_op(client, pid, type="EL", code="PVC", name="PVC")
    e2 = add_op(client, pid, type="EL", code="PVC", name="PVC")
    client.patch(f"/api/projects/{pid}/operations/{e2}", json={"el": {"thickness": 2}})
    x1 = add_op(client, pid, type="XNC", code="X", name="X")
    x2 = add_op(client, pid, type="XNC", code="X", name="X")
    g1 = add_op(client, pid, type="GR", code="G", name="G")
    g2 = add_op(client, pid, type="GR", code="G", name="G")
    p = client.post(f"/api/projects/{pid}/actions/merge-same").json()
    ids = [o["id"] for o in p["operations"]]
    assert e1 in ids and e2 in ids                                  # kromka qalinligi boshqa — boshqa material
    assert x1 in ids and x2 in ids and g1 in ids and g2 in ids      # faqat CS / CL / EL birlashtiriladi
    # takror chaqiruv — hech narsa o'zgarmaydi
    assert [o["id"] for o in client.post(f"/api/projects/{pid}/actions/merge-same").json()["operations"]] == ids


# ───────────────────────── 2. Кромочные операции по материалам раскроя ─────────────────────────
def test_split_edges_gives_each_cs_material_its_own_edge_operation(client):
    pid = mk(client)
    el = add_op(client, pid, type="EL", code="PVC", name="PVC 1/19")
    client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {"thickness": 1.5}})
    c1 = add_op(client, pid, type="CS", code="L16", name="LDSP")
    c2 = add_op(client, pid, type="CS", code="M18", name="MDF")
    c3 = add_op(client, pid, type="CS", code="K", name="Kromkasiz")
    parts(client, pid, c1, ("A", 500, 300, 1, {"edge_top": {"op_id": el}}), ("A2", 400, 300, 1, {"edge_left": {"op_id": el}}))
    parts(client, pid, c2, ("B", 600, 300, 1, {"edge_top": {"op_id": el}, "edge_bottom": {"op_id": el}}))
    parts(client, pid, c3, ("C", 700, 300, 1, {}))
    client.post(f"/api/projects/{pid}/operations/{c1}/optimize?quality=fast")
    v0 = version(client, pid)
    p = client.post(f"/api/projects/{pid}/actions/split-edges").json()
    els = [o for o in p["operations"] if o["type"] == "EL"]
    assert len(els) == 2 and els[0]["id"] == el and els[1]["id"] != el
    assert els[1]["name"] == "PVC 1/19 (MDF)" and els[1]["code"] == "PVC" and els[1]["el"]["thickness"] == 1.5
    assert [pt["edge_top"]["op_id"] for pt in op(p, c1)["parts"]][0] == el        # birinchi CS asl kromkada qoladi
    assert op(p, c1)["parts"][1]["edge_left"]["op_id"] == el
    b = op(p, c2)["parts"][0]
    assert b["edge_top"]["op_id"] == els[1]["id"] and b["edge_bottom"]["op_id"] == els[1]["id"]
    assert op(p, c3)["parts"][0]["edge_top"]["op_id"] is None
    assert op(p, c1)["result"] is not None                                          # kroy natijasi saqlanadi (o'lcham o'zgarmaydi)
    assert version(client, pid) == v0 + 1
    again = client.post(f"/api/projects/{pid}/actions/split-edges").json()          # takror — yangi kromka paydo bo'lmaydi
    assert len([o for o in again["operations"] if o["type"] == "EL"]) == 2


def test_split_edges_then_merge_same_do_not_fight(client):
    """Ajratilgan kromka nomi CS nomini o'z ichiga oladi — «birlashtirish» ularni qayta yig'maydi."""
    pid = mk(client)
    el = add_op(client, pid, type="EL", code="PVC", name="PVC")
    c1 = add_op(client, pid, type="CS", code="L", name="LDSP")
    c2 = add_op(client, pid, type="CS", code="M", name="MDF")
    parts(client, pid, c1, ("A", 500, 300, 1, {"edge_top": {"op_id": el}}))
    parts(client, pid, c2, ("B", 600, 300, 1, {"edge_top": {"op_id": el}}))
    client.post(f"/api/projects/{pid}/actions/split-edges")
    p = client.post(f"/api/projects/{pid}/actions/merge-same").json()
    assert len([o for o in p["operations"] if o["type"] == "EL"]) == 2


# ───────────────────────── 3. Оптимизировать операции ─────────────────────────
def test_optimize_ops_cleans_merges_orders_and_keeps_manual_work(client):
    pid = mk(client)
    x_manual = add_op(client, pid, type="XNC", code="XM", name="Qo'lda XNC")
    e_unused = add_op(client, pid, type="EL", code="EU", name="Ishlatilmagan")
    e1 = add_op(client, pid, type="EL", code="PVC", name="PVC")
    e2 = add_op(client, pid, type="EL", code="PVC", name="PVC")
    empty_cs = add_op(client, pid, type="CS", code="E", name="Bo'sh")
    c1 = add_op(client, pid, type="CS", code="L16", name="LDSP")
    c2 = add_op(client, pid, type="CS", code="L16", name="LDSP")
    g = add_op(client, pid, type="GR", code="G", name="Paz")
    parts(client, pid, c1, ("A", 500, 300, 2, {"edge_top": {"op_id": e1}}))
    parts(client, pid, c2, ("B", 600, 300, 1, {"edge_top": {"op_id": e2}}))
    before = proj(client, pid)
    uids = all_uids(before)
    v0 = version(client, pid)
    p = client.post(f"/api/projects/{pid}/actions/optimize-ops").json()
    kinds = [o["type"] for o in p["operations"]]
    assert kinds == ["CS", "EL", "GR", "XNC"], kinds                      # CS → EL → GR → XNC
    ids = {o["id"] for o in p["operations"]}
    assert empty_cs not in ids and e_unused not in ids and c2 not in ids and e2 not in ids
    assert {c1, e1, g, x_manual} <= ids                                    # qo'lda qo'shilgan XNC va GR saqlanadi
    assert all_uids(p) == uids and len(op(p, c1)["parts"]) == 2
    assert op(p, c1)["parts"][1]["edge_top"]["op_id"] == e1
    assert version(client, pid) == v0 + 1
    undone = client.post(f"/api/projects/{pid}/undo").json()
    assert [o["id"] for o in undone["operations"]] == [o["id"] for o in before["operations"]]


def test_optimize_ops_on_empty_project_is_harmless(client):
    pid = mk(client)
    p = client.post(f"/api/projects/{pid}/actions/optimize-ops").json()
    assert p["operations"] == [] and p["products"]


# ───────────────────────── 4. «Очистить проект» (taxminiy, xavfsiz talqin) ─────────────────────────
def _cut_project(client, kravat):
    pid, cs, el = kravat
    xnc = add_op(client, pid, type="XNC", code="XK", name="XNC kod")
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    client.patch(f"/api/projects/{pid}", json={"note": "muhim izoh"})
    return pid, cs, el, xnc


def test_clear_removes_results_only_and_is_one_undo_step(client, kravat):
    pid, cs, el, xnc = _cut_project(client, kravat)
    before = proj(client, pid)
    assert op(before, cs)["result"] and op(before, cs)["parts"][0]["used_qty"] > 0
    assert op(before, cs)["sheets"][0]["used_qty"] > 0
    client.post(f"/api/mes/scan/MXK:{before['number']}:{cs}:1/done")      # sex belgisi ham natija ichida
    v0 = version(client, pid)
    p = client.post(f"/api/projects/{pid}/actions/clear").json()
    # saqlanadi: operatsiyalar, detallar, listlar ro'yxati, parametrlar, sarlavha
    assert [o["id"] for o in p["operations"]] == [o["id"] for o in before["operations"]]
    assert len(op(p, cs)["parts"]) == 14 and op(p, cs)["cs_cut"] == op(before, cs)["cs_cut"]
    assert [pt["name"] for pt in op(p, cs)["parts"]] == [pt["name"] for pt in op(before, cs)["parts"]]
    assert len(op(p, cs)["sheets"]) == len(op(before, cs)["sheets"])
    assert op(p, el)["el"] == op(before, el)["el"] and op(p, xnc)["xnc"] == op(before, xnc)["xnc"]
    assert (p["name"], p["note"], p["status"], p["currency"]) == (before["name"], "muhim izoh", before["status"], before["currency"])
    assert [x["name"] for x in p["products"]] == [x["name"] for x in before["products"]]
    # tozalanadi: natija, ishlatilgan sanoqlar
    assert all(o["result"] is None for o in p["operations"])
    assert all(pt["used_qty"] == 0 for pt in op(p, cs)["parts"]) and all(sh["used_qty"] == 0 for sh in op(p, cs)["sheets"])
    assert all(pt["left_qty"] == 0 for pt in op(p, cs)["parts"])                    # kroysiz holat (UI: result yo'q — sanoq yo'q)
    assert version(client, pid) == v0 + 1
    # Ctrl+Z — natija qaytadi
    back = client.post(f"/api/projects/{pid}/undo").json()
    assert op(back, cs)["result"] is not None and op(back, cs)["result"]["total_parts"] == op(before, cs)["result"]["total_parts"]
    assert back["note"] == "muhim izoh"
    # takror «Очистить» — qayta kroy qilish mumkin
    client.post(f"/api/projects/{pid}/actions/clear")
    r = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    assert r.status_code == 200 and r.json()["total_parts"] == 19


def test_clear_on_clean_project_adds_no_history_step(client, kravat):
    pid, cs, _el = kravat
    v0 = version(client, pid)
    p = client.post(f"/api/projects/{pid}/actions/clear").json()
    assert len(op(p, cs)["parts"]) == 14 and version(client, pid) == v0           # bo'sh qadam yo'q
    assert client.post("/api/projects/yoq/actions/clear").status_code == 404


def test_clear_rolls_back_warehouse_remnants(client, kravat):
    pid, cs, _el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    added = client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").json()["added"]
    assert added
    ids = {a["id"] for a in added}
    live = lambda: {r["id"] for r in client.get("/api/remnants").json()}          # noqa: E731
    assert ids <= live()
    p = client.post(f"/api/projects/{pid}/actions/clear").json()
    assert op(p, cs)["result"] is None and not (ids & live())                      # omborga yozilganlar bekor qilindi
    back = client.post(f"/api/projects/{pid}/undo").json()
    res = op(back, cs)["result"]
    assert res is not None and res["remnants_saved"] is False and not (ids & live())   # undo ularni qayta yozmaydi


def test_clear_does_not_depend_on_order_status(client, kravat):
    """Holatga qarab bloklanmaydi (standart); UI tasdiq oynasida ogohlantiradi."""
    pid, cs, _el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    client.post(f"/api/projects/{pid}/order", json={"status": 2, "ready_date": "2026-12-01"})
    p = client.post(f"/api/projects/{pid}/actions/clear").json()
    assert p["status"] == 2 and op(p, cs)["result"] is None
    assert len(p["order_log"]) == 1                                                # tarix tegilmaydi
