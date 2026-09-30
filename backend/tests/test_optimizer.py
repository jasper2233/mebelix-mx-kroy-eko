"""Optimizator sifati va to'g'riligi (daraxt, minimal obrezka, tekstura, F, LT, paket, tezlik)."""
import random
import time

from app.models import CSCutParams, CSMaterialParams, FirstCutDir, StockSheet, StripSort
from app.services.optimizer import Item, optimize
from app.services.validate import validate

KRAVAT = [(1, 748, 1468, 1), (2, 200, 1468, 2), (3, 154, 748, 1), (4, 154, 1052, 1),
          (5, 50, 1052, 2), (6, 480, 800, 1), (7, 154, 400, 2), (8, 100, 1452, 1),
          (9, 470, 800, 1), (10, 900, 800, 1), (11, 500, 1452, 1), (12, 116, 552, 1),
          (13, 100, 350, 2), (14, 100, 503, 2)]
SHEET = [StockSheet(id="s", length=2750, width=1830)]


def kravat_items():
    return [Item(f"p{u}", u, L, W, True) for u, L, W, q in KRAVAT for _ in range(q)]


def test_benchmark_kravat_quality_and_validity():
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2)
    items = kravat_items()
    res = optimize(items, SHEET, cut, CSMaterialParams())
    assert not validate(res, items, SHEET, cut)
    assert res.total_sheets == 2 and not res.unplaced
    first = res.maps[0]
    assert 100 * first.parts_area_m2 / first.sheet_area_m2 >= 91.0
    # F GibLab usulida: detal maydoni ÷ (list − деловой qoldiq)
    last = res.maps[-1]
    assert last.remnant_area_m2 > 4.0            # oxirgi listda katta деловой qoldiq
    exp = 100 * last.parts_area_m2 / (last.sheet_area_m2 - last.remnant_area_m2)
    assert abs(last.fill_percent - round(exp, 2)) < 0.02


def test_commands_structure_T1_T2():
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2)
    res = optimize(kravat_items(), SHEET, cut, CSMaterialParams())
    for m in res.maps:
        assert m.commands[0].code == "T" and m.commands[0].level == 1
        # har 1-darajali polosadan keyin T2 (polosa xom chetini torsovka)
        for i, c in enumerate(m.commands):
            if c.code == "C" and c.level == 1:
                assert m.commands[i + 1].code == "T" and m.commands[i + 1].level == 2


def test_cut_length_single_part_like_giblab():
    # GibLab: 2750×1830 listda bitta 50×1052 detal → LT 3.76 m (T1 + C1 + T2 + P2)
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2)
    res = optimize([Item("a", 1, 50, 1052, True)], SHEET, cut, CSMaterialParams())
    assert abs(res.maps[0].cut_length_m - 3.76) < 1e-6
    assert res.maps[0].offcuts and any(o.business for o in res.maps[0].offcuts)


def test_raw_edge_allows_small_rest():
    # 20 × (2740×88): 20×88 + 19×3 = 1817 ≤ 1820 — oxirgi 3 mm list chetida (torsovka zapasi bor)
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2)
    items = [Item("s", 1, 2740, 88, True) for _ in range(20)]
    res = optimize(items, SHEET, cut, CSMaterialParams())
    assert res.total_sheets == 1 and not res.unplaced
    # torsovkasiz XDF: 2069 mm detal 2070 mm listga sig'adi
    xdf = [StockSheet(id="x", length=2800, width=2070)]
    items = [Item("a", 1, 2069, 1059, True) for _ in range(3)] + [Item("b", 2, 2069, 1099, True) for _ in range(2)]
    res = optimize(items, xdf, CSCutParams(kerf=3, trim_length=0, trim_width=0), CSMaterialParams())
    assert res.total_sheets == 3


def test_min_trim_inside_respected():
    # ichki kesimda 2 mm qirindi bo'lmasligi kerak (validate buni tekshiradi)
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, min_trim_cut=5)
    items = [Item("a", 1, 1000, 500, False)] * 3 + [Item("b", 2, 998, 300, False)] * 3
    res = optimize(items, SHEET, cut, CSMaterialParams())
    assert not validate(res, items, SHEET, cut)


def test_grain_never_rotated():
    cut = CSCutParams(use_grain=True)
    items = [Item("g", 1, 1000, 300, False) for _ in range(9)]
    res = optimize(items, SHEET, cut, CSMaterialParams())
    for m in res.maps:
        for p in m.placements:
            assert (p.length, p.width, p.rotated) == (1000, 300, False)


def test_packets_copies_and_counts():
    cut = CSCutParams(kerf=4, trim_length=10, trim_width=10)
    items = [Item("d", 1, 716, 396, True) for _ in range(120)]
    res = optimize(items, SHEET, cut, CSMaterialParams())
    assert not validate(res, items, SHEET, cut)
    assert any(m.copies > 1 for m in res.maps)          # bir xil kartalar birlashtirilgan (C: n)
    assert res.total_parts == 120


def test_remnant_stock_used_first():
    cut = CSCutParams()
    stock = [StockSheet(id="r", length=1200, width=800, qty=1, is_remnant=True), SHEET[0]]
    items = [Item("a", 1, 500, 300, True) for _ in range(4)]
    res = optimize(items, stock, cut, CSMaterialParams())
    assert res.maps[0].sheet_id == "r" and res.maps[0].is_remnant


def test_max_types_per_map():
    cut = CSCutParams(max_part_types_per_map=2)
    items = [Item(f"t{k}", k, 300 + 10 * k, 200 + 5 * k, True) for k in range(8) for _ in range(3)]
    res = optimize(items, SHEET, cut, CSMaterialParams())
    for m in res.maps:
        assert len({(p.length, p.width) if not p.rotated else (p.width, p.length) for p in m.placements}) <= 2


def test_first_cut_direction_forced():
    for d, axis in ((FirstCutDir.LENGTH, "y"), (FirstCutDir.WIDTH, "x")):
        cut = CSCutParams(first_cut=d)
        res = optimize(kravat_items(), SHEET, cut, CSMaterialParams())
        assert all(m.strips[0]["a"] == axis for m in res.maps)


def test_random_layouts_valid():
    rnd = random.Random(3)
    for _ in range(12):
        items = [Item(f"p{k}", k, rnd.randint(40, 1500), rnd.randint(40, 900), rnd.random() < 0.7)
                 for k in range(rnd.randint(1, 15)) for _ in range(rnd.randint(1, 6))]
        cut = CSCutParams(kerf=rnd.choice([3, 4.4]), trim_length=rnd.choice([0, 2, 10]), trim_width=rnd.choice([0, 5]),
                          max_rotations=rnd.choice([2, 4, 6]), strip_sort=rnd.choice(list(StripSort)), quality="fast")
        res = optimize(items, SHEET, cut, CSMaterialParams())
        assert not validate(res, items, SHEET, cut)


def test_500_parts_under_5_seconds():
    rnd = random.Random(5)
    items = [Item(f"p{k}", k, rnd.randint(60, 1400), rnd.randint(60, 900), True) for k in range(500)]
    t = time.time()
    res = optimize(items, SHEET, CSCutParams(), CSMaterialParams())
    assert time.time() - t < 5.0
    assert not res.unplaced
