"""Ishlov markazi o'rnatilgan formatlari: Masterwood MW310 (.prg), umumiy «G CODE», AES Sirius (G-kod) — sun'iy XNC
dasturlari bilan. Namunalar bilan bayt-ma-bayt solishtirish — `tools/bench/pp_online_check_mw_gcode_aes.py`."""
import pytest

from app.models import Operation, OpType, Part, Project, XNCParams, XncCommand
from app.services import ppfmt
from app.services.ppfmt import aes_sirius as AES
from app.services.ppfmt import gcode_generic as GC
from app.services.ppfmt import tooling as TL

TOOLS = {TL.tool_key(k, p, d): str(i) for i, (k, p, d) in enumerate((
    ("drill", "front", 5), ("through", "front", 8), ("drill", "front", 8), ("drill", "left", 8), ("drill", "left", 4.5),
    ("drill", "right", 8), ("drill", "right", 4.5), ("drill", "top", 8), ("drill", "bottom", 8), ("mill", "front", 8)), 1)}


def c(kind, **p):
    return XncCommand(cmd=kind, params=p)


FACE = [
    c("DrillFront", X=100, Y=50, D=5, DP=12, T="Bore5"),
    c("DrillFront", X=8, Y=200, D=8, DP="dz+3", T="BoreTh8"),
    c("DrillLeft", Y=40, Z=8, M="true", D=8, DP=30, T="Bore8"),
    c("DrillRight", Y=120.5, Z=8, M="true", D=4.5, DP=32, T="Bore4.5"),
    c("DrillTop", X=100, Z=6, M="false", D=8, DP=30, T="Bore8"),
    c("DrillBottom", X=150, Z=8, M="true", D=8, DP=34, T="Bore8"),
    c("MillStart", X=550, Y=410, DP=16, D=8, C=1, T="Mill8"),
    c("MillLine", X=550, Y=350),
    c("MillArcCenter", X=560, Y=340, CX=560, CY=350, DIR="true"),
    c("MillLine", X=610, Y=340),
]
BACK = [
    c("DrillFront", X=50, Y=60, D=8, DP=11, T="Bore8"),
    c("DrillLeft", Y=40, Z=8, M="true", D=8, DP=30, T="Bore8"),
]
EDGE = [
    c("DrillLeft", Y=30, Z=9, M="true", D=8, DP=25, T="Bore8"),
    c("DrillRight", Y=90.5, Z=9, M="true", D=4.5, DP=32, T="Bore4.5"),
]


def xop(code, prog, l=600, w=400, t=16, face=True):
    return Operation(type=OpType.XNC, code=code, name="detal",
                     xnc=XNCParams(by_part_size=False, length=l, width=w, thickness=t, qty=1, face_side=face, program=prog))


def job_of(prog, code="P1", tools=TOOLS, **kw):
    op = xop(code, prog, **kw)
    j = ppfmt.drill_job(Project(name="Sinov", operations=[op]), op)
    j.params = dict(j.params, tools=dict(tools))
    return j


@pytest.fixture(scope="module")
def jobs():
    ppfmt.load_all()
    face, back = xop("999901_01_001", FACE), xop("999901_01_001_2", BACK, face=False)
    part = Part(name="detal", code="01_001", length=600, width=400, qty=1, xnc_op_ids=[face.id, back.id])
    p = Project(name="Sinov", operations=[Operation(type=OpType.CS, code="L16", name="LDSP 16", parts=[part]), face, back])
    res = []
    for o in (face, back):
        j = ppfmt.drill_job(p, o)
        j.params = dict(j.params, tools=dict(TOOLS))
        res.append(j)
    return p, res[0], res[1]


def run(key, job):
    files = ppfmt.load_all()[key].fn(job)
    assert len(files) == 1
    return files[0][0], files[0][1].decode("ascii")


def test_registered():
    reg = ppfmt.load_all()
    for k, ext in (("mw310", "prg"), ("gcode", ""), ("aes_sirius", "")):
        assert reg[k].group == "cnc" and reg[k].ext == ext and reg[k].note
    assert reg["gcode"].batch is not None


def test_no_foreign_name(jobs):
    _p, f, b = jobs
    for k in ("mw310", "gcode"):
        for j in (f, b):
            assert "giblab" not in run(k, j)[1].lower()
    assert "giblab" not in run("aes_sirius", job_of(EDGE, l=400, w=120, t=18))[1].lower()


# ───────────────────────── Masterwood MW310 ─────────────────────────
def test_mw310_face(jobs):
    _p, f, _b = jobs
    name, t = run("mw310", f)
    assert name == "999901_01_001.prg"
    assert t.split("\r\n") == [
        "%", "|1", "|2 0", "|3 1", "|4 600", "|5 16", "|6 400", "|7 0 0 0 0", "|8 0", "|9", "|10", "|11", "|12", "|13", "|14",
        ":1",
        "G100 X100 Y50 Z12 T1",
        "G100 X8 Y200 Z19 T2",                    # o'tuvchi teshik — «сквозное сверло»
        "G182 X30 Y360 Z8 T4",                    # chap qirra: X — chuqurlik, Y = en − y
        "G183 X32 Y279.5 Z8 T7",
        "G184 X100 Y30 Z6 T8",                    # y=0 qirra: Y — chuqurlik
        "G185 X150 Y34 Z8 T9",
        "G172 X550 Y410 Z16 S20 E10 T10", "G42", "G101 X550 Y410 Z16",
        "G101 X550  Y350", "G102 X560  Y340 I560 J350", "G101 X610  Y340",
        "G40", "G101 X610 Y340",
        "%", ""]


def test_mw310_back(jobs):
    _p, _f, b = jobs
    name, t = run("mw310", b)
    assert name == "999901_01_001_2.prg"
    L = t.split("\r\n")
    assert L[16:] == ["G100 X550 Y60 Z11 T3", "G183 X30 Y360 Z8 T6", "%", ""]      # X ag'darilgan, chap → o'ng


def test_mw310_tools_required():
    with pytest.raises(ValueError, match="не указан инструмент"):
        run("mw310", job_of(FACE, tools={}))
    part = {k: v for k, v in TOOLS.items() if not k.startswith("mill")}
    with pytest.raises(ValueError, match="фреза"):
        run("mw310", job_of(FACE, tools=part))
    # o'tuvchi parma qatori bo'sh — oddiy parma raqami; u ham bo'lmasa — xato
    prog = [c("DrillFront", X=10, Y=10, D=8, DP=16, T="BoreTh8")]
    assert "G100 X10 Y10 Z16 T3" in run("mw310", job_of(prog, tools={"drill:front:8": "3"}))[1]
    with pytest.raises(ValueError, match="сквозное сверло"):
        run("mw310", job_of(prog, tools={"drill:front:5": "1"}))


def test_mw310_plain_contour_groove_and_empty():
    prog = [c("MillStart", X=-5, Y=100, DP=8, D=8, C=0, T="Mill8"), c("MillLine", X=305, Y=100)]
    L = run("mw310", job_of(prog, l=300, w=200))[1].split("\r\n")
    assert L[16:] == ["G172 X-5 Y100 Z8 S20 E10 T10", "G101 X-5 Y100 Z8", "G101 X305  Y100", "%", ""]   # korreksiyasiz
    prog[0] = c("MillStart", X=-5, Y=100, DP=8, D=8, C=2, T="Mill8")
    assert "G41" in run("mw310", job_of(prog, l=300, w=200))[1].split("\r\n")
    with pytest.raises(ValueError, match="паз"):
        run("mw310", job_of([c("Groove", X1=0, Y1=50, X2=300, Y2=50, DP=8, W=4, D=4, T="Cut4")], l=300, w=200))
    assert run("mw310", job_of([], l=300, w=200))[1].endswith("|14\r\n:1\r\n%\r\n")


def test_mw310_project_pack(jobs, monkeypatch):
    p, f, b = jobs
    monkeypatch.setattr(ppfmt, "drill_job", lambda _p, o, *_a, **_k: f if o.id == f.op.id else b)
    name, data, mime = ppfmt.run_cnc_project("mw310", p)
    assert name.endswith(".zip") and mime == "application/zip" and data[:2] == b"PK"


# ───────────────────────── G CODE ─────────────────────────
def test_gcode_face(jobs):
    _p, f, _b = jobs
    name, t = run("gcode", f)
    assert name == "999901_01_001" and not t.endswith("\n")
    assert t.split("\r\n") == [
        "N10 (generated code in MebeliX Kroy)", "N20 G90",
        "N30 (5MM Bore5)", "N40 M06", "N50 S3000 M04", "N60 X100 Y50 Z-12", "N70 G80", "N80 M05",
        "N90 (8MM BoreTh8)", "N100 M06", "N110 S3000 M04", "N120 X8 Y200 Z-19", "N130 G80", "N140 M05",   # qirra teshiklari yo'q
        "N150 (8MM Mill8)", "N160 M06", "N170 S3000 M04", "N180 G0 X550 Y410 Z20", "N190 G0 G41 X550 Y410",
        "N200 Z-16 F100", "N210 G1 Y350 Z-16", "N220 G3 X560 Y340 I10 J0", "N230 G1 X610", "N240 G0 Z20", "N250 M05",
        "N260 M30"]


def test_gcode_batch_state(jobs):
    p, f, b = jobs
    files = ppfmt.load_all()["gcode"].batch([b, b, f, f], p)
    assert [nm for nm, _d in files] == ["999901_01_001_2", "999901_01_001_2(1)", "999901_01_001", "999901_01_001(1)"]
    t = [d.decode("ascii").split("\r\n") for _n, d in files]
    assert t[0] == ["N10 (generated code in MebeliX Kroy)", "N20 G90", "N30 (8MM Bore8)", "N40 M06", "N50 S3000 M04",
                    "N60 X550 Y60 Z-11", "N70 M05", "N80 M30"]                    # orqa tomon: X ag'darilgan
    assert t[1][2] == "N30 G80" and t[1][3:6] == ["N40 (8MM Bore8)", "N50 M06", "N60 S3000 M04"]   # oldingi fayl sikli
    assert t[2][2] == "N30 G80" and "N220 G1 Y350 Z-16" in t[2]
    assert t[3][2] == "N30 (5MM Bore5)" and "N210 G1 Y350" in t[3]                # freza Z — oldingi fayldan
    # yakka dastur — holat toza
    assert run("gcode", b)[1].split("\r\n") == t[0]


def test_gcode_groups_mirror_and_errors():
    prog = [c("DrillFront", X=10, Y=10, D=8, DP=10, T="Bore8"), c("DrillTop", X=50, Z=8, M="true", D=8, DP=30, T="Bore8"),
            c("DrillFront", X=20, Y=10, D=8, DP=10, T="Bore8"), c("DrillFront", X=30, Y=10, D=8, DP=19, T="BoreTh8")]
    L = run("gcode", job_of(prog, l=300, w=200))[1].split("\r\n")
    assert L[2:] == ["N30 (8MM Bore8)", "N40 M06", "N50 S3000 M04", "N60 X10 Y10 Z-10", "N70 X20 Y10 Z-10", "N80 G80", "N90 M05",
                     "N100 (8MM BoreTh8)", "N110 M06", "N120 S3000 M04", "N130 X30 Y10 Z-19", "N140 M05", "N150 M30"]
    assert run("gcode", job_of([c("DrillLeft", Y=40, Z=8, M="true", D=8, DP=30)], l=300, w=200))[1] == \
        "N10 (generated code in MebeliX Kroy)\r\nN20 G90\r\nN30 M30"
    # orqa tomon frezasi: X ag'dariladi, yoy yo'nalishi va korreksiya teskari
    mill = [c("MillStart", X=250, Y=210, DP=16, D=8, C=1, T="Mill8"), c("MillLine", X=250, Y=150),
            c("MillArcCenter", X=260, Y=140, CX=260, CY=150, DIR="true"), c("MillLine", X=310, Y=140)]
    L = run("gcode", job_of(mill, l=300, w=200, face=False))[1].split("\r\n")
    assert L[5:11] == ["N60 G0 X50 Y210 Z20", "N70 G0 G42 X50 Y210", "N80 Z-16 F100", "N90 G1 Y150 Z-16",
                       "N100 G2 X40 Y140 I-10 J0", "N110 G1 X-10"]
    with pytest.raises(ValueError, match="паз"):
        run("gcode", job_of([c("Groove", X1=0, Y1=50, X2=300, Y2=50, DP=8, W=4, D=4, T="Cut4")], l=300, w=200))
    assert GC.dup_names(["a", "b", "a", "a"]) == ["a", "b", "a(1)", "a(2)"]


# ───────────────────────── AES Sirius ─────────────────────────
def test_aes_edge_holes():
    name, t = run("aes_sirius", job_of(EDGE, code="E1", l=400, w=120, t=18))
    assert name == "E1"
    assert t.split("\r\n") == [
        "{           400              }",
        "{     ++++++++++++++++   1   }",
        "{     ################   2   }",
        "{     ################   0   }",
        "{   O                        }",
        "{                            }",
        "(R170=400) { LENGTH", "(R169=120) { WIDTH", "(R173=200) { PUSHER POSITION", "L M7", "M12",
        # avval o'ng qirra (XNC) — stanokda X = 0 tomoni
        "M85", "M87", "M06T7", "M16", "G0 Z30.0", "G0 X-20.0 Y90.5", "M7", "G0 Z-9.0", "G1 X32.0 F2000", "G0 X-20.0",
        "G0 Z30.0",
        "M85", "M87", "M06T4", "M16", "G0 Z30.0", "G0 X420.0 Y30.0", "M4", "G0 Z-9.0", "G1 X375.0 F2000", "G0 X420.0",
        "G0 Z30.0",
        "M85", "M88", "L GFINPRO.ISC", "M02", ""]


def test_aes_picture_and_numbers():
    rows = AES.picture(1768, 57.5)
    assert all(len(r) == 30 for r in rows) and rows[0] == "{           1768             }"
    assert [r[25] for r in rows[1:5]] == ["5", "7", ".", "5"] and rows[1][6] == "+" and rows[2][6] == "#"
    assert AES.f1(30) == "30.0" and AES.f1(120.5) == "120.5" and AES.f1(-8) == "-8.0"
    t = run("aes_sirius", job_of([], l=337, w=100))[1]
    assert "(R173=168.5) { PUSHER POSITION\r\nL M7\r\nM12\r\nM85\r\nM88\r\nL GFINPRO.ISC\r\nM02\r\n" in t


def test_aes_unsupported_and_tools():
    with pytest.raises(ValueError, match="не указан инструмент"):
        run("aes_sirius", job_of(EDGE, tools={}, l=400, w=120))
    for prog, msg in (([c("DrillFront", X=10, Y=10, D=8, DP=10)], "пласть"),
                      ([c("DrillTop", X=50, Z=8, M="true", D=8, DP=30)], "торец"),
                      ([c("Groove", X1=0, Y1=50, X2=300, Y2=50, DP=8, W=4, D=4)], "паз"),
                      ([c("MillStart", X=-5, Y=100, DP=8, D=8, C=1), c("MillLine", X=305, Y=100)], "фрезерование")):
        with pytest.raises(ValueError, match=msg):
            run("aes_sirius", job_of(prog, l=300, w=200))
    # FormatError — foydalanuvchiga 400 xabar
    op = xop("X", [c("DrillFront", X=10, Y=10, D=8, DP=10)], l=300, w=200)
    with pytest.raises(ppfmt.FormatError, match="AES Sirius"):
        ppfmt.run_cnc("aes_sirius", Project(name="x", operations=[op]), op)
