"""Arra postprotsessorlari: Nanxing .CUT (nanxing_nxcutsaw), Nanxing .ncp (nanxing_cutsaw / nanxing_cutsawfg),
AES Alpha .ss (aes_alpha / aess_alpha), FastPanel .ocm (fastpanel). Formatlar — docs/mebelix/postprocessors/*.md.
Hamma ma'lumot shu faylda sun'iy quriladi (korxona fayllari ishlatilmaydi). Korpus bilan solishtirish —
tools/bench/pp_saw_check_nanxing.py."""
from __future__ import annotations

import io
import struct
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime

import pytest

from app.models import (CSCutParams, CSMaterialParams, EdgeRef, ELParams, OpType, Operation, Part, Product, Project,
                        StockSheet, XncCommand, XNCParams)
from app.services import ppfmt
from app.services.calc import run_cutting
from app.services.ppfmt import SawMap, SawNode, saw_job
from app.services.ppfmt import _saw_strips as S

ppfmt.load_all()
from app.services.ppfmt import saw_aes, saw_fastpanel, saw_nanxing_cut, saw_nanxing_ncp  # noqa: E402

KEYS = ("nanxing_nxcutsaw", "nanxing_cutsaw", "nanxing_cutsawfg", "aes_alpha", "aess_alpha", "fastpanel")


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(S, "now", lambda: datetime(2026, 10, 4, 10, 0, 0))


def make_project(extra_parts=()):
    pr = Project(name="9999 mijoz")
    prod = Product(name="01 shkaf", code="999901", qty=1)
    pr.products = [prod]
    el = Operation(type=OpType.EL, name="1-19 oq", el=ELParams(symbol="A", thickness=1))
    xnc = Operation(type=OpType.XNC, code="999901_01_002", name="fasad",
                    xnc=XNCParams(length=700, width=400, thickness=16, face_side=True,
                                  program=[XncCommand(cmd="DrillFront", params=dict(X=50.0, Y=50.0, DP=10.0))]))
    a = Part(uid=1, name="01_001 bok", length=1000, width=500, qty=2, product_id=prod.id)
    b = Part(uid=2, name="01_002 fasad", length=700, width=400, qty=1, grain=True, edge_top=EdgeRef(op_id=el.id),
             product_id=prod.id, xnc_op_ids=[xnc.id])
    cs = Operation(type=OpType.CS, name="LDSP OQ", cs_material=CSMaterialParams(thickness=16),
                   cs_cut=CSCutParams(kerf=3, trim_length=2, trim_width=2),
                   sheets=[StockSheet(id="s1", length=2750, width=1830, qty=10000)], parts=[a, b, *extra_parts])
    pr.operations = [cs, el, xnc]
    return pr, cs


def N(x, y, l, w, k, **kw):
    return SawNode(x=x, y=y, l=l, w=w, kind=k, **kw)


def minimal_job():
    """Hujjatdagi minimal misol (nanxing-nxcutsaw.md §5): bitta vertikal polosa + delovoy qoldiq."""
    pr, cs = make_project()
    job = saw_job(pr, cs)
    strip = N(5, 5, 1000, 1820, "C", axis="y", children=[
        N(5, 5, 1000, 500, "P", uid=1), N(5, 508, 1000, 500, "P", uid=1), N(5, 1011, 700, 400, "P", uid=2),
        N(5, 1414, 1000, 411, "W")])
    root = N(5, 5, 2740, 1820, "C", axis="x", children=[strip, N(1008, 5, 1737, 1820, "W", rem=1)])
    job.maps = [SawMap(index=1, copies=1, sheet_length=2750, sheet_width=1830, is_remnant=False, sheet_id="s1", tree=root,
                       placements=[], offcuts=[], commands=[])]
    return job


CUT_MINIMAL = (
    '<?xml version="1.0" encoding="UTF-8"?><AutoCUT ver="500"><Project Memo="" Name="9999 mijoz" Update="04.10.2026 10:00:00">'
    '<Data Ply="16" TypeName="LDSP OQ"><Spares Type="Shape"><Shape Count="1" Name="О1" Turn="False" X="1742" Y="1830"/></Spares>'
    '<Condition Count="1" Type="Shape"><Shape Count="10000" Flag="True" Name="LDSP OQ" Sx="5" Sy="5" X="2750" Y="1830"/></Condition>'
    '<Solutions SolveGap="3"><Solution><Layouts>'
    '<Layout Count="1" Cut="true" CutCount="0" ID="0" SheetID="0" SheetName="LDSP OQ" X="2750" Y="1830">'
    '<Part Px="5" Py="0" X="1000" Y="1830">'
    '<Part Px="5" Py="5" UID="0" X="1000" Y="500"/>'
    '<Part Grouped="2" Px="5" Py="508" UID="0" X="1000" Y="500"/>'
    '<Part Px="5" Py="1011" X="1000" Y="400"><Part Px="5" Py="1011" UID="1" X="700" Y="400"/></Part>'
    '</Part>'
    '<Part Px="1008" Py="0" Spare="True" UID="0" X="1742" Y="1830"/>'
    '</Layout></Layouts></Solution></Solutions>'
    '<Objective Count="2" Type="Shape">'
    '<Shape Count="2" F1="01_001 bok" F12="false" F13="false" F3="2" F4="1000.00" F5="500.00" Name="Д1" NestGap="3" '
    'Order="01 shkaf" Turn="true" X="1000" Y="500"/>'
    '<Shape Count="1" F1="01_002 fasad" F12="false" F13="true" F3="1" F4="700.00" F5="400.00" F6="999901_01_002" '
    'F8="(A) 1-19 oq" Name="Д2" NestGap="3" Order="01 shkaf" Turn="false" X="700" Y="400"/>'
    '</Objective></Data></Project></AutoCUT>')


def test_registered_keys():
    reg = ppfmt.load_all()
    for k in KEYS:
        assert k in reg and reg[k].group == "saw"
    assert reg["aes_alpha"].fn is reg["aess_alpha"].fn


def test_cut_minimal_matches_documented_example():
    name, data = saw_nanxing_cut.generate(minimal_job())[0]
    assert name == "9999_mijoz_LDSP_OQ.CUT"
    assert data == CUT_MINIMAL.encode("utf-8")
    assert not data.startswith(b"\xef\xbb\xbf") and b"\n" not in data


def test_file_stem_keeps_trailing_underscore_and_order_prefix():
    job = minimal_job()
    job.material_name = "LDSP UD (110197)_diffuseOriginal"
    assert S.file_stem(job) == "9999_mijoz_LDSP_UD_110197__diffuseOriginal"
    job.material_name = "LDSP UD "
    assert S.file_stem(job) == "9999_mijoz_LDSP_UD_"
    job.project_name, job.order = "mijoz", "1234"
    assert S.file_stem(job).startswith("1234_mijoz_")


def _ncp_nodes(d: bytes):
    nn = struct.unpack_from("<i", d, 0x30)[0]
    out = []
    for k in range(nn):
        st = 0x1C + k * 0x208
        name = d[st + 0x18:st + 0x58].decode("utf-16le", "replace").split("\0")[0] if k else ""
        par, nch = struct.unpack_from("<2i", d, st + 0x58)
        vals = struct.unpack_from("<8d", d, st + 0x60)
        cnt = struct.unpack_from("<i", d, st + 0x200)[0]
        ents = [struct.unpack_from("<iid", d, st + 0xA0 + 16 * i) for i in range(cnt)]
        out.append((name, par, nch, vals, ents))
    return out


def _ncp_labels(d: bytes):
    nn = struct.unpack_from("<i", d, 0x30)[0]
    off = 0x1C + nn * 0x208 + 0x68
    return [d[o:o + 0x1000].decode("utf-16le").split("\0")[0] for o in range(off, len(d), 0x1000)]


def test_ncp_structure_and_labels():
    job = minimal_job()
    job.maps[0].tree.children[0].children[-1].rem = 2          # polosa oxiridagi bo'lak ham delovoy qoldiq
    name, z = saw_nanxing_ncp.generate_cutsaw(job)[0]
    assert name == "9999_mijoz_LDSP_OQ.zip"
    zf = zipfile.ZipFile(io.BytesIO(z))
    assert zf.namelist() == ["001.ncp"]
    d = zf.read("001.ncp")
    nodes = _ncp_nodes(d)
    # ildiz + polosa + 2 detal + konteyner + detal + 2 qoldiq = 8 tugun; barglar: 3 detal + 2 qoldiq
    assert len(d) == 0x1C + 8 * 0x208 + 0x68 + 5 * 0x1000
    assert d[:4] == b"\x00ZBD" and struct.unpack_from("<3d", d, 4) == (2750.0, 1830.0, 16.0)
    assert struct.unpack_from("<d2i", d, 0x1C) == (3.0, 1, 1)
    root = nodes[0]
    assert root[4] == [(2, 1, 5.0), (0, 1, 1000.0)] and root[3][2] == 2750 - 5 - 1003      # chiqindi X
    names = [n[0] for n in nodes]
    assert names == ["", "$2", "NONE", "$1", "NONE", "Д2", "Д1", "Д1"]    # teskari kesish tartibi, pre-order
    strip = nodes[2]
    assert strip[4] == [(3, 1, 5.0), (1, 2, 500.0), (1, 1, 400.0)] and strip[2] == 3
    assert strip[3][4:6] == (0.0, 5.0)                                     # tX, tY
    rem2 = nodes[1]
    assert rem2[3][0:2] == (1737.0, 1830.0) and rem2[3][6] == 1008.0      # $ — chetdan torsovka ayirilgan
    labels = _ncp_labels(d)
    assert labels[0] == ("Д2,9999 mijoz,LDSP OQ,01_002 fasad,,2,700.00,400.00,1,false,(A) 1-19 oq,,,,false,false,true,"
                         "999901_01_002,,,01 shkaf")
    assert labels[1].startswith("Д1,9999 mijoz,LDSP OQ,01_001 bok,,1,1000.00,500.00,2,false,")
    assert labels[2] == "$2,9999 mijoz,LDSP OQ,,,2,1737.00,1820.00,0,true,,,,,false,false,false,,,,"
    assert labels[3].startswith("$1,") and labels[4] == ""
    util = struct.unpack_from("<f", d, 0x2C)[0]
    exp = (2 * 1000 * 500 + 700 * 400) / (2750 * 1830 - 1737 * 1820 - 1000 * 411)
    assert abs(util - exp) < 1e-6


def test_ncp_y_root_shift_and_entry_limit():
    pr, cs = make_project()
    job = saw_job(pr, cs)
    strip = N(5, 5, 2740, 500, "C", axis="x", children=[N(5, 5, 1000, 500, "P", uid=1), N(1008, 5, 1000, 500, "P", uid=1)])
    root = N(5, 5, 2740, 1820, "C", axis="y", children=[strip])
    job.maps = [SawMap(index=1, copies=2, sheet_length=2750, sheet_width=1830, is_remnant=False, sheet_id="s1", tree=root,
                       placements=[], offcuts=[], commands=[])]
    d = zipfile.ZipFile(io.BytesIO(saw_nanxing_ncp.generate_cutsaw(job)[0][1])).read("001.ncp")
    nodes = _ncp_nodes(d)
    assert nodes[0][4][0] == (3, 1, 5.0)
    assert nodes[1][3][7] == 8.0 and nodes[1][4] == [(2, 1, 5.0), (0, 2, 1000.0)]     # Y +propil (namunalardagi kabi)
    assert struct.unpack_from("<2i", d, 0x24) == (2, 2)
    # 22 dan ortiq turli kesim — format sig'imidan oshadi
    kids, x = [], 5.0
    for i in range(23):
        kids.append(N(x, 5, 10 + i, 1820, "P", uid=1))
        x += 10 + i + 3
    job.maps[0].tree = N(5, 5, 2740, 1820, "C", axis="x", children=[
        N(5, 5, 2740, 1820, "C", axis="y", children=[N(5, 5, 2740, 100, "C", axis="x", children=kids)])])
    with pytest.raises(ValueError):
        saw_nanxing_ncp.generate_cutsaw(job)


def test_aes_rows():
    job = minimal_job()
    name, data = saw_aes.generate(job)[0]
    assert name == "9999_mijoz_LDSP_OQ.ss" and data.endswith(b"BITIR\r\n")
    rows = data.decode("cp1251").split("\r\n")
    assert rows[:3] == ["BSL1,001,9999 mijoz", "BSL2,04.10.2026,10:00,", "BSL3,From MebeliX Kroy,1.0,,"]
    assert "KON2,     3.00,     3.00, 0.00,     0.00,     0.00,     0.00" in rows
    assert "LMT1,    16.00,    40.00" in rows
    assert "OZL1,*****,    1,   9.860,  1830.00,  2750.00,     2.00,     2.00,     2.00,     2.00" in rows
    assert "URN1,    2,    2,  1000.00,   500.00, ,N" in rows and "URN3, 1, 2" in rows
    assert ("PRT3,0000,        ,,        ,        ,1-19 oq,        ,        ,,        ,        ,,        " in rows)
    assert "PRT4,     0.00,     1.00,     0.00,     0.00,1,                    " in rows
    i = rows.index("BASLA")
    assert rows[i - 5] == "PNL1,01,S,1,0"
    assert rows[i + 1:i + 7] == ["KES1,01,  1000.00,0,000", "KES1,02,   500.00,1,001", "KES1,02,   500.00,1,001",
                                 "KES1,02,   400.00,0,000", "KES1,03,    -0.50,0,000", "KES1,03,   700.00,1,002"]


def test_fastpanel_text():
    name, data = saw_fastpanel.generate(minimal_job())[0]
    assert name == "9999_mijoz_LDSP_OQ.ocm"
    assert data == (b'<ManualPattern JobName="9999_mijoz_LDSP_OQ"><PanelInfo BladeThickness="3" Length="2750" Quantity="1" '
                    b'Thickness="16" TrimSize="5" Width="1830"/><Pattern><Entry Distance="1000" Quantity="1">'
                    b'<Entry Distance="500" Quantity="2"/><Entry Distance="400" Quantity="1"><Entry Distance="700" '
                    b'Quantity="1"/></Entry></Entry></Pattern></ManualPattern>')


def test_strip_tree_flattens_and_wraps():
    # bir xil o'qli ichki konteyner ota-onaga qo'shiladi; perpendikulyar bo'yicha kichik detal konteynerga o'raladi
    inner = N(5, 5, 600, 1820, "C", axis="x", children=[N(5, 5, 300, 1820, "P", uid=1), N(308, 5, 297, 1000, "P", uid=2)])
    root = N(5, 5, 2740, 1820, "C", axis="x", children=[inner, N(608, 5, 100, 1820, "W")])
    p = S.strip_tree(root)
    assert [c.kind for c in p.children] == ["C", "C"]
    assert all(c.level == 1 and c.w == 1820 for c in p.children)
    w = p.children[1]
    assert w.axis == "y" and w.children[0].kind == "P" and w.children[0].level == 2


def _cut_project(n_types=6):
    extra = [Part(uid=10 + i, name=f"02_{i:03d} polka", length=300 + 37 * i, width=200 + 11 * i, qty=2 + i % 3)
             for i in range(n_types)]
    pr, cs = make_project(extra)
    run_cutting(pr, cs, quality="fast")
    return pr, cs


def test_end_to_end_all_formats_reparse():
    pr, cs = _cut_project()
    for k in KEYS:
        name, data, mime = ppfmt.run_saw(k, pr, cs)
        assert b"GibLab" not in data and data
        if k.startswith("nanxing_cutsaw"):
            assert name.endswith(".zip")
    # .CUT qayta o'qish: har detal soni = barglar × karta nusxasi; daraxt — propil bilan ketma-ket
    job = saw_job(pr, cs)
    data = saw_nanxing_cut.generate(job)[0][1]
    d = ET.fromstring(data).find("Project/Data")
    shapes = d.findall("Objective/Shape")
    got = [0] * len(shapes)

    def walk(el, depth):
        kids = el.findall("Part")
        for a, b in zip(kids, kids[1:]):
            if b.get("Spare"):
                continue
            ax = "Px" if float(a.get("Py")) == float(b.get("Py")) else "Py"
            sz = "X" if ax == "Px" else "Y"
            assert float(b.get(ax)) >= float(a.get(ax)) + float(a.get(sz)) + 3 - 1e-6
        for k in kids:
            if not k.findall("Part") and not k.get("Spare"):
                yield int(k.get("UID"))
            yield from walk(k, depth + 1)

    sheets = 0
    for lay in d.findall("Solutions/Solution/Layouts/Layout"):
        c = int(lay.get("Count"))
        sheets += c
        for uid in walk(lay, 0):
            got[uid] += c
    assert got == [int(s.get("Count")) for s in shapes]
    assert sheets == cs.result.total_sheets
    # AES: detallar soni KES1 bo'yicha
    rows = saw_aes.generate(job)[0][1].decode("cp1251").split("\r\n")
    cnt, mult = {}, 1
    for r in rows:
        f = r.split(",")
        if f[0] == "PNL1":
            mult = int(f[3])
        elif f[0] == "KES1" and f[3] == "1":
            cnt[int(f[4])] = cnt.get(int(f[4]), 0) + mult
    assert [cnt.get(i + 1, 0) for i in range(len(job.parts))] == [p.qty for p in job.parts]


def test_cutsawfg_nests_other_materials():
    pr, cs = _cut_project(3)
    cs2 = cs.model_copy(deep=True)
    cs2.id, cs2.name, cs2.code = "cs2", "XDF 2800x2070", "XDF 5.8"
    cs2.cs_material.thickness = 3
    cs2.sheets = [StockSheet(id="x1", length=2800, width=2070, qty=10000)]
    pr.operations.append(cs2)
    run_cutting(pr, cs2, quality="fast")
    name, z = ppfmt.REGISTRY["nanxing_cutsawfg"].fn(saw_job(pr, cs))[0]
    zf = zipfile.ZipFile(io.BytesIO(z))
    inner = [n for n in zf.namelist() if n.endswith(".zip")]
    assert inner == ["9999_mijoz_XDF_2800x2070.zip"]
    assert zf.getinfo(inner[0]).compress_type == zipfile.ZIP_STORED
    iz = zipfile.ZipFile(io.BytesIO(zf.read(inner[0])))
    assert iz.namelist()[0] == "001.ncp" and struct.unpack_from("<3d", iz.read("001.ncp"), 4)[2] == 3.0
    # CutSaw — faqat joriy material
    z2 = ppfmt.REGISTRY["nanxing_cutsaw"].fn(saw_job(pr, cs))[0][1]
    assert not [n for n in zipfile.ZipFile(io.BytesIO(z2)).namelist() if n.endswith(".zip")]
