"""OEE (W17): smena kalendari (tanaffus, yarim tundan o'tish, zavod vaqti siljishi, dam olish kunlari), rejalashtirilgan to'xtash va
guruhlash — baza orqali (`oee.compute`)."""
from __future__ import annotations

from datetime import timedelta

import pytest

from app.db import OeeEventRow, SessionLocal
from app.services import oee

from oee_w17_util import add_machine, add_shift, epoch, fresh, monday, ts, z  # noqa: F401


def ev_run(client, machine, start, end, qty=1, **kw):
    body = dict(type="run", machine=machine, start=start, end=end, qty=qty, ideal_cycle_s=kw.pop("ideal", 60))
    body.update(kw)
    r = client.post("/api/oee/events", json=body)
    assert r.status_code in (200, 201), r.text
    return r.json()


@pytest.fixture()
def db(client):
    fresh(tz=0)
    yield client
    fresh(tz=0)


def test_defaults_seeded_once_and_not_restored(client):
    fresh(tz=0, keep_default_shift=True)
    shifts = oee.list_shifts()
    assert len(shifts) == 1 and shifts[0]["start"] == "08:00" and shifts[0]["end"] == "17:00"
    assert shifts[0]["weekdays"] == [0, 1, 2, 3, 4, 5] and shifts[0]["breaks"][0]["start"] == "12:00"
    assert len(oee.list_reasons()) == 15 and len(oee.list_reasons(kind="reject")) == 5
    oee.ensure_defaults()
    oee.ensure_defaults()
    assert len(oee.list_shifts()) == 1 and len(oee.list_reasons()) == 15
    oee.delete_shift(shifts[0]["id"])                       # foydalanuvchi o'chirdi — qayta tiklanmaydi
    oee.ensure_defaults()
    assert oee.list_shifts() == []
    fresh(tz=0)


def test_expand_default_shift_with_tashkent_offset(db):
    d = monday()
    oee.set_config(dict(tz_offset_min=300))
    add_shift(db, "08:00", "17:00", breaks=[dict(start="12:00", end="13:00", name="Obed")], weekdays=[0, 1, 2, 3, 4, 5])
    insts = oee.expand_shifts(oee.list_shifts(), None, epoch(d) - 86400, epoch(d) + 7 * 86400, 300)
    assert len(insts) == 6                                       # Du–Sha, yakshanba yo'q
    first = insts[0]
    assert first["date"] == d.isoformat()
    assert first["start"] == epoch(d, 3)                       # 08:00 mahalliy = 03:00 UTC
    assert first["end"] == epoch(d, 12)
    assert first["breaks"] == [(epoch(d, 7), epoch(d, 8), "Obed")]
    assert oee.planned_intervals([first]) == [(epoch(d, 3), epoch(d, 7)), (epoch(d, 8), epoch(d, 12))]
    # rejalashtirilgan vaqt: 9 soat − 1 soat tanaffus = 480 min
    pv = oee.preview_shifts(None, epoch(d), epoch(d) + 86400)
    assert pv[0]["planned_min"] == 480


def test_overnight_shift_with_break_after_midnight(db):
    d = monday()
    add_shift(db, "22:00", "06:00", breaks=[dict(start="02:00", end="02:30", name="Tanaffus")], weekdays=[0])
    insts = oee.expand_shifts(oee.list_shifts(), None, epoch(d) - 86400, epoch(d) + 3 * 86400, 0)
    assert len(insts) == 1
    i = insts[0]
    assert i["start"] == epoch(d, 22) and i["end"] == epoch(d + timedelta(days=1), 6)
    assert i["breaks"][0][0] == epoch(d + timedelta(days=1), 2)
    assert sum(b - a for a, b in oee.planned_intervals([i])) == 8 * 3600 - 1800


def test_off_days_and_machine_specific_shifts(db):
    d = monday()
    add_machine(db, "m1")
    add_machine(db, "m2")
    add_shift(db, "08:00", "12:00", weekdays=[0, 1])                                   # umumiy
    add_shift(db, "09:00", "10:00", weekdays=[0, 1], machine="m2", name="faqat m2")    # m2 uchun alohida (umumiyni almashtiradi)
    r = db.post("/api/oee/shifts", json=dict(kind="off", name="Bayram", valid_from=d.isoformat(), valid_to=d.isoformat()))
    assert r.status_code == 201
    rows = oee.list_shifts()
    lo, hi = epoch(d) - 86400, epoch(d) + 3 * 86400
    m1 = oee.expand_shifts(rows, "m1", lo, hi, 0)
    m2 = oee.expand_shifts(rows, "m2", lo, hi, 0)
    assert [i["date"] for i in m1] == [(d + timedelta(days=1)).isoformat()]          # dushanba — bayram
    assert [(i["name"], i["date"]) for i in m2] == [("faqat m2", (d + timedelta(days=1)).isoformat())]
    assert (m2[0]["end"] - m2[0]["start"]) == 3600


def test_validity_range_limits_shift(db):
    d = monday()
    add_shift(db, "08:00", "12:00", weekdays=[0, 1, 2, 3, 4, 5, 6], valid_from=(d + timedelta(days=2)).isoformat(),
              valid_to=(d + timedelta(days=3)).isoformat())
    insts = oee.expand_shifts(oee.list_shifts(), None, epoch(d) - 86400, epoch(d) + 8 * 86400, 0)
    assert [i["date"] for i in insts] == [(d + timedelta(days=2)).isoformat(), (d + timedelta(days=3)).isoformat()]


def test_lunch_break_is_not_idle_time(db):
    """Smena 08–17, tanaffus 12–13: stanok ikkala yarmida to'liq ishlasa — A = 100 %, tanaffus idle emas."""
    d = monday()
    add_machine(db, "m1")
    add_shift(db, "08:00", "17:00", weekdays=[d.weekday()], breaks=[dict(start="12:00", end="13:00", name="Obed")])
    ev_run(db, "m1", z(d, 8), z(d, 12), qty=10, ideal=1440)
    ev_run(db, "m1", z(d, 13), z(d, 17), qty=10, ideal=1440)
    r = oee.compute("m1", epoch(d), epoch(d) + 86400, "day", as_of=epoch(d) + 2 * 86400)
    s = r["summary"]
    assert s["planned_min"] == 480 and s["run_min"] == 480 and s["stop_min"] == 0
    assert s["availability"] == 1.0 and s["performance"] == 1.0 and s["quality"] == 1.0 and s["oee"] == 1.0


def test_planned_downtime_event_reduces_planned_time(db):
    d = monday()
    add_machine(db, "m1")
    add_shift(db, "08:00", "12:00", weekdays=[d.weekday()])
    db.post("/api/oee/events", json=dict(type="downtime", machine="m1", start=z(d, 9), end=z(d, 9, 30), reason="maintenance"))
    ev_run(db, "m1", z(d, 8), z(d, 9), qty=1, ideal=3600)
    ev_run(db, "m1", z(d, 9, 30), z(d, 12), qty=1, ideal=9000)
    r = oee.compute("m1", epoch(d), epoch(d) + 86400, "day", as_of=epoch(d) + 2 * 86400)
    assert r["summary"]["planned_min"] == 210 and r["summary"]["stop_min"] == 0 and r["summary"]["availability"] == 1.0
    assert [p["reason"] for p in r["planned_losses"]] == ["maintenance"] and r["planned_losses"][0]["minutes"] == 30
    assert r["pareto"] == []                                  # rejalashtirilgan to'xtash Paretoga kirmaydi
    # sabab «rejalashtirilgan» belgisi o'zgarsa — hisob ham o'zgaradi
    oee.update_reason("maintenance", oee.ReasonIn(planned=False), {"planned"})
    r = oee.compute("m1", epoch(d), epoch(d) + 86400, "day", as_of=epoch(d) + 2 * 86400)
    assert r["summary"]["planned_min"] == 240 and r["summary"]["stop_min"] == 30
    assert r["pareto"][0]["reason"] == "maintenance" and r["pareto"][0]["minutes"] == 30


def test_pareto_orders_by_minutes_with_cumulative_share(db):
    d = monday()
    add_machine(db, "m1")
    add_shift(db, "08:00", "12:00", weekdays=[d.weekday()])
    for start, end, reason in (((8, 0), (8, 10), "setup"), ((8, 10), (8, 50), "breakdown"), ((9, 0), (9, 20), "material_wait"),
                               ((9, 20), (9, 30), "setup")):
        db.post("/api/oee/events", json=dict(type="downtime", machine="m1", start=z(d, *start), end=z(d, *end), reason=reason))
    ev_run(db, "m1", z(d, 8, 50), z(d, 9), qty=1)
    ev_run(db, "m1", z(d, 9, 30), z(d, 12), qty=1)
    p = oee.compute("m1", epoch(d), epoch(d) + 86400, "day", as_of=epoch(d) + 86400 * 2)["pareto"]
    assert [(x["reason"], x["minutes"], x["count"]) for x in p] == [("breakdown", 40, 1), ("material_wait", 20, 1), ("setup", 20, 2)]
    assert p[0]["share"] == pytest.approx(0.5) and p[1]["cumulative"] == pytest.approx(0.75) and p[2]["cumulative"] == pytest.approx(1.0)
    assert all(not x["planned"] for x in p)


def test_idle_gap_appears_in_pareto_as_idle(db):
    d = monday()
    add_machine(db, "m1")
    add_shift(db, "08:00", "12:00", weekdays=[d.weekday()])
    ev_run(db, "m1", z(d, 8), z(d, 10), qty=1)
    r = oee.compute("m1", epoch(d), epoch(d) + 86400, "day", as_of=epoch(d) + 86400 * 2)
    assert r["pareto"][0]["reason"] == "idle" and r["pareto"][0]["minutes"] == 120 and r["pareto"][0]["count"] == 1
    assert r["summary"]["idle_min"] == 120
    gaps = oee.idle_gaps("m1", epoch(d), epoch(d) + 86400, as_of=epoch(d) + 86400 * 2)
    assert gaps == [dict(start=z(d, 10), end=z(d, 12), minutes=120.0)]


def test_series_group_by_hour_day_week_shift(db):
    d = monday()
    add_machine(db, "m1")
    add_shift(db, "08:00", "12:00", weekdays=[0, 1], name="Ertalab")
    for k in (0, 1, 7):                                  # dushanba, seshanba, keyingi dushanba
        day = d + timedelta(days=k)
        ev_run(db, "m1", z(day, 8), z(day, 12), qty=4, ideal=3600)
    lo, hi = epoch(d), epoch(d) + 14 * 86400
    asof = hi + 86400
    day = oee.compute("m1", lo, hi, "day", as_of=asof)["series"]
    assert len(day) == 14 and day[0]["label"] == d.isoformat() and day[0]["oee"] == 1.0
    assert day[2]["oee"] is None                          # shu kuni smena yo'q — planned 0
    week = oee.compute("m1", lo, hi, "week", as_of=asof)["series"]
    # 1-hafta: dushanba+seshanba ishlagan; 2-hafta: dushanba ishlagan, seshanba hodisasiz (idle) → A = 0.5
    assert len(week) == 2 and week[0]["planned_min"] == 480 and week[0]["availability"] == 1.0
    assert week[1]["planned_min"] == 480 and week[1]["availability"] == 0.5 and week[1]["idle_min"] == 240
    hour = oee.compute("m1", lo, lo + 86400, "hour", as_of=asof)["series"]
    assert len(hour) == 24 and sum(h["planned_min"] for h in hour) == 240
    assert [h["planned_min"] for h in hour][8:12] == [60, 60, 60, 60]
    shift = oee.compute("m1", lo, hi, "shift", as_of=asof)["series"]
    assert [s["name"] for s in shift] == ["Ertalab"] * 4 and shift[0]["date"] == d.isoformat() and shift[0]["planned_min"] == 240
    # panel bir so'rovda kun trendi va smenalar jadvalini oladi
    both = oee.compute("m1", lo, hi, "day", as_of=asof, also=("shift",))
    assert len(both["extra_series"]["shift"]) == 4 and len(both["series"]) == 14


def test_series_total_equals_summary_with_zone_offset(db):
    d = monday()
    oee.set_config(dict(tz_offset_min=300))
    add_machine(db, "m1")
    add_shift(db, "08:00", "17:00", weekdays=[0, 1, 2, 3, 4, 5, 6], breaks=[dict(start="12:00", end="13:00")])
    # mahalliy 22:00 dan kechasi (yarim tun o'tadi) — kun bo'laklari orasidan o'tuvchi hodisa
    ev_run(db, "m1", z(d, 3), z(d, 7), qty=10, ideal=1200)
    ev_run(db, "m1", z(d, 8), z(d, 12), qty=10, ideal=1200)
    lo, hi = epoch(d) - 5 * 3600, epoch(d) + 3 * 86400 - 5 * 3600
    r = oee.compute("m1", lo, hi, "day", as_of=hi + 86400)
    assert sum(s["planned_min"] for s in r["series"]) == pytest.approx(r["summary"]["planned_min"])
    assert sum(s["run_min"] for s in r["series"]) == pytest.approx(r["summary"]["run_min"])
    assert r["series"][0]["label"] == d.isoformat()


def test_no_data_machine_is_excluded_from_aggregate(db):
    d = monday()
    add_machine(db, "m1")
    add_machine(db, "m2")
    add_shift(db, "08:00", "12:00", weekdays=[d.weekday()])
    ev_run(db, "m1", z(d, 8), z(d, 12), qty=4, ideal=3600)
    r = oee.compute(None, epoch(d), epoch(d) + 86400, "day", as_of=epoch(d) + 2 * 86400)
    byk = {m["machine"]: m for m in r["machines"]}
    assert byk["m1"]["has_data"] and not byk["m2"]["has_data"] and "oee" not in byk["m2"]
    assert r["summary"]["machines"] == 1 and r["summary"]["oee"] == 1.0        # m2 «0 %» bilan aralashtirilmaydi
    assert {"code": "no_data", "machines": ["m2"]} in r["warnings"]


def test_aggregate_is_time_weighted_across_machines(db):
    d = monday()
    add_machine(db, "m1")
    add_machine(db, "m2")
    add_shift(db, "08:00", "12:00", weekdays=[d.weekday()])
    ev_run(db, "m1", z(d, 8), z(d, 12), qty=4, ideal=3600)                     # A = 1, P = 1
    ev_run(db, "m2", z(d, 8), z(d, 10), qty=1, ideal=7200)                     # A = 0.5, P = 1
    r = oee.compute(None, epoch(d), epoch(d) + 86400, "day", as_of=epoch(d) + 2 * 86400)
    s = r["summary"]
    assert s["planned_min"] == 480 and s["run_min"] == 360
    assert s["availability"] == pytest.approx(0.75)
    assert s["performance"] == pytest.approx(1.0)
    assert s["oee"] == pytest.approx(0.75)


def test_missing_calendar_warns_and_keeps_raw_counts(db):
    d = monday()
    add_machine(db, "m1")                                     # kalendar yo'q (smenalar o'chirilgan)
    ev_run(db, "m1", z(d, 8), z(d, 9), qty=3)
    r = oee.compute("m1", epoch(d), epoch(d) + 86400, "day", as_of=epoch(d) + 2 * 86400)
    assert r["summary"]["oee"] is None and r["summary"]["availability"] is None
    assert {"code": "no_calendar"} in r["warnings"]
    assert r["machines"][0]["has_data"]


def test_unit_setting_changes_produced_count(db):
    d = monday()
    add_machine(db, "m1")
    add_shift(db, "08:00", "12:00", weekdays=[d.weekday()])
    ev_run(db, "m1", z(d, 8), z(d, 12), qty=4, ideal=3600, parts=48, parts_per_sheet=12, reject_qty=6)
    args = ("m1", epoch(d), epoch(d) + 86400, "day")
    kw = dict(as_of=epoch(d) + 2 * 86400)
    a = oee.compute(*args, **kw)["summary"]
    assert a["produced"] == 4 and a["quality"] == pytest.approx(1 - 0.5 / 4)          # 6 detal = 0.5 list
    oee.set_config(dict(unit="part"))
    b = oee.compute(*args, **kw)["summary"]
    assert b["produced"] == 48 and b["quality"] == pytest.approx(42 / 48)
    assert a["quality"] == pytest.approx(b["quality"])


def test_events_loaded_with_lookback_for_startless_inference(db):
    """Oldingi kunning oxirgi hodisasi bugungi birinchi boshlanishi noma'lum hodisaga ta'sir qilmaydi (cheklangan davomiylik)."""
    d = monday()
    add_machine(db, "m1")
    add_shift(db, "08:00", "09:00", weekdays=[d.weekday(), (d + timedelta(days=1)).weekday()])
    ev_run(db, "m1", None, z(d, 8, 40), qty=1, ideal=600)                  # kecha
    ev_run(db, "m1", None, z(d + timedelta(days=1), 8, 5), qty=1, ideal=300)
    r = oee.compute("m1", epoch(d + timedelta(days=1)), epoch(d + timedelta(days=1)) + 86400, "day", as_of=epoch(d) + 5 * 86400)
    s = r["summary"]
    assert s["planned_min"] == 60 and s["run_min"] == pytest.approx(5)       # smena boshidan 08:05 gacha, kecha ta'sir qilmaydi
    assert s["idle_min"] == pytest.approx(55)


def test_event_times_roundtrip_utc_and_zone_offsets(db):
    d = monday()
    add_machine(db, "m1")
    r = db.post("/api/oee/events", json=dict(type="downtime", machine="m1", start=f"{d.isoformat()}T13:00:00+05:00",
                                             end=f"{d.isoformat()}T14:30:00+05:00", reason="setup"))
    assert r.status_code == 201
    e = r.json()["event"]
    assert e["start"] == z(d, 8) and e["end"] == z(d, 9, 30)                 # UTC da saqlanadi va qaytadi
    with SessionLocal() as s:
        row = s.get(OeeEventRow, e["id"])
        assert row.start_ts.tzinfo is None and row.start_ts.hour == 8
