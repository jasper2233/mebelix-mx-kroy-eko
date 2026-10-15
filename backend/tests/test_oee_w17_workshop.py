"""OEE (W17) + sex rejimi: karta «bajarildi» (`/mes/scan/{qr}/done`) avtomatik `run` hodisasi yozadi (ixtiyoriy, xatosi skanerni
buzmaydi); «To'xtash» — ochiq to'xtash boshlash/yopish."""
from __future__ import annotations

import time

import pytest

from app.services import oee
from oee_w17_util import add_machine, add_shift, fresh


@pytest.fixture()
def shop(client, kravat):
    """Kroy qilingan loyiha: (client, qr_prefix, pid, cs_id, project)."""
    fresh(tz=0)
    pid, cs, _el = kravat
    assert client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").status_code == 200
    p = client.get(f"/api/projects/{pid}").json()
    yield client, f"MXK:{p['number']}:{cs}", p, cs
    fresh(tz=0)


def op_of(p, cs):
    return next(o for o in p["operations"] if o["id"] == cs)


def events(client, **q):
    return client.get("/api/oee/events", params=q).json()["items"]


def test_done_writes_run_event_with_card_geometry(shop):
    c, qr, p, cs = shop
    add_machine(c, "saw1")
    m = op_of(p, cs)["result"]["maps"][0]
    r = c.post(f"/api/mes/scan/{qr}:1/done", params={"machine": "saw1"})
    assert r.status_code == 200 and r.json()["done"] == 1
    ev = events(c)
    assert len(ev) == 1
    e = ev[0]
    assert (e["type"], e["machine"], e["qty"], e["source"]) == ("run", "saw1", 1, "workshop")
    assert e["start"] is None and e["end"].endswith("Z")                       # boshlanish — hisobda avvalgi hodisadan
    assert e["project_number"] == p["number"] and e["project_id"] == p["id"] and e["op_id"] == cs and e["map_index"] == 1
    assert e["cut_length_m"] == pytest.approx(m["cut_length_m"]) and e["cuts"] == m["cuts_count"]
    assert e["parts_per_sheet"] == m["parts_count"] and e["sheets_per_pack"] >= 1
    # material samaradorligi KPI uchun kartadan maydonlar (OEE dan alohida)
    assert e["sheet_area_m2"] == pytest.approx(m["sheet_area_m2"]) and e["parts_area_m2"] == pytest.approx(m["parts_area_m2"])
    assert e["remnant_area_m2"] == pytest.approx(m["remnant_area_m2"])
    import calendar
    assert abs(time.time() - calendar.timegm(time.strptime(e["end"], "%Y-%m-%dT%H:%M:%SZ"))) < 120     # tugash vaqti — hozir (UTC)


def test_done_count_and_clamp_define_event_quantity(shop):
    c, qr, p, cs = shop
    add_machine(c, "saw1")
    copies = op_of(p, cs)["result"]["maps"][0]["copies"]
    r = c.post(f"/api/mes/scan/{qr}:1/done", params={"machine": "saw1", "count": copies + 5})
    assert r.json()["done"] == copies                                           # karta nusxalari bilan cheklangan
    assert [e["qty"] for e in events(c)] == [copies]                           # hodisa — haqiqatan qo'shilgan soni
    again = c.post(f"/api/mes/scan/{qr}:1/done", params={"machine": "saw1"})    # hammasi bajarilgan — o'zgarish yo'q
    assert again.status_code == 200 and again.json()["done"] == copies
    assert len(events(c)) == 1                                                  # qo'shimcha hodisa yozilmaydi
    c.post(f"/api/mes/scan/{qr}:1/done", params={"machine": "saw1", "count": -1})   # orqaga qaytarish — hodisa yo'q
    assert len(events(c)) == 1


def test_no_oee_machines_means_no_events_and_scan_works(shop):
    c, qr, p, cs = shop
    assert c.get("/api/oee/machines").json() == []
    r = c.post(f"/api/mes/scan/{qr}:1/done")
    assert r.status_code == 200 and r.json()["done"] == 1
    assert events(c) == []


def test_machine_resolution_rules(shop):
    c, qr, p, cs = shop
    add_machine(c, "saw1")
    add_machine(c, "saw2")
    add_machine(c, "edge1", kind="edge")

    def press(machine=None):
        """Karta belgisini 0 ga qaytarib (hodisa yozilmaydi), keyin bosadi — har bosish haqiqiy +1 bo'lsin."""
        c.post(f"/api/mes/scan/{qr}:1/done", params={"count": -99})
        r = c.post(f"/api/mes/scan/{qr}:1/done", params={"machine": machine} if machine else None)
        assert r.status_code == 200
        return r
    # ikki faol «saw» va stanok ko'rsatilmagan — qaysi biri noaniq: hodisa yozilmaydi
    press()
    assert events(c) == []
    # noma'lum stanok — hodisa yo'q, skaner ishlaydi
    assert press("yoq").json()["done"] == 1 and events(c) == []
    # ko'rsatilgan stanok
    press("saw2")
    assert [e["machine"] for e in events(c)] == ["saw2"]
    # nofaol stanok — hodisa yo'q
    c.put("/api/oee/machines/saw2", json=dict(active=False))
    n = len(events(c))
    press("saw2")
    assert len(events(c)) == n
    # yagona faol «saw» — stanok ko'rsatilmasa ham shu (kromka stanogi hisobga olinmaydi)
    c.put("/api/oee/machines/saw2", json=dict(active=True))
    c.delete("/api/oee/machines/saw1", params={"force": True})
    n = len(events(c))
    press()
    assert len(events(c)) == n + 1 and events(c)[0]["machine"] == "saw2"


def test_oee_failure_never_breaks_scan(shop, monkeypatch):
    c, qr, p, cs = shop
    add_machine(c, "saw1")

    def boom(*a, **k):
        raise RuntimeError("OEE buzildi")
    monkeypatch.setattr(oee, "record_sheet_done", boom)
    r = c.post(f"/api/mes/scan/{qr}:1/done", params={"machine": "saw1"})
    assert r.status_code == 200 and r.json()["done"] == 1
    assert c.get(f"/api/mes/scan/{qr}:1").json()["map"]["done"] == 1             # sex holati saqlandi
    assert events(c) == []


def test_part_label_scan_still_rejected(shop):
    c, qr, p, cs = shop
    add_machine(c, "saw1")
    assert c.post(f"/api/mes/scan/MXK:{p['number']}:1:1/4/done", params={"machine": "saw1"}).status_code == 400
    assert events(c) == []


def test_workshop_events_feed_dashboard(shop):
    c, qr, p, cs = shop
    add_machine(c, "saw1")
    add_shift(c, "00:00", "23:59")                           # sutka bo'yi (test kuni/soatiga bog'lanmaydi)
    for _ in range(3):
        c.post(f"/api/mes/scan/{qr}:1/done", params={"machine": "saw1"})
    now = time.time()
    r = c.get("/api/oee/summary", params={"machine": "saw1", "from": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - 7200)),
                                          "to": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + 3600))})
    s = r.json()
    m = s["machines"][0]
    assert r.status_code == 200 and m["has_data"] and m["produced"] >= 1                   # sex hodisalari hisobga olinadi
    assert m["ideal_cycle_s"] is not None                                                  # karta geometriyasidan ideal sikl
    assert not any(w["code"] == "no_ideal" for w in s["warnings"])


# ───────────────────────── To'xtash (sex rejimi) ─────────────────────────
def test_downtime_start_stop_cycle(client):
    fresh(tz=0)
    add_machine(client, "saw1")
    assert client.get("/api/oee/downtime/open", params={"machine": "saw1"}).json()["open"] is None
    r = client.post("/api/oee/downtime/start", json=dict(machine="saw1", reason="material_wait", note="list kutilmoqda"))
    assert r.status_code == 201
    e = r.json()
    assert e["type"] == "downtime" and e["open"] is True and e["end"] is None and e["source"] == "workshop"
    assert e["reason"] == "material_wait" and e["note"] == "list kutilmoqda" and e["start"].endswith("Z")
    o = client.get("/api/oee/downtime/open", params={"machine": "saw1"}).json()["open"]
    assert o["id"] == e["id"]
    # ikkinchi ochiq to'xtash — rad etiladi
    assert client.post("/api/oee/downtime/start", json=dict(machine="saw1", reason="setup")).status_code == 409
    st = client.post("/api/oee/downtime/stop", json=dict(machine="saw1"))
    assert st.status_code == 200 and st.json()["open"] is False and st.json()["end"] >= st.json()["start"]
    assert client.get("/api/oee/downtime/open", params={"machine": "saw1"}).json()["open"] is None
    assert client.post("/api/oee/downtime/stop", json=dict(machine="saw1")).status_code == 404
    assert len(events(client, type="downtime")) == 1
    # yangi to'xtash yana boshlanishi mumkin
    assert client.post("/api/oee/downtime/start", json=dict(machine="saw1", reason="setup")).status_code == 201
    fresh(tz=0)


def test_downtime_start_validation(client):
    fresh(tz=0)
    add_machine(client, "saw1")
    assert client.post("/api/oee/downtime/start", json=dict(machine="yoq", reason="setup")).status_code == 400
    assert client.post("/api/oee/downtime/start", json=dict(machine="saw1", reason="yoq")).status_code == 400
    assert client.post("/api/oee/downtime/start", json=dict(machine="saw1", reason="chip")).status_code == 400      # brak sababi
    assert client.post("/api/oee/downtime/start", json=dict(machine="saw1")).status_code == 400
    assert events(client) == []
    fresh(tz=0)


def test_open_downtime_counts_until_now_in_dashboard(client):
    fresh(tz=0)
    add_machine(client, "saw1")
    add_shift(client, "00:00", "23:59")
    client.post("/api/oee/downtime/start", json=dict(machine="saw1", reason="breakdown"))
    now = time.time()
    s = client.get("/api/oee/summary", params={
        "machine": "saw1", "from": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - 3600)),
        "to": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + 3600))}).json()
    assert s["machines"][0]["has_data"] and {"code": "open_downtime", "count": 1} in s["warnings"]
    fresh(tz=0)
