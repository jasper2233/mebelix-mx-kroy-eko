"""Giben (G57 / GVisionXP / GDrive) va KDT (XML / KS33X / yangi versiya) arra formatlari — sun'iy ish bilan.
Kutilgan qiymatlar docs/mebelix/postprocessors/{giben-*,kdt-*}.md dagi minimal misollardan (korxona fayllarisiz)."""
from __future__ import annotations

import io
import re
import struct
import zipfile

import pytest

from app.services import ppfmt
from app.services.ppfmt import SawMap, SawNode, SawPart
from app.services.ppfmt._saw_common import demo_job
from app.services.ppfmt._saw_giben import layout, leaf_counts, patterns, translit

L, W, KERF, TRIM = 2750.0, 1830.0, 3.0, 2.0
OFF = TRIM + KERF


def _parts():
    return [SawPart(uid=1, name="01_001 bok", code="01_001", length=1000, width=500, qty=2, grain=True,
                    edges={"left": {"symbol": "A", "name": "PVX", "thickness": 1.0}}),
            SawPart(uid=2, name="01_002 polka", code="01_002", length=600, width=400, qty=1, grain=False)]


def _map(children, copies=1, rem=True, axis="x"):
    root = SawNode(x=OFF, y=OFF, l=L - 2 * OFF, w=W - 2 * OFF, kind="C", axis=axis, children=children)
    offcuts = []
    if rem:
        last = children[-1]
        x = last.x + last.l + KERF
        w = SawNode(x=x, y=OFF, l=L - OFF - x, w=W - 2 * OFF, kind="W", rem=1)
        root.children.append(w)
        offcuts.append(dict(x=w.x, y=w.y, length=w.l, width=w.w, kind="remnant", number=1, business=True))
    return SawMap(index=1, copies=copies, sheet_length=L, sheet_width=W, is_remnant=False, sheet_id="s1", tree=root,
                  placements=[], offcuts=offcuts, commands=[], trim_length=TRIM, trim_width=TRIM)


def _strip_doc(lead=0.0):
    """Polosa 1000 → 500, 500 (detal 1), 400 lik bo'lakdan 600 (detal 2); lead — ichki bo'lak boshidagi siljish."""
    return SawNode(x=5, y=5, l=1000, w=1820, kind="C", axis="y", children=[
        SawNode(x=5, y=5, l=1000, w=500, kind="P", uid=1),
        SawNode(x=5, y=508, l=1000, w=500, kind="P", uid=1),
        SawNode(x=5, y=1011, l=1000, w=400, kind="C", axis="x", children=[
            SawNode(x=5 + lead, y=1011, l=600, w=400, kind="P", uid=2)])])


def _job(maps=None, **kw):
    job = demo_job(_parts(), maps or [_map([_strip_doc()])], kerf=KERF, trim=TRIM, **kw)
    job.material_code = ""
    return job


def _run(key, job):
    files = ppfmt.load_all()[key].fn(job)
    assert len(files) == 1
    return files[0]


def _unzip(data):
    z = zipfile.ZipFile(io.BytesIO(data))
    return [(i.filename, z.read(i)) for i in z.infolist()]


def _hex(s: str) -> bytes:
    return bytes.fromhex(re.sub(r"\s+", "", s))


def test_registered():
    reg = ppfmt.load_all()
    for key, ext in (("giben_g57", "fdt"), ("giben_gvisionxp", "fdt"), ("giben_gdrive", "zip"),
                     ("kdt_presize_xml", "zip"), ("kdt_ks33x", "zip"), ("kdt_new", "zip")):
        assert reg[key].group == "saw" and reg[key].ext == ext and reg[key].note


def test_pattern_and_layout():
    job = _job()
    (P,) = patterns(job)
    assert (P.dimx, P.dimy, P.off1, P.off2, P.axis) == (1830, 2750, 5, 5, "x")
    assert [(k.size, k.rep) for k in P.kids] == [(1000, 1)]
    assert [(k.size, k.rep, k.uid) for k in P.kids[0].kids] == [(500, 2, 1), (400, 1, 0)]
    assert P.rest is not None and P.rest_raw(KERF) == 1742
    assert layout(P, KERF) == [(1, 5, 5, 505, 1005), (1, 508, 5, 1008, 1005), (2, 1011, 5, 1411, 605)]
    assert leaf_counts(P.kids) == {1: 2, 2: 1}


def test_middle_waste_dropped_and_part_wrapped():
    # polosada: detal, chiqindi, detal — chiqindi yozilmaydi, ikkinchi detal oldinga suriladi;
    # polosa enini to'ldirmagan detal (600×400, polosa 1000) oraliq bo'lakka o'raladi
    strip = SawNode(x=5, y=5, l=1000, w=1820, kind="C", axis="y", children=[
        SawNode(x=5, y=5, l=1000, w=500, kind="P", uid=1),
        SawNode(x=5, y=508, l=1000, w=100, kind="W"),
        SawNode(x=5, y=611, l=600, w=400, kind="P", uid=2)])
    (P,) = patterns(_job([_map([strip], rem=False)]))
    assert P.dropped == 1 and P.rest is None
    assert layout(P, KERF) == [(1, 5, 5, 505, 1005), (2, 508, 5, 908, 605)]


def test_g57():
    name, data = _run("giben_g57", _job())
    assert name == "9001_test_LDSP_OQ.fdt"
    txt = data.decode("ascii")
    assert "\r" not in txt and txt.endswith("[EndOttimizzazioni]\n") and "giblab" not in txt.lower()
    lines = txt.split("\n")[:-1]
    assert len(lines) == 441                                    # hujjatdagi minimal misol
    assert all(ln.startswith("[") or " = " in ln for ln in lines)
    for must in ("MATERIALE = LDSP OQ", "MATERIALE =  LDSP OQ", "SPESSORE = 16000", "SPESSORELAMA = 3000",
                 "XBA = 2750000", "YAL = 1830000", "TOTALESCHEMI = 1", "AREATOTALEPANN = 5033",
                 "AREATOTALEELEM = 1240", "AREATOTALEELEMREC = 3161", "DIMX = 1830000", "DIMY = 2750000",
                 "RIFILO3 = 2000", "RIFILO4 = 2000", "XANGINF = 1831500", "MINIMOSFRIDOX = 30000"):
        assert must in lines, must
    assert txt.count("[StartDatiPannelloFDT1]") == 2 and "[EndPannelloFDT1]" in lines
    els = re.findall(r"IDP = (\d+)\nRUOTATO = 0\nRUOTABILE = -1\nXANGINF = (\d+)\nYANGINF = (\d+)\nXANGSUP = (\d+)\n"
                     r"YANGSUP = (\d+)", txt)
    assert els == [("1", "5000", "5000", "505000", "1005000"), ("1", "508000", "5000", "1008000", "1005000"),
                   ("2", "1011000", "5000", "1411000", "605000")]
    cuts = re.findall(r"QUOTATG = (\d+)\nTIPOTG = (\d)\nLINEATG = 0\nTGUTENTE = -1\nPEZZISTACCATI = 1\nQTARIP = (\d+)", txt)
    assert cuts == [("1000000", "3", "1"), ("500000", "4", "2"), ("400000", "4", "1"), ("600000", "5", "1")]
    ie = re.findall(r"IDP = (\d+)\n(?:.*\n)*?XBA = (\d+)\nYAL = (\d+)\n(?:.*\n)*?IE = (\d+)", txt)
    assert ie[:2] == [("1", "1000000", "500000", "1"), ("2", "600000", "400000", "2")]


def test_g57_sheet_id_param_and_copies():
    job = _job([_map([_strip_doc()], copies=2)], params={"sheet_id": "50"})
    txt = _run("giben_g57", job)[1].decode("ascii")
    assert txt.count("IDL = 50\n") == 2 and "COD = 50\n" in txt
    assert "QTA = 2\n" in txt and "RIPETIZIONI = 2\n" in txt and "FOGLIPACCO = 2\n" in txt


def test_gvisionxp():
    name, data = _run("giben_gvisionxp", _job())
    txt = data.decode("ascii")
    lines = txt.split("\n")[:-1]
    assert name.endswith(".fdt") and len(lines) == 313          # hujjatdagi minimal misol
    assert "SPESSORELAMA" not in txt and "IDP = " not in txt and "[StartTaglio1]" not in txt
    assert "AREATOTALEPANN = 10807500000" in lines and "NUMEROPANN = 2" in lines and "MATERIALE = " in lines
    assert txt.endswith("[EndPannelloFDS1]\n[StartTagli_Ed]\n[EndPannelliFDS]\n[EndOttimizzazione1]\n"
                        "[EndOttimizzazioni]\n")
    g57 = _run("giben_g57", _job())[1].decode("ascii")
    tg = lambda s: re.findall(r"\[StartTg_Ed\d+\]\n(?:.*\n)*?\[EndTg_Ed\d+\]", s)      # noqa: E731
    assert tg(txt) == tg(g57) and len(tg(txt)) == 4


DAX_DOC = """
04 00
FC 37 80 3E FC 67 FC 01 FC 28 FC 00
FF FF FC 32 01 FC 13 FC 01 FC 80 FC 00
89 13 00 00 30 F6 29 00 70 EC 1B 00 01 00 00 00 FC 18 FC 28 04 00 00 00 01 00 00 00 01 00 00 00 FC 44 FC 01 FC 28 FC 00
01 00 00 00 40 42 0F 00 20 A1 07 00 02 00 00 00 FC 18 30 31 5F 30 30 31 20 62 6F 6B FC 1E 01 00 00 00 02 00 00 00
02 00 00 00 FC 44 FC 01 FC 28 FC 00
02 00 00 00 C0 27 09 00 80 1A 06 00 01 00 00 00 FC 18 30 31 5F 30 30 32 20 70 6F 6C 6B 61 FC 1C 01 00 00 00 01 00 00 00
01 00 00 00 FC 44 FC 01 FC 28 FC 00
E7 03 00 00 40 42 0F 00 40 42 0F 00 E8 03 00 00 FC 18 44 4F 52 45 5A 41 54 21 21 21 FC 1E 01 00 00 00 E8 03 00 00
E8 03 00 00 FC 44 FC 01 FC 28 FC 00
"""
CPX_DOC = """
04 00
FF FF 01 00 01 00 00 00 01 00 00 00 70 EC 1B 00 30 F6 29 00 01 FC 4B FC 00
02 00 00 00 70 EC 1B 00 01 00 FC 26 FC 00
03 00 00 00 40 42 0F 00 01 00 FC 26 FC 00
04 00 01 00 20 A1 07 00 02 00 FC 26 FC 00
04 00 00 00 80 1A 06 00 01 00 FC 26 FC 00
05 00 02 00 C0 27 09 00 01 00 FC 26 FC 00
"""


def test_gdrive_doc_example():
    name, data = _run("giben_gdrive", _job())
    assert name == "9001_test_LDSP_OQ.zip"
    (n1, dax), (n2, cpx) = _unzip(data)
    assert (n1, n2) == ("9001_tes.DAX", "9001_tes.CPX")         # 8.3 nom
    assert dax == _hex(DAX_DOC)
    assert cpx == _hex(CPX_DOC)


def test_gdrive_deep_levels_and_names():
    # 5-darajadagi bo'lak yana kesilsa (6-daraja) — 999 «DOREZAT!!!», ichki kesim yozilmaydi
    deep = SawNode(x=5, y=5, l=1000, w=1820, kind="C", axis="y", children=[
        SawNode(x=5, y=5, l=1000, w=900, kind="C", axis="x", children=[
            SawNode(x=5, y=5, l=700, w=900, kind="C", axis="y", children=[
                SawNode(x=5, y=5, l=700, w=450, kind="C", axis="x", children=[
                    SawNode(x=5, y=5, l=600, w=450, kind="C", axis="y", children=[
                        SawNode(x=5, y=5, l=600, w=400, kind="P", uid=2)])])])])])
    job = _job([_map([deep], rem=False)])
    job.parts[0].name = "Фронтальная панель, очень длинное название детали номер один"
    (_, dax), (_, cpx) = _unzip(_run("giben_gdrive", job)[1])
    recs = [cpx[i:i + 14] for i in range(27, len(cpx), 14)]
    assert all(r[10:] == b"\xfc\x26\xfc\x00" for r in recs)
    rows = [struct.unpack("<hhih", r[:10]) for r in recs]
    assert rows == [(2, 0, 1830000, 1), (3, 0, 1000000, 1), (4, 0, 900000, 1), (5, 999, 700000, 1)]
    nm = translit(job.parts[0].name)[:40].encode("ascii")
    assert nm.startswith(b"Frontalynaya panely") and nm in dax and b"\xfc" not in nm
    # 0xFC bayti bor o'lcham (720 mm = 80 FC 0A 00) — sonli maydon xom yoziladi
    job.parts[1].length = 720
    (_, dax2), _ = _unzip(_run("giben_gdrive", job)[1])
    assert struct.pack("<3i", 2, 720000, 400000) in dax2


XML_DOC = """<?xml version="1.0" encoding="UTF-8"?>
<project>
<panel1 l="2750" w="1830" material="LDSP OQ" code="50" thickness="16" saw="3" num="1">
<no.1 l="2750" w="1830" trim="5" x="0" y="0" layer="1" id="0">
<part cut="1000" type="2" id="100" code="" />
<part cut="1742" type="3" id="112" code="O1" />
</no.1>
<no.2 l="1830" w="1742" trim="0" x="0" y="1008" layer="2" id="112">
</no.2>
<no.3 l="1830" w="1000" trim="5" x="0" y="5" layer="2" id="100">
<part cut="500" type="1" id="104" code="1" />
<part cut="500" type="1" id="106" code="1" />
<part cut="400" type="2" id="108" code="" />
</no.3>
<no.4 l="1000" w="400" trim="2.5" x="1011" y="5" layer="3" id="108">
<part cut="600" type="1" id="110" code="2" />
</no.4>
<no.5 l="400" w="600" trim="0" x="1011" y="7.5" layer="4" id="110">
</no.5>
<no.6 l="1000" w="500" trim="0" x="508" y="5" layer="3" id="106">
</no.6>
<no.7 l="1000" w="500" trim="0" x="5" y="5" layer="3" id="104">
</no.7>
</panel1>

<parts>
<part code="1" l="1000" w="500" sq="2" uc="2" rc="0" />
<part code="2" l="600" w="400" sq="1" uc="1" rc="0" />
<part code="O1" l="1742" w="1830" sq="1" uc="1" rc="0" />
</parts>
</project>"""


def test_kdt_xml_doc_example():
    # hujjatdagi misolda 3-qatlam bo'lagi ichida kesim 2.5 mm siljib boshlanadi (`trim="2.5"`)
    job = _job([_map([_strip_doc(lead=2.5)])], params={"sheet_id": "50"})
    assert 'trim="2.5"' not in _unzip(_run("kdt_presize_xml", _job())[1])[0][1].decode()      # bizning kroyda siljish 0
    assert _run("giben_g57", job)[1] == _run("giben_g57", _job(params={"sheet_id": "50"}))[1]  # G57 da ifodalanmaydi
    name, data = _run("kdt_presize_xml", job)
    assert name == "9001_test_LDSP_OQ.zip"
    inner = _unzip(data)
    assert inner[0][0] == "9001_test_LDSP_OQ.xml"
    for n, d in inner[1:]:                                      # etiketka rasmlari — faqat Pillow bo'lsa
        assert n in ("1.emf", "2.emf") and d[:4] == b"\x89PNG"
    txt = inner[0][1].decode("utf-8")
    # ichki id lar — bizning hisoblagich; ota-bola bog'lanishi saqlanishi kerak
    ours = re.findall(r'id="(\d+)"', txt)
    doc = re.findall(r'id="(\d+)"', XML_DOC)
    remap: dict[str, str] = {}
    for a, b in zip(ours, doc):
        assert remap.setdefault(a, b) == b
    assert len(set(remap.values())) == len(remap)
    assert re.sub(r'id="(\d+)"', lambda m: f'id="{remap[m.group(1)]}"', txt) == XML_DOC
    assert "giblab" not in txt.lower()


def test_kdt_xml_mcode_and_escape():
    job = _job()
    job.material_code = "110052"
    job.material_name = 'LDSP "A&B"'
    txt = _unzip(_run("kdt_presize_xml", job)[1])[0][1].decode("utf-8")
    assert 'material="LDSP &quot;A&amp;B&quot;" mcode="110052" code="1"' in txt


def _f32(b, o, n=3):
    return struct.unpack_from("<" + "f" * n, b, o)


@pytest.mark.parametrize("key,new", [("kdt_ks33x", False), ("kdt_new", True)])
def test_kdt_ks33x_doc_example(key, new):
    name, data = _run(key, _job())
    assert name == "9001_test_LDSP_OQ.zip"
    (qn, qk), (ln, lbd) = _unzip(data)
    assert qn == "NUM=1   PANELS( 1 x 1 = 1 ).qk" and ln == "NUM=1   PANELS( 1 x 1 = 1 ).lbd"
    assert len(qk) == (2920032 if new else 2720032)
    assert _f32(qk, 0, 1) == (3.0,)
    ea = 13 if new else 12
    bs = 4 + ea * 20000 + (1 if new else 0)
    want_a = {1: (5.0, 2750.0, 1830.0), 11: (5.0, 1830.0, 1000.0), 101: (0.0, 1000.0, 500.0),
              102: (0.0, 1000.0, 400.0), 1021: (0.0, 400.0, 600.0)}
    want_b = {1: (2750.0, 1830.0), 2: (1000.0, 1), 102: (500.0, 2), 103: (400.0, 1), 1022: (600.0, 1)}
    left = bytearray(qk)
    left[0:4] = bytes(4)
    for i, v in want_a.items():
        o = 4 + ea * i
        assert _f32(qk, o) == v
        assert not new or qk[o + 12] == 1
        left[o:o + ea] = bytes(ea)
    for i, v in want_b.items():
        o = bs + 12 * i
        if i == 1:
            assert struct.unpack_from("<ffi", qk, o) == v + (0,)
        else:
            assert struct.unpack_from("<fii", qk, o) == (v[0], 0, v[1])
        left[o:o + 12] = bytes(12)
    assert left.count(0) == len(left)                           # boshqa nol bo'lmagan bayt yo'q
    if new:
        assert qk[17:30] == _hex("00 00 A0 40 00 E0 2B 45 00 C0 E4 44 01")

    tree = _hex("""00 00 00 02
        01 00 0C D0 9F D0 BE D0 BB D0 BE D1 81 D0 B0 40 8F 40 00 00 00 00 00 00 00 00 01 00 00 00 02
        00 00 0C D0 94 D0 B5 D1 82 D0 B0 D0 BB D1 8C 40 7F 40 00 00 00 00 00 00 00 00 02 00 00 00 01 00 01 31
        40 8F 40 00 00 00 00 00 40 7F 40 00 00 00 00 00 00
        01 00 0C D0 9F D0 BE D0 BB D0 BE D1 81 D0 B0 40 79 00 00 00 00 00 00 00 00 00 01 00 00 00 01
        00 00 0C D0 94 D0 B5 D1 82 D0 B0 D0 BB D1 8C 40 82 C0 00 00 00 00 00 00 00 00 01 00 00 00 02 00 01 32
        40 82 C0 00 00 00 00 00 40 79 00 00 00 00 00 00 00""")
    assert lbd.startswith(tree)                                 # N=2: polosa + qoldiq tuguni
    rest = lbd[len(tree):]
    o = 0
    assert rest[o] == 0
    n = struct.unpack_from(">H", rest, 1)[0]
    assert rest[3:3 + n].decode("utf-8") == "Остаток"
    o = 3 + n
    cut, rep, idx = struct.unpack_from(">dii", rest, o)
    assert (cut, rep, idx) == (1737.0, 1, 3)
    o += 16
    n = struct.unpack_from(">H", rest, o)[0]
    assert rest[o + 2:o + 2 + n].decode("utf-8") == "Д1"
    o += 2 + n
    assert struct.unpack_from(">ddB", rest, o) == (1737.0, 1820.0, 1)
    o += 17
    m = struct.unpack_from(">i", rest, o)[0]
    o += 4
    rows = {}
    for _ in range(m):
        k, n = struct.unpack_from(">iH", rest, o)
        rows[k] = rest[o + 6:o + 6 + n].decode("utf-8").split(",")
        o += 6 + n
    assert rest[o:] == (b"\x00" if new else b"")
    assert list(rows) == [1, 2, 3] and all(len(f) == 31 and f[30] == "" for f in rows.values())
    assert rows[1][:15] == ["detail.fme", "", "2", "1", "1", "9001_test_LDSP_OQ", "1000", "500", "01_001 bok", "2",
                            "A", "", "", "", "true"]
    assert rows[2][:15] == ["detail.fme", "", "1", "2", "1", "9001_test_LDSP_OQ", "600", "400", "01_002 polka", "1",
                            "", "", "", "", "false"]
    assert rows[3][:8] == ["rest.fme", "", "1", "1", "1737", "1820", "3.161", "9001_test_LDSP_OQ"]
    assert b"giblab" not in lbd.lower()


def _three_strips():
    """Uchta bir xil farzandli polosa (300 → detal 2 600×... emas: 400×600 burilgan) + boshqa polosa."""
    kids = []
    x = 5.0
    for _ in range(3):
        kids.append(SawNode(x=x, y=5, l=400, w=1820, kind="C", axis="y", children=[
            SawNode(x=x, y=5, l=400, w=600, kind="P", uid=2, rotated=True),
            SawNode(x=x, y=608, l=400, w=600, kind="P", uid=2, rotated=True)]))
        x += 403
    kids.append(SawNode(x=x, y=5, l=500, w=1820, kind="C", axis="y", children=[
        SawNode(x=x, y=5, l=500, w=1000, kind="P", uid=1, rotated=True)]))
    return kids


def test_kdt_ks33x_reverse_and_book_split():
    from app.services.ppfmt.saw_kdt_ks33x import ks_tree, labels
    job = _job([_map(_three_strips(), rem=False)])
    job.parts[1].qty = 6
    job.parts[0].qty = 1
    (P,) = patterns(job)
    assert [(k.size, k.rep) for k in P.kids] == [(400, 3), (500, 1)]
    nodes = ks_tree(job, P)                    # 1-daraja teskari; 40 / (16 × 1) = 2 → 3 = 2 + 1
    assert [(n["cut"], n["rep"]) for n in nodes] == [(500, 1), (400, 2), (400, 1)]
    assert nodes[1]["ch"][0] == dict(strip=0, typ="Деталь", cut=600.0, rep=2, idx=2, code="2", l=600.0, w=400.0, fl=0)
    job2 = _job([_map(_three_strips(), copies=2, rem=False)])
    (P2,) = patterns(job2)                     # 2 listli kitob: 40 / (16 × 2) = 1 → 1 + 1 + 1
    assert [(n["cut"], n["rep"]) for n in ks_tree(job2, P2)] == [(500, 1), (400, 1), (400, 1), (400, 1)]
    old = dict(labels(job, P, nodes, "t", False))
    new = dict(labels(job, P, nodes, "t", True))
    assert old[2].split(",")[2] == "6" and new[2].split(",")[2] == "6"
    job.parts[1].qty = 12                      # yangi versiyada 2-maydon — shu kartadagi (bitta listdagi) soni
    assert dict(labels(job, P, nodes, "t", False))[2].split(",")[2] == "12"
    assert dict(labels(job, P, nodes, "t", True))[2].split(",")[2] == "6"


def test_kdt_ks33x_label_order_is_hash_order():
    from app.services.ppfmt.saw_kdt_ks33x import ks_tree, labels
    parts = [SawPart(uid=u, name=f"d{u}", code="", length=300, width=100, qty=1, grain=False) for u in (39, 26, 42, 47, 40)]
    kids = []
    y = 5.0
    for p in parts:
        kids.append(SawNode(x=5, y=y, l=300, w=100, kind="P", uid=p.uid))
        y += 103
    strip = SawNode(x=5, y=5, l=300, w=1820, kind="C", axis="y", children=kids)
    job = demo_job(parts, [_map([strip], rem=False)], kerf=KERF, trim=TRIM)
    (P,) = patterns(job)
    keys = [k for k, _ in labels(job, P, ks_tree(job, P), "t", False)]
    assert keys == [39, 40, 26, 42, 47]        # savat = id & 15: 7, 8, 10, 10 (kiritish tartibida), 15


def test_kdt_ks33x_limits():
    kids = []
    y = 5.0
    for _ in range(21):                        # bitta polosada 21 xil kesim (format chegarasi 20)
        kids.append(SawNode(x=5, y=y, l=1000, w=30 + len(kids), kind="C", axis="x", children=[
            SawNode(x=5, y=y, l=600, w=30 + len(kids), kind="P", uid=2)]))
        y += kids[-1].w + 3
    strip = SawNode(x=5, y=5, l=1000, w=1820, kind="C", axis="y", children=kids)
    job = _job([_map([strip], rem=False)])
    with pytest.raises(ValueError):
        _run("kdt_ks33x", job)


@pytest.mark.parametrize("key", ["giben_g57", "giben_gvisionxp", "giben_gdrive", "kdt_presize_xml", "kdt_ks33x",
                                 "kdt_new"])
def test_no_foreign_names_and_empty_job(key):
    name, data = _run(key, _job())
    blobs = [data] + ([d for _, d in _unzip(data)] if data[:2] == b"PK" else [])
    assert all(b"giblab" not in b.lower() for b in blobs)
    job = _job()
    job.maps = []
    ppfmt.load_all()[key].fn(job)              # bo'sh kroy — istisnosiz
