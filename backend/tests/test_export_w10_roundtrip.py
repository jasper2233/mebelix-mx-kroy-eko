"""W10: `.project` eksporti — sintetik loyiha → eksport → importer → ma'lumotlar teng (detallar, kromkalar, CS parametrlari,
XNC dasturlari, O qatorlari, LB, GR); «yoyilgan» XNC dasturlari; eksport tekshiruvchisi (sxema); chekka holatlar.
Mijoz ma'lumoti ishlatilmaydi — hamma loyiha shu faylda qurilgan."""
from __future__ import annotations

import copy
import re
import xml.etree.ElementTree as ET
from datetime import date

import pytest

from app.models import (CSCutParams, CSMaterialParams, ELParams, EdgeRef, FirstCutDir, GRParams, GrooveSide, LBParams,
                        OMaterial, OParams, OpCostBase, OpType, Operation, Part, Product, Project, SheetRounding, SizeMode,
                        StockSheet, StripSort, XncCommand, XNCParams)
from app.plugins.legacy_project import import_project, program_to_commands
from app.services import xnc as X
from app.services.project_export import (ExportError, LB_PROGRAM_EXPORTERS, export_project, safe_filename)
from app.services.project_export_xnc import needs_flatten, program_xml
from app.services.project_schema import schema_vocabulary, unknown_vocabulary, validate_project_xml, vocabulary
from app.services.xnc_templates import LIBRARY, library_program
from w10_helpers import canon, diff, metrics

LB_PROGRAM = ('<?xml version="1.0" encoding="UTF-8"?><program columns="2" dx="89" dy="60.25" gap="10" margin="true" '
              'printMode="0" rows="4"/>')


def C(cmd, comment="", enabled=True, **params):
    return XncCommand(cmd=cmd, params=params, comment=comment, enabled=enabled)


def plain_program() -> list[XncCommand]:
    """Formatda teg nomi bor hamma buyruqlar (yoyilmaydigan dastur)."""
    return [
        C("Tool", N="Bore8", D=8.0), C("Tool", N="Mill6", D=6.0),
        C("Var", "Chuqurlik", name="depth", value="dz+3", type="double"),
        C("Var", name="k", value=2.5, type="double"),
        C("DrillFront", X=8.0, Y=70.0, DP="depth", AC=3.0, AS=32.0, AV="true", T="Bore8"),
        C("DrillFront", X=50.0, Y=100.0, DP=10.0, AC=1.0, AV="false", T="Bore8"),
        C("DrillLeft", Y=70.0, Z=8.0, M="true", DP=34.0, AC=1.0, VER=2.0, T="Bore8"),
        C("DrillRight", Y=70.0, Z=5.0, M="false", DP=34.0, AC=1.0, VER=2.0, T="Bore8"),
        C("DrillTop", X=100.0, Z=8.0, M="true", DP=20.0, AC=1.0, VER=2.0, T="Bore8"),
        C("DrillBottom", X=200.0, Z=7.0, M="false", DP=20.0, AC=1.0, VER=2.0, T="Bore8"),
        C("Origin", X=10.0, Y=5.0),
        C("MillStart", "kontur", X=0.0, Y=0.0, DP="dz", T="Mill6", C=2.0, SDP=5.0, SXY=2.0, IN=1.0, OUT=1.0),
        C("MillLine", X=100.0, Y=0.0), C("MillLine", X=100.0, Y=50.0, DP=8.0),
        C("MillArc", X=150.0, Y=100.0, R=60.0, DIR="true"),
        C("MillArcCenter", X=150.0, Y=200.0, CX=100.0, CY=150.0, DIR="false", DP="dz"),
        C("Groove", X1=0.0, Y1=30.0, X2=300.0, Y2=30.0, DP=8.0, W=4.0, T="Mill6", C=1.0, P=0.0),
        C("Groove", enabled=False, comment="o'chirilgan", X1=0.0, Y1=60.0, X2=300.0, Y2=60.0, DP=8.0, W=4.0, T="Mill6", C=0.0),
        C("DrillFront", "o'chirilgan teshik", enabled=False, X=300.0, Y=300.0, DP=5.0, T="Bore8"),
    ]


def make_project(mode: SizeMode = SizeMode.DETAIL, turns: int = 4) -> Project:
    p = Project(name="W10 sinov loyiha", currency="UZS", order_date=date(2026, 9, 1), ready_date=date(2026, 9, 20),
                note="Loyiha izohi", size_mode=mode)
    p1 = Product(code="K-1", name="Shkaf", qty=2, order_info="Buyurtma 17", phone1="+998 90 111 22 33", description="Tavsif",
                 extra={"product.import": "bm.1.86", "product.color": "oq"})
    p2 = Product(name="Tumba", qty=3)
    p.products = [p1, p2]
    el1 = Operation(type=OpType.EL, code="PVC-19", name="PVC 0.4x19",
                    el=ELParams(width=19, thickness=0.4, jointing_width=1, overhang=30, min_glue_length=50, symbol="B",
                                color="#ff0000", marker_lines=2, price=1.5, op_price=0.5, waste_percent=3, min_perp_side=40,
                                count_material=False, material_round=11, work_round=21), description="Qizil kromka")
    el2 = Operation(type=OpType.EL, code="PVC-22", name="PVC 2x22", print=False, new_page=False,
                    el=ELParams(width=22, thickness=2, jointing_width=0, overhang=20, min_glue_length=0, symbol="C",
                                color="#00aa00", marker_lines=3, price=3, op_price=1))
    gr = Operation(type=OpType.GR, name="Orqa paz", description="paz izohi",
                   gr=GRParams(width=6, depth=9, offset=12, offset_inclusive=False, saw_thickness=3, price=2.5))
    parts = [
        Part(name="Yon", code="K1-01", description="Yon devor", length=720, width=560, qty=2, grain=True, minus_qty=1,
             edge_top=EdgeRef(op_id=el1.id), edge_bottom=EdgeRef(op_id=el2.id), edge_left=EdgeRef(op_id=el1.id),
             allow_top=2, allow_right=1.5, group_by="length", group_min=2, group_max=4, product_id=p1.id),
        Part(name="Tub", code="K1-02", length=564, width=300, qty=1, edge_top=EdgeRef(op_id=el2.id), product_id=p1.id,
             groove_top=GrooveSide(op_id=gr.id), groove_left=GrooveSide(op_id=gr.id, back_side=True)),
        Part(name="Tokcha", length=560, width=280, qty=4, product_id=p2.id, group_by="width", group_min=3, group_max=0),
        Part(name="", length=0, width=0, qty=1, product_id=p2.id),        # to'ldirilmagan (bo'sh) qator
    ]
    xnc = Operation(type=OpType.XNC, code="K1-01-XNC", name="Yon devor", description="Presadka",
                    xnc=XNCParams(by_part_size=False, length=720, width=560, thickness=18, qty=2, face_side=False,
                                  rotation=90, mirror_x=True, mirror_y=False, drill_price=0.2, mill_price_m=3, saw_price_m=4,
                                  extra_cost=1, program=plain_program()),
                    xnc_part_id=parts[0].id)
    parts[0].xnc_op_ids = [xnc.id]
    cs = Operation(
        type=OpType.CS, code="LDSP18", name="LDSP Oq 18", description="CS izoh",
        cs_material=CSMaterialParams(thickness=18, price=120000, est_fill_percent=85, cost_by_sheets=False,
                                     sheet_rounding=SheetRounding.W_1_2, op_cost_base=OpCostBase.MATERIAL_AREA, op_price=5.5,
                                     remnant_min_side1=800, remnant_min_side2=400, remnant_min_area=0.3,
                                     remnant_size_incl_trim=False, min_part_size=25),
        cs_cut=CSCutParams(kerf=4.4, kerf_group=2.0, trim_length=10, trim_width=12, trim_includes_kerf=True,
                           end_offset_bottom=8, end_offset_right=None, first_cut=FirstCutDir.LENGTH_PREF, use_grain=False,
                           complex_strips=False, max_rotations=turns, pack_height=50, fill_packet=80,
                           max_part_types_per_map=5, prefer_big_pack=False, strip_sort=StripSort.ASC,
                           in_strip_sort=StripSort.NARROW_CENTER, min_strip_width=100, max_strip_width=900,
                           max_strip_length=3000, min_trim_cut=7, merge_parts=True, save_drawings=False, machining_allowance=2),
        sheets=[StockSheet(length=1200, width=600, qty=1, description="qoldiq"),
                StockSheet(length=2800, width=2070, qty=3, trim_length=5, trim_width=6, end_offset_bottom=0, end_offset_right=4),
                StockSheet(length=2750, width=1830, qty=10000)],
        parts=parts)
    owner = Operation(type=OpType.O, name="Furnitura", description="O izoh",
                      o=OParams(owner_product_id=p1.id, work_cost=15000.0,
                                materials=[OMaterial(code="F-1", name="Petlya", unit="шт", qty=4, price=2500),
                                           OMaterial(code="F-2", name="Vint", unit="кг", qty=0.5, price=12000)]))
    lb = Operation(type=OpType.LB, name="Etiketkalar", description="LB izoh",
                   lb=LBParams(source="parts", mode="sheet", columns=2, rows=4, gap_mm=10, margin_mm=6.0, width_mm=89,
                               height_mm=60.25, print_parts=True, part_each=False, part_only_nonzero=False,
                               print_wastes=True, waste_each=False, product_each=False, product_only_nonzero=False,
                               fields=[dict(name="qty", title="qty", type="integer", width=10.0, default="1")],
                               legacy_program=LB_PROGRAM))
    p.operations = [owner, cs, el1, el2, gr, xnc, lb]
    return p


def rt(p: Project, **kw):
    res = export_project(p)
    p2, warns = import_project(res.xml, "x.project")
    return res, p2, warns


# ───────────────────────── 1. aylanma: ma'lumotlar teng ─────────────────────────
@pytest.mark.parametrize("mode", list(SizeMode))
def test_synthetic_roundtrip_data_equal_in_every_size_mode(mode):
    p = make_project(mode)
    before = copy.deepcopy(p)
    res, p2, warns = rt(p)
    assert p.model_dump() == before.model_dump()                     # eksport loyihani o'zgartirmaydi
    assert diff(canon(p), canon(p2)) == []
    assert p2.size_mode == mode and len(p2.operations) == 7
    assert len(warns) == 1 and "LB" in warns[0], warns               # LB shablon matni (program) haqida import ogohlantirishi
    assert metrics(p) == metrics(p2)                                 # detallar soni/maydoni, kromka metri, XNC statistikasi


def test_roundtrip_covers_specific_values():
    p = make_project()
    _res, p2, _w = rt(p)
    cs = next(o for o in p2.operations if o.type == OpType.CS)
    assert cs.code == "LDSP18" and cs.name == "LDSP Oq 18" and cs.description == "CS izoh"
    assert [s.qty for s in cs.sheets] == [1, 3, 10000] and cs.sheets[0].description == "qoldiq"
    assert (cs.sheets[1].trim_length, cs.sheets[1].trim_width, cs.sheets[1].end_offset_bottom,
            cs.sheets[1].end_offset_right) == (5, 6, 0, 4)
    assert cs.cs_cut.max_rotations == 4 and cs.cs_cut.kerf_group == 2.0 and cs.cs_cut.first_cut == FirstCutDir.LENGTH_PREF
    assert cs.cs_cut.end_offset_right is None and cs.cs_cut.end_offset_bottom == 8
    assert cs.cs_material.op_cost_base == OpCostBase.MATERIAL_AREA and cs.cs_material.sheet_rounding == SheetRounding.W_1_2
    pr = p2.products[0]
    assert (pr.code, pr.qty, pr.order_info, pr.phone1, pr.description) == ("K-1", 2, "Buyurtma 17", "+998 90 111 22 33", "Tavsif")
    assert pr.extra == {"product.import": "bm.1.86", "product.color": "oq"}
    assert (p2.order_date, p2.ready_date, p2.note) == (date(2026, 9, 1), date(2026, 9, 20), "Loyiha izohi")
    el = [o for o in p2.operations if o.type == OpType.EL]
    assert el[0].el.symbol == "B" and el[0].el.count_material is False and el[1].print is False
    x = next(o for o in p2.operations if o.type == OpType.XNC)
    assert x.xnc.rotation == 90 and x.xnc.mirror_x and not x.xnc.face_side and x.xnc_part_id
    assert len(x.xnc.program) == 19 and x.xnc.program[-1].enabled is False
    o = next(o for o in p2.operations if o.type == OpType.O)
    assert o.o.owner_product_id == p2.products[0].id and len(o.o.materials) == 2 and o.o.work_cost == 15000.0


def test_max_rotations_one_roundtrips():
    p = make_project(turns=1)
    res, p2, _w = rt(p)
    assert b'swMaxturns="1"' in res.xml and "rot_one" in {w["code"] for w in res.warnings}
    assert next(o for o in p2.operations if o.type == OpType.CS).cs_cut.max_rotations == 1
    assert "rot_one" not in {w["code"] for w in export_project(make_project(turns=2)).warnings}


def test_importer_accepts_one_rotation_and_rejects_out_of_range_in_models():
    xml = b'<project><good id="1" typeId="tool.cutting" swMaxturns="1"/><good id="2" typeId="sheet" name="M" t="16"/>' \
          b'<operation id="3" typeId="CS" tool1="1" cSizeMode="1"><material id="2"/></operation></project>'
    p, _w = import_project(xml, "a.project")
    assert p.operations[0].cs_cut.max_rotations == 1
    with pytest.raises(Exception):
        CSCutParams(max_rotations=0)
    with pytest.raises(Exception):
        CSCutParams(max_rotations=7)
    assert CSCutParams.model_validate({"max_rotations": 0}, context={"legacy": True}).max_rotations == 1


# ───────────────────────── 2. fayl tuzilmasi ─────────────────────────
def test_file_structure_matches_open_format_description():
    p = make_project()
    res = export_project(p)
    assert res.xml.startswith(b'<?xml version="1.0" encoding="UTF-8"?>\n<project ')
    root = ET.fromstring(res.xml)
    assert root.get("version") == "1"                                  # tavsifdagi standart (o'ylab topilmagan)
    assert re.fullmatch(r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}", root.get("project.uuid"))
    assert root.get("date").isdigit() and root.get("orderDate").isdigit() and root.get("currency") == "UZS"
    goods = {g.get("typeId") for g in root.findall("good")}
    assert goods >= {"product", "tool.cutting", "sheet", "tool.edgeline", "band", "simple"}
    ops = [o.get("typeId") for o in root.findall("operation")]
    assert ops == ["O", "CS", "EL", "EL", "GR", "XNC", "LB"]               # operatsiyalar tartibi saqlanadi
    # natija atributlari yozilmaydi
    for o in root.findall("operation"):
        assert not {"data", "draw", "cFilling", "cMaterialCount", "cTrimLength", "costTotal", "cost"} & set(o.attrib)
    # id lar butun loyiha bo'ylab noyob
    # id ta'riflari: ildizdagi good / operation va mahsulot ichidagi part (mahsulot ichidagi `<operation id>` — havola, X_1015 §9)
    ids = [e.get("id") for e in root if e.tag in ("good", "operation")] + \
          [x.get("id") for g in root.findall("good") for x in g.findall("part")]
    assert len(ids) == len(set(ids))
    # kromka / paz havolalari `@operation#N`
    el_ids = {o.get("id") for o in root.findall("operation") if o.get("typeId") == "EL"}
    first = root.find("good[@typeId='product']/part")
    assert re.fullmatch(r"@operation#\d+", first.get("elt")) and first.get("elt")[len("@operation#"):] in el_ids
    assert first.get("allowanceT") == "2" and first.get("groupInBlock") == "1"
    gr_part = root.findall("good[@typeId='product']/part")[1]
    assert gr_part.get("grts") is None and gr_part.get("grls") == "false"      # orqa tomon — grls=false
    # XNC program — ichki XML
    xo = next(o for o in root.findall("operation") if o.get("typeId") == "XNC")
    prog = ET.fromstring(xo.get("program"))
    assert prog.tag == "program" and (prog.get("dx"), prog.get("dy"), prog.get("dz")) == ("720", "560", "18")
    assert [c.tag for c in prog][:6] == ["tool", "tool", "var", "var", "bf", "bf"] and xo.get("turn") == "1"
    assert xo.find("part") is not None


def test_two_exports_differ_only_in_uuid_and_validate_against_schema():
    p = make_project()
    a, b = export_project(p), export_project(p)
    ua, ub = (re.search(rb'project\.uuid="([^"]+)"', r.xml).group(1) for r in (a, b))
    assert ua != ub
    assert a.xml.replace(ua, b"-") == b.xml.replace(ub, b"-")
    assert validate_project_xml(a.xml) == []
    assert unknown_vocabulary(vocabulary(a.xml)) == set()


def test_filename_is_safe_and_dated_in_local_noon():
    p = Project(name='A/B:C*?"<>| nom.', number=7)
    assert safe_filename(p) == "A B C nom.project"
    assert safe_filename(Project(name="", number=12)) == "12.project"
    r = export_project(Project(name="x", order_date=date(2026, 1, 1), ready_date=date(2026, 12, 31)))
    root = ET.fromstring(r.xml)
    from datetime import datetime, timezone
    noon = lambda y, m, d: str(int(datetime(y, m, d, 7, tzinfo=timezone.utc).timestamp() * 1000))      # 12:00 UTC+5
    assert root.get("orderDate") == noon(2026, 1, 1) and root.get("date") == noon(2026, 12, 31)


def test_control_characters_are_stripped_and_xml_stays_valid():
    p = make_project()
    p.name = "Nom\x00\x08\x0b bilan"
    p.products[0].name = "Shkaf\x1f<&>\"'"
    res, p2, _w = rt(p)
    assert p2.name == "Nom bilan" and p2.products[0].name == "Shkaf<&>\"'"
    assert validate_project_xml(res.xml) == []


def test_empty_project_exports_and_imports():
    res, p2, _w = rt(Project(name="Bo'sh"))
    assert p2.products == [] and p2.operations == [] and p2.name == "Bo'sh"
    assert res.warnings == []


# ───────────────────────── 3. ogohlantirishlar (nima o'tkazib yuborildi) ─────────────────────────
def _codes(res):
    return {w["code"] for w in res.warnings}


def test_warnings_report_what_was_skipped():
    p = make_project()
    p.products[0].extra["bad key"] = "1"                               # nuqtasiz / bo'sh joyli kalit — atribut bo'la olmaydi
    p.products[1].ready_date = "tez orada"
    p.customer = "Mijoz"
    p.operations.append(Operation(type=OpType.CN, name="Nesting"))
    p.operations[1].sheets[0].is_remnant = True
    p.operations[1].cs_material.est_fill_percent = 40
    p.operations[5].xnc.origin = "RB"
    p.operations[6].lb.fields = []
    p.operations[6].lb.legacy_program = ""
    res = export_project(p)
    assert {"op_skipped", "extra_key", "dropped", "remnant_sheet", "fill_ambig", "xnc_origin", "lb_no_program"} <= _codes(res)
    assert {w["level"] for w in res.warnings} == {"warn", "info"}
    assert all(w["text"] and "{" not in w["text"] for w in res.warnings)
    text = " ".join(w["text"] for w in res.warnings)
    assert "bad key" in text and "Nesting" in text and "RB" in text
    p2 = import_project(res.xml, "x.project")[0]
    assert "bad key" not in p2.products[0].extra
    assert [o.type for o in p2.operations].count(OpType.CN) == 0


def test_results_note_when_maps_exist():
    from app.models import CutMap, CuttingResult
    p = make_project()
    p.operations[1].result = CuttingResult(maps=[CutMap(index=1, sheet_id="s", sheet_length=2750, sheet_width=1830)])
    res = export_project(p)
    assert "results_note" in _codes(res)
    assert b"cFilling" not in res.xml and b"data=" not in res.xml


def test_parts_without_product_go_to_a_placeholder_product():
    p = make_project()
    p.operations[1].parts.append(Part(name="Yetim", length=300, width=200, qty=2, product_id=None))
    p.operations[1].parts.append(Part(name="Begona", length=100, width=100, qty=1, product_id="yo'q-mahsulot"))
    res, p2, _w = rt(p)
    assert "noproduct" in _codes(res)
    assert len(p2.products) == 3 and p2.products[2].qty == 1
    cs = next(o for o in p2.operations if o.type == OpType.CS)
    orphans = [pt for pt in cs.parts if pt.product_id == p2.products[2].id]
    assert [pt.name for pt in orphans] == ["Yetim", "Begona"]


def test_dangling_edge_and_groove_references_are_not_written():
    p = make_project()
    cs = p.operations[1]
    cs.parts[0].edge_right = EdgeRef(op_id="yo'q")
    cs.parts[1].groove_bottom = GrooveSide(op_id=p.operations[2].id)       # EL ni paz deb ko'rsatgan
    res = export_project(p)
    assert "dangling_ref" in _codes(res)
    assert validate_project_xml(res.xml) == []


def test_xnc_shared_by_two_parts_warns():
    p = make_project()
    cs = p.operations[1]
    x = p.operations[5]
    cs.parts[2].xnc_op_ids = [x.id]
    res = export_project(p)
    assert "xnc_shared" in _codes(res)


def test_lb_program_exporter_hook_is_used_when_no_legacy_program():
    p = make_project()
    p.operations[6].lb.legacy_program = ""
    LB_PROGRAM_EXPORTERS.append(lambda lb: LB_PROGRAM)
    try:
        res = export_project(p)
    finally:
        LB_PROGRAM_EXPORTERS.pop()
    assert "lb_no_program" not in _codes(res)
    assert next(o for o in ET.fromstring(res.xml).findall("operation") if o.get("typeId") == "LB").get("program") == LB_PROGRAM


def test_warnings_follow_ui_language():
    from app.i18n import LANG
    p = make_project()
    p.operations.append(Operation(type=OpType.CN, name="Nesting"))
    tok = LANG.set("uz")
    try:
        uz = " ".join(w["text"] for w in export_project(p).warnings)
    finally:
        LANG.reset(tok)
    ru = " ".join(w["text"] for w in export_project(p).warnings)
    assert "eksport qilinmadi" in uz and "не экспортирована" in ru


# ───────────────────────── 4. SP (W12) ─────────────────────────
def test_sp_operation_is_exported_with_part_links():
    from app.models import SPParams
    p = make_project()
    sp = Operation(type=OpType.SP, name="Lak", sp=SPParams(count_material=False, waste_percent=5, rest_side=10, size_mode=0,
                                                           op_price=7, price=3))
    p.operations.append(sp)
    cs = p.operations[1]
    cs.parts[0].surface_face_op = sp.id
    cs.parts[2].surface_back_op = sp.id
    res = export_project(p)
    assert {"sp_side", "dropped"} <= _codes(res)
    root = ET.fromstring(res.xml)
    so = next(o for o in root.findall("operation") if o.get("typeId") == "SP")
    assert so.get("spCalcMat") == "false" and so.get("spSizeMode") == "0" and so.get("spCost") == "7"
    assert len(so.findall("part")) == 2
    p2 = import_project(res.xml, "x.project")[0]
    sp2 = next(o for o in p2.operations if o.type == OpType.SP)
    assert (sp2.name, sp2.sp.count_material, sp2.sp.waste_percent, sp2.sp.rest_side, sp2.sp.size_mode, sp2.sp.op_price) == \
        ("Lak", False, 5, 10, 0, 7)


# ───────────────────────── 5. XNC: «yoyilgan» dasturlar ─────────────────────────
def _stats_of(xml_text: str, x: XNCParams) -> dict:
    cmds, size = program_to_commands(xml_text)
    return X.xnc_stats(x.model_copy(update=dict(program=cmds, length=size[0], width=size[1], thickness=size[2], par_values={})))


@pytest.mark.parametrize("key", list(LIBRARY))
def test_library_templates_export_with_same_statistics(key):
    prog = library_program(key, "ru")
    x = XNCParams(by_part_size=False, length=720, width=560, thickness=16, program=prog)
    notes = []
    txt = program_xml(x, key, lambda kind, kw: notes.append(kind))
    s0, s1 = X.xnc_stats(x), _stats_of(txt, x)
    assert s0["errors"] == 0 and s1["errors"] == 0
    assert s1["drills"] == s0["drills"]
    assert s1["mill_m"] == pytest.approx(s0["mill_m"], abs=0.002) and s1["saw_m"] == pytest.approx(s0["saw_m"], abs=0.002)
    assert ("flat" in notes) == needs_flatten(prog)
    root = ET.fromstring(txt.split("?>", 1)[1])
    assert set(c.tag for c in root) <= {"tool", "var", "bf", "bl", "br", "bt", "bb", "ms", "ml", "ma", "mac", "gr", "xy"}


def test_flatten_handles_rect_ellipse_arc3p_fillet_loops_and_par_values():
    prog = [
        C("Par", name="n", value=3.0, label="Soni", type="integer"),
        C("Par", name="r", value=20.0, label="Radius"),
        C("Tool", N="B5", D=5.0), C("Tool", N="M8", D=8.0),
        C("Var", name="i", value=0.0),
        XncCommand(cmd="While", params={"cond": "i<n"}, children=[
            C("DrillFront", X="50+i*32", Y=37.0, DP=13.0, T="B5"), C("Set", name="i", value="i+1")]),
        C("MillRect", X=360.0, Y=280.0, L=200.0, W=100.0, R="r", A=15.0, DP=6.0, T="M8"),
        C("MillEllipse", X=200.0, Y=400.0, RL=60.0, RW=30.0, A=0.0, DP=5.0, T="M8"),
        C("MillStart", X=500.0, Y=100.0, DP=4.0, T="M8", C=0.0),
        C("MillArc3P", X=560.0, Y=160.0, X2=545.0, Y2=120.0),
        C("MillLine", X=500.0, Y=200.0), C("MillLine", X=400.0, Y=200.0), C("MillFillet", R=15.0),
        C("MillLine", X=400.0, Y=100.0),
    ]
    x = XNCParams(by_part_size=False, length=720, width=560, thickness=16, program=prog, par_values={"n": 5.0})
    notes: list = []
    txt = program_xml(x, "T1", lambda kind, kw: notes.append(kind))
    assert "flat" in notes
    s0, s1 = X.xnc_stats(x), _stats_of(txt, x)
    assert (s0["drills"], s1["drills"]) == (5, 5)                       # kiritilgan Par qiymati (n=5) hisobga olingan
    assert s0["errors"] == 0 and s1["mill_m"] == pytest.approx(s0["mill_m"], rel=0.01)
    assert s1["mill_m"] > 1.2
    assert "<ml" in txt and "<mac" in txt and "<ms" in txt


def test_plain_program_with_par_becomes_var_with_entered_value():
    prog = [C("Par", name="d", value=8.0, label="Diametr", type="double"), C("Tool", N="B", D="d"),
            C("DrillFront", X=10.0, Y=10.0, DP=5.0, T="B")]
    x = XNCParams(by_part_size=False, length=100, width=100, thickness=16, program=prog, par_values={"d": 6.0})
    notes: list = []
    txt = program_xml(x, "P", lambda kind, kw: notes.append(kind))
    assert notes == ["par"] and not needs_flatten(prog)
    cmds, _size = program_to_commands(txt)
    assert cmds[0].cmd == "Var" and cmds[0].params["value"] == 6.0 and cmds[0].comment == "Diametr"


def test_flattened_program_skips_outside_holes_and_bad_contours():
    prog = [C("Tool", N="B", D=5.0), C("If", cond="1"), C("DrillFront", X=5000.0, Y=10.0, DP=5.0, T="B"),
            C("DrillFront", X=10.0, Y=10.0, DP=5.0, T="B")]
    prog[1] = XncCommand(cmd="If", params={"cond": "1"}, children=[prog[2], prog[3]])
    x = XNCParams(by_part_size=False, length=100, width=100, thickness=16, program=[prog[0], prog[1]])
    txt = program_xml(x, "O", lambda *_a: None)
    assert txt.count("<bf") == 1                                           # detaldan tashqaridagi teshik bajarilmaydi


# ───────────────────────── 6. sxema tekshiruvchisi ─────────────────────────
GOOD = ('<project version="1"><good id="1" typeId="product" name="P" count="1"><part id="5" l="100" w="50" count="1" txt="false"/>'
        '</good><good id="2" typeId="tool.cutting"/><good id="3" typeId="sheet" name="M" t="16"><part id="6" l="2750" w="1830" '
        'count="10000"/></good><operation id="4" typeId="CS" tool1="2" cSizeMode="0"><material id="3"/><part id="5"/>'
        '<part id="6"/></operation></project>')


def test_validator_accepts_minimal_valid_file():
    assert validate_project_xml(GOOD) == []


@pytest.mark.parametrize("mutate,needle", [
    (lambda s: s.replace('<good id="2" typeId="tool.cutting"/>', '<good id="2" typeId="tool.cutting" foo="1"/>'), "foo"),
    (lambda s: s.replace('id="6" l=', 'id="5" l='), "takroriy"),
    (lambda s: s.replace('tool1="2"', 'tool1="9"'), "tool1"),
    (lambda s: s.replace('<material id="3"/>', '<material id="42"/>'), "material"),
    (lambda s: s.replace('<part id="6"/></operation>', '<part id="77"/></operation>'), "77"),
    (lambda s: s.replace('txt="false"', 'txt="yes"'), "txt"),
    (lambda s: s.replace('count="1" txt', 'count="x" txt'), "count"),
    (lambda s: s.replace('<project version="1">', '<project version="1" bogus="1">'), "bogus"),
    (lambda s: s.replace('typeId="CS"', 'typeId="QQ"'), "QQ"),
    (lambda s: s.replace('l="100" w="50"', ''), "o'lcham"),
    (lambda s: s.replace('<material id="3"/>', ''), "material"),
    (lambda s: s.replace('</project>', '<operation id="8" typeId="XNC"/></project>'), "program"),
    (lambda s: s.replace('</project>', '<operation id="8" typeId="XNC" program="&lt;program dx=&quot;1&quot; dy=&quot;1&quot; '
                                       'dz=&quot;1&quot;&gt;&lt;zz/&gt;&lt;/program&gt;"/></project>'), "zz"),
    (lambda s: s.replace('count="1" txt="false"', 'count="1" txt="false" elt="@operation#4"'), "elt"),
])
def test_validator_catches_problems(mutate, needle):
    errs = validate_project_xml(mutate(GOOD))
    assert errs and any(needle in e for e in errs), errs


def test_validator_strict_vs_real_boolean_forms():
    s = GOOD.replace('txt="false"', 'txt="1"')
    assert validate_project_xml(s, strict=True) and validate_project_xml(s, strict=False) == []
    assert validate_project_xml("<nope/>") and validate_project_xml("<project>")


def test_export_error_when_schema_check_fails(monkeypatch):
    from app.services import project_export as pe
    monkeypatch.setattr(pe, "validate_project_xml", lambda *_a, **_k: ["buzuq"])
    with pytest.raises(ExportError) as ei:
        export_project(make_project())
    assert ei.value.errors == ["buzuq"]
    assert export_project(make_project(), validate=False).xml


def test_schema_vocabulary_covers_everything_the_exporter_writes():
    res = export_project(make_project())
    allowed = schema_vocabulary()
    found = vocabulary(res.xml)
    assert found <= allowed | {(k, a) for k, a in found if k.startswith("good[product]") and a.startswith("product.")}



