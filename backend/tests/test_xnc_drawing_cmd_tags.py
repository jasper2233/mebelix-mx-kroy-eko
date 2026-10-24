# -*- coding: utf-8 -*-
"""XNC chizmasi ↔ dastur buyrug'i: har geometrik element `data-cmd` atributini oladi — manba buyruqning daraxtdagi yo'li
(0 dan, nuqta bilan — frontend `pathKey`), Sub tanasi Call orqali bajarilsa — Call qatori yo'li ham. UI shu atribut bo'yicha
tanlangan buyruq geometriyasini qizil bilan belgilaydi (SVG qayta so'ralmaydi)."""
import re

from app.models import Operation, OpType, XncCommand as C, XNCParams
from app.services import xnc as X


def _xop(prog, dx=600, dy=400, dz=16):
    return Operation(type=OpType.XNC, name="op", xnc=XNCParams(length=dx, width=dy, thickness=dz, by_part_size=False, program=prog))


def _tags(svg):
    return re.findall(r'<(\w+)(?: class="([\w-]+)")?[^>]*? data-cmd="([^"]+)"', svg)


def _cmds(svg):
    return [set(t[2].split()) for t in _tags(svg)]


def test_hole_mill_groove_tagged():
    prog = [
        C(cmd="Tool", params={"N": "T5", "D": 5}),
        C(cmd="DrillFront", params={"X": 50, "Y": 50, "D": 8, "DP": 10}),
        C(cmd="DrillLeft", params={"Y": 100, "D": 8, "DP": 30}),
        C(cmd="MillStart", params={"X": 100, "Y": 100, "D": 8, "DP": 5}),
        C(cmd="MillLine", params={"X": 200, "Y": 100}),
        C(cmd="MillLine", params={"X": 200, "Y": 200}),
        C(cmd="Groove", params={"X1": 0, "Y1": 300, "X2": 600, "Y2": 300, "DP": 8, "W": 4}),
        C(cmd="MillRect", params={"X": 400, "Y": 200, "L": 100, "W": 50}),
    ]
    svg = X.xnc_drawing_svg(_xop(prog))
    tags = _tags(svg)
    by = {t[2]: (t[0], t[1]) for t in tags}
    assert by["1"] == ("g", "xnc-hole")                          # yuza teshigi: aylana + xoch + kesimlar bitta guruhda
    hole = re.search(r'<g class="xnc-hole" data-cmd="1">(.*?)</g>', svg).group(1)
    assert hole.count("<circle") == 1 and hole.count('class="xnc-sec"') == 2  # yuqori / pastki polosadagi kesimlar ham shu buyruqqa
    assert svg.count('class="xnc-sec"') >= 4                      # chap / o'ng kesimlar chiziladi, lekin belgilanmaydi
    edge = re.search(r'<g class="xnc-edge-hole"[^>]*data-cmd="2">(.*?)</g>', svg).group(1)
    assert 'class="xnc-ch"' in edge and 'class="xnc-ctr"' in edge   # kanal va polosa belgisi markazi — tanlanganda qizil
    assert by["2"] == ("g", "xnc-edge-hole")
    assert by["3"][0] == "path"                                  # kontur — MillStart
    assert by["4"] == ("path", "xnc-seg") and by["5"] == ("path", "xnc-seg")
    assert by["6"] == ("g", "xnc-groove")
    assert by["7"][0] == "path"                                  # MillRect
    assert "0" not in by                                         # Tool — geometriya yo'q
    # segment nusxalari ko'rinmas: chizma ko'rinishi o'zgarmaydi
    assert all('stroke="none"' in m for m in re.findall(r'<path class="xnc-seg"[^>]*>', svg))


def test_nested_loop_maps_to_tree_path():
    prog = [
        C(cmd="Var", params={"name": "i", "value": 0}),
        C(cmd="While", params={"cond": "i<3"}, children=[
            C(cmd="DrillFront", params={"X": "50+i*100", "Y": 50, "D": 5, "DP": 10}),
            C(cmd="Set", params={"name": "i", "value": "i+1"}),
        ]),
    ]
    svg = X.xnc_drawing_svg(_xop(prog))
    holes = re.findall(r'<g class="xnc-hole" data-cmd="([^"]+)"', svg)
    assert holes == ["1.0"] * 3                                  # 3 ta takror — hammasi While (1) ichidagi 0-buyruq
    # frontend: tanlangan yo'l `1` (While) — `1.0` ham unga tegishli (prefiks)
    assert all(h == "1" or h.startswith("1.") for h in holes)


def test_sub_call_tags_call_site_and_body():
    prog = [
        C(cmd="Sub", params={"name": "s"}, children=[
            C(cmd="If", params={"cond": "1"}, children=[C(cmd="DrillFront", params={"X": 100, "Y": 100, "D": 5, "DP": 10})]),
        ]),
        C(cmd="Com", params={}),
        C(cmd="Call", params={"name": "s"}),
        C(cmd="Call", params={"name": "s"}),
    ]
    svg = X.xnc_drawing_svg(_xop(prog))
    holes = [set(h.split()) for h in re.findall(r'<g class="xnc-hole" data-cmd="([^"]+)"', svg)]
    assert holes == [{"0.0.0", "2"}, {"0.0.0", "3"}]             # Sub ichidagi buyruq + qaysi Call chaqirgan


def test_children_of_simple_command_and_disabled():
    prog = [
        C(cmd="Com", params={}),
        C(cmd="DrillFront", params={"X": 10, "Y": 10, "D": 5, "DP": 5}, children=[
            C(cmd="DrillFront", params={"X": 30, "Y": 10, "D": 5, "DP": 5}),
        ]),
    ]
    svg = X.xnc_drawing_svg(_xop(prog))
    assert re.findall(r'<g class="xnc-hole" data-cmd="([^"]+)"', svg) == ["1", "1.0"]
    ops = X.evaluate(prog, 600, 400, 16, tool_lib={})
    assert [o["cmd_path"] for o in ops] == ["2", "2.1"]           # ijro yo'li (1 dan) — avvalgidek


def test_fillet_arc_tagged_with_fillet_command():
    prog = [
        C(cmd="MillStart", params={"X": 100, "Y": 100, "D": 8, "DP": 5}),
        C(cmd="MillLine", params={"X": 300, "Y": 100}),
        C(cmd="MillFillet", params={"R": 20}),
        C(cmd="MillLine", params={"X": 300, "Y": 300}),
    ]
    svg = X.xnc_drawing_svg(_xop(prog))
    segs = re.findall(r'<path class="xnc-seg" d="([^"]+)"[^>]*data-cmd="([^"]+)"', svg)
    assert [s[1] for s in segs] == ["1", "2", "3"]
    assert " A " in segs[1][0]                                   # yumaloqlash yoyi — MillFillet buyrug'iga


def test_tags_can_be_disabled(monkeypatch):
    monkeypatch.setattr(X, "DRAW_CMD_TAGS", False)
    svg = X.xnc_drawing_svg(_xop([C(cmd="DrillFront", params={"X": 10, "Y": 10, "D": 5, "DP": 5})]))
    assert "data-cmd" not in svg and "xnc-seg" not in svg
