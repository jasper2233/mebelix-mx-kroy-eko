"""OEE demo-ma'lumot generatori (W17) — FAQAT ko'rsatish/test uchun (`POST /api/oee/demo-seed`, `MEBELIX_DEMO=1` va ADMIN).

2 ta sintetik stanok (`demo-saw-1`, `demo-saw-2`) × N kun (standart 14): smena kalendari bo'yicha (baza kalendari) kartalar kesilishi,
to'xtashlar (sozlash, nosozlik, material kutish, asbob almashtirish, operator yo'q, ish yo'q), brak va hodisasiz bo'shliqlar.
Natija `seed` qiymati bo'yicha takrorlanadi (testlar uchun). Hodisalar `source="demo"` bilan belgilanadi — `clear()` faqat shularni
o'chiradi, haqiqiy hodisalarga tegmaydi.

1-stanok: yaxshilanib boradigan trend, hodisalar boshlanishi bilan (MES uslubi); 2-stanok: sekinroq, ko'proq to'xtash va brak, hodisalar
faqat tugash vaqti bilan (sex «bajarildi» uslubi — boshlanish hisobda avvalgi hodisadan chiqariladi).
"""
from __future__ import annotations

import random
from types import SimpleNamespace

from sqlalchemy import func, select

from ..db import OeeEventRow, OeeMachineRow, SessionLocal
from . import oee
from . import oee_calc as C

DEMO_PREFIX = "demo-"
DEMO_SOURCE = "demo"

# (kalit, nom, pp_key, parametrlar)
DEMO_MACHINES = [
    ("demo-saw-1", "Demo: Kesish stanogi 1 (SCM)", "scm_wincut",
     dict(slow=(1.00, 1.12), gap=(3, 20), fill=(0.80, 0.93), p_break=0.006, p_wait=0.020, p_tool=0.008, p_noop=0.004, setup_prob=0.6,
          setup=(8, 15), reject_p=0.008, improve=0.40, explicit_start=True)),
    ("demo-saw-2", "Demo: Kesish stanogi 2 (Holzma)", "holzma_ptx",
     dict(slow=(1.25, 1.70), gap=(10, 60), fill=(0.72, 0.88), p_break=0.028, p_wait=0.050, p_tool=0.014, p_noop=0.020, setup_prob=0.9,
          setup=(12, 30), reject_p=0.032, improve=-0.10, explicit_start=False)),
]


def _ts(t: float):
    """Soniyagacha yaxlitlangan UTC vaqt (demo hodisalarida mikrosoniya bo'lmasin)."""
    return oee.naive_utc(round(t))


def is_enabled() -> bool:
    import os
    return os.getenv("MEBELIX_DEMO", "").strip().lower() in ("1", "true", "yes")


def clear() -> dict:
    """Demo hodisalarni (source=demo) va hodisasiz qolgan `demo-*` stanoklarni o'chiradi."""
    with SessionLocal() as s:
        n = s.query(OeeEventRow).filter(OeeEventRow.source == DEMO_SOURCE).delete(synchronize_session=False)
        gone = 0
        for r in s.scalars(select(OeeMachineRow).where(OeeMachineRow.key.like(DEMO_PREFIX + "%"))).all():
            if not s.scalar(select(func.count(OeeEventRow.id)).where(OeeEventRow.machine_key == r.key)):
                s.delete(r)
                gone += 1
        s.commit()
    return dict(events=int(n), machines=gone)


def _ensure_machines() -> None:
    have = {m["key"] for m in oee.list_machines()}
    for key, name, pp, _p in DEMO_MACHINES:
        if key not in have:
            oee.create_machine(oee.MachineIn(key=key, name=name, pp_key=pp, kind="saw"))


def seed(days: int = 14, now: float | None = None, seed_value: int = 17) -> dict:
    """Demo hodisalarni yaratadi (avval eski demo hodisalarni o'chiradi). `now` — epoch s (testlar uchun); standart — hozir."""
    days = max(1, min(int(days), 60))
    oee.ensure_defaults()
    clear()
    _ensure_machines()
    cfg = oee.get_config()
    now = oee.utc_now().replace(tzinfo=oee._UTC).timestamp() if now is None else now      # noqa: SLF001
    today = C.local_day_index(now, cfg.tz_offset_min)
    shifts = oee.list_shifts()
    machines = {m["key"]: m for m in oee.list_machines()}
    total = 0
    with SessionLocal() as s:
        for key, _name, _pp, prm in DEMO_MACHINES:
            m = machines[key]
            prof = C.MachineProfile(key, m["cut_speed_mm_s"], m["cut_change_s"], m["sheet_load_s"], m["ideal_unit_s"])
            seq = 0
            for k in range(days):
                di = today - (days - 1) + k
                rng = random.Random(f"{seed_value}:{key}:{di}")
                trend = k / max(1, days - 1)
                f = 1.0 - prm["improve"] * trend          # to'xtash ehtimoli koeffitsienti (kamayadi yoki oshadi)
                lo, hi = C.day_start(di, cfg.tz_offset_min), C.day_start(di + 1, cfg.tz_offset_min)
                insts = [i for i in oee.expand_shifts(shifts, key, lo, hi, cfg.tz_offset_min) if lo <= i["start"] < hi]
                segs = C.merge(oee.planned_intervals(insts))
                first = True
                for a, b in segs:
                    t = a
                    if t >= now:
                        break
                    if first and rng.random() < prm["setup_prob"]:
                        d = rng.uniform(*prm["setup"]) * 60
                        seq = _down(s, key, t, min(t + d, b), "setup", seq, now)
                        t += d
                    first = False
                    # tasodifiy erta tugash: ish yo'q (oxirida bo'shliq)
                    cut_off = b
                    if rng.random() < 0.18:
                        cut_off = b - rng.uniform(35, 90) * 60
                        if rng.random() < 0.5 and cut_off > t:
                            seq = _down(s, key, cut_off, b, "no_work", seq, now)
                    # alohida katta nosozlik (Pareto uchun), 2-stanokda 3 kun oldin
                    big = (t + 3600, t + 3600 + 2.5 * 3600) if key == "demo-saw-2" and di == today - 3 and a == segs[0][0] else None
                    while t < cut_off - 60 and t < now:
                        if big is not None and t >= big[0]:
                            seq = _down(s, key, big[0], min(big[1], cut_off), "breakdown", seq, now)
                            t, big = min(big[1], cut_off), None
                            continue
                        r = rng.random()
                        pb, pw, pt, pn = (prm["p_break"] * f, prm["p_wait"] * f, prm["p_tool"] * f, prm["p_noop"] * f)
                        if r < pb:
                            reason, dur = "breakdown", rng.uniform(25, 75)
                        elif r < pb + pw:
                            reason, dur = "material_wait", rng.uniform(5, 20)
                        elif r < pb + pw + pt:
                            reason, dur = "tool_change", rng.uniform(10, 16)
                        elif r < pb + pw + pt + pn:
                            reason, dur = "no_operator", rng.uniform(8, 25)
                        else:
                            reason = None
                        if reason:
                            e = min(t + dur * 60, cut_off)
                            seq = _down(s, key, t, e, reason, seq, now)
                            t = e
                            continue
                        L = rng.uniform(9.0, 24.0)
                        cuts = max(8, min(44, int(L * 1.5 + rng.uniform(-3, 4))))
                        qty = rng.choice([1, 1, 1, 2, 2, 3])
                        per = C.ideal_cycle(SimpleNamespace(cut_length_m=L, cuts_count=cuts), prof) or 120.0
                        act = per * qty * rng.uniform(*prm["slow"])
                        end = t + act
                        if end > cut_off or end > now:
                            break
                        pps = rng.randint(6, 18)
                        parts = pps * qty
                        sheet_m2 = round(2.75 * 1.83, 4)                      # standart list 2750×1830
                        fill = rng.uniform(*prm["fill"])
                        remn = round(sheet_m2 * rng.choice([0.0, 0.0, 0.03, 0.06, 0.1]), 4)       # деловой qoldiq
                        rej = sum(1 for _i in range(parts) if rng.random() < prm["reject_p"] * (0.5 + f / 2))
                        seq += 1
                        s.add(OeeEventRow(
                            type="run", machine_key=key, start_ts=_ts(t) if prm["explicit_start"] else None,
                            end_ts=_ts(end), qty=qty, reject_qty=rej, unit="part", parts=parts, parts_per_sheet=pps,
                            cut_length_m=round(L, 2), cuts=cuts, sheets_per_pack=1, sheet_area_m2=sheet_m2,
                            parts_area_m2=round(sheet_m2 * fill, 4), remnant_area_m2=remn, source=DEMO_SOURCE,
                            external_id=f"demo:{key}:{seq}", created_by="demo", created_at=oee.utc_now(), updated_at=oee.utc_now()))
                        total += 1
                        t = round(end) + rng.uniform(*prm["gap"])
                        if rng.random() < 0.02 and t < cut_off:      # keyinroq topilgan brak (alohida hodisa)
                            seq += 1
                            s.add(OeeEventRow(
                                type="reject", machine_key=key, end_ts=_ts(min(t, now)), qty=rng.randint(1, 3), unit="part",
                                reason=rng.choice(["chip", "size", "mat_defect", "damage"]), source=DEMO_SOURCE,
                                external_id=f"demo:{key}:{seq}", created_by="demo", created_at=oee.utc_now(), updated_at=oee.utc_now()))
            s.flush()
        s.commit()
        n_ev = s.scalar(select(func.count(OeeEventRow.id)).where(OeeEventRow.source == DEMO_SOURCE)) or 0
    return dict(days=days, machines=[m[0] for m in DEMO_MACHINES], events=int(n_ev))


def _down(s, key: str, a: float, b: float, reason: str, seq: int, now: float) -> int:
    if b <= a or a >= now:
        return seq
    seq += 1
    s.add(OeeEventRow(type="downtime", machine_key=key, start_ts=_ts(a), end_ts=_ts(min(b, now)),
                      reason=reason, source=DEMO_SOURCE, external_id=f"demo:{key}:{seq}", created_by="demo",
                      created_at=oee.utc_now(), updated_at=oee.utc_now()))
    return seq
