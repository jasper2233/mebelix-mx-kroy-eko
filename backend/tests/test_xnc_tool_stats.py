# XNC ishi asbob bo'yicha (2026-10-25, foydalanuvchi talabi): MES moliya har asbob ishiga alohida narx qo'yadi — parma — teshik,
# freza / arra — metr. Sintetik dastur (korxona fayllari ishlatilmaydi).
import math

from app.models import XNCParams, XncCommand as C
from app.services import xnc as X
from app.services.xnc_tool_stats import op_tool_usage, project_tool_summary
from test_qa_fix_calc import _set_prog, _xnc_for

PROG = [
    C(cmd="DrillFront", params={"X": 50, "Y": 50, "DP": 12, "D": 5, "T": "Bore5"}),
    C(cmd="DrillFront", params={"X": 100, "Y": 50, "DP": 12, "D": 5, "T": "Bore5"}),
    C(cmd="DrillFront", params={"X": 150, "Y": 50, "DP": 16, "D": 8, "T": "BoreTh8"}),       # teshib o'tadi (16 mm)
    C(cmd="DrillLeft", params={"Y": 100, "Z": 8, "DP": 30, "D": 8, "T": "Bore8"}),
    C(cmd="MillStart", params={"X": 100, "Y": 100, "DP": 8, "D": 8, "T": "Mill8", "C": 0}),
    C(cmd="MillLine", params={"X": 300, "Y": 100}),
    C(cmd="MillLine", params={"X": 300, "Y": 200}),
    C(cmd="Groove", params={"X1": 0, "Y1": 300, "X2": 400, "Y2": 300, "DP": 8, "W": 4, "D": 4, "T": "Cut4"}),
]


def test_op_tool_usage_matches_program_stats():
    x = XNCParams(length=500, width=400, thickness=16, qty=1, program=PROG)
    uses, errs = op_tool_usage(x)
    by = {(u["kind"], u["name"]): u for u in uses}
    assert by[("drill", "Bore5")]["holes"] == 2 and by[("drill", "Bore5")]["side"] == "face" and not by[("drill", "Bore5")]["through"]
    assert by[("drill", "BoreTh8")]["through"] is True and by[("drill", "BoreTh8")]["holes"] == 1
    assert by[("drill", "Bore8")]["side"] == "side" and by[("drill", "Bore8")]["holes"] == 1
    assert math.isclose(by[("mill", "Mill8")]["mill_m"], 0.3, abs_tol=1e-6)            # 200 + 100 mm
    assert math.isclose(by[("saw", "Cut4")]["saw_m"], 0.4, abs_tol=1e-6)
    st = X.program_stats(x.program, 500, 400, 16, X.program_vars(x), x.par_values)
    assert sum(u["holes"] for u in uses) == st["drills"]
    assert math.isclose(sum(u["mill_m"] for u in uses), st["mill_m"], abs_tol=1e-3)
    assert math.isclose(sum(u["saw_m"] for u in uses), st["saw_m"], abs_tol=1e-3)
    assert not errs


def test_project_summary_and_mes_package(client, kravat):
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    _set_prog(client, pid, xid, [c.model_dump() for c in PROG])
    s = client.get(f"/api/projects/{pid}/xnc-tools").json()
    assert s["xnc_ops"] == 1 and s["xnc_parts"] >= 1
    t = {(u["kind"], u["name"]): u for u in s["tools"]}
    q = s["xnc_parts"]
    assert t[("drill", "Bore5")]["holes"] == 2 * q and t[("drill", "Bore5")]["parts"] == q
    assert math.isclose(t[("mill", "Mill8")]["mill_m"], 0.3 * q, abs_tol=1e-3)
    assert t[("drill", "Bore5")]["uses"][0]["op_id"] == xid
    pkg = client.get(f"/api/projects/{pid}/mes-package").json()
    assert pkg["xnc_tools"]["xnc_ops"] == 1
    assert {(u["kind"], u["name"]) for u in pkg["xnc_tools"]["tools"]} == set(t)
    sch = client.get("/api/mes-package/schema").json()
    assert "xnc_tools" in sch["properties"]
    assert project_tool_summary.__doc__


def test_xnc_mes_settings_codes_and_filters(client, kravat):
    """«XNC → MES»: asbobning MES kodi paketga qo'shiladi; o'chirilgan qiymatlar yuborilmaydi; umuman o'chiq — bo'sh."""
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    _set_prog(client, pid, xid, [c.model_dump() for c in PROG])
    base = client.get("/api/settings/xnc_mes/default").json()
    try:
        cfg = {"enabled": True, "send_holes": True, "send_mill": True, "send_mill_passes": False, "send_saw": False, "send_parts": False,
               "codes": [{"kind": "drill", "name": "Bore5", "d": 5, "side": "face", "through": False, "mes_code": "FIN-D5", "comment": ""}]}
        assert client.put("/api/settings/xnc_mes/default", json=cfg).status_code == 200
        pkg = client.get(f"/api/projects/{pid}/mes-package").json()["xnc_tools"]
        t = {(u["kind"], u["name"]): u for u in pkg["tools"]}
        assert t[("drill", "Bore5")]["mes_code"] == "FIN-D5"
        assert ("saw", "Cut4") not in t                                    # arra yuborilmaydi
        assert t[("mill", "Mill8")]["mill_pass_m"] == 0 and t[("mill", "Mill8")]["mill_m"] > 0
        assert all(u["uses"] == [] for u in pkg["tools"])                  # batafsil yo'q
        v = client.get(f"/api/projects/{pid}/xnc-tools").json()
        assert any(u["name"] == "Cut4" for u in v["tools"]) and not any(u["name"] == "Cut4" for u in v["mes"]["tools"])
        rows = client.get("/api/xnc-mes/tools", params={"pid": pid}).json()
        assert any(r["name"] == "Mill8" and r["in_project"] for r in rows)
        assert any(r["name"] == "Bore5" and r["mes_code"] == "FIN-D5" for r in rows)
        cfg["enabled"] = False
        client.put("/api/settings/xnc_mes/default", json=cfg)
        pkg = client.get(f"/api/projects/{pid}/mes-package").json()["xnc_tools"]
        assert pkg["enabled"] is False and pkg["tools"] == []
    finally:
        client.put("/api/settings/xnc_mes/default", json=base)
