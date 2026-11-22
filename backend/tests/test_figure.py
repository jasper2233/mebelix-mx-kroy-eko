"""Figurali detal (services/figure.py): kesib tashlanadigan qism, yangi qirralar kromkasi, EL metraji va MES paketi."""
import pytest

from app.models import (ELParams, EdgeRef, Operation, OpType, Part, Project, XNCParams, XncCommand)
from app.services import figure as F
from app.services.calc import edge_usage


def _cmd(cmd, **params):
    return dict(cmd=cmd, params=params, comment="", enabled=True, children=[])


def _proj(program, length=600, width=400, edges=("top", "right"), figure_edges=None, op_price=1000.0, fig_price=None):
    p = Project(name="f")
    el = Operation(type=OpType.EL, name="Kromka oq", el=ELParams(symbol="A", overhang=20, min_glue_length=0, op_price=op_price,
                                                                  figure_op_price=fig_price, price=100))
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
    (c,) = f["cuts"]
    assert c["length"] == pytest.approx(200, abs=0.2)                 # 100 pastga + 100 o'ngga (detal ichida)
    assert c["edge"]["op_id"] == el.id and c["rule"] == "corner" and c["source"] == "auto"
    assert f["edge_mm"] == pytest.approx(200, abs=0.2)


def test_corner_notch_unedged_side_stays_without_edge():
    p, part, _el = _proj(NOTCH, edges=("top",))
    (c,) = F.compute(p, part)["cuts"]
    assert c["edge"] is None and c["rule"] == "corner"


def test_arch_replacing_whole_side_takes_that_side_edge():
    # yuqori qirra butunlay yoy bilan almashtirildi (chapdan o'ngga), faqat «top» kromkali
    prog = [_cmd("MillStart", X=-10, Y=0, DP=16, T="Mill8", D=8, C=0), _cmd("MillLine", X=0, Y=0),
            _cmd("MillArc", X=600, Y=0, R=500, DIR=False), _cmd("MillLine", X=610, Y=0)]
    p, part, el = _proj(prog, edges=("top",))
    f = F.compute(p, part)
    assert f is not None and f["cuts"]
    assert any(c["edge"] and c["rule"] == "side" and c["edge"]["side"] == "top" for c in f["cuts"])


def test_inner_cutout_is_hatched_without_edge():
    prog = [_cmd("MillRect", X=300, Y=200, L=200, W=100, R=0, DP=16, T="Mill8")]
    p, part, _el = _proj(prog, edges=("top", "bottom", "left", "right"))
    f = F.compute(p, part)
    assert len(f["removed"]) == 1 and f["cuts"][0]["rule"] == "inner" and f["cuts"][0]["edge"] is None
    assert f["cuts"][0]["length"] == pytest.approx(600, abs=1)
    assert f["edge_mm"] == 0


def test_edge_usage_counts_figure_separately_with_own_price():
    p, part, el = _proj(NOTCH, fig_price=3000.0)
    u = edge_usage(p, el)
    # to'g'ri tomonlar GibLab qoidasi bilan o'zgarmaydi: (600 + 400) × 2 dona
    assert u["work_m"] == pytest.approx(2.0, abs=0.01)
    assert u["figure_work_m"] == pytest.approx(0.4, abs=0.01)          # 200 mm × 2 dona
    assert u["figure_material_m"] == pytest.approx(0.48, abs=0.01)     # (200 + 2·20) × 2
    assert u["total_material_m"] == pytest.approx(u["material_m"] + u["figure_material_m"], abs=0.001)
    assert el.cost_operation == pytest.approx(u["work_m"] * 1000 + u["figure_work_m"] * 3000, abs=1)
    assert u["figure_rows"][0]["figure_mm"] == pytest.approx(200, abs=0.2)
    # o'chirilsa — figura hisobga olinmaydi
    el.el.figure_count = False
    assert edge_usage(p, el)["figure_work_m"] == 0


def test_bazis_edges_override_auto_rule():
    p, part, el = _proj(NOTCH, edges=("top",),
                        figure_edges=[dict(x1=500, y1=0, x2=500, y2=100, op_id=None),
                                      dict(x1=500, y1=100, x2=600, y2=100, op_id=None)])
    part.figure_edges[0]["op_id"] = el.id
    part.figure_edges[1]["op_id"] = el.id
    (c,) = F.compute(p, part)["cuts"]
    assert c["source"] == "bazis" and c["edge"]["op_id"] == el.id


def test_mes_package_carries_figure(client):            # `client` — baza jadvallari (postprotsessor ruxsatlari)
    from app.services import mes_package as MP
    p, part, el = _proj(NOTCH)
    pkg = MP.build(p)
    pp = next(x for x in pkg.parts if x.mx_id == part.id)
    assert pp.figure is not None and pp.figure.cuts[0].edge.ref == el.id
    assert pp.figure.edge_m == pytest.approx(0.2, abs=0.001)
    band = next(b for b in pkg.edge_bands if b.ref == el.id)
    assert band.figure_work_m == pytest.approx(0.4, abs=0.01)


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
    (c,) = F.compute(p, part)["cuts"]
    assert c["source"] == "bazis" and c["edge"]["op_id"] == el.id    # avtomatik qoida bu yerda kromkasiz berardi
    assert F.bazis_edges("buzuq", 600, 400, {}, [el]) == []
