"""Figurali detal (services/figure.py): kesib tashlanadigan qism, yangi qirralar kromkasi, EL metraji va MES paketi."""
import pytest

from app.models import (ELParams, EdgeRef, Operation, OpType, Part, Project, XNCParams, XncCommand)
from app.services import figure as F
from app.services.calc import edge_usage


def _cmd(cmd, **params):
    return dict(cmd=cmd, params=params, comment="", enabled=True, children=[])


def _proj(program, length=600, width=400, edges=("top", "right"), figure_edges=None, op_price=1000.0):
    p = Project(name="f")
    el = Operation(type=OpType.EL, name="Kromka oq", el=ELParams(symbol="A", overhang=20, min_glue_length=0, op_price=op_price,
                                                                  price=100))
    xo = Operation(type=OpType.XNC, name="x", xnc=XNCParams(length=length, width=width, thickness=16, by_part_size=False,
                                                          origin="LT", program=[XncCommand(**c) for c in program]))
    kw = {f"edge_{s}": EdgeRef(op_id=el.id) for s in edges}
    part = Part(name="p", length=length, width=width, qty=2, xnc_op_ids=[xo.id], figure_edges=figure_edges or [], **kw)
    cs = Operation(type=OpType.CS, name="LDSP", parts=[part])
    p.operations += [cs, xo, el]
    return p, part, el


# o'ng-yuqori burchak kesigi: (500, −10) dan pastga 100 gacha, keyin o'ngga detaldan chiqadi
NOTCH = [_cmd("MillStart", X=500, Y=-10, DP=16, T="Mill8", D=8, C=0), _cmd("MillLine", X=500, Y=100),
         _cmd("MillLine", X=610, Y=100)]


def test_rect_part_has_no_figure():
    p, part, _el = _proj([_cmd("DrillFront", X=50, Y=50, D=5, DP=10, T="Bore5")])
    assert F.compute(p, part) is None


def test_corner_notch_both_sides_edged_gets_edge_and_hatch():
    p, part, el = _proj(NOTCH)
    f = F.compute(p, part)
    assert f["size"] == [600, 400]
    assert len(f["removed"]) == 1
    xs = [q[0] for q in f["removed"][0]]
    ys = [q[1] for q in f["removed"][0]]
    assert min(xs) == pytest.approx(500, abs=0.1) and max(xs) == pytest.approx(600, abs=0.1)
    assert min(ys) == pytest.approx(0, abs=0.1) and max(ys) == pytest.approx(100, abs=0.1)
    # ikkita to'g'ri qirra (100 pastga + 100 o'ngga) — har biri alohida, oddiy KROMKA posti uchun «line»
    assert [round(c["length"]) for c in f["cuts"]] == [100, 100]
    assert all(c["shape"] == "line" and c["edge"]["op_id"] == el.id and c["rule"] == "corner" and c["source"] == "auto"
               for c in f["cuts"])
    assert f["edge_mm"] == pytest.approx(200, abs=0.2)


def test_corner_notch_unedged_side_stays_without_edge():
    p, part, _el = _proj(NOTCH, edges=("top",))
    cuts = F.compute(p, part)["cuts"]
    assert cuts and all(c["edge"] is None and c["rule"] == "corner" for c in cuts)


def test_arch_replacing_whole_side_takes_that_side_edge():
    # yuqori qirra butunlay yoy bilan almashtirildi (chapdan o'ngga), faqat «top» kromkali
    prog = [_cmd("MillStart", X=-10, Y=0, DP=16, T="Mill8", D=8, C=0), _cmd("MillLine", X=0, Y=0),
            _cmd("MillArc", X=600, Y=0, R=500, DIR=False), _cmd("MillLine", X=610, Y=0)]
    p, part, el = _proj(prog, edges=("top",))
    f = F.compute(p, part)
    assert f is not None and f["cuts"]
    arc = [c for c in f["cuts"] if c["shape"] == "curve"]
    assert arc and all(c["edge"] and c["rule"] == "side" and c["edge"]["side"] == "top" for c in arc)   # yoy — OVAL


def test_inner_cutout_is_hatched_without_edge():
    prog = [_cmd("MillRect", X=300, Y=200, L=200, W=100, R=0, DP=16, T="Mill8")]
    p, part, _el = _proj(prog, edges=("top", "bottom", "left", "right"))
    f = F.compute(p, part)
    assert len(f["removed"]) == 1 and all(c["rule"] == "inner" and c["edge"] is None for c in f["cuts"])
    assert sum(c["length"] for c in f["cuts"]) == pytest.approx(600, abs=1) and len(f["cuts"]) == 4
    assert f["edge_mm"] == 0


def test_edge_usage_ignores_figure_edges():
    """Figurali qirra kromkasi MX da hisoblanmaydi (foydalanuvchi qarori): metraj va OVAL posti — MES da."""
    p, part, el = _proj(NOTCH)
    u = edge_usage(p, el)
    # to'g'ri tomonlar GibLab qoidasi bilan: (600 + 400) × 2 dona
    assert u["work_m"] == pytest.approx(2.0, abs=0.01)
    assert not any(k.startswith(("figure", "total")) for k in u)
    assert el.cost_operation == pytest.approx(u["work_m"] * el.el.op_price, abs=1)


def test_bazis_edges_override_auto_rule():
    p, part, el = _proj(NOTCH, edges=("top",),
                        figure_edges=[dict(x1=500, y1=0, x2=500, y2=100, op_id=None),
                                      dict(x1=500, y1=100, x2=600, y2=100, op_id=None)])
    part.figure_edges[0]["op_id"] = el.id
    part.figure_edges[1]["op_id"] = el.id
    cuts = F.compute(p, part)["cuts"]
    assert len(cuts) == 2 and all(c["source"] == "bazis" and c["edge"]["op_id"] == el.id for c in cuts)


def test_mes_package_carries_figure(client):            # `client` — baza jadvallari (postprotsessor ruxsatlari)
    from app.services import mes_package as MP
    p, part, el = _proj(NOTCH)
    pkg = MP.build(p)
    pp = next(x for x in pkg.parts if x.mx_id == part.id)
    assert pp.figure is not None and pp.figure.cuts[0].edge.ref == el.id
    assert pp.figure.edge_m == pytest.approx(0.2, abs=0.001)
    band = next(b for b in pkg.edge_bands if b.ref == el.id)
    assert not hasattr(band, "figure_work_m")                        # metrajni MES o'zi `parts[].figure` dan hisoblaydi


def test_bazis_attribute_orientation_is_matched_by_side_edges():
    """Bazis konturi o'z o'qlarida (Y yuqoriga, siljigan): 4 tomon kromkasi `.project` bilan mos keladigan yo'nalish tanlanadi."""
    import json
    p, part, el = _proj(NOTCH, edges=("top",))
    el.name = "06-19 oq"
    # Bazis: chap-past (100, 50), Y yuqoriga; detal «top» (y=0) — Bazisda y=450 tomoni; o'ng-yuqori burchak kesigi
    def B(x, y):
        return 100 + x, 50 + (400 - y)
    pts = [(0, 0), (500, 0), (500, 100), (600, 100), (600, 400), (0, 400)]
    mats = ["06-19 oq", "06-19 oq", "06-19 oq", "", "", ""]          # top (2 bo'lak) + kesik qirralari; qolganlari yo'q
    segs = []
    for i, (a, b) in enumerate(zip(pts, pts[1:] + pts[:1])):
        (x1, y1), (x2, y2) = B(*a), B(*b)
        segs.append(dict(x1=x1, y1=y1, x2=x2, y2=y2, mat=mats[i], sign="A" if mats[i] else ""))
    fe = F.bazis_edges(json.dumps({"v": 1, "segs": segs}), 600, 400, {"top": el.id}, [el])
    top = [e for e in fe if abs(e["y1"]) < 1e-6 and abs(e["y2"]) < 1e-6]
    assert top and all(e["op_id"] == el.id for e in top)
    part.figure_edges = fe
    cuts = F.compute(p, part)["cuts"]
    assert cuts and all(c["source"] == "bazis" and c["edge"]["op_id"] == el.id for c in cuts)   # avto qoida kromkasiz berardi
    assert F.bazis_edges("buzuq", 600, 400, {}, [el]) == []


def _project_xml(mx_figure: str) -> bytes:
    from xml.sax.saxutils import quoteattr
    prog = ('<?xml version="1.0"?><program dx="600" dy="400" dz="16"><tool name="Mill8" d="8"/>'
            '<var name="contMillDepth" type="double" expr="dz"/>'
            '<ms x="500" y="-30" dp="contMillDepth" name="Mill8" c="1"/><ml x="500" y="100"/><ml x="630" y="100"/></program>')
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project name="fig">
  <good typeId="product" id="1" code="01" name="Shkaf" count="1">
    <part id="11" code="001" name="bok" count="1" txt="false" dl="600" dw="400" elt="@operation#1"
          mxFigure={quoteattr(mx_figure)}/>
  </good>
  <good typeId="tool.edgeline" id="3" elRestSide="20"/>
  <good typeId="sheet" id="4" name="LDSP" t="16" l="2750" w="1830" count="1"/>
  <good typeId="band" id="5" name="Kromka oq" t="1" w="19"/>
  <good typeId="band" id="7" name="Oval oq" t="1" w="19"/>
  <operation typeId="EL" id="1" tool1="3" w="19" t="1" elSymbol="A"><material id="5"/><part id="11"/></operation>
  <operation typeId="EL" id="6" tool1="3" w="19" t="1" elSymbol="C"><material id="7"/><part id="11"/></operation>
  <operation typeId="CS" id="2" t="16" l="2750" w="1830"><material id="4"/><part id="11"/></operation>
  <operation typeId="XNC" id="8" code="x" typeName="bok" side="true" bySizeDetail="true" program={quoteattr(prog)}>
    <part id="11"/></operation>
</project>""".encode("utf-8")


def test_bazis_export_v2_figure_edges_per_element():
    """GibLabExport 2.00 MX: kontur elementlari XNC koordinatalarida va har birining EL havolasi bilan — bitta kesimda
    kromkali (o'yiq devori, «oval») va kromkasiz (tubi) qismlar alohida; metraj o'z EL operatsiyasiga."""
    import json
    from app.plugins.legacy_project import import_project
    segs = [dict(x1=0, y1=0, x2=500, y2=0, el="@operation#1", mat="Kromka oq", sign="A"),
            dict(x1=500, y1=0, x2=500, y2=100, el="@operation#6", mat="Oval oq", sign="C"),
            dict(x1=500, y1=100, x2=600, y2=100, el=""),
            dict(x1=600, y1=100, x2=600, y2=400, el=""),
            dict(x1=600, y1=400, x2=0, y2=400, el=""),
            dict(x1=0, y1=400, x2=0, y2=0, el="")]
    p, _w = import_project(_project_xml(json.dumps({"v": 2, "frame": "xnc", "l": 600, "w": 400, "segs": segs})), "fig.project")
    cs = next(o for o in p.operations if o.type == OpType.CS)
    part = cs.parts[0]
    oval = next(o for o in p.operations if o.type == OpType.EL and o.name == "Oval oq")
    assert part.figure_edges and any(e["op_id"] == oval.id for e in part.figure_edges)
    cuts = F.compute(p, part)["cuts"]
    edged = [c for c in cuts if c["edge"]]
    plain = [c for c in cuts if not c["edge"]]
    assert len(edged) == 1 and edged[0]["edge"]["op_id"] == oval.id and edged[0]["edge"]["symbol"] == "C"
    assert edged[0]["length"] == pytest.approx(100, abs=0.5) and edged[0]["source"] == "bazis"
    assert sum(c["length"] for c in plain) == pytest.approx(100, abs=0.5)


def test_bazis_v2_arc_by_mid_point():
    segs = [dict(x1=0, y1=100, x2=100, y2=0, cx=100, cy=100, mx=29.29, my=29.29, el="@operation#1", mat="Kromka oq")]
    el = Operation(type=OpType.EL, name="Kromka oq", el=ELParams(symbol="A"))
    fe = F.bazis_edges(json_dumps({"v": 2, "frame": "xnc", "segs": segs}), 600, 400, {}, [el], ref_ops={"@operation#1": el})
    total = sum(((e["x2"] - e["x1"]) ** 2 + (e["y2"] - e["y1"]) ** 2) ** 0.5 for e in fe)
    assert total == pytest.approx(3.14159 * 100 / 2, abs=0.2)          # chorak aylana (qisqa yo'l), uzunlik to'g'ri
    assert all(e["op_id"] == el.id for e in fe)
    xs = [e["x1"] for e in fe]
    assert max(xs) <= 100.01                                          # o'rta nuqta tomonidagi yoy (katta yoy emas)


def json_dumps(d):
    import json
    return json.dumps(d)


def test_u_notch_on_one_side_is_not_edged():
    """Bitta tomon ichidagi U-o'yiq (kabel kesigi) — tomon kromkali bo'lsa ham kromkalanmaydi (korxona qoidasi)."""
    prog = [_cmd("MillStart", X=250, Y=-10, DP=16, T="Mill8", D=8, C=0), _cmd("MillLine", X=250, Y=60),
            _cmd("MillLine", X=350, Y=60), _cmd("MillLine", X=350, Y=-10)]
    p, part, _el = _proj(prog, edges=("top", "bottom", "left", "right"))
    f = F.compute(p, part)
    assert f["cuts"] and all(c["edge"] is None and c["rule"] == "notch" for c in f["cuts"])
    assert f["edge_mm"] == 0


def test_arc_corner_is_curve_straight_bevel_is_line():
    """Yumaloq burchak (yoy) — «curve» (OVAL), qiya kesilgan burchak (bitta to'g'ri chiziq) — «line» (oddiy KROMKA)."""
    rnd = [_cmd("MillStart", X=500, Y=-10, DP=16, T="Mill8", D=8, C=0), _cmd("MillLine", X=500, Y=0),
           _cmd("MillArc", X=600, Y=100, R=100, DIR=True), _cmd("MillLine", X=610, Y=100)]
    p, part, _el = _proj(rnd)
    shapes = {c["shape"] for c in F.compute(p, part)["cuts"] if c["length"] > 5}
    assert shapes == {"curve"}
    bevel = [_cmd("MillStart", X=490, Y=-10, DP=16, T="Mill8", D=8, C=0), _cmd("MillLine", X=610, Y=110)]
    p, part, _el = _proj(bevel)
    cuts = F.compute(p, part)["cuts"]
    assert len(cuts) == 1 and cuts[0]["shape"] == "line" and cuts[0]["length"] == pytest.approx(141.4, abs=0.5)


def test_curved_planka_outline_keeps_part_not_hatched():
    """Egri planka (950×179): yopiq kontur detalning O'ZI — gabarit eni 90 % dan kam bo'lsa ham (tomonlarga tegadi, maydoni katta)
    ichi saqlanadi, faqat egri qirra ortidagi bo'lak shtrixlanadi (ilgari detalning o'zi shtrixlanardi)."""
    prog = [_cmd("MillStart", X=0, Y=179, DP=16, T="Mill8", D=8, C=0), _cmd("MillLine", X=950, Y=179),
            _cmd("MillLine", X=950, Y=60), _cmd("MillArc", X=0, Y=60, R=5650.6, DIR=False), _cmd("MillLine", X=0, Y=179)]
    p, part, _el = _proj(prog, length=950, width=179, edges=("top", "bottom"))
    f = F.compute(p, part)
    assert f is not None

    def removed(x, y):
        def inside(r):
            c = False
            for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
                if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    c = not c
            return c
        return sum(inside(r) for r in f["removed"]) % 2 == 1
    assert not removed(475, 150) and not removed(100, 170)     # detalning o'zi — shtrixsiz
    assert removed(475, 5) and removed(20, 30)                  # egri qirra ortidagi bo'lak — shtrix
    assert any(c["shape"] == "curve" for c in f["cuts"])


def test_inner_window_stays_removed():
    """Fasad oynasi (ichki to'rtburchak o'yiq, tomonlarga tegmaydi) — ichi olib tashlanadi."""
    prog = [_cmd("MillRect", X=600, Y=249.5, L=1000, W=299, R=0, DP=16, T="Mill8")]
    p, part, _el = _proj(prog, length=1200, width=499, edges=("top", "bottom", "left", "right"))
    f = F.compute(p, part)
    assert len(f["removed"]) == 1 and all(c["rule"] == "inner" for c in f["cuts"])


def test_bazis_edge_on_unused_el_op_takes_op_symbol():
    """Figurali qirra kromkasi detal tomonlarida ishlatilmagan EL dan (masalan faqat burchak yoyida) — chekda shu EL
    belgisi (ilgari material nomi «kromka PVC …» belgi bo'lib chiqardi)."""
    import json
    p, part, el = _proj(NOTCH, edges=("top",))
    el2 = Operation(type=OpType.EL, name="1-19 qora", el=ELParams(symbol="B"))
    p.operations.append(el2)
    segs = [dict(x1=500, y1=0, x2=500, y2=100, el=f"@operation#{el2.id}", mat="kromka PVC 1-19 qora")]
    part.figure_edges = F.bazis_edges(json.dumps({"v": 2, "frame": "xnc", "segs": segs}), 600, 400, {}, [el, el2],
                                      ref_ops={f"@operation#{el2.id}": el2})
    cuts = [c for c in F.compute(p, part)["cuts"] if c["edge"]]
    assert cuts and all(c["edge"]["symbol"] == "B" and c["edge"]["name"] == "1-19 qora" for c in cuts)


def test_open_cut_reversed_correction_keeps_bigger_piece():
    """Egri planka ochiq yo'l bilan (pastdan kirib, uchini aylanib, chapdan chiqadi), korreksiya Bazis faylida teskari (C=2 —
    detal tomonida): ilgari detalning o'zi (74 %) shtrixlanardi (1050 Kubo «01_008 planka», 2026-11-24) — endi kichik bo'lak."""
    prog = [_cmd("MillStart", X=400, Y=190, DP=16, T="Mill8", D=8, C=2), _cmd("MillLine", X=450, Y=170),
            _cmd("MillLine", X=900, Y=120), _cmd("MillLine", X=945, Y=60), _cmd("MillLine", X=880, Y=5),
            _cmd("MillLine", X=-10, Y=20)]
    p, part, _el = _proj(prog, length=950, width=179, edges=("top", "bottom"))
    f = F.compute(p, part)

    def removed(x, y):
        def inside(r):
            c = False
            for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
                if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    c = not c
            return c
        return sum(inside(r) for r in f["removed"]) % 2 == 1
    assert not removed(100, 150) and not removed(600, 100)     # detalning o'zi — shtrixsiz
    assert removed(940, 170) and removed(500, 3)                # chiqindi — shtrix
