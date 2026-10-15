"""2026-10-15 (2-sessiya): onlayn tizim bilan solishtiruvdagi import va hisobot farqlari (X_1015 §9).

F8  — `.project` detal «ID» (uid) fayldagi `<part id="N">` raqami (detal qaysi operatsiyada bo'lsa ham o'sha), yaroqsiz id —
      eng kattasidan keyingi raqam; eksport o'sha raqamlarni yozadi (aylanma import saqlaydi).
F20 — EL «Линии маркировки» `elLineMark="0"` → 0.
F25 — O operatsiyasi egasi — mahsulot ichidagi `<operation id="N"/>` havolasi; eksport ham shunday yozadi.
F35–F39 — hisobot: jadvallar sahifa kengligida, sanalar «дд.мм.гггг», «Требование на склад» operatsiya raqami bilan (O — bitta
      qator + N.k material qatorlari), detal nomi ostida «P1-1: <kod>», karta sarlavhasi ikki qatorda, o'lcham yozuvida kromka
      belgisi («951 A»), karta yonidagi jadvalda «T», legenda «[T] Текстура» / «[%] Сверление» / «A: …».
Sintetik fayl — mijoz ma'lumoti yo'q."""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET

from app import store
from app.models import OpType, Operation, OParams, Part, Project, StockSheet
from app.plugins.legacy_project import import_project
from app.services.project_export import export_project
from app.services.project_schema import validate_project_xml

PROG_DRILL = html.escape('<program dx="951" dy="500" dz="16"><bf x="10" y="10" dp="5" name="Bore5"/></program>', quote=True)


def xml(el_line_mark: str = ' elLineMark="0"') -> bytes:
    """Ikki mahsulot, 2 CS + CS (ikkinchi mahsulot), EL×2, O×4, XNC×2 — real fayl tuzilishi (id lar aralash tartibda)."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project name="X1015b" currency="UZS" version="1" date="1785152837899" orderDate="1785152837899">
 <good typeId="product" id="2" count="1" name="Model-A" code="4210">
  <part id="18" name="polka" dl="951" dw="500" count="1" txt="true" elt="@operation#1"/>
  <part id="2" name="tom" dl="1950" dw="600" count="1" txt="true"/>
  <part id="3" name="bok" dl="1968" dw="600" count="2" txt="false"/>
  <part id="x7" name="badid" dl="400" dw="300" count="1"/>
  <part id="0" name="zeroid" dl="450" dw="300" count="1"/>
  <part id="40" name="fasad-xdf" dl="1999" dw="1949" count="1" txt="false"/>
  <operation id="9"/>
 </good>
 <good typeId="product" id="1" count="2" name="Model-B">
  <part id="77" name="pol" dl="883" dw="584" count="2" txt="true"/>
  <operation id="31"/>
 </good>
 <good typeId="tool.cutting" id="3" swSawthick="3" swMaxturns="4"/>
 <good typeId="tool.edgeline" id="7" elRestSide="30" elMinSize="100" elWidthPreJoint="1" elCost="0"/>
 <good typeId="sheet" id="4" t="16" name="LMDF" l="2750" w="1830" count="5" cost="0"><part id="71" count="5" l="2750" w="1830"/></good>
 <good typeId="sheet" id="6" t="3" name="XDF" code="XDF 5.8" l="2800" w="2070" count="2" cost="0"/>
 <good typeId="band" id="8" t="1" w="19" name="PVC 19" code="KP-19"/>
 <good typeId="simple" id="15" unit="шт" count="134" cost="0" name="Mix 2.5" code="Q25 kg"/>
 <good typeId="simple" id="16" unit="шт" count="72" cost="0" name="Yevrovint"/>
 <good typeId="simple" id="17" unit="кг" count="1" cost="0" name="Kley" code="KL-1"/>
 <operation typeId="CS" id="3" tool1="3" cSizeMode="1" cTrimL="2" cTrimW="2" l="2750" w="1830" t="16" printable="true" startNewPage="true">
  <material id="4"/><part id="18"/><part id="2"/><part id="3"/><part id="x7"/><part id="0"/><part id="71"/>
 </operation>
 <operation typeId="CS" id="4" tool1="3" cSizeMode="1" l="2800" w="2070" t="3" printable="true" startNewPage="true">
  <material id="6"/><part id="40"/>
 </operation>
 <operation typeId="EL" id="1" tool1="7" w="19" t="1" elCalcMat="true" elSymbol="A" elColor="#000000"{el_line_mark} printable="true" startNewPage="true">
  <material id="8"/><part id="18"/>
 </operation>
 <operation typeId="O" typeName="Komplektuyushie" id="9" costOperation="0" printable="true" startNewPage="true">
  <material id="15" count="134"/><material id="16" count="72"/>
 </operation>
 <operation typeId="XNC" id="8" code="X-18-1" typeName="polka" program="{PROG_DRILL}" count="1" side="true" turn="0" bySizeDetail="true" printable="true" startNewPage="true">
  <part id="18"/>
 </operation>
 <operation typeId="XNC" id="22" code="X-18-2" typeName="polka orqa" program="{PROG_DRILL}" count="1" side="false" turn="0" bySizeDetail="true" printable="true" startNewPage="true">
  <part id="18"/>
 </operation>
 <operation typeId="CS" id="32" tool1="3" cSizeMode="1" l="2750" w="1830" t="16" printable="true" startNewPage="true">
  <material id="4"/><part id="77"/><part id="18"/>
 </operation>
 <operation typeId="EL" id="5" tool1="7" w="19" t="1" elCalcMat="true" elSymbol="B" elColor="#ff0000" elLineMark="2" printable="true" startNewPage="true">
  <material id="8"/>
 </operation>
 <operation typeId="O" typeName="Komplektuyushie" id="31" costOperation="0" printable="true" startNewPage="true">
  <material id="15" count="10"/>
 </operation>
 <operation typeId="O" typeName="Upakovka" id="33" costOperation="0" printable="true" startNewPage="true">
  <material id="17" count="1"/>
 </operation>
 <operation typeId="O" typeName="Owner-attr" id="34" owner="1" costOperation="0" printable="true" startNewPage="true">
  <material id="17" count="2"/>
 </operation>
</project>""".encode("utf-8")


def _imp(data: bytes = None):
    return import_project(data or xml(), "x1015b.project")


def _ops(p, t):
    return [o for o in p.operations if o.type == t]


def _owner_name(p: Project, op: Operation):
    return next((pr.name for pr in p.products if pr.id == op.o.owner_product_id), None) if op.o else None


# ───────────────────────── F8: detal ID fayldan ─────────────────────────
def test_part_ids_come_from_file_and_unusable_ids_continue_after_max():
    p, warns = _imp()
    cs1, cs2, cs3 = _ops(p, OpType.CS)
    assert [pt.uid for pt in cs1.parts] == [18, 2, 3, 78, 79]        # fayldagi raqamlar; «x7» va «0» — eng kattasi (77) dan keyin
    assert [pt.name for pt in cs1.parts][3:] == ["badid", "zeroid"]
    assert [pt.uid for pt in cs2.parts] == [40]
    assert [pt.uid for pt in cs3.parts] == [77, 18]                   # nusxa ham o'sha ID bilan (detal ikki operatsiyada)
    assert any("18" in w for w in warns)                              # nusxa haqida ogohlantirish qoladi
    assert cs3.parts[1].id != cs1.parts[0].id                         # ichki id lar alohida
    for o in (cs1, cs2, cs3):
        assert len({pt.uid for pt in o.parts}) == len(o.parts)       # operatsiya ichida noyob
    assert store.next_uid(p) == 80                                    # yangi detal eng kattasidan keyin


def test_duplicate_file_id_inside_one_operation_gets_a_fresh_number():
    data = xml().replace(b'<material id="6"/><part id="40"/>', b'<material id="6"/><part id="40"/><part id="40"/>')
    p, _w = _imp(data)
    cs2 = _ops(p, OpType.CS)[1]
    assert [pt.uid for pt in cs2.parts] == [40, 80] and cs2.parts[0].id != cs2.parts[1].id   # 78, 79 — «x7» va «0» (1-CS)


# ───────────────────────── F20: Линии маркировки ─────────────────────────
def test_el_line_mark_zero_is_imported_as_zero():
    p, _w = _imp()
    el0, el2 = _ops(p, OpType.EL)
    assert el0.el.marker_lines == 0 and el2.el.marker_lines == 2
    p, _w = _imp(xml(el_line_mark=""))
    assert _ops(p, OpType.EL)[0].el.marker_lines == 1                 # atribut yo'q — standart 1
    p, _w = _imp(xml(el_line_mark=' elLineMark="9"'))
    assert _ops(p, OpType.EL)[0].el.marker_lines == 3                 # chegara


# ───────────────────────── F25: O egasi ─────────────────────────
def test_o_owner_comes_from_product_operation_reference():
    p, warns = _imp()
    o9, o31, o33, o34 = _ops(p, OpType.O)
    assert _owner_name(p, o9) == "Model-A"                            # `<operation id="9"/>` Model-A ichida
    assert _owner_name(p, o31) == "Model-B"
    assert o33.o.owner_product_id is None                             # havola ham, owner ham yo'q — loyiha
    assert _owner_name(p, o34) == "Model-B"                           # `owner` atributi avvalgidek ishlaydi
    assert not any("Komplektuyushie" in w for w in warns)
    assert o31.o.multiplier == 1 and o31.cost_material == 0           # hisob keyin (calc) — import narxni o'zgartirmaydi


# ───────────────────────── eksport: id lar va egasi aylanma importda saqlanadi ─────────────────────────
def test_export_writes_part_uids_and_owner_reference_and_roundtrips():
    p, _w = _imp()
    res = export_project(p)
    assert validate_project_xml(res.xml, strict=True) == []
    root = ET.fromstring(res.xml)
    prods = root.findall("good[@typeId='product']")
    ids_a = [e.get("id") for e in prods[0].findall("part")]
    assert ids_a[:3] == ["18", "2", "3"] and {"78", "79", "40"} <= set(ids_a)
    assert ids_a.count("18") == 1 and len(ids_a) == 6                  # ikki CS dagi nusxa — bitta qator (real fayllardagidek)
    assert [e.get("id") for e in prods[1].findall("part")] == ["77"]
    cs_refs = [[r.get("id") for r in o.findall("part")] for o in root.findall("operation") if o.get("typeId") == "CS"]
    assert cs_refs[0][:5] == ["18", "2", "3", "78", "79"] and cs_refs[2][:2] == ["77", "18"]   # ikkala CS o'sha id ga havola
    o_ids = [o.get("id") for o in root.findall("operation") if o.get("typeId") == "O"]
    assert [r.get("id") for r in prods[0].findall("operation")] == [o_ids[0]]              # Model-A ← O #9
    assert [r.get("id") for r in prods[1].findall("operation")] == [o_ids[1], o_ids[3]]    # Model-B ← O #31, O #34
    others = [e.get("id") for e in root.iter() if e.tag in ("good", "operation") and e.get("id")]
    assert all(int(i) > 79 for i in others)                           # qolgan id lar detal raqamlaridan keyin
    p2, _w2 = import_project(res.xml, "rt.project")
    for a, b in zip(_ops(p, OpType.CS), _ops(p2, OpType.CS)):
        assert [pt.uid for pt in a.parts] == [pt.uid for pt in b.parts]
    assert [_owner_name(p2, o) for o in _ops(p2, OpType.O)] == ["Model-A", "Model-B", None, "Model-B"]
    assert [o.el.marker_lines for o in _ops(p2, OpType.EL)] == [0, 2]


def test_export_allocates_fresh_ids_for_missing_or_repeated_uids():
    cs1 = Operation(type=OpType.CS, name="A", sheets=[StockSheet(length=2750, width=1830)],
                    parts=[Part(uid=0, name="no-uid", length=300, width=200), Part(uid=5, name="five", length=300, width=200)])
    cs2 = Operation(type=OpType.CS, name="B", sheets=[StockSheet(length=2750, width=1830)],
                    parts=[Part(uid=5, name="five-again", length=300, width=200)])
    p = Project(name="ids", operations=[cs1, cs2])
    for pt in cs1.parts + cs2.parts:
        pt.product_id = p.products[0].id if p.products else None
    res = export_project(p)
    assert validate_project_xml(res.xml, strict=True) == []
    root = ET.fromstring(res.xml)
    ids = [e.get("id") for e in root.iter("part") if e.get("name")]
    assert "5" in ids and len(ids) == len(set(ids)) == 3
    p2, _w = import_project(res.xml, "ids.project")
    assert [pt.uid for o in _ops(p2, OpType.CS) for pt in o.parts if pt.name == "five"] == [5]


def test_schema_rejects_product_operation_reference_to_unknown_operation():
    p, _w = _imp()
    res = export_project(p)
    bad = re.sub(rb'<operation id="(\d+)"/>', b'<operation id="999"/>', res.xml, count=1)
    assert any("999" in e for e in validate_project_xml(bad, strict=True))


# ───────────────────────── hisobot (F35–F39) ─────────────────────────
def _report(client, **ps):
    r = client.post("/api/projects/import-file", files={"file": ("x1015b.project", xml(), "application/xml")})
    assert r.status_code == 200, r.text[:300]
    p = r.json()["project"]
    pid = p["id"]
    cs = next(o for o in p["operations"] if o["type"] == "CS")["id"]
    assert client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").status_code == 200
    # tayanadigan bo'limlar aniq yoqiladi (profil standartlari boshqa agent/foydalanuvchi qaroriga bog'liq — F40)
    base = dict(header=True, warehouse=True, cs_title=True, cs_parts=True, cs_maps=True, map_parts_list=True, map_edges=True)
    return client.post(f"/api/projects/{pid}/report?lang=ru", json={**base, **ps}).text, pid


def test_report_tables_full_width_and_dates_dmy(client):
    h, _pid = _report(client)
    assert re.search(r"table \{[^}]*width: 100%", h) and ".kv, .side table { width: auto; }" in h
    assert re.search(r"td, th \{[^}]*overflow-wrap: anywhere", h)
    assert "<td><b>Дата заказа</b></td><td>27.07.2026</td>" in h and "<td>2026-07-27</td>" not in h


def test_report_warehouse_numbers_by_operation_and_o_rows(client):
    h, _pid = _report(client)
    wh = h.split("Требование на склад")[1].split("</table>")[0]
    rows = [re.sub(r"</?t[dh][^>]*>", "|", r) for r in re.findall(r"<tr>(.*?)</tr>", wh)]
    assert rows[1].startswith("|1||CS||||LMDF (Листы:")
    assert rows[2].startswith("|2||CS||XDF 5.8||XDF")
    assert rows[3].startswith("|3||EL||KP-19||PVC 19 (Длина кромкования")
    assert rows[4] == "|4||O||Model-A||Komplektuyushie|||||"                      # O — bitta qator, egasi mahsulot
    assert rows[5] == "|4.1||||Q25 kg||Mix 2.5||шт||134|" and rows[6] == "|4.2||||||Yevrovint||шт||72|"
    # XNC lar 5 va 6 — talabnomada yo'q, lekin raqam ularni ham sanaydi: ikkinchi mahsulot 7 (CS), 9, 10, 11 (O)
    assert rows[7].startswith("|7||CS||||LMDF")
    assert rows[8] == "|9||O||Model-B||Komplektuyushie|||||" and rows[9] == "|9.1||||Q25 kg||Mix 2.5||шт||20|"  # × 2 dona
    assert rows[10] == "|10||O||Проект||Upakovka|||||" and rows[11] == "|10.1||||KL-1||Kley||кг||1|"
    assert rows[12] == "|11||O||Model-B||Owner-attr|||||"
    assert not any(r.startswith("|5||") or r.startswith("|6||") or r.startswith("|8||") for r in rows)


def test_report_parts_table_lists_programs_under_name_without_marks(client):
    h, _pid = _report(client)
    sec = h.split("(CS)")[1]
    row = re.search(r"<tr><td>18</td>.*?</tr>", sec).group(0)
    assert row.endswith("<td>polka<br>P1-1: X-18-1<br>P2-1: X-18-2</td></tr>")       # lits 1, orqa 2
    assert "% polka" not in h and "<td>polka</td>" not in sec.split("Листы")[0]
    assert "<td>tom</td>" in sec                                                      # dastursiz detal — faqat nom


def test_report_map_header_dimension_symbols_marks_and_legend(client):
    h, _pid = _report(client)
    heads = re.findall(r"<div class='maphdr'>(.*?)</div>", h)
    assert heads and re.fullmatch(r"LMDF<br>№:1/\d+  S:2750/1830  C:1/\d+  Cp:\d+/6  LT:[\d.]+/[\d.]+  F:[\d.]+%/[\d.]+%", heads[0])
    assert re.search(r">(951|500) A</text>", h)                                       # kromkali tomon bo'ylab o'lcham + belgi
    assert re.search(r">(1950|600)</text>", h)                                        # kromkasiz detal — faqat son
    # karta yonidagi jadval (detal qaysi kartada bo'lsa ham): «Мт» — Ткт + teshik dasturi; teksturasiz, dastursiz detal — bo'sh
    assert re.search(r"<tr><td>18</td><td>951</td><td>500</td><td>1</td><td>T%</td></tr>", h)
    assert re.search(r"<tr><td>3</td><td>1968</td><td>600</td><td>\d</td><td></td></tr>", h)
    legend = re.search(r"<div class='legend'>(.*?)</div>", h).group(1)
    assert legend.startswith("[T] Текстура<br>[%] Сверление<br>") and legend.endswith("</span> A: PVC 19")
    assert "A-1:" not in legend


def test_report_print_settings_still_apply(client):
    h, _pid = _report(client, map_parts_list=False, cs_maps=True, map_part_marks=True)
    assert "class='legend'" not in h and "<td>T%</td>" not in h
    assert re.search(r'font-weight="bold" fill="#241400"[^>]*>%</text>', h)         # kartadagi ishlov belgisi (sozlama bilan)
    h2, _pid = _report(client, cs_maps=False, warehouse=False)
    assert "class='maphdr'" not in h2 and "Требование на склад" not in h2
