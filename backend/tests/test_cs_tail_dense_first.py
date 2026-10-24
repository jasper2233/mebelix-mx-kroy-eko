# Foydalanuvchi qoidasi (2026-10-24, xodim loyihasi «4407»): detallar avval listlarga maksimal teriladi, listlar bir chetdan
# to'ladi, qoldiq faqat OXIRIDA. Avval yakuniy bosqich jami деловой maydonini oshirardi — oxirgi ikki list yarim-yarim
# to'lib, ikkalasida 2.2 m² dan qoldiq (5-list 2 ta 2104×506 + 988×600, 6-list 2104×506 + 3 ta 988×500).
from app.models import CSCutParams, CSMaterialParams, StockSheet
from app.services.optimizer import Item, optimize

PARTS = [(1020, 600, 6), (2078, 600, 6), (988, 600, 2), (988, 500, 4), (100, 1650, 2), (2110, 120, 2),
         (250, 1650, 2), (100, 1650, 6), (2104, 506, 6)]


def test_previous_sheets_dense_remnant_only_at_end():
    items = [Item(f"p{i}", i + 1, l, w, True) for i, (l, w, q) in enumerate(PARTS) for _k in range(q)]   # Ткт yo'q
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, use_grain=True, max_rotations=6, multiplicity=2,
                      fill_packet=90, prefer_big_pack=True, quality="normal")
    mat = CSMaterialParams(thickness=16, remnant_min_side1=1000, remnant_min_side2=500, remnant_min_area=0.5)
    r = optimize(items, [StockSheet(id="L", length=2750, width=1830, qty=10000)], cut, mat)
    assert not r.unplaced and len(r.maps) == 6
    area = [sum(pl.length * pl.width for pl in m.placements) / 1e6 for m in r.maps]
    assert area[-1] < 2.0, area                                   # oxirgi listda kam detal
    assert r.maps[-1].remnant_area_m2 >= 3.0                      # bitta katta qoldiq oxirida
    assert sum(m.remnant_area_m2 for m in r.maps[:-1]) < 1.0      # oldingi listlar yarim bo'sh emas
