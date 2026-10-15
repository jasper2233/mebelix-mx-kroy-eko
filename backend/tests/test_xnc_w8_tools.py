"""W8 · XNC asboblar jadvali («Инструменты») va palitra («Палитра»): standart to'plam, tekshiruv, sozlama API,
hisobda zaxira (T nomi → diametr / chuqurlik; dasturdagi Tool ustun), eski JSON mosligi."""
import json

import pytest
from pydantic import ValidationError

from app.models import Operation, OpType, XNCParams, XncCommand as C
from app.services import xnc as X
from app.services import xnc_tools as XT
from app.services.xnc_tools import ToolLib, XncPalette, XncTool, XncToolsDoc, library_of

from test_qa_fix_calc import _set_prog, _xnc_for


def cmd(kind, /, **p):
    return C(cmd=kind, params=p)


def xop(prog, length=200, width=100, thickness=16, **kw):
    return Operation(type=OpType.XNC, code="K1", name="Bok",
                     xnc=XNCParams(length=length, width=width, thickness=thickness, by_part_size=False, program=prog, **kw))


def lib(*tools) -> ToolLib:
    return ToolLib([XncTool(**t) for t in tools])


# ───────────────────────── Standart to'plam va tekshiruv ─────────────────────────
def test_default_tool_set():
    doc = XncToolsDoc()
    assert len(doc.tools) == 20
    front = [t for t in doc.tools if t.plane == "front"]
    assert [(t.d, t.name) for t in front] == [(35, "Bore35"), (26, "Bore26"), (25, "Bore25"), (20, "Bore20"), (18, "Bore18"),
                                              (15, "Bore15"), (10, "Bore10"), (8, "Bore8"), (7, "Bore7"), (5, "Bore5"),
                                              (4.5, "Bore4.5"), (3, "Bore3")]
    for pl in ("left", "right", "top", "bottom"):
        assert [(t.d, t.name) for t in doc.tools if t.plane == pl] == [(8, "Bore8"), (4.5, "Bore4.5")]
    assert not any(t.through or t.depth for t in doc.tools) and all(t.comment == "" for t in doc.tools)


def test_tool_validation():
    with pytest.raises(ValidationError):
        XncTool(plane="front", d=0, name="x")                                   # diametr > 0
    with pytest.raises(ValidationError):
        XncTool(plane="back", d=8, name="x")                                    # noma'lum tekislik
    with pytest.raises(ValidationError):
        XncTool(plane="front", d=8, name="   ")                                 # nom bo'sh
    with pytest.raises(ValidationError):
        XncTool(plane="front", d=8, name="x", depth=-1)
    assert XncTool(plane="left", d=8, name="  Bore8 ", through=True).through is False       # o'tuvchi — faqat frontal
    assert XncTool(plane="left", d=8, name="  Bore8 ").name == "Bore8"
    t = XncTool.model_validate({"d": 6, "name": "T6"})                           # eski/qisman JSON: tekislik — frontal
    assert t.plane == "front" and t.depth is None and t.comment == ""
    # nom (tekislik bo'yicha) takrorlanmaydi; boshqa tekislikda bir xil nom mumkin
    with pytest.raises(ValidationError):
        XncToolsDoc(tools=[XncTool(d=8, name="A"), XncTool(d=9, name="a")])
    XncToolsDoc(tools=[XncTool(plane="front", d=8, name="A"), XncTool(plane="left", d=8, name="A")])
    assert XncToolsDoc.model_validate({}).tools == XncToolsDoc().tools            # tools yo'q — standart to'plam
    assert XncToolsDoc.model_validate({"tools": []}).tools == []                  # bo'sh jadval ham mumkin


def test_tool_library_lookup_plane_then_name():
    lb = lib(dict(plane="front", d=9, name="X"), dict(plane="left", d=8, name="X"), dict(plane="top", d=4, name="Y"))
    assert lb.find("X", "left").d == 8 and lb.find("X", "front").d == 9
    assert lb.find("x", "right").d == 9                                           # shu tekislikda yo'q — nom bo'yicha birinchisi
    assert lb.find("Y").d == 4 and lb.find("Z") is None and lb.find("") is None
    assert not ToolLib([]) and lb


# ───────────────────────── Hisobda zaxira ─────────────────────────
def ops(prog, tool_lib, **kw):
    return list(X.evaluate(prog, kw.get("dx", 200), kw.get("dy", 100), kw.get("dz", 16), tool_lib=tool_lib))


def test_drill_diameter_and_depth_from_library():
    lb = library_of()
    o = ops([cmd("DrillFront", X=50, Y=50, T="Bore35")], lb)[0]
    assert o["D"] == 35 and o["DP"] == 16                                         # chuqurlik berilmagan — qalinlik (avvalgidek)
    assert ops([cmd("DrillFront", X=50, Y=50, T="Bore35")], {})[0]["D"] == 5.0    # jadvalsiz — avvalgi standart
    lb2 = lib(dict(plane="front", d=12, name="Cup", depth=11), dict(plane="front", d=6, name="Thru", through=True, depth=9),
              dict(plane="left", d=8, name="Dow", depth=30))
    o = ops([cmd("DrillFront", X=50, Y=50, T="Cup")], lb2)[0]
    assert (o["D"], o["DP"]) == (12, 11)
    o = ops([cmd("DrillFront", X=50, Y=50, T="Thru")], lb2)[0]
    assert (o["D"], o["DP"]) == (6, 16)                                           # o'tuvchi asbob — qalinlik
    o = ops([cmd("DrillLeft", Y=50, Z=8, T="Dow")], lb2)[0]
    assert (o["D"], o["DP"]) == (8, 30)
    assert ops([cmd("DrillFront", X=50, Y=50, T="Unknown")], lb2)[0]["D"] == 5.0  # jadvalda yo'q — standart
    # yon tekislik: (tekislik, nom) aniq mos
    lb3 = lib(dict(plane="front", d=9, name="B"), dict(plane="top", d=7, name="B"))
    assert ops([cmd("DrillTop", X=50, Z=8, T="B")], lb3)[0]["D"] == 7
    assert ops([cmd("DrillFront", X=50, Y=50, T="B")], lb3)[0]["D"] == 9
    assert ops([cmd("DrillLeft", Y=50, Z=8, T="B")], lb3)[0]["D"] == 9           # chap tekislikda yo'q — nom bo'yicha


def test_priority_command_then_program_tool_then_library():
    lb = lib(dict(plane="front", d=12, name="B", depth=11))
    # buyruqdagi D / DP hammadan ustun
    o = ops([cmd("DrillFront", X=50, Y=50, T="B", D=7, DP=4)], lb)[0]
    assert (o["D"], o["DP"]) == (7, 4)
    # dasturdagi Tool ustun (diametr); chuqurlik jadvaldan
    o = ops([cmd("Tool", N="B", D=9), cmd("DrillFront", X=50, Y=50, T="B")], lb)[0]
    assert (o["D"], o["DP"]) == (9, 11)
    # Tool D siz — jadval diametri
    o = ops([cmd("Tool", N="B"), cmd("DrillFront", X=50, Y=50, T="B")], lb)[0]
    assert o["D"] == 12
    # jadvalsiz Tool D siz — 0 (avvalgidek)
    assert ops([cmd("Tool", N="B"), cmd("DrillFront", X=50, Y=50, T="B")], {})[0]["D"] == 0
    # oldingi buyruqdagi DP (meros) jadval chuqurligidan ustun
    o = ops([cmd("DrillFront", X=50, Y=50, T="B", DP=5), cmd("DrillFront", X=80, Y=50, T="B")], lb)
    assert [x["DP"] for x in o] == [5, 5]


def test_mill_and_groove_diameter_from_library():
    lb = lib(dict(plane="front", d=10, name="Mill10"), dict(plane="front", d=4, name="Saw4"), dict(plane="front", d=3, name="Saw3"))
    o = ops([cmd("MillStart", X=0, Y=0, DP=5, T="Mill10"), cmd("MillLine", X=50, Y=0)], lb)
    assert o[0]["D"] == 10 and o[0]["SXY"] == 5                                   # tekislikdagi qadam D/2
    assert ops([cmd("MillStart", X=0, Y=0, DP=5, T="Mill10")], {})[0]["D"] == 0
    g = ops([cmd("Groove", X1=0, Y1=50, X2=100, Y2=50, W=6, DP=5, T="Saw3")], lb)[0]
    assert g["D"] == 3
    assert X.groove_passes(6, 3) == 1 + 2 and ops([cmd("Groove", X1=0, Y1=50, X2=100, Y2=50, W=6, DP=5, T="No")], lb)[0]["D"] == 4.0


def test_stats_and_machine_program_use_library_via_provider():
    calls = []
    prev = X._TOOL_LIB_PROVIDER
    X.set_tool_library_provider(lambda: calls.append(1) or lib(dict(plane="front", d=12, name="Mine")))
    try:
        op = xop([cmd("DrillFront", X=50, Y=50, DP=8, T="Mine")])
        p = X.machine_program(op)
        assert p["ops"][0]["d"] == 12 and p["tools"][0]["name"] == "Mine" and p["tools"][0]["d"] == 12 and calls
        assert X.xnc_stats(op.xnc)["drills"] == 1
        # aniq jadval / bo'sh jadval provayderdan ustun
        assert ops([cmd("DrillFront", X=50, Y=50, T="Mine")], {})[0]["D"] == 5.0
    finally:
        X.set_tool_library_provider(prev)
    # provayder xatosi hisobni buzmaydi
    X.set_tool_library_provider(lambda: 1 / 0)
    try:
        assert ops([cmd("DrillFront", X=50, Y=50, T="Mine")], None)[0]["D"] == 5.0
    finally:
        X.set_tool_library_provider(prev)


def test_no_provider_means_unchanged_behaviour():
    prev = X._TOOL_LIB_PROVIDER
    X.set_tool_library_provider(None)
    try:
        assert ops([cmd("DrillFront", X=50, Y=50, T="Bore35")], None)[0]["D"] == 5.0
        st = X.program_stats([cmd("DrillFront", X=50, Y=50, T="Bore35")], 200, 100, 16)
        assert st["drills"] == 1
    finally:
        X.set_tool_library_provider(prev)


def test_library_does_not_change_counts_of_programs_with_own_tools():
    prog = [cmd("Tool", N="B8", D=8), cmd("DrillFront", X=30, Y=20, DP=12, T="B8"),
            cmd("Tool", N="M6", D=6), cmd("MillStart", X=10, Y=10, DP=8, T="M6"), cmd("MillLine", X=100, Y=10),
            cmd("Tool", N="S4", D=4), cmd("Groove", X1=0, Y1=60, X2=200, Y2=60, W=10, DP=8, T="S4")]
    a = X.program_stats(prog, 200, 100, 16, tool_lib={})
    b = X.program_stats(prog, 200, 100, 16, tool_lib=library_of())
    assert a == b


# ───────────────────────── Sozlama API ─────────────────────────
@pytest.fixture()
def reset_tools(client):
    yield
    client.put("/api/settings/xnc_tools/default", json={})
    client.put("/api/settings/xnc_palette/default", json={})


def test_tools_settings_api_roundtrip_and_cache(client, reset_tools):
    d = client.get("/api/settings/xnc_tools/default").json()
    assert len(d["tools"]) == 20 and d["tools"][0] == dict(plane="front", d=35, through=False, name="Bore35", depth=None, comment="")
    assert {"xnc_tools", "xnc_palette"} <= set(client.get("/api/settings").json())
    d["tools"].append(dict(plane="front", d=12.5, through=False, name="MyCup", depth=11, comment="shisha"))
    assert client.put("/api/settings/xnc_tools/default", json=d).status_code == 200
    assert client.get("/api/settings/xnc_tools/default").json()["tools"][-1]["name"] == "MyCup"
    # kesh darhol yangilanadi (hisob yangi asbobni ko'radi)
    assert XT.current_library().find("MyCup", "front").d == 12.5
    o = list(X.evaluate([cmd("DrillFront", X=50, Y=50, T="MyCup")], 200, 100, 16))[0]
    assert (o["D"], o["DP"]) == (12.5, 11)
    # takrorlangan nom — 4xx, avvalgisi saqlanadi
    bad = dict(d, tools=[*d["tools"], dict(plane="front", d=3, name="mycup")])
    assert 400 <= client.put("/api/settings/xnc_tools/default", json=bad).status_code < 500
    assert 400 <= client.put("/api/settings/xnc_tools/default", json=dict(tools=[dict(plane="front", d=3, name="")])).status_code < 500
    assert len(client.get("/api/settings/xnc_tools/default").json()["tools"]) == 21
    # standartga qaytarish
    client.put("/api/settings/xnc_tools/default", json={})
    assert len(client.get("/api/settings/xnc_tools/default").json()["tools"]) == 20
    assert XT.current_library().find("MyCup") is None


def test_library_reaches_postprocess_and_stats(client, kravat, reset_tools):
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    _set_prog(client, pid, xid, [dict(cmd="DrillFront", params=dict(X=30, Y=20, T="MyCup"), comment="", children=[]),
                                 dict(cmd="DrillFront", params=dict(X=80, Y=20, T="Bore8", DP=12), comment="", children=[])])
    get = lambda: json.loads(client.get(f"/api/projects/{pid}/operations/{xid}/postprocess",           # noqa: E731
                                        params={"key": "json"}).content)["xnc"]["ops"]
    assert [o["d"] for o in get()] == [5.0, 8.0]                                  # MyCup yo'q → 5 mm; Bore8 → standart jadval
    tools = client.get("/api/settings/xnc_tools/default").json()
    tools["tools"].append(dict(plane="front", d=14, through=False, name="MyCup", depth=10, comment=""))
    client.put("/api/settings/xnc_tools/default", json=tools)
    o = get()
    assert [x["d"] for x in o] == [14.0, 8.0] and o[0]["depth"] == 10
    st = client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()
    assert st["drills"] == 2                                                      # sanoq o'zgarmaydi


# ───────────────────────── Palitra ─────────────────────────
def test_palette_default_and_normalization():
    p = XncPalette()
    assert [i.cmd for i in p.items] == list(XT.ALL_CMDS) and all(i.enabled for i in p.items)
    assert len(p.items) == 31 and p.items[0].cmd == "Com" and p.items[-1].cmd == "Origin"
    q = XncPalette.model_validate({"items": [{"cmd": "Groove", "enabled": False}, {"cmd": "Nope"}, {"cmd": "DrillFront"},
                                             {"cmd": "Groove", "enabled": True}, "MillRect"]})
    cmds = [i.cmd for i in q.items]
    assert cmds[:3] == ["Groove", "DrillFront", "MillRect"] and len(cmds) == 31 and len(set(cmds)) == 31 and "Nope" not in cmds
    assert q.items[0].enabled is False and all(i.enabled for i in q.items[1:])      # yetishmaganlari yoqilgan holda oxirida
    assert "Groove" not in q.enabled_cmds() and q.enabled_cmds()[0] == "DrillFront"
    assert XncPalette.model_validate({}).items == p.items and XncPalette.model_validate({"items": None}).items == p.items
    assert XncPalette.model_validate(q.model_dump()) == q


def test_palette_api_roundtrip(client, reset_tools):
    d = client.get("/api/settings/xnc_palette/default").json()
    assert len(d["items"]) == 31
    items = [dict(i) for i in d["items"]]
    items[items.index(next(i for i in items if i["cmd"] == "Origin"))]["enabled"] = False
    items.reverse()
    assert client.put("/api/settings/xnc_palette/default", json=dict(items=items)).status_code == 200
    d2 = client.get("/api/settings/xnc_palette/default").json()
    assert d2["items"][0]["cmd"] == "Origin" and d2["items"][0]["enabled"] is False and d2["items"][-1]["cmd"] == "Com"
    assert XT.current_palette().enabled_cmds()[0] == "Groove" and "Origin" not in XT.current_palette().enabled_cmds()
    client.put("/api/settings/xnc_palette/default", json={})
    assert [i["cmd"] for i in client.get("/api/settings/xnc_palette/default").json()["items"]] == list(XT.ALL_CMDS)


def test_old_project_json_still_loads_and_calculates(client, kravat, reset_tools):
    """Eski loyiha JSON (asbob sozlamasi / cheklov maydonlari yo'q) hech qanday o'zgarishsiz ochiladi va hisoblanadi."""
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    _set_prog(client, pid, xid, [dict(cmd="Tool", params=dict(N="B8", D=8), comment="", children=[]),
                                 dict(cmd="DrillFront", params=dict(X=30, Y=20, DP=12, T="B8"), comment="", children=[])])
    st = client.get(f"/api/projects/{pid}/operations/{xid}/xnc-stats").json()
    assert st["drills"] == 1 and st["errors"] == 0 and st["constraint_issues"] == []
