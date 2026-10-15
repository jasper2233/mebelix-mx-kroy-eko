# -*- coding: utf-8 -*-
"""X_1015 §10 — XNC chizmasining onlayn ko'rinishga mosligi: o'lcham yozuvlari standart o'chiq (`dims`), yuza teshigining minimal
ekran o'lchami (`width_px`/`height_px` masshtabi), tekstura belgisi (detal Ткт), qirra teshigi — yon polosada chiziqcha (eski kanal
va doira yo'q), orqa yuzada kromka belgilari akslanadi, dastur xatosi / bo'sh nom — chizma ustida qizil matn, endpoint parametrlari."""
import re

from app.models import EdgeRef, ELParams, Operation, OpType, Part, Project, XncCommand as C, XNCParams
from app.services import xnc as X


def _xop(prog, dx=200, dy=100, dz=16, name="op", **kw):
    return Operation(type=OpType.XNC, name=name, xnc=XNCParams(length=dx, width=dy, thickness=dz, by_part_size=False, program=prog, **kw))


def _scale(svg, width_px, height_px=0):
    """SVG viewBox dan ekran masshtabi (px / mm) — xnc_drawing_svg bilan bir xil formula."""
    vb = re.search(r'viewBox="(-?[\d.]+) (-?[\d.]+) ([\d.]+) ([\d.]+)"', svg)
    k = width_px / float(vb.group(3))
    if height_px:
        k = min(k, height_px / float(vb.group(4)))
    return k


def _r(svg, cx, cy):
    m = re.search(rf'<circle cx="{cx}" cy="{cy}" r="([\d.]+)"', svg)
    assert m, svg
    return float(m.group(1))


def _project(grain=True, face=True, prog=None, edges=()):
    """Bog'langan detalli loyiha: CS (detal, kromkalar `edges` tomonlarida) + EL + XNC."""
    el = Operation(type=OpType.EL, name="PVC 2", el=ELParams(symbol="A"))
    part = Part(name="p", length=600, width=400, qty=1, grain=grain)
    for sd in edges:
        setattr(part, f"edge_{sd}", EdgeRef(op_id=el.id))
    xop = Operation(type=OpType.XNC, name="x", xnc=XNCParams(length=600, width=400, thickness=16, by_part_size=False,
                                                           program=prog or [], face_side=face))
    part.xnc_op_ids = [xop.id]
    cs = Operation(type=OpType.CS, name="cs", parts=[part])
    return Project(name="t", operations=[cs, el, xop]), xop


def test_dims_hidden_by_default_and_shown_on_demand():
    op = _xop([C(cmd="DrillFront", params={"X": 10, "Y": 20, "D": 8, "DP": 12})])
    svg = X.xnc_drawing_svg(op)
    assert ">200</text>" not in svg and ">100</text>" not in svg and "xnc-dims" not in svg
    svg2 = X.xnc_drawing_svg(op, dims=True)
    assert ">200</text>" in svg2 and ">100</text>" in svg2 and 'class="xnc-dims"' in svg2
    assert 'cx="10" cy="20"' in svg and 'width="560"' in svg               # teshik o'rni va svg eni o'zgarmagan


def test_small_hole_has_min_screen_radius_big_hole_real_radius():
    op = _xop([C(cmd="DrillFront", params={"X": 100, "Y": 50, "D": 3, "DP": 5})], 2000, 400)
    svg = X.xnc_drawing_svg(op, width_px=700)
    r = _r(svg, 100, 50)
    assert r > 1.5 and r * _scale(svg, 700) >= 3.99                     # 3 mm teshik ekranda kamida 4 px radius
    big = _xop([C(cmd="DrillFront", params={"X": 100, "Y": 50, "D": 35, "DP": 5})], 2000, 400)
    assert _r(X.xnc_drawing_svg(big, width_px=700), 100, 50) == 17.5
    # xoch — aylanadan tashqariga chiqadi (4 ta chiziq uchi aylana radiusidan uzoqroq)
    m = re.search(r'<line x1="([\d.]+)" y1="50" x2="([\d.]+)" y2="50"', svg)
    assert m and float(m.group(2)) - float(m.group(1)) > 2 * r
    # yon ko'rinishlardagi chuqurlik kesimlari (eski ko'rinish) yo'q
    assert 'fill-opacity=".85"' not in svg


def test_height_limits_scale_for_tall_part():
    op = _xop([C(cmd="DrillFront", params={"X": 100, "Y": 50, "D": 3, "DP": 5})], 400, 2000)      # tik detal
    a = X.xnc_drawing_svg(op, width_px=700)
    b = X.xnc_drawing_svg(op, width_px=700, height_px=300)
    ra, rb = _r(a, 100, 50), _r(b, 100, 50)
    assert rb > ra and rb * _scale(b, 700, 300) >= 3.99                 # balandlik cheklasa masshtab kichik → radius (mm) katta


def test_texture_lines_only_for_grain_part_and_rotate():
    pr, op = _project(grain=True)
    svg = X.xnc_drawing_svg(op, pr)
    g = re.search(r'<g class="xnc-grain">(.*?)</g>', svg)
    assert g and g.group(1).count("<line") == 3
    xs = re.findall(r'<line x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" y2="([\d.]+)"', g.group(1))
    assert all(y1 == y2 for _x1, y1, _x2, y2 in xs)                           # gorizontal (detal uzunligi bo'ylab)
    assert abs(float(xs[1][2]) - float(xs[1][0]) - 200) < 1e-6 and abs(float(xs[1][1]) - 200) < 1e-6   # ≈ 1/3, markazda
    pr2, op2 = _project(grain=False)
    assert "xnc-grain" not in X.xnc_drawing_svg(op2, pr2)
    assert "xnc-grain" not in X.xnc_drawing_svg(op)                           # bog'lanmagan — belgisiz
    op.xnc.rotation = 90
    g90 = re.search(r'<g class="xnc-grain">(.*?)</g>', X.xnc_drawing_svg(op, pr)).group(1)
    assert all(x1 == x2 for x1, _y1, x2, _y2 in re.findall(r'<line x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" y2="([\d.]+)"', g90))


def test_edge_hole_drawn_as_thin_marks_on_strip_and_face():
    op = _xop([C(cmd="DrillLeft", params={"Y": 50, "Z": 8, "D": 8, "DP": 30, "M": "true"})])
    svg = X.xnc_drawing_svg(op)
    assert "stroke-dasharray" not in svg and svg.count('class="xnc-edge-hole"') == 1
    g = re.search(r'<g class="xnc-edge-hole" data-side="left">(.*?)</g>', svg)
    assert g and g.group(1).count("<line") == 3 and "<circle" not in g.group(1)
    assert '<line x1="0" y1="50" x2="30" y2="50"' in g.group(1)              # chuqurlik chizig'i: chetdan 30 mm ichkariga
    assert '<line x1="30" y1="46" x2="30" y2="54"' in g.group(1)             # oxirida diametr (8) kengligida chiziqcha
    # ko'zgu / burish — polosa tomoni mos
    assert 'data-side="right"' in X.xnc_drawing_svg(_xop(op.xnc.program, mirror_x=True))
    assert 'data-side="top"' in X.xnc_drawing_svg(_xop(op.xnc.program, rotation=90))
    for cmd, sd in (("DrillRight", "right"), ("DrillTop", "top"), ("DrillBottom", "bottom")):
        k = "X" if sd in ("top", "bottom") else "Y"
        assert f'data-side="{sd}"' in X.xnc_drawing_svg(_xop([C(cmd=cmd, params={k: 50, "D": 8, "DP": 30})]))


def test_back_side_mirrors_edge_symbols_and_face_indicator():
    pr, op = _project(edges=("left",))
    front = X.xnc_drawing_svg(op, pr)
    assert 'data-face="1"' in front
    tx = float(re.search(r'<text x="(-?[\d.]+)" y="[\d.]+" font-size="[\d.]+" font-family="Times New Roman', front).group(1))
    assert tx < 0                                                             # chap kromka harfi — chapda
    pr2, op2 = _project(edges=("left",), face=False)
    back = X.xnc_drawing_svg(op2, pr2)
    assert 'data-face="0"' in back
    tx2 = float(re.search(r'<text x="(-?[\d.]+)" y="[\d.]+" font-size="[\d.]+" font-family="Times New Roman', back).group(1))
    assert tx2 > 600                                                          # orqa yuzadan qaralganda — o'ngda (BACK_FACE_MIRROR = x)


def test_program_error_and_empty_name_drawn_as_red_text():
    good = _xop([C(cmd="DrillFront", params={"X": 10, "Y": 20, "D": 8, "DP": 12})])
    assert "xnc-error" not in X.xnc_drawing_svg(good)
    bad = _xop([C(cmd="DrillFront", params={"X": "abc", "Y": 20, "D": 8, "DP": 12})])
    svg = X.xnc_drawing_svg(bad)
    m = re.search(r'<text class="xnc-error" x="100" y="50" [^>]*font-weight="bold"[^>]*fill="#d01010">([^<]+)</text>', svg)
    assert m and "XNC 1" in m.group(1)
    noname = _xop([C(cmd="DrillFront", params={"X": 10, "Y": 20, "D": 8, "DP": 12})], name="")
    assert 'class="xnc-error"' in X.xnc_drawing_svg(noname)


def test_svg_endpoint_height_and_dims_params(client, kravat):
    pid, cs, _el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    part = next(o for o in p["operations"] if o["id"] == cs)["parts"][5]                 # 480×800
    p = client.post(f"/api/projects/{pid}/operations/{cs}/parts/{part['id']}/xnc").json()
    xid = [o for o in p["operations"] if o["type"] == "XNC"][-1]["id"]
    prog = [{"cmd": "DrillFront", "params": {"X": 100, "Y": 100, "D": 3, "DP": 5}}]
    assert client.patch(f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"program": prog}}).status_code == 200
    base = f"/api/projects/{pid}/operations/{xid}/xnc.svg"
    a = client.get(base, params={"width": 400}).text
    assert "xnc-dims" not in a and 'cx="100" cy="100"' in a
    b = client.get(base, params={"width": 400, "height": 200, "dims": "true"}).text
    assert 'class="xnc-dims"' in b and _r(b, 100, 100) > _r(a, 100, 100)
    assert client.get(base, params={"width": 400, "height": -5}).status_code == 200      # manfiy balandlik — e'tiborsiz
