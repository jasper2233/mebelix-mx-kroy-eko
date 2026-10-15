"""W3-B: «Товары» — kategoriyalar daraxti, katalog importi (id/parent_id/isfolder/…/rasm/parametrlar), ildiz
kategoriyalar, `/catalog` daraxt API, rasm xavfsizligi, MES sync buzilmasligi."""
import base64
import importlib.util
import io
import json
import struct
import zlib
from pathlib import Path

import pytest
from openpyxl import Workbook

FIX = Path(__file__).parent / "fixtures"
UZ = {"Accept-Language": "uz"}
HEAD = ["id", "parent_id", "isfolder", "code", "name", "unit", "price", "stock", "image", "params", "thickness", "length", "width"]
CMAP = {"id": "A", "parent_id": "B", "isfolder": "C", "code": "D", "name": "E", "unit": "F", "price": "G", "stock": "H",
        "image": "I", "params": "J", "thickness": "K", "length": "L", "width": "M"}


def _png(w=1, h=1):
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\xff\x00\x00" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def _uri(data=None, mime="image/png"):
    return f"data:{mime};base64," + base64.b64encode(data if data is not None else _png()).decode()


def _xlsx(rows):
    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _import(client, rows, cmap=None, name="g.xlsx", **form):
    data = {"col_map": json.dumps(cmap or CMAP), "start_row": 2, **{k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in form.items()}}
    return client.post("/api/catalog/import", files={"file": (name, rows if isinstance(rows, bytes) else _xlsx(rows))}, data=data)


def _all(client):
    """Butun katalog (sessiya bazasi umumiy — testlar o'z ID prefikslari bo'yicha ajratadi): {id: qator}."""
    return {x["id"]: x for x in client.get("/api/catalog", params={"limit": 5000}).json()}


def _find(nodes, nid):
    for n in nodes:
        if n["id"] == nid:
            return n
        r = _find(n.get("children", []), nid)
        if r:
            return r
    return None


def _goods(prefix):
    """goods.xls tuzilmasi: ildiz «Листовой» (0) → ishlab chiqaruvchi → qalinlik → o'lcham → materiallar; kromka ildizi (10)."""
    return [HEAD,
            [0, None, 1, "", "Листовой материал", "", None, None, None, None, None, None, None],
            [1, 0, 1, "", "Производитель А", "", None, None, None, None, None, None, None],
            [2, 1, 1, "", "ЛДСП - 100 мм", "", None, None, None, None, None, None, None],
            [3, 1, 1, "", "ЛДСП - 16 мм", "", None, None, None, None, None, None, None],
            [4, 3, 1, "", "2800x2070", "", None, None, None, None, None, None, None],
            [1001, 4, 0, f"{prefix}A.101", "ЛДСП Ваниль 16мм", "м2", 120000, 15, _uri(), "kerf=4; grain=true; trim_length=10", 16, 2800, 2070],
            [1002, 4, 0, f"{prefix}A.102", "ЛДСП Белый 16мм", "м2", 118000, 0, None, None, 16, 2800, 2070],
            [10, None, 1, "", "Кромка", "", None, None, None, None, None, None, None],
            [2001, 10, 0, f"{prefix}E.1", "ПВХ 2 мм", "м", 1500, 0, None, None, 2, None, 22]]


# ───────────────────────── import va daraxt ─────────────────────────
def test_goods_tree_import_roots_kinds_and_tree_api(client):
    r = _import(client, _goods("w3a"), roots={"sheet": "0", "edge": "10"}, id_prefix="w3a-")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["count"] == 9 and d["folders"] == 6 and d["items"] == 3 and d["images"] == 1 and d["warnings"] == []
    # tur — ildiz kategoriyadan: 0 ostida — list, 10 ostida — kromka
    it = _all(client)
    assert it["w3a-1001"]["kind"] == "sheet" and it["w3a-2001"]["kind"] == "edge" and it["w3a-3"]["kind"] == "folder"
    assert it["w3a-1001"]["parent_id"] == "w3a-4" and it["w3a-0"]["parent_id"] is None
    assert it["w3a-1001"]["params"] == {"kerf": 4, "grain": True, "trim_length": 10}
    assert it["w3a-1001"]["has_image"] is True and it["w3a-1002"]["has_image"] is False and "image" not in it["w3a-1001"]
    # daraxt: papkalar, hisob, tabiiy tartib («16 мм» < «100 мм»)
    t = client.get("/api/catalog/tree").json()
    root = _find(t["nodes"], "w3a-0")
    assert root["count"] == 2 and [c["id"] for c in root["children"]] == ["w3a-1"]
    assert [c["name"] for c in _find(t["nodes"], "w3a-1")["children"]] == ["ЛДСП - 16 мм", "ЛДСП - 100 мм"]
    assert _find(t["nodes"], "w3a-2")["count"] == 0 and _find(t["nodes"], "w3a-4")["count"] == 2
    assert _find(t["nodes"], "w3a-10")["count"] == 1 and all(n["kind"] == "folder" for n in root["children"])
    # operatsiya turiga qarab filtr: kromka — faqat «Кромка» shoxi; bo'sh papkalar tushadi
    te = client.get("/api/catalog/tree", params={"kind": "edge"}).json()
    assert _find(te["nodes"], "w3a-10") and _find(te["nodes"], "w3a-0") is None
    ts = client.get("/api/catalog/tree", params={"kind": "sheet"}).json()
    assert _find(ts["nodes"], "w3a-2") is None and _find(ts["nodes"], "w3a-3")["count"] == 2
    # qidiruv daraxtni toraytiradi
    tq = client.get("/api/catalog/tree", params={"q": "ваниль"}).json()
    assert _find(tq["nodes"], "w3a-4")["count"] == 1 and _find(tq["nodes"], "w3a-10") is None
    # materiallar jadvali: papka ostidagi to'g'ridan-to'g'ri / ichki papkalar bilan
    own = client.get("/api/catalog", params={"parent_id": "w3a-4", "folders": "false"}).json()
    assert [x["id"] for x in own] == ["w3a-1002", "w3a-1001"] or {x["id"] for x in own} == {"w3a-1001", "w3a-1002"}
    rec = client.get("/api/catalog", params={"parent_id": "w3a-0", "recursive": "true", "folders": "false"}).json()
    assert {x["id"] for x in rec} == {"w3a-1001", "w3a-1002"}
    assert client.get("/api/catalog", params={"parent_id": "w3a-0", "recursive": "true", "kind": "edge"}).json() == []
    # daraxt + materiallar barg sifatida (`/catalog?tree=true`)
    full = client.get("/api/catalog", params={"tree": "true", "limit": 5000}).json()
    leaf = _find(full, "w3a-1001")
    assert leaf and leaf["kind"] == "sheet" and leaf["children"] == [] and _find(full, "w3a-4")["children"]
    # eski usul: ildiz (ota yo'q) — `parent_id=""`
    roots = {x["id"] for x in client.get("/api/catalog", params={"parent_id": "", "limit": 5000}).json()}
    assert {"w3a-0", "w3a-10"} <= roots and "w3a-1" not in roots


def test_isfolder_inferred_when_column_missing_and_default_kind_without_roots(client):
    rows = [["id", "parent", "name"], ["w3b-a", None, "Категория"], ["w3b-b", "w3b-a", "Материал 1"], ["w3b-c", "w3b-a", "Материал 2"]]
    r = _import(client, rows, {"id": "A", "parent_id": "B", "name": "C"}, kind="linear")
    assert r.status_code == 200 and r.json()["folders"] == 1 and r.json()["items"] == 2
    it = _all(client)
    assert it["w3b-b"]["kind"] == "linear" and it["w3b-c"]["kind"] == "linear" and it["w3b-a"]["kind"] == "folder"
    # `kind` ustuni ildiz va standart turdan ustun
    rows = [["id", "name", "kind"], ["w3b-d", "Kromka X", "edge"], ["w3b-e", "Noma'lum tur", "zzz"]]
    _import(client, rows, {"id": "A", "name": "B", "kind": "C"}, kind="surface")
    it = _all(client)
    assert it["w3b-d"]["kind"] == "edge" and it["w3b-e"]["kind"] == "surface"


def test_import_validation_prefix_cycles_duplicates_and_reimport_keeps_images(client):
    assert _import(client, [HEAD], {"id": "A"}).status_code == 400                       # nom ustuni yo'q
    assert _import(client, [HEAD], {"name": "E", "zzz": "A"}).status_code == 400          # noma'lum maydon
    assert _import(client, [HEAD], {"name": "11"}).status_code == 400                     # ustun harfi emas
    assert _import(client, [HEAD], {"name": "E"}, roots="[1]").status_code == 400
    rows = [["id", "parent_id", "name"], ["c1", "c2", "A"], ["c2", "c1", "B"], ["c3", "c3", "C"], ["c4", None, "D"], ["c4", None, "D2"]]
    r = _import(client, rows, {"id": "A", "parent_id": "B", "name": "C"}, id_prefix="w3c-")
    d = r.json()
    assert d["count"] == 4 and len(d["warnings"]) == 2                                    # sikllar uzildi + takroriy ID
    tr = client.get("/api/catalog/tree").json()                                           # sikl daraxtni buzmaydi
    ids = {i for i in _all(client) if i.startswith("w3c-")}
    assert ids == {"w3c-c1", "w3c-c2", "w3c-c3", "w3c-c4"} and tr["nodes"]
    assert _all(client)["w3c-c4"]["name"] == "D2"                                          # takroriy ID — oxirgi qator
    # rasm ustuni ko'rsatilmasa — qayta importda rasm va parametrlar saqlanadi
    _import(client, _goods("w3d"), id_prefix="w3d-")
    first = client.get("/api/catalog/w3d-1001").json()
    assert first["image"].startswith("data:image/png;base64,") and first["params"]["kerf"] == 4
    _import(client, _goods("w3d"), {k: v for k, v in CMAP.items() if k not in ("image", "params")}, id_prefix="w3d-")
    again = client.get("/api/catalog/w3d-1001").json()
    assert again["image"] == first["image"] and again["params"] == first["params"] and again["has_image"] is True


def test_empty_name_rows_reported_and_deep_chain_does_not_break_tree(client):
    rows = [["id", "parent_id", "name"], ["w3e-0", None, "Ildiz"]]
    rows += [[f"w3e-{i}", f"w3e-{i - 1}", f"Papka {i}"] for i in range(1, 1500)]        # 1500 darajali zanjir
    rows += [["w3e-m", "w3e-1499", "Material"], ["w3e-x", None, None]]
    d = _import(client, rows, {"id": "A", "parent_id": "B", "name": "C"}).json()
    assert d["count"] == 1501 and d["skipped"] == [{"row": 1503, "reason": "Наименование: пусто"}]
    t = client.get("/api/catalog/tree")                                                  # rekursiyasiz, JSON chuqurligi cheklangan
    assert t.status_code == 200
    nodes, depth, total = t.json()["nodes"], 0, 0
    stack = [(n, 1) for n in nodes]
    while stack:
        n, dp = stack.pop()
        depth, total = max(depth, dp), total + (1 if n["id"].startswith("w3e-") else 0)
        stack += [(c, dp + 1) for c in n["children"]]
    assert depth <= 70 and total == 1500                                                 # barcha papkalar ko'rinadi, chuqurlik ≤ 64 + 1
    assert client.get("/api/catalog/tree", params={"root": "w3e-0"}).status_code == 200


# ───────────────────────── rasm xavfsizligi ─────────────────────────
def _put_image(client, iid, **kw):
    return client.put(f"/api/catalog/{iid}/image", **kw)


def test_image_upload_validation_and_removal(client):
    client.post("/api/catalog/sync", json=[{"id": "w3i-1", "kind": "sheet", "name": "Rasmli material"}])
    ok = _put_image(client, "w3i-1", files={"file": ("a.png", _png(3, 2))})
    assert ok.status_code == 200
    it = client.get("/api/catalog/w3i-1").json()
    assert it["has_image"] and it["image"] == _uri(_png(3, 2))
    # mijoz aytgan tur emas, mazmun hal qiladi: SVG / HTML — png deb yuborilsa ham rad etiladi
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"><script>alert(1)</script></svg>'
    for name, data in (("a.png", svg), ("a.png", b"<html><script>alert(1)</script></html>"), ("x.gif", b"GIF8"), ("a.png", b"")):
        r = _put_image(client, "w3i-1", files={"file": (name, data)})
        assert r.status_code == 400, (name, data[:10])
    assert _put_image(client, "w3i-1", files={"file": ("big.png", _png(1, 1) + b"\0" * (300 * 1024))}).status_code == 400   # hajm
    # juda katta o'lcham (sarlavhada 20000×20000, kichik fayl)
    assert _put_image(client, "w3i-1", files={"file": ("huge.png", _png(20000, 1)[:33] + b"\0" * 20)}).status_code == 400
    # havola: faqat http(s); credentials, bo'shliq, javascript:, file:, data:svg — rad
    assert _put_image(client, "w3i-1", data={"url": "https://cdn.example.com/a.png"}).status_code == 200
    assert client.get("/api/catalog/w3i-1").json()["image"] == "https://cdn.example.com/a.png"
    for bad in ("javascript:alert(1)", "file:///C:/Windows/win.ini", "C:\\img\\a.png", "/etc/passwd", "ftp://x/a.png",
                "https://user:pw@host/a.png", "https://host/a b.png", "https://host/\"><script>", "http://",
                "data:image/svg+xml;base64," + base64.b64encode(svg).decode(), "data:image/png,rawtext",
                "data:image/png;base64,@@@@", "https://h/" + "a" * 600):
        assert _put_image(client, "w3i-1", data={"url": bad}).status_code == 400, bad
    assert client.get("/api/catalog/w3i-1").json()["image"] == "https://cdn.example.com/a.png"   # rad etilganlar o'zgartirmadi
    assert _put_image(client, "w3i-1").status_code == 400
    assert _put_image(client, "yoq", files={"file": ("a.png", _png())}).status_code == 404
    # data: URI — qayta kodlanadi (sehrli baytlar bo'yicha tur), mijoz MIME ga ishonilmaydi
    assert _put_image(client, "w3i-1", data={"url": _uri(_png(), "image/jpeg")}).status_code == 200
    assert client.get("/api/catalog/w3i-1").json()["image"] == _uri(_png(), "image/png")
    # o'chirish
    assert client.delete("/api/catalog/w3i-1/image").status_code == 200
    it = client.get("/api/catalog/w3i-1").json()
    assert it["image"] is None and it["has_image"] is False
    assert client.delete("/api/catalog/yoq/image").status_code == 404
    assert client.get("/api/catalog/yoq").status_code == 404
    r = _put_image(client, "w3i-1", data={"url": "javascript:1"}, headers=UZ)
    assert "PNG" in r.json()["detail"]


def test_import_image_column_accepts_only_safe_values_and_skips_paths(client):
    rows = [HEAD[:5] + ["image"],
            ["w3f-1", None, 0, "", "Data URI", _uri()], ["w3f-2", None, 0, "", "URL", "http://img.example.org/x.jpg"],
            ["w3f-3", None, 0, "", "Yo'l", "C:\\images\\1.jpg"], ["w3f-4", None, 0, "", "SVG", "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="],
            ["w3f-5", None, 0, "", "Server fayli", "/etc/passwd"]]
    r = _import(client, rows, {"id": "A", "name": "E", "image": "F"})
    d = r.json()
    assert r.status_code == 200 and d["images"] == 2 and len(d["warnings"]) == 1 and "3" in d["warnings"][0]
    got = {i: client.get(f"/api/catalog/{i}").json() for i in ("w3f-1", "w3f-2", "w3f-3", "w3f-4", "w3f-5")}
    assert got["w3f-1"]["image"] == _uri() and got["w3f-2"]["image"] == "http://img.example.org/x.jpg"
    assert all(got[i]["image"] is None for i in ("w3f-3", "w3f-4", "w3f-5"))


def test_mes_sync_keeps_images_params_and_reports_bad_images(client):
    client.post("/api/catalog/sync", json=[{"id": "w3s-1", "kind": "sheet", "code": "S1", "name": "Sync", "price": 5, "image": _uri(),
                                            "params": {"grain": True}}])
    assert client.get("/api/catalog/w3s-1").json()["image"] == _uri()
    # MES rasmsiz qayta yuboradi — rasm saqlanadi (narx yangilanadi, `params` MES nima yuborsa shu)
    r = client.post("/api/catalog/sync", json=[{"id": "w3s-1", "kind": "sheet", "code": "S1", "name": "Sync", "price": 9}]).json()
    assert r == {"count": 1, "image_errors": 0}
    it = client.get("/api/catalog/w3s-1").json()
    assert it["price"] == 9 and it["image"] == _uri() and it["has_image"]
    # yaroqsiz rasm sinxronni to'xtatmaydi
    r = client.post("/api/catalog/sync", json=[{"id": "w3s-2", "kind": "sheet", "name": "Yaxshi"},
                                               {"id": "w3s-3", "kind": "sheet", "name": "Yomon rasm", "image": "javascript:1"}]).json()
    assert r["count"] == 2 and r["image_errors"] == 1
    assert client.get("/api/catalog/w3s-3").json()["image"] is None


def test_catalog_params_drive_new_cs_and_folder_delete_is_recursive(client):
    _import(client, _goods("w3g"), roots={"sheet": "0"}, id_prefix="w3g-")
    p = client.post("/api/projects", json={"name": "Katalog CS"}).json()
    o = client.post(f"/api/projects/{p['id']}/operations", json={"type": "CS", "material_id": "w3g-1001"}).json()["operations"][-1]
    assert o["cs_cut"]["kerf"] == 4 and o["cs_cut"]["use_grain"] is True and o["cs_cut"]["trim_length"] == 10
    assert o["cs_material"]["thickness"] == 16 and o["sheets"][0]["length"] == 2800
    # oddiy o'chirish — faqat shu qator; papkani rekursiv o'chirish — ichidagilar va rasmlari bilan
    assert client.delete("/api/catalog/w3g-1002").json() == {"ok": True, "deleted": 1}
    r = client.delete("/api/catalog/w3g-1", params={"recursive": "true"}).json()
    assert r["ok"] and r["deleted"] == 5                                               # papkalar w3g-1, 2, 3, 4 va w3g-1001
    left = {i for i in _all(client) if i.startswith("w3g-")}
    assert left == {"w3g-0", "w3g-10", "w3g-2001"}
    assert client.get("/api/catalog/w3g-1001").status_code == 404
    from app.db import CatalogImageRow, SessionLocal
    with SessionLocal() as s:
        assert s.get(CatalogImageRow, "w3g-1001") is None                               # rasm ham o'chdi
    assert client.delete("/api/catalog/w3g-1").status_code == 404


def test_flat_mes_catalog_compat_and_unfiled(client):
    """Papkasiz (tekis) MES katalogi: avvalgi `/catalog` xulqi o'zgarmaydi; `unfiled` papkasiz materiallar."""
    client.post("/api/catalog/sync", json=[{"id": "w3h-1", "kind": "edge", "code": "W3H-1", "name": "Tekis kromka"},
                                           {"id": "w3h-2", "kind": "folder", "name": "W3H papka"},
                                           {"id": "w3h-3", "parent_id": "w3h-2", "kind": "edge", "name": "W3H ichida"}])
    assert [x["id"] for x in client.get("/api/catalog", params={"kind": "edge", "q": "W3H-1"}).json()] == ["w3h-1"]
    un = {x["id"] for x in client.get("/api/catalog", params={"unfiled": "true", "q": "W3H"}).json()}
    assert un == {"w3h-1"}
    assert [x["id"] for x in client.get("/api/catalog", params={"parent_id": "w3h-2"}).json()] == ["w3h-3"]
    t = client.get("/api/catalog/tree", params={"kind": "edge"}).json()
    assert t["unfiled"] >= 1 and _find(t["nodes"], "w3h-2")["count"] == 1


# ───────────────────────── .xls (xlrd) ─────────────────────────
@pytest.mark.skipif(importlib.util.find_spec("xlrd") is None, reason=".xls o'qish uchun xlrd kerak (pip install xlrd)")
def test_goods_xls_import_with_tree_and_roots(client):
    data = (FIX / "w3_goods.xls").read_bytes()
    pv = client.post("/api/import/preview", files={"file": ("goods.xls", data)}).json()
    assert pv["format"] == "xls" and pv["sheets"] == ["Лист1"] and pv["rows"][0][:3] == ["id", "parent_id", "isfolder"]
    assert pv["rows"][5][0] == "1001"
    cmap = {"id": "A", "parent_id": "B", "isfolder": "C", "code": "D", "name": "E", "unit": "F", "price": "G",
            "thickness": "H", "length": "I", "width": "J"}
    r = _import(client, data, cmap, name="goods.xls", roots={"sheet": "0", "edge": "10"}, id_prefix="w3x-")
    d = r.json()
    assert r.status_code == 200 and d["count"] == 8 and d["folders"] == 5 and d["items"] == 3
    a = client.get("/api/catalog/w3x-1001").json()
    assert (a["kind"], a["parent_id"], a["price"], a["thickness"], a["length"], a["width"], a["unit"]) == \
        ("sheet", "w3x-3", 120000, 10, 2800, 2070, "м2")
    assert client.get("/api/catalog/w3x-2001").json()["kind"] == "edge"
    assert _find(client.get("/api/catalog/tree").json()["nodes"], "w3x-3")["count"] == 2


def test_image_header_parsers_and_dimension_limits():
    """GIF / JPEG / WebP sarlavhasidan o'lcham o'qiladi; ruxsat etilgan chegaradan kattasi va buzuqlari rad etiladi."""
    from app.services import catalog as cat
    gif = b"GIF89a" + struct.pack("<HH", 40, 30) + b"\x00" * 10
    assert cat.image_size("image/gif", gif) == (40, 30)
    jpg = (b"\xff\xd8\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x00" * 9               # APP0
           + b"\xff\xc0" + struct.pack(">HBHHB", 11, 8, 30, 40, 1) + b"\x01\x11\x00")           # SOF0: 30 (bo'y) × 40 (en)
    assert cat.image_size("image/jpeg", jpg) == (40, 30)
    vp8x = b"RIFF" + b"\0\0\0\0" + b"WEBP" + b"VP8X" + b"\0\0\0\0" + b"\0\0\0\0" + (63).to_bytes(3, "little") + (19).to_bytes(3, "little")
    assert cat.image_size("image/webp", vp8x) == (64, 20)
    for data in (gif, jpg, vp8x):
        assert cat.image_from_bytes(data).startswith("data:image/")
    big = b"GIF89a" + struct.pack("<HH", 9000, 10) + b"\x00" * 10
    for bad in (big, b"GIF89a\x01", b"\xff\xd8\xff\xe0\x00", b"RIFF\0\0\0\0WEBPVP8X"):
        with pytest.raises(ValueError):
            cat.image_from_bytes(bad)
    assert cat.parse_params("{\"kerf\": 4, \"grain\": true, \"x\": {\"a\": 1}}") == ({"kerf": 4, "grain": True}, 1)
    assert cat.parse_params("kerf: 4,5; grain; 9bad=1; name=Дуб светлый") == ({"kerf": 4.5, "grain": True, "name": "Дуб светлый"}, 1)
