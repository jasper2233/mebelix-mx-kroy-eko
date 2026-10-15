# -*- coding: utf-8 -*-
"""§11 (2026-10-15, 2-sessiya) — «Печать отчета» sozlamalari oynalari: yangi PrintSettings maydonlari (standartlar xodimlar
o'rgangan tizimdagidek), ustunlar jadvallari (`map_header_cols`, `xnc_stat_cols`) ↔ eski maydonlar, hisobotga ulanishi:
materiallar guruhlash, mahsulot/operatsiya ro'yxatlari, XNC statistika ustunlari va guruhlash, (CS) talabnoma/statistika,
kromka belgilari va «Форма печати деталей», karta ko'zgu rejimlari, kromka marker uslubi, ifoda qiymati, ishlov belgilari,
sahifa chegaralari (ko'zgu, kolontitul) va (XNC) orqa tomon ko'zgusi."""
import re

from app import store
from app.models import (CSCutParams, CSMaterialParams, CutMap, CutCommand, Operation, OpType, Part, Placement, PrintCol,
                        PrintSettings, Product, Project, ELParams, EdgeRef, XNCParams, XncCommand)
from app.services import render, settings


# ───────────────────────── model: standartlar va ustunlar jadvallari ─────────────────────────
def test_defaults_match_reference_dialogs():
    ps = PrintSettings()
    # «Настройки печати»
    assert (ps.header, ps.materials_list, ps.materials_group_by_code, ps.warehouse, ps.warehouse_cut_work, ps.warehouse_edge_work) == \
        (True, False, False, True, True, True)
    assert (ps.products_list, ps.products_list_single, ps.operations_list, ps.operations_list_single, ps.operations, ps.xnc_stats) == \
        (False, False, False, False, True, False)
    # «Изделия», «Поля страницы»
    assert (ps.prod_header, ps.prod_operations, ps.prod_materials, ps.prod_parts) == (False, False, False, True)
    assert (ps.page_margin_left, ps.page_margin_right, ps.page_margin_top, ps.page_margin_bottom) == (10, 10, 8, 10)
    assert (ps.page_mirror_margins, ps.page_footer_pos) == (False, "bottom")
    # (CS) Общие / Детали / Карты кроя
    assert (ps.cs_title, ps.cs_warehouse, ps.cs_stats, ps.cs_parts, ps.cs_unplaced, ps.cs_sheets, ps.cs_remnants, ps.cs_maps) == \
        (False, False, False, True, False, True, False, True)
    assert (ps.cs_edge_symbols, ps.cs_parts_form, ps.map_mirror_h, ps.map_mirror_v, ps.map_part_expr) == (False, "merged", "no", False, "")
    assert (ps.map_edge_marker, ps.map_edge_line_style, ps.map_machining, ps.map_num_bold, ps.map_dim_bold, ps.map_dim_rotate) == \
        ("lines", "solid", False, True, True, True)
    assert ps.map_header_fields == ["N", "S", "C", "Cp", "LT", "F"]
    assert [c.key for c in ps.map_header_cols] == ["N", "S", "C", "Cp", "LT", "F", "R", "CT", "T", "AP", "AM", "AW", "PK"]
    assert [c.on for c in ps.map_header_cols][:7] == [True] * 6 + [False]
    # (EL), (XNC), (CL)
    assert (ps.el_params, ps.el_parts, ps.el_header_work, ps.el_header_material) == (True, True, False, False)
    assert (ps.xnc_stats_group, ps.xnc_back_mirror, ps.xnc_origin_as_op, ps.xnc_origin) == ("material", "horizontal", False, "lt")
    assert len(ps.xnc_stat_cols) == 18 and [c.key for c in ps.xnc_stat_cols[:3]] == ["n", "side", "code"]
    assert [(c.key, c.on, c.width) for c in ps.xnc_stat_cols if c.key in ("drill_price", "mill_len")] == \
        [("drill_price", False, 10), ("mill_len", True, 9)]
    assert (ps.cl_warehouse, ps.cl_stats) == (False, False)


def test_header_cols_sync_with_legacy_fields():
    # eski profil: faqat ro'yxat → ustunlar undan quriladi (tartib saqlanadi, qolganlari o'chiq)
    ps = PrintSettings(map_header_fields=["F", "N", "XX"])
    assert ps.map_header_fields == ["F", "N"] and [(c.key, c.on) for c in ps.map_header_cols[:3]] == [("F", True), ("N", True), ("S", False)]
    # yangi mijoz: faqat ustunlar → ro'yxat ulardan
    ps = PrintSettings(map_header_cols=[PrintCol(key="T", width=5), PrintCol(key="N", on=False)])
    assert ps.map_header_fields == ["T"] and ps.map_header_cols[0].width == 5
    # eski mijoz butun sozlamani olib faqat ro'yxatni o'zgartirdi → ro'yxat ustun, kengliklar saqlanadi
    d = PrintSettings().model_dump()
    d["map_header_cols"][0]["width"] = 33
    d["map_header_fields"] = ["N", "PK"]
    ps = PrintSettings(**d)
    assert ps.map_header_fields == ["N", "PK"] and ps.map_header_cols[0].key == "N" and ps.map_header_cols[0].width == 33
    # saqlash (profil) orqali ham bir xil
    clean = settings.validate_data("print", {"map_header_fields": ["S"]})
    assert clean["map_header_fields"] == ["S"] and clean["map_header_cols"][0] == {"key": "S", "on": True, "width": 12}


def test_mirror_flag_migration():
    assert PrintSettings(map_mirror=True).map_mirror_h == "yes"
    assert PrintSettings(map_mirror_h="cuts_v").map_mirror is False
    d = PrintSettings(map_mirror_h="yes").model_dump()
    d["map_mirror"] = False                                   # eski mijoz «Зеркально» ni o'chirdi
    assert PrintSettings(**d).map_mirror_h == "no"
    assert PrintSettings(map_part_label="none").map_part_label == "none"


# ───────────────────────── yordamchi loyiha ─────────────────────────
def _project(strips_axis="x", face_side=True):
    el = Operation(type=OpType.EL, name="Kromka A", el=ELParams(symbol="A", thickness=0.4, color="#ff0000"))
    part = Part(uid=1, name="Panel", length=600, width=400, qty=2, edge_top=EdgeRef(op_id=el.id), edge_left=EdgeRef(op_id=el.id))
    part2 = Part(uid=2, name="Bok", length=300, width=200, qty=1)
    prog = [XncCommand(cmd="DrillFront", params={"X": "100", "Y": "50", "D": "8", "DP": "12", "T": "1"}),
            XncCommand(cmd="Groove", params={"X1": "0", "Y1": "100", "X2": "600", "Y2": "100", "W": "4", "DP": "8"})]
    xnc = Operation(type=OpType.XNC, code="P1-1", name="Teshik", xnc=XNCParams(length=600, width=400, thickness=16, qty=2,
                                                                                  program=prog, face_side=face_side, drill_price=2,
                                                                                  mill_price_m=3, saw_price_m=4, extra_cost=1))
    part.xnc_op_ids = [xnc.id]
    xnc.xnc_part_id = part.id
    cs = Operation(type=OpType.CS, name="LDSP", code="M1", cs_material=CSMaterialParams(thickness=16), cs_cut=CSCutParams(),
                   parts=[part, part2])
    prod = Product(name="Shkaf", code="SH", qty=1)
    part.product_id = prod.id
    pl = [Placement(part_id=part.id, part_uid=1, x=10, y=10, length=600, width=400),
          Placement(part_id=part.id, part_uid=1, x=10, y=430, length=400, width=600, rotated=True)]
    m = CutMap(index=1, sheet_id="s", sheet_length=2750, sheet_width=1830, placements=pl, parts_count=2,
               strips=[{"x": 0, "y": 0, "l": 2750, "w": 1830, "k": "C", "a": strips_axis, "c": []}],
               commands=[CutCommand(code="T", level=1, size=10, count=1), CutCommand(code="T", level=2, size=5, count=1)],
               sheet_area_m2=5.0325, parts_area_m2=0.48, remnant_area_m2=1.0)
    from app.models import CuttingResult
    cs.result = CuttingResult(maps=[m], total_sheets=1, total_parts=2, total_fill_percent=9.5, total_cut_length_m=4.2,
                              total_cuts=3, material_area_m2=5.0325, parts_area_m2=0.48, remnant_area_m2=1.0, material_qty_m2=4.0)
    return Project(name="P<>\"", number=1234, operations=[cs, el, xnc], products=[prod]), cs, el, xnc, m


def _svg(proj, cs, m, **kw):
    ps = PrintSettings(**kw)
    return render.map_svg(m, 800, None, proj, cs, ps.map_part_label, ps.map_edges, ps.map_remnant_number,
                          render._map_mirror(m, ps), style=ps)


# ───────────────────────── hisobot: umumiy sozlamalar ─────────────────────────
def test_general_blocks_products_operations_xnc_stats():
    proj, cs, el, xnc, _m = _project()
    # bitta mahsulot: «если изделие одно» Нет → ro'yxat yo'q; Да → ro'yxat + «Изделия» bloklari
    html = render.project_report_html(proj, PrintSettings(products_list=True), "ru")
    assert "<h2>1. Изделия" not in html and "Изделия</h2>" not in html
    html = render.project_report_html(proj, PrintSettings(products_list=True, products_list_single=True, prod_header=True,
                                                          prod_operations=True, prod_materials=True), "ru")
    assert "Изделия</h2>" in html and "Изделие: SH Shkaf × 1 шт" in html and "<td>Panel</td>" in html
    # operatsiyalar ro'yxati (3 ta operatsiya → «если одна» shart emas)
    html = render.project_report_html(proj, PrintSettings(operations_list=True, operations=False), "ru")
    assert "Операции</h2>" in html and "<td>XNC</td>" in html and "(CS)" not in html
    # XNC statistikasi: ustunlar (Вкл, tartib, Ш-на) va guruhlash
    ps = PrintSettings(xnc_stats=True, operations=False, xnc_stats_group="material",
                       xnc_stat_cols=[PrintCol(key="code", width=30), PrintCol(key="side"), PrintCol(key="drills"),
                                      PrintCol(key="drill_cost"), PrintCol(key="op_cost"), PrintCol(key="name", on=False)])
    html = render.project_report_html(proj, ps, "ru")
    assert "Материал: LDSP" in html and "Кол. св-ний" in html and "Ст-ть св-ний" in html and "<th>" in html
    assert html.index("Код</span>") < html.index("Ст</span>") < html.index("Кол. св-ний")
    assert "Наименование</span>" not in html.split("Обработка</h2>")[1]
    assert "<td>P1-1</td><td>Лиц</td><td>1</td><td>4</td>" in html             # 1 teshik × 2 UZS × 2 dona
    html_p = render.project_report_html(proj, PrintSettings(xnc_stats=True, operations=False, xnc_stats_group="product"), "ru")
    assert "Изделие: Shkaf" in html_p
    html_n = render.project_report_html(proj, PrintSettings(xnc_stats=True, operations=False, xnc_stats_group="none"), "ru")
    assert "class='grp'" not in html_n.split("Обработка</h2>")[1]


def test_materials_group_by_code(client, kravat):
    pid, cs, _el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    proj = store.load(pid)
    plain = render._materials_rows(proj, PrintSettings(materials_list=True))
    grouped = render._materials_rows(proj, PrintSettings(materials_list=True, materials_group_by_code=True))
    assert len(grouped) <= len(plain) and all("qty" in r for r in grouped)
    html = client.post(f"/api/projects/{pid}/report", json={"materials_list": True, "materials_group_by_code": True}).text
    assert "Материалы</h2>" in html


# ───────────────────────── (CS) Общие / Детали ─────────────────────────
def test_cs_warehouse_stats_edge_symbols_and_sides_form():
    proj, cs, el, xnc, m = _project()
    html = render.project_report_html(proj, PrintSettings(cs_warehouse=True, cs_stats=True, operations=True), "ru")
    assert "1. Требование на склад</h3>" in html and "2. Статистика</h3>" in html and "3. Детали" in html
    assert "<td>Листов</td><td><b>1</b></td>" in html and "Заполнение</td><td><b>9.5%</b>" in html
    # belgilar + legenda (o'lcham bo'yicha birlashtirilgan): uzunlik bo'ylab «A», en bo'ylab «A»
    html = render.project_report_html(proj, PrintSettings(cs_edge_symbols=True), "ru")
    assert "<td>A</td>" in html and "Обозначения кромок: <b>A</b> — Kromka A (0.4 мм)" in html and "(1) Kromka A" not in html
    # har tomon alohida: ОВ ОН ОЛ ОП ustunlari, yuqori va chapda «A», pastda/o'ngda bo'sh
    html = render.project_report_html(proj, PrintSettings(cs_edge_symbols=True, cs_parts_form="sides"), "ru")
    assert "<th>ОВ</th><th>ОН</th><th>Ширина</th><th>ОЛ</th><th>ОП</th>" in html
    assert "<td>600</td><td>A</td><td></td><td>400</td><td>A</td><td></td>" in html
    html = render.project_report_html(proj, PrintSettings(cs_parts_form="sides"), "ru")
    assert "<td>(1) Kromka A</td><td></td>" in html                       # nomlar bilan ham


# ───────────────────────── (CS) Карты кроя ─────────────────────────
def test_map_header_r_t_and_mirror_modes():
    proj, cs, el, xnc, m = _project(strips_axis="x")
    hdr = render.map_header(m, cs.result, ["R", "T", "CT"])
    assert hdr.startswith("R:70.59%/70.59%") and "T:10/5" in hdr and "CT:0/3" in hdr
    # «Горизонтально»: Да / Нет / birinchi kesimlar tik (ildiz o'qi x) / yotiq
    assert render._map_mirror(m, PrintSettings(map_mirror_h="yes")) is True
    assert render._map_mirror(m, PrintSettings(map_mirror_h="no")) is False
    assert render._map_mirror(m, PrintSettings(map_mirror_h="cuts_v")) is True
    assert render._map_mirror(m, PrintSettings(map_mirror_h="cuts_h")) is False
    _p2, _cs2, _e2, _x2, m_y = _project(strips_axis="y")
    assert render._map_mirror(m_y, PrintSettings(map_mirror_h="cuts_v")) is False
    assert render._map_mirror(m_y, PrintSettings(map_mirror_h="cuts_h")) is True
    # ko'zguda x koordinatalari akslanadi
    plain, mir = _svg(proj, cs, m), _svg(proj, cs, m, map_mirror_h="yes")
    assert 'x="10"' in plain and 'x="2140"' in mir


def test_map_mirror_vertical_keeps_text_readable():
    proj, cs, el, xnc, m = _project()
    svg = _svg(proj, cs, m, map_mirror_v=True)
    assert svg.count('<g transform="translate(0 1830) scale(1 -1)">') == 1 and svg.endswith("</g></svg>")
    texts = re.findall(r"<text [^>]*>", svg)
    assert texts and all("scale(1 -1)" in t for t in texts)              # har matn teskari aks bilan to'g'rilangan
    assert any("rotate(-90" in t for t in texts)                         # en yozuvi pastdan yuqoriga
    assert "<circle" not in svg


def test_map_edge_marker_style_symbols_expression_machining():
    proj, cs, el, xnc, m = _project()
    base = _svg(proj, cs, m)
    assert "stroke-dasharray" not in base and ">A</text>" not in base
    dashed = _svg(proj, cs, m, map_edge_line_style="dashed")
    assert 'stroke="#ff0000"' in dashed and 'stroke-dasharray=' in dashed
    sym = _svg(proj, cs, m, map_edge_marker="symbols")
    assert 'stroke="#ff0000"' not in sym and sym.count('fill="#ff0000"') == 4          # 2 joylashuv × 2 kromkali tomon
    both = _svg(proj, cs, m, map_edge_marker="both")
    assert 'stroke="#ff0000"' in both and both.count('fill="#ff0000"') == 4
    # «Печать значения выражения»: detal o'zgaruvchilari (services/expr.py), xato — bo'sh
    ex = _svg(proj, cs, m, map_part_expr='name + " / " + qty')
    assert ">Panel / 2</text>" in ex and "Panel / 2" not in base
    assert _svg(proj, cs, m, map_part_expr="nosuch(") == base                        # xato: chiqish o'zgarmaydi
    # «Печать обработки на деталях»: teshik (aylana) va paz (punktir) — burilgan nusxada ham
    mach = _svg(proj, cs, m, map_machining=True)
    circles = re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="[\d.]+"', mach)
    assert [(float(a), float(b)) for a, b in circles] == [(110.0, 60.0), (360.0, 530.0)]
    assert mach.count("stroke-dasharray") == 2 and 'x1="10" y1="110" x2="610" y2="110"' in mach
    # «Печать номера / наименования детали»: ikkalasi o'chiq
    none = _svg(proj, cs, m, map_part_label="none")
    assert ">1</text>" not in none and "Panel" not in none


# ───────────────────────── sahifa chegaralari, kolontitul, XNC chizma ─────────────────────────
def test_page_css_mirror_margins_footer_and_escaping():
    proj, *_ = _project()
    css = render._page_css(PrintSettings(), proj, render.T["ru"])
    assert "@page { size: A4; margin: 8mm 10mm 10mm 10mm; }" in css and "@bottom-center" in css and "counter(page)" in css
    assert "<" not in css.split("content:")[1].split(";")[0] and "\\3c " in css and '\\"' in css      # <style> dan chiqib bo'lmaydi
    css = render._page_css(PrintSettings(page_mirror_margins=True, page_footer_pos="top", page_margin_left=15), proj)
    assert "@page :left { margin: 8mm 15mm 10mm 10mm; }" in css and "@top-center" in css
    assert "center" not in render._page_css(PrintSettings(page_footer_pos="none"), proj)
    assert "@page" in render._page_css(PrintSettings())                   # loyihasiz ham ishlaydi
    html = render.project_report_html(proj, PrintSettings(), "ru")
    assert "</style>" in html and html.count("<style>") == 1 and "<script" not in html


def test_xnc_back_mirror_only_for_back_side():
    proj, cs, el, xnc, m = _project(face_side=False)
    assert render._xnc_print_op(xnc, PrintSettings(xnc_back_mirror="none")) is xnc
    h = render._xnc_print_op(xnc, PrintSettings(xnc_back_mirror="horizontal"))
    assert h.xnc.mirror_x is True and h.xnc.mirror_y is False and xnc.xnc.mirror_x is False       # asl dastur o'zgarmaydi
    v = render._xnc_print_op(xnc, PrintSettings(xnc_back_mirror="vertical"))
    assert v.xnc.mirror_y is True and v.xnc.mirror_x is False
    front = _project(face_side=True)[3]
    assert render._xnc_print_op(front, PrintSettings()) is front
    plain = render.project_report_html(proj, PrintSettings(xnc_back_mirror="none"), "ru")
    mirrored = render.project_report_html(proj, PrintSettings(), "ru")
    assert "(XNC)" in plain and plain != mirrored


def test_profile_roundtrip_api(client):
    data = {"map_header_cols": [{"key": "F", "on": True, "width": 9}, {"key": "N", "on": True, "width": 8}],
            "map_header_fields": ["F", "N"], "xnc_stat_cols": [{"key": "code", "on": True, "width": 40}],
            "map_mirror_h": "cuts_v", "cs_parts_form": "sides", "page_footer_pos": "top", "map_part_label": "none"}
    prof = client.post("/api/settings/print", json={"name": "X1015b grid", "data": data}).json()
    got = next(p for p in client.get("/api/settings/print").json() if p["id"] == prof["id"])["data"]
    assert got["map_header_fields"] == ["F", "N"] and got["map_header_cols"][0] == {"key": "F", "on": True, "width": 9}
    assert got["map_mirror"] is False and got["map_mirror_h"] == "cuts_v" and got["xnc_stat_cols"] == data["xnc_stat_cols"]
    assert client.post("/api/settings/print", json={"name": "bad", "data": {"map_mirror_h": "sideways"}}).status_code == 400
