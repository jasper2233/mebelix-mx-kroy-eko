"""KDT — korxonada stanokda HOZIR ishlayotgan fayllar (2026-10-26): arra `kdt_presize_xml` (v2) va prisadka `kdt_panel`
(`KDTPanelFormat`). Qoidalar korxonaning 10 buyurtmasidagi real fayllardan olingan (solishtiruv vositasi —
`tools/bench/pp_kdt_real.py`, korxona fayllari repoga kirmaydi); bu yerda — sun'iy ish bilan."""
from __future__ import annotations

import io
import re
import zipfile

from app.models import EdgeRef, ELParams, Operation, OpType, Part, Product, Project, XNCParams, XncCommand
from app.services import ppfmt
from test_ppfmt_saw_giben import _job, _map, _run, _strip_doc, _unzip


def c(kind, **p):
    return XncCommand(cmd=kind, params=p)


# ---------------------------------------------------------------- arra (v2)

def test_kdt_xml_v2_layout_and_print_codes():
    job = _job([_map([_strip_doc()])])
    job.project_name = "9001 Акрил"
    name, data = _run("kdt_presize_xml", job)
    inner = dict(_unzip(data))
    xml_name = next(n for n in inner if n.endswith(".xml"))
    folder = xml_name.split("/")[0]
    assert xml_name == f"{folder}/{folder}.xml" and folder.startswith("9001 Akril ")      # lotin, probellar saqlanadi
    txt = inner[xml_name].decode("utf-8")
    assert "\n" not in txt and txt.startswith('<?xml version="1.0" encoding="UTF-8"?><project><panel1 code=')
    # atributlar alifbo tartibida, bo'sh tugun — `/>`
    for tag in re.findall(r"<(?:panel\d+|no\.\d+|part) [^>]*>", txt):
        keys = re.findall(r' (\w+)="', tag)
        assert keys == sorted(keys), tag
    assert re.search(r'<no\.\d+ [^>]*/>', txt)
    # print_code: detalning operatsiyadagi tartib raqami, qoldiq — O1
    assert re.search(r'code="2" cut="600" id="\d+" print_code="2" type="1"', txt)
    assert 'print_code="O1" type="3"' in txt
    # 3-qatlam konteyneri: siljish = (torsovka + propil) / 2, bola shuncha suriladi
    m = re.search(r'<no\.\d+ id="\d+" l="(\d+)" layer="3" trim="2.5" w="400" x="1011" y="5">', txt)
    assert m and re.search(r'layer="4" trim="0" w="600" x="1011" y="7.5"', txt)
    # etiketkalar: har detal va qoldiq — 640×480 PNG
    for n in (f"{folder}/1.emf", f"{folder}/2.emf", f"{folder}/O1.emf"):
        png = inner[n]
        assert png[:4] == b"\x89PNG" and png[16:24] == (640).to_bytes(4, "big") + (480).to_bytes(4, "big")


def test_kdt_xml_v2_children_in_map_order_and_inner_remnant():
    """Bo'laklar — kartadagi joylashuv tartibida (real fayllardan tiklangan 32 kroyning hammasida); polosa oxiridagi деловой
    qoldiq ham `type="3"` bilan yoziladi va etiketkasi chiqadi."""
    from app.services.ppfmt import SawNode
    strip = SawNode(x=5, y=5, l=377, w=1820, kind="C", axis="y", children=[
        SawNode(x=5, y=5, l=377, w=686, kind="P", uid=1),
        SawNode(x=5, y=694, l=377, w=80, kind="C", axis="x", children=[SawNode(x=5, y=694, l=348, w=80, kind="P", uid=2)]),
        SawNode(x=5, y=777, l=377, w=450, kind="C", axis="x", children=[SawNode(x=5, y=777, l=347, w=450, kind="P", uid=2)]),
        SawNode(x=5, y=1230, l=377, w=595, kind="W", rem=1)])
    inner = dict(_unzip(_run("kdt_presize_xml", _job([_map([strip], rem=False)]))[1]))
    xml = next(d for n, d in inner.items() if n.endswith(".xml")).decode()
    no2 = re.search(r'<no\.\d+ [^>]*layer="2"[^>]*>(.*?)</no', xml).group(1)
    assert [int(x) for x in re.findall(r'cut="(\d+)"', no2)] == [686, 80, 450, 595]
    assert 'cut="595" id="' in no2 and 'print_code="O1" type="3"' in no2
    assert '<part code="O1" l="377" ' in xml and any(n.endswith("/O1.emf") for n in inner)


def test_kdt_xml_v1_kept():
    name, data = _run("kdt_presize_xml_v1", _job())
    assert name.endswith(".zip") and _unzip(data)[0][0].endswith(".xml")


# ---------------------------------------------------------------- prisadka (KDTPanelFormat)

FACE = [c("DrillFront", X=100, Y=50, D=5, DP=9, T="Bore5"),
        c("DrillFront", X=8, Y=200, D=8, DP="dz+3", T="BoreTh8"),
        c("DrillLeft", Y=40, Z=8, M="true", D=8, DP=30, T="Bore8"),
        c("DrillLeft", Y=300, Z=8, M="true", D=8, DP=30, T="Bore8"),
        c("DrillRight", Y=120, Z=8, M="true", D=8, DP=30, T="Bore8"),
        c("DrillRight", Y=320, Z=8, M="true", D=8, DP=30, T="Bore8"),
        c("MillStart", X=550, Y=410, DP=16, D=8, C=1, T="Mill8"), c("MillLine", X=550, Y=350),
        c("MillArcCenter", X=560, Y=340, CX=560, CY=350, DIR="true"), c("MillLine", X=610, Y=340)]
BACK_HOLES = [c("DrillFront", X=592, Y=70, D=8, DP=11, T="Bore8"), c("DrillFront", X=592, Y=330, D=8, DP=11, T="Bore8")]


def make_project(face_prog, back_prog, face_code="999901_01_001", back_code="999901_01_001_2"):
    el = Operation(type=OpType.EL, code="PVC", name="PVC 1x19", el=ELParams(width=19, thickness=1, symbol="B", color="#D2691E"))
    face = Operation(type=OpType.XNC, code=face_code, name="01_001 bok",
                     xnc=XNCParams(by_part_size=False, length=600, width=400, thickness=16, qty=1, program=face_prog))
    ops = [face]
    if back_prog is not None:
        ops.append(Operation(type=OpType.XNC, code=back_code, name="01_001 bok",
                             xnc=XNCParams(by_part_size=False, length=600, width=400, thickness=16, qty=1, face_side=False,
                                           program=back_prog)))
    prod = Product(name="Shkaf", code="01")
    part = Part(name="01_001 bok", code="01_001", length=600, width=400, qty=1, product_id=prod.id,
                edge_bottom=EdgeRef(op_id=el.id), xnc_op_ids=[o.id for o in ops])
    cs = Operation(type=OpType.CS, code="LDSP16", name="LDSP 16", parts=[part])
    return Project(name="9999 sinov", operations=[cs, el, *ops], products=[prod]), ops


def _files(p, ops):
    fmt = ppfmt.load_all()["kdt_panel"]
    return fmt.batch([ppfmt.drill_job(p, o) for o in ops], p)


def cads(txt: str) -> list[str]:
    return re.findall(r"<CAD>\r\n(.*?)</CAD>", txt, re.S)


def test_kdt_panel_one_file_per_part_with_back_holes():
    p, ops = make_project(FACE, BACK_HOLES)
    files = _files(p, ops)
    assert [n for n, _ in files] == ["999901_01_001.xml"]                 # orqa dastur alohida fayl emas
    txt = files[0][1].decode()
    assert txt.startswith('<?xml version="1.0" encoding="UTF-8"?>\r\n<KDTPanelFormat>\r\n<PANEL>') and txt.endswith("</KDTPanelFormat>\r\n")
    # kontur: past tomon (dasturdagi y = en) kromkali — 1.5, «(B) 1mm», rang; qolganlari 0.3 / «-»
    v = re.findall(r"<Vertex>\r\n(.*?)</Vertex>", txt, re.S)
    assert "<Banding>1.5</Banding>" in v[0] and "<Description>(B) 1mm</Description>" in v[0] and "rgb(210,105,30)" in v[0]
    assert all("<Banding>0.3</Banding>" in x and "rgb(200, 200, 200)" in x for x in v[1:])
    cs = cads(txt)
    # yuza teshigi: X dasturdagidek, Y pastdan (400 − 50)
    assert any("<TypeNo>1</TypeNo>" in x and "<X1>100</X1>" in x and "<Y1>350</Y1>" in x for x in cs)
    # orqa teshiklar — 8, X o'zgarishsiz, Y pastdan
    back = [x for x in cs if "<TypeNo>8</TypeNo>" in x]
    assert len(back) == 2 and any("<X1>592</X1>" in x and "<Y1>330</Y1>" in x for x in back)
    # freza — Path: nuqtalar Y pastdan, korreksiya 1 → 2, yoy (soat strelkasiga qarshi) → Direction 0
    path = next(x for x in cs if "<TypeNo>7</TypeNo>" in x)
    assert "<Correction>2</Correction>" in path and "<X1>550</X1>\r\n<Y1>-10</Y1>" in path and "<Direction>0</Direction>" in path
    # qirra teshiklari oxirida: chap (Y o'sishi), keyin o'ng (Y kamayishi)
    edge = [x for x in cs if "<TypeNo>2</TypeNo>" in x]
    assert cs[-len(edge):] == edge
    q = [(re.search(r"<Quadrant>(\d)", x).group(1), float(re.search(r"<Y1>([\d.]+)", x).group(1))) for x in edge]
    assert q == [("1", 100.0), ("1", 360.0), ("2", 280.0), ("2", 80.0)]


def test_kdt_panel_nearest_first_route():
    prog = [c("DrillFront", X=500, Y=350, D=5, DP=9, T="Bore5"), c("DrillFront", X=20, Y=380, D=5, DP=9, T="Bore5"),
            c("DrillFront", X=300, Y=200, D=5, DP=9, T="Bore5")]
    p, ops = make_project(prog, None)
    xs = [float(x) for x in re.findall(r"<X1>([\d.]+)</X1>", "".join(cads(_files(p, ops)[0][1].decode())))]
    assert xs == [20, 300, 500]                                              # boshdan (0,0): (20,20) → (300,200) → (500,50)


def test_kdt_panel_flipped_when_back_has_groove():
    """Orqa dasturda paz (yuzda freza / paz yo'q) — detal ag'dariladi: orqa dastur asosiy, hamma X ko'zgu."""
    face = [c("DrillFront", X=8, Y=70, D=8, DP=11, T="Bore8"), c("DrillFront", X=86, Y=8, D=8, DP="dz+3", T="BoreTh8")]
    back = [c("DrillFront", X=592, Y=70, D=8, DP=11, T="Bore8"),
            c("Groove", X1=592, Y1=0, X2=0, Y2=0, DP=8, W=6, D=4, T="Cut4")]
    p, ops = make_project(face, back)
    cs = cads(_files(p, ops)[0][1].decode())
    groove = next(x for x in cs if "<TypeNo>3</TypeNo>" in x)
    assert "<BeginX>8</BeginX>" in groove and "<EndX>600</EndX>" in groove and "<BeginY>400</BeginY>" in groove
    t1 = [x for x in cs if "<TypeNo>1</TypeNo>" in x]
    assert any("<X1>8</X1>" in x and "<Y1>330</Y1>" in x for x in t1)       # orqa teshik: 600 − 592
    assert any("<X1>514</X1>" in x and "<Y1>392</Y1>" in x for x in t1)     # yuzdagi teshib o'tuvchi — asosiy tomonda
    t8 = [x for x in cs if "<TypeNo>8</TypeNo>" in x]
    assert len(t8) == 1 and "<X1>592</X1>" in t8[0]                          # yuzdagi ko'r teshik — 8 (600 − 8)


def test_kdt_panel_name_without_code_and_label_qr():
    p, ops = make_project(FACE, None, face_code="")
    assert [n for n, _ in _files(p, ops)] == ["01_001 bok_null_1.xml"]
    # arra etiketkasidagi QR — shu nom (stanok etiketkani skanerlab dasturni ochadi)
    cs = p.operations[0]
    from app.services.ppfmt import saw_job
    part = saw_job(p, cs).parts[0]
    assert part.xnc_file == "01_001 bok_null_1"
