"""Scheer va KDT PreSize V3.3.0P arra formatlari + 8 belgili dastur nomlari (Holzma SPL, Giben GDrive, Biesse NC300) —
sun'iy ish bilan. Kutilgan qiymatlar docs/mebelix/postprocessors/{scheer,kdt-presize-qk-v3}.md dagi qoidalardan
(korxona fayllarisiz)."""
from __future__ import annotations

import io
import struct
import zipfile

import pytest

from app.services import ppfmt
from app.services.ppfmt import SawMap, SawNode, SawPart
from app.services.ppfmt import _saw_bsf as B
from app.services.ppfmt import biesse_nc300, saw_kdt_qk3, saw_scheer
from app.services.ppfmt._saw_common import demo_job
from app.services.ppfmt._saw_giben import patterns

L, W, KERF, TRIM = 2750.0, 1830.0, 3.0, 2.0
OFF = TRIM + KERF
N = SawNode


def _parts():
    return [SawPart(uid=1, name="01_001 bok", code="01_001", length=1000, width=500, qty=2, grain=True),
            SawPart(uid=2, name="01_002 polka", code="01_002", length=600, width=400, qty=2, grain=False),
            SawPart(uid=3, name="01_003 planka", code="01_003", length=600, width=90, qty=1, grain=False)]


def _map(children, axis="x", copies=1, index=1):
    root = N(x=OFF, y=OFF, l=L - 2 * OFF, w=W - 2 * OFF, kind="C", axis=axis, children=children)
    return SawMap(index=index, copies=copies, sheet_length=L, sheet_width=W, is_remnant=False, sheet_id="s1", tree=root,
                  placements=[], offcuts=[], commands=[], trim_length=TRIM, trim_width=TRIM)


def _strip_x():
    """Polosa 1000 (X bo'ylab) → 500, 500 (detal 1), 400 lik bo'lakdan 600 (detal 2) — 3 daraja."""
    return N(x=5, y=5, l=1000, w=1820, kind="C", axis="y", children=[
        N(x=5, y=5, l=1000, w=500, kind="P", uid=1), N(x=5, y=508, l=1000, w=500, kind="P", uid=1),
        N(x=5, y=1011, l=1000, w=400, kind="C", axis="x", children=[N(x=5, y=1011, l=600, w=400, kind="P", uid=2)])])


def _map_y():
    """Polosalar Y bo'ylab: 500 (detal 1 + 600 lik bo'lakda 400 va 90) va 400 (detal 2) — 3 daraja."""
    a = N(x=5, y=5, l=2740, w=500, kind="C", axis="x", children=[
        N(x=5, y=5, l=1000, w=500, kind="P", uid=1),
        N(x=1008, y=5, l=600, w=500, kind="C", axis="y", children=[
            N(x=1008, y=5, l=600, w=400, kind="P", uid=2), N(x=1008, y=408, l=600, w=90, kind="P", uid=3)])])
    b = N(x=5, y=508, l=2740, w=400, kind="C", axis="x", children=[N(x=5, y=508, l=600, w=400, kind="P", uid=2)])
    return _map([a, b], axis="y")


def _deep():
    """4 daraja: polosa 1000 → 400 → 600 → 300."""
    return N(x=5, y=5, l=1000, w=1820, kind="C", axis="y", children=[
        N(x=5, y=5, l=1000, w=400, kind="C", axis="x", children=[
            N(x=5, y=5, l=600, w=400, kind="C", axis="y", children=[N(x=5, y=5, l=600, w=300, kind="P", uid=2)])])])


def _job(maps=None, **kw):
    return demo_job(_parts(), maps or [_map([_strip_x()])], kerf=KERF, trim=TRIM, **kw)


def _run(key, job):
    (name, data), = ppfmt.load_all()[key].fn(job)
    return name, data


def _unzip(data):
    z = zipfile.ZipFile(io.BytesIO(data))
    return {i.filename: z.read(i) for i in z.infolist()}


def test_registered():
    reg = ppfmt.load_all()
    for key in ("scheer", "kdt_presize_qk"):
        assert reg[key].group == "saw" and reg[key].ext == "zip" and reg[key].note


# ───────────────────────── Scheer ─────────────────────────
def test_scheer_files():
    name, data = _run("scheer", _job())
    assert name == "9001_test_LDSP_OQ.zip"
    f = _unzip(data)
    assert sorted(f) == ["NAME.CUT", "holz0000.rec", "soll.cut", "teile.lst"]        # etikett.bin chiqarilmaydi
    assert f["NAME.CUT"] == b"9001_tes" + b" " * 24 + b"\r\n"
    assert f["soll.cut"] == (b"   1,1830.0,2750.0,  16.0,LDSP OQ         ,   1,   0.0, ,9001_TEST" + b" " * 22 + b"\r\n")
    tail = "," + ",".join(" " * n for n in (4, 4, 12, 30, 30)) + "\r\n"
    assert f["teile.lst"].decode("ascii") == (
        "9001_tes,9001_tes,  1,  1,LDSP OQ         ,16.0,1         ,  2,  2, 1000.0,  500.0,1" + tail
        + "9001_tes,9001_tes,  1,  1,LDSP OQ         ,16.0,2         ,  2,  1,  600.0,  400.0,0" + tail)
    assert b"giblab" not in b"".join(f.values()).lower()


def test_scheer_rec():
    rec = _unzip(_run("scheer", _job())[1])["holz0000.rec"]
    assert len(rec) == 0x180 + 2 * 0x580 and rec[4:0x180] == saw_scheer.HEAD[4:] and rec[0x180:0x700] == saw_scheer.BLOCK0
    # 0-maydon — bloklar soni (0-blok + kartalar): 1 karta → 2 (onlayn fayllar: 3 karta → 4, 7 karta → 8; 2026-10-24)
    assert struct.unpack_from("<I", rec, 0)[0] == 2
    h = rec[0x700:0x780]
    assert struct.unpack_from("<hfffh", h, 0) == (11, 2750.0, 1830.0, 16.0, 1)       # 1-daraja X bo'ylab → (L, W)
    assert h[0x2e:0x3e] == b"LDSP OQ         "
    cuts = [struct.unpack_from("<hffh8s", rec, 0x780 + 20 * i) for i in range(64)]
    assert cuts[:4] == [(1, 1000.0, 0.0, 0, b"        "), (2, 0.0, 500.0, 0, b"1       "),
                        (1, 0.0, 400.0, 0, b"        "), (101, 600.0, 0.0, 0, b"2       ")]
    assert not any(rec[0x780 + 80:])


def test_scheer_strips_along_width_and_copies():
    f = _unzip(_run("scheer", _job([_map_y(), _map([_strip_x()], copies=2, index=2)]))[1])
    lines = f["soll.cut"].decode("ascii").split("\r\n")
    assert lines[0].startswith("   1,2750.0,1830.0,  16.0,") and lines[1].startswith("   2,1830.0,2750.0,  16.0,")
    assert lines[1].split(",")[5] == "   2"
    rec = f["holz0000.rec"]
    assert len(rec) == 0x180 + 3 * 0x580
    assert struct.unpack_from("<hfffh", rec, 0x700) == (11, 1830.0, 2750.0, 16.0, 1)
    assert struct.unpack_from("<hfffh", rec, 0x700 + 0x580) == (11, 2750.0, 1830.0, 16.0, 2)
    cuts = [struct.unpack_from("<hffh8s", rec, 0x780 + 20 * i)[:3] for i in range(7)]
    assert cuts == [(1, 500.0, 0.0), (1, 0.0, 1000.0), (1, 0.0, 600.0), (101, 400.0, 0.0), (101, 90.0, 0.0),
                    (1, 400.0, 0.0), (1, 0.0, 600.0)]
    # teile.lst: detal 1 — 1- va 2-kartada (2 nusxa) → o'sib boruvchi son 1, keyin 5
    t = [ln.split(",") for ln in f["teile.lst"].decode("ascii").split("\r\n") if ln]
    assert [(x[2], x[6].strip(), x[8]) for x in t] == [("  1", "1", "  1"), ("  1", "2", "  1"), ("  1", "3", "  1"),
                                                       ("  1", "2", "  2"), ("  2", "1", "  5"), ("  2", "2", "  4")]
    assert {len(",".join(x)) for x in t} == {169}


def test_scheer_limits_and_names():
    with pytest.raises(ValueError, match="глубже 3 уровн"):
        _run("scheer", _job([_map([_deep()])]))
    strips = []
    x = 5.0
    for i in range(33):                                    # 33 polosa × (konteyner + detal) = 66 yozuv > 64
        strips.append(N(x=x, y=5, l=40 + i, w=1820, kind="C", axis="y",
                        children=[N(x=x, y=5, l=40 + i, w=500, kind="P", uid=1)]))
        x += 40 + i + KERF
    with pytest.raises(ValueError, match="предел формата 64"):
        _run("scheer", _job([_map(strips)]))
    job = _job(project_name="Без имени", order="0", material="ЛДСП белый, 16")
    f = _unzip(_run("scheer", job)[1])
    assert f["NAME.CUT"].startswith(b"Bez_imen ")
    assert f["soll.cut"].split(b",")[4] == b"LDSP BELYY  16  " and b"BEZ IMENI" in f["soll.cut"]
    assert saw_scheer.program_name(_job(params={"program_name": "Шкаф №12 new"})) == "Shkaf_12"


# ───────────────────────── KDT PreSize V3.3.0P ─────────────────────────
REC = 273


def _qk_recs(b: bytes):
    assert (len(b) - 12) % REC == 0
    out = []
    for o in range(12, len(b), REC):
        base, idx, a0, a1, a2, one, thick, flag = struct.unpack_from("<ii3fifB", b, o)
        kids = [struct.unpack_from("<fii", b, o + 29 + 12 * i) for i in range(20)]
        assert (one, thick, flag) == (1, 16.0, 1) and all(z == 0 for _c, z, _r in kids)
        out.append((base, idx, (a0, a1, a2), [(c, r) for c, _z, r in kids if c], struct.unpack_from("<f", b, o + 269)[0]))
    return out


def test_qk3_doc_example():
    name, data = _run("kdt_presize_qk", _job())
    assert name == "9001_test_LDSP_OQ.zip"
    f = _unzip(data)
    assert sorted(f) == ["NUM=1   PANELS( 1 x 1 = 1 ).lbd", "NUM=1   PANELS( 1 x 1 = 1 ).qk"]
    qk = f["NUM=1   PANELS( 1 x 1 = 1 ).qk"]
    assert struct.unpack_from("<fff", qk, 0) == (3.0, 2750.0, 1830.0)
    assert _qk_recs(qk) == [(0, 1, (5.0, 2750.0, 1830.0), [(1000.0, 1)], 1742.0),
                            (100, 11, (5.0, 1830.0, 1000.0), [(500.0, 2), (400.0, 1)], 416.0),
                            (1020, 102, (0.0, 1000.0, 400.0), [(600.0, 1)], 397.0)]
    # 1-daraja list uzunligi bo'ylab — .lbd KDT «yangi versiya» bilan bir xil
    new = _unzip(_run("kdt_new", _job())[1])
    assert f["NUM=1   PANELS( 1 x 1 = 1 ).lbd"] == new["NUM=1   PANELS( 1 x 1 = 1 ).lbd"]
    assert b"giblab" not in b"".join(f.values()).lower()


def test_qk3_strips_along_width_order_and_rest():
    """List eni bo'ylab polosalar: 1-daraja o'z tartibida (KS33X da teskari), 3-daraja teskari; ildiz qoldig'i list
    uzunligidan, 1-daraja bo'lak qoldig'i list enidan hisoblanadi."""
    job = _job([_map_y()])
    qk = _unzip(_run("kdt_presize_qk", job)[1])["NUM=1   PANELS( 1 x 1 = 1 ).qk"]
    assert struct.unpack_from("<fff", qk, 0) == (3.0, 1830.0, 2750.0)
    assert _qk_recs(qk) == [(0, 1, (5.0, 1830.0, 2750.0), [(500.0, 1), (400.0, 1)], 2750.0 - 5 - 503 - 403),
                            (100, 11, (5.0, 2750.0, 500.0), [(1000.0, 1), (600.0, 1)], 1830.0 - 5 - 1003 - 603),
                            (1020, 102, (0.0, 500.0, 600.0), [(90.0, 1), (400.0, 1)], 500.0 - 93 - 403),
                            (120, 12, (5.0, 2750.0, 400.0), [(600.0, 1)], 1830.0 - 5 - 603)]
    (P,) = patterns(job)
    assert [n["cut"] for n in saw_kdt_qk3.tree(job, P)] == [500.0, 400.0]
    from app.services.ppfmt import saw_kdt_ks33x
    assert [n["cut"] for n in saw_kdt_ks33x.ks_tree(job, P)] == [400.0, 500.0]


def test_qk3_limits():
    # 4 daraja — joiz (4-daraja bolalar 3-daraja yozuvida), 5 daraja — xato
    recs = _qk_recs(_unzip(_run("kdt_presize_qk", _job([_map([_deep()])]))[1])["NUM=1   PANELS( 1 x 1 = 1 ).qk"])
    assert [(b, i) for b, i, *_ in recs] == [(0, 1), (100, 11), (1000, 101), (10020, 1001)]
    deep5 = N(x=5, y=5, l=1000, w=1820, kind="C", axis="y", children=[
        N(x=5, y=5, l=1000, w=400, kind="C", axis="x", children=[
            N(x=5, y=5, l=600, w=400, kind="C", axis="y", children=[
                N(x=5, y=5, l=600, w=300, kind="C", axis="x", children=[N(x=5, y=5, l=500, w=300, kind="P", uid=2)])])])])
    with pytest.raises(ValueError, match="глубже 4 уровн"):
        _run("kdt_presize_qk", _job([_map([deep5])]))
    strips = []
    x = 5.0
    for i in range(21):
        strips.append(N(x=x, y=5, l=40 + i, w=1820, kind="C", axis="y",
                        children=[N(x=x, y=5, l=40 + i, w=500, kind="P", uid=1)]))
        x += 40 + i + KERF
    with pytest.raises(ValueError, match="предел формата 20"):
        _run("kdt_presize_qk", _job([_map(strips)]))


# ───────────────────────── 8 belgili dastur nomlari, NC300 tartibi ─────────────────────────
def test_short_names_are_transliterated():
    job = _job(project_name="Без имени", order="0")
    assert _run("holzma_cadmatic3", job)[0] == "Bez_imen.SPL"
    assert sorted(_unzip(_run("giben_gdrive", job)[1])) == ["Bez_imen.CPX", "Bez_imen.DAX"]
    assert biesse_nc300.nome(job) == "Bez_imen"
    assert _run("holzma_cadmatic3", _job())[0] == "9001_tes.SPL"


def test_nc300_y_lists_reversed_and_hash_order():
    _ax, cuts = B.cut_tree(_map_y())
    geo = B.merge_runs(cuts, by_part=False)
    assert [(c.level, c.dim) for c in B.walk_cuts(geo)] == [(1, 500), (2, 1000), (2, 600), (3, 400), (3, 90), (1, 400), (2, 600)]
    assert [(c.level, c.dim) for c in B.walk_cuts(biesse_nc300.flip_y(geo))] == [
        (1, 400), (2, 600), (1, 500), (2, 1000), (2, 600), (3, 90), (3, 400)]
    assert biesse_nc300.hash_order([33, 1, 20, 3, 17]) == [33, 1, 17, 3, 20]      # sig'im 16: savat 1 (33, 1, 17), 3, 4
    assert biesse_nc300.hash_order(list(range(13, 0, -1))) == list(range(1, 14))  # sig'im 32
