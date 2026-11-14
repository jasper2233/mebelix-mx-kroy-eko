# «Повторяющиеся карты» (2026-11-14, foydalanuvchi talabi): bir xil detallar ko'p bo'lsa kroy bir xil kartalar guruhlaridan
# tuzilsin — pilniy markazda bir nechta list ustma-ust kesiladi, arrachi adashmaydi. Sozlama o'chiq bo'lsa natija o'zgarmaydi;
# yoqilganda listlar soni ko'pi bilan «Допуск листов» ga oshadi (standart 0 — material ko'paymaydi), turli kartalar kamayadi.
from app.models import CSCutParams, CSMaterialParams, StockSheet
from app.services.optimizer import Item, optimize
from app.services.validate import validate

PARTS = [(716, 560, 24, 1), (560, 300, 36, 0), (716, 100, 48, 0), (400, 560, 20, 1), (1200, 560, 8, 1)]


def _run(rep: bool, extra: int = 0):
    items = [Item(f"p{i}", i + 1, l, w, not g) for i, (l, w, q, g) in enumerate(PARTS) for _k in range(q)]
    cut = CSCutParams(kerf=4, trim_length=10, trim_width=10, max_rotations=4, pack_height=40, quality="normal",
                      repeat_maps=rep, repeat_extra_sheets=extra)
    stock = [StockSheet(id="L", length=2750, width=1830, qty=10000)]
    r = optimize(items, stock, cut, CSMaterialParams(thickness=16))
    assert not r.unplaced
    assert validate(r, items, stock, cut) == []
    return r


def test_repeat_maps_fewer_distinct_same_sheets():
    off, on = _run(False), _run(True)
    assert on.total_sheets <= off.total_sheets                      # material ko'paymaydi (допуск 0)
    assert len(on.maps) < len(off.maps)                             # turli kartalar kamroq
    assert max(m.copies for m in on.maps) >= 4                      # katta bir xil guruh (ustma-ust kesish)


def test_repeat_same_size_rows_merge_into_copies():
    """Bir xil o'lchamli detallar turli qatorlarda (chap / o'ng yon devor): nusxalarga aynan bir xil detallar tushadi —
    kartalar «×N» bo'lib birlashadi (avval turli part_id sabab alohida kartalar bo'lib qolardi)."""
    rows = [("L", 720, 560, 9, 1), ("R", 720, 560, 9, 1), ("P", 560, 300, 18, 0), ("F", 716, 396, 18, 1)]
    items = [Item(pid, i + 1, l, w, not g) for i, (pid, l, w, q, g) in enumerate(rows) for _k in range(q)]
    cut = CSCutParams(kerf=4, trim_length=10, trim_width=10, max_rotations=4, pack_height=40, repeat_maps=True)
    stock = [StockSheet(id="L", length=2750, width=1830, qty=10000)]
    r = optimize(items, stock, cut, CSMaterialParams(thickness=16))
    assert not r.unplaced and validate(r, items, stock, cut) == []
    assert max(m.copies for m in r.maps) >= 2, [m.copies for m in r.maps]
    placed = {}
    for m in r.maps:
        for p in m.placements:
            placed[p.part_id] = placed.get(p.part_id, 0) + m.copies
    assert placed == {"L": 9, "R": 9, "P": 18, "F": 18}            # nusxalar sanog'i to'g'ri


def test_repeat_params_validate_range():
    assert CSCutParams().repeat_maps is False and CSCutParams().repeat_extra_sheets == 0
    assert CSCutParams.model_validate({"repeat_extra_sheets": 3}).repeat_extra_sheets == 3
