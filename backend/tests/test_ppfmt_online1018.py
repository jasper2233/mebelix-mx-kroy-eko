"""Onlayn tizim bilan parallel sinovdan (2026-10-18) topilgan farqlar — sun'iy XNC dasturlari bilan:
kodsiz XNC dasturi nomi («<loyiha> <nom>»), IMA mahsulot nomi lotincha va kodsiz BEZB bo'sh, TPA / BiesseWorks da
chuqurligi qalinlikka teng teshik (TPA — o'tuvchi, BiesseWorks — yo'q)."""
import io
import re
import zipfile

import pytest

from app.models import Operation, OpType, Part, Product, Project, XNCParams, XncCommand
from app.services import ppfmt


def c(kind, **p):
    return XncCommand(cmd=kind, params=p)


PROG = [c("DrillFront", X=100, Y=22, D=35, DP=16, T="Bore35"),      # chuqurlik = qalinlik
        c("DrillFront", X=200, Y=40, D=8, DP=19, T="BoreTh8"),      # qalinlikdan chuqur
        c("DrillFront", X=300, Y=40, D=5, DP=12, T="Bore5")]        # ko'r teshik


def make_project(code: str = "", name: str = " chap tomon"):
    xnc = Operation(type=OpType.XNC, code=code, name=name,
                    xnc=XNCParams(by_part_size=False, length=410, width=101, thickness=16, qty=1, face_side=True,
                                  program=PROG))
    prod = Product(name="Модель 7", code="7")
    part = Part(name=name, code="", length=410, width=101, qty=1, product_id=prod.id, xnc_op_ids=[xnc.id])
    cs = Operation(type=OpType.CS, code="LDSP16", name="LDSP 16", parts=[part])
    return Project(name="9001 sinov", operations=[cs, xnc], products=[prod]), xnc


def files_of(key: str, p: Project) -> dict[str, bytes]:
    _n, data, _m = ppfmt.run_cnc_project(key, p)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return {i.filename: z.read(i) for i in z.infolist()}


@pytest.fixture(scope="module", autouse=True)
def _load():
    ppfmt.load_all()


def test_nocode_program_named_project_plus_op_name():
    p, op = make_project()
    assert ppfmt.drill_job(p, op).code == "9001 sinov  chap tomon"
    assert list(files_of("xilog3", p)) == ["9001 sinov  chap tomon.pgm"]
    assert list(files_of("woodwop", p)) == ["9001 sinov  chap tomon.mpr"]
    # kodli dastur — kod; nomsiz va kodsiz — «xnc»
    p2, op2 = make_project(code="2608011")
    assert ppfmt.drill_job(p2, op2).code == "2608011"
    p3, op3 = make_project(name="")
    assert ppfmt.drill_job(p3, op3).code == "xnc"
    p4, op4 = make_project()
    p4.name = ""
    assert ppfmt.drill_job(p4, op4).code == " chap tomon"


def test_startech_comment_uses_same_name():
    p, _op = make_project()
    (_n, data), = files_of("scm_startech", p).items()
    assert ";9001 sinov  chap tomon" in data.decode("cp1251").split("\r\n")


def test_ima_product_transliterated_and_nocode_bezb_empty():
    p, _op = make_project()
    (name, data), = files_of("ima_wop", p).items()
    assert name == "9001 sinov  chap tomon.FMC"
    lines = data.decode("cp1251").split("\r\n")
    assert lines[:2] == ["[PGKOPF60]", "BEZB="]
    assert "BEZB=Modely7" in lines and "KOM=Modely7" in lines
    assert not any("Модель" in ln for ln in lines)
    p2, _ = make_project(code="2608011")
    (_n, d2), = files_of("ima_wop", p2).items()
    assert d2.decode("cp1251").split("\r\n")[1] == "BEZB=2608011"


def test_tpa_through_flag_includes_depth_equal_thickness():
    p, _op = make_project(code="X1")
    (_n, data), = files_of("tpa", p).items()
    flags = {m.group(1): m.group(2) for m in re.finditer(r"#1002=([\d.]+) #1001=(\d)", data.decode("cp1251"))}
    assert flags == {"35.0": "1", "8.0": "1", "5.0": "0"}


def test_biesseworks_through_flag_only_deeper_than_thickness():
    p, _op = make_project(code="X1")
    (_n, data), = files_of("biesseworks", p).items()
    rows = [ln for ln in data.decode("cp1251").split("\r\n") if ln.startswith("@ BG")]
    thr = {ln.split(",")[11].strip(): re.search(r'"", "", (\d), 0, 0, 0, 0, "", 0, 0, 0, 0, 0, "", "", "BG"$', ln).group(1)
           for ln in rows}
    assert thr == {"35": "0", "8": "1", "5": "0"}
