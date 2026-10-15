"""W1 (ixtiyoriy) · DXF → XNC kontur importi: kichik ASCII parser, zanjir, bulge, aylana, koordinata o'tkazish, xatolar, API."""
import math
import random

import pytest

from app.services import xnc as X
from app.services import xnc_dxf as D

from test_qa_fix_calc import _op, _xnc_for


def dxf(*ents):
    return ("0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n" + "".join(ents)
            + "0\nENDSEC\n0\nEOF\n").encode()


def line(x1, y1, x2, y2):
    return f"0\nLINE\n8\n0\n10\n{x1}\n20\n{y1}\n30\n0\n11\n{x2}\n21\n{y2}\n31\n0\n"


def arc(cx, cy, r, a0, a1):
    return f"0\nARC\n8\n0\n10\n{cx}\n20\n{cy}\n30\n0\n40\n{r}\n50\n{a0}\n51\n{a1}\n"


def circle(cx, cy, r):
    return f"0\nCIRCLE\n8\n0\n10\n{cx}\n20\n{cy}\n30\n0\n40\n{r}\n"


def lwpoly(pts, closed=True):
    s = f"0\nLWPOLYLINE\n8\n0\n90\n{len(pts)}\n70\n{1 if closed else 0}\n"
    for p in pts:
        s += f"10\n{p[0]}\n20\n{p[1]}\n" + (f"42\n{p[2]}\n" if len(p) > 2 else "")
    return s


def length(prog, dz=16):
    """Freza uzunligi, mm (statistika 1 mm ga yaxlitlaydi — taqqoslashda abs ≥ 0.6)."""
    return X.program_stats(prog, 1000, 1000, dz)["mill_m"] * 1000


def test_rectangle_from_loose_lines_is_one_closed_contour():
    # tartibsiz va ba'zilari teskari yo'nalishda chizilgan 4 chiziq
    segs = [line(0, 0, 100, 0), line(100, 50, 100, 0), line(100, 50, 0, 50), line(0, 0, 0, 50)]
    random.Random(1).shuffle(segs)
    prog, warn, st = D.to_program(dxf(*segs))
    assert st["contours"] == 1 and st["open"] == 0 and warn == []
    assert [c.cmd for c in prog] == ["Tool", "MillStart", "MillLine", "MillLine", "MillLine", "MillLine"]
    assert length(prog) == pytest.approx(300, abs=0.6)
    # bbox: chap-yuqori burchak (0, 0) ga, Y pastga
    assert st["bbox"] == [0, 0, 100, 50] and st["size"] == [100, 50]
    xs = [c.params["X"] for c in prog if "X" in c.params]
    ys = [c.params["Y"] for c in prog if "Y" in c.params]
    assert min(xs) == 0 and max(xs) == 100 and min(ys) == 0 and max(ys) == 50


def test_origin_modes_and_y_flip():
    ent = dxf(line(100, 200, 160, 200), line(160, 200, 160, 230))
    prog, _w, st = D.to_program(ent, origin="bbox")
    start = next(c for c in prog if c.cmd == "MillStart")
    assert (start.params["X"], start.params["Y"]) == (0, 30)                 # bbox yuqori chap burchagi (100, 230) -> (0, 0)
    assert [(c.params["X"], c.params["Y"]) for c in prog if c.cmd == "MillLine"] == [(60, 30), (60, 0)]
    prog, _w, _s = D.to_program(ent, origin="zero", height=500)
    start = next(c for c in prog if c.cmd == "MillStart")
    assert (start.params["X"], start.params["Y"]) == (100, 300)                   # 500 - 200
    prog, _w, _s = D.to_program(ent, origin="zero", flip_y=False)
    start = next(c for c in prog if c.cmd == "MillStart")
    assert (start.params["X"], start.params["Y"]) == (100, 200)


def test_arc_direction_and_length_with_flip():
    quarter = dxf(arc(0, 0, 10, 0, 90), line(0, 10, 0, 40), line(0, 40, 50, 40))
    prog, _w, st = D.to_program(quarter, flip_y=True)
    a = next(c for c in prog if c.cmd == "MillArcCenter")
    assert a.params["DIR"] == "false"                                         # Y aks etildi: CCW -> teskari
    assert length(prog) == pytest.approx(10 * math.pi / 2 + 30 + 50, abs=0.6)
    assert st["bbox"] == [0, 0, 50, 40]
    prog2, _w, _s = D.to_program(quarter, flip_y=False)
    assert next(c for c in prog2 if c.cmd == "MillArcCenter").params["DIR"] == "true"
    assert length(prog2) == pytest.approx(10 * math.pi / 2 + 30 + 50, abs=0.6)
    # chizilgan SVG da yoy markaz tomonga (ichkariga) egiladi: boshlang'ich nuqtadan oxirgi nuqtagacha markazga nisbatan CCW (DXF)
    start = next(c for c in prog if c.cmd == "MillStart")
    assert (start.params["X"], start.params["Y"]) == (10, 40)                # (10, 0) -> y' = 40 - 0 (Y aks)


def test_bbox_uses_only_arc_sweep():
    """Chorak yoyning bbox si butun doira emas: x 0..10, y 0..10."""
    prog, _w, st = D.to_program(dxf(arc(0, 0, 10, 0, 90)))
    assert st["bbox"] == [0, 0, 10, 10]
    prog, _w, st = D.to_program(dxf(arc(0, 0, 10, 0, 270)))                   # 3/4 doira: x -10..10, y -10..10
    assert st["bbox"] == [-10, -10, 10, 10]


def test_lwpolyline_bulge_rounded_rectangle():
    r = 10
    b = math.tan(math.radians(90) / 4)                                        # 90° yoy bulge
    pts = [(r, 0, b), (100 - r, 0), (100, r, b), (100, 50 - r), (100 - r, 50, b), (r, 50), (0, 50 - r, b), (0, r)]
    # har burchakda: chiziq + yoy; bulge — shu tepadan keyingisiga yoy
    poly = [(r, 0), (100 - r, 0, b), (100, r), (100, 50 - r, b), (100 - r, 50), (r, 50, b), (0, 50 - r), (0, r, b)]
    prog, warn, st = D.to_program(dxf(lwpoly(poly)))
    assert st["contours"] == 1 and st["open"] == 0
    assert sum(1 for c in prog if c.cmd == "MillArcCenter") == 4
    assert length(prog) == pytest.approx(2 * (100 + 50) - 8 * r + 2 * math.pi * r, abs=0.6)
    # yoylar markazi — burchaklar ichida (Y aks etilgan: y' = 50 - y)
    centers = sorted((round(c.params["CX"], 3), round(c.params["CY"], 3)) for c in prog if c.cmd == "MillArcCenter")
    assert centers == sorted([(100 - r, r), (100 - r, 50 - r), (r, 50 - r), (r, r)])
    del pts


def test_polyline_old_style_and_open_contour_warning():
    old = ("0\nPOLYLINE\n8\n0\n66\n1\n70\n0\n" + "".join(f"0\nVERTEX\n8\n0\n10\n{x}\n20\n{y}\n" for x, y in ((0, 0), (50, 0), (50, 30)))
           + "0\nSEQEND\n")
    prog, warn, st = D.to_program(dxf(old))
    assert st["contours"] == 1 and st["open"] == 1 and any("1" in w for w in warn)
    assert length(prog) == pytest.approx(80, abs=0.6)


def test_circle_as_contour_or_drill():
    ents = dxf(circle(50, 50, 20), circle(100, 100, 4), circle(130, 100, 4))
    prog, _w, st = D.to_program(ents)
    assert st["circles"] == 3 and st["drills"] == 0
    assert length(prog) == pytest.approx(2 * math.pi * (20 + 4 + 4), abs=0.6)
    prog, _w, st = D.to_program(ents, drill_max_d=10)
    assert st["circles"] == 1 and st["drills"] == 2
    drills = [c for c in prog if c.cmd == "DrillFront"]
    assert len(drills) == 2 and all(d.params["T"] == "Bore8" for d in drills)
    assert sum(1 for c in prog if c.cmd == "Tool") == 2                          # Mill + Bore8
    assert X.program_stats(prog, 1000, 1000, 16)["drills"] == 2
    # aylana doira konturi: to'liq doira, boshi = oxiri
    ring = next(c for c in prog if c.cmd == "MillArcCenter")
    start = next(c for c in prog if c.cmd == "MillStart")
    assert (ring.params["X"], ring.params["Y"]) == (start.params["X"], start.params["Y"])


def test_options_depth_tool_correction():
    prog, _w, _s = D.to_program(dxf(line(0, 0, 10, 0)), depth="dz/2", tool_d=8, correction=2)
    assert prog[0].params == {"N": "Mill", "D": 8}
    ms = prog[1]
    assert ms.params["DP"] == "dz/2" and ms.params["C"] == 2 and ms.params["T"] == "Mill"


def test_skipped_entities_and_errors():
    prog, warn, st = D.to_program(dxf(line(0, 0, 10, 0), "0\nTEXT\n8\n0\n1\nsalom\n", "0\nSPLINE\n8\n0\n", "0\nSPLINE\n8\n0\n"))
    assert any("TEXT" in w for w in warn) and any("SPLINE" in w and "2" in w for w in warn) and st["contours"] == 1
    for bad in (b"AutoCAD Binary DXF\r\n\x1a\x00", b"hello world", b"", dxf(), b"0\nSECTION\n2\nENTITIES\n0\nLINE\n10\nabc\n0\nENDSEC\n",
                b"abc\ndef\n"):
        with pytest.raises(D.DxfError):
            D.to_program(bad)
    with pytest.raises(D.DxfError):
        D.to_program(b"0\nSECTION\n2\nENTITIES\n0\nLINE\n10\n1e99\n20\n0\n11\n1\n21\n1\n0\nENDSEC\n")      # ma'nosiz katta son


def test_crlf_and_cp1251_files():
    raw = dxf(line(0, 0, 10, 0), "0\nTEXT\n8\n0\n1\nsalom\n").replace(b"\n", b"\r\n")
    assert D.to_program(raw)[2]["contours"] == 1
    cyr = ("0\nSECTION\n2\nENTITIES\n0\nLINE\n8\nСлой\n10\n0\n20\n0\n11\n10\n21\n0\n0\nENDSEC\n").encode("cp1251")
    assert D.to_program(cyr)[2]["contours"] == 1


# ───────────────────────── API ─────────────────────────
def test_import_dxf_api_append_and_replace(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)                         # 480×800
    body = dxf(line(0, 0, 100, 0), line(100, 0, 100, 50), line(100, 50, 0, 50), line(0, 50, 0, 0), circle(300, 300, 4))
    r = client.post(f"/api/projects/{pid}/operations/{xid}/xnc/import-dxf", files={"file": ("a.dxf", body)},
                    data={"mode": "append", "drill_max_d": "10", "origin": "bbox"})
    assert r.status_code == 200, r.text
    d = r.json()
    x = _op(d["project"], xid)["xnc"]
    cmds = [c["cmd"] for c in x["program"]]
    assert cmds.count("MillStart") == 1 and cmds.count("MillLine") == 4 and cmds.count("DrillFront") == 1
    assert d["stats"]["contours"] == 1 and d["stats"]["drills"] == 1
    st = client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()
    assert st["drills"] == 1 and st["mill_m"] == pytest.approx(0.3, abs=1e-3)
    n = len(x["program"])
    r = client.post(f"/api/projects/{pid}/operations/{xid}/xnc/import-dxf", files={"file": ("a.dxf", body)}, data={"mode": "append"})
    assert len(_op(r.json()["project"], xid)["xnc"]["program"]) > n                    # qo'shildi
    r = client.post(f"/api/projects/{pid}/operations/{xid}/xnc/import-dxf", files={"file": ("a.dxf", body)}, data={"mode": "replace"})
    assert len(_op(r.json()["project"], xid)["xnc"]["program"]) == len(D.to_program(body, height=800)[0])
    # xatolar
    assert client.post(f"/api/projects/{pid}/operations/{xid}/xnc/import-dxf", files={"file": ("a.dxf", b"junk")}).status_code == 400
    assert client.post(f"/api/projects/{pid}/operations/{xid}/xnc/import-dxf", files={"file": ("a.dxf", body)},
                       data={"mode": "zz"}).status_code == 400
    assert client.post(f"/api/projects/{pid}/operations/{xid}/xnc/import-dxf", files={"file": ("a.dxf", body)},
                       data={"tool_d": "0"}).status_code == 400
    assert client.post(f"/api/projects/{pid}/operations/{cs}/xnc/import-dxf", files={"file": ("a.dxf", body)}).status_code == 400
