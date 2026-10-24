"""W11 — (CL) `.project` importi: real-uslubdagi sintetik fikstura (Bazis'dan hisoblanmagan manfiy uzunlik, band tovari, tool.cutting)."""
import os
from pathlib import Path

import pytest

from app.models import OpType, SheetRounding
from app.plugins.legacy_project import import_project

FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<project name="CL import" currency="сум" version="23051701">
 <good typeId="product" id="1" name="Shkaf A" count="2">
  <part id="10" code="01_021" name="№ 01_021" part.code="01_021" l="-350" w="7" dl="-350" dw="7" jl="-350" jw="7" cl="-350" cw="7" count="1" minusCount="0" usedCount="0" txt="true"/>
  <part id="11" code="01_022" name="Plintus" l="1200" w="45" dl="1200" dw="45" jl="1200" jw="45" count="3" elt="@operation#4" ell="@operation#4"/>
  <part id="12" code="01_023" name="CS detal" l="-600" w="300" dl="-600" dw="300" count="1"/>
  <part id="13" code="01_024" name="Brusok" l="800" w="45" dl="800" dw="45" count="2"/>
 </good>
 <good typeId="band" id="20" name="Plintus 45" code="PL-45" l="3200" w="45" t="22" cost="1500" count="-1.54">
  <part count="10000" id="50" l="3200" w="45" usedCount="0"/>
  <part count="3" id="51" l="1000" w="45" usedCount="0"/>
 </good>
 <good typeId="tool.cutting" id="30" swSawthick="4" swPackageHeight="60"/>
 <good typeId="tool.edgeline" id="31" elCost="0" elRestSide="20" elMinSize="0" elWidthPreJoint="0"/>
 <good typeId="band" id="32" name="PVC" code="PVC1" w="19" t="1" cost="500"/>
 <good typeId="sheet" id="33" name="LDSP" l="2750" w="1830" t="16" cost="100"><part id="60" count="10000" l="2750" w="1830"/></good>
 <operation typeId="EL" id="4" tool1="31" w="19" t="1" elSymbol="A" elColor="#ff0000"><material id="32"/></operation>
 <operation typeId="CL" id="7" tool1="30" cSizeMode="1" l="3200" w="45" t="22" cTrimW="10" cTrimEW="-1" cFillRep="0.9" cCPF="0.9"
   cCostCut="100" cCostType="1" cMinDimRegWaste1="150" cBusinessWaste="0.8" cTrimWaste="false" cMinDimDetail="20" cCostByItem="false"
   cCostByItemRound="11" printable="true" startNewPage="true" cPartCountP="4" cPartsAmountP="-1.4"><material id="20" count="-1.54"/><part id="10"/><part id="11"/><part id="13"/><part id="50"/></operation>
 <operation typeId="CS" id="8" tool1="30" cSizeMode="1" cTrimL="10" cTrimW="10"><material id="33" count="1"/><part id="12"/><part id="60"/></operation>
</project>
"""


def _imp(xml=FIXTURE):
    return import_project(xml.encode("utf-8"), "cl.project")


def test_cl_operation_imported_with_params_and_sheets():
    p, warns = _imp()
    cl_ops = [o for o in p.operations if o.type == OpType.CL]
    assert len(cl_ops) == 1
    op = cl_ops[0]
    c = op.cl
    assert (op.code, op.name) == ("PL-45", "Plintus 45")
    assert c.width == 45 and c.thickness == 22 and c.kerf == 4 and c.pack_height == 60       # band good + tool.cutting
    assert c.trim == 10 and c.end_offset is None                                           # cTrimW; cTrimEW < 0 → torsovka
    assert c.waste_min == 150 and c.business_min == 800 and c.waste_incl_trim is False       # cBusinessWaste: m → mm
    assert c.min_part_len == 20 and c.op_cost_base.value == 1 and c.op_price == 100
    assert c.price == 1500 and c.price_by_strip is False and c.strip_rounding == SheetRounding.WHOLE
    assert c.est_fill_percent == 90 and c.fill_packet == 90
    assert [(s.length, s.width, s.qty) for s in op.sheets] == [(1000.0, 45.0, 3), (3200.0, 45.0, 10000)]   # soni bo'yicha o'sish
    assert p.size_mode.value == "detail"


def test_negative_length_rule_uncomputed_not_skipped():
    p, warns = _imp()
    op = next(o for o in p.operations if o.type == OpType.CL)
    by_code = {pt.code: pt for pt in op.parts}
    unc = by_code["01_021"]
    assert unc.length == 0 and unc.width == 0 and unc.src_length == -350 and unc.qty == 1    # hisoblanmagan: 0 + xom qiymat
    ok = by_code["01_022"]
    assert ok.length == 1200 and ok.width == 0 and ok.qty == 3 and ok.src_length is None
    assert len(op.parts) == 3                                                                # polosa (stock) havolasi detal emas
    assert any("1" in w and "CL" in w for w in warns)                                         # imp_cl_uncomputed
    # CS ga tegishli manfiy detal — import qilinmaydi (eski xulq), alohida ogohlantirish
    cs = next(o for o in p.operations if o.type == OpType.CS)
    assert cs.parts == []
    assert any("отрицательным размером" in w or "Manfiy" in w for w in warns)
    # kromka havolasi CL detalida ham o'rnatildi
    el_id = next(o for o in p.operations if o.type == OpType.EL).id
    assert ok.edge_top.op_id == el_id and ok.edge_left.op_id == el_id and ok.edge_bottom.op_id is None


def test_imported_cl_runs_and_reports_uncomputed(tmp_path):
    from app.services import calc
    p, _w = _imp()
    op = next(o for o in p.operations if o.type == OpType.CL)
    for i, pt in enumerate(op.parts, 1):
        pt.uid = i
    calc.run_linear(p, op)
    res = op.result
    # mahsulot soni 2: (1200×3 + 800×2) × 2 = 10 detal; hisoblanmagan detal (1 × 2) kroyga kirmaydi
    assert res.kind == "linear" and res.total_parts == 10 and len(res.unplaced) == 2
    assert any("2" in w for w in res.warnings)
    unc = next(pt for pt in op.parts if pt.src_length)
    assert unc.left_qty == 2 and unc.used_qty == 0


def test_only_cl_project_takes_size_mode_from_cl():
    xml = FIXTURE.replace('cSizeMode="1" l="3200"', 'cSizeMode="2" l="3200"')
    xml = xml.replace('<operation typeId="CS" id="8" tool1="30" cSizeMode="1" cTrimL="10" cTrimW="10"><material id="33" count="1"/><part id="12"/><part id="60"/></operation>', "")
    p, _w = _imp(xml)
    assert p.size_mode.value == "jointed"


def test_business_waste_mm_heuristic_and_defaults():
    xml = FIXTURE.replace('cBusinessWaste="0.8"', 'cBusinessWaste="500"').replace('cMinDimRegWaste1="150"', "")
    p, _w = _imp(xml)
    c = next(o for o in p.operations if o.type == OpType.CL).cl
    assert c.business_min == 500 and c.waste_min == 100                                       # ≥ 50 → mm; atribut yo'q — standart


def test_api_import_file_roundtrip(client):
    r = client.post("/api/projects/import-file", files={"file": ("cl.project", FIXTURE.encode("utf-8"), "application/xml")})
    assert r.status_code == 200, r.text
    data = r.json()
    proj = data["project"]
    op = next(o for o in proj["operations"] if o["type"] == "CL")
    assert op["cl"]["width"] == 45 and len(op["parts"]) == 3 and op["sheets"][0]["width"] == 45
    assert any("CL" in w for w in data["warnings"])
    res = client.post(f"/api/projects/{proj['id']}/operations/{op['id']}/optimize")
    assert res.status_code == 200 and res.json()["total_parts"] == 10
    # eksport (W10) CL ni yozadi (sxema tekshiruvidan o'tadi) va qayta o'qiydi
    exp = client.get(f"/api/projects/{proj['id']}/export/project")
    assert exp.status_code == 200, exp.text[:300]
    p2, _w = import_project(exp.content, "again.project")
    op2 = next(o for o in p2.operations if o.type == OpType.CL)
    a, b = op["cl"], op2.cl
    for k in ("width", "thickness", "kerf", "trim", "waste_min", "business_min", "waste_incl_trim", "min_part_len", "price", "op_price"):
        assert abs(float(a[k]) - float(getattr(b, k))) < 1e-6 if not isinstance(a[k], bool) else a[k] == getattr(b, k), k
    assert [s.length for s in op2.sheets] == [s["length"] for s in op["sheets"]]
    assert sorted((pt.length, pt.qty) for pt in op2.parts) == sorted((pt["length"], pt["qty"]) for pt in op["parts"])
    assert any(pt.src_length == -350 for pt in op2.parts)                  # hisoblanmagan belgi (manfiy uzunlik) saqlanadi


@pytest.mark.skipif(not os.environ.get("MEBELIX_REAL_PROJECTS"), reason="korxona fayllari: MEBELIX_REAL_PROJECTS=<papka>")
def test_real_cl_files_import_generic():
    """Real (Bazis'dan, hisoblanmagan) CL loyihalar: hammasi o'qiladi; CL operatsiyalari va manfiy detallar soni umumiy hisoblanadi."""
    root = Path(os.environ["MEBELIX_REAL_PROJECTS"])
    n_cl = n_unc = 0
    for f in root.rglob("*.project"):
        data = f.read_bytes()
        if b'typeId="CL"' not in data:
            continue
        p, _w = import_project(data, "x.project")
        for op in p.operations:
            if op.type == OpType.CL:
                n_cl += 1
                assert op.cl.width > 0 and op.sheets and all(s.width == op.cl.width for s in op.sheets)
                n_unc += sum(1 for pt in op.parts if pt.src_length is not None and pt.length == 0)
    assert n_cl >= 1 and n_unc >= 0


def test_kerf_group_import_export_roundtrip(client):
    """«Толщина пилы для групповых деталей» (CL, onlayndagidek tahrirlanadi): swSawthickDiv o'qiladi, saqlanadi, eksportda qaytadi;
    -1 / yo'q — bo'sh (asosiy propil)."""
    p, _w = _imp()
    assert next(o for o in p.operations if o.type == OpType.CL).cl.kerf_group is None
    xml = FIXTURE.replace('swSawthick="4"', 'swSawthick="4" swSawthickDiv="2.5"')
    p, _w = _imp(xml)
    assert next(o for o in p.operations if o.type == OpType.CL).cl.kerf_group == 2.5
    r = client.post("/api/projects/import-file", files={"file": ("cl.project", xml.encode("utf-8"), "application/xml")}).json()
    pid, op = r["project"]["id"], next(o for o in r["project"]["operations"] if o["type"] == "CL")
    assert op["cl"]["kerf_group"] == 2.5
    assert client.patch(f"/api/projects/{pid}/operations/{op['id']}", json={"cl": {**op["cl"], "kerf_group": 1.5}}).status_code == 200
    p2, _w = import_project(client.get(f"/api/projects/{pid}/export/project").content, "again.project")
    assert next(o for o in p2.operations if o.type == OpType.CL).cl.kerf_group == 1.5
    assert client.patch(f"/api/projects/{pid}/operations/{op['id']}", json={"cl": {**op["cl"], "kerf_group": None}}).status_code == 200
    p3, _w = import_project(client.get(f"/api/projects/{pid}/export/project").content, "again.project")
    assert next(o for o in p3.operations if o.type == OpType.CL).cl.kerf_group is None
