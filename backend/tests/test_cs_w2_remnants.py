"""W2 — qoldiqlar: «Исп. кол-во» (mijoz olib ketgan bo'laklar omborga yozilmaydi, standart — hammasi yoziladi) va
rezerv (REM-009: tanlangan qoldiq loyihada band, boshqa loyiha ishlata olmaydi)."""
import sqlite3

import pytest

from app import db, store
from app.db import RemnantRow, SessionLocal
from app.models import CutMap, CuttingResult, Offcut, Operation, OpType, Project, StockSheet
from app.services import warehouse


def _cut(client, kravat):
    pid, cs, _ = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    return pid, cs


def _groups(client, pid, cs):
    return client.get(f"/api/projects/{pid}/operations/{cs}/remnant-groups").json()


def _op(p, oid):
    return next(o for o in p["operations"] if o["id"] == oid)


def _small_project(client, name):
    """Boshqa loyiha: LDSP16, bitta kichik detal (ombor qoldig'idan kesiladi). Qaytaradi: (project dict, cs id)."""
    p = client.post("/api/projects", json={"name": name}).json()
    pid = p["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "LDSP16", "name": "L"}).json()
    cs = p["operations"][-1]["id"]
    client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[{"name": "K", "length": 300, "width": 200}])
    return client.get(f"/api/projects/{pid}").json(), cs


def _remnant_row(client, rid):
    return next((r for r in client.get("/api/remnants?include_empty=true").json() if r["id"] == rid), None)


# ───────────────────────── «Исп. кол-во» ─────────────────────────
def test_default_writes_all_business_remnants(client, kravat):
    """Standart (taken bo'sh) — eski xulq: hamma деловой qoldiq yoziladi."""
    pid, cs = _cut(client, kravat)
    g = _groups(client, pid, cs)
    biz = [x for x in g["groups"] if x["business"]]
    assert biz and all(x["taken"] == 0 for x in biz) and not g["saved"]
    info = client.get(f"/api/projects/{pid}/operations/{cs}/remnants").json()
    assert sum(r["qty"] for r in info["remnants"]) == sum(x["qty"] for x in biz)
    out = client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").json()
    assert sum(a["qty"] for a in out["added"]) == sum(x["qty"] for x in biz)


def test_taken_remnants_are_not_written(client, kravat):
    pid, cs = _cut(client, kravat)
    biz = [x for x in _groups(client, pid, cs)["groups"] if x["business"]]
    total = sum(x["qty"] for x in biz)
    g = biz[0]
    p = client.put(f"/api/projects/{pid}/operations/{cs}/result/taken", json={"key": g["key"], "qty": g["qty"]}).json()
    assert _op(p, cs)["result"]["taken_remnants"] == {g["key"]: g["qty"]}
    after = _groups(client, pid, cs)["groups"]
    assert next(x for x in after if x["key"] == g["key"])["taken"] == g["qty"]
    info = client.get(f"/api/projects/{pid}/operations/{cs}/remnants").json()
    assert sum(r["qty"] for r in info["remnants"]) == total - g["qty"]       # olib ketilgani yozilmaydi
    out = client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").json()
    assert sum(a["qty"] for a in out["added"]) == total - g["qty"]
    # omborga yozilgandan keyin o'zgartirib bo'lmaydi; yozuvni bekor qilgach — mumkin
    r = client.put(f"/api/projects/{pid}/operations/{cs}/result/taken", json={"key": g["key"], "qty": 0})
    assert r.status_code == 409
    client.post(f"/api/projects/{pid}/operations/{cs}/remnants/rollback")
    p = client.put(f"/api/projects/{pid}/operations/{cs}/result/taken", json={"key": g["key"], "qty": 0}).json()
    assert _op(p, cs)["result"]["taken_remnants"] == {}
    info = client.get(f"/api/projects/{pid}/operations/{cs}/remnants").json()
    assert sum(r["qty"] for r in info["remnants"]) == total


def test_taken_validation_and_reset_on_recut(client, kravat):
    pid, cs = _cut(client, kravat)
    g = _groups(client, pid, cs)["groups"][0]
    url = f"/api/projects/{pid}/operations/{cs}/result/taken"
    assert client.put(url, json={"key": g["key"], "qty": g["qty"] + 1}).status_code == 400      # qoldiqlar sonidan ko'p
    assert client.put(url, json={"key": "b:1x1", "qty": 1}).status_code == 404                   # bunday qoldiq yo'q
    assert client.put(url, json={"key": g["key"], "qty": -1}).status_code == 422
    client.put(url, json={"key": g["key"], "qty": 1})
    # qayta kroy — yangi natija, «Исп. кол-во» tozalanadi
    res = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").json()
    assert res["taken_remnants"] == {}
    # natija yo'q — 400
    client.delete(f"/api/projects/{pid}/operations/{cs}/result")
    assert client.put(url, json={"key": g["key"], "qty": 0}).status_code == 400


def test_taken_partial_count_with_copies():
    """3 nusxali kartadagi bitta деловой qoldiqdan 2 tasini mijoz oladi — 1 tasi yoziladi."""
    off = Offcut(x=0, y=0, length=1200, width=700, kind="remnant", business=True, raw_length=1210, raw_width=710)
    m = CutMap(index=1, sheet_id="s", sheet_length=2750, sheet_width=1830, copies=3, offcuts=[off])
    key = warehouse.rem_key(True, 1200, 700)
    op = Operation(type=OpType.CS, name="L", result=CuttingResult(maps=[m], taken_remnants={key: 2}))
    assert warehouse.business_remnants(op) == [dict(length=1210.0, width=710.0, qty=1)]
    op.result.taken_remnants = {key: 99}                                   # ortiqcha — qirqiladi (manfiy bo'lmaydi)
    assert warehouse.business_remnants(op) == []
    op.result.taken_remnants = {}
    assert warehouse.business_remnants(op) == [dict(length=1210.0, width=710.0, qty=3)]
    g = warehouse.result_remnant_groups(op)
    assert g[0]["key"] == key and g[0]["qty"] == 3 and g[0]["taken"] == 0
    assert key == "b:120000x70000"                                          # yuzdan birlarda (frontend bilan bir xil)


def test_old_results_without_taken_still_load():
    """Eski saqlangan natija (taken_remnants maydonisiz) — standart bo'sh."""
    res = CuttingResult.model_validate({"maps": [], "total_sheets": 1})
    assert res.taken_remnants == {}


# ───────────────────────── rezerv ─────────────────────────
def test_reservation_blocks_other_projects_and_releases(client, kravat):
    pid, cs = _cut(client, kravat)
    out = client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").json()
    rid = out["added"][0]["id"]
    assert _remnant_row(client, rid)["reserved_project"] is None             # yozilgan qoldiq — erkin
    b, csb = _small_project(client, "Rezerv B")
    c, csc = _small_project(client, "Rezerv C")
    r = client.post(f"/api/projects/{b['id']}/operations/{csb}/sheets/from-remnants", json={"ids": [rid]})
    assert r.status_code == 200 and _op(r.json(), csb)["sheets"][0]["source_remnant_id"] == rid
    row = _remnant_row(client, rid)
    assert row["reserved_project"] == b["id"] and row["reserved_number"] == b["number"]
    # boshqa loyiha: qo'shib ham, qo'lda yuborib ham bo'lmaydi
    r = client.post(f"/api/projects/{c['id']}/operations/{csc}/sheets/from-remnants", json={"ids": [rid]})
    assert r.status_code == 409 and f"№{b['number']}" in r.json()["detail"]
    r = client.put(f"/api/projects/{c['id']}/operations/{csc}/sheets", json=[
        {"length": 1000, "width": 500, "qty": 1, "is_remnant": True, "source_remnant_id": rid}])
    assert r.status_code == 409
    assert _op(client.get(f"/api/projects/{c['id']}").json(), csc)["sheets"][0]["source_remnant_id"] is None
    # egasi o'z listini tahrirlay oladi (o'z rezervi)
    sheets = _op(client.get(f"/api/projects/{b['id']}").json(), csb)["sheets"]
    assert client.put(f"/api/projects/{b['id']}/operations/{csb}/sheets", json=sheets).status_code == 200
    # B listdan olib tashlasa — rezerv bo'shaydi, C ni olishi mumkin
    client.put(f"/api/projects/{b['id']}/operations/{csb}/sheets", json=[{"length": 2750, "width": 1830, "qty": 10000}])
    assert _remnant_row(client, rid)["reserved_project"] is None
    r = client.post(f"/api/projects/{c['id']}/operations/{csc}/sheets/from-remnants", json={"ids": [rid]})
    assert r.status_code == 200 and _remnant_row(client, rid)["reserved_project"] == c["id"]
    # loyiha o'chsa — rezerv bo'shaydi
    client.delete(f"/api/projects/{c['id']}")
    assert _remnant_row(client, rid)["reserved_project"] is None


def test_undo_redo_follow_the_reservation(client, kravat):
    """Rezerv loyiha listiga ergashadi: undo qoldiqni bo'shatadi, redo qayta band qiladi (hech kim egallamagan bo'lsa);
    eski loyiha (listda bor, lekin band emas) saqlanganda band qilinadi."""
    pid, cs = _cut(client, kravat)
    rid = client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").json()["added"][0]["id"]
    b, csb = _small_project(client, "Undo B")
    client.post(f"/api/projects/{b['id']}/operations/{csb}/sheets/from-remnants", json={"ids": [rid]})
    assert _remnant_row(client, rid)["reserved_project"] == b["id"]
    client.post(f"/api/projects/{b['id']}/undo")
    assert _remnant_row(client, rid)["reserved_project"] is None
    client.post(f"/api/projects/{b['id']}/redo")
    assert _remnant_row(client, rid)["reserved_project"] == b["id"]
    # boshqa loyiha band qilgan bo'lsa — redo uni tortib olmaydi
    client.post(f"/api/projects/{b['id']}/undo")
    c, csc = _small_project(client, "Undo C")
    assert client.post(f"/api/projects/{c['id']}/operations/{csc}/sheets/from-remnants", json={"ids": [rid]}).status_code == 200
    client.post(f"/api/projects/{b['id']}/redo")
    assert _remnant_row(client, rid)["reserved_project"] == c["id"]
    # eski loyiha: rezervsiz, lekin listida turgan qoldiq keyingi saqlashda band qilinadi
    client.delete(f"/api/projects/{c['id']}")
    with SessionLocal() as s:
        s.get(RemnantRow, rid).reserved_project = None
        s.commit()
    client.patch(f"/api/projects/{b['id']}", json={"note": "saqlash"})
    assert _remnant_row(client, rid)["reserved_project"] == b["id"]


def test_commit_refuses_remnant_reserved_by_other(client, kravat):
    pid, cs = _cut(client, kravat)
    rid = client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").json()["added"][0]["id"]
    b, csb = _small_project(client, "Konflikt B")
    c, csc = _small_project(client, "Konflikt C")
    client.post(f"/api/projects/{b['id']}/operations/{csb}/sheets/from-remnants", json={"ids": [rid]})
    client.post(f"/api/projects/{b['id']}/operations/{csb}/optimize?quality=fast")
    # ombor boshqaruvchisi B ning rezervini bo'shatdi, C band qildi — B ning chiqimi (commit) rad etiladi
    assert client.post("/api/remnants/reservations/release", json={"ids": [rid]}).json()["released"] == 1
    assert client.post(f"/api/projects/{c['id']}/operations/{csc}/sheets/from-remnants", json={"ids": [rid]}).status_code == 200
    r = client.post(f"/api/projects/{b['id']}/operations/{csb}/remnants/commit")
    assert r.status_code == 409 and f"№{c['number']}" in r.json()["detail"]
    qty = _remnant_row(client, rid)["qty"]
    client.delete(f"/api/projects/{c['id']}")                                  # C ketdi — B endi yoza oladi
    assert client.post(f"/api/projects/{b['id']}/operations/{csb}/remnants/commit").status_code == 200
    assert _remnant_row(client, rid)["qty"] == qty - 1


def test_stale_reservation_is_ignored(client, kravat):
    """Rezervchi loyiha yo'q (o'chgan) yoki qoldiq listida yo'q — rezerv eskirgan: ko'rsatilmaydi va to'siq emas."""
    pid, cs = _cut(client, kravat)
    rid = client.post(f"/api/projects/{pid}/operations/{cs}/remnants/commit").json()["added"][0]["id"]
    with SessionLocal() as s:
        s.get(RemnantRow, rid).reserved_project = "yoq-loyiha"
        s.commit()
    assert _remnant_row(client, rid)["reserved_project"] is None                # ro'yxatda band ko'rinmaydi
    b, csb = _small_project(client, "Eskirgan")
    assert client.post(f"/api/projects/{b['id']}/operations/{csb}/sheets/from-remnants", json={"ids": [rid]}).status_code == 200
    # mavjud loyiha band qilgan, lekin listida yo'q (qo'lda DB o'zgargan) — yangisi egallay oladi
    c, csc = _small_project(client, "Egallovchi")
    client.put(f"/api/projects/{b['id']}/operations/{csb}/sheets", json=[{"length": 2750, "width": 1830, "qty": 1}])
    with SessionLocal() as s:
        s.get(RemnantRow, rid).reserved_project = b["id"]
        s.commit()
    assert client.post(f"/api/projects/{c['id']}/operations/{csc}/sheets/from-remnants", json={"ids": [rid]}).status_code == 200
    assert _remnant_row(client, rid)["reserved_project"] == c["id"]


def _stock_rows():
    with SessionLocal() as s:
        a = RemnantRow(material_code="RSV", length=1000, width=500, thickness=16, qty=1)
        b = RemnantRow(material_code="RSV", length=900, width=500, thickness=16, qty=1, reserved_project="p-x")
        z = RemnantRow(material_code="RSV", length=800, width=500, thickness=16, qty=0)
        s.add_all([a, b, z]); s.commit()
        return a.id, b.id, z.id


def test_reserve_skips_empty_and_stale():
    ia, ib, iz = _stock_rows()
    p = Project(name="R")
    store.save_new(p)
    # p-x loyihasi yo'q → ib ning rezervi eskirgan, band qilish mumkin; soni 0 bo'lgan qoldiq o'tkazib yuboriladi
    ok, blocked = warehouse.reserve(p.id, [ia, ib, iz])
    assert ok == [ia, ib] and blocked == []
    warehouse.release([ia, ib], p.id)
    with SessionLocal() as s:
        assert s.get(RemnantRow, ia).reserved_project is None and s.get(RemnantRow, ib).reserved_project is None


def test_reserve_atomic_conflict_rolls_back():
    """Yaxlit rezerv: bittasi haqiqatan boshqa loyihada band bo'lsa — hech biri band qilinmaydi."""
    ia, ib, _iz = _stock_rows()
    holder = Project(name="Egasi", operations=[Operation(type=OpType.CS, name="L", sheets=[
        StockSheet(length=900, width=500, qty=1, is_remnant=True, source_remnant_id=ib)])])
    store.save_new(holder)
    with SessionLocal() as s:
        s.get(RemnantRow, ib).reserved_project = holder.id
        s.commit()
    me = Project(name="Men")
    store.save_new(me)
    ok, blocked = warehouse.reserve(me.id, [ia, ib])                           # yumshoq rejim: bo'sh qolgani band bo'ladi
    assert ok == [ia] and blocked == [(ib, holder.number)]
    warehouse.release([ia], me.id)
    with pytest.raises(warehouse.WarehouseConflict) as e:
        warehouse.reserve(me.id, [ia, ib], atomic=True)
    assert f"№{holder.number}" in str(e.value)
    with SessionLocal() as s:
        assert s.get(RemnantRow, ia).reserved_project is None                  # atomik: ia ham band qilinmagan
        assert s.get(RemnantRow, ib).reserved_project == holder.id
    store.delete(holder.id)                                                    # egasi ketdi — rezerv bo'shaydi
    with SessionLocal() as s:
        assert s.get(RemnantRow, ib).reserved_project is None


# ───────────────────────── migratsiya ─────────────────────────
def test_migration_adds_reserved_project_column(tmp_path, monkeypatch):
    """Eski bazada `remnants.reserved_project` yo'q — `_migrate` uni qo'shadi (SQLite; PostgreSQL ham ALTER TABLE ADD COLUMN)."""
    from sqlalchemy import create_engine, inspect
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE remnants (id INTEGER PRIMARY KEY AUTOINCREMENT, material_code VARCHAR(100), length FLOAT, "
                "width FLOAT, thickness FLOAT, qty INTEGER, source_project VARCHAR(32), note TEXT)")
    con.execute("INSERT INTO remnants (material_code, length, width, thickness, qty) VALUES ('X', 1000, 500, 16, 2)")
    con.commit(); con.close()
    eng = create_engine(f"sqlite:///{path}")
    monkeypatch.setattr(db, "engine", eng)
    db._migrate()
    cols = {c["name"] for c in inspect(eng).get_columns("remnants")}
    assert "reserved_project" in cols and {"material_name", "source_number", "source_op", "created_at"} <= cols
    with eng.connect() as c:
        assert c.exec_driver_sql("SELECT qty, reserved_project FROM remnants").fetchall() == [(2, None)]
    db._migrate()                                                              # qayta chaqirish zararsiz
    eng.dispose()
