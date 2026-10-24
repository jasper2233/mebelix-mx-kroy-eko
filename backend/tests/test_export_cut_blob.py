"""`.project` eksportidagi CS kroy kartalari (`data` bloki) — korxona MES tizimi shu blokdan kartalarni o'qiydi va bloksiz faylni
rad etadi (foydalanuvchi qarori, 2026-10-19). Blok mustaqil dekoder bilan ochiladi va statistika, detal / qoldiq havolalari,
kataklar soni hamda geometriya tekshiriladi."""
import base64
import struct
import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient

from app.main import app

REC = struct.Struct(">BdBBi")


def decode(b64: str) -> list[dict]:
    raw = base64.b64decode(b64)
    assert struct.unpack_from(">IIB", raw, 0) == (0, 1, 3)
    n, off, pats = struct.unpack_from(">I", raw, 9)[0], 13, []
    for _ in range(n):
        d = off + 4
        assert struct.unpack_from(">dddd", raw, d + 21) == (-1.0, -1.0, -1.0, -1.0)
        nr = struct.unpack_from(">I", raw, d + 113)[0]
        recs = [REC.unpack_from(raw, d + 117 + 15 * j) for j in range(nr)]
        pats.append(dict(mult=struct.unpack_from(">I", raw, off)[0], L=struct.unpack_from(">d", raw, d)[0],
                         W=struct.unpack_from(">d", raw, d + 8)[0], stock=struct.unpack_from(">I", raw, d + 16)[0],
                         parts=struct.unpack_from(">I", raw, d + 53)[0], part_area=struct.unpack_from(">d", raw, d + 69)[0],
                         cut_len=struct.unpack_from(">d", raw, d + 93)[0], cut_n=struct.unpack_from(">I", raw, d + 101)[0],
                         recs=[(t >> 3, t & 7, v, q, pid) for t, v, _f, q, pid in recs]))
        off = d + 132 + 15 * (nr - 1)
    assert off == len(raw)
    return pats


def place(recs: list, L: float, W: float) -> list[tuple]:
    """Preorder daraxt → kataklar (x, y, w, h, tur, id): vertikal ildizda slot — birinchi yozuv, gorizontalda — bo'sh slot."""
    slot, rest = recs[0], recs[1:]
    vertical = not (slot[0] == 0 and slot[1] == 1 and slot[2] == 0)
    flat = ([slot] if vertical else []) + rest
    cells: list[tuple] = []
    pos = [0]

    def level(x, y, w, h, vert, depth):
        cur = 0.0
        while pos[0] < len(flat) and flat[pos[0]][0] == depth:
            _d, t, v, q, pid = flat[pos[0]]
            pos[0] += 1
            start = pos[0]
            for _ in range(max(q, 1)):
                rx, ry = (x + cur, y) if vert else (x, y + cur)
                rw, rh = (v, h) if vert else (w, v)
                if t in (3, 4):
                    cells.append((rx, ry, rw, rh, t, pid))
                elif t == 2:
                    pos[0] = start
                    level(rx, ry, rw, rh, not vert, depth + 1)
                cur += v
        return cur

    level(0.0, 0.0, L, W, vertical, 1)
    return cells


@pytest.fixture()
def exported(tmp_path, monkeypatch):
    monkeypatch.setenv("MEBELIX_DB_URL", f"sqlite:///{(tmp_path / 'b.db').as_posix()}")
    with TestClient(app) as c:
        pid = c.post("/api/projects", json={"name": "BLOB"}).json()["id"]
        p = c.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "L16", "name": "LDSP"}).json()
        cs = p["operations"][0]["id"]
        ops = c.post(f"/api/projects/{pid}/operations", json={"type": "EL", "code": "K1", "name": "kromka 19"}).json()["operations"]
        el = next(o for o in ops if o["type"] == "EL")["id"]
        parts = [{"name": f"d{i}", "length": l, "width": w, "qty": q, "edge_top": {"op_id": el}}
                 for i, (l, w, q) in enumerate([(700, 500, 6), (2100, 560, 4), (400, 300, 9), (1200, 800, 3), (300, 100, 12)])]
        c.post(f"/api/projects/{pid}/operations/{cs}/parts", json=parts)
        assert c.post(f"/api/projects/{pid}/operations/{cs}/optimize", json={"quality": "fast"}).status_code == 200
        r = c.get(f"/api/projects/{pid}/export/project")
        assert r.status_code == 200
        yield ET.fromstring(r.content), c.get(f"/api/projects/{pid}").json()


def test_cs_data_blob_matches_stats_and_parts(exported):
    root, proj = exported
    assert root.get("version") == "21052101"
    cs = next(o for o in root.findall("operation") if o.get("typeId") == "CS")
    pats = decode(cs.get("data"))
    res = next(o for o in proj["operations"] if o["type"] == "CS")["result"]
    assert sum(p["mult"] for p in pats) == int(cs.get("cMaterialCount")) == res["total_sheets"]
    assert sum(p["parts"] for p in pats) == int(cs.get("cPartCount")) == 34
    assert abs(sum(p["cut_len"] for p in pats) - float(cs.get("cTrimLength"))) < 0.01
    assert sum(p["cut_n"] for p in pats) == int(cs.get("cTrimCount"))
    assert cs.find("material").get("count") == cs.get("cMaterialCount")
    # detal / list havolalari
    prod_parts = {p.get("id"): p for g in root.findall("good") if g.get("typeId") == "product" for p in g.findall("part")}
    sheet = next(g for g in root.findall("good") if g.get("typeId") == "sheet")
    stock_ids = {p.get("id") for p in sheet.findall("part") if not p.get("waste")}
    waste_ids = {p.get("id") for p in sheet.findall("part") if p.get("waste") == "true"}
    stubs = {p.get("id") for p in cs.findall("part")}
    assert waste_ids <= stubs and stock_ids <= stubs
    per_part: dict[str, int] = {}
    for p in pats:
        assert str(p["stock"]) in stock_ids
        cells = place(p["recs"], p["L"], p["W"])
        assert sum(1 for c in cells if c[4] == 3) * p["mult"] == p["parts"]
        for x, y, w, h, t, pid in cells:
            assert x + w <= p["L"] + 0.5 and y + h <= p["W"] + 0.5
            if t == 4:
                assert str(pid) in waste_ids
                continue
            pt = prod_parts[str(pid)]
            dims = sorted((float(pt.get("cl")), float(pt.get("cw"))))
            assert sorted((w, h)) == pytest.approx(dims, abs=1.5)
            per_part[str(pid)] = per_part.get(str(pid), 0) + p["mult"]
    for pid, n in per_part.items():                             # har detal nusxalari soni = detal soni (MES tekshiruvi)
        assert n == int(prod_parts[pid].get("count")) == int(prod_parts[pid].get("usedCount"))
    assert all(p.get("eltMat") == "kromka 19" for p in prod_parts.values())
