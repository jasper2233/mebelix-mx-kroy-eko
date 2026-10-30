# Xodim loyihasi «1275» AKRIL Mokriy (2026-10-30): 8 fasad 717×337, 3 fasad 237×604, 3 sokl 100×1150, list 2440×1220.
# Onlayn tizim — 1 list (F 90.65 %): 1-kesim o'ngda 100 mm ustunni ajratadi (3-sokl tik, butun list eni bo'ylab), chapdagi
# blokda fasadlar va 2 sokl. MX avval 2 list berardi: ichki qidiruv chetdagi tor ustunni qurmasdi (`_best_sheet.tail_col`).
from app.models import CSCutParams, CSMaterialParams, StockSheet
from app.services.optimizer import Item, optimize
from app.services.validate import validate

PARTS = [("sokl", 100, 1150, 3), ("fasad", 717, 337, 8), ("fasad2", 237, 604, 3)]


def test_long_thin_parts_go_to_far_edge_column():
    items = [Item(pid, n + 1, l, w, True) for n, (pid, l, w, q) in enumerate(PARTS) for _k in range(q)]
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, use_grain=False, max_rotations=6, complex_strips=True,
                      min_trim_cut=5, quality="normal")
    stock = [StockSheet(id="L", length=2440, width=1220, qty=10000)]
    r = optimize(items, stock, cut, CSMaterialParams(thickness=16))
    assert not r.unplaced and len(r.maps) == 1
    assert validate(r, items, stock, cut) == []
    tik = [pl for pl in r.maps[0].placements if pl.part_id == "sokl" and pl.width == 1150]
    assert len(tik) == 1 and tik[0].x > 2300                       # 3-sokl o'ng chetda tik
