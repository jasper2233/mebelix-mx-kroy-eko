"""W11 — (CL) Погонажный раскрой: 1D optimizator (cl_optimizer) — formulalar, to'g'rilik (brute-force), tezlik, qoidalar.
Qabul testlari T-CL-1…8 (docs/mebelix/giblab_inventory/02_CL_CLE.md §3.9)."""
import random
import time

import pytest

from app.models import CLParams, StockSheet
from app.services import cl_optimizer as co
from app.services.cl_optimizer import LItem


def _items(lengths, start=1):
    return [LItem(f"p{i}", i, float(p)) for i, p in enumerate(lengths, start)]


def _stock(L, w=100, qty=10000, **kw):
    return StockSheet(id=kw.pop("id", f"s{L}"), length=L, width=w, qty=qty, **kw)


# ───────────────────────── Formulalar (T-CL-1…5) ─────────────────────────
def test_tcl1_usable_length():
    assert co.usable_length(1600, 20, 10) == 1540                      # L − (T + k) − (T + k)
    assert co.usable_length(1600, 0, 10) == 1600                       # torsovka 0 — T + k qo'shilmaydi
    assert co.usable_length(1600, 20, 10, end_offset=0) == 1570        # oxirida otstup yo'q
    assert co.usable_length(1600, 20, 10, end_offset=40) == 1520       # «Минимальный отступ в конце»


def test_tcl2_waste_80_and_110_cuts_5():
    cl = CLParams(width=360, kerf=10, trim=20, waste_min=0)
    items = _items([780, 500, 150])
    st = [_stock(1600, 360)]
    res = co.optimize_linear(items, st, cl)
    m = res.maps[0]
    # R1 chizmasi: 20 | k | 780 | k | 500 | k | 150 | k | otxod 80 | k | 20 = 1600
    assert [(p.part_uid, p.x, p.length) for p in m.placements] == [(1, 30.0, 780.0), (2, 820.0, 500.0), (3, 1330.0, 150.0)]
    off = [o for o in m.offcuts if o.kind == "remnant"]
    assert len(off) == 1 and off[0].x == 1490.0 and off[0].length == 80.0 and off[0].raw_length == 110.0
    assert m.cuts_count == 5 and m.cut_length_m == 1.8 and m.fill_percent == 89.38        # F = 1430/1600
    assert [(c.code, c.size, c.ref) for c in m.commands] == [("T", 20.0, ""), ("P", 780.0, "1"), ("P", 500.0, "2"),
                                                              ("P", 150.0, "3"), ("W", 80.0, "Д1"), ("T", 20.0, "")]
    assert not co.validate_cl(res, items, st, cl)
    # ☐ «Торцовка отходов»: otxod oxirgi torsovka zonasini ham oladi — 110, oxirgi torsovka kesimi yo'q (4 kesim)
    cl2 = cl.model_copy(update={"waste_incl_trim": False})
    res2 = co.optimize_linear(items, st, cl2)
    m2 = res2.maps[0]
    off2 = [o for o in m2.offcuts if o.kind == "remnant"]
    assert off2[0].length == 110.0 and off2[0].raw_length == 110.0 and m2.cuts_count == 4
    assert [c.code for c in m2.commands] == ["T", "P", "P", "P", "W"]
    assert not co.validate_cl(res2, items, st, cl2)


def test_tcl3_exact_fit_cuts_6_fill_and_lt():
    cl = CLParams(width=600, kerf=10, trim=20)
    items = [LItem("a", 1, 800.0), LItem("a", 1, 800.0)] + [LItem("b", 2, 500.0)] * 3
    st = [_stock(3200, 600)]
    res = co.optimize_linear(items, st, cl)
    assert res.total_sheets == 1 and len(res.maps) == 1
    m = res.maps[0]
    assert m.cuts_count == 6                                           # T + 5 P (oxirgi P — oxirgi torsovka kesimi)
    assert m.fill_percent == 96.88                                     # 3100 / 3200
    assert m.cut_length_m == 3.6                                       # LT = 6 × 0.6 m
    assert not [o for o in m.offcuts if o.kind == "remnant"]
    assert [(c.code, c.size, c.count) for c in m.commands] == [("T", 20.0, 1), ("P", 800.0, 2), ("P", 500.0, 3)]
    assert res.total_fill_percent == 96.88 and res.total_cut_length_m == 3.6


def test_tcl4_no_trim():
    cl = CLParams(width=100, kerf=3, trim=0, end_offset=None, waste_min=0)
    assert co.usable_length(1000, 0, 3) == 1000
    st = [_stock(1000)]
    full = co.optimize_linear(_items([497, 500]), st, cl)             # 497 + 3 + 500 = 1000: R = 0
    assert full.maps[0].cuts_count == 1 and full.maps[0].offcuts == []        # n − 1 + [R > 0] = 1
    part = co.optimize_linear(_items([400, 300]), st, cl)             # R = 1000 − 700 − 3 = 297 → otxod 294
    m = part.maps[0]
    assert m.cuts_count == 2                                           # n − 1 + [R > 0]
    assert m.placements[0].x == 0.0
    off = [o for o in m.offcuts if o.kind == "remnant"][0]
    assert off.length == 294.0 and off.raw_length == 294.0


def test_waste_classification_thresholds():
    st = [_stock(1000)]
    base = dict(width=100, kerf=3, trim=0)
    # R = 1000 − 400 = 600 − ... bitta detal 400: otxod 597
    items = _items([400])
    r = co.optimize_linear(items, st, CLParams(**base, waste_min=100, business_min=500))
    o = r.maps[0].offcuts[0]
    assert o.kind == "remnant" and o.business and o.length == 597.0
    assert r.business_len_m == 0.597 and r.material_len_m == 1.0
    r = co.optimize_linear(items, st, CLParams(**base, waste_min=100, business_min=1000))
    o = r.maps[0].offcuts[0]
    assert o.kind == "remnant" and not o.business and r.business_len_m == 0
    r = co.optimize_linear(items, st, CLParams(**base, waste_min=800, business_min=1000))
    o = r.maps[0].offcuts[0]
    assert o.kind == "waste" and o.number == 0 and not r.remnants          # oddiy chiqindi: qoldiq jadvaliga kirmaydi


def test_fill_percent_total_and_business_not_subtracted():
    cl = CLParams(width=100, kerf=3, trim=0, waste_min=0, business_min=100)
    res = co.optimize_linear(_items([400]), [_stock(1000)], cl)
    assert res.total_fill_percent == 40.0                              # Σp / L (R4 hisobi); деловой otxod mahrajdan ayirilmaydi


# ───────────────────────── Aniqlik: brute-force ─────────────────────────
def _brute(pieces, lengths, cl):
    """Aniq minimum: (jami polosa uzunligi) — barcha bo'linishlar bo'yicha DP; lengths — cheksiz turlar."""
    k = co.u(cl.kerf)
    ts, te = co.trims_of(cl)
    caps = {L: co.Geom(co.u(L), k, ts, te).cap for L in lengths}
    n = len(pieces)
    ws = [co.u(p) + k for p in pieces]
    cost = [None] * (1 << n)
    for mask in range(1, 1 << n):
        tot = sum(ws[i] for i in range(n) if mask >> i & 1)
        fit = [L for L in lengths if tot <= caps[L]]
        cost[mask] = min(fit) if fit else None
    inf = 1 << 60
    dp = [inf] * (1 << n)
    dp[0] = 0
    for mask in range(1, 1 << n):
        low = mask & -mask
        sub = mask
        while sub:
            if sub & low and cost[sub] is not None and dp[mask ^ sub] + cost[sub] < dp[mask]:
                dp[mask] = dp[mask ^ sub] + cost[sub]
            sub = (sub - 1) & mask
    return dp[-1]


def test_bruteforce_single_and_two_types_optimal():
    rnd = random.Random(11)
    checked = 0
    for it in range(200):
        n = rnd.randint(1, 9)
        two = it % 2 == 1
        lengths = [3000, 6000] if two else [rnd.choice([1000, 1200, 3000, 6000])]
        cl = CLParams(width=50, kerf=rnd.choice([3, 4, 10]), trim=rnd.choice([0, 10, 20]), waste_min=0, business_min=500)
        hi = min(lengths[-1], 2900) if two else int(lengths[0] * 0.7)
        pieces = [float(rnd.randint(300 if two else max(50, lengths[0] // 8), max(301, hi))) for _ in range(n)]
        items = _items(pieces)
        st = [_stock(L, 50) for L in lengths]
        res = co.optimize_linear(items, st, cl)
        assert not co.validate_cl(res, items, st, cl)               # tekshiruv xatosi 0
        if res.unplaced:
            continue
        mat = sum(m.sheet_length * m.copies for m in res.maps)
        assert mat == _brute(pieces, lengths, cl), (pieces, lengths, cl.kerf, cl.trim)
        checked += 1
    assert checked >= 150


@pytest.mark.parametrize("hi,need", [(0.30, 0.95), (0.45, 0.90)])
def test_random_200_instances_valid_not_worse_than_ffd_and_near_lb(hi, need):
    """T-CL-6. Detal polosaning 3–30 % i (profil / plintus / bruss: ≥ 95 % holatda ≤ LB + 1); 3–45 % da LB zaiflashadi
    (yarmiga yaqin detallar — butun sonli cheklov), shuning uchun u yerda ≥ 90 % (qarang tools/bench/cl_bench.py, T_W11_CL.md §6)."""
    rnd = random.Random(2026)
    near = 0
    N = 200
    for it in range(N):
        cl = CLParams(width=100, kerf=rnd.choice([3, 4.4]), trim=rnd.choice([0, 10]), waste_min=100, business_min=1000,
                      waste_incl_trim=rnd.random() < 0.7)
        L = rnd.choice([3000, 6000])
        pieces = []
        for _k in range(rnd.randint(2, 30)):
            pieces += [float(rnd.randint(int(L * 0.03), int(L * hi)))] * rnd.randint(1, 20)
        pieces = pieces[:400]
        items = _items(pieces)
        st = [_stock(L)]
        res = co.optimize_linear(items, st, cl)
        errs = co.validate_cl(res, items, st, cl)
        assert not errs, errs[:3]
        assert not res.unplaced
        lb = co.lower_bound(pieces, st, cl)
        assert res.total_sheets >= lb
        assert res.total_sheets <= co.ffd_strips(pieces, st, cl)        # FFD dan yomon emas
        near += res.total_sheets <= lb + 1
    assert near >= need * N                                              # ≥ 95 % (3–45 % da 90 %) holatda ≤ LB + 1


def test_deterministic_same_input_same_output():
    rnd = random.Random(5)
    pieces = [float(rnd.randint(300, 2200)) for _ in range(150)]
    cl = CLParams(width=60, kerf=3, trim=10)
    a = co.optimize_linear(_items(pieces), [_stock(6000, 60)], cl)
    b = co.optimize_linear(_items(pieces), [_stock(6000, 60)], cl)
    assert a.model_dump(exclude={"elapsed_s"}) == b.model_dump(exclude={"elapsed_s"})


@pytest.mark.parametrize("quality", ["fast", "normal"])
def test_1000_parts_time_budget(quality):
    rnd = random.Random(1000)
    lens = [rnd.randint(200, 2800) for _ in range(300)]
    pieces = [float(lens[i % 300]) for i in range(1000)]
    cl = CLParams(width=100, kerf=3, trim=10, quality=quality)
    items = _items(pieces)
    st = [_stock(6000)]
    t = time.time()
    res = co.optimize_linear(items, st, cl)
    assert time.time() - t < 2.0
    assert not res.unplaced and not co.validate_cl(res, items, st, cl)
    assert res.total_sheets <= co.lower_bound(pieces, st, cl) + 2


def test_20000_parts_max_job_finishes_quickly():
    """MEBELIX_MAX_CUT_ITEMS (20000) chegarasi: FFD segment daraxti va DP bitset — loyiha qulfi daqiqalab band bo'lmaydi."""
    rnd = random.Random(20000)
    lens = [float(rnd.randint(150, 2900)) for _ in range(50)]
    items = [LItem(f"p{i % 50}", i % 50, lens[i % 50]) for i in range(20000)]
    cl = CLParams(width=100, kerf=3, trim=10)
    st = [_stock(6000)]
    t = time.time()
    res = co.optimize_linear(items, st, cl)
    assert time.time() - t < 8.0
    assert res.total_parts == 20000 and not res.unplaced and not co.validate_cl(res, items, st, cl)
    lb = co.lower_bound([i.length for i in items], st, cl)
    assert res.total_sheets <= lb * 1.01 + 2                               # katta hajmda ham LB dan ≤ 1 % + 2


# ───────────────────────── Polosa tanlash va chekka holatlar ─────────────────────────
def test_tcl7_limited_remnants_first_in_list_order():
    cl = CLParams(width=100, kerf=3, trim=0, waste_min=0)
    st = [_stock(1200, qty=1, id="r1", is_remnant=True), _stock(900, qty=1, id="r2", is_remnant=True), _stock(6000, id="new")]
    items = _items([1100, 800, 5900])                                  # har biri o'z polosasiga: qoldiqlarsiz 12 m kerak bo'lardi
    res = co.optimize_linear(items, st, cl)
    assert [m.sheet_id for m in res.maps] == ["r1", "r2", "new"]      # ro'yxat tartibi = ustuvorlik (qoldiqlar birinchi)
    assert res.maps[0].is_remnant and res.maps[1].is_remnant and not res.maps[2].is_remnant
    assert not co.validate_cl(res, items, st, cl)
    # qoldiq yetmasa / kerak bo'lmasa — cheklangan son oshmaydi, kartalar tartibi ro'yxat tartibida
    items = _items([500, 500, 400, 400, 300])
    res = co.optimize_linear(items, st, cl)
    idx = {"r1": 0, "r2": 1, "new": 2}
    seq = [idx[m.sheet_id] for m in res.maps]
    assert seq == sorted(seq)
    used = {}
    for m in res.maps:
        used[m.sheet_id] = used.get(m.sheet_id, 0) + m.copies
    assert used.get("r1", 0) <= 1 and used.get("r2", 0) <= 1
    assert not co.validate_cl(res, items, st, cl)


def test_tcl8_too_long_part_unplaced_rest_continues():
    cl = CLParams(width=100, kerf=3, trim=10)
    items = _items([7000, 500, 500])                                   # 7000 > U = 6000 − 26
    st = [_stock(6000)]
    res = co.optimize_linear(items, st, cl)
    assert res.unplaced == ["p1"]
    assert res.total_parts == 2 and res.total_sheets == 1
    assert not co.validate_cl(res, items, st, cl)


def test_limited_stock_exhausted_leaves_unplaced():
    cl = CLParams(width=100, kerf=3, trim=0)
    items = _items([900, 900, 900])
    st = [_stock(1000, qty=2)]
    res = co.optimize_linear(items, st, cl)
    assert res.total_sheets == 2 and len(res.unplaced) == 1
    assert not co.validate_cl(res, items, st, cl)


def test_equal_length_parts_keep_identity_and_counts():
    """Bir xil uzunlikdagi turli detallar: har biri o'z soni bilan, ortiqcha joylashmaydi (validate_cl count)."""
    cl = CLParams(width=100, kerf=3, trim=10)
    items = [LItem("A", 1, 800.0)] * 5 + [LItem("B", 2, 800.0)] * 3 + [LItem("C", 3, 450.0)] * 4
    st = [_stock(2500)]
    res = co.optimize_linear(items, st, cl)
    assert not co.validate_cl(res, items, st, cl)
    cnt = {}
    for m in res.maps:
        for p in m.placements:
            cnt[p.part_id] = cnt.get(p.part_id, 0) + m.copies
    assert cnt == {"A": 5, "B": 3, "C": 4}


def test_identical_strips_merge_into_one_card_with_copies():
    cl = CLParams(width=100, kerf=3, trim=10)
    items = [LItem("A", 1, 990.0)] * 12                                # bitta detal × 12; 2 tasi sig'adi → 6 ta bir xil polosa
    res = co.optimize_linear(items, [_stock(2030)], cl)
    assert len(res.maps) == 1 and res.maps[0].copies == 6 and res.total_sheets == 6 and res.total_parts == 12


def test_kerf_always_positive_and_multi_unlimited_prefers_shorter_for_small_rest():
    cl = CLParams(width=100, kerf=3, trim=0)
    with pytest.raises(Exception):
        CLParams(kerf=0)                                               # CL da propil > 0
    st = [_stock(6000, id="long"), _stock(3000, id="short")]
    res = co.optimize_linear(_items([2500, 2500, 2400]), st, cl)       # 7400: 6000 + 2400 (3000 ga tushiriladi)
    lens = sorted(m.sheet_length * m.copies for m in res.maps)
    assert sum(lens) <= 9000
    assert not co.validate_cl(res, _items([2500, 2500, 2400]), st, cl)


def test_validate_catches_errors():
    cl = CLParams(width=100, kerf=3, trim=0)
    items = _items([500, 400])
    st = [_stock(1000)]
    res = co.optimize_linear(items, st, cl)
    bad = res.model_copy(deep=True)
    bad.maps[0].placements[1].x += 5
    assert co.validate_cl(bad, items, st, cl)
    bad = res.model_copy(deep=True)
    bad.maps[0].placements[0].length = 900
    assert co.validate_cl(bad, items, st, cl)
    bad = res.model_copy(deep=True)
    bad.maps[0].copies = 3
    assert co.validate_cl(bad, items, st, cl)                          # soni oshib ketdi (count)
    bad = res.model_copy(deep=True)
    bad.maps[0].cuts_count += 1
    assert co.validate_cl(bad, items, st, cl)


def test_end_offset_and_per_strip_trims_in_map():
    cl = CLParams(width=100, kerf=3, trim=10, end_offset=30, waste_min=0)
    res = co.optimize_linear(_items([400]), [_stock(1000)], cl)
    m = res.maps[0]
    assert m.trim_length == 10.0 and m.end_offset_right == 30.0         # kartaga aniq yoziladi
    assert m.placements[0].x == 13.0                                    # T_boshi + k
    off = m.offcuts[0]                                                  # R = 1000 − 13 − 33 − 400 = 554 → W = 551 (T ✓)
    assert off.length == 551.0 and off.raw_length == 584.0
