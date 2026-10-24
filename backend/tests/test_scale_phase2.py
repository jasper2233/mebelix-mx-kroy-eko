"""2-bosqich (docs/mebelix/Y_MASSHTAB_ABONENTLAR.md): hisoblar navbati (ishchi jarayon), loyihalar ro'yxati sahifalab,
siqilgan tarix, katalog kaliti korxona bo'yicha, sozlama keshini jarayonlararo tozalash."""
from __future__ import annotations

import threading
import time

import pytest

from app import store, tenant
from app.db import IS_PG, CatalogItemRow, JobRow, ProjectHistoryRow, SessionLocal, ckey
from app.services import cn_jobs, compute

from tests.test_cn_w16_api import _mk as _cn_mk


class _Worker:
    """Test ichidagi hisob ishchisi (app.worker.child kabi, lekin oqimda)."""

    def __init__(self):
        self.stop = threading.Event()
        self.done: list[str] = []
        self.t = threading.Thread(target=self._loop, daemon=True)

    def _loop(self):
        while not self.stop.is_set():
            row = compute.claim("test:1", compute.kinds() + ["cn"])
            if row is None:
                time.sleep(0.01)
                continue
            if row.kind == "cn":
                cn_jobs.run_claimed(row)
            else:
                compute.execute(row)
            self.done.append(row.kind)

    def __enter__(self):
        self.t.start()
        return self

    def __exit__(self, *_a):
        self.stop.set()
        self.t.join(5)


@pytest.fixture()
def queue_mode(monkeypatch):
    monkeypatch.setenv("MEBELIX_COMPUTE", "queue")
    monkeypatch.setattr(compute, "CLAIM_WAIT", 5.0)


def _jobs_left() -> int:
    with tenant.system(), SessionLocal() as s:
        return s.query(JobRow).filter(JobRow.kind != "cn").count()


# ───────────────────────── Hisoblar navbati ─────────────────────────
def test_cut_through_worker_same_answer_as_inline(client, kravat, queue_mode, monkeypatch):
    pid, cs, _el = kravat
    with _Worker() as w:
        r = client.post(f"/api/projects/{pid}/operations/{cs}/optimize", params={"quality": "fast"})
        assert r.status_code == 200, r.text
        q = r.json()
        assert w.done == ["cut"]
    assert q["total_sheets"] >= 1 and q["maps"] and not q["unplaced"]
    # natija loyihada saqlangan (ishchi jarayon yozgan) va javob bilan bir xil
    p = client.get(f"/api/projects/{pid}").json()
    op = next(o for o in p["operations"] if o["id"] == cs)
    assert op["result"]["total_sheets"] == q["total_sheets"] and len(op["result"]["maps"]) == len(q["maps"])
    assert _jobs_left() == 0                       # kutuvchi yozuvni o'chiradi
    # xuddi shu so'rov navbatsiz (inline) — javob tuzilishi bir xil
    monkeypatch.setenv("MEBELIX_COMPUTE", "inline")
    i = client.post(f"/api/projects/{pid}/operations/{cs}/optimize", params={"quality": "fast"}).json()
    assert set(i) == set(q) and i["total_sheets"] == q["total_sheets"]


def test_queue_http_error_keeps_code_and_text(client, queue_mode, monkeypatch):
    pid = client.post("/api/projects", json={"name": "Bo'sh"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "L16", "name": "LDSP"}).json()
    cs = p["operations"][-1]["id"]
    with _Worker() as w:
        r = client.post(f"/api/projects/{pid}/operations/{cs}/optimize")
        assert w.done == ["cut"]
    monkeypatch.setattr(compute, "CLAIM_WAIT", 0.2)
    own = client.post(f"/api/projects/{pid}/operations/{cs}/optimize")   # navbat yoqiq, ishchisiz → veb-jarayon o'zi
    assert r.status_code == own.status_code == 400 and r.json()["detail"] == own.json()["detail"]
    assert _jobs_left() == 0


def test_no_worker_falls_back_to_web_process(client, kravat, queue_mode, monkeypatch):
    monkeypatch.setattr(compute, "CLAIM_WAIT", 0.2)
    pid, cs, _el = kravat
    t = time.time()
    r = client.post(f"/api/projects/{pid}/operations/{cs}/optimize", params={"quality": "fast"})
    assert r.status_code == 200 and r.json()["total_sheets"] >= 1
    assert time.time() - t < 30
    assert _jobs_left() == 0


def test_variants_and_cut_all_through_worker(client, kravat, queue_mode):
    pid, cs, _el = kravat
    with _Worker() as w:
        v = client.post(f"/api/projects/{pid}/operations/{cs}/variants")
        a = client.post(f"/api/projects/{pid}/actions/optimize-all", params={"quality": "fast"})
    assert v.status_code == 200 and isinstance(v.json(), (list, dict))
    assert a.status_code == 200, a.text
    body = a.json()
    assert body["project"]["id"] == pid and any("sheets" in r for r in body["results"])
    assert w.done == ["variants", "cut_all"]


def test_cn_job_through_worker(client, queue_mode):
    pid, oid = _cn_mk(client)
    with _Worker() as w:
        j = client.post(f"/api/projects/{pid}/operations/{oid}/cn/jobs", params={"quality": "fast"})
        assert j.status_code == 200 and j.json()["state"] == "running"          # navbatda — UI uchun «running»
        jid = j.json()["id"]
        # band: ikkinchi boshlash — 409
        assert client.post(f"/api/projects/{pid}/operations/{oid}/cn/jobs").status_code == 409
        t = time.time()
        while time.time() - t < 60:
            s = client.get(f"/api/projects/{pid}/operations/{oid}/cn/jobs/{jid}").json()
            if s["state"] != "running":
                break
            time.sleep(0.05)
        assert s["state"] == "done", s
        t = time.time()                    # holat «done» ishchi `done` ro'yxatiga yozishidan oldin ko'rinishi mumkin
        while "cn" not in w.done and time.time() - t < 5:
            time.sleep(0.02)
        assert "cn" in w.done
    op = next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)
    assert op["result"]["kind"] == "nest"


def test_cn_job_queued_cancel_and_fallback(client, queue_mode, monkeypatch):
    pid, oid = _cn_mk(client)
    # ishchisiz: bekor qilish navbatdagi ishni darhol to'xtatadi
    jid = client.post(f"/api/projects/{pid}/operations/{oid}/cn/jobs", params={"quality": "fast"}).json()["id"]
    assert client.delete(f"/api/projects/{pid}/operations/{oid}/cn/jobs/{jid}").status_code in (200, 204)
    assert client.get(f"/api/projects/{pid}/operations/{oid}/cn/jobs/{jid}").json()["state"] == "cancelled"
    # ishchisiz: CLAIM_WAIT dan keyin veb-jarayon o'zi bajaradi
    monkeypatch.setattr(compute, "CLAIM_WAIT", 0.2)
    jid = client.post(f"/api/projects/{pid}/operations/{oid}/cn/jobs", params={"quality": "fast"}).json()["id"]
    t = time.time()
    while time.time() - t < 60:
        s = client.get(f"/api/projects/{pid}/operations/{oid}/cn/jobs/{jid}").json()
        if s["state"] != "running":
            break
        time.sleep(0.05)
    assert s["state"] == "done", s


# ───────────────────────── Loyihalar ro'yxati ─────────────────────────
def test_project_list_paging_and_total(client):
    fid = client.post("/api/folders", json={"name": "Sahifalash"}).json()["id"]
    for i in range(7):
        client.post("/api/projects", json={"name": f"Sahifa {i}", "folder_id": fid})
    full = client.get("/api/projects", params={"folder_id": fid}).json()
    assert len(full) == 7 and "data" not in full[0] and {"id", "number", "name", "cost", "updated_at"} <= set(full[0])
    r = client.get("/api/projects", params={"folder_id": fid, "limit": 3, "offset": 3})
    assert r.headers["x-total-count"] == "7"
    assert [p["id"] for p in r.json()] == [p["id"] for p in full[3:6]]
    assert "x-total-count" not in client.get("/api/projects", params={"folder_id": fid}).headers


# ───────────────────────── Siqilgan tarix ─────────────────────────
def test_history_is_compressed_and_undo_works(client):
    pid = client.post("/api/projects", json={"name": "Tarix 1"}).json()["id"]
    client.patch(f"/api/projects/{pid}", json={"name": "Tarix 2"})
    with SessionLocal() as s:
        rows = s.query(ProjectHistoryRow).filter(ProjectHistoryRow.project_id == pid).order_by(ProjectHistoryRow.version).all()
        assert rows and all(h.zdata is not None and h.data is None for h in rows)
        assert store.history_data(rows[-1])["name"] == "Tarix 2"
    assert client.post(f"/api/projects/{pid}/undo").json()["name"] == "Tarix 1"
    assert client.post(f"/api/projects/{pid}/redo").json()["name"] == "Tarix 2"


def test_legacy_history_rows_are_packed(client):
    pid = client.post("/api/projects", json={"name": "Eski tarix"}).json()["id"]
    with SessionLocal() as s:                           # 2-bosqichdan oldingi ko'rinish: siqilmagan JSON
        for h in s.query(ProjectHistoryRow).filter(ProjectHistoryRow.project_id == pid):
            h.data, h.zdata = store.history_data(h), None
        s.commit()
    client.patch(f"/api/projects/{pid}", json={"name": "Eski tarix 2"})
    assert client.post(f"/api/projects/{pid}/undo").json()["name"] == "Eski tarix"     # aralash: eski + yangi
    assert store.pack_history_backlog() >= 1
    with SessionLocal() as s:
        assert s.query(ProjectHistoryRow).filter(ProjectHistoryRow.project_id == pid, ProjectHistoryRow.zdata.is_(None)).count() == 0
    assert client.post(f"/api/projects/{pid}/redo").json()["name"] == "Eski tarix 2"


# ───────────────────────── Katalog kaliti ─────────────────────────
def test_catalog_same_id_in_two_companies():
    from tests.test_tenancy import _mk_company
    c2 = _mk_company("Katalog B")
    for cid, name in ((1, "Bizniki"), (c2, "Ularniki")):
        with tenant.use(cid), SessionLocal() as s:
            s.add(CatalogItemRow(id="MES-777", kind="sheet", code="L16", name=name))
            s.commit()
    for cid, name in ((1, "Bizniki"), (c2, "Ularniki")):
        with tenant.use(cid), SessionLocal() as s:
            assert s.get(CatalogItemRow, ckey("MES-777")).name == name
    with tenant.use(1), SessionLocal() as s:
        s.query(CatalogItemRow).filter(CatalogItemRow.id == "MES-777", CatalogItemRow.company_id == 1).delete()
        s.commit()


# ───────────────────────── Sozlama keshi ─────────────────────────
@pytest.mark.skipif(not IS_PG, reason="NOTIFY — faqat PostgreSQL")
def test_settings_change_notifies_other_processes():
    from app.services import notify, settings
    got = threading.Event()
    notify.on(notify.SETTINGS, lambda p: got.set() if p == "xnc_tools" else None)
    settings.listen()
    time.sleep(0.5)                                     # tinglovchi ulanib olsin
    settings._changed("xnc_tools")
    assert got.wait(5)
