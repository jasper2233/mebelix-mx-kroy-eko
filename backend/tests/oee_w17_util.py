"""OEE (W17) testlari uchun umumiy yordamchilar: bazani tozalash, sana/vaqt, tezkor API chaqiruvlari."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.db import (OeeConfigRow, OeeEventRow, OeeMachineRow, OeeReasonRow, OeeShiftRow, SessionLocal)
from app.services import oee

H = 3600


def wipe() -> None:
    """Barcha OEE jadvallarini bo'shatadi (testlar umumiy bazada ishlaydi)."""
    with SessionLocal() as s:
        for t in (OeeEventRow, OeeMachineRow, OeeShiftRow, OeeReasonRow, OeeConfigRow):
            s.query(t).delete()
        s.commit()


def fresh(tz: int = 0, keep_default_shift: bool = False, **cfg) -> None:
    """Toza OEE: boshlang'ich sabablar, zavod vaqti = UTC + tz, standart smena olib tashlanadi (keep_default_shift=False)."""
    wipe()
    oee.ensure_defaults()
    oee.set_config(dict(tz_offset_min=tz, **cfg))
    if not keep_default_shift:
        with SessionLocal() as s:
            s.query(OeeShiftRow).delete()
            s.commit()


def monday(weeks_ago: int = 2) -> date:
    """O'tgan dushanba (hozirdan `weeks_ago` hafta oldin) — hodisalar «kelajakda» bo'lib qolmasin."""
    today = datetime.now(timezone.utc).date()
    return today - timedelta(days=today.weekday() + 7 * weeks_ago)


def ts(d: date, h: int = 0, m: int = 0, s: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, h, m, s, tzinfo=timezone.utc)


def z(d: date, h: int = 0, m: int = 0, s: int = 0) -> str:
    """ISO 8601 UTC matn (`...Z`)."""
    return ts(d, h, m, s).strftime("%Y-%m-%dT%H:%M:%SZ")


def epoch(d: date, h: int = 0, m: int = 0, s: int = 0) -> float:
    return ts(d, h, m, s).timestamp()


def add_machine(client, key: str = "m1", **kw) -> dict:
    body = dict(key=key, name=kw.pop("name", key), kind="saw", cut_speed_mm_s=1000, cut_change_s=5, sheet_load_s=20)
    body.update(kw)
    r = client.post("/api/oee/machines", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def add_shift(client, start="08:00", end="12:00", **kw) -> dict:
    body = dict(name="S", weekdays=[0, 1, 2, 3, 4, 5, 6], start=start, end=end, breaks=[])
    body.update(kw)
    r = client.post("/api/oee/shifts", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def post_events(client, events):
    r = client.post("/api/oee/events", json=events)
    return r


def day_range(d: date, days: int = 1) -> dict:
    return {"from": z(d), "to": z(d + timedelta(days=days))}
