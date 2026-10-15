"""v2 biznes qoidalari (docs/mebelix/B_DOMAIN_RULES.md, L_ACCEPTANCE_TESTS.md) — GibLab yordami va korxona
loyihalaridagi saqlangan natijalar bilan solishtirilgan raqamlar."""
import math

import pytest

from app.models import (CSCutParams, CSMaterialParams, EdgeRef, ELParams, OpCostBase, Operation, OpType, Part,
                        Product, Project, SheetRounding, SizeMode, StockSheet)
from app.plugins.legacy_project import import_project
from app.services import calc
from app.services.optimizer import Item, _zone, optimize
from app.services.sizes import compute_sizes
from app.services.validate import validate
from app.services.xnc import arc_sweep, groove_passes

# «Detskiy kravat» (xodimlar loyihasi) detallari: (uid, L, W, qty)
KRAVAT = [
    (1, 748, 1468, 1), (2, 200, 1468, 2), (3, 154, 748, 1), (4, 154, 1052, 1),
    (5, 50, 1052, 2), (6, 480, 800, 1), (7, 154, 400, 2), (8, 100, 1452, 1),
    (9, 470, 800, 1), (10, 900, 800, 1), (11, 500, 1452, 1), (12, 116, 552, 1),
    (13, 100, 350, 2), (14, 100, 503, 2),
]


# ───────────── Torsovka va minimal otstup (B3) ─────────────
def test_trim_example_manual():
    """1200×1000, торцовка 20, пила 10 → foydali en 1000 − 30 − 30 = 940, uzunlik 1140."""
    z = _zone(StockSheet(length=1200, width=1000), CSCutParams(kerf=10, trim_length=20, trim_width=20))
    assert (z.UL, z.UW, z.ox, z.oy) == (1140, 940, 30, 30)


def test_trim_zero_means_no_trim_and_no_kerf():
    z = _zone(StockSheet(length=2800, width=2070), CSCutParams(kerf=4, trim_length=0, trim_width=0))
    assert (z.UL, z.UW) == (2800, 2070)


def test_end_offsets_override():
    p = CSCutParams(kerf=3, trim_length=2, trim_width=2, end_offset_bottom=0, end_offset_right=10)
    z = _zone(StockSheet(length=2750, width=1830), p)
    assert z.UW == 1830 - 5 and z.UL == 2750 - 5 - 13
    # list qatoridagi qiymat operatsiyanikidan ustun
    z2 = _zone(StockSheet(length=2750, width=1830, end_offset_bottom=7), p)
    assert z2.UW == 1830 - 5 - 10


def test_v1_end_offsets_migration():
    assert CSCutParams.model_validate({"trim_both_sides": False}).end_offset_bottom == 0
    p = CSCutParams.model_validate({"min_end_offset": 7})
    assert p.end_offset_bottom == 7 and p.end_offset_right == 7
    assert CSCutParams.model_validate({}).end_offset_bottom is None


# ───────────── O'lcham rejimlari (B2): 300×300, kromka 2 mm + prifugovka 1 mm, ОВ+ОН ─────────────
@pytest.mark.parametrize("mode,detail,jointed,blank", [
    (SizeMode.BLANK, (300, 302), (300, 298), (300, 300)),
    (SizeMode.DETAIL, (300, 300), (300, 296), (300, 298)),
    (SizeMode.JOINTED, (300, 304), (300, 300), (300, 302)),
])
def test_size_modes_manual(mode, detail, jointed, blank):
    el = ELParams(thickness=2, jointing_width=1)
    part = Part(length=300, width=300, edge_top=EdgeRef(op_id="e"), edge_bottom=EdgeRef(op_id="e"))
    s = compute_sizes(part, mode, {"e": el})
    assert s.detail == detail and s.jointed == jointed and s.blank == blank and s.saw == blank


# ───────────── Kromka (B6) ─────────────
def _kravat_project():
    pr = Product(name="Model5")
    el1 = Operation(type=OpType.EL, code="KP-1/19-S", name="kromka PVC 1-19 Sasna",
                    el=ELParams(overhang=20, min_glue_length=100, material_round=10, work_round=10))
    el2 = Operation(type=OpType.EL, code="KP-1/19-S", name="!СмЧт kromka PVC 1-19 Sasna",
                    el=ELParams(symbol="B", overhang=20, min_glue_length=100, material_round=10, work_round=10))
    cs = Operation(type=OpType.CS, name="LDSP BELI KARONA TEKSTURA", cs_material=CSMaterialParams(),
                   cs_cut=CSCutParams(kerf=3, trim_length=2, trim_width=2, min_trim_cut=5),
                   sheets=[StockSheet(length=2750, width=1830)])
    e1, e2 = EdgeRef(op_id=el1.id), EdgeRef(op_id=el2.id)
    spec = {2: dict(edge_right=e1), 6: dict(edge_top=e1, edge_bottom=e1, edge_right=e1),
            8: dict(edge_left=e1, edge_right=e1), 9: dict(edge_top=e2, edge_bottom=e1, edge_right=e2),
            10: dict(edge_top=e2, edge_bottom=e1, edge_right=e2), 11: dict(edge_right=e1)}
    for uid, L, W, q in KRAVAT:
        cs.parts.append(Part(uid=uid, length=L, width=W, qty=q, product_id=pr.id, **spec.get(uid, {})))
    return Project(name="Detskiy kravat", products=[pr], operations=[cs, el1, el2]), cs, el1, el2


def test_edge_usage_matches_giblab():
    """GibLab hisobotidagi «Detskiy kravat»: kromka 1 — material 10.8 m, ish 10.4 m; kromka 2 — 3.1 / 3.0 m."""
    proj, cs, el1, el2 = _kravat_project()
    u = calc.edge_usage(proj, el1)
    assert u["material_m"] == 10.8 and u["work_m"] == 10.4
    u2 = calc.edge_usage(proj, el2)
    assert u2["work_m"] == 3.0 and u2["material_m"] == 3.1


def test_edge_min_length_goes_to_material_not_work():
    proj = Project(products=[Product(name="x")])
    el = Operation(type=OpType.EL, el=ELParams(overhang=20, min_glue_length=100, material_round=30, work_round=30))
    cs = Operation(type=OpType.CS, parts=[Part(length=50, width=300, edge_top=EdgeRef(op_id=el.id),
                                               product_id=proj.products[0].id)])
    proj.operations = [cs, el]
    u = calc.edge_usage(proj, el)
    assert u["work_m"] == 0.05          # ish — sof uzunlik
    assert u["material_m"] == 0.14      # material — max(50, 100) + 2·20


def test_rounding_codes():
    assert calc.round_code(10.8222, 10) == 10.8
    assert calc.round_code(10.8222, 11) == 10.9
    assert calc.round_code(10.8999, 22) == 10.89
    assert calc.round_code(3.5, 0) == 4
    assert calc.round_code(4.896, 20) == 4.9


def test_v1_edge_rounding_migration():
    assert ELParams.model_validate({"material_rounding": 0}).material_round == 20
    assert ELParams.model_validate({"material_rounding": 0.1, "work_rounding": 1}).material_round == 11
    assert ELParams.model_validate({"work_rounding": 1}).work_round == 1
    assert ELParams().material_round == 20


# ───────────── CS: taxmin, narx, yaxlitlash (B5) ─────────────
def test_estimate_formula():
    proj = Project(products=[Product(name="x")])
    cs = Operation(type=OpType.CS, cs_material=CSMaterialParams(est_fill_percent=90, cost_by_sheets=False,
                                                                price=100),
                   cs_cut=CSCutParams(), parts=[Part(length=1000, width=1000, qty=1, product_id=proj.products[0].id)],
                   sheets=[StockSheet(length=2750, width=1830)])
    proj.operations = [cs]
    assert math.isclose(calc.estimate_consumption_m2(proj, cs), 1.1)
    info = calc.cs_cost(proj, cs)
    assert info["estimated"] and math.isclose(cs.cost_material, 110.0)


def test_cost_by_sheets_and_m2():
    proj, cs, *_ = _kravat_project()
    cs.cs_material.price = 500000
    cs.cs_material.cost_by_sheets = True
    calc.run_cutting(proj, cs, quality="fast")
    assert cs.cost_material == 500000 * cs.result.total_sheets
    cs.cs_material.cost_by_sheets = False
    cs.cs_material.price = 100000
    calc.cs_cost(proj, cs)
    res = cs.result
    assert res.material_qty_m2 == round(res.material_area_m2 - res.remnant_area_m2, 4)
    assert math.isclose(cs.cost_material, round(res.material_qty_m2 * 100000, 2), abs_tol=0.02)


def test_sheet_rounding_half_length():
    proj, cs, *_ = _kravat_project()
    cs.cs_material.sheet_rounding = SheetRounding.L_1_2
    calc.run_cutting(proj, cs, quality="fast")
    n = calc._rounded_sheet_count(cs)
    assert cs.result.total_sheets - 1 < n <= cs.result.total_sheets
    assert n * 2 == int(n * 2)


def test_v1_price_per_m2_migration():
    op = Operation.model_validate({"type": "CS", "cs_material": {"price": 100, "price_per_m2": True,
                                                                  "cost_by_sheets": True},
                                   "sheets": [{"length": 2750, "width": 1830}]})
    assert not op.cs_material.price_per_m2 and op.cs_material.price == 503.25     # 100 × 5.0325 m²
    op2 = Operation.model_validate({"type": "CS", "cs_material": {"price": 100, "price_per_m2": True,
                                                                   "cost_by_sheets": False}})
    assert op2.cs_material.price == 100 and not op2.cs_material.cost_by_sheets


def test_operation_cost_material_area_excludes_business():
    proj, cs, *_ = _kravat_project()
    cs.cs_material.op_cost_base = OpCostBase.MATERIAL_AREA
    cs.cs_material.op_price = 1000
    calc.run_cutting(proj, cs, quality="fast")
    assert math.isclose(cs.cost_operation, round(cs.result.material_qty_m2 * 1000, 2), abs_tol=0.02)


# ───────────── Soni: ОК, МК, ИК (B8), karralik (B9) ─────────────
def test_minus_qty_excluded():
    proj = Project(products=[Product(name="x", qty=2)])
    cs = Operation(type=OpType.CS, cs_material=CSMaterialParams(), cs_cut=CSCutParams(),
                   parts=[Part(uid=1, length=500, width=400, qty=3, minus_qty=1, product_id=proj.products[0].id)],
                   sheets=[StockSheet(length=2750, width=1830)])
    proj.operations = [cs]
    calc.run_cutting(proj, cs, quality="fast")
    assert cs.result.total_parts == 5 and cs.parts[0].used_qty == 5 and cs.parts[0].left_qty == 0


def test_multiplicity_is_automatic():
    op = Operation(type=OpType.CS, cs_material=CSMaterialParams(thickness=16),
                   cs_cut=CSCutParams(pack_height=40, multiplicity=7))
    assert calc.sheets_per_pack(op) == 2              # ⌊40 / 16⌋, qo'lda kiritilgan 7 e'tiborsiz


def test_min_part_size_excluded_with_warning():
    proj = Project(products=[Product(name="x")])
    cs = Operation(type=OpType.CS, cs_material=CSMaterialParams(min_part_size=30), cs_cut=CSCutParams(),
                   parts=[Part(uid=1, length=500, width=20, qty=2, product_id=proj.products[0].id),
                          Part(uid=2, length=500, width=400, qty=1, product_id=proj.products[0].id)],
                   sheets=[StockSheet(length=2750, width=1830)])
    proj.operations = [cs]
    calc.run_cutting(proj, cs, quality="fast")
    assert cs.result.total_parts == 1 and cs.result.unplaced.count(cs.parts[0].id) == 2
    assert cs.result.warnings and cs.parts[0].left_qty == 2
    assert "Мин. размер детали" in cs.result.warnings[0] and "(30 мм)" in cs.result.warnings[0]


# ───────────── Optimizator: daraja = burilish raqami ─────────────
@pytest.mark.parametrize("turns", [1, 2, 3, 4])
def test_cut_levels_never_exceed_max_rotations(turns):
    items = []
    for uid, L, W, q in KRAVAT:
        items += [Item(f"p{uid}", uid, L, W, True) for _ in range(q)]
    st = [StockSheet(id="s", length=2750, width=1830)]
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, min_trim_cut=5, max_rotations=turns, quality="fast")
    res = optimize(items, st, cut, CSMaterialParams())
    assert not validate(res, items, st, cut)
    if turns >= 2:
        assert not res.unplaced
    else:
        # 1 burilish: faqat polosalar — detal polosa o'lchamiga to'liq mos kelishi shart; kravat detallari mos emas → joylashmaydi
        assert len(res.unplaced) == len(items) and not res.maps
    for m in res.maps:
        assert all(c.level <= turns for c in m.commands if c.code in ("C", "P", "W")), (turns, m.commands)


def test_one_rotation_places_only_strip_exact_parts():
    """max_rotations = 1: ildizning bevosita bolalari (polosalar) — detal listning foydali enini to'liq egallaydi."""
    uw = 1830 - 2 * (2 + 3)                          # foydali en (torsovka 2 + propil 3, ikki chetda) = 1820
    items = [Item(f"q{i}", i, L, uw, False) for i, L in enumerate([600, 600, 600, 500, 400])]
    items.append(Item("odd", 99, 300, 700, False))   # polosa enini to'ldirmaydi → joylashmaydi
    st = [StockSheet(id="s", length=2750, width=1830)]
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, min_trim_cut=5, max_rotations=1, quality="normal")
    res = optimize(items, st, cut, CSMaterialParams())
    assert not validate(res, items, st, cut)
    assert res.unplaced == ["odd"] and res.total_sheets == 1
    assert all(c.level <= 1 for m in res.maps for c in m.commands if c.code in ("C", "P", "W"))


def test_kravat_two_sheets_dense_first_sheet():
    """GibLab: 2 list, 1-list 93.87 %. MebeliX ham 2 list, 1-list kamida 92 %."""
    items = []
    for uid, L, W, q in KRAVAT:
        items += [Item(f"p{uid}", uid, L, W, True) for _ in range(q)]
    res = optimize(items, [StockSheet(id="s", length=2750, width=1830)],
                   CSCutParams(kerf=3, trim_length=2, trim_width=2, min_trim_cut=5), CSMaterialParams())
    assert not res.unplaced and res.total_sheets == 2
    assert max(m.parts_area_m2 / m.sheet_area_m2 for m in res.maps) >= 0.92


# ───────────── Деловой qoldiq: bo'sh joy bitta katta bo'lakka yig'iladi ─────────────
# Korxona loyihalaridan (1084 «prihojka» op5 va 1094 op3) — GibLab saqlagan natija: 1 list / 0.977 m² va
# 2 list / 1.835 m² деловой qoldiq (≥ 1000×500, ≥ 0.5 m²).
PRIHOJKA = [(657, 357, 2), (657, 356, 2), (2097, 357, 2), (100, 1540, 2), (2200, 80, 1), (2200, 70, 1),
            (660, 80, 1), (657, 70, 2), (481, 80, 1), (481, 70, 1), (644, 80, 1), (380, 715, 1)]


def _business_m2(res) -> float:
    return sum(o.length * o.width / 1e6 * m.copies for m in res.maps for o in m.offcuts if o.kind == "remnant" and o.business)


def test_last_sheet_waste_is_one_business_remnant():
    items = [Item(f"p{i}", i, L, W, True) for i, (L, W, q) in enumerate(PRIHOJKA) for _ in range(q)]
    st = [StockSheet(id="s", length=2750, width=1830)]
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, min_trim_cut=5, max_rotations=6)
    res = optimize(items, st, cut, CSMaterialParams())
    assert res.total_sheets == 1 and not res.unplaced and not validate(res, items, st, cut)
    assert _business_m2(res) >= 0.85          # GibLab: 0.977 m²; siqishsiz bizda 0 edi (2740×261 tilim)


def test_compaction_respects_turn_limit_and_min_trim():
    items = []
    for i, (L, W, q) in enumerate(PRIHOJKA):
        items += [Item(f"p{i}", i, L, W, True) for _ in range(q)]
    st = [StockSheet(id="s", length=2750, width=1830)]
    for turns in (3, 4):
        cut = CSCutParams(kerf=4, trim_length=10, trim_width=10, min_trim_cut=10, max_rotations=turns, quality="fast")
        res = optimize(items, st, cut, CSMaterialParams())
        assert not res.unplaced and not validate(res, items, st, cut), turns
        for m in res.maps:
            assert all(c.level <= turns for c in m.commands if c.code in ("C", "P", "W"))


def _useful_business(res) -> float:
    """Деловой qoldiqlar «foydali» maydoni: list bo'yi/eni bo'ylab butun polosa — to'liq, «burchak» bo'lak — ×0.75
    (optimizer.REMNANT_CORNER_WEIGHT; foydalanuvchi talabi: qoldiq iloji boricha butun polosa bo'lsin)."""
    from app.services import optimizer as O
    tot = 0.0
    for m in res.maps:
        for o in m.offcuts:
            if o.kind == "remnant" and o.business:
                full = o.raw_length >= m.sheet_length - 1.0 or o.raw_width >= m.sheet_width - 1.0
                tot += o.length * o.width / 1e6 * m.copies * (1.0 if full else O.REMNANT_CORNER_WEIGHT)
    return tot


def test_compaction_never_reduces_business_area(monkeypatch):
    """Qoldiq yig'ish деловой qoldiqlarning foydali maydonini kamaytirmaydi (butun polosa afzal: burchak bo'lak ×0.75)."""
    from app.services import optimizer as O
    parts = [(211, 473, True, 4), (336.8, 454, False, 2), (438, 600, True, 4), (458.7, 604, True, 5)]
    items = [Item(f"p{i}", i, L, W, r) for i, (L, W, r, q) in enumerate(parts) for _ in range(q)]
    st = [StockSheet(id="m", length=2750, width=1830)]
    cut = CSCutParams(kerf=5, trim_length=15, trim_width=0, end_offset_bottom=0, max_rotations=4, min_trim_cut=10,
                      strip_sort=1, prefer_big_pack=False, fill_packet=70, quality="fast")
    mat = CSMaterialParams(remnant_min_side1=300, remnant_min_side2=200, remnant_min_area=0.0)
    on = optimize(items, st, cut, mat)
    monkeypatch.setattr(O, "COMPACT_BUDGET", {"fast": 0.0, "normal": 0.0, "max": 0.0})
    off = optimize(items, st, cut, mat)
    assert not validate(on, items, st, cut) and on.total_sheets == off.total_sheets
    assert _useful_business(on) >= _useful_business(off) - 0.01


def test_compaction_prefers_full_strip_remnant():
    """Oxirgi listdagi деловой qoldiq — list bo'yi yoki eni bo'ylab butun polosa (kvadrat burchak bo'lak emas)."""
    parts = [(211, 473, True, 4), (336.8, 454, False, 2), (438, 600, True, 4), (458.7, 604, True, 5)]
    items = [Item(f"p{i}", i, L, W, r) for i, (L, W, r, q) in enumerate(parts) for _ in range(q)]
    st = [StockSheet(id="m", length=2750, width=1830)]
    cut = CSCutParams(kerf=5, trim_length=15, trim_width=0, end_offset_bottom=0, max_rotations=4, min_trim_cut=10,
                      strip_sort=1, prefer_big_pack=False, fill_packet=70, quality="normal")
    mat = CSMaterialParams(remnant_min_side1=300, remnant_min_side2=200, remnant_min_area=0.0)
    res = optimize(items, st, cut, mat)
    assert not validate(res, items, st, cut)
    last = res.maps[-1]
    biz = [o for o in last.offcuts if o.kind == "remnant" and o.business]
    assert biz, "oxirgi listda деловой qoldiq bo'lishi kerak"
    big = max(biz, key=lambda o: o.length * o.width)
    assert big.raw_length >= last.sheet_length - 1.0 or big.raw_width >= last.sheet_width - 1.0


@pytest.mark.parametrize("fc, axis", [("LENGTH_PREF", "y"), ("WIDTH_PREF", "x")])
def test_compaction_keeps_preferred_first_cut(fc, axis):
    """«По длине/ширине предпочтительно»: to'liq bo'lmagan oxirgi list afzal yo'nalishda qoladi (C2)."""
    from app.models import FirstCutDir
    items = [Item(f"p{i}", i, L, W, True) for i, (L, W, q) in enumerate(PRIHOJKA) for _ in range(q)]
    st = [StockSheet(id="s", length=2750, width=1830)]
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, min_trim_cut=5, first_cut=FirstCutDir[fc], quality="fast")
    res = optimize(items, st, cut, CSMaterialParams())
    assert not validate(res, items, st, cut)
    assert res.maps[-1].strips[0]["a"] == axis


def test_min_strip_width_never_exceeds_sheet():
    """«Мин. ширина полосы» qolgan joydan katta bo'lsa polosa ochilmaydi (detal list tashqarisiga chiqmaydi)."""
    from app.models import FirstCutDir
    st = [StockSheet(id="m", length=2800, width=2070)]
    cut = CSCutParams(kerf=0, trim_length=5, trim_width=10, end_offset_right=0, first_cut=FirstCutDir.WIDTH_PREF,
                      max_rotations=3, min_trim_cut=5, max_part_types_per_map=3, min_strip_width=150, quality="fast")
    items = [Item("a", 1, 564, 80, True)] + [Item("b", 2, 2000, 450, True) for _ in range(5)] + [Item("c", 3, 2000, 397, True)]
    for _ in range(3):
        res = optimize(items, st, cut, CSMaterialParams(remnant_min_side1=1000, remnant_min_side2=200, remnant_min_area=0))
        assert not res.unplaced and not validate(res, items, st, cut)


def test_many_small_parts_respect_time_budget():
    """400 ta mayda detal (listda ~130 dona): «Быстро» rejimi soniyalarda tugaydi (avval ustunli qidiruv
    muddatga qaramay 45 s gacha cho'zilardi)."""
    import random
    import time
    r = random.Random(2)
    items = [Item(f"p{k}", k, r.randint(60, 300), r.randint(60, 210), True) for k in range(400)]
    st = [StockSheet(id="s", length=2750, width=1830)]
    t = time.monotonic()
    res = optimize(items, st, CSCutParams(quality="fast"), CSMaterialParams())
    assert time.monotonic() - t < 8.0
    assert not res.unplaced and res.total_sheets <= 3 and not validate(res, items, st, CSCutParams(quality="fast"))


# ───────────── Yangi detal: Ткт standarti (N_CHANGES #14) ─────────────
def test_new_part_grain_defaults_to_material_texture(client):
    p = client.post("/api/projects", json={"name": "Ткт"}).json()
    pid = p["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS"}).json()
    op = p["operations"][-1]
    assert op["cs_cut"]["use_grain"] is True
    p = client.post(f"/api/projects/{pid}/operations/{op['id']}/parts",
                    json=[{"length": 600, "width": 400}, {"length": 500, "width": 300, "grain": False}]).json()
    parts = p["operations"][-1]["parts"]
    assert [x["grain"] for x in parts] == [True, False]          # berilmagan → ✓; aniq berilgan saqlanadi
    op["cs_cut"]["use_grain"] = False                             # material teksturasiz
    op["parts"] = []
    client.put(f"/api/projects/{pid}/operations/{op['id']}", json=op)
    p = client.post(f"/api/projects/{pid}/operations/{op['id']}/parts", json=[{"length": 700, "width": 200}]).json()
    assert p["operations"][-1]["parts"][-1]["grain"] is False


# ───────────── XNC: paz o'tishlari va yoylar (GibLab saqlagan qiymatlar bilan) ─────────────
def test_groove_passes():
    assert [groove_passes(w, 4) for w in (3, 4, 6, 10, 10.5, 11, 26)] == [0, 1, 2, 4, 4, 4, 9]


def test_arc_sweep_major_arc():
    r, sw = arc_sweep((115.3267, -30), (50.6737, -30), (83.0002, -12), "true")
    assert math.isclose(r * sw, 153.8, abs_tol=0.2)      # katta yoy (GibLab: 342.33 − 2 × 94.25)
    r, sw = arc_sweep((83, 397), (68, 412), (83, 412), "false")
    assert math.isclose(sw, math.pi / 2, abs_tol=1e-6)


# ───────────── .project importi ─────────────
GL_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<project name="t" currency="UZS">
  <good id="1" typeId="product" name="Shkaf" count="2">
    <part id="100" dl="720" dw="280" l="718" w="280" count="2" minusCount="1" txt="true" name="Yon" elt="@operation#20"/>
  </good>
  <good id="2" typeId="sheet" name="LDSP Yasen" l="2800" w="2070" t="18" cost="450000">
    <part id="50" l="2800" w="2070" count="1000" cTrimL="-1" cTrimEL="4"/>
  </good>
  <good id="3" typeId="band" name="Yasen 1mm" w="22" t="1" cost="1500"/>
  <good id="4" typeId="tool.cutting" swSawthick="4.4" swMaxturns="4" swMinPruning="5" swSawthickDiv="-1"/>
  <good id="5" typeId="tool.edgeline" elRestSide="20" elMinSize="50" elWidthPreJoint="1"/>
  <operation id="10" typeId="CS" tool1="4" cTrimL="10" cTrimW="10" cTrimEL="-1" cTrimEW="0" csDirectCut="3"
             cCostByItem="true" cCostByItemRound="32" cCPF="0.9" cFillRep="0.85" cCostType="2" cSizeMode="1">
    <material id="2" used="base"/><part id="100"/>
  </operation>
  <operation id="20" typeId="EL" tool1="5" elSymbol="A" elWastePRC="10" elRoundMat="10" elRoundLength="21">
    <material id="3" used="base"/>
  </operation>
</project>"""


def test_import_project_mapping():
    p, _w = import_project(GL_XML, "t.project")
    cs = next(o for o in p.operations if o.type == OpType.CS)
    el = next(o for o in p.operations if o.type == OpType.EL)
    assert p.size_mode == SizeMode.DETAIL
    assert cs.cs_cut.kerf == 4.4 and cs.cs_cut.max_rotations == 4 and cs.cs_cut.kerf_group is None
    assert cs.cs_cut.end_offset_bottom is None and cs.cs_cut.end_offset_right == 0
    assert cs.cs_material.cost_by_sheets and cs.cs_material.sheet_rounding == SheetRounding.L_1_2
    assert cs.cs_material.est_fill_percent == 90 and cs.cs_cut.fill_packet == 85
    assert cs.cs_material.op_cost_base == OpCostBase.MATERIAL_AREA
    sh = cs.sheets[0]
    assert sh.trim_length is None and sh.end_offset_bottom == 4
    yon = cs.parts[0]
    assert (yon.length, yon.width, yon.qty, yon.minus_qty, yon.grain) == (720, 280, 2, 1, True)
    assert yon.edge_top.op_id == el.id
    assert el.el.material_round == 10 and el.el.work_round == 21 and el.el.waste_percent == 10


def test_import_sheet_count_100000_is_unlimited():
    """Real faylda «cheksiz» list soni 100000 bo'lishi mumkin (1230 Jamshid.project) — import qat'iy chegaradan yiqilmasin."""
    xml = GL_XML.replace(b'<part id="50" l="2800" w="2070" count="1000" cTrimL="-1" cTrimEL="4"/>',
                         b'<part id="50" l="2800" w="2070" count="100000"/>')
    p, _w = import_project(xml, "t.project")
    cs = next(o for o in p.operations if o.type == OpType.CS)
    assert [(s.length, s.width, s.qty) for s in cs.sheets] == [(2800, 2070, 10000)]


def test_import_sheets_limited_first():
    """Listlar ustuvorligi: soni cheklangan list avval, «cheksiz» (10000) oxirida; «waste» qoldiq qatori tushib qoladi."""
    xml = GL_XML.replace(
        b'<part id="50" l="2800" w="2070" count="1000" cTrimL="-1" cTrimEL="4"/>',
        b'<part id="50" l="2750" w="1830" count="10000" usedCount="0"/>'
        b'<part id="51" l="2140" w="1140" count="1" usedCount="1"/>'
        b'<part id="52" l="2337" w="1820" count="1" waste="true" business="true"/>')
    p, _w = import_project(xml, "t.project")
    cs = next(o for o in p.operations if o.type == OpType.CS)
    assert [(s.length, s.width, s.qty) for s in cs.sheets] == [(2140, 1140, 1), (2750, 1830, 10000)]


# Cheklangan listlar (qirqim + 2 ta butun list), to'lish 90.7 %, tekstura: oddiy qidiruv 1 detalni sig'dira olmasdi —
# «bin completion» barcha mavjud listlarga to'liq joylaydi (v2.5, _fit_limited). O'lchamlar real buyurtmadan (nomsiz).
LIMITED_3SHEETS = [
    (1870, 864, 1, True), (1970, 650, 1, True), (590, 864, 1, True), (864, 500, 2, True), (480, 650, 1, True),
    (690, 358, 1, False), (90, 1940, 2, False), (466, 362, 2, True), (90, 1430, 1, True), (172, 726, 1, True),
    (1870, 60, 2, True), (178, 484, 2, True), (690, 116, 2, False), (120, 650, 1, True), (100, 650, 1, True),
    (390, 129, 2, False), (60, 744, 4, True), (65, 634, 1, True), (234, 130, 2, True), (500, 60, 2, True),
    (109, 129, 2, True), (122, 108, 2, True), (178, 66, 2, True), (1568, 733, 1, True), (1568, 418, 2, True),
    (765, 418, 2, True),
]


def test_limited_stock_fits_all_parts():
    items = [Item(f"p{i}_{k}", i, L, W, not g) for i, (L, W, q, g) in enumerate(LIMITED_3SHEETS) for k in range(q)]
    st = [StockSheet(id="a", length=580, width=1830, qty=1), StockSheet(id="b", length=2750, width=1830, qty=2)]
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, max_rotations=6, quality="normal")
    res = optimize(items, st, cut, CSMaterialParams())
    assert not validate(res, items, st, cut)
    assert res.unplaced == [] and res.total_sheets == 3
