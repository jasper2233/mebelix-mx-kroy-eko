"""Ishlov markazi (prisadka) o'rnatilgan formatlari: TPA (.CNC), Homag woodWOP (.mpr), Biesse Works (.bpp), SCM Xilog v3 (.pgm),
SCM Startech (.ISO) — sun'iy XNC dasturlari bilan (yuz teshigi, qirra teshigi, paz, freza chiziq + yoy, orqa tomon).
Korxona namunalari bilan bayt-ma-bayt solishtirish — `tools/bench/pp_cnc_check.py`."""
import io
import zipfile

import pytest

from app.models import EdgeRef, ELParams, Operation, OpType, Part, Project, XNCParams, XncCommand
from app.services import ppfmt
from app.services.ppfmt import xilog3 as XL
from app.services.ppfmt.scm_startech import groove_passes


def c(kind, **p):
    return XncCommand(cmd=kind, params=p)


FACE = [
    c("DrillFront", X=34, Y=70, D=5, DP=13, T="Bore5"),
    c("DrillFront", X=8, Y=200, D=8, DP="dz+3", T="BoreTh8"),
    c("DrillLeft", Y=50, Z=8, M="true", D=8, DP=34, T="Bore8"),
    c("DrillTop", X=100, Z=6, M="false", D=8, DP=30, T="Bore8"),
    c("DrillRight", Y=120.5, Z=8, M="true", D=4.5, DP=32, T="Bore4.5"),
    c("Groove", X1=0, Y1=380, X2=600, Y2=380, DP=8, W=6, D=4, T="Cut4"),
    c("MillStart", X=-10, Y=100, DP=16, D=8, C=1, T="Mill8"),
    c("MillLine", X=300, Y=100),
    c("MillArcCenter", X=400, Y=200, CX=300, CY=200, DIR="true"),
]
BACK = [
    c("DrillFront", X=50, Y=60, D=8, DP=11, T="Bore8"),
    c("Groove", X1=600, Y1=0, X2=100, Y2=0, DP=8, W=4, D=4, T="Cut4"),
]


def make_project():
    el = Operation(type=OpType.EL, code="PVC", name="PVC 1x19", el=ELParams(width=19, thickness=1, symbol="A", color="#D2691E"))
    face = Operation(type=OpType.XNC, code="999901_01_001", name="01_001 bok",
                     xnc=XNCParams(by_part_size=False, length=600, width=400, thickness=16, qty=1, program=FACE))
    back = Operation(type=OpType.XNC, code="999901_01_001_2", name="01_001 bok",
                     xnc=XNCParams(by_part_size=False, length=600, width=400, thickness=16, qty=1, face_side=False,
                                   program=BACK))
    part = Part(name="01_001 bok", code="01_001", length=600, width=400, qty=2, edge_bottom=EdgeRef(op_id=el.id),
                edge_left=EdgeRef(op_id=el.id), xnc_op_ids=[face.id, back.id])
    cs = Operation(type=OpType.CS, code="LDSP16", name="LDSP 16", parts=[part])
    p = Project(name="Sinov", operations=[cs, el, face, back])
    return p, face, back


@pytest.fixture(scope="module")
def jobs():
    ppfmt.load_all()
    p, face, back = make_project()
    return p, ppfmt.drill_job(p, face), ppfmt.drill_job(p, back)


def text(files, i=0, enc="cp1251"):
    return files[i][1].decode(enc).split("\r\n")


def test_registered():
    reg = ppfmt.load_all()
    for k, ext in (("tpa", "CNC"), ("woodwop", "mpr"), ("biesseworks", "bpp"), ("xilog3", "pgm"), ("scm_startech", "ISO")):
        assert reg[k].group == "cnc" and reg[k].ext == ext and reg[k].note
    assert reg["scm_startech"].batch and reg["biesseworks"].batch


def test_no_foreign_name_in_output(jobs):
    p, f, b = jobs
    reg = ppfmt.load_all()
    for k in ("tpa", "woodwop", "biesseworks", "xilog3", "scm_startech"):
        fmt = reg[k]
        files = fmt.batch([f, b], p) if fmt.batch else fmt.fn(f) + fmt.fn(b)
        for _n, data in files:
            assert b"giblab" not in data.lower()


# ───────────────────────── TPA ─────────────────────────
def test_tpa_face(jobs):
    _p, f, _b = jobs
    files = ppfmt.load_all()["tpa"].fn(f)
    assert files[0][0] == "999901_01_001.CNC"
    L = text(files)
    assert L[:4] == ["TPA\\ALBATROS\\EDICAD\\01.00:86:r0w0h0", "$=01_001 bok", "::SIDE=1", "::UNm DL=600 DH=400 DS=16"]
    s1 = L[L.index("SIDE#1{") + 1:L.index("SIDE#2{") - 1]
    assert s1[0] == "W#81{ ::WTp #1=34 #2=70 #3=-13 #1002=5.0 #1001=0 }W"
    assert s1[1] == "W#81{ ::WTp #1=8 #2=200 #3=-19 #1002=8.0 #1001=1 }W"            # o'tuvchi (dp > dz)
    assert s1[2] == ("W#1050{ ::WT2 #6=1 #8509=0 #8517=600 #8510=0 #8511=380 #8512=-8 #8514=1 #8515=1 #8525=0 #8526=0 "
                     "#8527=0 }W")
    assert s1[3] == "W#89{ ::WTs #1=-10 #2=100 #3=-16 #40=1 #36=4 }W"
    assert s1[4] == "W#2201{ ::WTl  #1=300  #2=100 }W"
    assert s1[5] == "W#2101{ ::WTa  #1=400  #2=200 #34=1 #31=0 #32=100 }W"           # markaz — boshlanishga nisbatan
    assert L[L.index("SIDE#3{") + 1] == "W#81{ ::WTp #1=100 #2=10 #3=-30 #1002=8.0 #1001=0 }W"   # dz − z = 16 − 6
    assert L[L.index("SIDE#4{") + 1] == "W#81{ ::WTp #1=120.5 #2=8 #3=-32 #1002=4.5 #1001=0 }W"
    assert L[L.index("SIDE#6{") + 1] == "W#81{ ::WTp #1=50 #2=8 #3=-34 #1002=8.0 #1001=0 }W"
    assert L[-2:] == ["}SIDE", ""]


def test_tpa_back(jobs):
    _p, _f, b = jobs
    L = text(ppfmt.load_all()["tpa"].fn(b))
    s1 = L[L.index("SIDE#1{") + 1:L.index("SIDE#2{") - 1]
    assert s1[0] == "W#81{ ::WTp #1=550 #2=60 #3=-11 #1002=8.0 #1001=0 }W"          # X = dx − x
    assert "#8517=500 #8510=0 #8511=0" in s1[1]


# ───────────────────────── Homag woodWOP ─────────────────────────
def test_woodwop(jobs):
    _p, f, b = jobs
    files = ppfmt.load_all()["woodwop"].fn(f)
    assert files[0][0] == "999901_01_001.mpr"
    L = text(files)
    assert L[:2] == ["[H", 'VERSION="4.0 Alpha"'] and 'ANZ="2"' in L and "_BSX=600" in L and L[-2:] == ["!", ""]
    i = L.index("<102 \\BohrVert\\")
    assert L[i - 1] == "" and L[i + 1:i + 6] == ['XA="34"', 'YA="70"', 'BM="LS"', 'TI="13"', 'DU="5"']
    i = L.index("<102 \\BohrVert\\", i + 1)
    assert L[i + 1:i + 5] == ['XA="8"', 'YA="200"', 'BM="LSL"', 'DU="8"']               # o'tuvchi: chuqurliksiz
    hz = [L[j + 1:j + 7] for j, x in enumerate(L) if x == "<103 \\BohrHoriz\\"]
    assert hz[0] == ['XA="0"', 'YA="50"', 'ZA="8"', 'TI="34"', 'BM="XP"', 'DU="8"']
    assert hz[1] == ['XA="100"', 'YA="0"', 'ZA="10"', 'TI="30"', 'BM="YP"', 'DU="8"']
    assert hz[2] == ['XA="600.0"', 'YA="120.5"', 'ZA="8"', 'TI="32"', 'BM="XM"', 'DU="4.5"']
    i = L.index("<109 \\Nuten\\")
    assert L[i + 1:i + 8] == ['XA="0"', 'YA="380"', 'XE="600"', 'YE="380"', 'TI="8"', 'NB="6"', 'RK="NoWRK"']
    i = L.index("]1")
    assert L[i:i + 18] == ["]1", "$E0", "KP ", "X=-10", "Y=100", "Z=0", "KO=00", "", "$E1", "KL ", "X=300", "Y=100", "",
                           "$E2", "KA", "X=400", "Y=200", "DS=1"]
    assert L[i + 18] == "R=100"
    i = L.index("<105 \\Konturfraesen\\")
    assert L[i + 1:i + 4] == ['EA="1:0"', 'EE="1:2"', 'RK="WRKL"'] and 'ZA="0"' in L[i:i + 10]
    g = [j for j, x in enumerate(L) if x == "<152 \\Grafischer Kommentar\\"]
    assert L[g[0] + 1:g[0] + 13] == ['LOCAL="1"', 'XA="300"', 'YA="400"', 'BR="600"', 'HE="5"', 'WI="0"', 'ROT="210"',
                                     'GRUEN="105"', 'BLAU="30"', 'WIDTH="3"', 'KAT="PVC 1x19"', 'MNM="PVC 1x19"']
    assert L[g[1] + 2:g[1] + 4] == ['XA="0"', 'YA="200"']                                  # chap kromka
    assert L[g[2] + 1:g[2] + 3] == ['LOCAL="2"', 'XA="570"']                               # yuz tomon belgisi
    B = text(ppfmt.load_all()["woodwop"].fn(b))
    i = B.index("<102 \\BohrVert\\")
    assert B[i + 1:i + 3] == ['XA="550"', 'YA="60"']
    gb = [j for j, x in enumerate(B) if x == "<152 \\Grafischer Kommentar\\"]
    assert B[gb[1] + 2] == 'XA="600"'                                                      # orqada chap kromka o'ngda
    assert B[gb[2] + 1:gb[2] + 6] == ['LOCAL="2"', 'XA="30"', 'YA="30"', 'ROT="200"', 'GRUEN="10"']


# ───────────────────────── Biesse Works ─────────────────────────
def test_biesse(jobs):
    p, f, b = jobs
    files = ppfmt.load_all()["biesseworks"].batch([f, b], p)
    assert [n for n, _ in files] == ["999901_01_001.bpp", "999901_01_001_2.bpp"]
    L = text(files)
    assert L[:7] == ["[HEADER]", "TYPE=BPP", "VER=130", "", "[DESCRIPTION]", "|01_001 bok", "|"]
    assert "PAN=LPX|600||0|" in L and "PAN=LPZ|16||0|" in L
    prog = L[L.index("[PROGRAM]") + 1:L.index("[VBSCRIPT]") - 1]
    assert prog[0].startswith('@ BG, "", "", 11, "", 0 : 0, "1", 34, 70, 0, 13, 5, 0, -1, 32, 32, 50,')
    assert '"P00001", 0, "", "", 0,' in prog[0]
    assert prog[1].startswith('@ BG, "", "", 21, "", 0 : 0, "1", 8, 200, 0, 19, 8,') and '"P00002", 0, "", "", 1,' in prog[1]
    assert prog[2].startswith('@ BG, "", "", 32, "", 0 : 1, "1", 50, 8, 0, 34, 8,')       # chap qirra: X = y, Y = z
    assert prog[3].startswith('@ BG, "", "", 43, "", 0 : 4, "4", 100, 6, 0, 30, 8,')      # yuqori qirra: z (dz − z emas)
    assert prog[4].startswith('@ BG, "", "", 52, "", 0 : 3, "4", 120.5, 8, 0, 32, 4.5,')
    assert prog[5].startswith('@ CUT_G, "", "", 64, "", 0 : 0, "1", 0, 380, 0, 8, 2, 0, 0, 600, 380, 0, 0, "", 1, 4, -1,')
    assert ', 1, 0, 6, 0, 0, 0, 1, "P00006",' in prog[5]
    assert prog[6].startswith('@ ROUT, "", "", 75, "", 0 : "P00007", 0, "1", 0, 16, "", 1, 8, -1,') and '103, 1, 2, 9,' in prog[6]
    assert prog[7] == '  @ START_POINT, "", "", 86, "", 0 : -10, 100, 0'
    assert prog[8] == '  @ LINE_EP, "", "", 97, "", 0 : 300, 100, 0, 0, 0, 0, 0, 0, 0'
    assert prog[9] == '  @ ARC_EPCE, "", "", 108, "", 0 : 400, 200, 300, 200, 1, 0, 0, 0, 0, 0, 0'
    assert prog[10] == '  @ ENDPATH, "", "", 119, "", 0 :'
    assert prog[11].startswith('@ GEO, "", "EB", 0, "", 0 : "P00008"')
    assert '"(A) 1mm", LPX/2, -37, 0, 0,' in prog[15]
    assert any('"FACE MARK"' in x and '0, "1", 0, 1,' in x for x in prog)
    B = text(files, 1)
    bp = B[B.index("[PROGRAM]") + 1:B.index("[VBSCRIPT]") - 1]
    assert bp[0].startswith('@ BG, "", "", 11, "", 0 : 0, "1", 550, 60, 0, 11, 8,')
    assert '"P00013"' in bp[0]                                                           # hisoblagich yuz dasturidan davom etadi
    assert bp[1].startswith('@ CUT_G, "", "", 24, "", 0 : 0, "1", 0, 0, 0, 8, 2, 0, 0, 500, 0,')
    assert any('"ER"' in x for x in bp) and any('"FACE MARK"' in x and '0, "4", 0, 1,' in x for x in bp)
    single = text(ppfmt.load_all()["biesseworks"].fn(b))
    assert '"P00001"' in single[single.index("[PROGRAM]") + 1]


# ───────────────────────── SCM Xilog v3 ─────────────────────────
def test_xilog(jobs):
    _p, f, b = jobs
    files = ppfmt.load_all()["xilog3"].fn(f)
    assert files[0][0] == "999901_01_001.pgm"
    data = files[0][1]
    assert data[:2] == b"BM" and data[0x42:0x4E] == b"Xilog3-7.0 \x00" and data[-3:] == b"\x02\x37\x10"
    assert int.from_bytes(data[0x80:0x84], "little") == len(data)
    assert int.from_bytes(data[0x74:0x78], "little") == len(data) - 0x8A
    h, recs = XL.read_records(data)
    assert h == 'H DX=600 DY=400 DZ=16 -AB C=0 R=1 *MM /"def.tlg" ;^:(A) 1mm  >:(A) 1mm  01_001 bok'
    assert recs == [
        "XBO X=34 Y=70 Z=13 D=5 N=P F=1",
        "XBO X=8 Y=200 Z=19 D=8 N=L F=1",
        "XBO X=8 Y=50 Z=34 D=8 N=P F=3",
        "XBO X=100 Y=10 Z=30 D=8 N=P F=5",
        "XBO X=8 Y=120.5 Z=32 D=4.5 N=P F=2",
        "XG0 X=0 Y=380 Z=8 T=-1 F=1 C=0",
        "G1 X=600 Y=380",
        "XGIN Q=0 G=2 C=1",
        "XG0 X=-10 Y=100 Z=16 T=-1 F=1 C=1",
        "XL2P X=300 Y=100",
        "G2 X=400 Y=200 I=300 J=200",
        ";END",
    ]
    hb, rb = XL.read_records(ppfmt.load_all()["xilog3"].fn(b)[0][1])
    assert hb.endswith(";^:(A) 1mm  <:(A) 1mm  01_001 bok")                              # orqada chap kromka strelkasi «<»
    assert rb == ["XBO X=550 Y=60 Z=11 D=8 N=P F=1", "XG0 X=0 Y=0 Z=8 T=-1 F=1 C=0", "G1 X=500 Y=0", ";END"]


def test_xilog_round():
    assert XL.fmt(298.2989) == "298.3" and XL.fmt(283.7059) == "283.71" and XL.fmt(568.0) == "568" and XL.fmt(-0.001) == "0"


# ───────────────────────── SCM Startech ─────────────────────────
def test_startech(jobs):
    p, f, b = jobs
    files = ppfmt.load_all()["scm_startech"].batch([b, f], p)       # orqa tomon baribir oxirida
    assert [n for n, _ in files] == ["1_2.ISO"]
    L = text(files, enc="ascii")
    assert L[:5] == ["o1", ";999901_01_001", "$1 X600.000 Y400.000 Z16.000", "(1.000,1.000,0.000)G200", "(1.000)G101"]
    # 6 mm paz, 4 mm arra: 2 o'tish (+3, +1 o'ng normal bo'ylab); «-0.000» — namunadagi kabi (burchak orqali hisob)
    assert L[5:7] == ["G300 X-0.000 Y17.000 Q600.000 Z8.000 K0 J2 I0", "G300 X-0.000 Y19.000 Q600.000 Z8.000 K0 J2 I0"]
    assert L[7:12] == ["G81 X34.000 Y330.000 Z13.000 K1 J0 I0 Q5.000", "G81 X8.000 Y200.000 Z19.000 K1 J0 I0 Q8.000",
                       "G81 X8.000 Y350.000 Z34.000 K2 J0 I0 Q8.000", "G81 X100.000 Y6.000 Z30.000 K4 J0 I0 Q8.000",
                       "G81 X8.000 Y279.500 Z32.000 K3 J0 I0 Q4.500"]
    assert L[12:15] == ["G80", "M30", ""]                         # freza chiqmaydi; bloklar orasida bo'sh qator
    assert L[15:17] == ["o2", ";999901_01_001_2"]
    assert "G300 X-0.000 Y398.000 Q500.000 Z8.000 K0 J2 I0" in L                     # orqa: X = dx − x, Y = dy − y
    assert "G81 X550.000 Y340.000 Z11.000 K1 J0 I0 Q8.000" in L
    assert L[-2:] == ["M30", ""]


def test_startech_split_99(jobs):
    p, f, _b = jobs
    files = ppfmt.load_all()["scm_startech"].batch([f] * 120, p)
    assert [n for n, _ in files] == ["1_99.ISO", "100_120.ISO"]
    L = text(files, 1, "ascii")
    assert L[0] == "o1" and "o21" in L and "o22" not in L


def test_startech_groove_passes():
    pts, ln = groove_passes(1784, 141.5, 0, 141.5, 10.5, 4)        # 10.5 mm paz, 4 mm arra → 4 o'tish
    assert ln == 1784 and [round(y, 3) for _x, y in pts] == [146.75, 143.75, 140.75, 140.25]


def test_run_cnc_project_zip(jobs):
    p, _f, _b = jobs
    name, data, mime = ppfmt.run_cnc_project("tpa", p)
    assert mime == "application/zip"
    assert sorted(zipfile.ZipFile(io.BytesIO(data)).namelist()) == ["999901_01_001.CNC", "999901_01_001_2.CNC"]


def test_arc_by_radius_expanded():
    """MillArc (R bilan) markazli yoyga aylantiriladi (namunada yo'q — barcha formatlarda yoy markazi bilan)."""
    prog = [c("MillStart", X=0, Y=0, DP=16, D=8, C=2), c("MillArc", X=100, Y=0, R=50, DIR="false")]
    op = Operation(type=OpType.XNC, code="R1", name="r", xnc=XNCParams(by_part_size=False, length=200, width=200,
                                                                         thickness=16, program=prog))
    p = Project(name="r", operations=[op])
    j = ppfmt.drill_job(p, op)
    _h, recs = XL.read_records(ppfmt.load_all()["xilog3"].fn(j)[0][1])
    assert recs[2] == "G3 X=100 Y=0 I=50 J=0"
    L = text(ppfmt.load_all()["tpa"].fn(j))
    assert "W#2101{ ::WTa  #1=100  #2=0 #34=0 #31=50 #32=0 }W" in L
