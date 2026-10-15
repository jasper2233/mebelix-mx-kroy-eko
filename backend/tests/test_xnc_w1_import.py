"""W1 · `.project` importi: yetishmayotgan atributlar — ms sdp/sxy/in/out/c, gr c/p, qirra teshigi m/ver, ml/mac dp,
«oldingi qiymat» (yozilmagan atribut 0 bo'lmaydi), part.allowance*, groupInBlock*. Statistika (korpus mosligi) o'zgarmaydi."""
import math
from xml.sax.saxutils import quoteattr

import pytest

from app.models import OpType
from app.plugins.legacy_project import import_project, program_to_commands
from app.services import xnc as X


def _prog(body, dx=720, dy=560, dz=16):
    return f'<program dx="{dx}" dy="{dy}" dz="{dz}">{body}</program>'


def test_millstart_attributes_imported():
    cmds, size = program_to_commands(_prog(
        '<tool name="M6" d="6"/><ms x="10" y="20" dp="dz" name="M6" c="3" sdp="dz/4" sxy="2.5" in="1" out="0"/>'
        '<ml x="100" y="20"/><ms x="0" y="0" dp="5" name="M6"/>'))
    ms = [c for c in cmds if c.cmd == "MillStart"]
    assert ms[0].params == {"X": 10.0, "Y": 20.0, "DP": "dz", "T": "M6", "C": 3, "SDP": "dz/4", "SXY": 2.5, "IN": 1, "OUT": 0}
    assert ms[1].params["C"] == 0 and "SDP" not in ms[1].params and "IN" not in ms[1].params      # yozilmagan — qo'shilmaydi
    ops = X.evaluate(cmds, *size)
    o = next(o for o in ops if o["kind"] == "MillStart")
    assert (o["C"], o["SDP"], o["SXY"], o["IN"], o["OUT"], o["DP"]) == (3, 4, 2.5, 1, 0, 16)


def test_groove_c_and_p_imported():
    cmds, size = program_to_commands(_prog('<gr x1="0" y1="20" x2="100" y2="20" t="4" dp="8" c="2" p="0" name="S4"/>'
                                           '<gr x1="0" y1="40" x2="100" y2="40" t="4" dp="8" c="0"/>'
                                           '<gr x1="0" y1="60" x2="100" y2="60" t="4" dp="8"/>'))
    assert cmds[0].params["C"] == 2 and cmds[0].params["P"] == 0
    assert cmds[1].params["C"] == 0 and "P" not in cmds[1].params
    assert "C" not in cmds[2].params
    assert [o["C"] for o in X.evaluate(cmds, *size)] == [2, 0, 0]


def test_edge_hole_m_and_ver_imported():
    cmds, size = program_to_commands(_prog(
        '<bl ver="2" y="50" dp="30" z="8" m="true" ac="1" name="B8"/><br ver="2" y="50" dp="30" z="7.5" m="false" name="B8"/>'
        '<bt x="100" dp="30" z="8" name="B8"/><bf x="10" y="10" dp="12" name="B8"/>'))
    bl, br, bt, bf = cmds
    assert bl.params["M"] == "true" and bl.params["VER"] == 2 and br.params["M"] == "false"
    assert "M" not in bt.params and "VER" not in bt.params and "M" not in bf.params       # yozilmagan — yo'q (eski mantiq)
    ops = X.evaluate(cmds, *size)
    zs = [o["Z"] for o in ops if o["kind"] != "DrillFront"]
    assert zs == [8, 7.5, 8]                                                               # dz/2 = 8; m=false — z; M yo'q — z


def test_ml_mac_dp_and_previous_value_rule():
    cmds, size = program_to_commands(_prog(
        '<ms x="0" y="0" dp="10" name="M6"/><ml x="100" dp="6"/><ml y="50"/><mac x="150" y="0" cx="125" cy="25" dir="true" dp="4"/>'
        '<bf x="10" y="10" dp="12" name="B8"/><bf y="90"/>'))
    ml1, ml2, mac = cmds[1], cmds[2], cmds[3]
    assert ml1.params == {"X": 100.0, "DP": 6.0} and ml2.params == {"Y": 50.0}                # yozilmagan atribut — 0 emas
    assert mac.params["DP"] == 4
    ops = X.evaluate(cmds, *size)
    lines = [o for o in ops if o["kind"] == "MillLine"]
    assert [(o["X"], o["Y"]) for o in lines] == [(100, 0), (100, 50)] and lines[0]["DP"] == 6
    assert [(o["X"], o["Y"]) for o in ops if o["kind"] == "DrillFront"] == [(10, 10), (10, 90)]


def _project(part_attrs=""):
    prog = _prog('<tool name="B5" d="5"/><bf x="50" y="50" dp="12" name="B5"/>')
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project name="W1 import" currency="UZS">
  <good typeId="product" id="1" code="P1" name="Shkaf" count="1">
    <part id="11" name="Bok" count="3" dl="720" dw="560" {part_attrs}/>
    <part id="12" name="Polka" count="2" dl="700" dw="300"/>
  </good>
  <good typeId="sheet" id="4" code="LDSP" name="LDSP 16" t="16" l="2750" w="1830" count="2">
    <part id="20" l="2750" w="1830" count="10000"/></good>
  <operation typeId="CS" id="2" t="16"><material id="4" count="2"/><part id="11"/><part id="12"/></operation>
  <operation typeId="XNC" id="7" code="X1" typeName="Bok" count="1" program={quoteattr(prog)}><part id="11"/></operation>
</project>""".encode("utf-8")


def test_part_allowance_and_group_in_block_imported():
    p, w = import_project(_project('allowanceT="2" allowanceB="3.5" allowanceL="1" allowanceR="0" '
                                   'groupInBlock="2" groupInBlockMC="2" groupInBlockMaxC="5"'), "a.project")
    cs = next(o for o in p.operations if o.type == OpType.CS)
    bok = next(x for x in cs.parts if x.name == "Bok")
    polka = next(x for x in cs.parts if x.name == "Polka")
    assert (bok.allow_top, bok.allow_bottom, bok.allow_left, bok.allow_right) == (2, 3.5, 1, 0)
    assert (bok.group_by, bok.group_min, bok.group_max) == ("width", 2, 5)
    assert (polka.allow_top, polka.allow_left, polka.group_by, polka.group_min, polka.group_max) == (0, 0, "none", 0, 0)
    # uzunlik bo'yicha guruhlash
    p, _w = import_project(_project('groupInBlock="1" groupInBlockMC="3"'), "b.project")
    bok = next(x for o in p.operations if o.type == OpType.CS for x in o.parts if x.name == "Bok")
    assert (bok.group_by, bok.group_min, bok.group_max) == ("length", 3, 0)
    # noto'g'ri qiymatlar xatosiz: manfiy pripusk — 0, noma'lum guruhlash kodi — yo'q
    p, _w = import_project(_project('allowanceT="-5" groupInBlock="9" groupInBlockMC="x"'), "c.project")
    bok = next(x for o in p.operations if o.type == OpType.CS for x in o.parts if x.name == "Bok")
    assert bok.allow_top == 0 and bok.group_by == "none" and bok.group_min == 0


def test_allowance_reaches_xnc_variables_and_saw_size(client):
    import_ = client.post("/api/projects/import-file", files={"file": ("a.project", _project('allowanceT="2" allowanceL="4"'))})
    assert import_.status_code == 200, import_.text
    p = import_.json()["project"]
    xo = next(o for o in p["operations"] if o["type"] == "XNC")
    assert xo["xnc"]["part_vars"]["allowanceT"] == 2 and xo["xnc"]["part_vars"]["allowanceL"] == 4
    cs = next(o for o in p["operations"] if o["type"] == "CS")
    assert cs["parts"][0]["allow_top"] == 2                                                # saqlangan


def test_corpus_stats_unchanged_with_new_importer():
    """Importer o'zgarishi XNC hisobini (teshik / freza / paz) o'zgartirmaydi — barcha atributlar bilan."""
    cmds, size = program_to_commands(_prog(
        '<tool name="B5" d="5"/><tool name="M6" d="6"/>'
        '<bf x="37" y="32" dp="12" ac="3" as="32" av="true" name="B5"/><bl ver="2" y="50" dp="30" z="8" m="true" name="B5"/>'
        '<ms x="10" y="10" dp="8" c="2" in="0" out="1" sxy="3" name="M6"/><ml x="110" y="10"/><mac x="130" y="30" cx="110" cy="30" dir="true"/>'
        '<gr x1="0" y1="200" x2="300" y2="200" t="4" dp="8" c="0" p="0" name="S4"/>'))
    st = X.program_stats(cmds, *size)
    assert st["drills"] == 4 and st["errors"] == 0
    assert st["mill_m"] == pytest.approx((100 + math.pi * 20 / 2) / 1000, abs=1e-3)
    assert st["saw_m"] == pytest.approx(0.3, abs=1e-3)
