"""Ishlov markazi o'rnatilgan formatlari, 2-guruh: Daron FoxCNC (.ban), HIRZT MAGI (.pd4), KDT WDX trepan (.xml),
Nanxing SyntecCad (.scx), XDWoodCam (.wxf) — sun'iy XNC dasturlari bilan (yuz / qirra teshigi, paz, freza chiziq + yoy,
o'tuvchi kesim, orqa tomon). Korxona namunalari bilan bayt-ma-bayt solishtirish — `tools/bench/pp_cnc_check2.py`."""
import re

import pytest

from app.models import CSMaterialParams, EdgeRef, ELParams, Operation, OpType, Part, Product, Project, XNCParams, XncCommand
from app.services import ppfmt
from app.services.ppfmt import _cnc2 as C2
from app.services.ppfmt import daron_foxcnc as DA
from app.services.ppfmt import nanxing_syntec as NX

KEYS = (("daron_foxcnc", "ban"), ("hirzt_magi", "pd4"), ("kdt_trepan", "xml"), ("nanxing_syntec", "scx"),
        ("xd_woodcam", "wxf"))


def c(kind, **p):
    return XncCommand(cmd=kind, params=p)


FACE = [
    c("DrillFront", X=100, Y=50, D=5, DP=12, T="Bore5"),
    c("DrillFront", X=8, Y=200, D=8, DP="dz+3", T="BoreTh8"),
    c("DrillFront", X=300, Y=200, D=15, DP=12.5, T="Bore15"),
    c("Groove", X1=0, Y1=350, X2=600, Y2=350, DP=8, W=4, D=4, T="Cut4"),
    c("DrillLeft", Y=40, Z=8, M="true", D=8, DP=30, T="Bore8"),
    c("DrillRight", Y=120.5, Z=8, M="true", D=4.5, DP=32, T="Bore4.5"),
    c("DrillTop", X=100, Z=6, M="false", D=8, DP=30, T="Bore8"),
    c("DrillBottom", X=150, Z=8, M="true", D=8, DP=34, T="Bore8"),
    # o'tuvchi kesim: o'ng-pastki burchakda 50×60 o'yiq, r=10 yumaloqlash bilan (dir=false), asbob o'ngda (C=1)
    c("MillStart", X=550, Y=410, DP=16, D=8, C=1, T="Mill8"),
    c("MillLine", X=550, Y=350),
    c("MillArcCenter", X=560, Y=340, CX=560, CY=350, DIR="true"),
    c("MillLine", X=610, Y=340),
]
BACK = [
    c("DrillFront", X=50, Y=60, D=8, DP=11, T="Bore8"),
    c("Groove", X1=600, Y1=0, X2=100, Y2=0, DP=8, W=6, D=4, T="Cut4"),
]


def make_project():
    el = Operation(type=OpType.EL, code="PVC", name="PVC 1x19", el=ELParams(width=19, thickness=1, symbol="A", color="#D2691E"))
    face = Operation(type=OpType.XNC, code="999901_01_001", name="01_001 bok",
                     xnc=XNCParams(by_part_size=False, length=600, width=400, thickness=16, qty=1, program=FACE))
    back = Operation(type=OpType.XNC, code="999901_01_001_2", name="01_001 bok",
                     xnc=XNCParams(by_part_size=False, length=600, width=400, thickness=16, qty=1, face_side=False,
                                   program=BACK))
    prod = Product(name="Shkaf", code="01", order_info="9001 mijoz")
    part = Part(name="01_001 bok", code="01_001", length=600, width=400, qty=2, grain=True, product_id=prod.id,
                edge_bottom=EdgeRef(op_id=el.id), edge_left=EdgeRef(op_id=el.id), xnc_op_ids=[face.id, back.id])
    cs = Operation(type=OpType.CS, code="LDSP16", name="LDSP 16", parts=[part])
    p = Project(name="9001_mijoz", operations=[cs, el, face, back], products=[prod])
    return p, face, back


@pytest.fixture(scope="module")
def jobs():
    ppfmt.load_all()
    p, face, back = make_project()
    return p, ppfmt.drill_job(p, face), ppfmt.drill_job(p, back)


def out(key, job, enc="utf-8"):
    files = ppfmt.load_all()[key].fn(job)
    assert len(files) == 1
    return files[0][0], files[0][1].decode(enc)


def test_registered():
    reg = ppfmt.load_all()
    for k, ext in KEYS:
        assert reg[k].group == "cnc" and reg[k].ext == ext and reg[k].note


def test_names_and_no_foreign_name(jobs):
    _p, f, b = jobs
    for k, ext in KEYS:
        for j in (f, b):
            if k == "nanxing_syntec" and j is b:
                continue                                    # orqa tomon — old tomon faylida (test_nanxing_back_merged…)
            name, text = out(k, j)
            assert name == f"{j.code}.{ext}"
            assert "giblab" not in text.lower()


# ───────────────────────── HIRZT ─────────────────────────
def test_hirzt_face(jobs):
    _p, f, _b = jobs
    _n, t = out("hirzt_magi", f)
    L = t.split("\r\n")
    assert L[:5] == ["BEGIN ID CID3", " ''=01_001 bok", " REL= 3.10", " AXIS= x+,y-,z-", "END ID"]
    assert "[ 0.0 ] PROGETTO  999901_01_001 (" in L
    # tartib: yuz guruhi (teshik + paz dastur tartibida), chap, o'ng, y=dy (SOPRA), y=0 (SOTTO); freza chiqmaydi
    paths = [x for x in L if "PATH" in x]
    assert len(paths) == 8
    assert paths[0] == '[ 0.1 ] PATH    "" "Drill\\1_Single.pm4" (QX = 100 "Quota X",QY = 50 "Quota Y",DIA = 5 "Diametro",PRF = 12 "Profondita")'
    assert paths[3] == '[ 0.4 ] PATH    "" "Saw\\X1_LPX.pm4" QY = 350 "Quota Y",LPX = 600 "Larghezza",PRF = 8 "Profondita",SP = 4 "Spessore lama")'
    assert 'QX = 40 "Quota X",QY = 8 "Quota Y"' in paths[4]              # chap
    assert 'QX = 120.5 "Quota X",QY = 8 "Quota Y"' in paths[5]           # o'ng
    assert 'QX = 450 "Quota X",QY = 8 "Quota Y"' in paths[6]             # y=dy: L − x
    assert 'QX = 100 "Quota X",QY = 10 "Quota Y"' in paths[7]            # y=0: dz − z
    labs = [x.split("CREA_LAB ")[1] for x in L if "CREA_LAB" in x]
    assert labs == ["FRONTALE"] * 4 + ["SINISTRA", "DESTRA", "SOPRA", "SOTTO"]
    assert "[ 15.0 ] INSERISCI FORI SIMMETRICO ASSE_Y PIANO  #5" in L and "[ 18.0 ] INSERISCI FORI  #6" in L
    assert "[ 3.0 ] INSERISCI FORI #1" in L
    tech = [x for x in L if x.startswith("&&&")]
    assert [re.search(r"#TYPE=(\d)", x).group(1) for x in tech] == ["1", "2", "3", "1", "1", "1", "1", "1"]
    assert tech[3].endswith("#TYPE=1,#AZ=0.0,#DIAM=4,#ID_PARDEPTH=8,#ISBLOCK=0,#SAWINSERTMODE=0")
    assert "  POINT,X=100,Y=50,Z=0" in L and "  POINT,X=0.0 ,Y=40,Z=8" in L and "  POINT,X=600.0 ,Y=120.5,Z=8" in L
    assert "  POINT,X=450 ,Y=400.0,Z=8" in L and "  POINT,X=100 ,Y=0.0,Z=10" in L
    assert "    LINE,XS=0,YS=350,ZS=8,XE=600,YE=350,ZE=8" in L
    assert [x for x in L if "WORKSIDE=" in x and "#" not in x] == [
        "   WORKSIDE=0", "   WORKSIDE=0", "   WORKSIDE=0", "    WORKSIDE=0", "   WORKSIDE=1", "   WORKSIDE=3",
        "   WORKSIDE=2", "   WORKSIDE=4"]
    assert L[-2:] == ["END BLOCK", ""]


def test_hirzt_back_and_empty(jobs):
    p, _f, b = jobs
    _n, t = out("hirzt_magi", b)
    assert 'QX = 550 "Quota X",QY = 60 "Quota Y"' in t                   # X ag'darilgan
    assert "LINE,XS=0,YS=0,ZS=8,XE=500,YE=0,ZE=8" in t
    op = Operation(type=OpType.XNC, code="E", name="bo'sh", xnc=XNCParams(by_part_size=False, length=100, width=50, thickness=16,
                                                                           program=[c("MillStart", X=-5, Y=10, DP=16, D=8, C=1),
                                                                                    c("MillLine", X=105, Y=10)]))
    p2 = Project(name="x", operations=[op])
    _n, t = out("hirzt_magi", ppfmt.drill_job(p2, op))
    assert "BEGIN BLOCK" not in t and "PATH" not in t and t.endswith("END PARAMETRIC SECTION\r\n")


# ───────────────────────── KDT ─────────────────────────
def test_kdt_face(jobs):
    _p, f, _b = jobs
    _n, t = out("kdt_trepan", f)
    L = t.split("\r\n")
    assert L[:8] == ['<?xml version="1.0" encoding="UTF-8"?>', "<AndersonXMLdata>", "<PANEL>", "<PanelLength>600</PanelLength>",
                     "<PanelWidth>400</PanelWidth>", "<PanelThickness>16</PanelThickness>", "<PanelName>01_001 bok</PanelName>",
                     "</PANEL>"]
    cads = t.split("<CAD>\r\n")[1:]
    names = [re.search(r"<TypeName>(.*?)</TypeName>", x).group(1) for x in cads]
    assert names == ["Vertical Hole"] * 3 + ["Groove", "Line", "Arc", "Line"] + ["Horizontal Hole"] * 4
    assert "<X1>500</X1>\r\n<Y1>50</Y1>\r\n<Depth>12</Depth>\r\n<Diameter>5</Diameter>\r\n<HoleNo>1</HoleNo>" in cads[0]   # L − x
    assert "<Depth>19</Depth>" in cads[1]
    assert "<BeginX>600</BeginX>\r\n<BeginY>350</BeginY>\r\n<EndX>0</EndX>\r\n<EndY>350</EndY>\r\n<Width>4</Width>\r\n" \
           "<Correction>0</Correction>\r\n<UseSaw>1</UseSaw>\r\n<Depth>8</Depth>" in cads[3]
    assert "<BeginX>50</BeginX>\r\n<BeginY>410</BeginY>\r\n<EndX>50</EndX>\r\n<EndY>350</EndY>\r\n<Width>8</Width>\r\n" \
           "<Correction>2</Correction>\r\n<Depth>16</Depth>" in cads[4]                 # C=1 → 2
    assert "<StartX>50</StartX>\r\n<StartY>350</StartY>\r\n<EndX>40</EndX>\r\n<EndY>340</EndY>\r\n<Radius>10</Radius>\r\n" \
           "<Direction>0</Direction>\r\n<Correction>2</Correction>\r\n<Width>8</Width>\r\n<Depth>16</Depth>" in cads[5]
    # qirra: Quadrant 1 (o'ng, X1=0), 2 (chap, X1=L), 4 (y=0), 3 (y=W); X1/Quadrant tartibi turlicha
    assert "<PlaneID>2</PlaneID>\r\n<X1>0</X1>\r\n<Quadrant>1</Quadrant>\r\n<Y1>120.5</Y1>\r\n<Z1>8</Z1>" in cads[7]
    assert "<PlaneID>2</PlaneID>\r\n<X1>600</X1>\r\n<Quadrant>2</Quadrant>\r\n<Y1>40</Y1>" in cads[8]
    assert "<Quadrant>4</Quadrant>\r\n<X1>500</X1>\r\n<Y1>0</Y1>\r\n<Z1>10</Z1>\r\n<Depth>30</Depth>" in cads[9]
    assert "<Quadrant>3</Quadrant>\r\n<X1>450</X1>\r\n<Y1>400</Y1>\r\n<Z1>8</Z1>" in cads[10]
    assert t.endswith("</CAD>\r\n</AndersonXMLdata>\r\n")


def test_kdt_back(jobs):
    _p, _f, b = jobs
    _n, t = out("kdt_trepan", b)
    assert "<X1>50</X1>\r\n<Y1>60</Y1>" in t                              # ikki marta aks → X1 = x
    assert "<BeginX>600</BeginX>\r\n<BeginY>0</BeginY>\r\n<EndX>100</EndX>" in t


# ───────────────────────── XDWoodCam ─────────────────────────
def test_xd_face(jobs):
    _p, f, _b = jobs
    _n, t = out("xd_woodcam", f)
    L = t.split("\r\n")
    assert L[:10] == ["[WXF]", "Version=2.0", "Description=9001 mijoz 999901_01_001", "Password=" + "0" * 32, "X_Length=600",
                      "Y_Width=400", "Z_Thickness=16", "Edge=Type:61184 Left:1 Front:0 Right:0 Back:1", "Contour=", "[DATA]"]
    tail = " Disable:0 ImageX:0 ImageY:0 ImageXY:0 Tool:0 Num:1 Dx:0 Dy:0 Edge:0"
    assert L[10:] == [
        "Count=8",                                                        # paz chiqmaydi
        "1=Type:57856 Panel:0 Ref:0 Xs:100 Ys:350 Zs:12 Dia:5" + tail,
        "2=Type:57856 Panel:0 Ref:0 Xs:8 Ys:200 Zs:19 Dia:8" + tail,
        "3=Type:57856 Panel:0 Ref:0 Xs:300 Ys:200 Zs:12.5 Dia:15" + tail,
        "4=Type:59904 Panel:1 Ref:0 Xs:30 Ys:360 Zs:8 Dia:8" + tail,      # chap: chuqurlik, W − y
        "5=Type:59904 Panel:2 Ref:0 Xs:32 Ys:120.5 Zs:8 Dia:4.5" + tail,  # o'ng: chuqurlik, y
        "6=Type:59904 Panel:3 Ref:0 Xs:100 Ys:30 Zs:10 Dia:8" + tail,     # y=0: x, chuqurlik; Zs = dz − z
        "7=Type:59904 Panel:4 Ref:0 Xs:450 Ys:34 Zs:8 Dia:8" + tail,      # y=W: L − x
        "8=Type:58368 Panel:0 Ref:0 Xs:550 Ys:-10 Zs:16 Dia:8 Disable:0 ImageX:0 ImageY:0 ImageXY:0 Tool:0 RK:2 Num:3 "
        "LineTo:(Xe:550, Ye:50, Dep:16) ArcTo:(Xc:560, Yc:50, Dep:16, Angle:90) LineTo:(Xe:610, Ye:60, Dep:16)",
        ""]


def test_xd_back(jobs):
    _p, _f, b = jobs
    _n, t = out("xd_woodcam", b)
    L = t.split("\r\n")
    assert "Edge=Type:61184 Left:0 Front:0 Right:1 Back:1" in L            # chap ↔ o'ng
    assert L[10] == "Count=1" and L[11].startswith("1=Type:57856 Panel:0 Ref:0 Xs:550 Ys:340 Zs:11 Dia:8 ")


# ───────────────────────── Nanxing SyntecCad ─────────────────────────
# Format — stanok qabul qilgan namunadagidek (2026-10-22): to'rtburchak kontur, EdgeGroup, freza markaz yo'li (中), ID, IsGenCode=2.
def _rows(t):
    assert t.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<Root ') and t.endswith("</Root>\r\n")
    return t.split("\n", 1)[1].split("\r\n")[:-1]


def test_nanxing_face(jobs):
    _p, f, _b = jobs
    name, t = out("nanxing_syntec", f)
    R = _rows(t)
    assert name == "999901_01_001.scx"
    assert R[:4] == ['<Root Cad="MebeliX Kroy" version="2.0">', "<Project>", "<Panels>",
                     '<Panel ID="01_01_001" IsProduce="true" Length="600" MachiningPoint="1" Name="01_001 bok" '
                     'Thickness="16" Width="400">']                     # ID — mahsulot kodi + detal kodi
    assert R[4:10] == ["<Outline>", '<Point X="600" Y="0"/>', '<Point X="600" Y="400"/>', '<Point X="0" Y="400"/>',
                       '<Point X="0" Y="0"/>', "</Outline>"]
    assert R[10:14] == ["<EdgeGroup>",                                   # chap va XNC y=W (Nanxing pastki) kromka
                        '<Edge CentralAngle="0" Face="4" Pre_Milling="1.0" Thickness="1.0" X="0" Y="0"/>',
                        '<Edge CentralAngle="0" Face="2" Pre_Milling="1.0" Thickness="1.0" X="0" Y="0"/>', "</EdgeGroup>"]
    m = [r for r in R if r.startswith("<Machining ")]
    # tartib: qirra teshiklari → yuza teshiklari → paz → freza
    assert m[0] == '<Machining Depth="30" Diameter="8" Face="4" ID="1000" IsGenCode="2" Type="1" X="0" Y="360" Z="8"/>'
    assert m[1] == '<Machining Depth="32" Diameter="4.5" Face="3" ID="1001" IsGenCode="2" Type="1" X="600" Y="279.5" Z="8"/>'
    assert m[2] == '<Machining Depth="30" Diameter="8" Face="1" ID="1002" IsGenCode="2" Type="1" X="100" Y="400" Z="6"/>'
    assert m[3] == '<Machining Depth="34" Diameter="8" Face="2" ID="1003" IsGenCode="2" Type="1" X="150" Y="0" Z="8"/>'
    assert m[4] == '<Machining Depth="12" Diameter="5" Face="5" ID="1004" IsGenCode="2" Type="2" X="100" Y="350"/>'
    assert m[7] == ('<Machining Depth="8" EndX="600" EndY="50" EndZ="16" Face="5" ID="1007" IsGenCode="2" ToolOffset="中" '
                    'Type="4" Width="4" X="0" Y="50" Z="16"/>')
    # freza: asbob markazi (d/2 = 4 korreksiya tomoniga), yoy radiusi 10 − 4
    i = R.index('<Machining Closed="0" Depth="16" Diameter="8" Face="5" ID="1008" IsGenCode="2" Pocket="0" ToolOffset="中" '
                'Type="3" X="554" Y="-10">')
    assert R[i + 1:i + 7] == ["<Lines>", '<Line Angle="0" EndX="554" EndY="50" LineID="0"/>',
                              '<Line Angle="90" EndX="560" EndY="56" LineID="1"/>',
                              '<Line Angle="0" EndX="610" EndY="56" LineID="2"/>', "</Lines>", "</Machining>"]
    assert "左" not in t and "右" not in t


def test_nanxing_back_merged_into_front_file(jobs):
    """Orqa tomon dasturi alohida fayl emas: amallari Face=6 bilan old tomon fayliga (X ag'darilmaydi)."""
    p, f, b = jobs
    assert ppfmt.load_all()["nanxing_syntec"].fn(b) == []
    files = ppfmt.load_all()["nanxing_syntec"].batch([f, b], p)
    assert [n for n, _d in files] == ["999901_01_001.scx"]
    assert ppfmt.load_all()["nanxing_syntec"].batch([b], p)[0][0] == "999901_01_001.scx"     # faqat orqasi tanlansa ham
    R = _rows(files[0][1].decode("utf-8"))
    m = [r for r in R if r.startswith("<Machining ")]
    assert m[-2] == '<Machining Depth="11" Diameter="8" Face="6" ID="1009" IsGenCode="2" Type="2" X="50" Y="340"/>'
    assert m[-1] == ('<Machining Depth="8" EndX="100" EndY="400" EndZ="16" Face="6" ID="1010" IsGenCode="2" ToolOffset="中" '
                     'Type="4" Width="6" X="600" Y="400" Z="16"/>')


def test_nanxing_plain_part_and_latin_name():
    op = Operation(type=OpType.XNC, code="P", name="№1 Полка – верх",
                   xnc=XNCParams(by_part_size=False, length=300, width=200, thickness=16,
                                 program=[c("DrillFront", X=10, Y=10, D=5, DP=5)]))
    _n, t = out("nanxing_syntec", ppfmt.drill_job(Project(name="x", operations=[op]), op))
    R = _rows(t)
    assert R[3] == '<Panel ID="P" IsProduce="true" Length="300" MachiningPoint="1" Name="№1 Polka - verh" Thickness="16" Width="200">'
    assert "<EdgeGroup>" not in R and R[10] == "<Machines>"


def _one(prog, L=600, W=400, T=16, **kw):
    op = Operation(type=OpType.XNC, code="S", name="s",
                   xnc=XNCParams(by_part_size=False, length=L, width=W, thickness=T, program=prog, **kw))
    return _rows(out("nanxing_syntec", ppfmt.drill_job(Project(name="x", operations=[op]), op))[1])


def test_nanxing_order_pocket_border_and_depth_vars():
    R = _one([c("DrillFront", X=100, Y=50, D=5, DP=12),
              c("MillStart", X=16, Y=416 - 400 + 300, DP=8, D=4, C=3),          # cho'ntak 8×4, freza d=4
              c("MillLine", X=16, Y=320), c("MillLine", X=8, Y=320), c("MillLine", X=8, Y=316), c("MillLine", X=16, Y=316),
              c("DrillLeft", Y=40, Z=8, M="true", D=8, DP=30),
              c("MillStart", X=0, Y=-10, DP="throughCutDepth", D=8, C=2),     # chet bo'ylab, c=2; o'zgaruvchi e'lon qilinmagan
              c("MillLine", X=0, Y=410)])
    m = [r for r in R if r.startswith("<Machining ")]
    assert 'Face="4"' in m[0] and 'Type="2"' in m[1]                       # tartib: qirra → yuza → freza
    i = R.index(m[2])
    assert m[2].endswith('ToolOffset="中" Type="3" X="14" Y="82">')          # cho'ntak ichiga: 10..14 chiziq
    assert R[i + 2:i + 4] == ['<Line Angle="0" EndX="10" EndY="82" LineID="0"/>', '<Line Angle="0" EndX="14" EndY="82" LineID="1"/>']
    assert m[3] == ('<Machining Closed="0" Depth="19" Diameter="8" Face="5" ID="1003" IsGenCode="2" Pocket="0" ToolOffset="右" '
                    'Type="3" X="0" Y="410">')                             # xom yo'l, chuqurlik dz+3


def test_nanxing_double_thickness_and_mirror():
    cs = Operation(type=OpType.CS, code="L16", name="LDSP 16", cs_material=CSMaterialParams(thickness=16))
    xop = Operation(type=OpType.XNC, code="D", name="qo'sh",
                    xnc=XNCParams(by_part_size=False, length=500, width=300, thickness=32, mirror_x=True,
                                  program=[c("DrillFront", X=100, Y=50, D=5, DP=35), c("DrillLeft", Y=40, Z=16, M="true", D=8, DP=30)]))
    cs.parts.append(Part(name="qo'sh", length=500, width=300, qty=1, xnc_op_ids=[xop.id]))
    R = _rows(out("nanxing_syntec", ppfmt.drill_job(Project(name="x", operations=[cs, xop]), xop))[1])
    assert 'Thickness="16"' in R[3]
    m = [r for r in R if r.startswith("<Machining ")]
    assert m[0] == '<Machining Depth="30" Diameter="8" Face="3" ID="1000" IsGenCode="2" Type="1" X="500" Y="260" Z="8"/>'   # ko'zgu: chap → o'ng
    assert m[1] == '<Machining Depth="19" Diameter="5" Face="5" ID="1001" IsGenCode="2" Type="2" X="400" Y="250"/>'


def _sample_shape(c_side, start_x, arcs_dir):
    """Namunadagi shakl: 700×450, past burchaklari r=100 bilan o'tuvchi freza (d=8)."""
    if c_side == 2:
        prog = [c("MillStart", X=700, Y=-30, DP="dz", D=8, C=2, T="Mill8"), c("MillLine", X=700, Y=350),
                c("MillArcCenter", X=600, Y=450, CX=600, CY=350, DIR="true"), c("MillLine", X=100, Y=450),
                c("MillArcCenter", X=0, Y=350, CX=100, CY=350, DIR="true"), c("MillLine", X=0, Y=-30)]
    else:
        prog = [c("MillStart", X=0, Y=-30, DP="dz", D=8, C=1, T="Mill8"), c("MillLine", X=0, Y=350),
                c("MillArcCenter", X=100, Y=450, CX=100, CY=350, DIR="false"), c("MillLine", X=600, Y=450),
                c("MillArcCenter", X=700, Y=350, CX=600, CY=350, DIR="false"), c("MillLine", X=700, Y=-30)]
    op = Operation(type=OpType.XNC, code="S", name="pol",
                   xnc=XNCParams(by_part_size=False, length=700, width=450, thickness=16, program=prog))
    return _rows(out("nanxing_syntec", ppfmt.drill_job(Project(name="x", operations=[op]), op))[1])


def test_nanxing_mill_center_path_like_sample():
    """Stanok xatosi «Mill path node not on panel outline» — freza markaz yo'li namunadagidek bo'lishi shart."""
    R = _sample_shape(2, 700, True)
    assert R[4:10] == ["<Outline>", '<Point X="700" Y="0"/>', '<Point X="700" Y="450"/>', '<Point X="0" Y="450"/>',
                       '<Point X="0" Y="0"/>', "</Outline>"]
    i = next(k for k, r in enumerate(R) if 'Type="3"' in r)
    assert R[i].endswith('ToolOffset="中" Type="3" X="704" Y="480">')
    assert R[i + 2:i + 7] == ['<Line Angle="0" EndX="704" EndY="100" LineID="0"/>',
                              '<Line Angle="90" EndX="600" EndY="-4" LineID="1"/>',
                              '<Line Angle="0" EndX="100" EndY="-4" LineID="2"/>',
                              '<Line Angle="90" EndX="-4" EndY="100" LineID="3"/>',
                              '<Line Angle="0" EndX="-4" EndY="480" LineID="4"/>']
    R = _sample_shape(1, 0, False)
    i = next(k for k, r in enumerate(R) if 'Type="3"' in r)
    assert R[i].endswith('ToolOffset="中" Type="3" X="-4" Y="480">')
    assert R[i + 2:i + 7] == ['<Line Angle="0" EndX="-4" EndY="100" LineID="0"/>',
                              '<Line Angle="-90" EndX="100" EndY="-4" LineID="1"/>',
                              '<Line Angle="0" EndX="600" EndY="-4" LineID="2"/>',
                              '<Line Angle="-90" EndX="704" EndY="100" LineID="3"/>',
                              '<Line Angle="0" EndX="704" EndY="480" LineID="4"/>']


def test_nanxing_latin():
    assert NX.latin("в„–01_004 pol") == "v„-01_004 pol"
    assert NX.latin("Шкаф Ўрта қопқоқ") == "Shkaf O'rta qopqoq"


# ───────────────────────── Daron ─────────────────────────
def test_daron_face(jobs):
    _p, f, _b = jobs
    L = DA.program(f, when="2026/01/01 12:00:00").split("\r\n")
    assert L[0] == '<MicroDrawBan_XML Version="3.0" Time="2026/01/01 12:00:00" Source="" SourceType="BAN">'
    assert L[1] == ('<Plane Name="01_001 bok" Code="999901_01_001" Material="LDSP 16" PlaneNo=" " Width="600" Hight="400" '
                    'Thickness="16" Grain="DIR_HOR" EdgeFBLR="1 ,0 ,1 ,0" PlaneSize="1" MachineBase="-1">')
    i, j = L.index("<Outline>"), L.index("</Outline>")
    ol = L[i + 1:j]
    # kesilgan kontur: yo'lga kirish nuqtasidan (C=1 — chiqish uchi), X = x − L
    assert ol[0] == ol[-1] == '<Point Value="0 340 0"/>' and ol[1] == '<Point Value="-40 340 0"/>'
    assert ol[8:13] == ['<Point Value="-50 350 0"/>', '<Point Value="-50 400 0"/>', '<Point Value="-600 400 0"/>',
                        '<Point Value="-600 0 0"/>', '<Point Value="0 0 0"/>']
    assert len(ol) == 14
    body = L[j + 1:-3]
    assert body[0] == '<HoleV Name="" Face="A" Start="-500 50 0.00" End="-500 50 -12" Diameter="5" IsCuted="0"/>'
    assert body[1] == '<HoleV Name="" Face="A" Start="-592 200 0.00" End="-592 200 -19" Diameter="8" IsCuted="0"/>'
    assert body[3] == '<SlotL Start="-600 350 -8" End="0 350 -8" Face="A" Width="4" IsCuted="0" />'
    # asbob markazi: chiziq 4 mm o'ngga (x + 4), yoy radiusi 10 − 4, SlotA soat miliga teskari
    assert body[4] == '<SlotL Start="-46 410 -16" End="-46 350 -16" Face="A" Width="8" IsCuted="0" />'
    assert body[5] == '<SlotA Start="-46 350 -16" End="-40 344 -16" Center="-40 350 -16" Face="A" Width="8" IsCuted="0" />'
    assert body[6] == '<SlotL Start="-40 344 -16" End="10 344 -16" Face="A" Width="8" IsCuted="0" />'
    assert body[7] == '<HoleH Name="" Face="L" Start="-600 40 -8" End="-570 40 -8" Diameter="8" IsCuted="0"/>'
    assert body[8] == '<HoleH Name="" Face="R" Start="0 120.5 -8" End="-32 120.5 -8" Diameter="4.5" IsCuted="0"/>'
    assert body[9] == '<HoleH Name="" Face="D" Start="-500 0 -10" End="-500 30 -10" Diameter="8" IsCuted="0"/>'
    assert body[10] == '<HoleH Name="" Face="U" Start="-450 400 -8" End="-450 366 -8" Diameter="8" IsCuted="0"/>'
    assert L[-3:] == ["</Plane>", "</MicroDrawBan_XML>", ""]


def test_daron_back(jobs):
    _p, _f, b = jobs
    name, t = out("daron_foxcnc", b)
    assert re.search(r'Time="\d{4}/\d\d/\d\d \d\d:\d\d:\d\d"', t)
    assert 'EdgeFBLR="1 ,0 ,0 ,1"' in t
    assert '<HoleV Name="" Face="A" Start="-50 60 0.00" End="-50 60 -11" Diameter="8" IsCuted="0"/>' in t      # X = −x
    assert '<SlotL Start="-600 0 -8" End="-100 0 -8" Face="A" Width="6" IsCuted="0" />' in t
    L = t.split("\r\n")
    ol = L[L.index("<Outline>") + 1:L.index("</Outline>")]
    assert ol[0] == '<Point Value="-600 340 0"/>' and ol[1] == '<Point Value="-560 340 0"/>'    # kontur X bo'yicha ag'darilgan


def test_daron_offset_corner():
    """Ichki burchak: siljigan chiziqlar kesishish nuqtasida tutashadi; C=2 — chapga."""
    cont = [dict(t="ms", x=100.0, y=-10.0, dp=16.0, d=8.0, c=1), dict(t="ml", x=100.0, y=54.0), dict(t="ml", x=-10.0, y=54.0)]
    segs = DA.offset_path(cont)
    assert [s[0] for s in segs] == ["L", "L"]
    assert segs[0][1] == (96.0, -10.0) and segs[0][2] == pytest.approx((96.0, 50.0)) and segs[1][2] == (-10.0, 50.0)
    cont[0]["c"] = 2
    segs = DA.offset_path(cont)
    assert segs[0][2] == pytest.approx((104.0, 58.0))
    cont[0]["c"] = 0
    segs = DA.offset_path(cont)
    assert segs[0][1] == (100.0, -10.0) and segs[1][2] == (-10.0, 54.0)


# ───────────────────────── umumiy geometriya ─────────────────────────
def test_cut_outline_plain_and_two_cuts():
    poly, seam, rseam = C2.cut_outline(600, 400, [])
    assert poly == [(0.0, 400.0), (0.0, 0.0), (600.0, 0.0), (600.0, 400.0)] and seam == (0.0, 400.0) and rseam == (0.0, 0.0)
    a = [dict(t="ms", x=100.0, y=-10.0, dp=16.0, d=8.0, c=1), dict(t="ml", x=100.0, y=54.0), dict(t="ml", x=-10.0, y=54.0)]
    b = [dict(t="ms", x=610.0, y=300.0, dp=16.0, d=8.0, c=2), dict(t="ml", x=500.0, y=300.0), dict(t="ml", x=500.0, y=410.0)]
    poly, seam, _r = C2.cut_outline(600, 400, [a, b])
    assert seam == (0.0, 54.0) and poly[0] == seam           # chok — birinchi kesimda qoladi
    assert poly == [(0.0, 54.0), (100.0, 54.0), (100.0, 0.0), (600.0, 0.0), (600.0, 300.0), (500.0, 300.0), (500.0, 400.0),
                    (0.0, 400.0)]
    # detalni kesmaydigan (qirra bo'ylab yoki ichkarida tugaydigan) kontur — o'zgarishsiz
    e = [dict(t="ms", x=610.0, y=0.0, dp=16.0, d=8.0, c=1), dict(t="ml", x=300.0, y=0.0)]
    i = [dict(t="ms", x=-10.0, y=100.0, dp=16.0, d=8.0, c=1), dict(t="ml", x=300.0, y=100.0)]
    assert C2.cut_outline(600, 400, [e, i])[0] == [(0.0, 400.0), (0.0, 0.0), (600.0, 0.0), (600.0, 400.0)]


def test_arc_segments_and_num():
    assert [C2.arc_segments(6, 90), C2.arc_segments(10, 90), C2.arc_segments(150, 90), C2.arc_segments(27.135, 63.435)] == [5, 7, 23, 7]
    assert C2.num(-0.00001, 4) == "0" and C2.num(1239.99994, 4) == "1239.9999" and C2.num(-54.354102, 5) == "-54.3541"
    assert C2.xml_attr('a "b" & <c>') == "a &quot;b&quot; &amp; &lt;c&gt;"
