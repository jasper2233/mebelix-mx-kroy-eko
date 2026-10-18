"""MES paketi v1 (2026-10-18): sxema, QR qoidasi, kesish xaritasi, qoldiqlar, faqat ochilgan postprotsessorlar, sha256.
Ma'lumotlar sintetik (korxona fayllari ishlatilmaydi)."""
import base64
import hashlib

import pytest

from app.models import Product, Project
from app.services import mes_package as M
from test_qa_fix_calc import _set_prog, _xnc_for

ORDER = "B-2026-901"


@pytest.fixture()
def reset_access(client):
    yield
    client.put("/api/postprocessors/access", json={"open": None})
    client.put("/api/postprocessors/machines", json={"enabled": {}, "profile": {}, "prefix": False})


@pytest.fixture()
def proj(client, kravat):
    """kravat + mahsulot «KR01» (×2) + XNC (detal №6), MES buyurtma raqami, kroy qilingan."""
    pid, cs, _el = kravat
    pid, cs, ptid, xid = _xnc_for(client, kravat)
    _set_prog(client, pid, xid, [dict(cmd="DrillFront", params=dict(X=30, Y=20, DP=12, D=8), comment="", children=[])])
    p = client.post(f"/api/projects/{pid}/products", json={"name": "Kravat", "code": "KR01", "qty": 2}).json()
    prid = p["products"][-1]["id"]
    parts = next(o for o in p["operations"] if o["id"] == cs)["parts"]
    for i, pt in enumerate(parts):
        r = client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{pt['id']}",
                         json={"product_id": prid, "code": f"{i + 1:03d}"})
        assert r.status_code == 200, r.text
    assert client.patch(f"/api/projects/{pid}", json={"mes_order_ref": ORDER}).status_code == 200
    r = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    assert r.status_code == 200, r.text
    return pid, cs, xid


def _pkg(client, pid, **q):
    r = client.get(f"/api/projects/{pid}/mes-package", params={"version": 1, **q})
    assert r.status_code == 200, r.text
    return r.json()


def test_schema_validates_and_core_rules(client, proj, reset_access):
    pid, cs, xid = proj
    d = _pkg(client, pid, pp="none")
    pkg = M.MesPackageV1.model_validate(d)                      # qat'iy sxema (extra=forbid)
    assert pkg.package.format == "mebelix.kroy.mes-package" and pkg.package.version == 1
    assert pkg.source.mes_order_number == ORDER and pkg.source.kind == "manual" and pkg.source.project_id == pid
    sch = client.get("/api/mes-package/schema", params={"version": 1}).json()
    assert sch["title"] == "MesPackageV1" and "PostprocessorFile" in sch["$defs"]
    assert client.get(f"/api/projects/{pid}/mes-package", params={"version": 2}).status_code == 400
    assert client.get("/api/projects/nope/mes-package").status_code == 404
    # materiallar, kromka
    assert [m.ref for m in pkg.materials] == [cs] and pkg.materials[0].kind == "sheet" and pkg.materials[0].thickness > 0
    assert pkg.edge_bands and pkg.edge_bands[0].code == "KP-1/19" and pkg.edge_bands[0].work_m > 0
    # detallar: QR qoidasi {buyurtma}_{mahsulot}_{detal}[_n]; mahsulot ×2 → har detalda kamida 2 nusxa (_1, _2)
    p6 = next(p for p in pkg.parts if p.name == "Panel6")
    assert p6.key == "KR01_006" and p6.qty_total == 2 and set(p6.edges) == {"t", "b"}
    assert [i.qr for i in p6.instances] == [f"{ORDER}_KR01_006_1", f"{ORDER}_KR01_006_2"]
    assert p6.xnc_refs == [xid]
    assert len({i.qr for p in pkg.parts for i in p.instances}) == sum(p.qty_total for p in pkg.parts)   # global noyob
    # har nusxa kesish xaritasidagi katakka bog'langan; katakdagi nusxalar soni = andoza listlari soni
    sheets = {s.no: s for cm in pkg.cut_maps for s in cm.sheets}
    count: dict = {}
    for p in pkg.parts:
        for i in p.instances:
            assert i.pattern_no in sheets and i.cell_index is not None and 1 <= i.sheet_copy <= sheets[i.pattern_no].mult
            cell = next(c for c in sheets[i.pattern_no].cells if c.cell == i.cell_index)
            assert cell.part_key == p.key and not cell.waste
            count[(i.pattern_no, i.cell_index)] = count.get((i.pattern_no, i.cell_index), 0) + 1
    for no, s in sheets.items():
        for c in s.cells:
            if not c.waste:
                assert count[(no, c.cell)] == s.mult
            assert -0.01 <= c.x and c.x + c.w <= s.L + 0.01 and -0.01 <= c.y and c.y + c.h <= s.W + 0.01
        assert s.cuts and s.commands                           # gilyotina chiziqlari va arra buyruqlari
        for ln in s.cuts:
            assert (ln.x1 == ln.x2 or ln.y1 == ln.y2) and max(ln.x1, ln.x2) <= s.L + 0.01 and max(ln.y1, ln.y2) <= s.W + 0.01
    assert sum(u.qty for u in pkg.sheets if u.source == "new") == sum(s.mult for s in sheets.values())
    # foydali qoldiqlar: har jismoniy nusxa — alohida ATX
    assert [r.id for r in pkg.remnants] == [f"ATX-{ORDER}-{n}" for n in range(1, len(pkg.remnants) + 1)]
    for r in pkg.remnants:
        assert r.sheet_no in sheets and r.to_warehouse and r.material_code == "LDSP16"
    # sarf (avtomatik hujjat uchun), XNC dasturi
    assert any(c.material_ref == cs and c.unit == "sheets" and c.qty > 0 for c in pkg.consumption)
    x = next(x for x in pkg.xnc_programs if x.mx_op_id == xid)
    assert x.part_key == "KR01_006" and x.stats.get("drills") == 1
    # fayl yo'q — MES ishlov oqimi boshlanmaydi
    assert pkg.postprocessor_files == [] and not pkg.machining.saw_ready and not pkg.machining.cnc_ready


def test_only_opened_postprocessors_and_checksums(client, proj, reset_access):
    pid, cs, xid = proj
    client.put("/api/postprocessors/access", json={"open": ["holzma_ptx", "tpa"]})
    d = _pkg(client, pid, pp="all")
    pkg = M.MesPackageV1.model_validate(d)
    keys = {f.machine.key for f in pkg.postprocessor_files}
    assert keys == {"holzma_ptx", "tpa"}                         # yopiqlar (scm_wincut, woodwop …) kirmaydi
    for f in pkg.postprocessor_files:
        raw = base64.b64decode(f.content_base64)
        assert f.size == len(raw) and f.sha256 == hashlib.sha256(raw).hexdigest() and f.url is None
        assert f.format_id == f"machine:{f.machine.key}" and f.source == "native" and f.file_name
    saw = next(f for f in pkg.postprocessor_files if f.machine.group == "saw")
    cnc = next(f for f in pkg.postprocessor_files if f.machine.group == "cnc")
    assert saw.op_ref == cs and cnc.op_ref == xid and cnc.part_keys == ["KR01_006"]
    assert pkg.machining.saw_ready and pkg.machining.cnc_ready and pkg.machining.files == len(pkg.postprocessor_files)
    # yopiq postprotsessor aniq so'ralsa — 403; noma'lum — 400
    r = client.get(f"/api/projects/{pid}/mes-package", params={"pp": "machine:scm_wincut"})
    assert r.status_code == 403 and "администратор" in r.json()["detail"]
    assert client.get(f"/api/projects/{pid}/mes-package", params={"pp": "zzz"}).status_code == 400
    # aniq ro'yxat (ochilgan) va files=meta: kontentsiz, url bilan
    d = _pkg(client, pid, pp="machine:holzma_ptx", files="meta")
    f = d["postprocessor_files"][0]
    assert len(d["postprocessor_files"]) == 1 and f["content_base64"] is None and f["url"] and len(f["sha256"]) == 64
    assert client.get(f["url"]).status_code == 200
    assert client.get(f"/api/projects/{pid}/mes-package", params={"files": "zip"}).status_code == 400


def test_default_selection_is_enabled_machines(client, proj, reset_access):
    pid, _cs, _xid = proj
    assert _pkg(client, pid)["postprocessor_files"] == []          # hech bir stanok yoqilmagan
    client.put("/api/postprocessors/machines", json={"enabled": {"holzma_ptx": True, "scm_wincut": True}, "profile": {},
                                                      "prefix": False})
    assert {f["machine"]["key"] for f in _pkg(client, pid)["postprocessor_files"]} == {"holzma_ptx", "scm_wincut"}
    client.put("/api/postprocessors/access", json={"open": ["holzma_ptx"]})       # admin yopdi
    assert {f["machine"]["key"] for f in _pkg(client, pid)["postprocessor_files"]} == {"holzma_ptx"}


def test_without_order_number_and_source_kind(client, kravat, reset_access):
    pid, cs, _el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    d = _pkg(client, pid, pp="none")
    assert d["source"]["mes_order_number"] is None and any("mes_order_number" in w for w in d["warnings"])
    assert all(i["qr"] is None for p in d["parts"] for i in p["instances"]) and all(r["id"] is None for r in d["remnants"])
    d = _pkg(client, pid, pp="none", mes_order_number="B-2026-7", mes_order_id=77)
    assert d["source"]["mes_order_id"] == 77 and d["parts"][0]["instances"][0]["qr"].startswith("B-2026-7_")
    # kodsiz mahsulot (kirill nomi) — ID nomdan olinadi va skaner o'qiy olmasligi haqida ogohlantiriladi (MES qoidasi)
    assert any("skaner" in w for w in d["warnings"])
    assert M.source_kind(Project(products=[Product(name="A", extra={"product.import": "bm.1.86"})])) == "bazis_file"
    assert M.source_kind(Project(products=[Product(name="A", legacy_program="x")])) == "project_file"
    assert M.source_kind(Project(products=[Product(name="A")])) == "manual"
    assert not M.scannable("Изделие1") and M.scannable("4358 Sarvar")
