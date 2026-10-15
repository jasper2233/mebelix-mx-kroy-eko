"""O'rnatilgan arra formatlari (ppfmt: Holzma PTX/LC4/SPL, HOMAG, HOMAG CHF, Shelling, Shelling MCS) — sun'iy ishlar bilan.
Korxona fayllari ishlatilmaydi (namunalar bilan tekshiruv — tools/bench/pp_saw_check_holzma.py)."""
from __future__ import annotations

import io
import struct
import zipfile
from datetime import datetime

import pytest

from app.services import ppfmt
from app.services.ppfmt import SawMap, SawNode, SawPart
from app.services.ppfmt import _saw_shelling as SH
from app.services.ppfmt._saw_common import demo_job, job_title, leaves, part_totals, tree_errors
from app.services.ppfmt._saw_homag import parse_pattern

KEYS = ["holzma_ptx", "holzma_cadmatic4", "holzma_cadmatic3", "homag", "homag_chf", "shelling", "shelling_mcs"]


def _parts():
    return [SawPart(uid=1, name="01_001 bok", code="01_001", length=720, width=560, qty=2, grain=False,
                    product="01 shkaf", product_code="900101",
                    edges={"left": dict(symbol="A", name="1-19 Oq", thickness=1.0),
                           "right": dict(symbol="A", name="1-19 Oq", thickness=1.0)}),
            SawPart(uid=2, name="01_002 polka", code="01_002", length=1200, width=400, qty=1, grain=True,
                    product="01 shkaf", product_code="900101",
                    edges={"bottom": dict(symbol="A", name="1-19 Oq", thickness=1.0)})]


def _rip_map(rem: bool = True) -> SawMap:
    """TYPE=0: ildiz Y bo'ylab polosalar (list 2750×1830, trim 2+propil 3 = 5)."""
    root = SawNode(5, 5, 2740, 1820, "C", axis="y", children=[
        SawNode(5, 5, 2740, 560, "C", axis="x", children=[
            SawNode(5, 5, 720, 560, "P", uid=1), SawNode(728, 5, 720, 560, "P", uid=1),
            SawNode(1451, 5, 1294, 560, "W")]),
        SawNode(5, 568, 2740, 400, "C", axis="x", children=[
            SawNode(5, 568, 1200, 400, "P", uid=2), SawNode(1208, 568, 1537, 400, "W")]),
        SawNode(5, 971, 2740, 854, "W", rem=1 if rem else 0)])
    return SawMap(index=1, copies=1, sheet_length=2750, sheet_width=1830, is_remnant=False, sheet_id="s1", tree=root,
                  placements=[], offcuts=[], commands=[], trim_length=2, trim_width=2)


def _head_map(copies: int = 1) -> SawMap:
    """TYPE=2: ildiz X bo'ylab bo'laklar; ichida takrorlanuvchi polosalar va aylantirilgan detal."""
    root = SawNode(5, 5, 2740, 1820, "C", axis="x", children=[
        SawNode(5, 5, 1200, 1820, "C", axis="y", children=[
            SawNode(5, 5, 1200, 560, "C", axis="x", children=[
                SawNode(5, 5, 720, 560, "P", uid=1), SawNode(728, 5, 477, 560, "W")]),
            SawNode(5, 568, 1200, 560, "C", axis="x", children=[
                SawNode(5, 568, 720, 560, "P", uid=1), SawNode(728, 568, 477, 560, "W")]),
            SawNode(5, 1131, 1200, 400, "P", uid=2),
            SawNode(5, 1534, 1200, 291, "W")]),
        SawNode(1208, 5, 560, 1820, "C", axis="y", children=[
            SawNode(1208, 5, 560, 720, "P", uid=1, rotated=True), SawNode(1208, 728, 560, 1097, "W")]),
        SawNode(1771, 5, 974, 1820, "W")])
    return SawMap(index=1, copies=copies, sheet_length=2750, sheet_width=1830, is_remnant=False, sheet_id="s1",
                  tree=root, placements=[], offcuts=[], commands=[], trim_length=2, trim_width=2)


def _lines(data: bytes) -> list[str]:
    assert data.endswith(b"\r\n")
    return data.decode("cp1251").split("\r\n")[:-1]


# ───────────────────────── umumiy ─────────────────────────
def test_registered_saw_formats():
    reg = ppfmt.load_all()
    assert "holzma_ptx" in reg and reg["holzma_ptx"].ext == "ptx"
    for k in KEYS:
        assert k in reg and reg[k].group == "saw", k


@pytest.mark.parametrize("key", KEYS)
def test_no_foreign_program_name_in_any_output(key):
    """Hech bir faylda (zip ichida ham) boshqa dastur nomi yoki uning ichki etiketka fayli bo'lmasin."""
    job = demo_job(_parts(), [_head_map(copies=2)], kerf=3.0, trim=2.0)
    files = ppfmt.load_all()[key].fn(job)
    assert files
    for name, data in files:
        blobs = [(name, data)]
        if data[:2] == b"PK":
            z = zipfile.ZipFile(io.BytesIO(data))
            blobs += [(n, z.read(n)) for n in z.namelist()]
        for n, d in blobs:
            assert "giblab" not in n.lower()
            assert b"giblab" not in d.lower() and "giblab".encode("utf-16-le") not in d.lower()


def test_job_title_no_double_order():
    j = demo_job(_parts(), [_rip_map()], project_name="9001_mijoz", order="9001", material="LDSP  OQ")
    assert job_title(j) == "9001_mijoz_LDSP_OQ"
    j.project_name = "mijoz"
    assert job_title(j) == "9001_mijoz_LDSP_OQ"


def test_demo_trees_valid():
    for m in (_rip_map(), _head_map()):
        assert tree_errors(m.tree, 3.0) == []


# ───────────────────────── Holzma PTX ─────────────────────────
def _ptx(maps, **kw):
    job = demo_job(_parts(), maps, kerf=3.0, trim=2.0, project_name="9001_mijoz", material="LDSP OQ", **kw)
    files = ppfmt.load_all()["holzma_ptx"].fn(job)
    assert len(files) == 1
    return files[0][0], _lines(files[0][1])


def test_ptx_rip_pattern_matches_documented_example():
    name, ln = _ptx([_rip_map()])
    assert name == "9001_mijoz_LDSP_OQ.ptx"
    assert ln[0] == "HEADER,1.13,9001_mijoz_LDSP_OQ,0,0,1"
    assert ln[1] == "JOBS,1,9001 mijoz LDSP OQ,,01.10.2026,01.10.2026,,1,,"
    assert ln[2] == "PARTS_REQ,1,1,01_001 bok,1,720,560,2,0,0,0,2,0,0,0"
    assert ln[3] == "PARTS_REQ,1,2,01_002 polka,1,1200,400,1,0,0,1,1,0,0,0"
    inf = ln[4].split(",")
    assert len(inf) == 31 and inf[10:12] == ["1-19 Oq", "1-19 Oq"] and inf[14:16] == ["A", "A"]
    assert inf[18] == "LDSP OQ" and inf[21] == "01 shkaf" and inf[23] == "900101" and inf[30] == "(CS) LDSP OQ"
    assert ln[6] == "BOARDS,1,1,M1,1,2750,1830,10000,1,0,0,2750 x 2750,LDSP OQ,1"
    assert ln[7] == "MATERIALS,1,1,M1,LDSP OQ,16,2,3,3,5,5,5,5,0,0,0,1,1,1,1,,1"
    assert ln[8:] == [
        "PATTERNS,1,1,1,0,1,1,1,,0,0",
        "CUTS,1,1,1,0,91,5,0,0,0",
        "CUTS,1,1,2,0,1,560,1,0,0",
        "CUTS,1,1,3,0,92,5,0,0,0",
        "CUTS,1,1,4,0,2,720,2,1,2",
        "CUTS,1,1,5,0,1,400,1,0,0",
        "CUTS,1,1,6,0,92,5,0,0,0",
        "CUTS,1,1,7,0,2,1200,1,2,1",
        "OFFCUTS,1,1,Остаток 2740 x 854,1,2750,859,1"]


def test_ptx_head_cut_pattern_repeat_and_book():
    _, ln = _ptx([_head_map(copies=3)])
    pat = [x for x in ln if x.startswith(("PATTERNS", "CUTS"))]
    assert pat == [
        "PATTERNS,1,1,1,2,3,2,2,,0,0",          # 3 list, paket = min(3, 40//16=2)
        "CUTS,1,1,1,0,90,5,0,0,0",
        "CUTS,1,1,2,0,0,1200,1,0,0",
        "CUTS,1,1,3,0,91,5,0,0,0",
        "CUTS,1,1,4,0,1,560,2,0,0",             # ikki bir xil polosa → QTY_RPT=2
        "CUTS,1,1,5,0,2,720,1,1,1",
        "CUTS,1,1,6,0,1,400,1,2,1",             # polosa = detal (to'liq uzunlik)
        "CUTS,1,1,7,0,0,560,1,0,0",
        "CUTS,1,1,8,0,91,5,0,0,0",
        "CUTS,1,1,9,0,1,720,1,1,1"]             # aylantirilgan detal 560×720
    assert not any(x.startswith("OFFCUTS") for x in ln)
    assert "BOARDS,1,1,M1,1,2750,1830,10000,3," in "\n".join(ln)


def test_ptx_quantities_add_up():
    job = demo_job(_parts(), [_head_map(copies=2)], kerf=3.0, trim=2.0)
    assert part_totals(job) == {1: 6, 2: 2}
    _, ln = _ptx([_rip_map(rem=False)])
    assert not any(x.startswith("OFFCUTS") for x in ln)


def test_ptx_middle_waste_kept_as_piece():
    """O'rtadagi chiqindi bo'lagi detalsiz qator sifatida qoladi (keyingi bo'laklar joyi siljimasin)."""
    m = _rip_map(rem=False)
    strip = m.tree.children[0]
    strip.children = [SawNode(5, 5, 720, 560, "P", uid=1), SawNode(728, 5, 100, 560, "W"),
                      SawNode(831, 5, 720, 560, "P", uid=1), SawNode(1554, 5, 1191, 560, "W")]
    _, ln = _ptx([m])
    cuts = [x for x in ln if x.startswith("CUTS")][:6]
    assert cuts[3:6] == ["CUTS,1,1,4,0,2,720,1,1,1", "CUTS,1,1,5,0,2,100,1,0,0", "CUTS,1,1,6,0,2,720,1,1,1"]


def test_ptx_no_foreign_program_name_and_safe_text():
    parts = _parts()
    parts[0].name = "bok, chap"
    job = demo_job(parts, [_rip_map()], kerf=3.0, trim=2.0)
    data = ppfmt.load_all()["holzma_ptx"].fn(job)[0][1]
    assert b"giblab" not in data.lower()
    assert "bok  chap" in data.decode("cp1251")


# ───────────────────────── Holzma LC4 / SPL ─────────────────────────
KERF, TRIM = 4.0, 10.0
OFF = KERF + TRIM            # ildiz zonasi boshi (trim + propil)


def _hz_parts():
    return [
        SawPart(uid=1, name="01_001 bok", code="01_001", length=800, width=400, qty=4, grain=False, product="01 shkaf",
                product_code="900101", xnc_face="900101_01_001", xnc_back="900101_01_001_2", has_drill=True,
                edges={"bottom": dict(symbol="A", name="1-19 Oq", thickness=1.0),
                       "right": dict(symbol="B", name="2-19 Oq", thickness=2.0)}),
        SawPart(uid=2, name="01_002 polka", code="01_002", length=600, width=300, qty=2, grain=True, product="01 shkaf",
                product_code="900101"),
        SawPart(uid=3, name="01_003 sokl", code="01_003", length=2042, width=100, qty=2, grain=False),
    ]


def _hz_tree():
    """List 2800×2070, ildiz X bo'ylab: [polosa 800: 2×(800×400), 600×300 burilgan emas → ichki bo'lak] [100 × 2042 — 1-daraja
    detal (burilgan)] [chiqindi 50 — o'rtada] [qoldiq]."""
    W = 2070 - 2 * OFF
    s1 = SawNode(x=OFF, y=OFF, l=800, w=W, kind="C", axis="y", children=[
        SawNode(x=OFF, y=OFF, l=800, w=400, kind="P", uid=1),
        SawNode(x=OFF, y=OFF + 404, l=800, w=400, kind="P", uid=1),
        SawNode(x=OFF, y=OFF + 808, l=800, w=300, kind="C", axis="x", children=[
            SawNode(x=OFF, y=OFF + 808, l=600, w=300, kind="P", uid=2),
            SawNode(x=OFF + 604, y=OFF + 808, l=196, w=300, kind="W"),
        ]),
        SawNode(x=OFF, y=OFF + 1112, l=800, w=W - 1112, kind="W"),
    ])
    p3 = SawNode(x=OFF + 804, y=OFF, l=100, w=W, kind="P", uid=3, rotated=True)
    waste = SawNode(x=OFF + 908, y=OFF, l=50, w=W, kind="W")
    rem = SawNode(x=OFF + 962, y=OFF, l=2800 - 2 * OFF - 962, w=W, kind="W", rem=1)
    return SawNode(x=OFF, y=OFF, l=2800 - 2 * OFF, w=W, kind="C", axis="x", children=[s1, p3, waste, rem])


def _hz_job(tree=None, copies=2, **kw):
    t = tree or _hz_tree()
    m = SawMap(index=1, copies=copies, sheet_length=2800, sheet_width=2070, is_remnant=False, sheet_id="s1", tree=t,
               placements=[], offcuts=[dict(number=1, x=OFF + 962, y=OFF, length=1810, width=2042, business=True,
                                            kind="remnant")], commands=[])
    return demo_job(_hz_parts(), [m], kerf=KERF, trim=TRIM, **kw)


# ───────────────────────── LC4: kichik o'quvchi ─────────────────────────
class _LC4:
    def __init__(self, b):
        self.b, self.i = b, 0

    def tag(self, t):
        v = struct.unpack_from("<H", self.b, self.i)[0]
        self.i += 2
        assert v == t, (hex(v), hex(t), self.i)

    def boolean(self):
        self.tag(1)
        self.i += 1
        return bool(self.b[self.i - 1])

    def num(self, t, fmt, n):
        self.tag(t)
        self.i += n
        return struct.unpack_from(fmt, self.b, self.i - n)[0]

    def i16(self): return self.num(5, "<h", 2)
    def i32(self): return self.num(6, "<i", 4)

    def obj(self, ver=1):
        assert self.boolean() and self.i16() == ver

    def string(self):
        self.tag(0x0D)
        assert self.boolean()
        self.tag(0x0E)
        n = self.i32()
        self.i += n
        return self.b[self.i - n:self.i].decode("utf-8")

    def dec(self):
        self.tag(0x0F)
        assert self.i16() == 1
        v = self.num(8, "<q", 8) / 100000
        assert not self.boolean()
        return v

    def enum(self, t):
        self.tag(t)
        return self.i32()

    def lst(self, fn):
        self.obj()
        return [fn() for _ in range(self.i32())]

    def item(self):
        self.obj()
        assert self.i16() == 2
        r = dict(id=self.string(), fme=self.string(), fme2=self.string(), L=self.dec(), W=self.dec(), T=self.dec(),
                 q1=self.i32(), q2=self.i32(), grain=self.enum(0x13))
        assert not self.boolean()
        r["map"] = self.lst(lambda: (self.obj(), self.string(), self.string())[1:])
        assert not self.boolean()
        return r

    def node(self, root=False):
        self.obj()
        if root:
            assert self.i16() == 1
        r = dict(name=self.string(), n2=self.string(), size=self.dec(), rep=self.i32(), kind=self.enum(0x11),
                 sub=self.enum(0x12))
        assert self.i16() == 1
        r["info"] = None
        if self.i32():
            self.obj()
            r["info"] = dict(a=self.i32(), rot=self.boolean(), label=self.string(), c=self.boolean(),
                             e14=self.enum(0x14), ref=self.i32())
        assert self.lst(lambda: None) == []
        r["kids"] = self.lst(self.node)
        if root:
            r.update(W=self.dec(), x1=self.i32(), x2=self.i32(), mat=self.string())
            assert self.i16() == 1
            r.update(e10=self.enum(0x10), fb=self.boolean(),
                     params=self.lst(lambda: (self.obj(2), self.string(), self.string(), self.boolean())[1:]))
        return r

    def file(self):
        self.obj()
        r = dict(job=self.string(), order=self.string(), parts=self.lst(self.item), boards=self.lst(self.item))
        assert self.lst(lambda: None) == []
        r["patterns"] = self.lst(lambda: self.node(True))
        assert self.i == len(self.b)
        return r


def _lc4(job):
    files = ppfmt.load_all()["holzma_cadmatic4"].fn(job)
    assert len(files) == 1
    return files[0][0], files[0][1], _LC4(files[0][1]).file()


def test_lc4_registered():
    f = ppfmt.load_all()["holzma_cadmatic4"]
    assert f.group == "saw" and f.ext == "LC4"


def test_lc4_header_parts_boards():
    name, data, r = _lc4(_hz_job())
    assert name == "9001_test_LDSP_OQ.LC4"
    assert b"GibLab" not in data and "GibLab".encode("utf-16-le") not in data
    assert r["job"] == "9001_test_LDSP_OQ" and r["order"] == "9001 test"
    assert [p["id"] for p in r["parts"]] == ["Д1", "Д2", "Д3", "Д1"]            # 3 detal + 1 qoldiq
    p1 = r["parts"][0]
    assert (p1["L"], p1["W"], p1["T"], p1["q1"], p1["q2"], p1["grain"]) == (800, 400, 16, 4, 4, 0)
    assert r["parts"][1]["grain"] == 2
    f = p1["fme"].split(",")
    assert len(f) == 31 and f[0] == "detail.fme" and f[2] == "4" and f[3] == "1" and f[5] == "9001_test_LDSP_OQ"
    assert f[6:10] == ["800", "400", "01_001 bok", "4"]
    assert f[10:15] == ["", "B", "", "A", "false"]                             # kromka belgilari l, r, t, b; tekstura
    assert f[30] == "" and p1["fme"] == p1["fme2"]                             # etiketka blobi yozilmaydi
    m = dict(p1["map"])
    assert m["AddInfo_001"] == "LDSP OQ" and m["AddInfo_002"] == "M1" and m["AddInfo_009"] == "01_001 bok"
    assert m["AddInfo_010"] == "01_001" and m["AddInfo_011"] == "1" and m["AddInfo_014"] == "true"
    assert m["AddInfo_015"] == "900101_01_001" and m["AddInfo_016"] == "900101_01_001_2"
    assert m["Edge_MaterialFront"] == "(A) 1-19 Oq" and m["Edge_MaterialRight"] == "(B) 2-19 Oq"
    assert m["PartFinishedLength"] == "800.0" and m["PartFinishedWidth"] == "400.0"
    keys = [k for k, _ in p1["map"]]
    assert keys.index("Edge_MaterialRight") < keys.index("AddInfo_016") < keys.index("AddInfo_002")
    assert keys[0] == "AddInfo_010" and keys[-1] == "AddInfo_009"
    assert "AddInfo_015" not in dict(r["parts"][1]["map"])
    rest = r["parts"][3]
    assert rest["q1"] == 0 and (rest["L"], rest["W"]) == (1810, 2042)
    assert rest["fme"].startswith("rest.fme,,1,1,1810,2042,3.696,9001_test_LDSP_OQ,") and len(rest["fme"].split(",")) == 31
    b = r["boards"]
    assert len(b) == 1 and b[0]["id"] == "1" and b[0]["fme"] == "LDSP OQ" and (b[0]["L"], b[0]["W"]) == (2800, 2070)
    assert b[0]["q1"] == 2 and b[0]["map"] == []


def test_lc4_tree():
    _, _, r = _lc4(_hz_job())
    root = r["patterns"][0]
    assert root["name"] == "00001" and root["size"] == 2800 and root["W"] == 2070 and (root["kind"], root["sub"]) == (1, 1)
    assert root["info"] == dict(a=0, rot=False, label="", c=True, e14=3, ref=0)
    assert root["x1"] == root["x2"] == 2 and root["mat"] == "LDSP OQ"
    par = {k: v for k, v, _ in root["params"]}
    assert par["SaegeblattStaerke"] == "4" and par["AnschnittLinks"] == "14.0" and par["AnschnittOben"] == "14.0"
    kids = root["kids"]
    sig = [(k["size"], k["rep"], k["kind"], k["sub"]) for k in kids]
    # trim, kerf, polosa 800, kerf, [1-daraja detal o'ralgan] polosa 100, kerf, o'rtadagi chiqindi 50, kerf, qoldiq, kerf
    assert sig == [(10, 1, 4, 4), (4, 1, 2, 4), (800, 1, 0, 0), (4, 1, 2, 4), (100, 1, 0, 0), (4, 1, 2, 4),
                   (50, 1, 0, 0), (4, 1, 2, 4), (2800 - (OFF + 962), 0, 10, 0), (4, 1, 2, 4)]
    s1 = kids[2]["kids"]
    assert [(k["size"], k["rep"], k["kind"]) for k in s1] == [(10, 1, 4), (4, 1, 2), (400, 2, 11), (4, 1, 2), (300, 1, 0),
                                                             (4, 1, 2)]
    assert s1[2]["info"] == dict(a=1, rot=False, label="Part", c=True, e14=1, ref=0)
    inner = s1[4]["kids"]                                   # 2-darajadan chuqurda trim yo'q; oxirgi chiqindi yozilmaydi
    assert [(k["size"], k["rep"], k["kind"]) for k in inner] == [(600, 1, 11), (4, 1, 2)]
    assert inner[0]["info"]["ref"] == 1
    wrap = kids[4]["kids"]                                  # 1-darajadagi detal: polosa ichida trim + detal (list eni bo'ylab)
    assert [(k["size"], k["kind"]) for k in wrap] == [(10, 4), (4, 2), (2042, 11), (4, 2)]
    assert wrap[2]["info"]["rot"] is True and wrap[2]["info"]["ref"] == 2
    assert kids[6]["kids"] == []
    assert kids[8]["info"] == dict(a=1, rot=False, label="Rest", c=True, e14=1, ref=3)


def test_lc4_rotated_card_and_counts():
    """Ildiz Y bo'ylab (karta burilgan): 1-daraja o'lchamlari list eni bo'ylab; detal `rot` = karta XOR detal burilishi."""
    L = 2800 - 2 * OFF
    strip = SawNode(x=OFF, y=OFF, l=L, w=400, kind="C", axis="x", children=[
        SawNode(x=OFF + i * 804, y=OFF, l=800, w=400, kind="P", uid=1) for i in range(3)])
    strip2 = SawNode(x=OFF, y=OFF + 404, l=L, w=600, kind="C", axis="x", children=[
        SawNode(x=OFF, y=OFF + 404, l=300, w=600, kind="P", uid=2, rotated=True)])
    root = SawNode(x=OFF, y=OFF, l=L, w=2070 - 2 * OFF, kind="C", axis="y", children=[strip, strip2])
    _, _, r = _lc4(_hz_job(root, copies=1))
    p = r["patterns"][0]
    assert p["info"]["rot"] is True and p["size"] == 2800
    k = p["kids"]
    assert [(x["size"], x["kind"]) for x in k] == [(10, 4), (4, 2), (400, 0), (4, 2), (600, 0), (4, 2)]
    part = k[2]["kids"][2]
    assert (part["size"], part["rep"], part["kind"]) == (800, 3, 11) and part["info"]["rot"] is True
    assert k[4]["kids"][2]["info"]["rot"] is False          # list bo'yicha burilgan detal burilgan kartada — False
    assert len(r["parts"]) == 3                             # qoldiq yo'q


# ───────────────────────── SPL ─────────────────────────
def _spl_parse(data):
    i, recs = 0, []
    while i < len(data):
        n, lv = struct.unpack_from(">HH", data, i)
        assert data[i + 6:i + 11] == b"\x30\x21\x00\x00\x00"
        t = chr(data[i + 11])
        p = data[i + 12:i + 12 + n]
        i += 12 + n
        link = None
        if t in "cf" or (t == "x" and i < len(data)):
            link = struct.unpack_from(">I", data, i)[0]
            i += 4
        recs.append((t, lv, p, link))
    return recs


def _be(b, o):
    return struct.unpack_from(">I", b, o)[0]


def test_spl_structure():
    f = ppfmt.load_all()["holzma_cadmatic3"]
    assert f.group == "saw" and f.ext == "SPL"
    job = _hz_job()
    (name, data), = f.fn(job)
    assert name == "9001_tes.SPL" and b"GibLab" not in data
    recs = _spl_parse(data)
    assert [r[0] for r in recs[:4]] == ["c", "d", "e", "f"] and recs[-1][0] == "x" and recs[-1][3] is None
    c, d, e, fr = (recs[i][2] for i in range(4))
    assert len(c) == 52 and _be(c, 8) == 1 and _be(c, 12) == 5
    assert recs[0][3] == len(data) - (12 + 52 + 4)                      # c link = 1-blok uzunligi
    assert len(d) == 131 and d[18:21] == b"001" and _be(d, 24) == 0 and _be(d, 28) == _be(d, 32) == 2
    assert (_be(d, 36), _be(d, 40), _be(d, 44)) == (28000000, 20700000, 160000)
    assert struct.unpack_from(">HH", d, 74) == (2, 1)
    assert len(e) == 460 and all(_be(e, o) == 40000 for o in (228, 288, 380, 384))
    assert all(_be(e, o) == 100000 for o in (32, 36, 40, 44))
    nodes = [(lv, int.from_bytes(p[3:8], "big"), _be(p, 8) / 1e4, p[19]) for t, lv, p, _ in recs if t == "n"]
    assert nodes == [(1, 0, 2800, 0), (2, 0, 800, 0), (3, 1, 400, 99), (3, 1, 400, 99), (3, 0, 300, 0), (4, 2, 600, 99),
                     (2, 0, 100, 0), (3, 3, 2042, 99)]                 # qoldiq va oxirgi chiqindi yozilmaydi
    assert all(p[2] == lv - 1 and p[:2] == b"\x00\x80" and p[12] == 4 for t, lv, p, _ in recs if t == "n")
    assert _be(fr, 12) == 5 and _be(fr, 20) == 4 * 2 and recs[3][3] == 41 * len(nodes) + 12
    assert _be(fr, 16) + _be(fr, 28) == 4 and _be(fr, 28) == 4          # bo'sh maydon ≥ 4 m²


def test_spl_rotated_two_patterns_and_depth_limit():
    L = 2800 - 2 * OFF
    strip = SawNode(x=OFF, y=OFF, l=L, w=400, kind="C", axis="x", children=[
        SawNode(x=OFF + i * 804, y=OFF, l=800, w=400, kind="P", uid=1) for i in range(3)])
    root = SawNode(x=OFF, y=OFF, l=L, w=2070 - 2 * OFF, kind="C", axis="y", children=[strip])
    job = _hz_job(root, copies=1)
    job.maps.append(SawMap(index=2, copies=3, sheet_length=2800, sheet_width=2070, is_remnant=False, sheet_id="s1",
                           tree=_hz_tree(), placements=[], offcuts=[], commands=[]))
    (_, data), = ppfmt.load_all()["holzma_cadmatic3"].fn(job)
    recs = _spl_parse(data)
    ds = [p for t, _, p, _ in recs if t == "d"]
    assert [d[18:21] for d in ds] == [b"001", b"002"] and [_be(d, 24) for d in ds] == [1, 0]
    assert _be(recs[0][2], 8) == 2
    first = [(lv, int.from_bytes(p[3:8], "big"), _be(p, 8) / 1e4) for t, lv, p, _ in recs if t == "n"][:5]
    assert first == [(1, 0, 2070), (2, 0, 400), (3, 1, 800), (3, 1, 800), (3, 1, 800)]
    xs = [r for r in recs if r[0] == "x"]
    assert xs[0][3] is not None and xs[1][3] is None                    # oxirgi blokda link yo'q
    # chuqurlik > 4 kesish darajasi — xato
    n = SawNode(x=OFF, y=OFF, l=100, w=100, kind="P", uid=1)
    for k in range(5):
        ax = "x" if k % 2 else "y"
        n = SawNode(x=OFF, y=OFF, l=100 + 50 * (k + 1), w=100 + 50 * (k + 1), kind="C", axis=ax, children=[
            n, SawNode(x=OFF, y=OFF, l=40, w=40, kind="P", uid=2)])
    deep = SawNode(x=OFF, y=OFF, l=L, w=2070 - 2 * OFF, kind="C", axis="x", children=[n])
    with pytest.raises(ValueError):
        ppfmt.load_all()["holzma_cadmatic3"].fn(_hz_job(deep))


# ───────────────────────── HOMAG / HOMAG CHF ─────────────────────────
def _hp(uid, l, w, qty, grain=False):
    return SawPart(uid=uid, name=f"d{uid}", code=f"{uid:03d}", length=l, width=w, qty=qty, grain=grain)


def _N(kind, x, y, l, w, axis="", ch=(), uid=0, rot=False, rem=0):
    return SawNode(x=x, y=y, l=l, w=w, kind=kind, axis=axis, children=list(ch), uid=uid, rotated=rot, rem=rem)


def _homag_doc_job(copies=1):
    """Hujjatdagi (homag-zip.md §5) misol: list 2750×1830×16, trim 2, propil 3 — bizning daraxt ko'rinishida."""
    k = 3
    s1 = _N("C", 5, 5, 1900, 1820, "y", [
        _N("P", 5, 5, 1900, 347, uid=1),
        _N("P", 5, 5 + 347 + k, 1900, 347, uid=1),
        _N("C", 5, 5 + 2 * (347 + k), 1900, 560, "x", [
            _N("P", 5, 705, 900, 560, uid=2), _N("P", 908, 705, 900, 560, uid=2), _N("W", 1811, 705, 94, 560)]),
        _N("W", 5, 1268, 1900, 557)])
    s2 = _N("C", 1908, 5, 800, 1820, "y", [
        _N("C", 1908, 5, 800, 600, "x", [
            _N("C", 1908, 5, 400, 600, "y", [_N("P", 1908, 5, 400, 300, uid=3), _N("W", 1908, 308, 400, 297)]),
            _N("W", 2311, 5, 397, 600)]),
        _N("W", 1908, 608, 800, 1217, rem=1)])
    root = _N("C", 5, 5, 2740, 1820, "x", [s1, s2, _N("W", 2711, 5, 34, 1820)])
    m = SawMap(index=1, copies=copies, sheet_length=2750, sheet_width=1830, is_remnant=False, sheet_id="s1", tree=root,
               placements=[], offcuts=[], commands=[], trim_length=2, trim_width=2)
    parts = [_hp(1, 1900, 347, 2 * copies), _hp(2, 900, 560, 2 * copies, grain=True), _hp(3, 400, 300, copies)]
    return demo_job(parts, [m], kerf=3, trim=2, material="LDSP OQ", project_name="0001_mijoz", order="0001")


HOMAG_DOC = ("#REMARK,0001 mijoz,LDSP OQ,\r\n#DIMENSION,2750,1830,16,0,\r\n#SPEEDS,0.00,0.00,0.00,0.00,\r\n"
             "#TRIMS,2.0,2.0,0.0,0.0,0,\r\n"
             "#CUT,1,1900,1,0,0,0,0,0,0.00000,0,0,0,0,\r\n#CUT,2,347,2,0,0,0,0,0,0.00000,0,0,0,0,\r\n"
             "#CUT,2,560,1,0,0,0,0,0,0.00000,0,0,0,0,\r\n#CUT,3,900,2,0,0,0,0,0,0.00000,0,0,0,0,\r\n"
             "#CUT,1,800,1,0,0,0,0,0,0.00000,0,0,0,0,\r\n#CUT,2,600,1,0,0,0,0,0,0.00000,0,0,0,0,\r\n"
             "#CUT,3,400,1,0,0,0,0,0,0.00000,0,0,0,0,\r\n#CUT,7,300,1,0,0,0,0,0,0.00000,0,0,0,0,\r\n").encode()


def _unzip(files):
    assert len(files) == 1 and files[0][0].endswith(".zip")
    z = zipfile.ZipFile(io.BytesIO(files[0][1]))
    return files[0][0], [(i.filename, z.read(i)) for i in z.infolist()]


def test_homag_pattern_matches_documented_example():
    ppfmt.load_all()
    name, inner = _unzip(ppfmt.REGISTRY["homag"].fn(_homag_doc_job()))
    assert name == "0001_mijoz_LDSP_OQ.zip"
    assert [n for n, _ in inner] == ["pattern.001"]
    assert inner[0][1] == HOMAG_DOC
    assert b"GibLab" not in inner[0][1]


def test_homag_roundtrip_parts_and_kerf():
    ppfmt.load_all()
    _, inner = _unzip(ppfmt.REGISTRY["homag_chf"].fn(_homag_doc_job()))
    d = parse_pattern(inner[0][1], kerf=3)
    got = sorted(tuple(sorted((n.l, n.w))) for n in leaves(d["tree"]))
    assert got == [(300, 400), (347, 1900), (347, 1900), (560, 900), (560, 900)]
    from app.services.ppfmt._saw_common import tree_errors
    assert tree_errors(d["tree"], 3) == []


def test_homag_books_vs_chf_sheets():
    """HOMAG: bir xil kartali listlar paketga (40/16 → 2 list) — 3 list = 2 fayl; CHF: har list alohida fayl."""
    ppfmt.load_all()
    job = _homag_doc_job(copies=3)
    _, inner = _unzip(ppfmt.REGISTRY["homag"].fn(job))
    assert [n for n, _ in inner] == ["pattern.001", "pattern.002"] and inner[0][1] == inner[1][1]
    _, inner = _unzip(ppfmt.REGISTRY["homag_chf"].fn(job))
    assert len(inner) == 3


def test_homag_rotated_sheet_and_strip_leaf():
    """1-daraja o'qi y bo'lsa D1 = list eni; 1-darajali barg (polosaning o'zi detal) 2-daraja kesimi bilan yoziladi."""
    ppfmt.load_all()
    root = _N("C", 5, 5, 2740, 1820, "y", [
        _N("P", 5, 5, 2740, 600, uid=1),
        _N("C", 5, 608, 2740, 500, "x", [_N("P", 5, 608, 1000, 500, uid=2), _N("P", 1008, 608, 1000, 500, uid=3),
                                         _N("W", 2011, 608, 734, 500)]),
        _N("W", 5, 1111, 2740, 714)])
    m = SawMap(index=1, copies=1, sheet_length=2750, sheet_width=1830, is_remnant=False, sheet_id="s1", tree=root,
               placements=[], offcuts=[], commands=[], trim_length=2, trim_width=2)
    job = demo_job([_hp(1, 2740, 600, 1), _hp(2, 1000, 500, 1), _hp(3, 1000, 500, 1)], [m], kerf=3, trim=2)
    _, inner = _unzip(ppfmt.REGISTRY["homag_chf"].fn(job))
    txt = inner[0][1].decode()
    rows = [r.split(",")[1:4] for r in txt.split("\r\n") if r.startswith("#CUT")]
    assert "#DIMENSION,1830,2750,16,0," in txt
    # turli detallar (uid 2 va 3) bir xil o'lchamda bo'lsa ham alohida qator (namunalardagi kabi)
    assert rows == [["1", "600", "1"], ["2", "2740", "1"], ["1", "500", "1"], ["2", "1000", "1"], ["2", "1000", "1"]]


def test_homag_depth_limit():
    ppfmt.load_all()

    def deep(lv, x, y, l, w, ax):
        if lv == 0:
            return _N("P", x, y, l, w, uid=1)
        a = _N("C", x, y, l, w, ax)
        cl, cw = (l / 2, w) if ax == "x" else (l, w / 2)
        a.children = [deep(lv - 1, x, y, cl, cw, "y" if ax == "x" else "x"), _N("W", x + (cl if ax == "x" else 0),
                                                                              y + (cw if ax == "y" else 0), cl, cw)]
        return a
    root = deep(6, 5, 5, 2740, 1820, "x")
    m = SawMap(index=1, copies=1, sheet_length=2750, sheet_width=1830, is_remnant=False, sheet_id="s1", tree=root,
               placements=[], offcuts=[], commands=[], trim_length=2, trim_width=2)
    job = demo_job([_hp(1, 42.8, 56.9, 1)], [m])
    with pytest.raises(ValueError):
        ppfmt.REGISTRY["homag_chf"].fn(job)


# ───────────────────────── Shelling / Shelling MCS ─────────────────────────
def _sh_parts():
    return [SawPart(uid=1, name="01_001 bok", code="01_001", length=720, width=560, qty=2, grain=True, product="01 shkaf",
                    edges={"bottom": dict(symbol="A", name="PVC", thickness=1.0),
                           "left": dict(symbol="A", name="PVC", thickness=1.0)}, xnc_face="900101_01_001"),
            SawPart(uid=2, name="01_002 polka", code="01_002", length=564, width=300, qty=3, grain=False,
                    product="01 shkaf")]


def _sh_tree_k():
    """K karta (list 2750×1830, trim 5, propil 3): X01 720 (2×560 + a01 300 → 564), X02 300 (2×564 burilgan), qoldiq."""
    N = SawNode
    x01 = N(5, 5, 720, 1820, "C", "y", children=[
        N(5, 5, 720, 560, "P", uid=1), N(5, 568, 720, 560, "P", uid=1),
        N(5, 1131, 720, 300, "C", "x", children=[N(5, 1131, 564, 300, "P", uid=2), N(572, 1131, 153, 300, "W")]),
        N(5, 1434, 720, 391, "W")])
    x02 = N(728, 5, 300, 1820, "C", "y", children=[
        N(728, 5, 300, 564, "P", uid=2, rotated=True), N(728, 572, 300, 564, "P", uid=2, rotated=True),
        N(728, 1139, 300, 686, "W")])
    root = N(5, 5, 2740, 1820, "C", "x", children=[x01, x02, N(1031, 5, 1714, 1820, "W", rem=1)])
    return root


def _sh_job(tree, copies=1, **kw):
    m = SawMap(index=1, copies=copies, sheet_length=2750, sheet_width=1830, is_remnant=False, sheet_id="s1", tree=tree,
               placements=[], offcuts=[], commands=[])
    job = demo_job(_sh_parts(), [m], kerf=3, trim=2, **kw)
    job.stock = [dict(id="s1", length=2750, width=1830, qty=10000, is_remnant=False)]
    return job


def _sh_members(job, mcs=False):
    files = ppfmt.load_all()["shelling_mcs" if mcs else "shelling"].fn(job)
    assert len(files) == 1
    name, data = files[0]
    z = zipfile.ZipFile(io.BytesIO(data))
    return name, {n: z.read(n).decode("cp1251") for n in z.namelist()}, data


def test_shelling_basic_layout():
    name, mem, raw = _sh_members(_sh_job(_sh_tree_k()))
    assert name == "9001_test_LDSP_OQ.l.zip"
    assert sorted(mem) == ["0000.ncl", "0001.ncp"]           # etiketka fayli yozilmaydi
    assert b"giblab" not in raw.lower() and all("giblab" not in v.lower() for v in mem.values())
    ncl = mem["0000.ncl"]
    assert ncl.endswith("S$\r\n")
    lines = ncl.split("\r\n")[:-1]
    widths = {"S 01": 67, "S 46": 75, "B 01": 99, "P 09": 45, "F 80": 159}
    for l in lines:
        if l[:4] in widths:
            assert len(l) == widths[l[:4]], l
    f01 = [l for l in lines if l.startswith("F 01")]
    assert [len(l) for l in f01] == [312, 312, 154]
    assert f01[0][61:69] == "00720000" and f01[0][118] == "0" and f01[0][17:23] == "000002"
    assert f01[0][155:175].strip() == "900101_01_001" and f01[0][284:293] == "000000001"
    assert f01[1][118] == "1"
    assert f01[2][61:69] == "01714000" and f01[2][70:78] == "01820000" and f01[2][97:104] == "Ostatok"
    f80 = [l for l in lines if l.startswith("F 80")]
    assert f80[0][46:67].strip() == "(A) 1" and f80[0][88:109].strip() == "(A) 1" and f80[0][67:88].strip() == ""
    ncp = mem["0001.ncp"].split("\r\n")[:-1]
    assert ncp[:4] == ["P 01 0001 0001 000001 0 0 0000 0", "P 02 01 0001 0001 00000000 001",
                       "P 03 00 0 00 00000000 02750000 01830000 02750000 01830000", "P 98 0 0 0"]
    assert ncp[4:] == ["C K01 T   00005000 001", "C K01 X01 00720000 001", "C X01 T   00005000 001",
                       "C X01     00560000 002 0 0001", "C X01 a01 00300000 001", "C a01     00564000 001 0 0002",
                       "C K01 X02 00300000 001", "C X02 T   00005000 001", "C X02     00564000 002 0 0002",
                       "C K01 R   00000000 000 0 0001", "P$"]


def test_shelling_runs_and_books():
    _, mem, _ = _sh_members(_sh_job(_sh_tree_k(), copies=2))
    ncp = mem["0001.ncp"].split("\r\n")
    assert ncp[0] == "P 01 0001 0001 000002 0 0 0000 0" and ncp[1] == "P 02 01 0001 0002 00000000 001"
    rem = [l for l in mem["0000.ncl"].split("\r\n") if l.startswith("F 01") and l[15] == "1"]
    assert rem[0][17:23] == "000002"                       # qoldiq soni = listlar soni
    assert SH._books(3, 2) == (3, 1) and SH._books(4, 2) == (2, 2) and SH._books(1, 2) == (1, 1)


def test_shelling_rip_first_and_repeats():
    """L karta (ildiz o'qi y) va bir xil polosalar takrori (soni 002)."""
    N = SawNode
    strip = lambda y: N(5, y, 2740, 300, "C", "x", children=[N(5, y, 564, 300, "P", uid=2), N(572, y, 2173, 300, "W")])
    root = N(5, 5, 2740, 1820, "C", "y", children=[strip(5), strip(308), N(5, 611, 2740, 1214, "W")])
    job = _sh_job(root)
    job.parts[1].qty = 2
    _, mem, _ = _sh_members(job)
    ncp = mem["0001.ncp"].split("\r\n")
    assert ncp[2] == "P 03 00 0 00 00000000 01830000 02750000 01830000 02750000"
    assert ncp[4:9] == ["C L01 T   00005000 001", "C L01 X01 00300000 002", "C X01 T   00005000 001",
                        "C X01     00564000 001 0 0002", "P$"]


def test_shelling_same_axis_group_and_inner_waste():
    """Ota bilan bir o'qdagi ichki guruh ochiladi; o'rtadagi chiqindi — bo'sh polosa."""
    N = SawNode
    inner = N(5, 5, 1500, 1820, "C", "x", children=[
        N(5, 5, 720, 1820, "C", "y", children=[N(5, 5, 720, 560, "P", uid=1)]),
        N(728, 5, 100, 1820, "W"),
        N(831, 5, 300, 1820, "C", "y", children=[N(831, 5, 300, 564, "P", uid=2)])])
    root = N(5, 5, 2740, 1820, "C", "x", children=[inner, N(1508, 5, 1237, 1820, "W")])
    _, mem, _ = _sh_members(_sh_job(root))
    c = [l for l in mem["0001.ncp"].split("\r\n") if l.startswith("C K01")]
    assert c == ["C K01 T   00005000 001", "C K01 X01 00720000 001", "C K01 X02 00100000 001",
                 "C K01 X03 00300000 001"]


def test_shelling_mcs_date_and_id():
    job = _sh_job(_sh_tree_k())
    job.order_date, job.ready_date = "2026-09-01", "2026-09-20"
    _, mem, _ = _sh_members(job, mcs=True)
    f = [l for l in mem["0000.ncl"].split("\r\n") if l.startswith("F 01")][0]
    assert f[294:304] == "2026.09.01"
    _, mem2, _ = _sh_members(job)
    f2 = [l for l in mem2["0000.ncl"].split("\r\n") if l.startswith("F 01")][0]
    assert f2[294:304] == "2026.09.20"
    t, files = SH.build(job, gid="1a2b000001a0e33b80ab", export=datetime(2026, 10, 4))
    s01 = dict(files)["0000.ncl"].decode().split("\r\n")[0]
    assert s01 == "S 01 001 001 9001_test_LDSP_OQ    2026-10-04 0 1a2b000001a0e33b80ab"
    gid = SH.make_id(0x01a0e33b80ab)
    assert len(gid) == 20 and gid.endswith("000001a0e33b80ab")


def test_shelling_title_rules():
    job = _sh_job(_sh_tree_k())
    job.material_name = "LDSP UD (110197)_diffuse"
    assert SH.zip_title(job) == "9001_test_LDSP_UD_110197__diffuse"
    job.material_name = "LDSP  UD "
    assert SH.zip_title(job) == "9001_test_LDSP_UD_"
    job.project_name = "mijoz"
    assert SH.zip_title(job).startswith("9001_mijoz_")
