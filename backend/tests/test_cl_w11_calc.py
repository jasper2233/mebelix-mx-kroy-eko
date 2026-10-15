"""W11 — (CL) hisob-kitoblar: kroygacha taxmin (T-CL-5), narx asoslari, kromka / paz eni (CL-038), talabnoma, mahsulot ulushi."""
from app.models import (CLCostBase, CLParams, EdgeRef, ELParams, GrooveSide, GRParams, OpType, Operation, Part, Product, Project,
                        SheetRounding, StockSheet)
from app.services import calc, cl_calc


def _project(parts, cl=None, sheets=None, **proj):
    cl = cl or CLParams(width=100, kerf=3, trim=0)
    op = Operation(type=OpType.CL, code="PR-40", name="Profil 40", cl=cl, parts=parts,
                   sheets=sheets or [StockSheet(id="s", length=6000, width=cl.width)])
    p = Project(name="CL", operations=[op], products=[Product(id="pr1", name="Shkaf", qty=1)], **proj)
    for i, pt in enumerate(parts, 1):
        pt.uid = i
        pt.product_id = "pr1"
    return p, op


def _part(length, qty=1, **kw):
    return Part(length=length, width=0, qty=qty, **kw)


def test_tcl5_estimate_before_cut_price_per_m():
    cl = CLParams(width=100, kerf=3, trim=0, price=1000, est_fill_percent=90)
    p, op = _project([_part(2500, 2), _part(2500, 2)], cl)                # Σ = 10 m
    info = calc.cl_cost(p, op)
    assert info["estimated"] and abs(info["material_qty_m"] - 11.0) < 1e-9       # Σ × (2 − 90/100)
    assert op.cost_material == 11000.0 and op.cl.usage_m == 11.0
    calc.recalc_project(p)                                                      # har saqlashda shu hisob
    assert op.cost_material == 11000.0


def test_cost_after_cut_material_minus_business_and_bases():
    cl = CLParams(width=100, kerf=3, trim=10, price=2000, op_price=500, waste_min=100, business_min=1000,
                  op_cost_base=CLCostBase.CUT_WITH_TRIM)
    p, op = _project([_part(1000, 2), _part(500, 2)], cl)
    calc.run_linear(p, op)
    res = op.result
    assert res.kind == "linear" and res.total_sheets == 1 and not res.unplaced
    assert res.business_len_m > 2.9                                              # 6 m dan 3 m detal: katta деловой qoldiq
    qty = res.material_len_m - res.business_len_m
    assert abs(op.cl.usage_m - round(qty, 4)) < 1e-9
    assert op.cost_material == round(qty * 2000, 2)                              # деловой qoldiq sarfdan ayiriladi
    # operatsiya narxi: kesim uzunligi (torsovka bilan) = kesimlar × polosa eni
    assert abs(op.cost_operation - round(res.total_cut_length_m * 500, 2)) < 1e-6
    for base, expect in ((CLCostBase.MATERIAL_LEN, qty), (CLCostBase.PARTS_LEN, 3.0)):
        op.cl.op_cost_base = base
        info = calc.cl_cost(p, op)
        assert abs(info["op_base"] - expect) < 1e-3, base
    op.cl.op_cost_base = CLCostBase.CUT_NO_TRIM
    info = calc.cl_cost(p, op)
    m = res.maps[0]
    # torsovkasiz: kesimlar − boshidagi torsovka kesimi − oxirgi torsovka kesimi
    assert abs(info["op_base"] - round((m.cuts_count - 2) * 0.1, 3)) < 1e-6


def test_estimate_cut_length_two_cuts_per_part_times_width():
    cl = CLParams(width=60, kerf=3, trim=0, op_price=100, op_cost_base=CLCostBase.CUT_WITH_TRIM)
    p, op = _project([_part(1000, 3)], cl)
    info = calc.cl_cost(p, op)
    assert info["estimated"] and abs(info["op_base"] - 2 * 3 * 0.06) < 1e-9       # cTrimLengthP: 2 kesim × polosa eni
    assert op.cost_operation == round(2 * 3 * 0.06 * 100, 2)


def test_price_by_strip_rounding_fraction():
    cl = CLParams(width=100, kerf=3, trim=0, price=50000, price_by_strip=True, strip_rounding=SheetRounding.L_1_2)
    p, op = _project([_part(5000), _part(1000), _part(1900)], cl)                 # 2 polosa: ikkinchisida ~2.9/6 → 1/2 gacha
    calc.run_linear(p, op)
    assert op.result.total_sheets == 2
    assert abs(cl_calc.rounded_strip_count(op) - 1.5) < 1e-9
    assert op.cost_material == 75000.0


def test_multiplicity_from_pack_height_and_thickness():
    cl = CLParams(width=100, kerf=3, trim=0, pack_height=40, thickness=16)
    p, op = _project([_part(1000, 4)], cl)
    calc.cl_cost(p, op)
    assert op.cl.multiplicity == 2
    calc.run_linear(p, op)
    assert op.result.sheets_per_pack == 2
    assert all(m.packs == -(-m.copies // 2) for m in op.result.maps)


def test_cl038_end_edges_use_strip_width():
    """ОЛ/ОП (detal uchlari) kromka uzunligi = polosa eni; Part.width = 0 bo'lsa ham 0 chiqmaydi."""
    el = Operation(type=OpType.EL, name="PVC 1", el=ELParams(width=19, thickness=1, overhang=0, min_glue_length=0))
    p, op = _project([_part(1000, 2, edge_left=EdgeRef(op_id=el.id), edge_right=EdgeRef(op_id=el.id),
                            edge_top=EdgeRef(op_id=el.id))], CLParams(width=45, kerf=3, trim=0))
    p.operations.append(el)
    u = calc.edge_usage(p, el)
    # har detalda: 1 × uzunlik (1000) + 2 × eni (45) = 1090 mm × 2 dona
    assert abs(u["work_m"] - 2.18) < 1e-6 and u["rows"][0]["width"] == 45
    assert not u["narrow"]
    # kromka qalinligi uchlarda uzunlikni kamaytiradi: 1000 − 2 × 1 = 998 (detal rejimi)
    assert cl_calc.cl_items(p, op).items[0].length == 998.0


def test_cl_groove_usage_width():
    gr = Operation(type=OpType.GR, name="Paz", gr=GRParams(price=10))
    pt = _part(1000, 1, groove_left=GrooveSide(op_id=None), groove_top=GrooveSide(op_id=None))
    p, op = _project([pt], CLParams(width=45, kerf=3, trim=0))
    pt.groove_left = GrooveSide(op_id=gr.id)
    pt.groove_top = GrooveSide(op_id=gr.id)
    p.operations.append(gr)
    u = calc.groove_usage(p, gr)
    assert abs(u["usage"] - 1.045) < 1e-9                                         # 1000 (uzun tomon) + 45 (eni)


def test_warehouse_request_cl_rows_and_remnant_rows():
    cl = CLParams(width=100, kerf=3, trim=0, price=100, business_min=20000)
    sheets = [StockSheet(id="r", length=1500, width=100, qty=1, is_remnant=True, source_remnant_id=7),
              StockSheet(id="n", length=6000, width=100)]
    p, op = _project([_part(1400), _part(5000), _part(900)], cl, sheets=sheets)
    calc.run_linear(p, op)
    rows = [r for r in calc.warehouse_request(p) if r["type"] == "CL"]
    main = rows[0]
    assert main["unit_code"] == "m" and main["qty"] == round(op.cl.usage_m, 3)
    assert op.result.total_sheets == 2 and main["strips"] == 1                  # yangi polosalar (ombor qoldig'i alohida qatorda)
    rem = [r for r in rows if r.get("remnant")]
    assert rem and rem[0]["remnant_id"] == 7 and rem[0]["qty"] == 1
    cl2 = cl.model_copy(update={"price_by_strip": True})
    op.cl = cl2
    main2 = [r for r in calc.warehouse_request(p) if r["type"] == "CL"][0]
    assert main2["unit_code"] == "strips"


def test_product_cost_share_for_cl():
    cl = CLParams(width=100, kerf=3, trim=0, price=1000)
    p, op = _project([_part(1000, 2), _part(500, 2)], cl)
    p.products.append(Product(id="pr2", name="Tumba", qty=2))
    op.parts[1].product_id = "pr2"
    calc.run_linear(p, op)
    calc.recalc_project(p)
    s = {pr.id: pr for pr in p.products}
    tot = op.cost_material
    # ulush — detal uzunligi × soni: pr1 → 2000, pr2 → 1000 × (mahsulot soni 2 → 2000 → 2000): narx 1 dona uchun
    assert s["pr1"].cost_material > 0 and s["pr2"].cost_material > 0
    assert abs(s["pr1"].cost_material * 1 + s["pr2"].cost_material * 2 - tot) < 0.05


def test_cl_params_stale_rules():
    a = Operation(type=OpType.CL, cl=CLParams())
    b = a.model_copy(deep=True)
    b.cl.price = 123                                                              # narx natijani eskirtirmaydi
    b.cl.quality = "max"
    assert not cl_calc.cl_params_stale(a, b)
    for field, val in (("kerf", 5.0), ("trim", 20.0), ("end_offset", 5.0), ("waste_min", 50.0), ("business_min", 300.0),
                       ("waste_incl_trim", False), ("width", 77.0), ("min_part_len", 10.0)):
        c = a.model_copy(deep=True)
        setattr(c.cl, field, val)
        assert cl_calc.cl_params_stale(a, c), field


def test_uncomputed_imported_parts_flagged_not_cut():
    cl = CLParams(width=7, kerf=3, trim=10)
    ok = _part(500, 2)
    unc = Part(length=0, width=0, qty=3, src_length=-350.0)
    p, op = _project([ok, unc], cl)
    calc.run_linear(p, op)
    res = op.result
    assert res.total_parts == 2
    assert res.unplaced.count(unc.id) == 3 and any("3" in w for w in res.warnings)
    assert unc.left_qty == 3 and unc.used_qty == 0 and ok.used_qty == 2
