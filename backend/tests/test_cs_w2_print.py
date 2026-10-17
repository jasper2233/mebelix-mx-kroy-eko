"""W2 — CS chop sozlamalari va karta chizmasi: pripusk punktiri, shrift, rang/shtrixlash, ishlov belgilari, yo'nalish,
mahsulot bo'yicha guruhlash, kromka ustunini ajratish, CS sarlavhasi. Standart qiymatlarda chiqish eskisi bilan bir xil."""
import re

import pytest

from app import store
from app.models import (CutMap, Operation, OpType, Part, Placement, PrintSettings, Product, Project, GrooveSide,
                        CSCutParams, CSMaterialParams)
from app.services import render, settings


# ───────────────────────── yordamchilar ─────────────────────────
def _map_project(rotated=False, ma=0.0, allow=(0, 0, 0, 0), grooved=False):
    """Bitta detalli (300×200, joyi 100,50) qo'lda yig'ilgan karta."""
    part = Part(uid=1, name="Panel", length=300, width=200,
                allow_top=allow[0], allow_bottom=allow[1], allow_left=allow[2], allow_right=allow[3])
    if grooved:
        part.groove_top = GrooveSide(op_id="g1")
    op = Operation(type=OpType.CS, name="LDSP", cs_material=CSMaterialParams(), cs_cut=CSCutParams(machining_allowance=ma),
                   parts=[part])
    proj = Project(name="P", operations=[op], products=[Product(name="Shkaf")])
    pl = Placement(part_id=part.id, part_uid=1, x=100, y=50, length=300, width=200, rotated=rotated)
    m = CutMap(index=1, sheet_id="s", sheet_length=1000, sheet_width=600, placements=[pl])
    return proj, op, m


def _svg(proj, op, m, ps=None, **kw):
    ps = ps or PrintSettings()
    return render.map_svg(m, 800, None, proj, op, ps.map_part_label, ps.map_edges, ps.map_remnant_number, ps.map_mirror,
                          style=ps, **kw)


def _report(client, kravat, **ps):
    pid, cs, _el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    return render.project_report_html(store.load(pid), PrintSettings(**ps), "ru")


# ───────────────────────── standart qiymatlar: eski chiqish ─────────────────────────
def test_defaults_keep_old_output():
    proj, op, m = _map_project()
    svg = _svg(proj, op, m)
    assert "<defs>" not in svg and "stroke-dasharray" not in svg and "url(#" not in svg
    assert 'font-weight="bold"' in svg                                     # detal raqami qalin (eski xulq)
    assert 'fill="#F2A541"' in svg and 'fill="#CBCED3"' not in svg        # strips yo'q — chiqindi foni chizilmaydi
    assert "rotate(90" in svg                                              # vertikal en yozuvi aylantirilgan
    ps = PrintSettings()
    # «Печать заголовка» standarti — bor (2026-10-17 solishtiruv #61: sarlavhasiz jadval materiali ko'rinmaydi)
    assert (ps.cs_title, ps.cs_group_by_product, ps.cs_edge_highlight, ps.map_orientation) == (True, False, False, "portrait")
    assert (ps.map_part_marks, ps.map_allowance, ps.map_num_font, ps.map_dim_font) == (False, True, 0, 0)


def test_old_print_profile_opens(client, kravat):
    """Yangi maydonlarsiz eski profil JSON — standart bilan to'ldiriladi va hisobot ochiladi."""
    pid, cs, _ = kravat
    old = {"header": True, "cs_maps": True, "map_header_fields": ["N", "S"], "page_margin_left": 12}
    clean = settings.validate_data("print", old)
    assert clean["map_orientation"] == "portrait" and clean["cs_title"] is True and clean["map_part_fill"] == "#F2A541"
    prof = client.post("/api/settings/print", json={"name": "Eski", "data": old}).json()
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    r = client.get(f"/api/projects/{pid}/report?profile_id={prof['id']}")
    assert r.status_code == 200 and "<svg" in r.text
    assert client.get("/api/settings/print/default").json()["map_orientation"] == "portrait"


def test_print_settings_validation(client):
    try:
        assert client.put("/api/settings/print/default", json={"map_part_fill": "#1a2B3c"}).status_code == 200
        for bad in ({"map_part_fill": "red"}, {"map_waste_fill": '#12345"/><script>'}, {"map_part_hatch": "dots"},
                    {"map_orientation": "diagonal"}, {"map_num_font": -1}, {"map_dim_font": 999}):
            assert client.put("/api/settings/print/default", json=bad).status_code in (400, 422), bad
    finally:
        client.put("/api/settings/print/default", json={})                 # standartga qaytarish


# ───────────────────────── pripusk punktiri (DM-010) ─────────────────────────
def test_allowance_dashed_rect_unrotated():
    proj, op, m = _map_project(allow=(1, 2, 3, 4))                        # top, bottom, left, right
    svg = _svg(proj, op, m)
    # ichkariga: chap 3, yuqori 1, o'ng 4, past 2 → (103, 51), 300−3−4=293 × 200−1−2=197
    assert '<rect x="103" y="51" width="293" height="197" fill="none"' in svg and "stroke-dasharray" in svg
    assert "stroke-dasharray" not in _svg(proj, op, m, show_allowance=False)
    assert "stroke-dasharray" not in _svg(proj, op, m, PrintSettings(map_allowance=False), show_allowance=False)


def test_allowance_dashed_rect_rotated_and_machining():
    proj, op, m = _map_project(rotated=True, allow=(1, 2, 3, 4))
    svg = _svg(proj, op, m)
    # burilgan: chap = asl past (2), yuqori = asl chap (3), o'ng = asl yuqori (1), past = asl o'ng (4)
    assert '<rect x="102" y="53" width="297" height="193" fill="none"' in svg
    proj, op, m = _map_project(ma=5)                                      # umumiy pripusk — to'rt tomonda
    assert '<rect x="105" y="55" width="290" height="190" fill="none"' in _svg(proj, op, m)


def test_allowance_mirror_and_zero():
    proj, op, m = _map_project(allow=(0, 0, 10, 0))
    ps = PrintSettings(map_mirror=True)
    svg = _svg(proj, op, m, ps)                    # ko'zgu: geometriya akslanadi (chap pripusk o'ngda qoladi)
    assert '<rect x="600" y="50" width="290" height="200" fill="none"' in svg    # 1000 − (100 + 10) − 290 = 600
    proj, op, m = _map_project()
    assert "stroke-dasharray" not in _svg(proj, op, m)


# ───────────────────────── shrift, rang, shtrixlash, belgilar ─────────────────────────
def test_fonts_fill_hatch_and_marks():
    proj, op, m = _map_project(grooved=True)
    ps = PrintSettings(map_part_fill="#112233", map_part_hatch="diag", map_waste_hatch="cross", map_num_bold=False,
                       map_dim_bold=True, map_dim_rotate=False, map_part_marks=True, map_num_font=10, map_dim_font=8)
    svg = _svg(proj, op, m, ps, uid="t1")
    assert '<pattern id="t1-hp"' in svg and '<pattern id="t1-hw"' in svg and 'fill="url(#t1-hp)"' in svg
    assert 'fill="#112233"' in svg
    assert "rotate(90" not in svg                                          # en yozuvi aylantirilmaydi
    # detal raqami qalin emas, o'lchamlar qalin
    num = re.search(r'<text[^>]*>1</text>', svg).group(0)
    assert "font-weight" not in num
    dims = [t for t in re.findall(r'<text[^>]*>(?:300|200)</text>', svg)]
    assert dims and all('font-weight="bold"' in t for t in dims)
    # shrift o'lchami pt dan list birligiga: 8 pt * (96/72) / (800/1000 px/mm) = 13.3
    assert 'font-size="13.3"' in svg
    assert re.search(r'font-weight="bold" fill="#241400">=</text>', svg)   # pazlash belgisi
    ps2 = PrintSettings(map_part_marks=False)
    assert ">=</text>" not in _svg(proj, op, m, ps2)


def test_hatch_kinds_are_valid_svg_patterns():
    for kind in ("diag", "cross", "horizontal", "vertical"):
        d = render._hatch_pattern("x", kind, 20, 1.5)
        assert d.startswith('<pattern id="x"') and d.endswith("</pattern>") and "<path" in d


def test_waste_fill_uses_chosen_color_on_real_result(client, kravat):
    pid, cs, _ = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    p = store.load(pid)
    op = next(o for o in p.operations if o.type == OpType.CS)
    svg = render.map_svg(op.result.maps[0], 600, None, p, op, style=PrintSettings(map_waste_fill="#00ff00",
                                                                                 map_waste_hatch="horizontal"), uid="w")
    assert 'fill="#00ff00"' in svg and 'fill="url(#w-hw)"' in svg and 'fill="#CBCED3"' not in svg
    assert "url(#w-hp)" not in svg                                         # detal shtrixlanmagan


# ───────────────────────── hisobot: yo'nalish, guruhlash, ajratish, sarlavha ─────────────────────────
def test_landscape_orientation(client, kravat):
    html = _report(client, kravat, map_orientation="landscape")
    assert "@page land" in html and "<div class='land'>" in html and 'width="840"' in html
    port = _report(client, kravat)
    assert "<div class='land'>" not in port and 'width="620"' in port
    assert port.count("<svg") >= 1


def test_group_by_product(client):
    pid = client.post("/api/projects", json={"name": "Guruh"}).json()["id"]
    p = client.get(f"/api/projects/{pid}").json()
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "LDSP16", "name": "L"}).json()
    cs = p["operations"][-1]["id"]
    client.post(f"/api/projects/{pid}/products", json={"name": "Shkaf <b>1</b>", "qty": 2})
    pr = client.post(f"/api/projects/{pid}/products", json={"name": "Stol", "qty": 1}).json()
    by_name = {x["name"]: x["id"] for x in pr["products"]}               # [standart mahsulot, Shkaf, Stol]
    parts = [dict(name="A", length=500, width=300, product_id=by_name["Stol"]),
             dict(name="B", length=400, width=300, product_id=by_name["Shkaf <b>1</b>"]),
             dict(name="C", length=450, width=300, product_id=by_name["Stol"]),
             dict(name="D", length=350, width=300, product_id=None)]
    client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=parts)
    proj = store.load(pid)
    next(o for o in proj.operations if o.type == OpType.CS).parts[3].product_id = None   # API standart mahsulotga bog'laydi
    html = render.project_report_html(proj, PrintSettings(cs_group_by_product=True), "ru")
    grp = re.findall(r"<tr class='grp'><td colspan='9'>(.*?)</td></tr>", html)
    # mahsulotlar tartibida (qismi yo'q standart mahsulot o'tkazib yuboriladi), oxirida «Без изделия»; matn escape qilingan
    assert len(grp) == 3 and "&lt;b&gt;1&lt;/b&gt;" in grp[0] and "× 2" in grp[0] and "Stol" in grp[1] and "Без изделия" in grp[2]
    assert "<b>1</b>" not in html
    # guruhlash o'chiq (standart) — guruh qatorlari yo'q
    assert "<tr class='grp'>" not in render.project_report_html(proj, PrintSettings(), "ru")


def test_edge_highlight_and_cs_title(client, kravat):
    pid, cs, _el = kravat                                                  # №6 detalda ОВ va ОН kromka
    proj = store.load(pid)
    off = render.project_report_html(proj, PrintSettings(cs_title=True), "ru")
    on = render.project_report_html(proj, PrintSettings(cs_edge_highlight=True), "ru")
    assert "td class='hl'" not in off and on.count("td class='hl'") == 1   # faqat uzunlik bo'ylab kromkali bitta katak
    assert "(CS) Листовой раскрой" in off
    no_title = render.project_report_html(proj, PrintSettings(cs_title=False), "ru")
    assert "(CS) Листовой раскрой" not in no_title and "<div class='pb'></div>" in no_title
    # hisobotning boshqa qismlari saqlanadi
    assert "<h3>1. Детали" in no_title


def test_report_api_accepts_new_settings(client, kravat):
    pid, cs, _ = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    body = PrintSettings(map_orientation="landscape", map_part_hatch="diag", cs_group_by_product=True).model_dump(mode="json")
    r = client.post(f"/api/projects/{pid}/report", json=body, params={"lang": "uz"})
    assert r.status_code == 200 and "<div class='land'>" in r.text and "Content-Security-Policy" in r.text
