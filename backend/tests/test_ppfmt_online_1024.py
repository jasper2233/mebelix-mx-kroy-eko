"""2026-10-24: onlayn tizim bilan bir xil kroyda solishtiruvdan keyingi tuzatishlar va yangi formatlar (sun'iy ishlar bilan;
kutilgan qiymatlar docs/mebelix/postprocessors/ dagi qoidalardan, korxona fayllarisiz).

Yangi: Altendorf (ELMO) `.saw`, Lisec (XOpt) `.DAT`, (CN) nesting — NCStudio / KDT GCode / WoodWOP / TPA / BiesseWorks.
Tuzatilgan: Scheer bloklar soni, F4Classic detal raqami (tartib raqami), Felder PC6 kromka bayroqlari va lotin yozuvi,
Shelling / AES lotin yozuvi, MaestroCut UTF-8 va bo'sh kromka, XDWoodCam UTF-8, frezalash bayrog'i (teshib o'tuvchi kesim)."""
from __future__ import annotations

import io
import zipfile

from app.models import Operation, OpType, Part, Project, XNCParams
from app.services import ppfmt, pp_access
from app.services.ppfmt import SawMap, SawNode, SawPart
from app.services.ppfmt import cn_nest as C
from app.services.ppfmt._saw_common import demo_job
from app.services.render import part_mill_flag

L, W, KERF, TRIM = 2750.0, 1830.0, 3.0, 2.0
OFF = TRIM + KERF
N = SawNode


def _parts():
    return [SawPart(uid=7, name="01_001 bok", code="01_001", length=1000, width=500, qty=2, grain=True),
            SawPart(uid=9, name="01_002 polka", code="01_002", length=600, width=400, qty=1, grain=False)]


def _job(params=None):
    strip = N(x=5, y=5, l=1000, w=1820, kind="C", axis="y", children=[
        N(x=5, y=5, l=1000, w=500, kind="P", uid=7), N(x=5, y=508, l=1000, w=500, kind="P", uid=7),
        N(x=5, y=1011, l=1000, w=400, kind="C", axis="x", children=[
            N(x=5, y=1011, l=600, w=400, kind="P", uid=9), N(x=608, y=1011, l=397, w=400, kind="W")]),
        N(x=5, y=1414, l=1000, w=411, kind="W")])
    root = N(x=OFF, y=OFF, l=L - 2 * OFF, w=W - 2 * OFF, kind="C", axis="x",
             children=[strip, N(x=1008, y=5, l=1737, w=1820, kind="W")])
    m = SawMap(index=1, copies=1, sheet_length=L, sheet_width=W, is_remnant=False, sheet_id="s1", tree=root,
               placements=[], offcuts=[], commands=[], trim_length=TRIM, trim_width=TRIM)
    return demo_job(_parts(), [m], kerf=KERF, trim=TRIM, params=params)


def _files(key, job):
    out = {}
    for n, d in ppfmt.load_all()[key].fn(job):
        out[n] = d
    return out


# ───────────────────────── Altendorf (ELMO) ─────────────────────────
def test_altendorf_structure():
    f = _files("elmo3", _job())
    assert list(f) == ["0001.0001.saw"]
    t = f["0001.0001.saw"].decode("cp1251")
    assert t.startswith(";MebeliX Kroy postprocessor for Altendorf\nVER (1)\n") and "giblab" not in t.lower()
    acut = [x for x in t.split("\n") if x.startswith("ACUT")]
    assert acut == [
        "ACUT (-1;0;;;* 1825;2745 * 1825 * 16;0;1003;1825;1;1x;P;1000;S;A;H;49;U;G;L;1845;U;G;S;0;U;A;M;16;U;A)",
        # bir xil detal (id 7) ikki marta — bitta ACUT, «2x»; detal o'lchamlari — detalning o'zi (l; w)
        "ACUT (1;1;Label-Identifikation-7;7;* 1000;1825 * 1000 * 16;1;1000;500;2;2x;P;500;S;A;H;49;U;G;L;1425;U;G;S;0;U;A;M;16;U;A)",
        "ACUT (1;2;;;* 1000;819 * 1000 * 16;0;1000;403;1;1x;P;400;S;A;H;49;U;G;L;519;U;G;S;0;U;A;M;16;U;A)",
        "ACUT (2;3;Label-Identifikation-9;9;* 400;1000 * 400 * 16;1;600;400;1;1x;P;600;S;A;H;49;U;G;L;500;U;G;S;0;U;A;M;16;U;A)"]
    assert [x for x in t.split("\n") if x.startswith("BLOCK")] == [
        'BLOCK (0;0;0;2745;1825;"2745";;;"1825";1;1)', 'BLOCK (1;0;0;1003;1825;"1003";;;"1825";1;1)',
        'BLOCK (2;0;1006;1000;1409;"1000";;;"403";1;1)']
    assert [x for x in t.split("\n") if x.startswith("LINE")] == [
        "LINE (-1;0;1000;0;1000;1825;1;1;1;1;3;1)", "LINE (1;1;0;500;1000;500;1;1;1;1;3;1)",
        "LINE (1;1;0;1003;1000;1003;1;1;1;1;3;1)", "LINE (1;2;0;1406;1000;1406;1;1;1;1;3;1)",
        "LINE (2;3;600;1006;600;1406;1;1;1;1;3;1)"]


def test_altendorf_fence_rule_and_params():
    from app.services.ppfmt import saw_altendorf as A
    assert A.fence(560, 1825, {}) == "P" and A.fence(2168, 1825, {}) == "L"      # bo'ylama tirgak ≤ 1600
    assert A.fence(554, 32, {}) == "L" and A.fence(528, 434, {}) == "P"          # balandlik / en ≤ 4
    f = _files("elmo3", _job({"program_name": "12", "saw_blade_height": 60}))
    assert list(f) == ["0012.0001.saw"] and b";H;60;U;G;" in f["0012.0001.saw"]


# ───────────────────────── Lisec (XOpt) ─────────────────────────
def test_lisec_dat():
    f = _files("lisec_xopt", _job())
    assert list(f) == ["PL001.DAT"]
    assert f["PL001.DAT"].decode("utf-8").split("\r\n") == [
        "[LPL_REF] MebeliX", "[LPL_AUF] 9001_test", "[LPL_AUFNR] Stroka?", "[LPL_BREITE] 183.0", "[LPL_HOEHE] 275.0",
        "[LPL_DICKE] 1.6", "[LPL_TYPE] 1", "[LPL_BV] .2", "[LPL_BU] .2", "",
        "[TRAVERE] 100.0", "[Y_SCHNITT] 50.0 [BOCK_CODE] 1", "[Y_SCHNITT] 50.0 [BOCK_CODE] 1", "[Y_SCHNITT] 40.0",
        "[Z_SCHNITT] 60.0 [BOCK_CODE] 2", ""]
    assert ppfmt.ROT_LIMIT["lisec_xopt"] == 3


# ───────────────────────── (CN) nesting ─────────────────────────
def _nest(overhang=0.0, maps=2):
    ms = [C.NestMap(index=1, length=2750, width=1830, paths=[[(4, 4), (4, 300), (200, 300)], [(616, 100), (616, 50)]])]
    if maps > 1:
        ms.append(C.NestMap(index=2, length=2750, width=1830, paths=[[(10, 10), (500, 10)]]))
    return C.NestJob(thickness=18, overhang=overhang, tool=C.NestTool(rpm=3000, feed_z=100, feed_xy=5000), maps=ms)


def test_cn_ncstudio_first_g1_has_z_once_per_job():
    f = _files("cn_ncstudio", _nest())
    a, b = f["F1.NC"].decode().split("\r\n"), f["F2.NC"].decode().split("\r\n")
    assert a[:7] == ["(NCStudio, generated code in MebeliX Kroy)", "G90", "(12MM MillBaseCut)", "T1 M06", "G0 Z30.0",
                     " M04 S3000", "G43 H1"]
    assert a[7:12] == ["G0 X4.0 Y4.0", "Z-18.0 F100.0", "G1 Y300.0 Z-18.0 F5000.0", "G1 X200.0", "G0 Z30.0"]
    assert a[12:16] == ["G0 X616.0 Y100.0", "Z-18.0 F100.0", "G1 Y50.0 F5000.0", "G0 Z30.0"] and a[-3:] == ["M05", "M30", ""]
    assert b[8:10] == ["Z-18.0 F100.0", "G1 X500.0 F5000.0"]          # 2-faylda Z yozilmaydi


def test_cn_kdt_y_from_bottom_and_z_from_table():
    t = _files("cn_kdt_gcode", _nest(overhang=0.5, maps=1))["F1.NC"].decode().split("\r\n")
    assert t[:9] == ["G53 Z-15.000", "M129", "M123", "M125", "G53 Z-15.000", "G54 G90", "M6 T1", "M04 S3000", "G43 H1"]
    assert t[9:14] == ["G0 X4.0 Y-1826.0", "G1 Z-0.5 F100", "G1 X4.0 Y-1530.0 F5000", "G1 X200.0 Y-1530.0", "G0 Z38.0"]
    assert t[-3:] == ["M5", "M30", ""]
    t0 = _files("cn_kdt_gcode", _nest(maps=1))["F1.NC"].decode()
    assert "G1 Z0.0 F100" in t0 and "Z-0.0" not in t0


def test_cn_woodwop_tpa_biesse():
    j = _nest(overhang=0.5)
    w = _files("cn_woodwop", j)["F1.mpr"].decode().split("\r\n")
    assert w[:3] == ["[H", 'VERSION="4.0 Alpha"', 'MAT="HOMAG"'] and "_BSZ=18" in w and w[-2:] == ["!", ""]
    assert w[w.index("]1"):w.index("]1") + 7] == ["]1", "$E0", "KP ", "X=4", "Y=4", "Z=-0.5", "KO=00"]
    assert 'EE="1:2"' in w and 'ZA="-0.5"' in w and w[-3] == 'F_="STANDARD"'
    tp = _files("cn_tpa", j)["F1.TCN"].decode().split("\r\n")
    assert tp[3] == "::UNm DL=2750 DH=1830 DS=18"
    assert "W#89{ ::WTs #1=4 #2=4 #3=-18.5 #40=0 #205=1 }W" in tp and "W#2201{ ::WTl  #1=4  #2=300 }W" in tp
    assert tp[-13:] == [C.TPA_LABEL, "}SIDE", "SIDE#2{", "}SIDE", "SIDE#3{", "}SIDE", "SIDE#4{", "}SIDE", "SIDE#5{", "}SIDE",
                        "SIDE#6{", "}SIDE", ""]
    bp = _files("cn_biesseworks", j)
    b1, b2 = bp["F1.bpp"].decode(), bp["F2.bpp"].decode()
    assert '@ ROUT, "", "", 15, "", 0 : "P00001", 0, "1", 0, 18.5, "", 1, 12, -1,' in b1
    assert '  @ START_POINT, "", "", 26, "", 0 : 4, 4, 0' in b1 and '  @ LINE_EP, "", "", 37, "", 0 : 4, 300, 0' in b1
    assert '  @ LINE_EP, "", "", 47, "", 0 : 200, 300, 0' in b1 and '  @ ENDPATH, "", "", 59, "", 0 :' in b1
    assert '@ ROUT, "", "", 65, "", 0 : "P00002"' in b1
    assert '"P00003"' in b2 and '@ ROUT, "", "", 15,' in b2          # P raqami fayllar bo'ylab davom etadi
    assert b1.endswith("[TOOLING]\r\n\r\n")


def test_cn_machines_registered_as_nest_group():
    from app.services.postprocessors import MACHINE_BY_KEY
    for k in ("cn_ncstudio", "cn_kdt_gcode", "cn_woodwop", "cn_tpa", "cn_biesseworks"):
        assert MACHINE_BY_KEY[k][1] == "nest" and ppfmt.load_all()[k].group == "nest"
    assert MACHINE_BY_KEY["elmo3"] == ("Altendorf (ELMO)", "saw") and MACHINE_BY_KEY["lisec_xopt"][1] == "saw"


def test_cn_postprocess_api_zip(client):
    pid = client.post("/api/projects", json={"name": "CN PP"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CN", "name": "MDF", "code": "MDF16"}).json()
    oid = p["operations"][-1]["id"]
    client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=[dict(name="A", length=600, width=400, qty=2)])
    assert client.post(f"/api/projects/{pid}/operations/{oid}/optimize", params={"quality": "fast"}).status_code == 200
    lst = client.get("/api/postprocessors").json()
    nest = [x for x in lst if x.get("group") == "nest"]
    assert {x["key"] for x in nest} >= {"machine:cn_ncstudio", "machine:cn_tpa"} and all(x["available"] for x in nest)
    r = client.get(f"/api/projects/{pid}/operations/{oid}/postprocess", params={"key": "machine:cn_ncstudio"})
    assert r.status_code == 200, r.text
    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert z.namelist() == ["F1.NC"]
    t = z.read("F1.NC").decode()
    assert t.count("G0 Z30.0") >= 3 and "Z-16.0" in t or "Z-18.0" in t          # har detal konturi — alohida yo'l
    bad = client.get(f"/api/projects/{pid}/operations/{oid}/postprocess", params={"key": "machine:cn_tpa_x"})
    assert bad.status_code in (400, 404)


# ───────────────────────── tuzatishlar ─────────────────────────
def test_f4classic_part_number_is_operation_index():
    j = _job()
    txt = _files("felder_f4classic", j)
    body = next(iter(txt.values()))
    data = zipfile.ZipFile(io.BytesIO(body)).read(zipfile.ZipFile(io.BytesIO(body)).namelist()[0]).decode() \
        if body[:2] == b"PK" else body.decode()
    rows = [x for x in data.splitlines() if x.count(",") >= 4]
    assert rows and all(x.rsplit(",", 1)[1].strip() in ("1", "2", "1:1") for x in rows), rows   # id 7 → 1, id 9 → 2


def test_pc6_edge_flags_two_chars_and_latin():
    from app.services.pp_machine_schema import _PC6_TEXT0
    assert _PC6_TEXT0.startswith("if(empty(ets),'  ',")
    from app.services.ppfmt.felder_format4 import _fit6
    assert _fit6("Без имени", 12) == "Bez imeni   " and _fit6("Жёлтый", 6) == "Zhyolt"     # lotin, keyin kenglik


def _xnc_project(dps: list[str]) -> tuple[Project, Part]:
    from app.models import XncCommand
    prog = []
    for dp in dps:
        prog += [XncCommand(cmd="MillStart", params={"X": 10, "Y": 10, "DP": dp, "T": "Mill5"}),
                 XncCommand(cmd="MillLine", params={"X": 100, "Y": 10})]
    x = Operation(type=OpType.XNC, code="X1", name="x", xnc=XNCParams(program=prog))
    part = Part(uid=1, name="p", length=300, width=200, xnc_op_ids=[x.id])
    cs = Operation(type=OpType.CS, name="m", parts=[part])
    return Project(name="t", operations=[cs, x]), part


def test_mill_flag_ignores_through_cut_parts():
    p, part = _xnc_project(["5"])
    assert part_mill_flag(part, p) is True
    p, part = _xnc_project(["throughCutDepth", "5"])                   # teshib o'tuvchi kesim + oddiy freza (korxona: false)
    assert part_mill_flag(part, p) is False


def test_pp_access_new_native_keys_open_for_old_saved_list(monkeypatch):
    monkeypatch.setattr(pp_access, "_row", lambda: {"open": ["holzma_ptx"]})
    keys = pp_access.open_keys()
    assert "holzma_ptx" in keys and "cn_ncstudio" in keys and "elmo3" in keys and "scm_wincut" not in keys
    monkeypatch.setattr(pp_access, "_row", lambda: {"open": ["holzma_ptx"], "known": sorted(
        __import__("app.services.postprocessors", fromlist=["MACHINE_BY_KEY"]).MACHINE_BY_KEY)})
    assert pp_access.open_keys() == {"holzma_ptx"}                     # admin ko'rib chiqqan — o'zgarmaydi
