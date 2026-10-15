"""OEE (W17) API: hodisalarni qabul qilish (idempotentlik, ommaviy), validatsiya, rollar, CRUD, hisob-kitob endpointlari, CSV, demo."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.services import oee
from oee_w17_util import add_machine, add_shift, epoch, fresh, monday, z

SECRET = "s3cret-for-tests-only-0123456789"


@pytest.fixture()
def api(client):
    fresh(tz=0)
    yield client
    fresh(tz=0)


def run_ev(machine="m1", d=None, start=(8, 0), end=(9, 0), **kw):
    d = d or monday()
    body = dict(type="run", machine=machine, end=z(d, *end), qty=2, cut_length_m=10, cuts=18)
    if start:
        body["start"] = z(d, *start)
    body.update(kw)
    return body


def down_ev(machine="m1", d=None, start=(9, 0), end=(9, 30), reason="setup", **kw):
    d = d or monday()
    body = dict(type="downtime", machine=machine, start=z(d, *start), reason=reason)
    if end:
        body["end"] = z(d, *end)
    body.update(kw)
    return body


# ───────────────────────── Qabul qilish: bitta hodisa, idempotentlik ─────────────────────────
def test_post_single_event_created_then_idempotent(api):
    add_machine(api, "m1")
    body = run_ev(external_id="mes-1")
    r = api.post("/api/oee/events", json=body)
    assert r.status_code == 201
    j = r.json()
    assert j["status"] == "created" and j["event"]["type"] == "run" and j["event"]["qty"] == 2
    assert j["event"]["start"].endswith("Z") and j["event"]["sheets_per_pack"] == 1 and j["event"]["reject_qty"] == 0
    # qayta yuborish (MES retry) — dublikat yaratilmaydi
    r2 = api.post("/api/oee/events", json=body)
    assert r2.status_code == 200 and r2.json()["status"] == "unchanged" and r2.json()["id"] == j["id"]
    assert api.get("/api/oee/events").json()["total"] == 1
    # o'zgargan maydon — shu hodisa yangilanadi
    r3 = api.post("/api/oee/events", json={**body, "qty": 5, "note": "tuzatildi"})
    assert r3.status_code == 200 and r3.json()["status"] == "updated" and r3.json()["id"] == j["id"]
    assert r3.json()["event"]["qty"] == 5 and r3.json()["event"]["note"] == "tuzatildi"
    assert api.get("/api/oee/events").json()["total"] == 1


def test_external_id_cannot_switch_type_or_machine(api):
    add_machine(api, "m1")
    add_machine(api, "m2")
    assert api.post("/api/oee/events", json=run_ev(external_id="x1")).status_code == 201
    r = api.post("/api/oee/events", json=run_ev(machine="m2", external_id="x1"))
    assert r.status_code == 409 and "external_id" in r.json()["detail"]
    r = api.post("/api/oee/events", json=down_ev(external_id="x1"))
    assert r.status_code == 409


def test_open_downtime_is_closed_by_resending_same_external_id(api):
    add_machine(api, "m1")
    r = api.post("/api/oee/events", json=down_ev(end=None, external_id="d1"))
    assert r.status_code == 201 and r.json()["event"]["open"] is True and r.json()["event"]["end"] is None
    r2 = api.post("/api/oee/events", json=down_ev(end=(9, 40), external_id="d1"))
    assert r2.status_code == 200 and r2.json()["status"] == "updated"
    assert r2.json()["event"]["open"] is False and r2.json()["event"]["end"].endswith("09:40:00Z")
    assert api.get("/api/oee/events").json()["total"] == 1


def test_events_without_external_id_are_never_merged(api):
    add_machine(api, "m1")
    assert api.post("/api/oee/events", json=run_ev()).status_code == 201
    assert api.post("/api/oee/events", json=run_ev()).status_code == 201
    assert api.get("/api/oee/events").json()["total"] == 2


def test_reject_event_accepts_start_only_and_defaults(api):
    add_machine(api, "m1")
    d = monday()
    r = api.post("/api/oee/events", json=dict(type="reject", machine="m1", start=z(d, 10), reason="chip"))
    assert r.status_code == 201
    e = r.json()["event"]
    assert e["end"] == z(d, 10) and e["qty"] == 1 and e["unit"] == "part" and e["reason"] == "chip" and e["start"] is None


# ───────────────────────── Ommaviy qabul ─────────────────────────
def test_batch_partial_success_and_all_failed(api):
    add_machine(api, "m1")
    items = [run_ev(external_id="a"), run_ev(machine="yoq", external_id="b"), down_ev(external_id="c")]
    r = api.post("/api/oee/events", json=items)
    assert r.status_code == 200
    j = r.json()
    assert (j["created"], j["errors"], j["updated"], j["unchanged"]) == (2, 1, 0, 0)
    assert [x["status"] for x in j["results"]] == ["created", "error", "created"]
    assert j["results"][1]["index"] == 1 and "yoq" in j["results"][1]["error"]
    # {"events": [...]} shakli va qayta yuborish — idempotent
    r2 = api.post("/api/oee/events", json={"events": items})
    assert r2.json()["unchanged"] == 2 and r2.json()["errors"] == 1 and r2.status_code == 200
    # hammasi xato → 422
    bad = api.post("/api/oee/events", json=[run_ev(machine="yoq"), run_ev(machine="yoq2")])
    assert bad.status_code == 422 and bad.json()["errors"] == 2
    assert api.get("/api/oee/events").json()["total"] == 2


def test_batch_limit_500(api):
    add_machine(api, "m1")
    d = monday()
    base = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)

    def many(n):
        return [dict(type="run", machine="m1", end=(base + timedelta(minutes=i)).strftime("%Y-%m-%dT%H:%M:%SZ"), qty=1,
                     external_id=f"b{i}") for i in range(n)]
    r = api.post("/api/oee/events", json=many(500))
    assert r.status_code == 200 and r.json()["created"] == 500
    assert api.post("/api/oee/events", json=many(500)).json()["unchanged"] == 500        # to'liq retry
    r = api.post("/api/oee/events", json=many(501))
    assert r.status_code == 400 and "500" in r.json()["detail"]
    assert api.post("/api/oee/events", json=[]).status_code == 200                      # bo'sh ro'yxat — xato emas


def test_duplicate_external_id_inside_one_batch_last_wins(api):
    add_machine(api, "m1")
    r = api.post("/api/oee/events", json=[run_ev(external_id="z", qty=1), run_ev(external_id="z", qty=7)])
    assert r.status_code == 200
    j = r.json()
    assert j["created"] == 1 and j["updated"] == 1 and j["results"][0]["id"] == j["results"][1]["id"]
    assert api.get(f"/api/oee/events/{j['results'][0]['id']}").json()["qty"] == 7


# ───────────────────────── Validatsiya ─────────────────────────
D = monday()
INVALID = [
    ("naive vaqt", dict(type="run", machine="m1", end="2026-09-01T10:00:00")),
    ("end <= start", dict(type="run", machine="m1", start=z(D, 10), end=z(D, 9))),
    ("run end yo'q", dict(type="run", machine="m1", start=z(D, 9))),
    ("run 25 soat", dict(type="run", machine="m1", start=z(D, 0), end=z(D + timedelta(days=1), 1))),
    ("run qty 0", dict(type="run", machine="m1", end=z(D, 9), qty=0)),
    ("downtime sababsiz", dict(type="downtime", machine="m1", start=z(D, 9), end=z(D, 10))),
    ("noma'lum sabab", dict(type="downtime", machine="m1", start=z(D, 9), end=z(D, 10), reason="yoq-sabab")),
    ("brak sababi to'xtashga", dict(type="downtime", machine="m1", start=z(D, 9), end=z(D, 10), reason="chip")),
    ("to'xtash sababi brakka", dict(type="reject", machine="m1", end=z(D, 9), reason="setup")),
    ("downtime end <= start", dict(type="downtime", machine="m1", start=z(D, 9), end=z(D, 9), reason="setup")),
    ("noma'lum stanok", dict(type="run", machine="yoq", end=z(D, 9))),
    ("noma'lum maydon", dict(type="run", machine="m1", end=z(D, 9), reasn="x")),
    ("noto'g'ri tur", dict(type="boshqa", machine="m1", end=z(D, 9))),
    ("kelajak", dict(type="run", machine="m1", end=(datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ"))),
    ("1999 yil", dict(type="run", machine="m1", end="1999-01-01T00:00:00Z")),
    ("manfiy kesim", dict(type="run", machine="m1", end=z(D, 9), cuts=-1)),
    ("NaN uzunlik", dict(type="run", machine="m1", end=z(D, 9), cut_length_m="nan")),
    ("brak birligi", dict(type="reject", machine="m1", end=z(D, 9), unit="kg")),
    ("stanok bo'sh", dict(type="run", machine="", end=z(D, 9))),
]


@pytest.mark.parametrize("name,body", INVALID, ids=[x[0] for x in INVALID])
def test_invalid_events_are_rejected_with_message(api, name, body):
    add_machine(api, "m1")
    r = api.post("/api/oee/events", json=body)
    assert r.status_code in (400, 422), (name, r.text)
    assert api.get("/api/oee/events").json()["total"] == 0


def test_validation_messages_follow_accept_language(api):
    add_machine(api, "m1")
    body = dict(type="run", machine="m1", end="2026-09-01T10:00:00")
    ru = api.post("/api/oee/events", json=body, headers={"Accept-Language": "ru"}).json()["detail"]
    uz = api.post("/api/oee/events", json=body, headers={"Accept-Language": "uz"}).json()["detail"]
    assert "часового пояса" in ru and "soat poyasi" in uz


def test_inactive_reason_is_rejected_for_new_events(api):
    add_machine(api, "m1")
    assert api.put("/api/oee/reasons/setup", json=dict(active=False)).status_code == 200
    r = api.post("/api/oee/events", json=down_ev())
    assert r.status_code == 400
    assert api.put("/api/oee/reasons/setup", json=dict(active=True)).status_code == 200
    assert api.post("/api/oee/events", json=down_ev()).status_code == 201


def test_body_must_be_object_or_list(api):
    assert api.post("/api/oee/events", json="matn").status_code == 422
    assert api.post("/api/oee/events", json=5).status_code == 422


# ───────────────────────── Hodisalar ro'yxati / tahrir ─────────────────────────
def test_list_filter_patch_delete(api):
    add_machine(api, "m1")
    add_machine(api, "m2")
    d = monday()
    api.post("/api/oee/events", json=[run_ev(external_id="r1"), run_ev(machine="m2", start=None, end=(11, 0), external_id="r2"),
                                      down_ev(), dict(type="reject", machine="m1", end=z(d, 9, 30), qty=2, reason="chip")])
    allv = api.get("/api/oee/events").json()
    assert allv["total"] == 4
    times = [e["end"] or e["start"] for e in allv["items"]]
    assert times == sorted(times, reverse=True) and allv["items"][0]["machine"] == "m2"        # eng yangisi birinchi
    assert api.get("/api/oee/events", params={"machine": "m2"}).json()["total"] == 1
    assert api.get("/api/oee/events", params={"type": "downtime"}).json()["total"] == 1
    assert api.get("/api/oee/events", params={"reason": "chip"}).json()["total"] == 1
    assert api.get("/api/oee/events", params={"type": "xato"}).status_code == 400
    page = api.get("/api/oee/events", params={"limit": 2, "offset": 2}).json()
    assert page["total"] == 4 and len(page["items"]) == 2
    rng = api.get("/api/oee/events", params={"from": z(d, 10), "to": z(d, 12)}).json()
    assert {e["machine"] for e in rng["items"]} == {"m2"}
    eid = allv["items"][0]["id"]
    # tahrir: qty o'zgartiriladi, turi — yo'q
    ev = api.get("/api/oee/events", params={"type": "run", "machine": "m1"}).json()["items"][0]
    p = api.patch(f"/api/oee/events/{ev['id']}", json=dict(qty=9, note="qo'lda"))
    assert p.status_code == 200 and p.json()["qty"] == 9 and p.json()["note"] == "qo'lda" and p.json()["cuts"] == 18
    assert api.patch(f"/api/oee/events/{ev['id']}", json=dict(type="downtime")).status_code == 400
    assert api.patch(f"/api/oee/events/{ev['id']}", json=dict(qty=0)).status_code == 400
    assert api.patch("/api/oee/events/999999", json=dict(qty=1)).status_code == 404
    assert api.delete(f"/api/oee/events/{eid}").status_code == 200
    assert api.get(f"/api/oee/events/{eid}").status_code == 404
    assert api.delete(f"/api/oee/events/{eid}").status_code == 404
    assert api.get("/api/oee/events").json()["total"] == 3


# ───────────────────────── Stanoklar ─────────────────────────
def test_machine_crud_and_pp_link(api):
    r = api.post("/api/oee/machines", json=dict(pp_key="scm_wincut"))
    assert r.status_code == 201
    m = r.json()
    assert m["key"] == "scm_wincut" and m["name"] == "SCM WinCut" and m["kind"] == "saw" and m["pp_name"] == "SCM WinCut"
    assert (m["cut_speed_mm_s"], m["cut_change_s"], m["sheet_load_s"]) == (1000.0, 5.0, 25.0) and m["active"] is True
    assert api.post("/api/oee/machines", json=dict(pp_key="scm_wincut")).status_code == 409
    assert api.post("/api/oee/machines", json=dict(key="x y")).status_code == 400
    assert api.post("/api/oee/machines", json=dict(pp_key="yoq-stanok")).status_code == 400
    assert api.post("/api/oee/machines", json=dict(name="kalitsiz")).status_code == 400
    assert api.post("/api/oee/machines", json=dict(key="m1", cut_speed_mm_s=0)).status_code == 422
    cnc = api.post("/api/oee/machines", json=dict(pp_key="woodwop")).json()
    assert cnc["kind"] == "cnc"
    erkin = api.post("/api/oee/machines", json=dict(key="edge-1", name="Kromka 1", kind="edge", ideal_unit_s=45)).json()
    assert erkin["kind"] == "edge" and erkin["ideal_unit_s"] == 45 and erkin["pp_key"] is None
    # yangilash: faqat berilgan maydonlar; null — standart/olib tashlash
    u = api.patch("/api/oee/machines/edge-1", json=dict(cut_speed_mm_s=1500, ideal_unit_s=None, note="eslatma"))
    assert u.status_code == 200 and u.json()["cut_speed_mm_s"] == 1500 and u.json()["ideal_unit_s"] is None and u.json()["name"] == "Kromka 1"
    assert api.put("/api/oee/machines/edge-1", json=dict(active=False)).json()["active"] is False
    assert api.get("/api/oee/machines", params={"active_only": True}).json() and \
        "edge-1" not in [x["key"] for x in api.get("/api/oee/machines", params={"active_only": True}).json()]
    assert api.patch("/api/oee/machines/edge-1", json=dict(key="boshqa")).status_code == 400
    assert api.get("/api/oee/machines/yoq").status_code == 404
    assert api.patch("/api/oee/machines/yoq", json=dict(name="x")).status_code == 404


def test_machine_delete_requires_force_when_events_exist(api):
    add_machine(api, "m1")
    api.post("/api/oee/events", json=[run_ev(), down_ev()])
    r = api.delete("/api/oee/machines/m1")
    assert r.status_code == 409 and "force" in r.json()["detail"]
    r = api.delete("/api/oee/machines/m1", params={"force": True})
    assert r.status_code == 200 and r.json()["events_deleted"] == 2
    assert api.get("/api/oee/events").json()["total"] == 0 and api.get("/api/oee/machines/m1").status_code == 404
    add_machine(api, "m2")
    assert api.delete("/api/oee/machines/m2").json()["events_deleted"] == 0


def test_pp_catalog_and_speed_suggestion(api):
    cat = api.get("/api/oee/machines/catalog").json()
    from app.services.postprocessors import MACHINES
    assert len(cat) == len(MACHINES) and all(not c["added"] for c in cat)
    api.post("/api/oee/machines", json=dict(pp_key="scm_wincut"))
    assert next(c for c in cat if c["key"] == "scm_wincut") and \
        next(c for c in api.get("/api/oee/machines/catalog").json() if c["key"] == "scm_wincut")["added"] is True
    s = api.get("/api/oee/machines/scm_wincut/suggest").json()
    # SCM VelAvanz = 30 (standart); birligi m/min deb taxmin qilinadi → 500 mm/s
    assert s["source"] == {"vel_avanz": 30.0} and s["suggested"]["cut_speed_mm_s"] == pytest.approx(500.0)
    # taklif avtomatik qo'llanmaydi
    assert api.get("/api/oee/machines/scm_wincut").json()["cut_speed_mm_s"] == 1000.0
    add_machine(api, "erkin")
    assert api.get("/api/oee/machines/erkin/suggest").status_code == 400
    api.post("/api/oee/machines", json=dict(pp_key="holzma_ptx"))
    assert api.get("/api/oee/machines/holzma_ptx/suggest").json()["suggested"] == {}


# ───────────────────────── Sabablar ─────────────────────────
def test_reasons_crud_rules(api):
    rs = api.get("/api/oee/reasons").json()
    assert len(rs) == 15 and {r["code"] for r in rs if r["planned"]} == {"maintenance", "break"}
    assert [r["code"] for r in api.get("/api/oee/reasons", params={"kind": "reject"}).json()] == \
        ["chip", "size", "mat_defect", "damage", "reject_other"]
    c = api.post("/api/oee/reasons", json=dict(code="power_cut", name_ru="Нет электричества", name_uz="Elektr yo'q"))
    assert c.status_code == 201 and c.json()["kind"] == "downtime" and c.json()["planned"] is False and c.json()["system"] is False
    assert api.post("/api/oee/reasons", json=dict(code="power_cut")).status_code == 409
    assert api.post("/api/oee/reasons", json=dict(code="idle")).status_code == 400          # tizim kodi
    assert api.post("/api/oee/reasons", json=dict(code="Katta Harf")).status_code == 400
    assert api.delete("/api/oee/reasons/setup").status_code == 409                          # boshlang'ich — o'chirilmaydi
    add_machine(api, "m1")
    api.post("/api/oee/events", json=down_ev(reason="power_cut"))
    r = api.delete("/api/oee/reasons/power_cut")
    assert r.status_code == 409 and "1" in r.json()["detail"]
    assert api.put("/api/oee/reasons/power_cut", json=dict(kind="reject")).status_code == 409    # ishlatilgan — turi o'zgarmaydi
    assert api.put("/api/oee/reasons/power_cut", json=dict(planned=True, name_uz="Yangi")).json()["planned"] is True
    api.delete("/api/oee/events/" + str(api.get("/api/oee/events").json()["items"][0]["id"]))
    assert api.delete("/api/oee/reasons/power_cut").status_code == 200
    assert api.delete("/api/oee/reasons/yoq").status_code == 404
    assert api.put("/api/oee/reasons/setup", json=dict(code="boshqa")).status_code == 400


# ───────────────────────── Smena kalendari API ─────────────────────────
def test_shift_api_validation_and_crud(api):
    add_machine(api, "m1")
    bad = [dict(start="25:00", end="12:00"), dict(start="08:00", end="08:00"), dict(start="8", end="12:00"),
           dict(start="08:00", end="12:00", weekdays=[7]), dict(start="08:00", end="12:00", weekdays=[]),
           dict(start="08:00", end="12:00", breaks=[dict(start="13:00", end="14:00")]),
           dict(start="08:00", end="12:00", breaks=[dict(start="10:00", end="10:00")]),
           dict(start="08:00", end="12:00", machine="yoq"),
           dict(start="08:00", end="12:00", valid_from="2026-02-02", valid_to="2026-01-01"),
           dict(kind="off", name="Bayram")]
    for b in bad:
        assert api.post("/api/oee/shifts", json=b).status_code in (400, 422), b
    ok = api.post("/api/oee/shifts", json=dict(name="Kunduzgi", start="08:00", end="17:00",
                                               breaks=[dict(start="12:00", end="13:00", name="Obed")]))
    assert ok.status_code == 201 and ok.json()["weekdays"] == [0, 1, 2, 3, 4, 5]
    sid = ok.json()["id"]
    up = api.put(f"/api/oee/shifts/{sid}", json=dict(name="Kunduzgi 2", start="07:00", end="16:00", machine="m1", weekdays=[0, 1]))
    assert up.status_code == 200 and up.json()["machine"] == "m1" and up.json()["start"] == "07:00" and up.json()["breaks"] == []
    off = api.post("/api/oee/shifts", json=dict(kind="off", name="Bayram", valid_from="2026-09-01", valid_to="2026-09-02"))
    assert off.status_code == 201 and off.json()["kind"] == "off"
    assert len(api.get("/api/oee/shifts").json()) == 2
    d = monday()
    pv = api.get("/api/oee/shifts/preview", params={"machine": "m1", "from": d.isoformat(), "to": d.isoformat()}).json()
    assert len(pv) == 1 and pv[0]["planned_min"] == 540 and pv[0]["start"] == z(d, 7)
    assert api.delete(f"/api/oee/shifts/{sid}").status_code == 200
    assert api.delete(f"/api/oee/shifts/{sid}").status_code == 404
    assert api.put("/api/oee/shifts/999999", json=dict(start="08:00", end="12:00")).status_code == 404


# ───────────────────────── Konfiguratsiya ─────────────────────────
def test_config_get_put_and_validation(api):
    c = api.get("/api/oee/config").json()
    assert c["config"]["tz_offset_min"] == 0 and c["bands"] == {"low": 0.6, "high": 0.85} and c["max_batch"] == 500
    assert set(c["groups"]) == {"hour", "shift", "day", "week"} and "last7" in c["periods"]
    r = api.put("/api/oee/config", json=dict(idle_gap_s=600, unit="part"))
    assert r.status_code == 200 and r.json()["config"]["idle_gap_s"] == 600 and r.json()["config"]["unit"] == "part"
    assert api.get("/api/oee/config").json()["config"]["tz_offset_min"] == 0              # boshqalari saqlanadi
    for bad in (dict(tz_offset_min=5000), dict(unit="kg"), dict(idle_gap_s=-1), dict(run_cap_factor=0.5), dict(yoq=1)):
        assert api.put("/api/oee/config", json=bad).status_code == 400, bad


# ───────────────────────── Hisob-kitob endpointlari ─────────────────────────
def _hand_example(api):
    """Smena 08–12; sozlash, nosozlik; 2 ta run (qo'lda hisoblangan: A 0.9, P 0.8333, Q 0.9667, OEE 0.725)."""
    d = monday()
    add_machine(api, "m1", cut_speed_mm_s=1000, cut_change_s=5, sheet_load_s=20)
    add_shift(api, "08:00", "12:00", weekdays=[d.weekday()])
    r = api.post("/api/oee/events", json=[
        down_ev(start=(8, 0), end=(8, 12), reason="setup"),
        run_ev(start=(8, 12), end=(10, 0), qty=45, cut_length_m=10, cuts=18),
        down_ev(start=(10, 0), end=(10, 12), reason="breakdown"),
        run_ev(start=(10, 12), end=(12, 0), qty=45, cut_length_m=10, cuts=18, reject_qty=3, unit="sheet")])
    assert r.json()["created"] == 4
    return d


def test_summary_series_pareto_hand_example(api):
    d = _hand_example(api)
    q = {"machine": "m1", "from": d.isoformat(), "to": d.isoformat()}
    s = api.get("/api/oee/summary", params=q).json()
    m = s["summary"]
    assert m["availability"] == pytest.approx(0.9) and m["performance"] == pytest.approx(0.8333, abs=1e-4)
    assert m["quality"] == pytest.approx(0.9667, abs=1e-4) and m["oee"] == pytest.approx(0.725)
    assert (m["planned_min"], m["run_min"], m["stop_min"], m["produced"], m["rejected"]) == (240, 216, 24, 90, 3)
    assert m["band"] == {"oee": "mid", "availability": "high", "performance": "mid", "quality": "high"}
    assert m["avg_cycle_s"] == pytest.approx(144.0) and m["ideal_cycle_s"] == pytest.approx(120.0)
    assert s["machines"][0]["machine"] == "m1" and s["machines"][0]["oee"] == pytest.approx(0.725)
    assert s["from"] == z(d) and s["bands"] == {"low": 0.6, "high": 0.85}
    ser = api.get("/api/oee/series", params={**q, "group_by": "hour"}).json()
    assert len(ser["series"]) == 24 and ser["series"][8]["planned_min"] == 60
    assert ser["series"][8]["availability"] == pytest.approx(0.8)        # 08:00–08:12 sozlash
    day = api.get("/api/oee/series", params={**q, "group_by": "day"}).json()["series"]
    assert len(day) == 1 and day[0]["oee"] == pytest.approx(0.725)
    p = api.get("/api/oee/downtime-pareto", params=q).json()
    assert [(x["reason"], x["minutes"]) for x in p["pareto"]] == [("breakdown", 12), ("setup", 12)] and p["pareto_total_min"] == 24
    assert p["pareto"][1]["cumulative"] == pytest.approx(1.0)
    dash = api.get("/api/oee/dashboard", params={**q, "group_by": "day"}).json()
    assert dash["summary"]["oee"] == pytest.approx(0.725) and len(dash["extra_series"]["shift"]) == 1 and dash["pareto"]


def test_material_efficiency_kpi_is_separate_from_oee(api):
    """Material KPI (OEE ga kirmaydi): fill = detallar / list maydoni; waste = (list − detallar − деловой qoldiq) / list."""
    d = monday()
    add_machine(api, "m1")
    add_shift(api, "08:00", "12:00", weekdays=[d.weekday()])
    api.post("/api/oee/events", json=[
        run_ev(start=(8, 0), end=(9, 0), qty=10, sheet_area_m2=5.0, parts_area_m2=4.0, remnant_area_m2=0.3, ideal_cycle_s=360),
        run_ev(start=(9, 0), end=(10, 0), qty=10, sheet_area_m2=5.0, parts_area_m2=4.5, ideal_cycle_s=360)])
    q = {"machine": "m1", "from": d.isoformat(), "to": d.isoformat()}
    m = api.get("/api/oee/summary", params=q).json()
    s = api.get("/api/oee/dashboard", params=q).json()
    mat = s["material"]
    assert mat["sheets"] == 20 and mat["sheet_m2"] == 100 and mat["parts_m2"] == 85 and mat["remnant_m2"] == 3
    assert mat["fill"] == pytest.approx(0.85) and mat["waste"] == pytest.approx((100 - 85 - 3) / 100)
    assert s["machines"][0]["material"]["fill"] == pytest.approx(0.85)
    assert m["summary"]["oee"] == s["summary"]["oee"]                                  # OEE materialga bog'liq emas
    # maydon ma'lumoti bo'lmasa — KPI yo'q (0 emas)
    api.delete("/api/oee/events/" + str(api.get("/api/oee/events").json()["items"][0]["id"]))
    api.delete("/api/oee/events/" + str(api.get("/api/oee/events").json()["items"][0]["id"]))
    api.post("/api/oee/events", json=run_ev(start=(8, 0), end=(9, 0), qty=3))
    assert api.get("/api/oee/dashboard", params=q).json()["material"] == dict(sheets=0, sheet_m2=0, parts_m2=0, remnant_m2=0, fill=None, waste=None)
    # noto'g'ri maydon
    assert api.post("/api/oee/events", json=run_ev(sheet_area_m2=0)).status_code == 400
    assert api.post("/api/oee/events", json=run_ev(parts_area_m2=-1)).status_code == 400


def test_period_presets_and_range_errors(api):
    add_machine(api, "m1")
    for p in ("today", "yesterday", "last7", "last14", "last30", "this_week", "this_month"):
        assert api.get("/api/oee/summary", params={"period": p}).status_code == 200, p
    assert api.get("/api/oee/summary", params={"period": "yoq"}).status_code == 400
    assert api.get("/api/oee/summary", params={"from": "2026-13-45"}).status_code == 400
    assert api.get("/api/oee/summary", params={"from": "2026-09-10T10:00:00"}).status_code == 400          # soat poyasi yo'q
    assert api.get("/api/oee/summary", params={"from": "2026-09-10", "to": "2026-09-01"}).status_code == 400
    assert api.get("/api/oee/summary", params={"from": "2020-01-01", "to": "2026-01-01"}).status_code == 400   # juda katta
    assert api.get("/api/oee/series", params={"group_by": "oy"}).status_code == 400
    assert api.get("/api/oee/summary", params={"machine": "yoq"}).status_code == 404
    # soat bo'yicha guruhlash — eng ko'pi 31 kun (juda ko'p bo'lak chiqmasin)
    r = api.get("/api/oee/series", params={"group_by": "hour", "from": "2026-01-01", "to": "2026-03-01"})
    assert r.status_code == 400 and "31" in r.json()["detail"]
    assert api.get("/api/oee/series", params={"group_by": "hour", "period": "last30"}).status_code == 200


def test_warnings_explain_missing_ideal_cap_and_overtime(api):
    d = monday()
    add_machine(api, "m1", cut_speed_mm_s=1000, cut_change_s=5, sheet_load_s=20)
    add_shift(api, "08:00", "12:00", weekdays=[d.weekday()])
    api.post("/api/oee/events", json=[
        dict(type="run", machine="m1", start=z(d, 8), end=z(d, 8, 5), qty=1),                                # ideal sikl noma'lum
        dict(type="run", machine="m1", start=z(d, 8, 5), end=z(d, 8, 15), qty=6, ideal_cycle_s=200),          # P > 100 %
        dict(type="run", machine="m1", start=z(d, 13), end=z(d, 14), qty=2, ideal_cycle_s=100)])             # smenadan tashqari
    q = {"machine": "m1", "from": d.isoformat(), "to": d.isoformat()}
    w = {x["code"]: x for x in api.get("/api/oee/summary", params=q).json()["warnings"]}
    assert w["no_ideal"]["count"] == 1 and "p_capped" in w and w["outside_shift"]["count"] == 2
    assert "no_calendar" not in w
    # kalendarsiz — alohida ogohlantirish
    api.delete("/api/oee/shifts/" + str(api.get("/api/oee/shifts").json()[0]["id"]))
    w2 = {x["code"] for x in api.get("/api/oee/summary", params=q).json()["warnings"]}
    assert "no_calendar" in w2


def test_resolve_range_uses_zone_offset():
    from app.services.oee import OeeConfig, resolve_range
    cfg = OeeConfig(tz_offset_min=300)
    now = datetime(2026, 9, 16, 22, 30, tzinfo=timezone.utc).timestamp()          # mahalliy: 17-sentabr 03:30
    lo, hi = resolve_range(None, None, "today", cfg, now)
    assert datetime.fromtimestamp(lo, timezone.utc) == datetime(2026, 9, 16, 19, 0, tzinfo=timezone.utc)     # 17-sentabr 00:00 mahalliy
    assert hi - lo == 86400
    lo7, hi7 = resolve_range(None, None, "last7", cfg, now)
    assert hi7 == hi and hi7 - lo7 == 7 * 86400
    wl, wh = resolve_range(None, None, "this_week", cfg, now)                   # 17-sentabr 2026 — chorshanba
    assert datetime.fromtimestamp(wl, timezone.utc) == datetime(2026, 9, 13, 19, 0, tzinfo=timezone.utc) and wh - wl == 7 * 86400
    ml, mh = resolve_range(None, None, "this_month", cfg, now)
    assert datetime.fromtimestamp(ml, timezone.utc) == datetime(2026, 8, 31, 19, 0, tzinfo=timezone.utc)
    assert datetime.fromtimestamp(mh, timezone.utc) == datetime(2026, 9, 30, 19, 0, tzinfo=timezone.utc)
    a, b = resolve_range("2026-09-01", "2026-09-03", None, cfg, now)             # sanalar — zavod kunlari, `to` ham kiradi
    assert b - a == 3 * 86400 and datetime.fromtimestamp(a, timezone.utc) == datetime(2026, 8, 31, 19, 0, tzinfo=timezone.utc)
    c, d = resolve_range("2026-09-01T00:00:00Z", "2026-09-01T06:00:00+00:00", None, cfg, now)
    assert d - c == 6 * 3600


def test_gaps_endpoint_lists_idle_and_disappears_after_reason_assigned(api):
    d = monday()
    add_machine(api, "m1")
    add_shift(api, "08:00", "12:00", weekdays=[d.weekday()])
    api.post("/api/oee/events", json=run_ev(start=(8, 0), end=(9, 0)))
    q = {"machine": "m1", "from": d.isoformat(), "to": d.isoformat()}
    g = api.get("/api/oee/gaps", params=q).json()["items"]
    assert g == [dict(start=z(d, 9), end=z(d, 12), minutes=180.0)]
    # sabab belgilash = to'xtash hodisasi
    assert api.post("/api/oee/events", json=down_ev(start=(9, 0), end=(12, 0), reason="no_work")).status_code == 201
    assert api.get("/api/oee/gaps", params=q).json()["items"] == []
    p = api.get("/api/oee/downtime-pareto", params=q).json()["pareto"]
    assert p[0]["reason"] == "no_work" and p[0]["minutes"] == 180


# ───────────────────────── CSV ─────────────────────────
def test_csv_exports_and_formula_injection_guard(api):
    d = _hand_example(api)
    api.post("/api/oee/events", json=down_ev(start=(7, 0), end=(7, 10), note="=HYPERLINK(\"x\")", reason="other"))
    q = {"machine": "m1", "from": d.isoformat(), "to": d.isoformat()}
    r = api.get("/api/oee/export.csv", params={**q, "kind": "events"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert 'filename="oee_events_m1.csv"' in r.headers["content-disposition"]
    text = r.content.decode("utf-8-sig")
    lines = text.strip().splitlines()
    assert lines[0].startswith("id;type;machine;start;end;qty") and len(lines) == 1 + 5
    assert "'=HYPERLINK" in text and ";=HYPERLINK" not in text
    s = api.get("/api/oee/export.csv", params={**q, "kind": "series", "group_by": "day", "sep": ","}).content.decode("utf-8-sig")
    rows = s.strip().splitlines()
    assert rows[0].split(",")[:2] == ["label", "start"] and rows[1].startswith(d.isoformat()) and "0.725" in rows[1]
    p = api.get("/api/oee/export.csv", params={**q, "kind": "pareto"}).content.decode("utf-8-sig")
    assert p.strip().splitlines()[1].startswith("breakdown;")
    assert api.get("/api/oee/export.csv", params={**q, "kind": "yoq"}).status_code == 400
    assert api.get("/api/oee/export.csv", params={**q, "sep": "|"}).status_code == 400


# ───────────────────────── Rollar ─────────────────────────
def _tok(roles=None, name="Ali"):
    claims = {"sub": "u1", "name": name, "exp": int(time.time()) + 300}
    if roles is not None:
        claims["roles"] = roles
    return {"Authorization": "Bearer " + jwt.encode(claims, SECRET, algorithm="HS256")}


def test_roles_events_config_and_demo(api, monkeypatch):
    monkeypatch.setenv("MEBELIX_AUTH_REQUIRED", "1")
    monkeypatch.setenv("MEBELIX_JWT_SECRET", SECRET)
    monkeypatch.setenv("MEBELIX_DEMO", "1")
    admin, tech, cutter, viewer, bare = (_tok(["admin"]), _tok(["technologist"]), _tok(["cutter"]), _tok(["viewer"]), _tok())
    assert api.get("/api/oee/summary").status_code == 401                                    # tokensiz
    assert api.post("/api/oee/machines", json=dict(key="m1"), headers=cutter).status_code == 403
    assert api.post("/api/oee/machines", json=dict(key="m1"), headers=tech).status_code == 201
    # hodisalar: ko'ruvchi yozolmaydi; kroychi / texnolog / rolsiz yozadi
    assert api.post("/api/oee/events", json=run_ev(), headers=viewer).status_code == 403
    assert api.post("/api/oee/events", json=run_ev(), headers=cutter).status_code == 201
    assert api.post("/api/oee/events", json=run_ev(), headers=bare).status_code == 201
    assert api.get("/api/oee/summary", headers=viewer).status_code == 200                    # o'qish — ruxsat
    # sozlamalar: faqat admin / texnolog (rolsiz token — to'liq huquq)
    for h, code in ((viewer, 403), (cutter, 403), (tech, 200), (admin, 200), (bare, 200)):
        assert api.put("/api/oee/config", json=dict(idle_gap_s=300), headers=h).status_code == code, h
    assert api.post("/api/oee/reasons", json=dict(code="r_x"), headers=cutter).status_code == 403
    assert api.post("/api/oee/shifts", json=dict(start="08:00", end="12:00"), headers=cutter).status_code == 403
    assert api.delete("/api/oee/machines/m1", params={"force": True}, headers=cutter).status_code == 403
    # demo: faqat admin (rolsiz va texnolog ham emas)
    for h, code in ((viewer, 403), (cutter, 403), (tech, 403), (bare, 403), (admin, 200)):
        assert api.post("/api/oee/demo-seed", params={"days": 2}, headers=h).status_code == code, h
    assert api.delete("/api/oee/demo-seed", headers=tech).status_code == 403
    assert api.delete("/api/oee/demo-seed", headers=admin).status_code == 200


# ───────────────────────── Demo ─────────────────────────
def test_demo_seed_requires_demo_env(api, monkeypatch):
    monkeypatch.delenv("MEBELIX_DEMO", raising=False)
    r = api.post("/api/oee/demo-seed")
    assert r.status_code == 403
    assert api.delete("/api/oee/demo-seed").status_code == 403
    assert api.get("/api/oee/machines").json() == []                                   # haqiqiy bazani to'ldirmaydi
    assert api.get("/api/oee/config").json()["demo_enabled"] is False
    monkeypatch.setenv("MEBELIX_DEMO", "yoq")
    assert api.post("/api/oee/demo-seed").status_code == 403


def test_demo_seed_generates_two_machines_and_spares_real_data(api, monkeypatch):
    monkeypatch.setenv("MEBELIX_DEMO", "1")
    oee.set_config(dict(tz_offset_min=300))
    add_machine(api, "real1")
    api.post("/api/oee/events", json=run_ev("real1"))
    # kalendar bo'lmasa demo ham haqiqiy emas — namunaviy smena qo'shamiz
    add_shift(api, "08:00", "17:00", weekdays=[0, 1, 2, 3, 4, 5], breaks=[dict(start="12:00", end="13:00")])
    r = api.post("/api/oee/demo-seed", params={"days": 14})
    assert r.status_code == 200
    j = r.json()
    assert j["days"] == 14 and j["machines"] == ["demo-saw-1", "demo-saw-2"] and j["events"] > 800
    keys = [m["key"] for m in api.get("/api/oee/machines").json()]
    assert keys == ["real1", "demo-saw-1", "demo-saw-2"]
    s = api.get("/api/oee/summary", params={"period": "last14"}).json()
    by = {m["machine"]: m for m in s["machines"]}
    assert by["demo-saw-1"]["has_data"] and by["demo-saw-2"]["has_data"]
    assert by["demo-saw-1"]["oee"] > by["demo-saw-2"]["oee"]                           # 1-stanok yaxshiroq
    assert 0.2 < by["demo-saw-2"]["oee"] < 0.6 and 0.6 < by["demo-saw-1"]["oee"] < 0.95
    d = api.get("/api/oee/dashboard", params={"period": "last14", "group_by": "day"}).json()
    assert len(d["series"]) == 14 and {x["reason"] for x in d["pareto"]} >= {"breakdown", "material_wait", "idle"}
    # takroran ishga tushirish — demo almashadi, ko'paymaydi; haqiqiy hodisa saqlanadi
    n1 = api.get("/api/oee/events", params={"source": "demo", "limit": 1}).json()["total"]
    api.post("/api/oee/demo-seed", params={"days": 14})
    assert api.get("/api/oee/events", params={"source": "demo", "limit": 1}).json()["total"] == n1
    # tozalash
    c = api.delete("/api/oee/demo-seed").json()
    assert c["machines"] == 2 and c["events"] == n1
    assert [m["key"] for m in api.get("/api/oee/machines").json()] == ["real1"]
    assert api.get("/api/oee/events").json()["total"] == 1


def test_demo_seed_is_deterministic(api, monkeypatch):
    from app.services import oee_demo
    monkeypatch.setenv("MEBELIX_DEMO", "1")
    add_shift(api, "08:00", "17:00", weekdays=[0, 1, 2, 3, 4, 5], breaks=[dict(start="12:00", end="13:00")])
    now = datetime(2026, 9, 25, 12, tzinfo=timezone.utc).timestamp()
    oee_demo.seed(5, now=now, seed_value=3)
    a = api.get("/api/oee/events", params={"limit": 1000}).json()["items"]
    oee_demo.seed(5, now=now, seed_value=3)
    b = api.get("/api/oee/events", params={"limit": 1000}).json()["items"]
    strip = lambda L: [(e["type"], e["machine"], e["start"], e["end"], e["qty"], e["reason"]) for e in sorted(L, key=lambda e: e["external_id"])]
    assert strip(a) == strip(b) and len(a) > 50
    assert all(e["end"] is None or e["end"] <= "2026-09-25T12:00:00Z" for e in a)           # kelajak hodisasi yo'q
    assert all(e["start"] is None or not e["start"].endswith(".0Z") for e in a) and all("." not in (e["end"] or "") for e in a)
