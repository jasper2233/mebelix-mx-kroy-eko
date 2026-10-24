# «Порядок листов: по списку» — ustuvorlik doim eng kam material (2026-10-24, foydalanuvchi qoidasi; xodim loyihasi «4421»):
# ro'yxatda soni cheklangan qoldiq (2500×650) birinchi, keyin butun listlar. Avval MX qoldiq + 2 list kesardi (11.69 m², katta
# деловой qoldiqlar bilan), keyin 2 butun list (10.07 m²). To'g'risi — qoldiqqa 2385×449 + 1400×100 + 1400×70, qolgani BITTA
# butun listga: 6.66 m² (listlar to'plami qidiruvi `_composition_search` vaqt yetmay ishlamay qolardi).
from app.models import CSCutParams, CSMaterialParams, StockSheet
from app.services import optimizer as mod
from app.services.validate import validate

P = [(1, 459, 520, 3), (2, 2385, 427, 1), (3, 2385, 449, 1), (4, 1400, 100, 2), (5, 1400, 70, 2), (6, 1377, 330, 2),
     (7, 1400, 330, 2), (8, 459, 485, 3)]


def _run(order: str):
    items = [mod.Item(f"p{u}", u, l, w, True) for u, l, w, n in P for _ in range(n)]
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, max_rotations=6, stock_order=order)
    mat = CSMaterialParams(remnant_min_side1=1000, remnant_min_side2=500, remnant_min_area=0.5)
    st = [StockSheet(id="r", length=2500, width=650, qty=1), StockSheet(id="s", length=2750, width=1830)]
    res = mod.optimize(items, st, cut, mat)
    assert not validate(res, items, st, cut) and not res.unplaced
    return res


def test_list_order_does_not_spend_extra_remnant():
    res = _run("list")
    used = sum(m.sheet_length * m.sheet_width * m.copies for m in res.maps) / 1e6
    assert res.total_sheets == 2 and sorted(m.sheet_id for m in res.maps) == ["r", "s"], [(m.sheet_id, m.copies) for m in res.maps]
    assert abs(used - 6.657) < 0.01


def test_remnant_still_first_when_it_saves_a_sheet():
    # qoldiqqa sig'adigan kichik buyurtma: butun list kerak emas — qoldiq ishlatiladi (ro'yxat tartibi)
    items = [mod.Item(f"q{i}", i, 600, 300, True) for i in range(4)]
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, max_rotations=4)
    st = [StockSheet(id="r", length=2500, width=650, qty=1), StockSheet(id="s", length=2750, width=1830)]
    res = mod.optimize(items, st, cut, CSMaterialParams())
    assert res.total_sheets == 1 and res.maps[0].sheet_id == "r"


def _material(st):
    items = [mod.Item(f"p{u}", u, l, w, True) for u, l, w, n in P for _ in range(n)]
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, max_rotations=6)
    res = mod.optimize(items, st, cut, CSMaterialParams(remnant_min_side1=1000, remnant_min_side2=500, remnant_min_area=0.5))
    assert not validate(res, items, st, cut) and not res.unplaced
    return round(sum(m.sheet_length * m.sheet_width * m.copies for m in res.maps) / 1e6, 3), sorted(m.sheet_id for m in res.maps)


def test_any_remnant_same_general_logic():
    # foydalanuvchi (2026-10-24): ro'yxatga qo'shilgan HAR QANDAY qoldiq bir xil mantiqqa kiradi — fayldagi qoldiq, ombordan
    # qo'shilgan qoldiq, ro'yxat oxiridagi qoldiq, soni 2 ta qoldiq — natija bir xil; keraksiz qoldiq kesilmaydi
    S = StockSheet(id="s", length=2750, width=1830)
    cases = [
        [StockSheet(id="r", length=2500, width=650, qty=1), S],
        [StockSheet(id="r", length=2500, width=650, qty=1, is_remnant=True), S],
        [S, StockSheet(id="r", length=2500, width=650, qty=1)],
        [StockSheet(id="r", length=2500, width=650, qty=2), S],
        [StockSheet(id="q", length=800, width=600, qty=1, is_remnant=True), StockSheet(id="r", length=2500, width=650, qty=1), S],
    ]
    for st in cases:
        assert _material(st) == (6.657, ["r", "s"]), [s.id for s in st]
