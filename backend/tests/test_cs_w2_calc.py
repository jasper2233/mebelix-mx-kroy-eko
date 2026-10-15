"""W2 — CS hisob-kitob bo'shliqlari: kroygacha/keyin material va list miqdori (CS-036/037), detallar maydoni zagotovka
(pripuskli pilniy o'lcham) bo'yicha (CS-081)."""
import math

from app.models import Operation, OpType, Part, Project, CSCutParams
from app.services import calc


def _op(p, oid):
    return next(o for o in p["operations"] if o["id"] == oid)


def _quantities(client, pid, cs):
    r = client.get(f"/api/projects/{pid}/operations/{cs}/cs-quantities")
    assert r.status_code == 200, r.text
    return r.json()


def test_quantities_before_cut_are_estimated(client, kravat):
    pid, cs, _el = kravat
    op = _op(client.get(f"/api/projects/{pid}").json(), cs)
    area = sum(pt["length"] * pt["width"] * pt["qty"] for pt in op["parts"]) / 1e6          # kromka qalinligi 0
    est = area * (2 - op["cs_material"]["est_fill_percent"] / 100)
    sheet = op["sheets"][0]["length"] * op["sheets"][0]["width"] / 1e6
    q = _quantities(client, pid, cs)
    assert q["estimated"] is True
    assert math.isclose(q["parts_area_m2"], round(area, 4), abs_tol=1e-4)
    assert math.isclose(q["material_qty_m2"], round(est, 4), abs_tol=1e-4)
    assert q["sheets"] == math.ceil(est / sheet - 1e-9) == q["sheets_total"]
    assert math.isclose(q["sheet_area_m2"], round(sheet, 4), abs_tol=1e-4)


def test_quantities_after_cut_come_from_result(client, kravat):
    pid, cs, _el = kravat
    res = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").json()
    q = _quantities(client, pid, cs)
    assert q["estimated"] is False
    assert q["sheets_total"] == res["total_sheets"] and math.isclose(q["material_qty_m2"], res["material_qty_m2"], abs_tol=1e-4)
    assert q["sheets"] >= 1                                                  # yangi listlar (yaxlitlangan) — narx asosi
    assert math.isclose(q["parts_area_m2"], round(sum(
        pt["length"] * pt["width"] * pt["qty"] for pt in _op(client.get(f"/api/projects/{pid}").json(), cs)["parts"]) / 1e6, 4),
        abs_tol=1e-4)


def test_quantities_estimate_ignores_remnant_first_sheet(client, kravat):
    """Ro'yxatning boshida ombor qoldig'i turgan bo'lsa ham, taxmin yangi list maydoni bo'yicha."""
    pid, cs, _el = kravat
    client.put(f"/api/projects/{pid}/operations/{cs}/sheets",
               json=[{"length": 600, "width": 400, "qty": 3, "is_remnant": True}, {"length": 2750, "width": 1830, "qty": 10000}])
    q = _quantities(client, pid, cs)
    assert math.isclose(q["sheet_area_m2"], round(2750 * 1830 / 1e6, 4), abs_tol=1e-4)
    assert q["sheets"] < 10                                                  # qoldiq maydoni bo'yicha (0.24 m²) bo'lsa — 80+ list


def test_quantities_errors(client, kravat):
    pid, _cs, el = kravat
    assert client.get(f"/api/projects/{pid}/operations/{el}/cs-quantities").status_code == 400      # CS emas
    assert client.get("/api/projects/nope/operations/x/cs-quantities").status_code == 404


def test_parts_area_uses_saw_size_with_allowance(client):
    """«Площадь» — zagotovka + pripusk (pilniy) o'lchamidan; detal (kromkali) o'lchamidan emas."""
    pid = client.post("/api/projects", json={"name": "Maydon"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "code": "E", "name": "PVC"}).json()
    el = p["operations"][-1]["id"]
    client.patch(f"/api/projects/{pid}/operations/{el}", json={"el": {"thickness": 2}})
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "LDSP16", "name": "L"}).json()
    cs = p["operations"][-1]["id"]
    client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": {"machining_allowance": 3}})
    client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[
        dict(name="A", length=500, width=300, qty=2, edge_left={"op_id": el}, edge_right={"op_id": el}, allow_top=1)])
    # detal 500×300, ikki chap/o'ng kromka 2+2 → zagotovka 496×300; pilniy = +2·3 (umumiy) + 1 (yuqori pripusk) → 502×307
    q = _quantities(client, pid, cs)
    assert math.isclose(q["parts_area_m2"], round(502 * 307 * 2 / 1e6, 4), abs_tol=1e-4)
    assert not math.isclose(q["parts_area_m2"], 500 * 300 * 2 / 1e6, abs_tol=1e-4)
    proj = client.get(f"/api/projects/{pid}").json()
    from app import store
    obj = store.load(pid)
    assert math.isclose(calc.parts_area_m2(obj, next(o for o in obj.operations if o.type == OpType.CS)), 502 * 307 * 2 / 1e6)


def test_estimate_consumption_unchanged_formula():
    """Eski formula: sarf = detallar (pilniy) maydoni × (2 − taxminiy foiz / 100)."""
    part = Part(uid=1, name="x", length=1000, width=1000, qty=1)
    op = Operation(type=OpType.CS, name="m", parts=[part], cs_cut=CSCutParams())
    proj = Project(name="p", operations=[op])
    assert math.isclose(calc.estimate_consumption_m2(proj, op), 1.0 * 1.1)
