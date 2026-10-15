"""Arra postprotsessorlari: Biesse Selco NC300 / OSI, SCM MaestroCut / WinCut, FELDER Format4 PC6 / PC7.
Formatlar — docs/mebelix/postprocessors/{biesse-selco-nc300,biesse-selco-osi,scm-maestrocut,scm-wincut,felder-pc6,felder-pc7}.md.
Hamma ma'lumot shu faylda sun'iy quriladi (korxona fayllari va mijoz nomlari ishlatilmaydi). Namunalar bilan solishtirish —
tools/bench/pp_saw_check_biesse.py."""
from __future__ import annotations

import base64
import io
import re
import struct
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime

import pytest

from app.models import (CSCutParams, CSMaterialParams, EdgeRef, ELParams, OpType, Operation, Part, Product, Project,
                        StockSheet)
from app.services import ppfmt
from app.services.calc import run_cutting
from app.services.ppfmt import SawNode, SawMap, saw_job
from app.services.ppfmt import _saw_bsf as B

ppfmt.load_all()
from app.services.ppfmt import biesse_nc300, biesse_osi, felder_format4, scm_maestrocut, scm_wincut  # noqa: E402

KEYS = ("biesse_nc300", "biesse_osi", "scm_maestrocut", "scm_wincut", "felder_format4_pc6", "felder_format4_pc7")
NOW = datetime(2026, 10, 1, 12, 0, 0)


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(B, "now", lambda: NOW)


def make_project():
    pr = Project(name="1001_mijoz", currency="UZS", size_mode="detail")
    prod = Product(name="01 shkaf", code="100101", qty=1, order_info="1001 mijoz")
    pr.products = [prod]
    el = Operation(type=OpType.EL, name="1-19 Namuna", code="KP-1/19-N", el=ELParams(symbol="A", thickness=1))
    e = EdgeRef(op_id=el.id)
    parts = [
        Part(uid=1, name="01_001 bok", code="01_001", length=800, width=400, qty=2, grain=True, product_id=prod.id,
             edge_top=e, edge_bottom=e, edge_left=e),
        Part(uid=2, name="01_002 polka uzun nomli", code="01_002", length=1000, width=300, qty=1, product_id=prod.id,
             edge_bottom=e),
        Part(uid=3, name="01_003 tom", code="01_003", length=500, width=600, qty=1, product_id=prod.id),
        Part(uid=4, name="01_004 sokl", code="01_004", length=480, width=290, qty=1, product_id=prod.id),
    ]
    cs = Operation(type=OpType.CS, name="LDSP  NAMUNA", cs_material=CSMaterialParams(thickness=16),
                   cs_cut=CSCutParams(kerf=3, trim_length=2, trim_width=2, pack_height=40),
                   sheets=[StockSheet(id="s1", length=2750, width=1830, qty=10000)], parts=parts)
    pr.operations = [cs, el]
    return pr, cs


def N(x, y, l, w, k, **kw):
    return SawNode(x=x, y=y, l=l, w=w, kind=k, **kw)


def doc_job(key, copies=1, label_fields=None):
    """Hujjatlardagi minimal misol: list 2750×1830, propil 3, torsovka 2 (+3 = 5); polosalar Y bo'ylab 400 va 600,
    oxirida ishbop qoldiq 2740×814."""
    pr, cs = make_project()
    job = saw_job(pr, cs, None)
    s1 = N(5, 5, 2740, 400, "C", axis="x", children=[
        N(5, 5, 800, 400, "P", uid=1), N(808, 5, 800, 400, "P", uid=1), N(1611, 5, 1134, 400, "W")])
    u2 = N(508, 711, 1000, 290, "C", axis="x", children=[N(508, 711, 480, 290, "P", uid=4), N(991, 711, 517, 290, "W")])
    x2 = N(508, 408, 1000, 600, "C", axis="y", children=[N(508, 408, 1000, 300, "P", uid=2), u2])
    s2 = N(5, 408, 2740, 600, "C", axis="x", children=[N(5, 408, 500, 600, "P", uid=3), x2, N(1511, 408, 1234, 600, "W")])
    rem = N(5, 1011, 2740, 814, "W", rem=1)
    root = N(5, 5, 2740, 1820, "C", axis="y", children=[s1, s2, rem])
    job.maps = [SawMap(index=1, copies=copies, sheet_length=2750, sheet_width=1830, is_remnant=False, sheet_id="s1", tree=root,
                       placements=[], commands=[], trim_length=2, trim_width=2,
                       offcuts=[dict(number=1, kind="remnant", business=True, x=5, y=1011, length=2740, width=814,
                                     raw_length=2750, raw_width=819)])]
    job.params = dict(ppfmt.saw_job(pr, cs, key).params)
    if label_fields is not None:
        job.params["_label_fields"] = label_fields
    return job


def unzip(b: bytes) -> dict:
    z = zipfile.ZipFile(io.BytesIO(b))
    return {n: z.read(n) for n in z.namelist()}


def all_bytes(name: str, data: bytes) -> bytes:
    out = name.encode() + data
    if data[:2] == b"PK":
        for n, b in unzip(data).items():
            out += n.encode() + b
    return out


# ───────────────────────── umumiy ─────────────────────────
def test_registered():
    reg = ppfmt.load_all()
    for k in KEYS:
        assert k in reg and reg[k].group == "saw"
    assert "Chk" in reg["biesse_osi"].note            # OSI nazorat summasi haqida ogohlantirish


@pytest.mark.parametrize("key", KEYS)
def test_generates_without_foreign_program_name(key):
    job = doc_job(key)
    files = ppfmt.REGISTRY[key].fn(job)
    assert len(files) == 1
    name, data = files[0]
    assert b"giblab" not in all_bytes(name, data).lower()
    assert data


def test_cut_tree_and_merge():
    job = doc_job("biesse_nc300")
    ax, cuts = B.cut_tree(job.maps[0])
    assert ax == "y"
    assert [(c.level, c.dim, c.uid, c.rem) for c in B.walk_cuts(cuts)] == [
        (1, 400, 0, 0), (2, 800, 1, 0), (2, 800, 1, 0), (1, 600, 0, 0), (2, 500, 3, 0), (2, 1000, 0, 0), (3, 300, 2, 0),
        (3, 290, 0, 0), (4, 480, 4, 0), (1, 814, 0, 1)]
    m = B.merge_runs(B.drop_rem(cuts), by_part=False)
    assert [(c.level, c.dim, c.rep) for c in B.walk_cuts(m)] == [
        (1, 400, 1), (2, 800, 2), (1, 600, 1), (2, 500, 1), (2, 1000, 1), (3, 300, 1), (3, 290, 1), (4, 480, 1)]
    leaf = next(c for c in B.walk_cuts(cuts) if c.uid == 4)
    assert (leaf.sx, leaf.sy) == (480, 290)


def test_partial_leaf_gets_extra_level():
    """Detal ota bo'lakni ikkinchi o'qda to'liq egallamasa — qo'shimcha kesim darajasi."""
    root = N(5, 5, 2740, 1820, "C", axis="y", children=[
        N(5, 5, 2740, 400, "C", axis="x", children=[N(5, 5, 800, 390, "P", uid=1)])])
    m = SawMap(index=1, copies=1, sheet_length=2750, sheet_width=1830, is_remnant=False, sheet_id="s", tree=root,
               placements=[], offcuts=[], commands=[])
    _ax, cuts = B.cut_tree(m)
    assert [(c.level, c.dim, c.uid) for c in B.walk_cuts(cuts)] == [(1, 400, 0), (2, 800, 0), (3, 390, 1)]


# ───────────────────────── Biesse NC300 ─────────────────────────
def nc_label(text: str):
    seg = text[text.index("B_LABEL\r\n") + 9:text.index("E_LABEL")]
    raw = base64.b64decode("".join(x.strip() for x in seg.split("\r\n")))
    p = 0

    def i32():
        nonlocal p
        v = struct.unpack(">i", raw[p:p + 4])[0]
        p += 4
        return v

    def rec():
        nonlocal p
        assert raw[p] == 1
        p += 1
        n = i32()
        s = raw[p:p + n]
        p += n
        o = bytearray()
        i = 0
        while i < len(s):
            if s[i] == 0xC1:
                o.append(0x40 | (s[i + 1] & 0x3F))
                i += 2
            else:
                o.append(s[i])
                i += 1
        return bytes(o).decode("utf-8").split(",")
    rests = [(rec(), i32()) for _ in range(i32())]
    dets = [rec() for _ in range(i32())]
    groups = [[(i32(), i32(), i32()) for _ in range(i32())] for _ in range(i32())]
    assert p == len(raw)
    return rests, dets, groups


def test_nc300():
    job = doc_job("biesse_nc300", copies=2)
    name, data = biesse_nc300.gen(job)[0]
    assert name == "1001_mij.zip"
    f = unzip(data)
    assert sorted(f) == ["dist/1001_mij", "tagli/1001_mij.001"]
    dist = f["dist/1001_mij"].decode("ascii")
    assert dist.startswith('1\r\nB_FDIS\r\n\tDAT\r\n\t\tNOME="1001_mij"\r\n\t\tPROX=""\r\n\t\tCPI=0\r\n\t\tCOMM="1001 mijoz"\r\nB_DIS\r\n')
    assert '\t\tNPG="1001_mij.001"\r\n\t\tQTA=2\r\n\t\tESE=0\r\n\t\tOPZ=""\r\n\t\tCOM="2750x1830x16: LDSP  NAMUNA"\r\nE_DIS\r\nE_FDIS\r\n' in dist
    t = f["tagli/1001_mij.001"].decode("ascii")
    assert t.endswith("E_LABEL\r\n") and "\n" not in t.replace("\r\n", "")
    for line in ('\tNM="1001_mij.001"', '\tMAT="LDSP  NAMUNA"', "\tX=275000", "\tY=183000", "\tZ=1600", "\tHP=4000", "\tQTA=2",
                 "\tROL=500", "\tROT=500", "\tRMIP=500"):
        assert line + "\r\n" in t
    cuts = re.findall(r'\tCUT=(\d+)\r\n\t\tCOD="(\w+)"\r\n\t\tDIM=(\d+)\r\n\t\tQTA=(\d+)', t)
    assert [(c, int(d), int(q)) for _i, c, d, q in cuts] == [
        ("4", 60000, 1), ("5", 50000, 1), ("5", 100000, 1), ("Z1", 29000, 1), ("Z2", 48000, 1), ("Z1", 30000, 1),
        ("4", 40000, 1), ("5", 80000, 2)]              # Y bo'ylab ro'yxatlar teskari (stanok Y o'qi ko'zguli)
    assert [int(i) for i, *_ in cuts] == list(range(1, 9))
    rests, dets, groups = nc_label(t)
    assert [r[0][:8] for r in rests] == [["rest.fme", "", "1", "1", "2740", "814", "2.23", "1001 mijoz"]]
    assert all(len(d) == 31 and d[30] == "" for d in dets) and len(rests[0][0]) == 31
    assert dets[0][:15] == ["detail.fme", "", "2", "1", "1", "1001 mijoz", "800", "400", "01_001 bok", "2", "A", "", "A", "A", "true"]
    assert [d[3] for d in dets] == ["1", "2", "3", "4"]            # xesh-jadval tartibi (detal raqami bo'yicha)
    assert groups == [[(80000, 40000, 0), (80000, 40000, 0)], [(50000, 60000, 2)], [(100000, 30000, 1)], [(48000, 29000, 3)]]


def test_nc300_first_cut_along_x_and_size_merge():
    """Polosalar X bo'ylab → kodlar 1/2; bir xil o'lchamli turli detallar ham QTA ga yig'iladi (NC300), OSI da — yo'q."""
    pr, cs = make_project()
    cs.parts.append(Part(uid=5, name="01_005 bok", length=800, width=400, qty=1, product_id=pr.products[0].id))
    job = saw_job(pr, cs, None)
    root = N(5, 5, 2740, 1820, "C", axis="x", children=[
        N(5, 5, 800, 1820, "C", axis="y", children=[N(5, 5, 800, 400, "P", uid=1), N(5, 408, 800, 400, "P", uid=5),
                                                    N(5, 811, 800, 400, "P", uid=1)])])
    job.maps = [SawMap(index=1, copies=1, sheet_length=2750, sheet_width=1830, is_remnant=False, sheet_id="s1", tree=root,
                       placements=[], offcuts=[], commands=[], trim_length=2, trim_width=2)]
    t = unzip(biesse_nc300.gen(job)[0][1])["tagli/1001_mij.001"].decode("ascii")
    assert re.findall(r'COD="(\w+)"\r\n\t\tDIM=(\d+)\r\n\t\tQTA=(\d+)', t) == [("1", "80000", "1"), ("2", "40000", "3")]
    _r, dets, groups = nc_label(t)
    assert len(dets) == 2 and [[i for _x, _y, i in g] for g in groups] == [[0], [1], [0]]    # guruhlar — listdagi tartibda
    r = ET.fromstring(biesse_osi.build(job))
    assert [(c.get("Code"), c.get("L"), c.get("Rep")) for c in r.iter("Cut")] == [
        ("1", "800.00", "1"), ("2", "400.00", "1"), ("2", "400.00", "1"), ("2", "400.00", "1")]


# ───────────────────────── Biesse OSI ─────────────────────────
def test_osi():
    job = doc_job("biesse_osi", copies=2)
    name, data = biesse_osi.gen(job)[0]
    assert name == "1001_mijoz_LDSP_NAMUNA.xml"
    s = data.decode("utf-8")
    assert s.startswith('<?xml version="1.0" encoding="UTF-8"?><Order Code="') and "\n" not in s
    assert "Chk" not in s                                         # algoritm noma'lum — yozilmaydi
    for m in re.finditer(r"<(\w+)((?: [\w.]+=\"[^\"]*\")*)", s):   # atributlar ASCII tartibida
        ks = re.findall(r' ([\w.]+)="', m.group(2))
        assert ks == sorted(ks), m.group(0)
    r = ET.fromstring(data)
    wl = r.find("WorkList")
    assert [e.tag for e in wl] == ["Part"] * 4 + ["Job"] + ["Piece"] * 4
    assert wl.get("Code") == "1001_mijoz_LDSP_NAMUNA" and wl.get("MaterialID") == "1"
    p1 = wl.find("Part")
    assert p1.get("id") == "P1" and p1.get("Code") == p1.get("PartNo") == "1" and p1.get("L") in ("800.0", "799.0") and p1.get("W") in ("400.0", "398.0")
    assert p1.get("Grain") == "1" and p1.get("Desc1") == "01 shkaf" and p1.get("IDesc") == "01_001 bok"
    assert (p1.get("ThkEdgeUp"), p1.get("ThkEdgeLo"), p1.get("ThkEdgeL"), p1.get("ThkEdgeR")) == ("1.0", "1.0", "1.0", "0.0")
    assert p1.get("TypEdgeUp") == "A" and p1.get("MatEdgeL") == "1-19 Namuna" and "TypEdgeR" not in p1.attrib
    assert p1.get("Material") == "LDSP  NAMUNA" and p1.get("DrillCode3") == "true" and "DrillBarCode2" not in p1.attrib
    job_el = wl.find("Job")
    assert job_el.get("Code") == "1001_mijoz_LDSP_NAMUNA.001" and job_el.get("QBoards") == job_el.get("ToWork") == "2"
    assert job_el.get("Comment") == r.get("Comment")
    assert [(t.get("ID"), t.get("Value")) for t in job_el.findall("TechnoParam")] == [
        (str(320 + i), "0" if i % 4 == 0 else "500") for i in range(16)]
    b = job_el.find("Board")
    assert (b.get("Code"), b.get("L"), b.get("W"), b.get("Thickness"), b.get("id")) == ("B11", "2750", "1830", "16", "1")
    assert [(c.get("Code"), c.get("L"), c.get("Rep"), c.get("id")) for c in job_el.find("Program")] == [
        ("4", "400.00", "1", "1"), ("5", "800.00", "2", "2"), ("4", "600.00", "1", "3"), ("5", "500.00", "1", "4"),
        ("5", "1000.00", "1", "5"), ("Z1", "300.00", "1", "6"), ("Z1", "290.00", "1", "7"), ("Z2", "480.00", "1", "8")]
    pc = wl.findall("Piece")
    assert [x.get("N") for x in pc] == ["1", "2", "3", "4"]
    assert pc[0].attrib == {"G": "1", "L": "800.00", "N": "1", "Q": "2", "W": "400.00", "qMin": "2"}
    assert [(e.tag, dict(e.attrib)) for e in pc[0]] == [("Pid", {"id": "P1"}),
                                                        ("Sid", {"id": "1001_mijoz_LDSP_NAMUNA.001", "qP1": "4"})]


def test_osi_label_table_drives_part_attributes():
    rows = [dict(name=n, expr=e) for n, e in (
        ("Код", "'X' + part.id"), ("Коорд min", "count"), ("Коорд max", "7"), ("Приоритет", "50"), ("Длина", "length"),
        ("Ширина", "width"), ("Текстура", "if(txt,1,0)"), ("Finish", "'T'"), ("EvDate", "'2026-01-02'"),
        ("PartNo", "indexInOperation"), ("Comment", "'izoh'"), ("Job", ""), ("Name", ""), ("I", "name"),
        ("II", "product.order"))]
    r = ET.fromstring(biesse_osi.build(doc_job("biesse_osi", label_fields=rows)))
    p = r.find(".//Part")
    assert (p.get("id"), p.get("qMin"), p.get("QMax"), p.get("Prio"), p.get("Finish"), p.get("EvDate"), p.get("Comment"),
            p.get("IIDesc")) == ("X1", "2", "7", "50", "T", "2026-01-02", "izoh", "1001 mijoz")
    assert "Job" not in p.attrib and "Name" not in p.attrib
    assert r.find(".//Pid").get("id") == "X1" and r.find(".//Sid").get("qX1") == "2"
    # jadval bo'sh — etiketka maydonlari yozilmaydi (bo'sh), format maydonlari qoladi
    p = ET.fromstring(biesse_osi.build(doc_job("biesse_osi", label_fields=[]))).find(".//Part")
    assert "IDesc" not in p.attrib and "L" not in p.attrib and p.get("Material") == "LDSP  NAMUNA"


# ───────────────────────── SCM MaestroCut / WinCut ─────────────────────────
def test_maestrocut():
    job = doc_job("scm_maestrocut", copies=2, label_fields=[])          # jadvalsiz — faqat format qoidalari
    name, data = scm_maestrocut.gen(job)[0]
    assert name == "1001_mijoz_LDSP_NAMUNA.zip"
    f = unzip(data)
    assert sorted(f) == ["1001_mijoz_LDSP_NAMUNA.001.XPrg", "1001_mijoz_LDSP_NAMUNA.XMix"]
    x = f["1001_mijoz_LDSP_NAMUNA.XMix"].decode("ascii")
    assert x == ('<xMix><Header Date="01.10.2026" Descrizione="1001_mijoz_LDSP_NAMUNA" Import="From MebeliX Kroy"/><Materials>'
                 '<Material Larghezza="1830" Lunghezza="2750" Quantita="2" Spessore="16" Tipologia=""/></Materials><RigheMix>'
                 '<RigaMix CambioMateriale="0" File="C:\\MaestroCut\\Client\\xMix\\1001_mijoz_LDSP_NAMUNA.001.XPrg" Pacco="2" '
                 'Rep="2"/></RigheMix></xMix>')
    t = f["1001_mijoz_LDSP_NAMUNA.001.XPrg"].decode("ascii")
    lines = t.split("\r\n")
    assert lines[0] == ('<SchemaDoc><Header TipoCave="1" NumFogliPacco="2" Descrizione="LDSP  NAMUNA" Spessore="16" '
                        'Date="01/10/2026" Lunghezza="2750" Larghezza="1830" SpessoreLama="3" Swap="0" Inforesto="1"/>')
    assert lines[1] == '<Material Tipologia="2" Codice=""/>' and lines[-1] == "</SchemaDoc>"
    cuts = re.findall(r'<Cut ID="(\d+)" T="(\w+)" Dim="([\d.]+)" Rip="(\d+)" EtiID="([^"]*)"/>', t)
    assert [c[1:] for c in cuts] == [
        ("P", "2750", "1", ""), ("RY", "5", "1", ""), ("Y", "400", "1", ""), ("RX", "5", "1", ""),
        ("X", "800", "2", "(1,1)(1,1)"), ("F", "0.00", "0", ""), ("Y", "600", "1", "(5)"), ("RX", "5", "1", ""),
        ("X", "500", "1", "(3,3)"), ("F", "0.00", "0", ""), ("X", "1000", "1", ""), ("U", "300", "1", "(2,2)"),
        ("F", "0.00", "0", ""), ("U", "290", "1", ""), ("V", "480", "1", "(4,4)"), ("F", "0.00", "0", "")]
    assert [int(c[0]) for c in cuts] == list(range(1, 17))
    et = [dict(re.findall(r'(\w+)="([^"]*)"', e)) for e in re.findall(r"<Etichetta ([^>]*)/>", t)]
    assert [e["Id"] for e in et] == ["1", "2", "3", "4", "5"] and [e["Resto"] for e in et] == ["0"] * 4 + ["1"]
    assert all(len(e) == 75 for e in et)
    e1 = et[0]
    assert (e1["Lunghezza"], e1["Larghezza"], e1["Campo3"], e1["Campo10"], e1["Campo40"]) == (
        "800.00", "400.00", "1", "01_001 bok", "1")
    assert (e1["Campo11"], e1["Campo14"], e1["Campo15"], e1["Campo51"], e1["Campo57"]) == (
        "1-19 Namuna", "", "KP-1/19-N", "1.0", "0.0")
    assert e1["Campo28"] == "LDSP  NAMUNA" and e1["Campo31"] == "01 shkaf" and e1["Campo49"] == "4"
    assert re.fullmatch(r"[0-9a-f]{32}#1", e1["Campo64"])
    r = et[4]
    assert (r["Lunghezza"], r["Larghezza"], r["Richiesti"], r["Campo19"], r["Campo46"]) == ("2740.00", "814.00", "1", "1", "true")


def test_maestrocut_label_table_by_attribute_name():
    rows = [dict(name="Codice", expr="product.order"), dict(name="Richiesti", expr="count"), dict(name="CodiceBordo1", expr="ets"),
            dict(name="Campo2", expr="'qo`shimcha'"), dict(name="NotAnAttribute", expr="1")]
    job = doc_job("scm_maestrocut", label_fields=rows)
    t = scm_maestrocut.files(job)["1001_mijoz_LDSP_NAMUNA.001.XPrg"].decode("cp1251")
    e1 = dict(re.findall(r'(\w+)="([^"]*)"', re.findall(r"<Etichetta ([^>]*)/>", t)[0]))
    assert (e1["Codice"], e1["Richiesti"], e1["CodiceBordo1"], e1["Campo2"]) == ("1001 mijoz", "2", "A", "qo`shimcha")
    assert "NotAnAttribute" not in t


def test_wincut():
    job = doc_job("scm_wincut")
    name, data = scm_wincut.gen(job)[0]
    assert name == "1001_mijoz_LDSP_NAMUNA.zip"
    f = unzip(data)
    assert list(f) == ["1001 mijoz/1001_mijoz_LDSP_NAMUNA.001"]
    t = f["1001 mijoz/1001_mijoz_LDSP_NAMUNA.001"].decode("ascii")
    blank = "," * 17
    assert t == "\r\n".join([
        "[Intestazione]", "Descrizione=LDSP  NAMUNA", "TipoMateriale=", "Lunghezza=2750", "Larghezza=1830", "Spessore=16",
        "AltPacco=16", "VelRotaz=3000", "VelAvanz=30", "[Dati]", "NumeroDati=5",
        f"1=,,2,jobName,jobDesc,1,800,400,16,,0,2{blank}PART,1,",
        f"2=,,1,jobName,jobDesc,2,1000,300,16,,0,1{blank}PART,2,",
        f"3=,,1,jobName,jobDesc,3,500,600,16,,0,1{blank}PART,3,",
        f"4=,,1,jobName,jobDesc,4,480,290,16,,0,1{blank}PART,4,",
        f"5=,,1,jobName,jobDesc,5,2740,814,16,,0,1{blank}REST,1,",
        "[Righe]",
        "1=RY,5,1,0.0000,0.0000,0.0000,0.0000", "2=Y,400,1,0.0000,0.0000,0.0000,0.0000", "3=RX,5,1,0.0000,0.0000,0.0000,0.0000",
        "4=X,800,2,0.0000,0.0000,0.0000,0.0000", "5=Y,600,1,0.0000,0.0000,0.0000,0.0000", "6=RX,5,1,0.0000,0.0000,0.0000,0.0000",
        "7=X,500,1,0.0000,0.0000,0.0000,0.0000", "8=U*,0.0000,0,0.0000,0.0000,0.0000,0.0000",
        "9=X,1000,1,0.0000,0.0000,0.0000,0.0000", "10=U,300,1,0.0000,0.0000,0.0000,0.0000",
        "11=V*,0.0000,0,0.0000,0.0000,0.0000,0.0000", "12=U,290,1,0.0000,0.0000,0.0000,0.0000",
        "13=V,480,1,0.0000,0.0000,0.0000,0.0000", "NumeroRighe=13", "[Riferimenti]",
        "1=", "2=", "3=", "4=(1)(1)", "5=(5)", "6=", "7=(3)", "8=", "9=", "10=(2)", "11=", "12=", "13=(4)"]) + "\r\n"


def test_wincut_pack_and_label_fields():
    rows = [dict(name="Campo10", expr="name"), dict(name="Campo11", expr="ets")]
    job = doc_job("scm_wincut", copies=2, label_fields=rows)
    t = next(iter(scm_wincut.files(job).values())).decode("cp1251")
    assert "AltPacco=32\r\n" in t and "4=(1,1)(1,1)\r\n" in t
    f = re.search(r"\r\n1=(.*?)\r\n", t).group(1).split(",")
    assert len(f) == 31 and f[2] == "4" and f[12:14] == ["01_001 bok", "A"] and f[14:28] == [""] * 14 and f[28:] == ["PART", "1", ""]


# ───────────────────────── FELDER Format4 ─────────────────────────
def test_pc6():
    job = doc_job("felder_format4_pc6", copies=2)
    name, data = felder_format4.gen_pc6(job)[0]
    assert name == "1001_mijoz_LDSP_NAMUNA.may"
    t = data.decode("ascii")
    assert t.endswith("MA999/\r\n")
    lines = t.split("\r\n")[:-1]
    assert [x[:5] for x in lines] == (["MA000", "MA005"] + ["MA010", "MA015"] * 4 + ["MA050", "MA200", "MA300", "MA310", "MA310",
                                      "MA300", "MA310", "MA320", "MA340", "MA999"])
    assert all(x.endswith("/") for x in lines)
    assert lines[0] == "MA000/011026/A//MebeliX /M/UZS/" + "1001_mijoz".ljust(30) + "/"
    f = lines[2].split("/")
    assert [len(x) for x in f[:21]] == [5, 10, 6, 5, 16, 8, 8, 5, 1, 2, 12, 8, 8, 8, 8, 30, 30, 30, 30, 5, 5]
    assert f[3:9] == ["016.0", "01_001 bok      ", "000800.0", "000400.0", "00002", "N"]
    assert f[11:15] == ["000800.0", "000400.0", "000799.0", "000398.0"]          # kesish o'lchami; kromkasiz (jl, jw)
    assert f[15].rstrip() == "(A) 1-19 Namuna" and f[18].strip() == ""
    assert lines[4].split("/")[4] == "01_002 polka uzu"                          # 16 belgiga kesiladi
    f15 = lines[3].split("/")
    assert [len(x) for x in f15[8:15]] == [30] * 7 and f15[14].rstrip() == "#P(1)"
    assert lines[10].split("/")[4:16] == ["Mebeli", "002750.0", "001830.0", "0015", "J   ", "0000.00", "000105.0", "05.0", "05.0",
                                          "05.0", "03.0", "LDSP  NAMUNA".ljust(30)]
    assert lines[11].split("/")[4:15] == ["Mebeli", "002750.0", "001830.0", "0002", "0002", "0002", "05.0", "05.0", "05.0", "05.0",
                                          "03.0"]
    assert lines[12:20] == [
        "MA300/000400.0/     /", "MA310/1               /000800.0/000400.0/01/     /",
        "MA310/1               /000800.0/000400.0/01/     /", "MA300/000600.0/     /",
        "MA310/3               /000500.0/000600.0/01/     /", "MA320/2               /001000.0/000300.0/01/     /",
        "MA340/4               /000480.0/000290.0/01/     /", "MA999/"]


def test_pc7():
    job = doc_job("felder_format4_pc7", copies=2)
    name, data = felder_format4.gen_pc7(job)[0]
    t = data.decode("utf-8")
    lines = t.split("\r\n")
    assert lines[-1] == "" and lines[-2] == "MA999"
    S = "§§"
    assert lines[0] == S.join(["MA000", "01.10.2026", "MebeliX Kroy", "I", "1001_mijoz_LDSP_NAMUNA.may", "MM", "UZS", "1001_mijoz"])
    f = lines[1].split(S)
    assert len(f) == 28
    assert f[:17] == ["MA010", "1", "LDSP  NAMUNA", "16", "01_001 bok", "800", "400", "2", "True", "(A) 1-19 Namuna",
                      "(A) 1-19 Namuna", "(A) 1-19 Namuna", "", "800", "400", "800", "400"]
    assert f[17:21] == ["1", "LDSP  NAMUNA", "", "01 shkaf"] and f[24:] == ["false", "false", "false", "#P(1)"]
    rest = [x.split(S) for x in lines if S + "REST" + S in x]
    assert [(r[5], r[6], r[7]) for r in rest] == [("2750", "1830", "2"), ("2740", "814", "0")]
    assert all(len(r) == 26 for r in rest)
    i = next(k for k, x in enumerate(lines) if x.startswith("MA200"))
    assert lines[i].split(S)[5:] == ["2750", "1830", "2", "2", "2", "5", "5", "5", "5", "3"]
    assert re.fullmatch(r"#N\(\d{17}\)", lines[i].split(S)[4])
    assert lines[i + 1:-1] == [
        "MA300§§400", "MA310§§D1§§800§§400§§1§§2", "MA310§§D1§§800§§400§§1§§2", "MA300§§600", "MA310§§D3§§500§§600§§3§§2",
        "MA320§§D2§§1000§§300§§2§§2", "MA340§§D4§§480§§290§§4§§2", "MA300§§819§§", f"MA310§§R1§§2750§§819§§{rest[1][1]}§§1",
        "MA999"]


def test_felder_hidden_piece_moves_after_ready_part():
    """Ichida tayyor detali yo'q 2-daraja bo'lagi polosa boshiga (yoki 2-daraja detaldan keyinga) ko'chiriladi."""
    pr, cs = make_project()
    job = saw_job(pr, cs, None)
    a = N(5, 5, 500, 600, "C", axis="y", children=[N(5, 5, 500, 300, "P", uid=2), N(5, 308, 500, 292, "W")])   # tayyor detalli
    hid = N(508, 5, 480, 600, "C", axis="y", children=[
        N(508, 5, 480, 290, "C", axis="x", children=[N(508, 5, 240, 290, "P", uid=4), N(751, 5, 237, 290, "P", uid=4)])])
    root = N(5, 5, 2740, 1820, "C", axis="y", children=[N(5, 5, 2740, 600, "C", axis="x", children=[a, hid])])
    job.maps = [SawMap(index=1, copies=1, sheet_length=2750, sheet_width=1830, is_remnant=False, sheet_id="s1", tree=root,
                       placements=[], offcuts=[], commands=[], trim_length=2, trim_width=2)]
    t = felder_format4.pc7(job)
    i = t.index("MA300")
    assert [x.split("§§")[:2] for x in t[i:].split("\r\n")[:5]] == [["MA300", "600"], ["MA340", "D4"], ["MA350", "D4"],
                                                                 ["MA320", "D2"], ["MA999"]]


# ───────────────────────── optimizator bilan (end-to-end) ─────────────────────────
def counts_from(key: str, name: str, data: bytes) -> dict:
    """Fayldan har detal uid uchun jami dona (karta nusxalari bilan)."""
    out: dict[int, int] = {}

    def add(u, n):
        out[u] = out.get(u, 0) + n
    if key == "biesse_nc300":
        for n, b in unzip(data).items():
            if n.startswith("tagli"):
                t = b.decode("ascii")
                q = int(re.search(r"\tQTA=(\d+)\r\nE_DAT", t).group(1))
                _r, dets, groups = nc_label(t)
                for g in groups:
                    for _x, _y, i in g:
                        add(int(dets[i][3]), q)
    elif key == "biesse_osi":
        for s in ET.fromstring(data).iter("Sid"):
            for k, v in s.attrib.items():
                if k.startswith("qP"):
                    add(int(k[2:]), int(v))
    elif key == "scm_maestrocut":
        for n, b in unzip(data).items():
            if n.endswith(".XPrg"):
                t = b.decode("ascii")
                ids = {e["Id"]: (e["Resto"], int(e["Campo3"])) for e in
                       (dict(re.findall(r'(\w+)="([^"]*)"', x)) for x in re.findall(r"<Etichetta ([^>]*)/>", t))}
                for eti in re.findall(r'EtiID="([^"]*)"', t):
                    for i in re.findall(r"\d+", eti):
                        if ids[i][0] == "0":
                            add(ids[i][1], 1)
    elif key == "scm_wincut":
        for b in unzip(data).values():
            for ln in b.decode("ascii").split("[Dati]")[1].split("[Righe]")[0].split("\r\n"):
                f = ln.split("=", 1)[-1].split(",")
                if len(f) == 31 and f[28] == "PART":
                    add(int(f[5]), int(f[2]))
    elif key == "felder_format4_pc6":
        q = 1
        for ln in data.decode("ascii").split("\r\n"):
            f = ln.split("/")
            if f[0] == "MA200":
                q = int(f[7])
            elif re.fullmatch(r"MA[34][1-9]0", f[0]):
                add(int(f[1]), q)
    else:
        for ln in data.decode("utf-8").split("\r\n"):
            f = ln.split("§§")
            if re.fullmatch(r"MA[34][1-9]0", f[0]) and f[1].startswith("D"):
                add(int(f[4]), int(f[5]))
    return out


@pytest.mark.parametrize("key", KEYS)
def test_end_to_end_with_optimizer(key):
    pr, cs = make_project()
    cs.parts[0].qty = 14
    cs.parts[1].qty = 9
    cs.parts[2].qty = 7
    cs.parts[3].qty = 11
    run_cutting(pr, cs, quality="fast")
    assert cs.result and cs.result.maps
    name, data, _mime = ppfmt.run_saw(key, pr, cs)
    assert b"giblab" not in all_bytes(name, data).lower()
    got = counts_from(key, name, data)
    assert got == {1: 14, 2: 9, 3: 7, 4: 11}
