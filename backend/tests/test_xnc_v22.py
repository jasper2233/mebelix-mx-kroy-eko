"""XNC dasturi (v2.2): teshik massivi AC/AS/AV, «oldingi qiymat» qoidasi, «Включить», butun tipli o'zgaruvchi,
GibLab ifoda tili (if, =, <>, ^, xor, radian)."""
import pytest

from app.models import XncCommand
from app.services.xnc import evaluate, program_stats


def C(cmd, enabled=True, children=None, **params):
    return XncCommand(cmd=cmd, params=params, enabled=enabled, children=children or [])


def holes(prog, dx=800, dy=600, dz=16):
    return [(o["X"], o["Y"]) for o in evaluate(prog, dx, dy, dz) if o["kind"].startswith("Drill")]


def test_drill_array_horizontal_and_vertical():
    # AV yo'q / false — X bo'ylab; true — Y bo'ylab
    assert holes([C("DrillFront", X=100, Y=50, DP=12, AC=3, AS=32)]) == [(100, 50), (132, 50), (164, 50)]
    assert holes([C("DrillFront", X=100, Y=50, DP=12, AC=3, AS=32, AV="true")]) == [(100, 50), (100, 82), (100, 114)]
    assert holes([C("DrillFront", X=100, Y=50, DP=12, AC=2, AS=-10, AV="false")]) == [(100, 50), (90, 50)]
    assert program_stats([C("DrillFront", X=100, Y=50, DP=12, AC=5, AS=32)], 800, 600, 16)["drills"] == 5
    # massiv bir qismi detaldan tashqarida — tashqaridagilar sanalmaydi
    assert program_stats([C("DrillFront", X=700, Y=50, DP=12, AC=5, AS=50)], 800, 600, 16)["drills"] == 3
    # ifodali massiv: AC=dx/200 -> 4 ta (haqiqiy / butun: dx double)
    assert program_stats([C("DrillFront", X=10, Y=10, DP=12, AC="dx/200", AS=20)], 800, 600, 16)["drills"] == 4
    # AC=1 yoki yo'q — bitta
    assert holes([C("DrillFront", X=1, Y=2, DP=12, AC=1, AS=5)]) == [(1, 2)]


def test_previous_value_rule():
    prog = [C("DrillFront", X=100, Y=50, DP=12, T="B8", AC=2, AS=32),
            C("DrillFront", Y=90),                                   # X, DP, T, AC, AS — oldingidan
            C("DrillFront", X=300)]                                  # Y=90 oldingidan
    ops = evaluate(prog, 800, 600, 16)
    assert [(o["X"], o["Y"], o["DP"], o["T"]) for o in ops] == [
        (100, 50, 12, "B8"), (132, 50, 12, "B8"), (100, 90, 12, "B8"), (132, 90, 12, "B8"),
        (300, 90, 12, "B8"), (332, 90, 12, "B8")]
    # turlar mustaqil: chap teshik oldingi chap teshikdan oladi, frontaldan emas
    prog = [C("DrillFront", X=10, Y=10, DP=5), C("DrillLeft", Y=70, DP=30), C("DrillLeft")]
    ops = evaluate(prog, 800, 600, 16)
    assert [(o["kind"], o["Y"], o["DP"]) for o in ops] == [("DrillFront", 10, 5), ("DrillLeft", 70, 30), ("DrillLeft", 70, 30)]


def test_previous_value_mill_contour_and_groove():
    prog = [C("MillStart", X=0, Y=0, DP=8, T="M6"), C("MillLine", X=100), C("MillLine", Y=50)]
    ops = [o for o in evaluate(prog, 800, 600, 16) if o["kind"] == "MillLine"]
    assert [(o["X"], o["Y"]) for o in ops] == [(100, 0), (100, 50)]      # kontur: yo'q koordinata — oldingisi
    st = program_stats(prog, 800, 600, 16)
    assert st["mill_m"] == pytest.approx(0.15)
    prog = [C("Groove", X1=10, Y1=20, X2=200, Y2=20, DP=8, W=4), C("Groove", Y1=40, Y2=40, X2=200)]
    ops = [o for o in evaluate(prog, 800, 600, 16) if o["kind"] == "Groove"]
    assert (ops[1]["X1"], ops[1]["Y1"], ops[1]["X2"]) == (10, 40, 200)


def test_disabled_commands_and_children_skipped():
    prog = [C("DrillFront", X=10, Y=10, DP=5), C("DrillFront", enabled=False, X=20, Y=20, DP=5),
            C("If", cond="1", children=[C("DrillFront", X=30, Y=30, DP=5)]),
            C("If", enabled=False, cond="1", children=[C("DrillFront", X=40, Y=40, DP=5)])]
    assert holes(prog) == [(10, 10), (30, 30)]
    # o'chirilgan buyruq «oldingi qiymat» ni ham yangilamaydi
    prog = [C("DrillFront", X=10, Y=10, DP=5), C("DrillFront", enabled=False, X=99, Y=99, DP=5), C("DrillFront", X=20)]
    assert holes(prog) == [(10, 10), (20, 10)]


def test_int_typed_variable_and_expression_language():
    prog = [C("Var", name="a", value="7/2", type="int"), C("Var", name="b", value="7.0/2"),
            C("DrillFront", X="a", Y="b", DP=5)]
    assert holes(prog) == [(3, 3.5)]                                    # 7/2 butun bo'lish; b haqiqiy
    prog = [C("Var", name="k", value="if(dx>500,10,20)"), C("Var", name="m", value="2^3"),
            C("DrillFront", X="k", Y="m", DP=5), C("DrillFront", X="dx<>800", Y="dx=800", DP=5)]
    assert holes(prog) == [(10, 8), (0, 1)]
    prog = [C("DrillFront", X="cos(pi)*-10", Y="sqrt(100)", DP=5)]
    assert holes(prog, dx=800) == [(10, 10)]                            # cos(pi) = -1 (radian)
    prog = [C("If", cond="dx>500 xor dy>500", children=[C("DrillFront", X=1, Y=1, DP=5)]),
            C("If", cond="true and not false", children=[C("DrillFront", X=2, Y=2, DP=5)])]
    assert holes(prog, dx=800, dy=300) == [(1, 1), (2, 2)]
    assert holes(prog, dx=800, dy=800) == [(2, 2)]


def test_import_enable_attribute_and_array():
    from app.plugins.legacy_project import program_to_commands
    xml = ('<program dx="800" dy="600" dz="16"><bf x="100" y="50" dp="12" ac="3" as="32" av="false"/>'
           '<bf enable="false" x="1" y="1" dp="12"/><bf x="200" y="50" dp="12" ac="2" as="40" av="true"/></program>')
    cmds, size = program_to_commands(xml)
    assert [c.enabled for c in cmds] == [True, False, True]
    assert holes(cmds) == [(100, 50), (132, 50), (164, 50), (200, 50), (200, 90)]
