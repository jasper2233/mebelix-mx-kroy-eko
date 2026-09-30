"""GibLab dagi 'Detskiy kravat' loyihasi ma'lumotlari bilan sinov."""
from fastapi.testclient import TestClient

from app.main import app
from app.models import CSCutParams, CSMaterialParams, StockSheet
from app.services.optimizer import Item, optimize

PARTS = [  # (uid, L, W, qty)
    (1, 748, 1468, 1), (2, 200, 1468, 2), (3, 154, 748, 1), (4, 154, 1052, 1),
    (5, 50, 1052, 2), (6, 480, 800, 1), (7, 154, 400, 2), (8, 100, 1452, 1),
    (9, 470, 800, 1), (10, 900, 800, 1), (11, 500, 1452, 1), (12, 116, 552, 1),
    (13, 100, 350, 2), (14, 100, 503, 2),
]


def items():
    out = []
    for uid, L, W, q in PARTS:
        out += [Item(f"p{uid}", uid, L, W, True) for _ in range(q)]
    return out


def _overlap(a, b):
    return a.x < b.x + b.length and b.x < a.x + a.length and a.y < b.y + b.width and b.y < a.y + a.width


def test_optimizer_valid_layout():
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2)
    res = optimize(items(), [StockSheet(id="s", length=2750, width=1830)], cut, CSMaterialParams())
    assert not res.unplaced
    assert res.total_parts == 19
    print("\nsheets", res.total_sheets, "fill", [m.fill_percent for m in res.maps], res.total_fill_percent)
    for m in res.maps:
        pl = m.placements
        for i in range(len(pl)):
            p = pl[i]
            assert p.x >= 0 and p.y >= 0 and p.x + p.length <= 2750 + 1e-6 and p.y + p.width <= 1830 + 1e-6
            for j in range(i + 1, len(pl)):
                assert not _overlap(p, pl[j]), (p, pl[j])
    # 19 detal, maydon ~4.78 m² → 1 list (5.03 m²) ga sig'maydi, 2 list kutiladi
    assert res.total_sheets == 2


def test_grain_not_rotated():
    cut = CSCutParams()
    its = [Item("g", 1, 1000, 300, False) for _ in range(5)]
    res = optimize(its, [StockSheet(id="s", length=2750, width=1830)], cut, CSMaterialParams())
    for p in res.maps[0].placements:
        assert (p.length, p.width) == (1000, 300)


def test_api_flow():
    with TestClient(app) as c:
        p = c.post("/api/projects", json={"name": "Detskiy kravat"}).json()
        pid = p["id"]
        p = c.post(f"/api/projects/{pid}/operations", json={"type": "EL", "code": "KP-1/19-S",
                                                            "name": "kromka PVC 1-19 Sasna"}).json()
        el_id = p["operations"][0]["id"]
        p = c.post(f"/api/projects/{pid}/operations", json={"type": "CS", "name": "LDSP BELI KARONA"}).json()
        cs_id = p["operations"][1]["id"]
        parts = [dict(name=f"Panel{u}", length=L, width=W, qty=q) for u, L, W, q in PARTS]
        parts[1]["edge_right"] = {"op_id": el_id}                       # 200x1468 ×2, ОП
        parts[5].update(edge_top={"op_id": el_id}, edge_bottom={"op_id": el_id},
                        edge_right={"op_id": el_id})                      # 480x800 ОВ ОН ОП
        c.post(f"/api/projects/{pid}/operations/{cs_id}/parts", json=parts)
        res = c.post(f"/api/projects/{pid}/operations/{cs_id}/optimize").json()
        assert res["total_parts"] == 19
        eu = c.get(f"/api/projects/{pid}/operations/{el_id}/edge-usage").json()
        # 2×(1468+40) + 2×(480+40) + (800+40) = 3016 + 1040 + 840 = 4.896 m
        assert abs(eu["material_m"] - 4.896) < 1e-6
        assert abs(eu["work_m"] - (2 * 1468 + 2 * 480 + 800) / 1000) < 1e-6
        svg = c.get(f"/api/projects/{pid}/operations/{cs_id}/maps/1.svg")
        assert svg.status_code == 200 and svg.text.startswith("<svg")
        html = c.get(f"/api/projects/{pid}/report").text
        assert "Omborga talabnoma" in html
        assert c.post(f"/api/projects/{pid}/undo").status_code == 200
