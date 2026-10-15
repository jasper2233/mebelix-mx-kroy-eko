"""W-parity (W_PARITY_SPEC.md §3, §4): (CL) «Параметры» — beshta yangi parametr; (SP) «Режим размеров».

CL: «Максимальное количество разновидностей деталей на карте кроя» (haqiqiy cheklov — xil = pilniy uzunlik), «Размер остатков с
учетом торцовки» (`waste_incl_trim`), «Объединение деталей» / «Группировка деталей по свойствам» / «Сохранение чертежа карт кроя»
(saqlanadi, 1D kroyga ta'sirsiz). SP: pilniy o'lcham (-1, standart) / zagotovka o'lchami (0)."""
import random

import pytest

from app.models import LEGACY_CTX, CLParams, OpType, Project, SPParams, StockSheet
from app.services import cl_calc
from app.services import cl_optimizer as co
from app.services.cl_optimizer import LItem


def _items(lengths, start=1):
    return [LItem(f"p{i}", i, float(p)) for i, p in enumerate(lengths, start)]


def _stock(L, w=100, qty=10000, **kw):
    return StockSheet(id=kw.pop("id", f"s{L}"), length=L, width=w, qty=qty, **kw)


def _kinds(m) -> int:
    return len({co.u(p.length) for p in m.placements})


def _sig(res):
    return [(m.sheet_id, m.copies, [(p.part_uid, p.x, p.length) for p in m.placements],
             [(o.kind, o.length, o.business) for o in m.offcuts]) for m in res.maps]


# ───────────────────────── (CL) model ─────────────────────────
def test_cl_new_fields_defaults():
    c = CLParams()
    assert (c.max_part_types_per_map, c.merge_parts, c.group_parts, c.save_drawings) == (0, False, 0, False)
    assert c.waste_incl_trim is True


def test_cl_old_json_loads_with_defaults_and_clamps():
    """Eski saqlangan loyiha (yangi maydonlarsiz) ochiladi; chegaradan chiqqan / buzilgan qiymatlar tuzatiladi."""
    raw = {"name": "old", "operations": [
        {"type": "CL", "cl": {"width": 45, "kerf": 4, "trim": 10, "waste_incl_trim": False}},
        {"type": "CL", "cl": {"max_part_types_per_map": 99999, "group_parts": -5, "merge_parts": "x", "save_drawings": None}}]}
    p = Project.model_validate(raw, context=LEGACY_CTX)
    a, b = p.operations[0].cl, p.operations[1].cl
    assert (a.max_part_types_per_map, a.merge_parts, a.group_parts, a.save_drawings) == (0, False, 0, False)
    assert a.waste_incl_trim is False and a.width == 45
    assert (b.max_part_types_per_map, b.group_parts, b.merge_parts, b.save_drawings) == (10000, 0, False, False)


def test_cl_remnant_flag_accepts_cs_name():
    """«Размер остатков с учетом торцовки»: CL da bitta maydon (`waste_incl_trim`); (CS) nomi ham kirishda qabul qilinadi."""
    assert CLParams.model_validate({"remnant_size_incl_trim": False}).waste_incl_trim is False
    assert CLParams.model_validate({"remnant_size_incl_trim": False, "waste_incl_trim": True}).waste_incl_trim is True
    assert "remnant_size_incl_trim" not in CLParams().model_dump()


# ───────────────────────── (CL) Максимальное количество разновидностей ─────────────────────────
@pytest.mark.parametrize("limit", [1, 2, 3, 5, 10])
@pytest.mark.parametrize("quality", ["fast", "normal"])
def test_max_kinds_limits_distinct_parts_per_map(limit, quality):
    rng = random.Random(1000 + limit)
    lengths = []
    for L in rng.sample(range(150, 1900, 7), 14):          # 14 xil uzunlik — har detal o'z uzunligida
        lengths += [L] * rng.randint(2, 9)
    items = []
    uid = 0
    for L in sorted(set(lengths)):
        uid += 1
        items += [LItem(f"p{uid}", uid, float(L))] * lengths.count(L)
    st = [_stock(6000)]
    cl = CLParams(kerf=3, trim=10, max_part_types_per_map=limit, quality=quality)
    res = co.optimize_linear(items, st, cl)
    assert not res.unplaced and res.total_parts == len(items)
    assert co.validate_cl(res, items, st, cl) == []
    assert max(_kinds(m) for m in res.maps) <= limit
    assert max(len({p.part_uid for p in m.placements}) for m in res.maps) <= limit       # har uzunlik — bitta detal
    free = co.optimize_linear(items, st, CLParams(kerf=3, trim=10, quality=quality))
    assert res.total_sheets >= free.total_sheets                                          # cheklov materialni tejamaydi


def test_max_kinds_one_means_single_length_strips():
    items = _items([1000] * 5 + [700] * 5 + [300] * 5)
    st = [_stock(3000)]
    cl = CLParams(kerf=3, trim=10, max_part_types_per_map=1)
    res = co.optimize_linear(items, st, cl)
    assert co.validate_cl(res, items, st, cl) == [] and not res.unplaced
    assert all(_kinds(m) == 1 for m in res.maps)
    free = co.optimize_linear(items, st, CLParams(kerf=3, trim=10))
    assert any(_kinds(m) > 1 for m in free.maps)                                          # cheklovsiz — aralash sxemalar


def test_max_kinds_with_limited_stock_and_two_strip_types():
    """Cheklangan (qoldiq) polosa + cheksiz: cheklov ikkala turda ham saqlanadi, polosa soni oshmaydi."""
    rng = random.Random(7)
    items = _items([rng.choice([420, 515, 630, 780, 905, 1210]) for _i in range(60)])
    st = [_stock(2500, qty=3, id="rem", is_remnant=True), _stock(6000, id="new")]
    cl = CLParams(kerf=4, trim=15, max_part_types_per_map=2, quality="max")
    res = co.optimize_linear(items, st, cl)
    assert co.validate_cl(res, items, st, cl) == [] and not res.unplaced
    assert all(_kinds(m) <= 2 for m in res.maps)
    assert sum(m.copies for m in res.maps if m.sheet_id == "rem") <= 3


def test_default_and_zero_limit_give_identical_result():
    """Standart qiymatlarda natija o'zgarmaydi: 0 (cheklanmagan) — avvalgi algoritm yo'li; saqlanadigan belgilar ta'sirsiz."""
    rng = random.Random(42)
    items = _items([rng.choice([333, 450, 615, 800, 1250, 1740]) for _i in range(80)])
    st = [_stock(6000)]
    base = co.optimize_linear(items, st, CLParams(kerf=3, trim=10))
    same = co.optimize_linear(items, st, CLParams(kerf=3, trim=10, max_part_types_per_map=0, merge_parts=True, group_parts=3,
                                                   save_drawings=True))
    assert _sig(base) == _sig(same)
    assert (base.total_sheets, base.total_cuts, base.total_fill_percent) == (same.total_sheets, same.total_cuts, same.total_fill_percent)


def test_best_pattern_limited_is_exact():
    """Cheklovli eng zich sxema — to'liq saralash bilan solishtirish (kichik masalalar)."""
    from itertools import combinations, product
    rng = random.Random(5)
    for _case in range(60):
        k = rng.choice([0, 3, 5]) * 100
        dem = {rng.randrange(100, 900) * 100: rng.randint(1, 4) for _i in range(rng.randint(1, 6))}
        cap = rng.randrange(900, 3000) * 100
        T = rng.randint(1, 3)
        best = 0
        for combo in combinations(sorted(dem), min(T, len(dem))):
            for cnt in product(*[range(dem[p] + 1) for p in combo]):
                w = sum((p + k) * n for p, n in zip(combo, cnt))
                if w <= cap:
                    best = max(best, w)
        s, pat = co._best_pattern(cap, dem, k, max_types=T)
        assert s == best, (cap, dem, k, T)
        assert len(pat) <= T and all(0 < n <= dem[p] for p, n in pat.items())
        assert sum((p + k) * n for p, n in pat.items()) == s
        big = max(dem)
        s2, pat2 = co._best_pattern(cap, dem, k, must=big, max_types=T)
        if big + k <= cap:
            assert pat2.get(big, 0) >= 1 and len(pat2) <= T and sum((p + k) * n for p, n in pat2.items()) == s2 <= cap


# ───────────────────────── (CL) Размер остатков с учетом торцовки ─────────────────────────
def test_remnant_size_with_trim_changes_length_and_class():
    """✓ — qoldiq toza uzunligi (80) va oxirgi torsovka kesimi; ☐ — torsovka zonasi bilan (110): tasnif shu uzunlik bo'yicha."""
    items = _items([780, 500, 150])
    st = [_stock(1600, 360)]
    on = co.optimize_linear(items, st, CLParams(width=360, kerf=10, trim=20, waste_min=0, business_min=100)).maps[0]
    off = co.optimize_linear(items, st, CLParams(width=360, kerf=10, trim=20, waste_min=0, business_min=100,
                                                 waste_incl_trim=False)).maps[0]
    r_on = next(o for o in on.offcuts if o.kind == "remnant")
    r_off = next(o for o in off.offcuts if o.kind == "remnant")
    assert (r_on.length, r_on.business, on.cuts_count) == (80.0, False, 5)
    assert (r_off.length, r_off.business, off.cuts_count) == (110.0, True, 4)


# ───────────────────────── (CL) saqlanadigan belgilar: API, eskirish, import / eksport ─────────────────────────
def _new_cl(client, **cl):
    pid = client.post("/api/projects", json={"name": "CL parity"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CL", "name": "Profil", "code": "PR"}).json()
    oid = p["operations"][-1]["id"]
    if cl:
        r = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cl": cl})
        assert r.status_code == 200, r.text
    return pid, oid


def _op(client, pid, oid):
    return next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)


def test_api_new_cl_has_fields_and_limit_is_applied(client):
    pid, oid = _new_cl(client, width=100, kerf=3, trim=10)
    c = _op(client, pid, oid)["cl"]
    assert (c["max_part_types_per_map"], c["merge_parts"], c["group_parts"], c["save_drawings"]) == (0, False, 0, False)
    body = [dict(name=f"P{i}", length=L, width=0, qty=q) for i, (L, q) in enumerate([(1000, 6), (750, 6), (430, 6), (260, 6)], 1)]
    assert client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=body).status_code == 200
    r = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cl": {"max_part_types_per_map": 2}})
    assert r.status_code == 200, r.text
    res = client.post(f"/api/projects/{pid}/operations/{oid}/optimize")
    assert res.status_code == 200, res.text
    res = res.json()
    assert res["total_parts"] == 24 and not res["unplaced"]
    assert all(len({p["part_uid"] for p in m["placements"]}) <= 2 for m in res["maps"])
    assert client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cl": {"max_part_types_per_map": -1}}).status_code == 422


def test_stored_flags_keep_result_but_limit_invalidates(client):
    pid, oid = _new_cl(client, width=100, kerf=3, trim=10)
    client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=[dict(name="A", length=900, width=0, qty=5)])
    assert client.post(f"/api/projects/{pid}/operations/{oid}/optimize").status_code == 200
    r = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cl": {"merge_parts": True, "group_parts": 1, "save_drawings": True}})
    assert r.status_code == 200, r.text
    op = _op(client, pid, oid)
    assert op["cl"]["merge_parts"] is True and op["cl"]["save_drawings"] is True and op["cl"]["group_parts"] == 1
    assert op["result"] and op["result"]["maps"]                                # kroyga ta'sirsiz belgilar natijani o'chirmaydi
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cl": {"max_part_types_per_map": 1}})
    op = _op(client, pid, oid)
    assert not (op["result"] and op["result"]["maps"])                          # xillar cheklovi — natija eskiradi


def test_non_cut_set_matches_model():
    assert {"merge_parts", "group_parts", "save_drawings"} <= cl_calc.CL_NON_CUT
    assert "max_part_types_per_map" not in cl_calc.CL_NON_CUT and "waste_incl_trim" not in cl_calc.CL_NON_CUT
    assert cl_calc.CL_NON_CUT <= set(CLParams.model_fields)


_XML = """<?xml version="1.0" encoding="UTF-8"?>
<project name="cl parity" currency="UZS">
 <good typeId="product" id="1" name="Izd" count="1">
  <part id="10" code="a" name="Reyka" l="900" w="45" dl="900" dw="45" count="4"/>
 </good>
 <good typeId="band" id="20" name="Plintus 45" code="PL-45" l="3200" w="45" t="22" cost="1500">
  <part count="10000" id="50" l="3200" w="45" usedCount="0"/>
 </good>
 <good typeId="tool.cutting" id="30" swSawthick="4" swPackageHeight="60"/>
 <operation typeId="CL" id="7" tool1="30" cSizeMode="1" l="3200" w="45" t="22" cTrimW="10" cTrimWaste="true" %s
   printable="true" startNewPage="true"><material id="20"/><part id="10"/><part id="50"/></operation>
</project>
"""


def test_project_import_export_roundtrip_of_new_attributes(client):
    from app.plugins.legacy_project import import_project
    p, _w = import_project((_XML % "").encode("utf-8"), "a.project")
    c = next(o for o in p.operations if o.type == OpType.CL).cl
    assert (c.max_part_types_per_map, c.merge_parts, c.group_parts, c.save_drawings) == (0, False, 0, False)
    attrs = 'cMaxPartsOnPattern="3" cCombiningParts="true" cGroupParts="2" cSaveDrawCut="true"'
    r = client.post("/api/projects/import-file", files={"file": ("b.project", (_XML % attrs).encode("utf-8"), "application/xml")})
    assert r.status_code == 200, r.text
    proj = r.json()["project"]
    c = next(o for o in proj["operations"] if o["type"] == "CL")["cl"]
    assert (c["max_part_types_per_map"], c["merge_parts"], c["group_parts"], c["save_drawings"]) == (3, True, 2, True)
    exp = client.get(f"/api/projects/{proj['id']}/export/project")
    assert exp.status_code == 200, exp.text[:300]
    p2, _w = import_project(exp.content, "again.project")
    c2 = next(o for o in p2.operations if o.type == OpType.CL).cl
    assert (c2.max_part_types_per_map, c2.merge_parts, c2.group_parts, c2.save_drawings) == (3, True, 2, True)


# ───────────────────────── (SP) Режим размеров ─────────────────────────
def _api(client, method, url, **kw):
    r = getattr(client, method)(url, **kw)
    assert r.status_code == 200, (url, r.status_code, r.text[:300])
    return r.json()


def _find(p, oid):
    return next(o for o in p["operations"] if o["id"] == oid)


def test_sp_size_mode_default_is_saw_and_old_json_loads():
    assert SPParams().size_mode == -1
    raw = {"name": "e", "operations": [{"type": "SP", "sp": {"waste_percent": 5}}, {"type": "SP", "sp": {"size_mode": "bad"}}]}
    p = Project.model_validate(raw, context=LEGACY_CTX)
    assert [o.sp.size_mode for o in p.operations] == [-1, -1]


def test_sp_area_from_saw_size_vs_blank_size(client):
    """Pilniy o'lcham = zagotovka + pripusk (▽ ▷) + 2 × «Припуск на обработку заготовки»; zagotovka = detal − kromka qalinligi."""
    p = _api(client, "post", "/api/projects", json={"name": "SP parity"})
    pid = p["id"]
    p = _api(client, "post", f"/api/projects/{pid}/operations", json={"type": "CS", "name": "LDSP"})
    cs = p["operations"][-1]["id"]
    _api(client, "patch", f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": {"machining_allowance": 3}})
    p = _api(client, "post", f"/api/projects/{pid}/operations", json={"type": "EL", "name": "PVC"})
    el = p["operations"][-1]["id"]
    _api(client, "patch", f"/api/projects/{pid}/operations/{el}", json={"el": {"thickness": 2}})
    p = _api(client, "post", f"/api/projects/{pid}/operations/{cs}/parts",
             json=[dict(name="A", length=1000, width=500, qty=2, allow_top=10, edge_left={"op_id": el}, edge_right={"op_id": el})])
    part = _find(p, cs)["parts"][0]["id"]
    p = _api(client, "post", f"/api/projects/{pid}/operations", json={"type": "SP", "name": "Lak"})
    sp = p["operations"][-1]["id"]
    assert _find(p, sp)["sp"]["size_mode"] == -1                                  # standart — «Пильный размер»
    _api(client, "patch", f"/api/projects/{pid}/operations/{sp}", json={"sp": {"op_price": 100, "price": 10}})
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{cs}/parts/{part}", json=dict(surface_face_op=sp))
    u = client.get(f"/api/projects/{pid}/operations/{sp}/surface-usage").json()
    saw_l, saw_w = u["rows"][0]["calc_length"], u["rows"][0]["calc_width"]
    saw_area = _find(p, sp)["sp"]["area_m2"]
    p = _api(client, "patch", f"/api/projects/{pid}/operations/{sp}", json={"sp": {"size_mode": 0}})
    u = client.get(f"/api/projects/{pid}/operations/{sp}/surface-usage").json()
    bl, bw = u["rows"][0]["calc_length"], u["rows"][0]["calc_width"]
    blank_area = _find(p, sp)["sp"]["area_m2"]
    assert (bl, bw) == (996.0, 500.0)                                             # zagotovka: 1000 − 2·2 (ОЛ, ОП kromka)
    assert (saw_l, saw_w) == (bl + 2 * 3, bw + 10 + 2 * 3)                        # pilniy: + pripusk ▽ 10 + 2 × 3
    assert blank_area == pytest.approx(bl * bw / 1e6 * 2, abs=1e-4)
    assert saw_area == pytest.approx(saw_l * saw_w / 1e6 * 2, abs=1e-4)
    assert saw_area > blank_area
    op = _find(p, sp)
    assert op["cost_operation"] == pytest.approx(blank_area * 100, abs=0.01)      # narx ham tanlangan rejim maydonidan
    assert op["cost_material"] == pytest.approx(op["sp"]["material_m2"] * 10, abs=0.01)
