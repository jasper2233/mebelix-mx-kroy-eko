# Xodim videolari 2026-11-16 (loyihalar «1299», «1182»): kroy ustuvorligi — eng kam material, keyin oldingi listlar maksimal zich,
# qoldiq oxirida.
# 1) Ro'yxat 615×1830 ×1, 2750×1830 ×7, 2750×1830 ∞: onlayn tizim 7 list + 615 bo'lak (36.35 m²); MX 8 butun list (40.26 m²) berardi —
#    soni cheklangan 2750×1830 «qoldiq» deb alohida ko'rilib, «aynan K ta listga» qidiruvlari ishlamasdi.
# 2) 2440×1220 ×2 + 1700×1220 qoldiq: butun listlar zich, ortgan detallar qoldiqqa (undan yana деловой qoldiq); MX qoldiqni 96 %
#    to'ldirib, 2-butun listni 62 % qoldirardi.
from app.models import CSCutParams, CSMaterialParams, StockSheet
from app.services.optimizer import Item, _merge_same_stock, optimize

LDSP = [(2740, 550, 1), (2560, 547, 1), (2300, 550, 1), (1650, 547, 2), (1230, 547, 2), (1280, 500, 1), (1247, 450, 1),
        (910, 520, 1), (750, 547, 6), (750, 500, 2), (836, 440, 3), (704, 520, 2), (660, 547, 1), (720, 500, 1), (704, 500, 12),
        (700, 500, 1), (717, 450, 2), (568, 547, 2), (567, 527, 1), (910, 300, 2), (750, 300, 4), (734, 300, 2), (2180, 100, 1),
        (700, 300, 5), (684, 300, 1), (717, 280, 3), (668, 300, 12), (668, 299, 1), (352, 547, 10), (370, 500, 2), (597, 300, 1),
        (597, 299, 1), (368, 480, 1), (1730, 100, 1), (836, 200, 2), (564, 280, 1), (337, 450, 2), (468, 300, 2), (1248, 106, 1),
        (370, 300, 2), (354, 300, 2), (439, 229, 2), (1248, 80, 1), (337, 280, 2), (800, 100, 1), (768, 100, 1), (836, 90, 2),
        (878, 80, 1), (231, 300, 2), (684, 100, 1), (836, 80, 2), (668, 100, 1), (718, 80, 4), (198, 280, 1), (550, 100, 1),
        (684, 80, 1), (668, 80, 1), (662, 80, 1), (878, 60, 1), (440, 119, 2), (644, 80, 2), (440, 109, 2), (547, 80, 1),
        (720, 60, 1), (662, 60, 1), (368, 100, 1), (684, 50, 1), (480, 66, 1), (303, 100, 1), (368, 80, 1), (338, 80, 4),
        (368, 70, 1), (352, 60, 1), (300, 66, 1), (352, 47, 1)]

AKRIL = [(398, 821, 2), (398, 747, 2), (398, 744, 1), (326, 904, 1), (398, 687, 1), (686, 372, 2), (686, 370, 2), (686, 367, 2),
         (686, 362, 2), (686, 347, 2), (100, 2317, 1), (100, 2180, 1), (674, 297, 2), (100, 1730, 1), (164, 904, 2), (100, 1360, 1),
         (100, 1136, 1), (100, 800, 1), (100, 768, 1), (686, 100, 1), (676, 80, 1), (400, 100, 1), (686, 50, 2), (400, 70, 1),
         (400, 60, 1)]


def _cut(q="normal"):
    return CSCutParams(kerf=3, trim_length=2, trim_width=2, use_grain=True, max_rotations=4, multiplicity=2, fill_packet=90,
                       prefer_big_pack=True, quality=q, min_trim_cut=5)


def _items(spec):
    return [Item(f"p{i}", i + 1, l, w, True) for i, (l, w, q) in enumerate(spec) for _k in range(q)]


def _used(r):
    u: dict = {}
    for m in r.maps:
        u[m.sheet_id] = u.get(m.sheet_id, 0) + m.copies
    return u


def test_merge_same_size_rows():
    st = [StockSheet(id="r", length=615, width=1830, qty=1), StockSheet(id="a", length=2750, width=1830, qty=7),
          StockSheet(id="b", length=2750, width=1830, qty=10000), StockSheet(id="w", length=2750, width=1830, qty=2, is_remnant=True)]
    out, members = _merge_same_stock(st)
    assert [(s.id, s.qty) for s in out] == [("r", 1), ("b", 10000), ("w", 2)]     # ombor qoldig'i birlashtirilmaydi
    assert [m.id for m in members["b"]] == ["a", "b"]


def test_same_size_limited_rows_save_full_sheet():
    mat = CSMaterialParams(thickness=16, remnant_min_side1=1000, remnant_min_side2=500, remnant_min_area=0.5)
    stock = [StockSheet(id="R", length=615, width=1830, qty=1), StockSheet(id="A", length=2750, width=1830, qty=7),
             StockSheet(id="B", length=2750, width=1830, qty=10000)]
    r = optimize(_items(LDSP), stock, _cut(), mat)
    assert not r.unplaced
    assert _used(r) == {"A": 7, "R": 1}, _used(r)                   # avval {"A": 7, "B": 1} (8 butun list)
    assert round(r.material_area_m2, 2) == 36.35
    assert r.maps[-1].sheet_id == "R"                               # qoldiq bo'lak oxirida


def test_full_sheets_dense_remnant_gets_rest():
    mat = CSMaterialParams(thickness=18, remnant_min_side1=1000, remnant_min_side2=500, remnant_min_area=0.5)
    stock = [StockSheet(id="R", length=1700, width=1220, qty=1), StockSheet(id="A", length=2440, width=1220, qty=2),
             StockSheet(id="B", length=2440, width=1220, qty=10000)]
    r = optimize(_items(AKRIL), stock, _cut(), mat)
    assert not r.unplaced
    assert _used(r) == {"A": 2, "R": 1}, _used(r)
    assert r.maps[-1].sheet_id == "R"
    full = [m for m in r.maps if m.sheet_id == "A"]
    assert min(m.fill_percent for m in full) >= 85                  # avval 2-butun list 62 %
    assert r.maps[-1].remnant_area_m2 > 0.5                         # qoldiqdan yana деловой qoldiq


# 3) 2026-11-17, «1182» AKRIL KASHMIR (2440×1220 ∞, 3 list har ikkala tizimda): onlayn tizim 1-list 942 / 160 / 80, 2-list 797 / 397
#    polosalar, 3-listda bitta 100×480 (qoldiq 2327×1210 = 2.82 m²); MX 3-listga ko'p detal tashlab 2.29–2.49 m² qoldirardi.
KASHMIR = [(1844, 537, 1), (717, 537, 1), (160, 2290, 1), (418, 797, 2), (418, 701, 2), (717, 397, 5), (160, 1420, 1),
           (1849, 80, 1), (371, 397, 1), (100, 1420, 1), (100, 1200, 1), (170, 397, 2), (720, 80, 1), (717, 80, 1),
           (100, 480, 1), (420, 80, 1)]


def test_two_full_sheets_dense_tail_one_small_part():
    mat = CSMaterialParams(thickness=18, remnant_min_side1=1000, remnant_min_side2=500, remnant_min_area=0.5)
    stock = [StockSheet(id="A", length=2440, width=1220, qty=10000)]
    r = optimize(_items(KASHMIR), stock, _cut(), mat)
    assert not r.unplaced
    assert r.total_sheets == 3
    assert r.maps[-1].remnant_area_m2 >= 2.7, [m.remnant_area_m2 for m in r.maps]     # avval 2.29–2.49
    assert len(r.maps[-1].placements) <= 2


# 4) 2026-11-19, «1071» XDF: qoldiq 1220×2070 ×1 + 2800×2070 ∞, 17 detal (7.55 m²) — avvalgi tizim qoldiq + 1 list (8.32 m²,
#    ikkala list ≈ 92 %); MX 2 butun list (11.59 m²) berardi: «bin completion» qoldiqni eng zich to'ldirib, qolgani (2154 li bilan)
#    butun listga sig'masdi. `_split_search` — qoldiqqa tushadigan to'plamlar eng muvozanatli to'ldirishdan boshlab.
XDF = [(2154, 599, 1), (799, 799, 1), (799, 699, 2), (719, 699, 2), (418, 1009, 1), (418, 999, 1), (418, 799, 1),
       (799, 399, 2), (418, 699, 2), (418, 691, 1), (719, 399, 2), (354, 691, 1)]


def test_remnant_plus_one_full_balanced_split():
    mat = CSMaterialParams(thickness=6)
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, use_grain=False, max_rotations=4, min_trim_cut=5)
    stock = [StockSheet(id="R", length=1220, width=2070, qty=1), StockSheet(id="A", length=2800, width=2070, qty=10000)]
    r = optimize(_items(XDF), stock, cut, mat)
    assert not r.unplaced
    assert _used(r) == {"R": 1, "A": 1}, _used(r)
