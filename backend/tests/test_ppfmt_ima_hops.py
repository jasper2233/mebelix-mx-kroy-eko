"""Ishlov markazi o'rnatilgan formatlari: IMA ImaWop (.FMC) va Holz-Her NC-HOPS (.hop) — sun'iy XNC dasturlari bilan
(yuz / qirra teshigi, freza chiziq + yoy, orqa tomon, kromka, asboblar jadvali). Namunalar bilan bayt-ma-bayt solishtirish —
`tools/bench/pp_online_check_ima_hops.py`."""
import pytest

from app.models import EdgeRef, ELParams, Operation, OpType, Part, Product, Project, XNCParams, XncCommand
from app.services import ppfmt
from app.services.ppfmt import holzher_nchops as HH
from app.services.ppfmt import ima_wop as IM


def c(kind, **p):
    return XncCommand(cmd=kind, params=p)


FACE = [
    c("DrillLeft", Y=40, Z=8, M="true", D=8, DP=30, T="Bore8"),
    c("DrillRight", Y=120.5, Z=8, M="true", D=4.5, DP=32, T="Bore4.5"),
    c("DrillTop", X=100, Z=8, M="true", D=8, DP=30, T="Bore8"),
    c("DrillBottom", X=150, Z=8, M="true", D=8, DP=34, T="Bore8"),
    c("DrillFront", X=100, Y=50, D=5, DP=12, T="Bore5"),
    c("DrillFront", X=300.126, Y=200, D=15, DP=12.5, T="Bore15"),
    c("MillStart", X=550, Y=410, DP=16, D=8, C=1, T="Mill8"),
    c("MillLine", X=550, Y=350),
    c("MillArcCenter", X=560, Y=340, CX=560, CY=350, DIR="true"),
    c("MillLine", X=610, Y=340),
]
BACK = [c("DrillFront", X=50, Y=60, D=8, DP=11, T="Bore8")]
GROOVE = [c("Groove", X1=0, Y1=350, X2=600, Y2=350, DP=8, W=4, D=4, T="Cut4")]


def make_project():
    el = Operation(type=OpType.EL, code="PVC", name="PVC 1x19", el=ELParams(width=19, thickness=1, symbol="A", color="#D2691E"))

    def xnc(code, prog, face=True):
        return Operation(type=OpType.XNC, code=code, name="01_001 bok chap",
                         xnc=XNCParams(by_part_size=False, length=600, width=400, thickness=16, qty=3, face_side=face,
                                       program=prog))
    face, back, gr = xnc("999901_01_001", FACE), xnc("999901_01_001_2", BACK, False), xnc("999901_01_002", GROOVE)
    prod = Product(name="Shkaf 02", code="01")
    part = Part(name="01_001 bok chap", code="01_001", length=600, width=400, qty=3, product_id=prod.id,
                edge_top=EdgeRef(op_id=el.id), edge_left=EdgeRef(op_id=el.id), xnc_op_ids=[face.id, back.id])
    cs = Operation(type=OpType.CS, code="LDSP16", name="LDSP 16", parts=[part])
    return Project(name="9001_sinov", operations=[cs, el, face, back, gr], products=[prod]), face, back, gr


def job_of(p, op, tools=None):
    j = ppfmt.drill_job(p, op)
    j.params = {"tools": dict(tools or {})}
    return j


@pytest.fixture(scope="module")
def prj():
    ppfmt.load_all()
    return make_project()


def blocks(text):
    """FMC → [(blok nomi, {kalit: qiymat})] (tartibda)."""
    res = []
    for ln in text.split("\r\n"):
        if ln.startswith("["):
            res.append((ln, {}))
        elif ln:
            k, _, v = ln.partition("=")
            res[-1][1][k] = v
    return res


# ───────────────────────── registratsiya ─────────────────────────
def test_registered():
    reg = ppfmt.load_all()
    assert reg["ima_wop"].group == "cnc" and reg["ima_wop"].ext == "FMC"
    assert reg["holzher_nchops"].group == "cnc" and reg["holzher_nchops"].ext == "hop"


# ───────────────────────── IMA ImaWop ─────────────────────────
def test_ima_header_and_drills(prj):
    p, face, _b, _g = prj
    (name, data), = ppfmt.load_all()["ima_wop"].fn(job_of(p, face, {"mill:front:8": "MILL8"}))
    assert name == "999901_01_001.FMC"
    text = data.decode("cp1251")
    assert text.endswith("\r\n") and "\n\n" not in text.replace("\r\n", "\n")
    b = blocks(text)
    assert [x[0] for x in b[:3]] == ["[PGKOPF60]", "[PRODUZ60]", "[BOHRPO60]"]
    assert b[0][1] == {"BEZB": "999901_01_001", "FTL": "600", "FTB": "400", "FTD": "16", "KOM1": "01_001bokchap", "KOM2": ""}
    assert b[1][1]["BEZB"] == "Shkaf02" and b[1][1]["KOM"] == "Shkaf02" and b[1][1]["STZ"] == "3" and b[1][1]["KAF"] == " "
    # qirra teshiklari: x=0 → HBXPLU, x=dx → HBXMIN, y=0 → HBYPLU, y=dy → HBYMIN; dastur tartibida
    assert [x[0] for x in b[3:9]] == ["[HBXPLU60]", "[HBXMIN60]", "[HBYPLU60]", "[HBYMIN60]", "[VBDMES60]", "[VBDMES60]"]
    assert b[3][1] == {"DM": "8", "TI": "30", "Y1": "40", "GRP": "1", "Z": "8", "BEZB": "Horizontal drilling X", "AFB": "1"}
    assert b[4][1]["Y1"] == "120.5" and b[4][1]["DM"] == "4.5"
    assert b[5][1]["X1"] == "100" and b[5][1]["BEZB"] == "Horizontal drilling Y"
    assert b[8][1] == {"BEZB": "Vertical drilling", "DM": "15", "TI": "12.5", "X": "300.13", "Y": "200", "GRP": "1",
                       "AFB": "1", "PKTBEZUG_XY": "0"}
    assert "GibLab" not in text


def test_ima_mill_contour(prj):
    p, face, _b, _g = prj
    text = IM.program(job_of(p, face, {"mill:front:8": "MILL8"}))
    b = blocks(text)
    names = [x[0] for x in b]
    i = names.index("[KDEFANFC]")
    assert names[i:i + 12] == ["[KDEFANFC]", "[G1]", "[G3]", "[G1]", "[KDEFENDE]", "[KTFRAE60]", "[[KAFRAE60]]", "[[G1]]",
                               "[[G3]]", "[[G1]]", "[[KDEFENDE]]", "[PRODBLOCK]"]
    assert b[i][1]["KNAME"] == "Kontur1" and b[i][1]["X"] == "550" and b[i][1]["Y"] == "410" and b[i][1]["TH"] == "-10"
    arc = b[i + 2][1]
    assert arc == {"BEZB": "Arc", "AFB": "1", "EB": "0", "PKTBEZUG_XY": "0", "MPX": "560", "MPY": "350", "RAD": "10",
                   "X": "560", "Y": "340", "Z": "0"}
    assert b[i + 5][1]["SWKZID"] == IM.MILL_SWKZID and b[i + 5][1]["TRKOR"] == "1" and b[i + 5][1]["KNAME"] == "Kontur1"
    assert b[i + 6][1]["BEZB"] == "Call mill" and b[i + 6][1]["X"] == "550"
    assert b[i + 8][1] == arc                                       # ichki ro'yxat — o'sha elementlar


def test_ima_mpy_sample_mode(prj, monkeypatch):
    p, face, _b, _g = prj
    monkeypatch.setattr(IM, "MPY_AS_SAMPLE", True)
    arcs = [d for nm, d in blocks(IM.program(job_of(p, face, {"mill:front:8": "MILL8"}))) if nm in ("[G3]", "[[G3]]")]
    assert arcs and all(d["MPY"] == d["MPX"] == "560" for d in arcs)


def test_ima_edges(prj):
    p, face, back, _g = prj
    b = blocks(IM.program(job_of(p, face, {"mill:front:8": "MILL8"})))
    i = [k for k, x in enumerate(b) if x[0] == "[PRODBLOCK]"]
    assert len(i) == 2 and b[i[0]][1] == {"PRODSTATUS": "1", "BEZ": "EDGEBEND-PVC 1x19"}
    top = b[i[0] + 1:i[1]]
    assert top[0][0] == "[[KDEFANFC]]" and top[0][1]["JUS"] == "21" and (top[0][1]["X"], top[0][1]["Y"]) == ("300", "-20")
    assert [(d["X"], d["Y"]) for nm, d in top[1:6]] == [("600", "-20"), ("600", "-25"), ("0", "-25"), ("0", "-20"), ("300", "-20")]
    assert "BEZB" not in top[1][1] and top[6][0] == "[[KDEFENDE]]"
    left = b[i[1] + 1:]
    assert left[0][1]["JUS"] == "12" and (left[0][1]["X"], left[0][1]["Y"]) == ("-20", "200")
    assert [(d["X"], d["Y"]) for nm, d in left[1:6]] == [("-20", "400"), ("-25", "400"), ("-25", "0"), ("-20", "0"), ("-20", "200")]
    # orqa tomon: X ag'darilgan, chap kromka o'ngda
    bb = blocks(IM.program(job_of(p, back)))
    assert [x for x in bb if x[0] == "[VBDMES60]"][0][1]["X"] == "550"
    st = [d for nm, d in bb if nm == "[[KDEFANFC]]"]
    assert [d["JUS"] for d in st] == ["21", "10"] and st[1]["X"] == "620"


def test_ima_tool_and_groove_errors(prj):
    p, face, _b, gr = prj
    with pytest.raises(ValueError, match="фреза"):
        IM.program(job_of(p, face))
    with pytest.raises(ValueError, match="паз"):
        IM.program(job_of(p, gr))


# ───────────────────────── Holz-Her NC-HOPS ─────────────────────────
HOP_HEAD = [";KOMMENTAR=", ";DX=0.000", ";DY=0.000", ";DZ=0", ";DIALOGDLL=Dialoge.Dll", ";DIALOGPROC=StandardFormAnzeigen",
            ";AUTOSCRIPTSTART=1", ";BUTTONBILD=", ";DIMENSION_UNIT=0", "VARS", "   DX := 600;*VAR*Dimension X",
            "   DY := 400;*VAR*Dimension Y", "   DZ := 16;*VAR*Dimension Z", "START",
            "FinishedPart (DX,DY,DZ,0,0,0,0,0,'',0,0,0)", "CALL HH_Park ( VAL PARK:=3,X:=0,Y:=0)"]


def test_hop_program(prj):
    p, face, _b, _g = prj
    (name, data), = ppfmt.load_all()["holzher_nchops"].fn(job_of(p, face, {"mill:front:8": "8", "drill:front:5": "-1"}))
    assert name == "999901_01_001.hop"
    text = data.decode("cp1251")
    assert text.endswith("\r\n") and "GibLab" not in text
    ln = text.split("\r\n")[:-1]
    assert ln[:16] == HOP_HEAD
    assert ln[16:] == [
        "TOOLD (501,_VE,_V,_VA,_SD,_ANF,'')",
        "HORD (0,360,8,8,-30,10,0,0,0,2,0,0)",
        "HORD (600,279.5,8,4.5,-32,10,0,180,0,2,0,0)",
        "HORD (100,400,8,8,-30,10,0,270,0,2,0,0)",                 # DrillTop (y=0) → Y=DY
        "HORD (150,0,8,8,-34,10,0,90,0,2,0,0)",
        "DRILLING (100,350,5,-12,10,0,0,1,0,0,0,0)",
        "DRILLING (300.126,200,15,-12.5,10,0,0,1,0,0,0,0)",
        "TOOLM (8,_VE,_V,_VA,_SD,0,'')",
        "SP (550,-10,-16,1,0,_ANF,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)",
        "G01 (550,50,-16,0,0,0)",
        "G03C (560,60,-16,560,50,0,0,0,0)",
        "G01 (610,60,-16,0,0,0)",
        "EP (0,_ANF,0)",
    ]


def test_hop_tb_sample_mode(prj, monkeypatch):
    p, face, _b, _g = prj
    monkeypatch.setattr(HH, "TB_AS_SAMPLE", True)
    ln = HH.lines(job_of(p, face, {"mill:front:8": "8"}))
    assert ln[3] == "HORD (100,0,8,8,-30,10,0,90,0,2,0,0)" and ln[4] == "HORD (150,400,8,8,-34,10,0,270,0,2,0,0)"


def test_hop_drill_tool_numbers(prj):
    p, face, back, _g = prj
    ln = HH.lines(job_of(p, face, {"mill:front:8": "8", "drill:front:15": "12", "drill:left:8": "21"}))
    assert ln[0] == "TOOLD (21,_VE,_V,_VA,_SD,_ANF,'')" and ln[2] == "TOOLD (501,_VE,_V,_VA,_SD,_ANF,'')"
    i = ln.index("TOOLD (12,_VE,_V,_VA,_SD,_ANF,'')")
    assert ln[i + 1].startswith("DRILLING (300.126,") and ln[i - 1].startswith("DRILLING (100,")
    # orqa tomon: X ag'darilgan, Y teskari
    assert HH.lines(job_of(p, back)) == ["TOOLD (501,_VE,_V,_VA,_SD,_ANF,'')", "DRILLING (550,340,8,-11,10,0,0,1,0,0,0,0)"]


@pytest.mark.parametrize("tools", [{}, {"mill:front:8": "-1"}, {"mill:front:8": "abc"}])
def test_hop_mill_tool_required(prj, tools):
    p, face, _b, _g = prj
    with pytest.raises(ValueError, match="инструмент"):
        HH.program(job_of(p, face, tools))


def test_hop_groove_error(prj):
    p, _f, _b, gr = prj
    with pytest.raises(ValueError, match="паз"):
        HH.program(job_of(p, gr))


# ───────────────────────── paket ─────────────────────────
def test_project_run_wraps_errors(prj):
    p, face, back, gr = prj
    with pytest.raises(ppfmt.FormatError):                       # asboblar jadvali bo'sh → freza uchun xato
        ppfmt.run_cnc("holzher_nchops", p, face)
    name, data, _mime = ppfmt.run_cnc("ima_wop", p, back)
    assert name == "999901_01_001_2.FMC" and data.startswith(b"[PGKOPF60]\r\n")
