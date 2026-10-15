"""OEE (W17) hisoblash yadrosi: A, P, Q, OEE formulalari qo'lda hisoblangan misollarda, chegaraviy holatlar (bazasiz)."""
from __future__ import annotations

import pytest

from app.models import CutMap
from app.services import oee_calc as C

H = 3600.0


def t(h: int, m: int = 0, s: int = 0) -> float:
    return h * H + m * 60 + s


PROF = C.MachineProfile("m1", cut_speed_mm_s=1000, cut_change_s=5, sheet_load_s=20, ideal_unit_s=None)
LO, HI, ASOF = t(0), t(24), t(100)        # sutka oynasi; as_of — uzoq kelajak (cheklamaydi)


def run(planned, runs=(), downs=(), rejs=(), cfg=None, prof=PROF, planned_codes=frozenset(), lo=LO, hi=HI, as_of=ASOF):
    cfg = cfg or C.Cfg()
    tl = C.build_timeline(prof, planned, set(planned_codes), list(runs), list(downs), list(rejs), cfg, lo, hi, as_of, "m1")
    return tl, C.ratios(C.components(tl, lo, hi, cfg)), cfg


def approx(v, x, tol=1e-4):
    assert v is not None, f"None, kutilgan {x}"
    assert abs(v - x) <= tol, f"{v} != {x}"


# ───────────────────────── ideal_cycle ─────────────────────────
def test_ideal_cycle_formula_by_hand():
    # 12 m / 1000 mm/s = 12 s;  20 kesim × 5 s = 100 s;  yuklash 20 s  → 132 s
    m = CutMap(index=1, sheet_id="s", sheet_length=2750, sheet_width=1830, cut_length_m=12.0, cuts_count=20)
    assert C.ideal_cycle(m, PROF) == pytest.approx(132.0)
    # paket: 2 list birga kesiladi — kesish vaqti bo'linadi, yuklash har list uchun
    assert C.ideal_cycle(m, PROF, sheets_per_pack=2) == pytest.approx((12 + 100) / 2 + 20)
    # tezlik ikki barobar → kesish uzunligi vaqti yarmiga
    fast = C.MachineProfile("f", cut_speed_mm_s=2000, cut_change_s=5, sheet_load_s=20)
    assert C.ideal_cycle(m, fast) == pytest.approx(6 + 100 + 20)


def test_ideal_cycle_missing_data_is_none():
    class X:
        cut_length_m = None
        cuts_count = 5
    assert C.ideal_cycle(X(), PROF) is None
    assert C.ideal_cycle(CutMap(index=1, sheet_id="s", sheet_length=1, sheet_width=1, cut_length_m=5, cuts_count=3),
                         C.MachineProfile("z", cut_speed_mm_s=0)) is None
    assert C.ideal_cycle(CutMap(index=1, sheet_id="s", sheet_length=1, sheet_width=1, cut_length_m=5, cuts_count=3),
                         C.MachineProfile("z", cut_speed_mm_s=None)) is None


def test_ideal_priority_explicit_over_geometry_over_unit():
    geo = C.RunEv(end=t(9), qty=2, cut_length_m=10, cuts=18)                       # 10 + 90 + 20 = 120 s/list
    assert C.run_ideal_total(geo, PROF) == pytest.approx(240.0)
    expl = C.RunEv(end=t(9), qty=2, cut_length_m=10, cuts=18, ideal_cycle_s=100)  # MES bergan — ustun
    assert C.run_ideal_total(expl, PROF) == pytest.approx(200.0)
    bare = C.RunEv(end=t(9), qty=3)
    assert C.run_ideal_total(bare, PROF) is None
    unit = C.MachineProfile("u", cut_speed_mm_s=None, ideal_unit_s=60)
    assert C.run_ideal_total(bare, unit) == pytest.approx(180.0)
    assert C.run_ideal_total(geo, C.MachineProfile("u", cut_speed_mm_s=None, ideal_unit_s=60)) == pytest.approx(120.0)


# ───────────────────────── Qo'lda hisoblangan misollar ─────────────────────────
def test_hand_example_explicit_starts():
    """Smena 08–12 (240 min). Sozlash 08:00–08:12, R1 08:12–10:00 (45 list), nosozlik 10:00–10:12, R2 10:12–12:00
    (45 list, 3 brak).  ideal sikl = 10 + 18×5 + 20 = 120 s.
    ish = 216 min → A = 0.9;  ideal = 90×120 = 10800 s, ish = 12960 s → P = 0.8333;  Q = 87/90 = 0.9667;  OEE = 0.725."""
    runs = [C.RunEv(end=t(10), start=t(8, 12), qty=45, cut_length_m=10, cuts=18),
            C.RunEv(end=t(12), start=t(10, 12), qty=45, reject_qty=3, unit="sheet", cut_length_m=10, cuts=18)]
    downs = [C.DownEv(t(8), "setup", t(8, 12)), C.DownEv(t(10), "breakdown", t(10, 12))]
    tl, r, _ = run([(t(8), t(12))], runs, downs)
    approx(r["planned_min"], 240)
    approx(r["stop_min"], 24)
    approx(r["run_min"], 216)
    approx(r["availability"], 0.9)
    approx(r["ideal_min"], 180)
    approx(r["performance"], 10800 / 12960)
    approx(r["quality"], 87 / 90)
    approx(r["oee"], 0.9 * (10800 / 12960) * (87 / 90))
    approx(r["oee"], 0.725)
    assert r["produced"] == pytest.approx(90) and r["rejected"] == pytest.approx(3) and r["good"] == pytest.approx(87)
    approx(r["avg_cycle_s"], 144.0, 1e-3)            # 6480 s / 45 list
    approx(r["ideal_cycle_s"], 120.0, 1e-3)
    assert not r["capped"]
    # to'xtash sabablari
    assert tl.ud_by_reason["setup"].measure(LO, HI) == pytest.approx(720)
    assert tl.ud_by_reason["breakdown"].measure(LO, HI) == pytest.approx(720)
    assert tl.idle.measure(LO, HI) == 0


def test_hand_example_start_less_events_gap_rules():
    """Smena 08–09. Hodisalar faqat tugash vaqti bilan (sex «bajarildi»): har 2 min (ideal 120 s) 08:02…08:30 (15 ta), keyin 08:50.
    Birinchi hodisa smena boshigacha kesiladi (08:00–08:02). 08:30–08:44 (14 min ≥ 5) va 08:50–09:00 (10 min) — idle.
    Oxirgi karta: 08:50 − 3×120 s = 08:44 dan.  ish = 30 + 6 = 36 min → A = 0.6; ideal = 16×120 = 1920 s, ish 2160 s → P = 0.8889."""
    runs = [C.RunEv(end=t(8, 2 * i), qty=1, ideal_cycle_s=120) for i in range(1, 16)] + [C.RunEv(end=t(8, 50), qty=1, ideal_cycle_s=120)]
    tl, r, _ = run([(t(8), t(9))], runs)
    approx(r["planned_min"], 60)
    approx(r["idle_min"], 24)
    approx(r["stop_min"], 24)
    approx(r["availability"], 0.6)
    approx(r["performance"], 1920 / 2160)
    approx(r["quality"], 1.0)
    approx(r["oee"], 0.6 * (1920 / 2160))
    assert r["produced"] == 16


def test_short_gaps_between_cards_are_run_not_idle():
    # kartalar orasida 2 min bo'shliq (< 5 min) — ish vaqti (karta almashtirish); 10 min — idle
    runs = [C.RunEv(end=t(8, 10), start=t(8, 0), qty=1, ideal_cycle_s=300),
            C.RunEv(end=t(8, 22), start=t(8, 12), qty=1, ideal_cycle_s=300),       # 2 min bo'shliq
            C.RunEv(end=t(8, 42), start=t(8, 32), qty=1, ideal_cycle_s=300)]       # 10 min bo'shliq
    tl, r, _ = run([(t(8), t(8, 42))], runs)
    approx(r["idle_min"], 10)
    approx(r["run_min"], 32)
    approx(r["availability"], 32 / 42)


@pytest.mark.parametrize("gap_s,is_idle", [(299, False), (300, True), (301, True)])
def test_idle_threshold_boundary_is_inclusive(gap_s, is_idle):
    runs = [C.RunEv(end=t(8, 10), start=t(8, 0), qty=1, ideal_cycle_s=600),
            C.RunEv(end=t(8, 10) + gap_s + 600, start=t(8, 10) + gap_s, qty=1, ideal_cycle_s=600)]
    end = t(8, 10) + gap_s + 600
    tl, r, _ = run([(t(8), end)], runs)
    assert (r["idle_min"] > 0) is is_idle


def test_idle_gap_setting_changes_classification():
    runs = [C.RunEv(end=t(8, 10), start=t(8, 0), qty=1, ideal_cycle_s=600),
            C.RunEv(end=t(8, 30), start=t(8, 20), qty=1, ideal_cycle_s=600)]       # 10 min bo'shliq
    _, r1, _ = run([(t(8), t(8, 30))], runs, cfg=C.Cfg(idle_gap_s=300))
    _, r2, _ = run([(t(8), t(8, 30))], runs, cfg=C.Cfg(idle_gap_s=900))
    approx(r1["idle_min"], 10)
    approx(r2["idle_min"], 0)


# ───────────────────────── Chegaraviy holatlar ─────────────────────────
def test_zero_planned_time_gives_none_not_error():
    runs = [C.RunEv(end=t(9), start=t(8), qty=5, cut_length_m=10, cuts=18)]
    tl, r, _ = run([], runs)
    assert r["availability"] is None and r["performance"] is None and r["quality"] is None and r["oee"] is None
    assert r["planned_min"] == 0 and r["run_min"] == 0
    assert tl.raw_runs == 1 and tl.raw_sheets == 5          # xom sanoq saqlanadi (kalendarsiz ham ko'rinadi)
    assert C.band(r["oee"]) == "none"


def test_no_events_all_idle_gives_zero_availability():
    tl, r, _ = run([(t(8), t(12))])
    approx(r["availability"], 0.0)
    approx(r["oee"], 0.0)                     # rejalashtirilgan vaqt bor, lekin ish yo'q → OEE 0 (P, Q aniqlanmaydi)
    assert r["performance"] is None and r["quality"] is None
    approx(r["idle_min"], 240)


def test_performance_capped_at_100_percent():
    # ideal sikl 200 s/list, haqiqiy 100 s/list → xom P = 2.0, chegara 1.0
    runs = [C.RunEv(end=t(8, 10), start=t(8, 0), qty=6, ideal_cycle_s=200)]        # ish 600 s, ideal 1200 s
    _, r, _ = run([(t(8), t(8, 10))], runs)
    approx(r["performance_raw"], 2.0)
    approx(r["performance"], 1.0)
    assert r["capped"] is True
    approx(r["oee"], r["availability"] * 1.0 * r["quality"])


def test_overlapping_downtimes_counted_once_earliest_wins():
    downs = [C.DownEv(t(8), "setup", t(8, 30)), C.DownEv(t(8, 20), "breakdown", t(8, 50))]
    tl, r, _ = run([(t(8), t(10))], downs=downs)
    assert tl.ud_by_reason["setup"].measure(LO, HI) == pytest.approx(1800)
    assert tl.ud_by_reason["breakdown"].measure(LO, HI) == pytest.approx(1200)       # kesishgan 10 min setup ga
    approx(tl.ud_all.measure(LO, HI) / 60, 50)                                          # 60 emas
    # bir xil boshlanish — id bo'yicha tartibli, ammo yig'indi baribir bir marta
    downs = [C.DownEv(t(8), "a", t(8, 30), id=1), C.DownEv(t(8), "b", t(8, 30), id=2)]
    tl, r, _ = run([(t(8), t(10))], downs=downs)
    approx(tl.ud_all.measure(LO, HI) / 60, 30)


def test_planned_downtime_reduces_planned_time_without_double_subtraction():
    # kalendar: 08–10 va 11–12 (10–11 tanaffus); rejalashtirilgan texnik xizmat 09:30–11:30 tanaffus bilan kesishadi
    planned = [(t(8), t(10)), (t(11), t(12))]
    downs = [C.DownEv(t(9, 30), "maintenance", t(11, 30))]
    runs = [C.RunEv(end=t(9, 30), start=t(8), qty=1, ideal_cycle_s=5400), C.RunEv(end=t(12), start=t(11, 30), qty=1, ideal_cycle_s=1800)]
    tl, r, _ = run(planned, runs, downs, planned_codes={"maintenance"})
    approx(r["planned_min"], 120)               # 08:00–09:30 (90) + 11:30–12:00 (30)
    approx(r["stop_min"], 0)
    approx(r["availability"], 1.0)
    assert tl.pd_by_reason["maintenance"].measure(LO, HI) == pytest.approx(60 * 60)    # smena ichidagi: 09:30–10:00 + 11:00–11:30
    approx(r["performance"], 1.0)


def test_downtime_outside_planned_time_is_ignored():
    downs = [C.DownEv(t(6), "breakdown", t(7))]
    runs = [C.RunEv(end=t(12), start=t(8), qty=1, ideal_cycle_s=14400)]
    _, r, _ = run([(t(8), t(12))], runs, downs)
    approx(r["availability"], 1.0)
    approx(r["stop_min"], 0)


def test_open_downtime_lasts_until_as_of():
    downs = [C.DownEv(t(9), "breakdown", None)]
    tl, r, _ = run([(t(8), t(12))], downs=downs, as_of=t(9, 45))
    # oyna as_of gacha qisqartiriladi: 08:00–09:45 = 105 min; shundan to'xtash 45 min
    approx(r["planned_min"], 105)
    assert tl.ud_by_reason["breakdown"].measure(LO, HI) == pytest.approx(45 * 60)
    assert tl.open_closed == 1


def test_open_downtime_closes_when_production_resumes():
    downs = [C.DownEv(t(9), "breakdown", None)]
    runs = [C.RunEv(end=t(9, 50), start=t(9, 20), qty=1, ideal_cycle_s=1800)]
    tl, r, _ = run([(t(8), t(10))], runs, downs, as_of=t(12))
    assert tl.ud_by_reason["breakdown"].measure(LO, HI) == pytest.approx(20 * 60)     # 09:00–09:20
    # keyingi to'xtash boshlanishi ham yopadi
    downs = [C.DownEv(t(9), "breakdown", None, id=1), C.DownEv(t(9, 30), "setup", t(9, 40), id=2)]
    tl, r, _ = run([(t(8), t(10))], downs=downs, as_of=t(12))
    assert tl.ud_by_reason["breakdown"].measure(LO, HI) == pytest.approx(30 * 60)


def test_production_outside_shift_not_counted_unless_overtime():
    runs = [C.RunEv(end=t(11), start=t(8), qty=3, ideal_cycle_s=3600),               # smena ichida
            C.RunEv(end=t(13), start=t(12, 20), qty=1, ideal_cycle_s=2400)]           # smenadan keyin (08–12)
    _, r, _ = run([(t(8), t(12))], runs)
    approx(r["produced"], 3)
    approx(r["outside_sheets"], 1)
    approx(r["planned_min"], 240)
    # smenadan tashqari ishlash rejalashtirilgan vaqtga qo'shilsa
    _, r2, _ = run([(t(8), t(12))], runs, cfg=C.Cfg(include_overtime=True))
    approx(r2["produced"], 4)
    approx(r2["planned_min"], 240 + 40)                                                # 12:20–13:00 qo'shildi
    approx(r2["outside_sheets"], 0)


def test_run_partially_before_shift_is_prorated():
    # 07:30–08:30 (60 min), smena 08:00 dan: yarmi hisobga olinadi (qty 2 → 1)
    runs = [C.RunEv(end=t(8, 30), start=t(7, 30), qty=2, ideal_cycle_s=900)]
    _, r, _ = run([(t(8), t(9))], runs)
    approx(r["produced"], 1.0)
    approx(r["outside_sheets"], 1.0)


def test_bands_boundaries():
    assert C.band(None) == "none"
    assert C.band(0.0) == "low" and C.band(0.5999) == "low"
    assert C.band(0.60) == "mid" and C.band(0.8499) == "mid"
    assert C.band(0.85) == "high" and C.band(1.0) == "high"
    assert (C.BAND_LOW, C.BAND_HIGH) == (0.60, 0.85)


# ───────────────────────── Sifat: birlik va konvertatsiya ─────────────────────────
def _q_events(unit_of_run="part"):
    # 10 list × 10 detal = 100 detal; 5 brak (detal) shu hodisada; alohida brak: 1 list (= 10 detal)
    runs = [C.RunEv(end=t(9), start=t(8), qty=10, parts=100, parts_per_sheet=10, reject_qty=5, unit="part", ideal_cycle_s=360)]
    rejs = [C.RejEv(ts=t(9, 30), qty=1, unit="sheet", parts_per_sheet=10)]
    return runs, rejs


def test_quality_in_parts_unit_converts_sheet_rejects():
    runs, rejs = _q_events()
    _, r, _ = run([(t(8), t(10))], runs, rejs=rejs, cfg=C.Cfg(unit="part"))
    approx(r["produced"], 100)
    approx(r["rejected"], 15)                      # 5 + 1 list × 10 detal
    approx(r["quality"], 0.85)


def test_quality_in_sheet_unit_converts_part_rejects():
    runs, rejs = _q_events()
    _, r, _ = run([(t(8), t(10))], runs, rejs=rejs, cfg=C.Cfg(unit="sheet"))
    approx(r["produced"], 10)
    approx(r["rejected"], 1.5)                     # 5 detal / 10 + 1 list
    approx(r["quality"], 0.85)                      # bir xil Q (detal soni bir xil bo'lganda)


def test_quality_unit_fallback_when_parts_per_sheet_unknown():
    runs = [C.RunEv(end=t(9), start=t(8), qty=10, reject_qty=2, unit="part", ideal_cycle_s=360)]
    _, r, _ = run([(t(8), t(9))], runs, cfg=C.Cfg(unit="sheet"))
    approx(r["rejected"], 2)                        # konvertatsiya imkonsiz → 1:1 (ogohlantirish bilan)
    assert r["fallback"] >= 1


def test_standalone_reject_outside_planned_time_not_counted():
    runs = [C.RunEv(end=t(9), start=t(8), qty=10, ideal_cycle_s=360)]
    rejs = [C.RejEv(ts=t(15), qty=5, unit="sheet")]       # smena (08–10) dan keyin
    _, r, _ = run([(t(8), t(10))], runs, rejs=rejs)
    approx(r["rejected"], 0)
    approx(r["quality"], 1.0)


def test_quality_never_negative():
    runs = [C.RunEv(end=t(9), start=t(8), qty=2, ideal_cycle_s=1800)]
    rejs = [C.RejEv(ts=t(9), qty=50, unit="sheet")]
    _, r, _ = run([(t(8), t(9))], runs, rejs=rejs)
    approx(r["quality"], 0.0)
    approx(r["oee"], 0.0)


# ───────────────────────── Ideal noma'lum ─────────────────────────
def test_unknown_ideal_gives_none_performance_and_oee():
    runs = [C.RunEv(end=t(9), start=t(8), qty=5)]            # geometriya ham, ideal sikl ham yo'q; stanokda ideal_unit_s yo'q
    tl, r, _ = run([(t(8), t(9))], runs)
    assert r["performance"] is None and r["oee"] is None
    approx(r["availability"], 1.0)
    approx(r["quality"], 1.0)
    assert tl.no_ideal == 1


def test_partial_unknown_ideal_scales_run_time():
    # 1-hodisa: ideal 100 s, ish 200 s;  2-hodisa: ideal noma'lum, ish 200 s.  P faqat ma'lumi bo'yicha: 100/200 = 0.5
    runs = [C.RunEv(end=t(8, 0, 200), start=t(8), qty=1, ideal_cycle_s=100),
            C.RunEv(end=t(8, 6, 40), start=t(8, 0, 200), qty=1)]
    _, r, _ = run([(t(8), t(8, 6, 40))], runs)
    approx(r["performance"], 0.5)


# ───────────────────────── Bo'laklash va qo'shiluvchanlik ─────────────────────────
def test_series_buckets_sum_to_window():
    runs = [C.RunEv(end=t(8, 50), start=t(8, 10), qty=8, ideal_cycle_s=240),           # ikki soatga yoyilgan hodisa
            C.RunEv(end=t(10, 20), start=t(9, 40), qty=10, ideal_cycle_s=200, reject_qty=1, unit="sheet"),
            C.RunEv(end=t(11, 30), qty=3, ideal_cycle_s=300)]                          # boshlanishi noma'lum
    downs = [C.DownEv(t(9), "setup", t(9, 25))]
    cfg = C.Cfg()
    tl = C.build_timeline(PROF, [(t(8), t(12))], set(), runs, downs, [], cfg, LO, HI, ASOF, "m1")
    whole = C.components(tl, LO, HI, cfg)
    tot = C.Comp()
    for a, b, _s in C.bucket_edges(LO, HI, "hour", 0):
        tot.add(C.components(tl, a, b, cfg))
    for f in ("ppt", "stop", "run", "idle", "ideal", "sheets_all", "produced", "rejects"):
        assert getattr(tot, f) == pytest.approx(getattr(whole, f)), f
    assert whole.ppt == 4 * H


def test_bucket_edges_day_week_with_tz_offset():
    off = 300                                                  # UTC+5
    # 2026-09-14 (dushanba) 00:00 mahalliy = 2026-09-13 19:00 UTC
    lo = 1789326000.0                                          # 2026-09-13T19:00:00Z
    edges = C.bucket_edges(lo, lo + 14 * 86400, "day", off)
    assert len(edges) == 14 and all(abs((b - a) - 86400) < 1e-6 for a, b, _s in edges)
    assert C.local_label(edges[0][2], off, "day") == "2026-09-14"
    wk = C.bucket_edges(lo, lo + 14 * 86400, "week", off)
    assert len(wk) == 2 and C.local_label(wk[0][2], off, "week") == "2026-W38"
    # oyna chegarasi kesiladi
    part = C.bucket_edges(lo + 3600, lo + 86400 + 7200, "day", off)
    assert len(part) == 2 and part[0][0] == lo + 3600 and part[1][1] == lo + 86400 + 7200


def test_card_finished_exactly_at_shift_end_belongs_to_that_shift():
    runs = [C.RunEv(end=t(17), qty=1, ideal_cycle_s=60)]
    tl, r, _ = run([(t(8), t(17))], runs)
    assert r["produced"] == 1


def test_intervals_algebra():
    assert C.merge([(1, 3), (2, 5), (7, 8), (8, 9), (4, 4)]) == [(1, 5), (7, 9)]
    assert C.subtract([(0, 10)], [(2, 3), (5, 7)]) == [(0, 2), (3, 5), (7, 10)]
    assert C.intersect([(0, 5), (8, 12)], [(3, 9), (11, 20)]) == [(3, 5), (8, 9), (11, 12)]
    s = C.IvSet([(0, 10), (20, 30)])
    assert s.measure(5, 25) == 10 and s.measure(-5, 100) == 20
    assert s.contains_point(10) and not s.contains_point(0) and s.contains_point(30) and not s.contains_point(15)
