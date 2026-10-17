"""2026-10-17 — ko'p loyihali solishtiruv (15 ta korxona loyihasi, avvalgi tizim saqlagan natija bilan) tuzatishlari.
Faqat sintetik ma'lumot (korxona fayllari / mijoz nomlari yo'q).

1. Stoleshnitsa (tor list 4200×610, 600 mm detal): 1-darajadagi «polosa = bitta detal» ham C1 → T2 → P2 bo'lib kesiladi —
   detalning uzun tomonlari (torsovka va qarama-qarshi chet) kesimi bor. Avval faqat 2 ko'ndalang kesim chiqardi (LT 1.22 m),
   avvalgi tizim: 3490 + 2020 mm detallar ikki listda — 8 kesim, 13.46 m (bizda endi aynan shunday).
2. «Листдан katta» ogohlantirishi dona bo'yicha sanaladi; tekstura sababli sig'maydigan (burilsa sig'adigan) detallar alohida
   ogohlantiriladi.
3. «Раскроить все» qalinligi 0 bo'lgan CS operatsiyani («zamena material», alyumin profil) o'tkazib yuboradi.
"""
from collections import deque

import pytest

from app.models import CSCutParams, CSMaterialParams, StockSheet
from app.services.optimizer import Item, optimize
from app.services.validate import validate

CUT = CSCutParams(kerf=3, trim_length=2, trim_width=2, max_rotations=4)
MAT = CSMaterialParams()


def _cmds(m):
    return [(c.code, c.level, c.size, c.count) for c in m.commands]


def test_countertop_full_width_part_gets_long_edge_cuts():
    st = StockSheet(id="s", length=4200, width=610)
    items = [Item("a", 1, 3490, 600, False), Item("b", 2, 2020, 600, False)]
    r = optimize(items, [st], CUT, MAT, time_limit=2)
    assert validate(r, items, [st], CUT) == []
    assert r.total_sheets == 2 and not r.unplaced
    by_len = {m.placements[0].length: m for m in r.maps}
    assert _cmds(by_len[3490]) == [("T", 1, 2.0, 1), ("C", 1, 3490.0, 1), ("T", 2, 2.0, 1), ("P", 2, 600.0, 1)]
    assert by_len[3490].cut_length_m == pytest.approx(8.2) and by_len[3490].cuts_count == 4
    assert by_len[2020].cut_length_m == pytest.approx(5.26)          # oxirgi деловой qoldiq (2167×600) kesimsiz
    assert r.total_cut_length_m == pytest.approx(13.46) and r.total_cuts == 8
    assert r.remnant_area_m2 == pytest.approx(1.3002)
    # daraxt (chizma / muharrir) ham shunday: 1-daraja C polosasi ichida 2-daraja detal
    strip = by_len[3490].strips[0]["c"][0]
    assert strip["k"] == "C" and strip["c"][0]["k"] == "P"


def test_full_width_part_on_raw_edge_sheet_is_not_wrapped():
    """Torsovka 0 va «отступ в конце» 0: detal list enini to'liq egallaydi — uzun tomonida kesim yo'q (o'zgarmaydi)."""
    cut = CSCutParams(kerf=3, trim_length=0, trim_width=0, end_offset_bottom=0, end_offset_right=0, max_rotations=4)
    st = StockSheet(id="s", length=3050, width=600)
    items = [Item("a", 1, 2500, 600, False)]
    r = optimize(items, [st], cut, MAT, time_limit=1)
    assert validate(r, items, [st], cut) == []
    assert [c for c in _cmds(r.maps[0]) if c[1] == 2] == []
    assert r.total_cut_length_m == pytest.approx(0.6)


def test_full_width_part_single_rotation_limit_keeps_level_one():
    cut = CUT.model_copy(update={"max_rotations": 1})
    st = StockSheet(id="s", length=3050, width=610)
    items = [Item("a", 1, 2500, 600, False)]
    r = optimize(items, [st], cut, MAT, time_limit=1)
    assert validate(r, items, [st], cut) == []


def _mk(client, name):
    return client.post("/api/projects", json={"name": name}).json()["id"]


def _cs(client, pid, name, parts, thickness=None, sheet=None):
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": name, "name": name}).json()
    oid = p["operations"][-1]["id"]
    if thickness is not None:
        client.patch(f"/api/projects/{pid}/operations/{oid}", json={"cs_material": {"thickness": thickness}})
    if sheet is not None:
        client.put(f"/api/projects/{pid}/operations/{oid}/sheets", json=[sheet])
    client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=parts)
    return oid


def test_oversize_warning_counts_pieces_and_names_grain(client):
    pid = _mk(client, "Ogohlantirish")
    oid = _cs(client, pid, "LDSP", [
        {"name": "ok", "length": 600, "width": 400, "qty": 1},
        {"name": "katta", "length": 3000, "width": 500, "qty": 2},            # har tomondan katta — 2 dona
        {"name": "sokl", "length": 70, "width": 2500, "qty": 3, "grain": True},   # burilsa sig'adi, tekstura taqiqlaydi
    ], sheet={"length": 2750, "width": 1830, "qty": 10000})
    r = client.post(f"/api/projects/{pid}/operations/{oid}/optimize?quality=fast")
    assert r.status_code == 200, r.text
    res = r.json()
    assert len(res["unplaced"]) == 5
    w = " | ".join(res["warnings"])
    assert "2 дет. больше любого листа" in w
    assert "3 дет. не помещаются на лист по направлению текстуры" in w


def test_optimize_all_skips_zero_thickness_ops(client):
    pid = _mk(client, "Zamena")
    a = _cs(client, pid, "LDSP", [{"name": "p", "length": 600, "width": 400, "qty": 2}], thickness=16)
    z = _cs(client, pid, "zamena material", [{"name": "p", "length": 600, "width": 400, "qty": 2}], thickness=0)
    d = client.post(f"/api/projects/{pid}/actions/optimize-all?quality=fast").json()
    res = {x["op_id"]: x for x in d["results"]}
    assert res[a]["sheets"] == 1
    assert res[z]["skipped"] is True and "0" in res[z]["reason"]
    # alohida «Раскроить» — baribir mumkin (foydalanuvchi o'zi tanlasa)
    r = client.post(f"/api/projects/{pid}/operations/{z}/optimize?quality=fast")
    assert r.status_code == 200 and r.json()["total_sheets"] == 1


def test_rebalance_tail_keeps_parts_and_never_loses_business():
    """Oxirgi ikki listni qayta taqsimlash: listlar soni, detallar to'plami saqlanadi, деловой qoldiq kamaymaydi."""
    import random
    import time as _t
    from app.services import optimizer as O
    rnd = random.Random(7)
    items = []
    for i in range(40):
        l, w = rnd.choice([(720, 560), (564, 300), (900, 450), (1200, 400), (380, 280), (1650, 600)])
        items.append(Item(f"p{i}", i + 1, l, w, True))
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, max_rotations=4)
    st = StockSheet(id="s", length=2750, width=1830)
    pool = O._Pool(items)
    pool.gk = O.group_kerf(cut)
    sheets, counts = O._run_job(pool, [st], cut, O._axes_for(cut), _t.monotonic() + 2.0)
    assert sum(counts) == 0 and len(sheets) >= 2

    def biz(shs):
        return sum(O._leaf_remnant(lf, s.zone, MAT)[2] for s in shs for lf in s.root.leaves()
                   if lf.kind == "W" and lf.l > O.EPS and lf.w > O.EPS and O._leaf_remnant(lf, s.zone, MAT)[1])

    def shapes(shs):
        tot = [0] * len(pool.shapes)
        for s in shs:
            for i, c in enumerate(O._shape_counts(pool, s.root)):
                tot[i] += c
        return tot
    new = O._rebalance_tail(pool, sheets, cut, O._axes_for(cut), MAT, _t.monotonic() + 2.0)
    assert len(new) == len(sheets)
    assert shapes(new) == shapes(sheets)
    assert biz(new) >= biz(sheets) - 1.0
    assert all(O._depth_ok(s.root, pool, cut.max_rotations) for s in new)
    res = O._finish(O._build_result(new, {s.idx: deque(s.pids) for s in pool.shapes}, cut, MAT, pool), MAT)
    assert validate(res, items, [st], cut) == []
