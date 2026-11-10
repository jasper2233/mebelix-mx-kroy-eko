# Xodim videosi 2026-11-10 (loyiha «2132»): ro'yxatda qoldiq 750×1830 (1 dona) + cheksiz 2750×1830. Lokal tizim — qoldiq + 5 butun
# list (F 93.93 %); MX qoldiqni ishlatmay 6 butun list berardi: qoldiqqa birinchi to'plamdan keyin qolgani ochko'zlik bilan
# kesilib 6 listga tushardi. Endi qoldiqqa muqobil to'plamlar + qolgani butun listlarga aynan K ta (bin completion / SVC).
from app.models import CSCutParams, CSMaterialParams, StockSheet
from app.services.optimizer import Item, optimize

PARTS = [(1189, 1550, 1, 1), (884, 530, 2, 1), (884, 968, 1, 1), (884, 550, 1, 1), (250, 250, 3, 0), (80, 384, 1, 1),
         (884, 1023, 1, 1), (514, 384, 2, 0), (450, 383, 1, 0), (907, 150, 3, 0), (868, 150, 3, 0), (884, 150, 2, 1),
         (884, 384, 1, 1), (1007, 60, 1, 0), (417, 378, 1, 1), (170, 378, 2, 1), (326, 90, 4, 0), (350, 106, 4, 0),
         (350, 326, 2, 0), (884, 550, 2, 1), (884, 1305, 1, 1), (2661, 550, 1, 1), (884, 484, 1, 1), (1306, 150, 3, 0),
         (1305, 150, 3, 0), (884, 1307, 1, 1), (2212, 60, 1, 0), (380, 365, 1, 0), (400, 380, 1, 0), (170, 394, 2, 1),
         (342, 90, 4, 0), (350, 106, 4, 0), (350, 342, 2, 0), (859, 582, 1, 1), (400, 300, 2, 0), (1368, 300, 2, 1),
         (368, 300, 3, 0), (1000, 700, 2, 0), (1368, 700, 2, 1), (1368, 684, 1, 1), (968, 684, 3, 0), (1368, 968, 1, 1)]


def test_remnant_plus_fewer_full_sheets():
    items = [Item(f"p{i}", i + 1, l, w, not g) for i, (l, w, q, g) in enumerate(PARTS) for _k in range(q)]
    assert len(items) == 80
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, use_grain=True, max_rotations=4, multiplicity=2,
                      fill_packet=90, prefer_big_pack=True, quality="normal", strip_sort=3, in_strip_sort=3, min_trim_cut=5)
    mat = CSMaterialParams(thickness=16, remnant_min_side1=1000, remnant_min_side2=500, remnant_min_area=0.5)
    stock = [StockSheet(id="R", length=750, width=1830, qty=1), StockSheet(id="L", length=2750, width=1830, qty=10000)]
    r = optimize(items, stock, cut, mat)
    assert not r.unplaced
    used = {}
    for m in r.maps:
        used[m.sheet_id] = used.get(m.sheet_id, 0) + m.copies
    assert used == {"L": 5, "R": 1}, used                          # avval {"L": 6}
    assert r.maps[-1].sheet_id == "R"                               # qoldiq kartasi oxirida (butun listlardan keyin)
